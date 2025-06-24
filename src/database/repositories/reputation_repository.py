"""
Reputation Data Repository
Author: fdyytu
Created at: 2025-03-07 22:35:08 UTC
Last Modified: 2025-03-12 02:51:46 UTC
"""

import sqlite3
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from database import get_connection

logger = logging.getLogger(__name__)

class ReputationRepository:
    """Repository untuk data reputation system"""
    
    def __init__(self):
        self.logger = logger
        self.setup_tables()

    def setup_tables(self):
        """Setup necessary database tables"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Reputation settings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reputation_settings (
                    guild_id TEXT PRIMARY KEY,
                    cooldown INTEGER DEFAULT 43200,
                    max_daily INTEGER DEFAULT 3,
                    min_message_age INTEGER DEFAULT 1800,
                    required_role TEXT,
                    blacklisted_roles TEXT,
                    log_channel TEXT,
                    auto_roles TEXT,
                    stack_roles BOOLEAN DEFAULT FALSE,
                    decay_enabled BOOLEAN DEFAULT FALSE,
                    decay_days INTEGER DEFAULT 30
                )
            """)
            
            # User reputation
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_reputation (
                    user_id TEXT,
                    guild_id TEXT,
                    reputation INTEGER DEFAULT 0,
                    total_given INTEGER DEFAULT 0,
                    total_received INTEGER DEFAULT 0,
                    last_given DATETIME,
                    last_received DATETIME,
                    PRIMARY KEY (user_id, guild_id)
                )
            """)
            
            # Reputation history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reputation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    giver_id TEXT NOT NULL,
                    receiver_id TEXT NOT NULL,
                    message_id TEXT,
                    reason TEXT,
                    amount INTEGER DEFAULT 1,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Reputation roles
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reputation_roles (
                    guild_id TEXT,
                    reputation INTEGER,
                    role_id TEXT,
                    PRIMARY KEY (guild_id, reputation)
                )
            """)
            
            conn.commit()
            logger.info("Reputation tables created successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Failed to setup reputation tables: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                conn.close()

    def get_settings(self, guild_id: int) -> Dict:
        """Get reputation settings for guild"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM reputation_settings WHERE guild_id = ?
            """, (str(guild_id),))
            
            data = cursor.fetchone()
            if data:
                return dict(data)
            else:
                # Return default settings
                return {
                    'guild_id': str(guild_id),
                    'cooldown': 43200,  # 12 hours
                    'max_daily': 3,
                    'min_message_age': 1800,  # 30 minutes
                    'required_role': None,
                    'blacklisted_roles': '',
                    'log_channel': None,
                    'auto_roles': '',
                    'stack_roles': False,
                    'decay_enabled': False,
                    'decay_days': 30
                }
                
        except sqlite3.Error as e:
            logger.error(f"Error getting reputation settings: {e}")
            return {}
        finally:
            if conn:
                conn.close()

    def update_settings(self, guild_id: int, settings: Dict) -> bool:
        """Update reputation settings"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO reputation_settings 
                (guild_id, cooldown, max_daily, min_message_age, required_role, 
                 blacklisted_roles, log_channel, auto_roles, stack_roles, 
                 decay_enabled, decay_days)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(guild_id),
                settings.get('cooldown', 43200),
                settings.get('max_daily', 3),
                settings.get('min_message_age', 1800),
                settings.get('required_role'),
                settings.get('blacklisted_roles', ''),
                settings.get('log_channel'),
                settings.get('auto_roles', ''),
                settings.get('stack_roles', False),
                settings.get('decay_enabled', False),
                settings.get('decay_days', 30)
            ))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error updating reputation settings: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def get_user_reputation(self, guild_id: int, user_id: int) -> Optional[Dict]:
        """Get user reputation data"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM user_reputation 
                WHERE guild_id = ? AND user_id = ?
            """, (str(guild_id), str(user_id)))
            
            data = cursor.fetchone()
            return dict(data) if data else None
            
        except sqlite3.Error as e:
            logger.error(f"Error getting user reputation: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def update_user_reputation(self, guild_id: int, user_id: int, reputation_change: int, 
                             is_giver: bool = False) -> bool:
        """Update user reputation"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get current data
            cursor.execute("""
                SELECT reputation, total_given, total_received 
                FROM user_reputation 
                WHERE guild_id = ? AND user_id = ?
            """, (str(guild_id), str(user_id)))
            
            data = cursor.fetchone()
            
            if data:
                current_rep = data['reputation']
                total_given = data['total_given']
                total_received = data['total_received']
            else:
                current_rep = 0
                total_given = 0
                total_received = 0
            
            # Calculate new values
            new_reputation = current_rep + reputation_change
            new_total_given = total_given + (1 if is_giver else 0)
            new_total_received = total_received + (1 if not is_giver and reputation_change > 0 else 0)
            
            # Update timestamp fields
            now = datetime.utcnow()
            if is_giver:
                cursor.execute("""
                    INSERT OR REPLACE INTO user_reputation 
                    (guild_id, user_id, reputation, total_given, total_received, last_given, last_received)
                    VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT last_received FROM user_reputation WHERE guild_id = ? AND user_id = ?), ?))
                """, (str(guild_id), str(user_id), new_reputation, new_total_given, new_total_received, now, str(guild_id), str(user_id), now))
            else:
                cursor.execute("""
                    INSERT OR REPLACE INTO user_reputation 
                    (guild_id, user_id, reputation, total_given, total_received, last_given, last_received)
                    VALUES (?, ?, ?, ?, ?, COALESCE((SELECT last_given FROM user_reputation WHERE guild_id = ? AND user_id = ?), ?), ?)
                """, (str(guild_id), str(user_id), new_reputation, new_total_given, new_total_received, str(guild_id), str(user_id), now, now))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error updating user reputation: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def add_reputation_history(self, guild_id: int, giver_id: int, receiver_id: int, 
                             amount: int, reason: str = None, message_id: int = None) -> bool:
        """Add reputation history entry"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO reputation_history 
                (guild_id, giver_id, receiver_id, message_id, reason, amount, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (str(guild_id), str(giver_id), str(receiver_id), str(message_id) if message_id else None, 
                  reason, amount, datetime.utcnow()))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error adding reputation history: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def get_reputation_history(self, guild_id: int, user_id: int = None, limit: int = 10) -> List[Dict]:
        """Get reputation history"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            if user_id:
                cursor.execute("""
                    SELECT * FROM reputation_history 
                    WHERE guild_id = ? AND (giver_id = ? OR receiver_id = ?)
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (str(guild_id), str(user_id), str(user_id), limit))
            else:
                cursor.execute("""
                    SELECT * FROM reputation_history 
                    WHERE guild_id = ?
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (str(guild_id), limit))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            logger.error(f"Error getting reputation history: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def get_leaderboard(self, guild_id: int, limit: int = 10) -> List[Dict]:
        """Get reputation leaderboard"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, reputation, total_given, total_received 
                FROM user_reputation 
                WHERE guild_id = ? AND reputation > 0
                ORDER BY reputation DESC 
                LIMIT ?
            """, (str(guild_id), limit))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            logger.error(f"Error getting reputation leaderboard: {e}")
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
                FROM user_reputation 
                WHERE guild_id = ? AND reputation > (
                    SELECT COALESCE(reputation, 0) FROM user_reputation 
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

    def get_reputation_roles(self, guild_id: int, reputation: int = None) -> List[Dict]:
        """Get reputation roles"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            if reputation is not None:
                cursor.execute("""
                    SELECT role_id FROM reputation_roles
                    WHERE guild_id = ? AND reputation <= ?
                    ORDER BY reputation DESC
                """, (str(guild_id), reputation))
            else:
                cursor.execute("""
                    SELECT reputation, role_id FROM reputation_roles
                    WHERE guild_id = ?
                    ORDER BY reputation ASC
                """, (str(guild_id),))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except sqlite3.Error as e:
            logger.error(f"Error getting reputation roles: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def add_reputation_role(self, guild_id: int, reputation: int, role_id: int) -> bool:
        """Add reputation role"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO reputation_roles 
                (guild_id, reputation, role_id)
                VALUES (?, ?, ?)
            """, (str(guild_id), reputation, str(role_id)))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error adding reputation role: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def remove_reputation_role(self, guild_id: int, reputation: int) -> bool:
        """Remove reputation role"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM reputation_roles 
                WHERE guild_id = ? AND reputation = ?
            """, (str(guild_id), reputation))
            
            conn.commit()
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error removing reputation role: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def get_daily_given_count(self, guild_id: int, user_id: int) -> int:
        """Get how many reputation points user has given today"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            today = datetime.utcnow().date()
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM reputation_history 
                WHERE guild_id = ? AND giver_id = ? 
                AND DATE(timestamp) = ?
            """, (str(guild_id), str(user_id), today))
            
            result = cursor.fetchone()
            return result['count'] if result else 0
            
        except sqlite3.Error as e:
            logger.error(f"Error getting daily given count: {e}")
            return 0
        finally:
            if conn:
                conn.close()
