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
        
        # Add close button
        close_button = Button(
            style=discord.ButtonStyle.danger,
            emoji="🔒",
            label="Close Ticket",
            custom_id=f"close_ticket_{ticket_id}"
        )
        self.add_item(close_button)

class TicketControlView(View):
    def __init__(self):
        super().__init__(timeout=None)
        
        # Create ticket button
        create_button = Button(
            style=discord.ButtonStyle.primary,
            emoji="🎫",
            label="Create Ticket",
            custom_id="create_ticket"
        )
        self.add_item(create_button)

class TicketConfirmView(View):
    def __init__(self):
        super().__init__(timeout=60.0)  # 60 second timeout
        
        # Add confirm/cancel buttons
        confirm_button = Button(
            style=discord.ButtonStyle.success,
            emoji="✅",
            label="Confirm",
            custom_id="confirm_ticket"
        )
        cancel_button = Button(
            style=discord.ButtonStyle.danger,
            emoji="❌",
            label="Cancel",
            custom_id="cancel_ticket"
        )
        
        self.add_item(confirm_button)
        self.add_item(cancel_button)
