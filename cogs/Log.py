import math

from datetime import datetime
from discord import Interaction, Embed, Game
from discord.ext import commands

from libs.env import ON_READY_CHANNEL_ID


class Log(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user.name} でログインしました')
        print(f'サーバー数: {len(self.bot.guilds)}')
        log_channel = await self.bot.fetch_channel(ON_READY_CHANNEL_ID)
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
            cmd_name = interaction.command.qualified_name
            await self.bot.db.add_cmd_log(interaction.user.id, cmd_name, interaction.channel.id)


async def setup(bot):
    await bot.add_cog(Log(bot))
