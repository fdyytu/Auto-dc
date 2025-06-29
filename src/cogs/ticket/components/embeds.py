"""
Ticket Embeds
Contains all the embed templates for the ticket system
"""

import discord
from datetime import datetime
from typing import Optional

class TicketEmbeds:
    @staticmethod
    def ticket_created(author: discord.Member, reason: str) -> discord.Embed:
        """Create embed for new ticket"""
        embed = discord.Embed(
            title="🎫 Support Ticket",
            description=f"Ticket created by {author.mention}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Reason", value=reason)
        embed.add_field(
            name="Instructions", 
            value="Click the 🔒 button below to close the ticket\nSupport team will assist you shortly.",
            inline=False
        )
        return embed

    @staticmethod
    def ticket_closed(closed_by: discord.Member, duration: str) -> discord.Embed:
        """Create embed for closed ticket"""
        embed = discord.Embed(
            title="🔒 Ticket Closed",
            description=f"Ticket closed by {closed_by.mention}",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="Duration", value=duration)
        return embed

    @staticmethod
    def ticket_settings(
        guild: discord.Guild,
        support_role: Optional[discord.Role],
        log_channel: Optional[discord.TextChannel],
        category: Optional[discord.CategoryChannel],
        settings: dict
    ) -> discord.Embed:
        """Create embed for ticket settings"""
        embed = discord.Embed(
            title="⚙️ Ticket System Settings",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        
        embed.add_field(
            name="Support Role",
            value=support_role.mention if support_role else "Not set",
            inline=False
        )
        embed.add_field(
            name="Log Channel",
            value=log_channel.mention if log_channel else "Not set",
            inline=False
        )
        embed.add_field(
            name="Ticket Category",
            value=category.name if category else "Not set",
            inline=False
        )
        embed.add_field(
            name="Max Tickets per User",
            value=settings['max_tickets'],
            inline=True
        )
        embed.add_field(
            name="Ticket Format",
            value=f"`{settings['ticket_format']}`",
            inline=True
        )
        embed.add_field(
            name="Auto Close Hours",
            value=settings['auto_close_hours'],
            inline=True
        )
        
        return embed

    @staticmethod
    def error_embed(message: str) -> discord.Embed:
        """Create error embed"""
        return discord.Embed(
            title="❌ Error",
            description=message,
            color=discord.Color.red()
        )

    @staticmethod
    def success_embed(message: str) -> discord.Embed:
        """Create success embed"""
        return discord.Embed(
            title="✅ Success",
            description=message,
            color=discord.Color.green()
        )
