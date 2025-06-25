import discord
from discord.ext import commands
import datetime
from collections import Counter
import plotly.graph_objects as go
import plotly.express as px
from plotly.io import to_image
import pandas as pd
import io
from .utils import Embed, get_connection, logger

class ServerStats(commands.Cog):
    """📊 Sistem Statistik Server"""
    
    def __init__(self, bot):
        self.bot = bot
        self.message_history = {}
        self.voice_time = {}
        
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
        """📊 Tampilkan statistik role"""
        roles = [role for role in ctx.guild.roles if not role.is_default()]
        
        if not roles:
            return await ctx.send("❌ Tidak ada role untuk ditampilkan!")
            
        member_counts = [len(role.members) for role in roles]
        role_names = [role.name for role in roles]
        
        # Create plot with Plotly (lebih ringan untuk HP low-end)
        fig = go.Figure(data=[
            go.Bar(x=role_names, y=member_counts, 
                   marker_color='lightblue',
                   text=member_counts,
                   textposition='auto')
        ])
        
        fig.update_layout(
            title='Role Distribution',
            xaxis_title='Roles',
            yaxis_title='Member Count',
            xaxis_tickangle=-45,
            height=400,
            width=600
        )
        
        # Save plot
        buf = io.BytesIO()
        img_bytes = to_image(fig, format="png", width=600, height=400)
        buf.write(img_bytes)
        buf.seek(0)
        
        # Send result
        file = discord.File(buf, 'role_stats.png')
        embed = Embed(
            title="📊 Role Statistics",
            description=f"Distribution of {len(roles)} roles in the server"
        )
        embed.set_image(url="attachment://role_stats.png")
        
        await ctx.send(embed=embed, file=file)

    @commands.command(name="activitystats")
    async def activity_statistics(self, ctx, days: int = 7):
        """📈 Tampilkan statistik aktivitas"""
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
                
            # Create plot with Plotly
            df = pd.DataFrame(data, columns=['activity_type', 'count', 'date'])
            
            fig = go.Figure()
            
            for activity in df['activity_type'].unique():
                activity_data = df[df['activity_type'] == activity]
                fig.add_trace(go.Scatter(
                    x=activity_data['date'], 
                    y=activity_data['count'],
                    mode='lines+markers',
                    name=activity,
                    line=dict(width=2),
                    marker=dict(size=6)
                ))
            
            fig.update_layout(
                title=f'Activity Statistics - Last {days} Days',
                xaxis_title='Date',
                yaxis_title='Activity Count',
                xaxis_tickangle=-45,
                height=400,
                width=800,
                showlegend=True
            )
            
            # Save plot
            buf = io.BytesIO()
            img_bytes = to_image(fig, format="png", width=800, height=400)
            buf.write(img_bytes)
            buf.seek(0)
            
            # Send result
            file = discord.File(buf, 'activity_stats.png')
            embed = Embed(
                title="📈 Activity Statistics",
                description=f"Activity overview for the last {days} days"
            )
            embed.set_image(url="attachment://activity_stats.png")
            
            await ctx.send(embed=embed, file=file)
            
        except Exception as e:
            logger.error(f"Error getting activity statistics: {e}")
            await ctx.send("❌ Terjadi kesalahan saat mengambil statistik aktivitas!")
        finally:
            if conn:
                conn.close()

    @commands.command(name="memberhistory")
    async def member_history(self, ctx):
        """📈 Tampilkan history member"""
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT member_count, 
                       strftime('%Y-%m-%d', timestamp) as date
                FROM member_history
                WHERE guild_id = ?
                ORDER BY timestamp
            """, (str(ctx.guild.id),))
            
            data = cursor.fetchall()
            
            if not data:
                return await ctx.send("❌ Tidak ada data history member!")
                
            # Create plot with Plotly
            dates = [row[1] for row in data]
            counts = [row[0] for row in data]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates, 
                y=counts,
                mode='lines+markers',
                name='Member Count',
                line=dict(color='blue', width=3),
                marker=dict(size=8, color='lightblue')
            ))
            
            fig.update_layout(
                title='Member Growth History',
                xaxis_title='Date',
                yaxis_title='Member Count',
                xaxis_tickangle=-45,
                height=400,
                width=800,
                showlegend=False
            )
            
            # Save plot
            buf = io.BytesIO()
            img_bytes = to_image(fig, format="png", width=800, height=400)
            buf.write(img_bytes)
            buf.seek(0)
            
            # Send result
            file = discord.File(buf, 'member_history.png')
            embed = Embed(
                title="📈 Member History",
                description="Server member count over time"
            )
            embed.set_image(url="attachment://member_history.png")
            
            await ctx.send(embed=embed, file=file)
            
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
