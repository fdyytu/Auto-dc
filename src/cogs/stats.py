import discord
from discord.ext import commands
import datetime
from collections import Counter
import pandas as pd
import io
from .utils import Embed, get_connection, logger

class ServerStats(commands.Cog):
    """📊 Sistem Statistik Server (ASCII Charts - Ramah HP Low-End)"""
    
    def __init__(self, bot):
        self.bot = bot
        self.message_history = {}
        self.voice_time = {}
        
    def create_ascii_bar_chart(self, data, labels, title="Chart", max_width=30):
        """Create ASCII bar chart yang ramah untuk HP low-end"""
        if not data or not labels:
            return "❌ Tidak ada data untuk ditampilkan"
            
        max_value = max(data) if data else 1
        chart_lines = [f"📊 {title}", "=" * (max_width + 10)]
        
        for i, (label, value) in enumerate(zip(labels, data)):
            # Calculate bar length
            bar_length = int((value / max_value) * max_width) if max_value > 0 else 0
            bar = "█" * bar_length + "░" * (max_width - bar_length)
            
            # Truncate label if too long
            display_label = label[:15] + "..." if len(label) > 15 else label
            chart_lines.append(f"{display_label:<18} │{bar}│ {value}")
        
        chart_lines.append("=" * (max_width + 10))
        return "\n".join(chart_lines)
    
    def create_ascii_line_chart(self, data, labels, title="Chart", max_width=50):
        """Create ASCII line chart untuk trend data"""
        if not data or not labels:
            return "❌ Tidak ada data untuk ditampilkan"
            
        max_value = max(data) if data else 1
        min_value = min(data) if data else 0
        height = 10
        
        chart_lines = [f"📈 {title}", "=" * max_width]
        
        # Normalize data to chart height
        normalized = []
        for value in data:
            if max_value == min_value:
                normalized.append(height // 2)
            else:
                norm = int(((value - min_value) / (max_value - min_value)) * (height - 1))
                normalized.append(norm)
        
        # Create chart grid
        for row in range(height - 1, -1, -1):
            line = ""
            for col, norm_val in enumerate(normalized):
                if norm_val >= row:
                    line += "●"
                else:
                    line += " "
                if col < len(normalized) - 1:
                    line += " "
            
            # Add y-axis labels
            if row == height - 1:
                chart_lines.append(f"{max_value:>6} │{line}")
            elif row == 0:
                chart_lines.append(f"{min_value:>6} │{line}")
            else:
                chart_lines.append(f"{'':>6} │{line}")
        
        # Add x-axis
        x_axis = "       └" + "─" * (len(normalized) * 2 - 1)
        chart_lines.append(x_axis)
        
        # Add x-axis labels (show first, middle, last)
        if len(labels) >= 3:
            x_labels = f"        {labels[0]:<10}"
            if len(labels) > 2:
                mid_idx = len(labels) // 2
                x_labels += f"{labels[mid_idx]:^10}{labels[-1]:>10}"
            chart_lines.append(x_labels)
        
        chart_lines.append("=" * max_width)
        return "\n".join(chart_lines)
        
    def log_activity(self, guild_id: int, user_id: int, activity_type: str, details: str = None):
        """Log any server activity"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO activity_logs (guild_id, user_id, activity_type, details)
                VALUES (?, ?, ?, ?)
            """, (str(guild_id), str(user_id), activity_type, details))
            
            conn.commit()
        except Exception as e:
            logger.error(f"Error logging activity: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

    def log_message_activity(self, message):
        """Log message activity"""
        if not message.guild or message.author.bot:
            return
            
        self.log_activity(
            message.guild.id,
            message.author.id,
            'message',
            f'Channel: {message.channel.name}'
        )

    def log_voice_activity(self, member, before, after):
        """Log voice activity"""
        if not member.guild:
            return
            
        if before.channel is None and after.channel is not None:
            self.log_activity(
                member.guild.id,
                member.id,
                'voice_join',
                f'Channel: {after.channel.name}'
            )
        elif before.channel is not None and after.channel is None:
            self.log_activity(
                member.guild.id,
                member.id,
                'voice_leave',
                f'Channel: {before.channel.name}'
            )

    @commands.command(name="serverstats")
    async def show_server_stats(self, ctx):
        """📊 Tampilkan statistik server"""
        guild = ctx.guild
        
        embed = Embed(
            title=f"📊 Statistik Server {guild.name}",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Members",
            value=f"Total: {guild.member_count}\n"
                  f"Humans: {len([m for m in guild.members if not m.bot])}\n"
                  f"Bots: {len([m for m in guild.members if m.bot])}",
            inline=True
        )
        
        embed.add_field(
            name="Channels",
            value=f"Text: {len(guild.text_channels)}\n"
                  f"Voice: {len(guild.voice_channels)}\n"
                  f"Categories: {len(guild.categories)}",
            inline=True
        )
        
        embed.add_field(
            name="Roles",
            value=f"Total Roles: {len(guild.roles)}\n"
                  f"Highest Role: {guild.roles[-1].name}",
            inline=True
        )
        
        embed.add_field(
            name="Server Info",
            value=f"Created: <t:{int(guild.created_at.timestamp())}:R>\n"
                  f"Owner: {guild.owner.mention}\n"
                  f"Region: {guild.preferred_locale}",
            inline=False
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        await ctx.send(embed=embed)

    @commands.command(name="rolestat")
    async def role_statistics(self, ctx):
        """📊 Tampilkan statistik role (ASCII Chart - Ramah HP Low-End)"""
        roles = [role for role in ctx.guild.roles if not role.is_default()]
        
        if not roles:
            return await ctx.send("❌ Tidak ada role untuk ditampilkan!")
            
        member_counts = [len(role.members) for role in roles]
        role_names = [role.name for role in roles]
        
        # Create ASCII bar chart
        chart = self.create_ascii_bar_chart(
            member_counts, 
            role_names, 
            "Role Distribution"
        )
        
        embed = Embed(
            title="📊 Role Statistics (ASCII Chart)",
            description=f"```\n{chart}\n```",
            color=discord.Color.blue()
        )
        
        await ctx.send(embed=embed)

    @commands.command(name="activitystats")
    async def activity_statistics(self, ctx, days: int = 7):
        """📈 Tampilkan statistik aktivitas (ASCII Chart)"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT activity_type, COUNT(*) as count, 
                       strftime('%Y-%m-%d', timestamp) as date
                FROM activity_logs
                WHERE guild_id = ?
                AND timestamp > datetime('now', ?)
                GROUP BY activity_type, date
                ORDER BY date
            """, (str(ctx.guild.id), f'-{days} days'))
            
            data = cursor.fetchall()
            
            if not data:
                return await ctx.send("❌ Tidak ada data aktivitas!")
                
            # Process data for chart
            df = pd.DataFrame(data, columns=['activity_type', 'count', 'date'])
            
            # Create summary chart
            activity_totals = df.groupby('activity_type')['count'].sum().to_dict()
            
            chart = self.create_ascii_bar_chart(
                list(activity_totals.values()),
                list(activity_totals.keys()),
                f"Activity Summary - Last {days} Days"
            )
            
            embed = Embed(
                title="📈 Activity Statistics (ASCII Chart)",
                description=f"```\n{chart}\n```",
                color=discord.Color.green()
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting activity statistics: {e}")
            await ctx.send("❌ Terjadi kesalahan saat mengambil statistik aktivitas!")
        finally:
            if conn:
                conn.close()

    @commands.command(name="memberhistory")
    async def member_history(self, ctx):
        """📈 Tampilkan history member (ASCII Line Chart)"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT member_count, 
                       strftime('%m-%d', timestamp) as date
                FROM member_history
                WHERE guild_id = ?
                ORDER BY timestamp
                LIMIT 30
            """, (str(ctx.guild.id),))
            
            data = cursor.fetchall()
            
            if not data:
                return await ctx.send("❌ Tidak ada data history member!")
                
            # Create line chart
            dates = [row[1] for row in data]
            counts = [row[0] for row in data]
            
            chart = self.create_ascii_line_chart(
                counts,
                dates,
                "Member Growth History (Last 30 Records)"
            )
            
            embed = Embed(
                title="📈 Member History (ASCII Chart)",
                description=f"```\n{chart}\n```",
                color=discord.Color.purple()
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error getting member history: {e}")
            await ctx.send("❌ Terjadi kesalahan saat mengambil history member!")
        finally:
            if conn:
                conn.close()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Track member joins"""
        self.log_activity(member.guild.id, member.id, 'member_join')
        
        # Update member history
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO member_history (guild_id, member_count)
                VALUES (?, ?)
            """, (str(member.guild.id), len(member.guild.members)))
            
            conn.commit()
        except Exception as e:
            logger.error(f"Error logging member join: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Track member leaves"""
        self.log_activity(member.guild.id, member.id, 'member_leave')
        
        # Update member history
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO member_history (guild_id, member_count)
                VALUES (?, ?)
            """, (str(member.guild.id), len(member.guild.members)))
            
            conn.commit()
        except Exception as e:
            logger.error(f"Error logging member leave: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

async def setup(bot):
    """Setup the Stats cog"""
    await bot.add_cog(ServerStats(bot))
