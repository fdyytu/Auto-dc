"""
Ticket System Module
"""

from .ticket_cog import TicketSystem

__all__ = ['TicketSystem']

async def setup(bot):
    """Setup the Ticket cog"""
    await bot.add_cog(TicketSystem(bot))
