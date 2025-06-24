"""
Leveling Data Repository
Author: fdyytu
Created at: 2025-03-07 22:35:08 UTC
Last Modified: 2025-03-12 02:51:46 UTC
"""

import sqlite3
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from database import get_connection

logger = logging.getLogger(__name__)

class LevelingRepository:
    """Repository untuk data leveling system"""
    
    def __init__(self):
        self.logger = logger
        self.setup_tables()

    def setup_tables(self):
        """Setup necessary database tables"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # User levels table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_levels (
                    guild_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 0,
                    messages INTEGER DEFAULT 0,
                    last_message TIMESTAMP,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)
            
            # Level rewards table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS level_rewards (
                    guild_id TEXT NOT NULL,
                    level INTEGER NOT NULL,
                    role_id TEXT NOT NULL,
                    PRIMARY KEY (guild_id, level)
                )
            """)
            
            # Leveling settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leveling_settings (
                    guild_id TEXT PRIMARY KEY,
                    enabled BOOLEAN DEFAULT TRUE,
                    announcement_channel TEXT,
                    min_xp INTEGER DEFAULT 15,
                    max_xp INTEGER DEFAULT 25,
                    cooldown INTEGER DEFAULT 60,
                    stack_rewards BOOLEAN DEFAULT TRUE,
                    ignored_channels TEXT,
                    ignored_roles TEXT,
                    double_xp_roles TEXT
                )
            """)
            
            conn.commit()
            logger.info("Leveling tables created successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to setup leveling tables: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def get_user_level_data(self, guild_id: int, user_id: int) -> Optional[Dict]:
        """Get user level data"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM user_levels 
                WHERE guild_id = ? AND user_id = ?
            """, (str(guild_id), str(user_id)))
            
            data = cursor.fetchone()
            return dict(data) if data else None
            
        except sqlite3.Error as e:
            logger.error(f"Error getting user level data: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def update_user_xp(self, guild_id: int, user_id: int, xp_gain: int) -> Tuple[int, int, bool]:
        """Update user XP and return (new_xp, new_level, level_up)"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get current data
            cursor.execute("""
                SELECT xp, level, messages FROM user_levels 
                WHERE guild_id = ? AND user_id = ?
            """, (str(guild_id), str(user_id)))
            
            data = cursor.fetchone()
            
            if data:
                current_xp = data['xp']
                current_level = data['level']
                messages = data['messages']
            else:
                current_xp = 0
                current_level = 0
                messages = 0
            
            # Calculate new values
            new_xp = current_xp + xp_gain
            new_level = self._calculate_level(new_xp)
            level_up = new_level > current_level
            new_messages = messages + 1
            
            # Update or insert
            cursor.execute("""
                INSERT OR REPLACE INTO user_levels 
                (guild_id, user_id, xp, level, messages, last_message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (str(guild_id), str(user_id), new_xp, new_level, new_messages, datetime.utcnow()))
            
            conn.commit()
            return new_xp, new_level, level_up
            
        except sqlite3.Error as e:
            logger.error(f"Error updating user XP: {e}")
            if conn:
                conn.rollback()
            return 0, 0, False
        finally:
            if conn:
                conn.close()

    def get_leaderboard(self, guild_id: int, limit: int = 10) -> List[Dict]:
        """Get leaderboard for guild"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, xp, level, messages 
                FROM user_levels 
                WHERE guild_id = ? 
                ORDER BY xp DESC 
                LIMIT ?
            """, (str(guild_id), limit))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_user_rank(self, guild_id: int, user_id: int) -> Optional[int]:
        """Get user rank in guild"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) + 1 as rank
                FROM user_levels 
                WHERE guild_id = ? AND xp > (
                    SELECT COALESCE(xp, 0) FROM user_levels 
                    WHERE guild_id = ? AND user_id = ?
                )
            """, (str(guild_id), str(guild_id), str(user_id)))
            
            result = cursor.fetchone()
            return result['rank'] if result else None
            
        except sqlite3.Error as e:
            logger.error(f"Error getting user rank: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def get_settings(self, guild_id: int) -> Dict:
        """Get leveling settings for guild"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM leveling_settings WHERE guild_id = ?
            """, (str(guild_id),))
            
            data = cursor.fetchone()
            if data:
                return dict(data)
            else:
                # Return default settings
                return {
                    'guild_id': str(guild_id),
                    'enabled': True,
                    'announcement_channel': None,
                    'min_xp': 15,
                    'max_xp': 25,
                    'cooldown': 60,
                    'stack_rewards': True,
                    'ignored_channels': '',
                    'ignored_roles': '',
                    'double_xp_roles': ''
                }
                
        except sqlite3.Error as e:
            logger.error(f"Error getting settings: {e}")
            return {}
        finally:
            if conn:
                conn.close()

    def update_settings(self, guild_id: int, settings: Dict) -> bool:
        """Update leveling settings"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO leveling_settings 
                (guild_id, enabled, announcement_channel, min_xp, max_xp, 
                 cooldown, stack_rewards, ignored_channels, ignored_roles, double_xp_roles)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(guild_id),
                settings.get('enabled', True),
                settings.get('announcement_channel'),
                settings.get('min_xp', 15),
                settings.get('max_xp', 25),
                settings.get('cooldown', 60),
                settings.get('stack_rewards', True),
                settings.get('ignored_channels', ''),
                settings.get('ignored_roles', ''),
                settings.get('double_xp_roles', '')
            ))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error updating settings: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def get_level_rewards(self, guild_id: int, level: int = None) -> List[Dict]:
        """Get level rewards"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            if level is not None:
                cursor.execute("""
                    SELECT role_id FROM level_rewards
                    WHERE guild_id = ? AND level <= ?
                    ORDER BY level DESC
                """, (str(guild_id), level))
            else:
                cursor.execute("""
                    SELECT level, role_id FROM level_rewards
                    WHERE guild_id = ?
                    ORDER BY level ASC
                """, (str(guild_id),))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            logger.error(f"Error getting level rewards: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def add_level_reward(self, guild_id: int, level: int, role_id: int) -> bool:
        """Add level reward"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO level_rewards 
                (guild_id, level, role_id)
                VALUES (?, ?, ?)
            """, (str(guild_id), level, str(role_id)))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error adding level reward: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def remove_level_reward(self, guild_id: int, level: int) -> bool:
        """Remove level reward"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM level_rewards 
                WHERE guild_id = ? AND level = ?
            """, (str(guild_id), level))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error removing level reward: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def _calculate_level(self, xp: int) -> int:
        """Calculate level from XP"""
        # Formula: level = floor(sqrt(xp / 100))
        # This means: level 1 = 100 XP, level 2 = 400 XP, level 3 = 900 XP, etc.
        import math
        return int(math.sqrt(xp / 100))

    def get_xp_for_level(self, level: int) -> int:
        """Get XP required for a specific level"""
        return level * level * 100

    def get_xp_for_next_level(self, current_xp: int) -> int:
        """Get XP required for next level"""
        current_level = self._calculate_level(current_xp)
        next_level = current_level + 1
        return self.get_xp_for_level(next_level)
