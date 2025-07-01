"""
Ticket Views
Contains all the views/UI components for the ticket system
"""

import discord
from discord.ui import View, Button
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class TicketView(View):
    def __init__(self, ticket_id: int):
        super().__init__(timeout=None)
        self.ticket_id = ticket_id
        
        # Add close button with dynamic custom_id
        close_button = Button(
            style=discord.ButtonStyle.danger,
            emoji="🔒",
            label="Close Ticket",
            custom_id=f"close_ticket_{ticket_id}"
        )
        close_button.callback = self.close_ticket_callback
        self.add_item(close_button)
    
    async def close_ticket_callback(self, interaction: discord.Interaction):
        """Handle close ticket button click"""
        logger.info(f"Close ticket button clicked by {interaction.user} (custom_id: {interaction.custom_id})")
        # The actual handling will be done by the cog's on_interaction listener

class TicketControlView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(
        style=discord.ButtonStyle.primary,
        emoji="🎫",
        label="Create Ticket",
        custom_id="create_ticket"
    )
    async def create_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle create ticket button click"""
        # This will be handled by the cog's on_interaction listener
        logger.info(f"Create ticket button clicked by {interaction.user} (custom_id: {interaction.custom_id})")

class TicketConfirmView(View):
    def __init__(self):
        super().__init__(timeout=60.0)  # 60 second timeout
    
    @discord.ui.button(
        style=discord.ButtonStyle.success,
        emoji="✅",
        label="Confirm",
        custom_id="confirm_ticket"
    )
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle confirm button click"""
        logger.info(f"Confirm ticket button clicked by {interaction.user} (custom_id: {interaction.custom_id})")
    
    @discord.ui.button(
        style=discord.ButtonStyle.danger,
        emoji="❌",
        label="Cancel",
        custom_id="cancel_ticket"
    )
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle cancel button click"""
        logger.info(f"Cancel ticket button clicked by {interaction.user} (custom_id: {interaction.custom_id})")
