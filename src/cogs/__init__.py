"""
Discord Bot Cogs
"""

from .admin import setup as admin_setup
from .ticket import TicketSystem
from .leveling import setup as leveling_setup
from .reputation import setup as reputation_setup
from .automod import setup as automod_setup
from .stats import setup as stats_setup
from .welcome import setup as welcome_setup
from .help_manager import setup as help_setup

__all__ = [
    'admin_setup',
    'TicketSystem',
    'leveling_setup',
    'reputation_setup',
    'automod_setup',
    'stats_setup',
    'welcome_setup',
    'help_setup'
]
