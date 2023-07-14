import os

import discord
from discord.ext import commands

from dotenv import load_dotenv
from libs.Database import Database
from cogs.Log import Log

load_dotenv()

extensions_list = [f[:-3] for f in os.listdir("./cogs") if f.endswith(".py")]


class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree.on_error = Log.on_app_command_error

    async def setup_hook(self):
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
    help_command=None
)
bot.db = Database()

if __name__ == '__main__':
    bot.run(os.getenv('DISCORD_BOT_TOKEN'))
