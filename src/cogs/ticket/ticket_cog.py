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

            if interaction.custom_id == "cancel_ticket":
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
        if not interaction.custom_id:
            return

        # Handle create ticket button
        if interaction.custom_id == "create_ticket":
            modal = discord.ui.Modal(title="Create Ticket")
            modal.add_item(
                discord.ui.TextInput(
                    label="Reason",
                    placeholder="Enter the reason for your ticket",
                    required=True,
                    max_length=1000
                )
            )
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
        if not interaction.custom_id == "create_ticket":
            return

        reason = interaction.data["components"][0]["components"][0]["value"]
        settings = self.db.get_guild_settings(interaction.guild_id)
        
        # Create ticket channel
        channel = await self.create_ticket_channel(interaction, reason, settings)
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

async def setup(bot):
    """Setup the Ticket cog"""
    await bot.add_cog(TicketSystem(bot))
