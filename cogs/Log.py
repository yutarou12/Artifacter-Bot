import math
import traceback
import os

from datetime import datetime

import discord
from discord import Interaction, Embed, Game
from discord.app_commands import AppCommandError
from discord.ext import commands

from libs.Convert import icon_convert


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

    async def on_app_command_error(self, interaction: Interaction, error: AppCommandError):
        traceback_channel = await self.bot.fetch_channel(int(os.getenv('TRACEBACK_CHANNEL_ID')))
        error_channel = await self.bot.fetch_channel(int(os.getenv('ERROR_CHANNEL_ID')))

        tracebacks = getattr(error, 'traceback', error)
        tracebacks = ''.join(traceback.TracebackException.from_exception(tracebacks).format())
        tracebacks = discord.utils.escape_markdown(tracebacks)
        embed_traceback = discord.Embed(title='Traceback Log', description=f'```{tracebacks}```')
        msg_traceback = await traceback_channel.send(embed=embed_traceback)

        embed_logs = Embed(title='Error Log')
        embed_logs.set_author(name=f'{interaction.user.display_name} ({interaction.user.id})',
                              icon_url=icon_convert(interaction.user.icon))
        embed_logs.add_field(name='Command', value=interaction.command.name, inline=False)
        embed_logs.add_field(name='Error', value=f'```{error}```', inline=False)
        embed_logs.add_field(name='Traceback Id', value=f'```{msg_traceback.id}```')
        if interaction.channel.type == discord.ChannelType.text:
            embed_logs.set_footer(
                text=f'{interaction.channel.name} \nG:{interaction.guild_id} C:{interaction.channel_id}',
                icon_url=icon_convert(interaction.guild.icon))
        else:
            embed_logs.set_footer(text=f"{interaction.user}'s DM_CHANNEL C:{interaction.channel_id}")
        await error_channel.send(embed=embed_logs)

        print(error)


async def setup(bot):
    await bot.add_cog(Log(bot))
