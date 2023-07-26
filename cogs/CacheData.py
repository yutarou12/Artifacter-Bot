import os
import requests
import math
import aiohttp

from io import BytesIO
from PIL import Image
from typing import Optional

import discord
from discord import app_commands, Interaction, Embed, ui
from discord.ext import commands


class CacheData(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='設定')
    async def cmd_cache_setting(self, interaction: Interaction):
        embed = Embed(title='キャッシュ機能設定')
        embed.description = '原神のキャラクター情報を取得している「EnkaNetwork」がメンテナンス等により、' \
                            'データを取得出来なかった際に、一番最後に取得したデータを使うことでビルド画像を生成する機能です。'
        if not await self.bot.db.get_user_cache(interaction.user.id):
            embed.add_field(name='現在の設定', value='無効', inline=False)
        else:
            embed.add_field(name='現在の設定', value='有効', inline=False)

        field_2_text = '設定を切り換えるには、「設定を切り換える」を押して下さい。\n「有効」にすると次「/build」でデータを取得できた際にデータが保存されます。\n' \
                       '「無効」にすると、即座に保存されていたデータを抹消します。'
        embed.add_field(name='🔰使い方', value=field_2_text, inline=False)

        view = CacheSettingView()
        await interaction.response.send_message(embed=embed, view=view)
        await view.wait()

        if view.value is None:
            return
        elif view.value:
            if await self.bot.db.get_user_cache(interaction.user.id):
                await self.bot.db.remove_user_cache_data(interaction.user.id)
            else:
                await self.bot.db.add_user_cache_data(interaction.user.id)


class CacheSettingView(ui.View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timeout = 120
        self.value = None

    @discord.ui.button(label='設定を切り換える', style=discord.ButtonStyle.green)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(content='設定を切り換えました。', ephemeral=True)
        self.value = True
        self.stop()


async def setup(bot):
    await bot.add_cog(CacheData(bot))
