import discord
from discord.ext import commands
import logging
from datetime import datetime
import json
import re
from src.database.connection import get_connection
from src.services.base_service import ServiceResponse
from src.config.constants.bot_constants import Balance, TransactionType

# Constants yang diperlukan - sementara hardcode sampai constants diperbaiki
CURRENCY_RATES = {
    'RATES': {
        'DL': 100,
        'BGL': 10000
    }
}

COLORS = {
    'SUCCESS': 0x00ff00,
    'ERROR': 0xff0000
}

PATHS = {
    'CONFIG': 'config.json'  # Adjust path sesuai kebutuhan
}

# Load config akan dilakukan saat setup, bukan saat import
DONATION_CHANNEL_ID = None

class DonationManager:
    """Manager class for handling donations"""
    _instance = None

    def __new__(cls, bot):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, bot):
        if not hasattr(self, 'initialized'):
            self.bot = bot
            self.logger = logging.getLogger("DonationManager")
            self.balance_manager = None
            
            # Validasi channel ID saat inisialisasi
            if not DONATION_CHANNEL_ID:
                self.logger.error("Donation channel ID not configured in config.json")
            
            self.initialized = True

    async def validate_growid(self, growid: str) -> tuple[bool, str]:
        """Validasi GrowID menggunakan user service"""
        try:
            # Import here to avoid circular imports
            from src.services.user_service import UserService
            
            # Gunakan user service untuk cek GrowID
            user_service = UserService(self.bot)
            user_response = await user_service.get_user_by_growid(growid)
            
            if not user_response.success or not user_response.data:
                self.logger.warning(f"Validate GrowID failed: {growid} not found in database")
                return False, "❌ GrowID tidak terdaftar di database"
                
            self.logger.info(f"Validate GrowID success: {growid}")
            return True, "✅ GrowID valid"
            
        except Exception as e:
            self.logger.error(f"Error validating GrowID: {e}")
            return False, "❌ Terjadi kesalahan saat validasi GrowID"

    async def process_donation_message(self, message: discord.Message) -> None:
        """Proses pesan donasi dari channel donation"""
        try:
            content = message.content.strip()
            
            # Cek apakah pesan embed
            if message.embeds:
                # Ambil content dari embed
                embed = message.embeds[0]
                if embed.description:
                    content = embed.description
                elif embed.fields:
                    # Gabungkan semua field content
                    content = "\n".join([f.value for f in embed.fields])
            
            # Parse pesan dengan format: GrowID: Fdy\nDeposit: 1 Diamond Lock
            patterns = [
                r"GrowID:\s*(\w+).*?Deposit:\s*(.+)",  # Format utama
                r"GrowID:\s*(\w+).*?Jumlah:\s*(.+)",   # Format alternatif
            ]
            
            match = None
            for pattern in patterns:
                match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
                if match:
                    break
            
            if not match:
                self.logger.debug(f"Format pesan tidak sesuai: {content}")
                return

            growid = match.group(1).strip()
            deposit_str = match.group(2).strip()

            self.logger.info(f"Processing donation: GrowID={growid}, Deposit={deposit_str}")

            # Validasi GrowID menggunakan user service
            is_valid, message_text = await self.validate_growid(growid)
            if not is_valid:
                self.logger.warning(f"Donation failed: {message_text} for growid {growid}")
                await message.channel.send(f"Failed to find growid {growid}")
                return

            # Get current balance via user service
            from src.services.user_service import UserService
            user_service = UserService(self.bot)
            user_response = await user_service.get_user_by_growid(growid)
            if not user_response.success or not user_response.data:
                self.logger.warning(f"Donation failed: User data not found for growid {growid}")
                await message.channel.send(f"Failed to find growid {growid}")
                return

            current_balance = user_response.data.balance

            # Parse deposit amounts
            try:
                wl, dl, bgl = self.parse_deposit(deposit_str)
                if wl == 0 and dl == 0 and bgl == 0:
                    self.logger.warning(f"Donation failed: Deposit amounts zero for growid {growid}")
                    await message.channel.send(f"Failed to find growid {growid}")
                    return
            except Exception as e:
                self.logger.error(f"Error parsing deposit: {e}")
                await message.channel.send(f"Failed to find growid {growid}")
                return

            # Process donation
            try:
                new_balance = await self.process_donation(growid, wl, dl, bgl, current_balance)
                
                # Format balance untuk response
                balance_text = f"{new_balance.wl:,} WL"
                if new_balance.dl > 0:
                    balance_text += f", {new_balance.dl:,} DL"
                if new_balance.bgl > 0:
                    balance_text += f", {new_balance.bgl:,} BGL"
                
                await message.channel.send(f"Successfully filled {growid}. Current growid balance {balance_text}")
                
            except Exception as e:
                self.logger.error(f"Error processing donation: {e}")
                await message.channel.send(f"Failed to find growid {growid}")

        except Exception as e:
            self.logger.error(f"Error processing donation message: {e}")
            await message.channel.send(f"Failed to find growid")

    def parse_deposit(self, deposit: str) -> tuple[int, int, int]:
        """Parse deposit string into WL, DL, BGL amounts"""
        wl = dl = bgl = 0
        
        if 'World Lock' in deposit:
            wl = int(re.search(r'(\d+) World Lock', deposit).group(1))
        if 'Diamond Lock' in deposit:
            dl = int(re.search(r'(\d+) Diamond Lock', deposit).group(1))
        if 'Blue Gem Lock' in deposit:
            bgl = int(re.search(r'(\d+) Blue Gem Lock', deposit).group(1))
                
        return wl, dl, bgl

    async def process_donation(self, growid: str, wl: int, dl: int, bgl: int, current_balance: Balance) -> Balance:
        """Process a donation"""
        try:
            # Calculate new balance
            new_balance = Balance(
                current_balance.wl + wl,
                current_balance.dl + dl,
                current_balance.bgl + bgl
            )

            # Update balance menggunakan balance manager
            await self.balance_manager.update_balance(
                growid,
                new_balance,
                TransactionType.DONATION,
                f"Donation: {wl} WL, {dl} DL, {bgl} BGL"
            )

            return new_balance

        except Exception as e:
            self.logger.error(f"Error processing donation: {e}")
            raise

    async def send_error(self, channel: discord.TextChannel, message: str):
        """Kirim pesan error"""
        embed = discord.Embed(
            title="❌ Donasi Gagal",
            description=message,
            color=COLORS['ERROR'],
            timestamp=datetime.utcnow()
        )
        await channel.send(embed=embed)

    async def send_success(self, channel: discord.TextChannel, growid: str, wl: int, dl: int, bgl: int, new_balance: Balance):
        """Kirim pesan sukses"""
        # Hitung total dalam WL
        total_wl = (
            wl + 
            (dl * CURRENCY_RATES['RATES']['DL']) + 
            (bgl * CURRENCY_RATES['RATES']['BGL'])
        )
        
        # Format deposit yang diterima
        deposit_parts = []
        if wl > 0:
            deposit_parts.append(f"{wl:,} WL")
        if dl > 0:
            deposit_parts.append(f"{dl:,} DL")
        if bgl > 0:
            deposit_parts.append(f"{bgl:,} BGL")
        
        deposit_text = " + ".join(deposit_parts)
        
        # Format balance baru
        balance_parts = []
        if new_balance.wl > 0:
            balance_parts.append(f"{new_balance.wl:,} WL")
        if new_balance.dl > 0:
            balance_parts.append(f"{new_balance.dl:,} DL")
        if new_balance.bgl > 0:
            balance_parts.append(f"{new_balance.bgl:,} BGL")
        
        balance_text = " + ".join(balance_parts)
        
        embed = discord.Embed(
            title="✅ Donasi Berhasil",
            color=COLORS['SUCCESS'],
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="👤 GrowID",
            value=f"`{growid}`",
            inline=True
        )
        
        embed.add_field(
            name="💰 Donasi Diterima",
            value=deposit_text,
            inline=True
        )
        
        embed.add_field(
            name="📊 Total Nilai (WL)",
            value=f"{total_wl:,} WL",
            inline=True
        )
        
        embed.add_field(
            name="💳 Balance Baru",
            value=balance_text,
            inline=False
        )
        
        await channel.send(embed=embed)

    async def setup_balance_manager(self, balance_manager):
        """Setup balance manager dependency"""
        self.balance_manager = balance_manager
        self.logger.info("Balance manager setup completed")

    async def setup_donation_channel(self, channel_id: int):
        """Setup donation channel ID"""
        global DONATION_CHANNEL_ID
        DONATION_CHANNEL_ID = channel_id
        self.logger.info(f"Donation channel ID set to: {channel_id}")

    def get_donation_channel_id(self) -> int:
        """Get configured donation channel ID"""
        return DONATION_CHANNEL_ID

    async def is_donation_channel(self, channel_id: int) -> bool:
        """Check if channel is donation channel"""
        return channel_id == DONATION_CHANNEL_ID
