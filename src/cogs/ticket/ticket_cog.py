"""
Ticket System Cog
Main entry point for the ticket system
"""

import discord
from discord.ext import commands
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
            await channel.send(embed=embed, view=view)
            logger.info(f"✅ Ticket panel berhasil dibuat di {channel.name}")
            
        except Exception as e:
            logger.error(f"❌ Error setup ticket panel: {e}")

    async def create_ticket_channel(self, ctx, reason: str, settings: Dict) -> Optional[discord.TextChannel]:
        """Create a new ticket channel"""
        # Check max tickets
        active_count = self.db.get_active_tickets(str(ctx.guild.id), str(ctx.author.id))
        if active_count >= settings['max_tickets']:
            await ctx.send(embed=TicketEmbeds.error_embed("You have reached the maximum number of open tickets!"))
            return None

        # Get or create category
        category_id = settings.get('category_id')
        category = ctx.guild.get_channel(int(category_id)) if category_id else None
        
        if not category:
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

        # Create channel
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
            self.active_tickets[channel.id] = ticket_id
            return channel
        
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
        embed = discord.Embed(
            title="🎫 Support Tickets",
            description="Click the button below to create a support ticket",
            color=discord.Color.blue()
        )
        
        view = TicketControlView()
        await channel.send(embed=embed, view=view)
        await ctx.send(embed=TicketEmbeds.success_embed(f"Ticket system setup in {channel.mention}"))

    @ticket.command(name="create")
    async def create_ticket(self, ctx, *, reason: str = "No reason provided"):
        """Create a new support ticket"""
        settings = self.db.get_guild_settings(ctx.guild.id)
        
        channel = await self.create_ticket_channel(ctx, reason, settings)
        if not channel:
            return

        # Send initial message with ticket view
        embed = TicketEmbeds.ticket_created(ctx.author, reason)
        view = TicketView(self.active_tickets[channel.id])
        await channel.send(embed=embed, view=view)

    @ticket.command(name="close")
    async def close_ticket(self, ctx):
        """Close the current ticket"""
        if ctx.channel.id not in self.active_tickets:
            await ctx.send(embed=TicketEmbeds.error_embed("This is not a ticket channel!"))
            return

        ticket_id = self.active_tickets[ctx.channel.id]
        
        # Create confirmation view
        view = TicketConfirmView()
        msg = await ctx.send("Are you sure you want to close this ticket?", view=view)

        try:
            interaction = await self.bot.wait_for(
                "interaction",
                check=lambda i: i.message.id == msg.id and i.user.id == ctx.author.id,
                timeout=60.0
            )

            # Pastikan interaction memiliki custom_id sebelum mengaksesnya
            custom_id = getattr(interaction, 'custom_id', None)
            if custom_id == "cancel_ticket":
                await msg.edit(content="Ticket closure cancelled.", view=None)
                return

            # Close the ticket
            if self.db.close_ticket(ticket_id, str(ctx.author.id)):
                await ctx.send("🔒 Closing ticket in 5 seconds...")
                await asyncio.sleep(5)
                await ctx.channel.delete()
                del self.active_tickets[ctx.channel.id]
            else:
                await ctx.send(embed=TicketEmbeds.error_embed("Failed to close ticket"))

        except asyncio.TimeoutError:
            await msg.edit(content="Ticket closure timed out.", view=None)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Handle button interactions"""
        # Hanya proses component interactions (button, select menu, dll)
        if interaction.type != discord.InteractionType.component:
            return
            
        # Pastikan custom_id ada dan tidak kosong
        if not getattr(interaction, 'custom_id', None):
            return

        # Handle create ticket button
        if interaction.custom_id == "create_ticket":
            # Create a simple modal for ticket creation
            class TicketModal(discord.ui.Modal):
                def __init__(self):
                    super().__init__(title="Create Ticket", custom_id="create_ticket")
                    
                    self.reason_input = discord.ui.TextInput(
                        label="Reason",
                        placeholder="Enter the reason for your ticket",
                        required=True,
                        max_length=1000,
                        style=discord.TextStyle.paragraph
                    )
                    self.add_item(self.reason_input)
                
                async def on_submit(self, interaction: discord.Interaction):
                    # This will be handled by on_modal_submit
                    pass
            
            modal = TicketModal()
            await interaction.response.send_modal(modal)
            return

        # Handle close ticket button
        if interaction.custom_id.startswith("close_ticket_"):
            ticket_id = int(interaction.custom_id.split("_")[-1])
            channel = interaction.channel
            
            if channel.id not in self.active_tickets:
                await interaction.response.send_message(
                    embed=TicketEmbeds.error_embed("This ticket is already closed!"),
                    ephemeral=True
                )
                return

            if self.db.close_ticket(ticket_id, str(interaction.user.id)):
                await interaction.response.send_message("🔒 Closing ticket in 5 seconds...")
                await asyncio.sleep(5)
                await channel.delete()
                del self.active_tickets[channel.id]
            else:
                await interaction.response.send_message(
                    embed=TicketEmbeds.error_embed("Failed to close ticket"),
                    ephemeral=True
                )

    @commands.Cog.listener()
    async def on_modal_submit(self, interaction: discord.Interaction):
        """Handle modal submissions"""
        # Hanya proses modal submit interactions
        if interaction.type != discord.InteractionType.modal_submit:
            return
            
        # Pastikan custom_id ada dan sesuai
        if not getattr(interaction, 'custom_id', None) or interaction.custom_id != "create_ticket":
            return

        # Get reason from modal data
        try:
            reason = interaction.data["components"][0]["components"][0]["value"]
        except (KeyError, IndexError):
            reason = "No reason provided"
        
        settings = self.db.get_guild_settings(interaction.guild_id)
        
        # Create a mock context object for create_ticket_channel
        class MockContext:
            def __init__(self, interaction):
                self.guild = interaction.guild
                self.author = interaction.user
                self.send = interaction.followup.send
        
        mock_ctx = MockContext(interaction)
        
        # Create ticket channel
        channel = await self.create_ticket_channel(mock_ctx, reason, settings)
        if not channel:
            await interaction.response.send_message(
                embed=TicketEmbeds.error_embed("Failed to create ticket"),
                ephemeral=True
            )
            return

        # Send initial message with ticket view
        embed = TicketEmbeds.ticket_created(interaction.user, reason)
        view = TicketView(self.active_tickets[channel.id])
        await channel.send(embed=embed, view=view)
        
        await interaction.response.send_message(
            embed=TicketEmbeds.success_embed(f"Ticket created in {channel.mention}"),
            ephemeral=True
        )
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Auto-setup ticket system saat bot ready"""
        if not self._auto_setup_done:
            await asyncio.sleep(2)  # Tunggu sebentar agar bot fully ready
            await self.auto_setup_ticket_system()
    
    @ticket.command(name="autosetup")
    @commands.has_permissions(administrator=True)
    async def auto_setup_command(self, ctx):
        """Manually trigger auto-setup ticket system"""
        await ctx.send("🔄 Memulai auto-setup ticket system...")
        
        self._auto_setup_done = False  # Reset flag
        await self.auto_setup_ticket_system()
        
        await ctx.send("✅ Auto-setup ticket system selesai!")

async def setup(bot):
    """Setup the Ticket cog"""
    await bot.add_cog(TicketSystem(bot))
