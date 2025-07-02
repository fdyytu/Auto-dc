"""
Ticket System Cog
Main entry point for the ticket system
"""

import discord
from discord.ext import commands, tasks
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict

from .utils.database import TicketDB
from .views.ticket_view import TicketView, TicketControlView, TicketConfirmView
from .components.embeds import TicketEmbeds

logger = logging.getLogger(__name__)

class TicketSystem(commands.Cog):
    """🎫 Advanced Ticket Support System"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = TicketDB()
        self.active_tickets = {}
        self.db.setup_tables()
        self._auto_setup_done = False
        
        # Start auto-close task
        self.auto_close_task.start()
    
    async def auto_setup_ticket_system(self):
        """Auto-setup ticket system from bot config"""
        if self._auto_setup_done:
            return
            
        try:
            # Get bot config
            config = getattr(self.bot, 'config', {})
            
            for guild in self.bot.guilds:
                # Auto-configure ticket settings from config.json
                if self.db.auto_setup_from_config(guild.id, config):
                    logger.info(f"✅ Auto-setup ticket system untuk guild: {guild.name}")
                    
                    # Setup ticket channel jika ada di config
                    ticket_channel_id = config.get('channels', {}).get('ticket_channel')
                    if ticket_channel_id:
                        channel = guild.get_channel(int(ticket_channel_id))
                        if channel:
                            await self._setup_ticket_panel(channel)
                            logger.info(f"✅ Ticket panel setup di channel: {channel.name}")
                        else:
                            logger.warning(f"⚠️  Ticket channel tidak ditemukan: {ticket_channel_id}")
                else:
                    logger.error(f"❌ Gagal auto-setup ticket system untuk guild: {guild.name}")
            
            self._auto_setup_done = True
            
        except Exception as e:
            logger.error(f"❌ Error dalam auto-setup ticket system: {e}")
    
    async def _setup_ticket_panel(self, channel):
        """Setup ticket panel di channel yang ditentukan"""
        try:
            # Cek apakah sudah ada ticket panel
            async for message in channel.history(limit=50):
                if (message.author == self.bot.user and 
                    message.embeds and 
                    "Support Tickets" in message.embeds[0].title):
                    logger.info(f"Ticket panel sudah ada di {channel.name}")
                    return
            
            # Buat ticket panel baru
            embed = discord.Embed(
                title="🎫 Support Tickets",
                description="Klik tombol di bawah untuk membuat ticket support",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="📋 Cara Menggunakan",
                value="• Klik tombol **Create Ticket**\n• Isi alasan ticket Anda\n• Tim support akan membantu Anda",
                inline=False
            )
            
            view = TicketControlView()
            
            # Register view sebagai persistent
            self.bot.add_view(view)
            
            await channel.send(embed=embed, view=view)
            logger.info(f"✅ Ticket panel berhasil dibuat di {channel.name}")
            
        except Exception as e:
            logger.error(f"❌ Error setup ticket panel: {e}")

    async def create_ticket_channel(self, ctx, reason: str, settings: Dict) -> Optional[discord.TextChannel]:
        """Create a new ticket channel"""
        try:
            # Check max tickets
            active_count = self.db.get_active_tickets(str(ctx.guild.id), str(ctx.author.id))
            if active_count >= settings['max_tickets']:
                logger.warning(f"User {ctx.author} mencoba membuat ticket melebihi batas maksimum ({settings['max_tickets']})")
                await ctx.send(embed=TicketEmbeds.error_embed("Anda telah mencapai batas maksimum tiket yang dapat dibuka!"))
                return None

            # Get or create category
            category_id = settings.get('category_id')
            category = None
            
            if category_id:
                channel_obj = ctx.guild.get_channel(int(category_id))
                # Pastikan channel adalah CategoryChannel, bukan TextChannel
                if channel_obj and isinstance(channel_obj, discord.CategoryChannel):
                    category = channel_obj
                else:
                    logger.warning(f"Channel dengan ID {category_id} bukan kategori atau tidak ditemukan")
            
            if not category:
                logger.info(f"Membuat kategori ticket baru untuk guild {ctx.guild.name}")
                category = await ctx.guild.create_category("Tickets")
                self.db.update_settings(str(ctx.guild.id), 'category_id', str(category.id))

            # Create channel
            ticket_number = active_count + 1
            channel_name = settings['ticket_format'].format(
                user=ctx.author.name.lower(),
                number=ticket_number
            )

            # Set permissions
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }

            # Add support role permissions
            if settings['support_role_id']:
                support_role = ctx.guild.get_role(int(settings['support_role_id']))
                if support_role:
                    overwrites[support_role] = discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=True
                    )
                    logger.info(f"Menambahkan permission untuk role support {support_role.name}")
                else:
                    logger.warning(f"Role support dengan ID {settings['support_role_id']} tidak ditemukan")

            # Create channel
            logger.info(f"Membuat channel ticket baru: {channel_name}")
            channel = await category.create_text_channel(
                channel_name,
                overwrites=overwrites
            )

            # Create ticket in database
            ticket_id = self.db.create_ticket(
                str(ctx.guild.id),
                str(channel.id),
                str(ctx.author.id),
                reason
            )

            if ticket_id:
                logger.info(f"Ticket berhasil dibuat dengan ID: {ticket_id}")
                self.active_tickets[channel.id] = ticket_id
                return channel
            
            logger.error(f"Gagal membuat ticket di database untuk channel {channel.name}")
            await channel.delete()
            return None

        except Exception as e:
            logger.error(f"Error saat membuat channel ticket: {str(e)}")
            if 'channel' in locals() and channel:
                await channel.delete()
            return None

    @commands.group(name="ticket")
    async def ticket(self, ctx):
        """🎫 Ticket management commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help(ctx.command)

    @ticket.command(name="setup")
    @commands.has_permissions(administrator=True)
    async def setup_ticket(self, ctx, channel: discord.TextChannel):
        """Setup ticket system in a channel"""
        try:
            logger.info(f"Memulai setup sistem ticket di channel {channel.name} oleh {ctx.author}")
            
            # Cek apakah bot memiliki permission yang diperlukan
            if not channel.permissions_for(ctx.guild.me).send_messages:
                logger.error(f"Bot tidak memiliki permission untuk mengirim pesan di channel {channel.name}")
                await ctx.send(embed=TicketEmbeds.error_embed("Bot tidak memiliki izin untuk mengirim pesan di channel tersebut"))
                return
                
            embed = discord.Embed(
                title="🎫 Support Tickets",
                description="Klik tombol di bawah untuk membuat ticket support",
                color=discord.Color.blue()
            )
            
            view = TicketControlView()
            
            # Register view sebagai persistent
            self.bot.add_view(view)
            
            await channel.send(embed=embed, view=view)
            
            logger.info(f"Setup ticket system berhasil di channel {channel.name}")
            await ctx.send(embed=TicketEmbeds.success_embed(f"Sistem ticket berhasil diatur di {channel.mention}"))
            
        except discord.Forbidden as e:
            logger.error(f"Error permission saat setup ticket di {channel.name}: {str(e)}")
            await ctx.send(embed=TicketEmbeds.error_embed("Bot tidak memiliki izin yang diperlukan"))
        except Exception as e:
            logger.error(f"Error saat setup ticket system: {str(e)}")
            await ctx.send(embed=TicketEmbeds.error_embed("Terjadi kesalahan saat mengatur sistem ticket"))

    @ticket.command(name="create")
    async def create_ticket(self, ctx, *, reason: str = "Tidak ada alasan yang diberikan"):
        """Create a new support ticket"""
        try:
            logger.info(f"Permintaan pembuatan ticket dari {ctx.author} dengan alasan: {reason}")
            
            settings = self.db.get_guild_settings(ctx.guild.id)
            if not settings:
                logger.error(f"Gagal mendapatkan pengaturan guild untuk {ctx.guild.name}")
                await ctx.send(embed=TicketEmbeds.error_embed("Sistem ticket belum dikonfigurasi di server ini"))
                return
            
            channel = await self.create_ticket_channel(ctx, reason, settings)
            if not channel:
                return  # Error sudah di-handle di create_ticket_channel

            # Send initial message with ticket view
            try:
                embed = TicketEmbeds.ticket_created(ctx.author, reason)
                view = TicketView(self.active_tickets[channel.id])
                
                # Register view sebagai persistent
                self.bot.add_view(view)
                
                await channel.send(embed=embed, view=view)
                logger.info(f"Ticket berhasil dibuat di channel {channel.name} oleh {ctx.author}")
            except Exception as e:
                logger.error(f"Error saat mengirim pesan awal di ticket channel: {str(e)}")
                await channel.delete()
                await ctx.send(embed=TicketEmbeds.error_embed("Terjadi kesalahan saat membuat tiket"))
                return
                
        except Exception as e:
            logger.error(f"Error saat membuat ticket: {str(e)}")
            await ctx.send(embed=TicketEmbeds.error_embed("Terjadi kesalahan saat membuat tiket"))

    @ticket.command(name="close")
    async def close_ticket(self, ctx):
        """Close the current ticket"""
        try:
            if ctx.channel.id not in self.active_tickets:
                logger.warning(f"Percobaan menutup non-ticket channel oleh {ctx.author} di {ctx.channel.name}")
                await ctx.send(embed=TicketEmbeds.error_embed("Channel ini bukan ticket channel!"))
                return

            ticket_id = self.active_tickets[ctx.channel.id]
            logger.info(f"Permintaan penutupan ticket (ID: {ticket_id}) oleh {ctx.author}")
            
            # Create confirmation view
            view = TicketConfirmView()
            msg = await ctx.send("Apakah Anda yakin ingin menutup ticket ini?", view=view)

            try:
                interaction = await self.bot.wait_for(
                    "interaction",
                    check=lambda i: i.message.id == msg.id and i.user.id == ctx.author.id,
                    timeout=60.0
                )

                # Pastikan interaction memiliki custom_id sebelum mengaksesnya
                custom_id = interaction.data.get('custom_id') if hasattr(interaction, 'data') and interaction.data else None
                if custom_id == "cancel_ticket":
                    logger.info(f"Penutupan ticket {ticket_id} dibatalkan oleh {ctx.author}")
                    await msg.edit(content="Penutupan ticket dibatalkan.", view=None)
                    return

                # Close the ticket
                try:
                    if self.db.close_ticket(ticket_id, str(ctx.author.id)):
                        logger.info(f"Ticket {ticket_id} berhasil ditutup oleh {ctx.author}")
                        await ctx.send("🔒 Menutup ticket dalam 5 detik...")
                        await asyncio.sleep(5)
                        await ctx.channel.delete()
                        del self.active_tickets[ctx.channel.id]
                    else:
                        logger.error(f"Gagal menutup ticket {ticket_id} di database")
                        await ctx.send(embed=TicketEmbeds.error_embed("Gagal menutup ticket"))
                except Exception as e:
                    logger.error(f"Error saat menutup ticket {ticket_id}: {str(e)}")
                    await ctx.send(embed=TicketEmbeds.error_embed("Terjadi kesalahan saat menutup ticket"))

            except asyncio.TimeoutError:
                logger.info(f"Timeout pada konfirmasi penutupan ticket {ticket_id}")
                await msg.edit(content="Waktu konfirmasi penutupan ticket habis.", view=None)

        except Exception as e:
            logger.error(f"Error tidak terduga saat proses penutupan ticket: {str(e)}")
            await ctx.send(embed=TicketEmbeds.error_embed("Terjadi kesalahan saat memproses penutupan ticket"))

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Handle button interactions"""
        # Log semua interaction untuk debugging
        logger.debug(f"Interaction received from {interaction.user}: type={interaction.type}, custom_id={interaction.data.get('custom_id', 'NONE') if hasattr(interaction, 'data') and interaction.data else 'NONE'}")
        
        # Hanya proses button interactions
        if interaction.type != discord.InteractionType.component:
            logger.debug(f"Skipping non-component interaction from {interaction.user}")
            return
            
        # Pastikan custom_id ada dengan pengecekan yang lebih robust
        custom_id = interaction.data.get('custom_id') if hasattr(interaction, 'data') and interaction.data else None
        if not custom_id:
            logger.warning(f"Interaksi dari {interaction.user} tidak memiliki custom_id. Type: {interaction.type}, Data: {getattr(interaction, 'data', {})}")
            try:
                await interaction.response.send_message(
                    embed=TicketEmbeds.error_embed("Terjadi kesalahan dengan tombol ini. Silakan coba lagi."),
                    ephemeral=True
                )
            except:
                pass  # Ignore jika sudah ada response
            return

        logger.info(f"Processing interaction with custom_id: {custom_id} from {interaction.user}")

        # Handle create ticket button - langsung buat channel tanpa modal
        if custom_id == "create_ticket":
            logger.info(f"Tombol create_ticket ditekan oleh: {interaction.user} (ID: {interaction.user.id})")
            try:
                # Get guild settings
                settings = self.db.get_guild_settings(interaction.guild_id)
                
                # Create a mock context object for create_ticket_channel
                class MockContext:
                    def __init__(self, interaction):
                        self.guild = interaction.guild
                        self.author = interaction.user
                        self.send = interaction.followup.send
                
                mock_ctx = MockContext(interaction)
                
                # Use default reason since we're not using modal
                default_reason = "Support diperlukan"
                
                # Create ticket channel directly
                channel = await self.create_ticket_channel(mock_ctx, default_reason, settings)
                if not channel:
                    logger.error(f"Gagal membuat ticket untuk {interaction.user} (ID: {interaction.user.id})")
                    await interaction.response.send_message(
                        embed=TicketEmbeds.error_embed("Gagal membuat tiket"),
                        ephemeral=True
                    )
                    return

                # Send initial message with ticket view
                embed = TicketEmbeds.ticket_created(interaction.user, default_reason)
                view = TicketView(self.active_tickets[channel.id])
                
                # Register view sebagai persistent
                self.bot.add_view(view)
                
                await channel.send(embed=embed, view=view)
                
                logger.info(f"Ticket berhasil dibuat oleh {interaction.user} di channel {channel.name}")
                await interaction.response.send_message(
                    embed=TicketEmbeds.success_embed(f"Tiket berhasil dibuat di {channel.mention}"),
                    ephemeral=True
                )
            except Exception as e:
                logger.error(f"Error saat membuat ticket: {str(e)}")
                try:
                    await interaction.response.send_message(
                        embed=TicketEmbeds.error_embed("Terjadi kesalahan saat membuat tiket"),
                        ephemeral=True
                    )
                except:
                    pass
            return

        # Handle close ticket button
        if custom_id.startswith("close_ticket_"):
            try:
                ticket_id = int(custom_id.split("_")[-1])
                logger.info(f"Tombol close_ticket ditekan oleh: {interaction.user} (ID: {interaction.user.id}) untuk ticket ID: {ticket_id}")
                channel = interaction.channel
                
                if channel.id not in self.active_tickets:
                    logger.warning(f"Close ticket gagal: Ticket channel {channel.id} tidak ditemukan di active_tickets")
                    await interaction.response.send_message(
                        embed=TicketEmbeds.error_embed("Tiket ini sudah tertutup!"),
                        ephemeral=True
                    )
                    return

                if self.db.close_ticket(ticket_id, str(interaction.user.id)):
                    logger.info(f"Ticket dengan ID {ticket_id} berhasil ditutup oleh {interaction.user}")
                    await interaction.response.send_message("🔒 Menutup ticket dalam 5 detik...")
                    await asyncio.sleep(5)
                    await channel.delete()
                    del self.active_tickets[channel.id]
                else:
                    logger.error(f"Gagal menutup ticket dengan ID {ticket_id} oleh {interaction.user}")
                    await interaction.response.send_message(
                        embed=TicketEmbeds.error_embed("Gagal menutup tiket"),
                        ephemeral=True
                    )
            except ValueError as e:
                logger.error(f"Error parsing ticket_id dari custom_id {custom_id}: {e}")
                await interaction.response.send_message(
                    embed=TicketEmbeds.error_embed("ID tiket tidak valid"),
                    ephemeral=True
                )
            except Exception as e:
                logger.error(f"Error saat menutup ticket: {str(e)}")
                try:
                    await interaction.response.send_message(
                        embed=TicketEmbeds.error_embed("Terjadi kesalahan saat menutup tiket"),
                        ephemeral=True
                    )
                except:
                    pass
            return
        
        # Handle confirm/cancel buttons
        if custom_id in ["confirm_ticket", "cancel_ticket"]:
            logger.info(f"Tombol {custom_id} ditekan oleh: {interaction.user}")
            # These are handled by the wait_for in close_ticket command
            return
        
        # Log unhandled custom_id
        logger.warning(f"Unhandled custom_id: {custom_id} dari {interaction.user}")


    async def register_persistent_views(self):
        """Register persistent views untuk memastikan views tetap aktif setelah restart"""
        try:
            # Register TicketControlView
            self.bot.add_view(TicketControlView())
            logger.info("✅ TicketControlView berhasil diregistrasi sebagai persistent view")
            
            # Register TicketView untuk setiap active ticket
            for channel_id, ticket_id in self.active_tickets.items():
                view = TicketView(ticket_id)
                self.bot.add_view(view)
                logger.info(f"✅ TicketView untuk ticket {ticket_id} berhasil diregistrasi")
                
        except Exception as e:
            logger.error(f"❌ Error saat registrasi persistent views: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        """Auto-setup ticket system saat bot ready"""
        if not self._auto_setup_done:
            await asyncio.sleep(2)  # Tunggu sebentar agar bot fully ready
            await self.auto_setup_ticket_system()
            
        # Register persistent views
        await self.register_persistent_views()
    
    @ticket.command(name="autosetup")
    @commands.has_permissions(administrator=True)
    async def auto_setup_command(self, ctx):
        """Manually trigger auto-setup ticket system"""
        await ctx.send("🔄 Memulai auto-setup ticket system...")
        
        self._auto_setup_done = False  # Reset flag
        await self.auto_setup_ticket_system()
        
        await ctx.send("✅ Auto-setup ticket system selesai!")

    @tasks.loop(hours=1)  # Cek setiap jam
    async def auto_close_task(self):
        """Background task untuk auto-close ticket yang sudah expired"""
        try:
            expired_tickets = self.db.get_expired_tickets()
            
            if not expired_tickets:
                return
                
            logger.info(f"🔍 Ditemukan {len(expired_tickets)} ticket yang perlu ditutup otomatis")
            
            for ticket in expired_tickets:
                try:
                    guild = self.bot.get_guild(int(ticket['guild_id']))
                    if not guild:
                        logger.warning(f"Guild {ticket['guild_id']} tidak ditemukan untuk ticket {ticket['id']}")
                        continue
                        
                    channel = guild.get_channel(int(ticket['channel_id']))
                    if not channel:
                        logger.warning(f"Channel {ticket['channel_id']} tidak ditemukan untuk ticket {ticket['id']}")
                        # Tutup ticket di database meskipun channel tidak ada
                        self.db.auto_close_ticket(ticket['id'])
                        continue
                    
                    # Kirim pesan peringatan sebelum menutup
                    embed = discord.Embed(
                        title="🕐 Ticket Auto-Close",
                        description=f"Ticket ini akan ditutup otomatis karena tidak ada aktivitas selama {ticket['auto_close_hours']} jam.",
                        color=discord.Color.orange()
                    )
                    embed.add_field(
                        name="📝 Alasan Ticket",
                        value=ticket['reason'] or "Tidak ada alasan",
                        inline=False
                    )
                    embed.add_field(
                        name="⏰ Dibuat pada",
                        value=ticket['created_at'],
                        inline=True
                    )
                    
                    await channel.send(embed=embed)
                    await asyncio.sleep(2)
                    
                    # Tutup ticket di database
                    if self.db.auto_close_ticket(ticket['id']):
                        logger.info(f"✅ Ticket {ticket['id']} berhasil ditutup otomatis")
                        
                        # Hapus dari active_tickets jika ada
                        if channel.id in self.active_tickets:
                            del self.active_tickets[channel.id]
                        
                        # Hapus channel
                        await channel.delete()
                        logger.info(f"🗑️ Channel {channel.name} berhasil dihapus")
                    else:
                        logger.error(f"❌ Gagal menutup ticket {ticket['id']} di database")
                        
                except Exception as e:
                    logger.error(f"❌ Error saat auto-close ticket {ticket['id']}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Error dalam auto_close_task: {e}")

    @auto_close_task.before_loop
    async def before_auto_close_task(self):
        """Wait until bot is ready before starting auto-close task"""
        await self.bot.wait_until_ready()
        logger.info("🚀 Auto-close task dimulai")

    def cog_unload(self):
        """Cleanup saat cog di-unload"""
        self.auto_close_task.cancel()
        logger.info("🛑 Auto-close task dihentikan")

    @ticket.command(name="settings")
    @commands.has_permissions(administrator=True)
    async def ticket_settings(self, ctx, auto_close_hours: int = None):
        """Atur pengaturan ticket termasuk auto-close timer"""
        if auto_close_hours is not None:
            if auto_close_hours < 0:
                await ctx.send(embed=TicketEmbeds.error_embed("Auto-close hours tidak boleh negatif. Gunakan 0 untuk menonaktifkan auto-close."))
                return
                
            if self.db.update_settings(str(ctx.guild.id), 'auto_close_hours', str(auto_close_hours)):
                if auto_close_hours == 0:
                    await ctx.send(embed=TicketEmbeds.success_embed("✅ Auto-close ticket dinonaktifkan"))
                else:
                    await ctx.send(embed=TicketEmbeds.success_embed(f"✅ Auto-close ticket diatur ke {auto_close_hours} jam"))
            else:
                await ctx.send(embed=TicketEmbeds.error_embed("❌ Gagal mengupdate pengaturan"))
        else:
            # Tampilkan pengaturan saat ini
            settings = self.db.get_guild_settings(ctx.guild.id)
            embed = discord.Embed(
                title="🎫 Pengaturan Ticket",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="⏰ Auto-Close",
                value=f"{settings.get('auto_close_hours', 48)} jam" if settings.get('auto_close_hours', 48) > 0 else "Dinonaktifkan",
                inline=True
            )
            embed.add_field(
                name="🎯 Max Tickets per User",
                value=settings.get('max_tickets', 1),
                inline=True
            )
            embed.add_field(
                name="📝 Format Ticket",
                value=settings.get('ticket_format', 'ticket-{user}-{number}'),
                inline=False
            )
            
            await ctx.send(embed=embed)

async def setup(bot):
    """Setup the Ticket cog"""
    await bot.add_cog(TicketSystem(bot))
