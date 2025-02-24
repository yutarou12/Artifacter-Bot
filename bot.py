import logging
import logging.handlers
import os
import traceback

import discord
from discord import Interaction, Embed
from discord.app_commands import AppCommandError
from discord.ext import commands

from libs.Database import Database
from libs.Convert import icon_convert
import libs.env as env
from libs.OriginHandler import WebhookHandler, DatetimeFormatter

extensions_list = [f[:-3] for f in os.listdir("./cogs") if f.endswith(".py")]

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
logging.getLogger('discord.http').setLevel(logging.INFO)
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = DatetimeFormatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')

discord_handler = WebhookHandler(url=env.WEBHOOK_URL)
discord_handler.setFormatter(formatter)
discord_handler.setLevel(level=logging.INFO)
logger.addHandler(discord_handler)


class MyBot(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.premium_guild_list = []
        self.tree.on_error = self.on_app_command_error

    async def on_app_command_error(self, interaction: Interaction, error: AppCommandError):
        traceback_channel = await bot.fetch_channel(env.TRACEBACK_CHANNEL_ID)
        error_channel = await bot.fetch_channel(env.ERROR_CHANNEL_ID)

        tracebacks = getattr(error, 'traceback', error)
        tracebacks = ''.join(traceback.TracebackException.from_exception(tracebacks).format())
        tracebacks = discord.utils.escape_markdown(tracebacks)
        embed_traceback = discord.Embed(title='Traceback Log', description=f'```{tracebacks}```')
        msg_traceback = await traceback_channel.send(embed=embed_traceback)

        embed_logs = Embed(title='Error Log')
        embed_logs.set_author(name=f'{interaction.user.display_name} ({interaction.user.id})',
                              icon_url=icon_convert(interaction.user.avatar))
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

    async def setup_hook(self):
        self.premium_guild_list = await bot.db.get_premium_guild_list()
        try:
            await bot.load_extension('jishaku')
        except discord.ext.commands.ExtensionAlreadyLoaded:
            await bot.reload_extension('jishaku')
        for ext in extensions_list:
            try:
                await bot.load_extension(f'cogs.{ext}')
            except discord.ext.commands.ExtensionAlreadyLoaded:
                await bot.reload_extension(f'cogs.{ext}')

    async def get_context(self, message, *args, **kwargs):
        return await super().get_context(message, *args, **kwargs)


intents = discord.Intents.default()

bot = MyBot(
    command_prefix=commands.when_mentioned_or('a.'),
    intents=intents,
    allowed_mentions=discord.AllowedMentions(replied_user=False, everyone=False),
    help_command=None,
    shard_count=5
)
bot.db = Database()

if __name__ == '__main__':
    bot.run(env.DISCORD_BOT_TOKEN)
