"""
Ticket System Cog Entry Point
Loads the ticket system from the ticket module
"""

from .ticket.ticket_cog import TicketSystem

async def setup(bot):
    """Setup the Ticket cog"""
    await bot.add_cog(TicketSystem(bot))
