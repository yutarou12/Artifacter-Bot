import json
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
                    return await interaction.followup.send(content='取得できませんでした\nUIDが間違っていないか確認してください')

        first_embed = discord.Embed(title=player["Name"])
        if player["Signature"]:
            first_embed.description = player["Signature"]
        first_embed.add_field(name='螺旋', value=player["Tower"])
        first_embed.add_field(name='アチーブメント', value=player["Achievement"])
        first_embed.set_footer(text=f'冒険ランク{player["Level"]}・世界ランク{player["worldLevel"]}')
        first_embed.set_thumbnail(url=f'https://enka.network/ui/{player["ProfilePicture"]}.png')
        if player["NameCard"]:
            first_embed.set_image(url=f'https://enka.network/ui/{player["NameCard"]}.png')

        view = MainCharacterView(user=interaction.user)
        character_select = MainCharacterSelect(
            data={"AllData": all_data, "Player": player}, uid=uid, user=interaction.user)

        view.add_item(discord.ui.Button(style=discord.ButtonStyle.url, url='https://enka.network', label='Enka Network'))

        if player["showAvatarInfo"]:
            for i, chara in enumerate(player["showAvatarInfo"]):
                name = fetch_character(str(chara["avatarId"]))
                level = chara["level"]
                character_select.add_option(label=name, description=f'Lv{level}', value=f'{i}')
        else:
            character_select.add_option(label='取得できません', value='404')
        view.add_item(character_select)

        await interaction.followup.send(embed=first_embed, view=view)


class MainCharacterView(discord.ui.View):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timeout = 120
        self.value = None
        self.user = user

    @discord.ui.button(label='生成をキャンセル', style=discord.ButtonStyle.red)
    async def cancel_button(self, interaction: discord.Interaction, button):
        if not interaction.user == self.user:
            return
        self.stop()
        self.value = True
        return await interaction.response.edit_message(view=None)


class MainCharacterSelect(discord.ui.Select):
    def __init__(self, data: dict, uid: int, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.placeholder = "メインキャラクターを選択"
        self.data = data
        self.uid = uid
        self.user = user

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user == self.user:
            return
        player = self.data.get('Player')
        main_character = int(self.values[0])
        if main_character == 404:
            self.view.stop()
            return await interaction.response.edit_message(view=None)

        first_embed = discord.Embed(title='Step1：スコア換算基準を選択',
                                    description='聖遺物のスコアの換算基準を選択してください。')
        first_embed.set_author(name=player.get('Name'), url=f'https://enka.network/ui/{player["ProfilePicture"]}.png')
        first_embed.set_footer(text='原神パーティー編成画像生成')

        view = discord.ui.View()
        step_first = StepFirstSelect(data=self.data, main_chara=main_character, uid=self.uid, user=interaction.user)
        for t in ['HP', '攻撃', '防御', 'チャージ', '元素熟知', 'キャンセル']:
            if t == 'キャンセル':
                step_first.add_option(label=t, description='画像の生成をキャンセルします')
            else:
                step_first.add_option(label=t)
        view.add_item(step_first)

        return await interaction.response.edit_message(embed=first_embed, view=view)


class StepFirstSelect(discord.ui.Select):
    def __init__(self, data: dict, main_chara: int, uid: int, user):
        super().__init__()
        self.placeholder = "スコア基準を選択"
        self.data = data
        self.main_character = main_chara
        self.uid = uid
        self.user = user

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user == self.user:
            return

        if self.values[0] == 'キャンセル':
            self.view.stop()
            return await interaction.response.edit_message(view=None)
        else:
            state = self.values[0]
            player = self.data.get('Player')

            embed = discord.Embed(title='Step2：キャラクターを選択',
                                        description='パーティーに入れるキャラクターを3人選択してください。')
            embed.add_field(name='メインキャラクター',
                            value=f'{fetch_character(str(player["showAvatarInfo"][self.main_character]["avatarId"]))}')
            embed.set_author(name=player.get('Name'), url=f'https://enka.network/ui/{player["ProfilePicture"]}.png')
            embed.set_footer(text='原神パーティー編成画像生成')

            view = discord.ui.View()
            select = StepSecondSelect(
                state=state, data=self.data, main_chara=self.main_character, uid=self.uid, user=interaction.user)

            if player["showAvatarInfo"]:
                for i, chara in enumerate(player["showAvatarInfo"]):
                    name = fetch_character(str(chara["avatarId"]))
                    level = chara["level"]
                    select.add_option(label=name, description=f'Lv{level}', value=f'{i}')
            else:
                select.add_option(label='取得できません', value='404')

            view.add_item(select)

            return await interaction.response.edit_message(view=view, embed=embed)


class StepSecondSelect(discord.ui.Select):
    def __init__(self, state: str, data: dict, main_chara: int, uid: int, user):
        super().__init__()
        self.placeholder = "キャラクターを選択"
        self.max_values = 3
        self.min_values = 3
        self.state = state
        self.data = data
        self.main_character = main_chara
        self.uid = uid
        self.user = user

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user == self.user:
            return
        await interaction.response.defer()

        embed = discord.Embed(title='Step3：生成中',
                              description='しばらくお待ちください。')
        await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed)

        chara_list = list()
        async with aiohttp.ClientSession() as session:
            data = {
                "data": self.data.get('AllData'),
                "index": self.main_character,
                "types": self.state
            }
            async with session.post('http://127.0.0.1:8080/api/team/main/converter', json=data) as r:
                if r.status == 200:
                    chara_list.append(await r.json())

        for sub_chara in self.values:
            async with aiohttp.ClientSession() as session:
                data = {
                    "data": self.data.get('AllData'),
                    "index": int(sub_chara)
                }
                async with session.post('http://127.0.0.1:8080/api/team/sub/converter', json=data) as r:
                    if r.status == 200:
                        chara_list.append(await r.json())

        if not len(chara_list) == 4:
            embed = discord.Embed(title='PT画像生成エラー', description='キャラクターを取得できませんでした。')
            return await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed)
        else:
            async with aiohttp.ClientSession() as session:
                data = {
                    "data": chara_list
                }
                async with session.post('http://127.0.0.1:8080/api/team/generation', json=data) as r:
                    if r.status == 200:
                        image_data = await r.content.read()
                        img = Image.open(BytesIO(image_data))
                        img.save(f'./Tests/{str(self.uid)}-TeamImage.png')
                    else:
                        return await interaction.followup.edit_message(
                            message_id=interaction.message.id, content='生成できませんでした。')

            file = discord.File(f'./Tests/{self.uid}-TeamImage.png', filename='image.png')

            embed = discord.Embed(title='パーティー編成カード')
            embed.set_image(url='attachment://image.png')
            return await interaction.followup.edit_message(
                message_id=interaction.message.id, embed=embed, attachments=[file], view=None)


async def setup(bot):
    await bot.add_cog(PartyCard(bot))
