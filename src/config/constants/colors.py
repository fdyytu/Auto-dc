"""
Color constants untuk Discord embeds
Author: fdyytu
Created at: 2025-03-07 18:04:56 UTC
Last Modified: 2025-03-10 10:09:16 UTC
"""

import discord

# Colors untuk Discord embeds
class COLORS:
    """Color constants untuk Discord embeds"""
    # Basic Colors
    PRIMARY = discord.Color.blue()
    SUCCESS = discord.Color.green()
    WARNING = discord.Color.orange()
    ERROR = discord.Color.red()
    INFO = discord.Color.blurple()
    
    # Custom Colors
    GOLD = discord.Color.gold()
    PURPLE = discord.Color.purple()
    TEAL = discord.Color.teal()
    DARK_BLUE = discord.Color.dark_blue()
    DARK_GREEN = discord.Color.dark_green()
    DARK_RED = discord.Color.dark_red()
    
    # Shop Colors
    SHOP = discord.Color.from_rgb(0, 255, 127)  # Spring Green
    PURCHASE = discord.Color.from_rgb(255, 215, 0)  # Gold
    BALANCE = discord.Color.from_rgb(0, 191, 255)  # Deep Sky Blue
    TRANSACTION = discord.Color.from_rgb(138, 43, 226)  # Blue Violet
    
    # Status Colors
    ONLINE = discord.Color.green()
    OFFLINE = discord.Color.red()
    IDLE = discord.Color.orange()
    DND = discord.Color.red()
    
    # Level Colors
    LEVEL_UP = discord.Color.gold()
    REPUTATION = discord.Color.purple()
    
    @classmethod
    def get_status_color(cls, status: str) -> discord.Color:
        """Get color based on status"""
        status_colors = {
            'online': cls.ONLINE,
            'offline': cls.OFFLINE,
            'idle': cls.IDLE,
            'dnd': cls.DND,
            'success': cls.SUCCESS,
            'error': cls.ERROR,
            'warning': cls.WARNING,
            'info': cls.INFO
        }
        return status_colors.get(status.lower(), cls.INFO)
