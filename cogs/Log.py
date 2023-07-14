import math
import os

from datetime import datetime

from discord import Interaction, Embed, Game
from discord.ext import commands


class Log(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user.name} でログインしました')
        print(f'サーバー数: {len(self.bot.guilds)}')
        log_channel = await self.bot.fetch_channel(int(os.getenv('ON_READY_CHANNEL_ID')))
        if log_channel:
            today_stamp = math.floor(datetime.utcnow().timestamp())
            embed = Embed(title='on_ready')
            embed.add_field(name='NowTime', value=f'<t:{today_stamp}:d> <t:{today_stamp}:T>', inline=False)
            embed.add_field(name='Servers', value=f'{len(self.bot.guilds)}', inline=False)
            await log_channel.send(embed=embed)

        await self.bot.change_presence(
            activity=Game(name='原神！！！！！！！！！')
        )

    @commands.Cog.listener()
    async def on_interaction(self, interaction: Interaction):
        if interaction.command:
            command_channel = await self.bot.fetch_channel(int(os.getenv('ON_INTERACTION_CHANNEL_ID')))
            if command_channel:
                cmd_name = interaction.command.qualified_name
                embed = Embed(title='Command Log')
                embed.add_field(name='Command', value=f'{cmd_name}', inline=False)
                embed.add_field(name='User', value=f'{interaction.user.display_name} ({interaction.user.id})', inline=False)
                await command_channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Log(bot))
