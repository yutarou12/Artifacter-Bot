import requests
import json
import math
import aiohttp

from io import BytesIO
from PIL import Image

import discord
from discord import app_commands
from discord.ext import commands

from libs.Convert import fetch_character


class PartyCard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='party')
    @app_commands.rename(uid_='uid')
    async def cmd_party(self, interaction: discord.Interaction, uid_: int = None):
        with open('./data/uid_list.json', 'r', encoding='utf-8') as d:
            uid_list = json.load(d)

        uid = uid_ or uid_list.get(str(interaction.user.id))
        if not uid:
            return await interaction.response.send_message('UIDを入れて下さい', ephemeral=True)

        await interaction.response.defer()

        async with aiohttp.ClientSession() as session:
            async with session.post('http://127.0.0.1:8080/api/player', json={"uid": uid}) as r:
                if r.status == 200:
                    j = await r.json()
                    player = j.get("Player")
                    all_data = j.get("AllData")
                else:
                    return await interaction.followup.send(content='取得できませんでした¥nUIDが間違っていないか確認してください')

        first_embed = discord.Embed(title=player["Name"])
        if player["Signature"]:
            first_embed.description = player["Signature"]
        first_embed.add_field(name='螺旋', value=player["Tower"])
        first_embed.add_field(name='アチーブメント', value=player["Achievement"])
        first_embed.set_footer(text=f'冒険ランク{player["Level"]}・世界ランク{player["worldLevel"]}')
        first_embed.set_thumbnail(url=f'https://enka.network/ui/{player["ProfilePicture"]}.png')
        if player["NameCard"]:
            first_embed.set_image(url=f'https://enka.network/ui/{player["NameCard"]}.png')

        view = MainCharacterView()
        character_select = MainCharacterSelect()

        if player["showAvatarInfo"]:
            for i, chara in enumerate(player["showAvatarInfo"]):
                name = fetch_character(str(chara["avatarId"]))
                level = chara["level"]
                character_select.add_option(label=name, description=f'Lv{level}', value=f'{i}')
        else:
            character_select.add_option(label='取得できません')
        view.add_item(character_select)

        await interaction.followup.send(embed=first_embed, view=view)


class MainCharacterView(discord.ui.View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timeout = 120
        self.value = None

    @discord.ui.button(label='Enka Network', style=discord.ButtonStyle.url)
    async def url_button(self):
        return

    @discord.ui.button(label='生成をキャンセル', style=discord.ButtonStyle.red)
    async def cancel_button(self, interaction: discord.Interaction, button):
        self.stop()
        self.value = True


class MainCharacterSelect(discord.ui.Select):
    def __init__(self):
        super().__init__()
        self.placeholder = "メインキャラクターを選択"

    async def callback(self, interaction: discord.Interaction):

        first_embed = discord.Embed(title='Step１：スコア換算基準を選択',
                                    description='聖遺物のスコアの換算基準を選択してください。')
        first_embed.set_author(name=player.get('Name'), url=f'https://enka.network/ui/{player["ProfilePicture"]}.png')
        first_embed.set_footer(text='原神パーティー編成画像生成')

        view = StepOneView()
        step_first = StepFirstSelect()
        for t in ['HP', '攻撃', '防御', 'チャージ', '元素熟知', 'キャンセル']:
            if t == 'キャンセル':
                step_first.add_option(label=t, description='画像の生成をキャンセルします')
            else:
                step_first.add_option(label=t)
        view.add_item(step_first)

        await interaction.followup.send(embed=first_embed, view=view)

        return


class StepOneView(discord.ui.View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class StepFirstSelect(discord.ui.Select):
    def __init__(self):
        super().__init__()
        self.placeholder = "スコア基準を選択"

    async def callback(self, interaction: discord.Interaction):
        return