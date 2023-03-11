import requests
import os
import json

from PIL import Image, ImageOps, ImageChops

import discord
from discord import app_commands
from discord.ext import commands

from Generater import generation


class Genshin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.convert = bot.convert

    @app_commands.command(name='build')
    async def cmd_build(self, interaction: discord.Interaction, uid: int):
        await interaction.response.defer()

        if not os.path.exists(f'./data/cache/{uid}.json'):
            res = requests.get(f'https://enka.network/api/uid/{uid}')
            res_data = res.json()
            with open(f'./data/cache/{uid}.json', 'w') as f:
                json.dump(res_data, f, indent=4)

        player = self.convert.player_info(uid)
        first_embed = discord.Embed(title=player["Name"])
        file = None
        if player["Signature"]:
            first_embed.description = player["Signature"]
        first_embed.add_field(name='螺旋', value=player["Tower"])
        first_embed.add_field(name='アチーブメント', value=player["Achievement"])
        first_embed.set_footer(text=f'冒険ランク{player["Level"]}・世界ランク{player["worldLevel"]}')
        first_embed.set_thumbnail(url=f'https://enka.network/ui/{player["ProfilePicture"]}.png')
        if player["NameCard"]:
            if not os.path.exists(f'./NameCard/{player["NameCard"]}.png'):
                image = requests.get(f'https://enka.network/ui/{player["NameCard"]}.png')
                with open(f'./NameCard/cache/{player["NameCard"]}.png', mode='wb') as f:
                    f.write(image.content)

                name_card = Image.open(f'./NameCard/cache/{player["NameCard"]}.png')

                bg_img = Image.new(name_card.mode, name_card.size, name_card.getpixel((0, 0)))
                diff_img = ImageChops.difference(name_card, bg_img)
                crop_range = diff_img.convert('RGB').getbbox()
                crop_img = name_card.crop(crop_range)
                crop_img.save(f'./NameCard/{player["NameCard"]}.png')

            file = discord.File(f'./NameCard/{player["NameCard"]}.png', filename='image.png')
            first_embed.set_image(url='attachment://image.png')

        view = discord.ui.View(timeout=180)
        if player["showAvatarInfo"]:
            view_select = FirstSelect(self.bot, uid, player)
            for i, chara in enumerate(player["showAvatarInfo"]):
                name = self.convert.fetch_character(str(chara["avatarId"]))
                level = chara["level"]
                view_select.add_option(label=name, description=f'Lv{level}', value=f'{i}')
        else:
            view_select = FirstSelect(self.bot, uid, player)
            view_select.add_option(label='取得できません')

        view.add_item(view_select)
        view.add_item(BaseButton(bot=self.bot, uid=uid, player=player, style=discord.ButtonStyle.green, label='攻撃'))
        view.add_item(BaseButton(bot=self.bot, uid=uid, player=player, style=discord.ButtonStyle.green, label='HP'))
        view.add_item(BaseButton(bot=self.bot, uid=uid, player=player, style=discord.ButtonStyle.green, label='チャージ'))
        view.add_item(BaseButton(bot=self.bot, uid=uid, player=player, style=discord.ButtonStyle.green, label='元素熟知'))
        view.add_item(BaseButton(bot=self.bot, uid=uid, player=player, style=discord.ButtonStyle.green, label='防御'))
        view.add_item(BaseButton(bot=self.bot, uid=uid, player=player, style=discord.ButtonStyle.red, label='終了'))

        await interaction.followup.send(embed=first_embed, view=view, file=file)


class FirstSelect(discord.ui.Select):
    def __init__(self, bot, uid, player):
        self.bot = bot
        self.uid = uid
        self.player = player
        self.convert = self.bot.convert
        super().__init__()
        self.placeholder = "キャラクターを選択"

    async def callback(self, interaction: discord.Interaction):
        self.convert.info_convert(self.uid, int(self.values[0]))
        with open(f'./data/cache/{self.uid}-character.json', mode='r', encoding='utf-8') as f:
            res = json.load(f)

        character = res["Character"]
        weapon = res["Weapon"]
        set_bonus_text = ''
        for q, n in res['Score']['Bonus']:
            set_bonus_text += f'**{q}セット** `{n}`\n'
        status_text = ''
        for k, v in character['Status'].items():
            status_text += f'**{k}**：{v}\n'

        embed = discord.Embed(description=f'{self.player["Name"]}・冒険ランク{self.player["Level"]}・世界ランク{self.player["worldLevel"]}',
                              color=discord.Color.from_str(character["Color"]))
        embed.set_author(name=f'{character["Name"]}のステータス',
                         icon_url=f'https://enka.network/ui/{character["SideIconName"]}.png')

        if weapon:
            embed.add_field(name=f'武器: **Lv{weapon["Level"]} {weapon["name"]}:R{weapon["totu"]}**',
                            value=f'**基礎攻撃力**：{weapon["BaseATK"]}\n**{weapon["Sub"]["name"]}**：{weapon["Sub"]["value"]}',
                            inline=False)

        embed.add_field(name='ステータス', value=status_text, inline=False)
        character_talent_list = [str(t) for t in list(character["Talent"].values())]

        embed.add_field(name='天賦レベル', value='/'.join(character_talent_list), inline=False)

        embed.set_footer(text=f'Lv.{character["Level"]}・好感度{character["Love"]}')
        await interaction.response.edit_message(embed=embed, attachments=[])


class BaseButton(discord.ui.Button):
    def __init__(self, bot, uid, player, *args, **kwargs):
        self.chara_data = None
        self.player = player
        self.uid = uid
        self.convert = bot.convert
        super().__init__(*args, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        if self.label == '終了':
            self.view.stop()
            if os.path.exists(f'./data/cache/{self.uid}-character.json'):
                os.remove(f'./data/cache/{self.uid}-character.json')
            if os.path.exists(f'./data/cache/{self.uid}.json'):
                os.remove(f'./data/cache/{self.uid}.json')
            if os.path.exists(f'./data/cache/{self.uid}-fixed.json'):
                os.remove(f'./data/cache/{self.uid}-fixed.json')
            return await interaction.response.edit_message(view=None)

        elif not os.path.exists(f'./data/cache/{self.uid}-character.json'):
            await interaction.response.send_message('先にキャラクターを選択してください。', ephemeral=True)
        else:
            await interaction.response.defer()
            res = self.convert.artifacts_convert(self.uid, self.label)

            generation(res)

            if res["Score"]["total"] >= 220:
                chara_rank = 'SS'
            elif res["Score"]["total"] >= 200:
                chara_rank = 'S'
            elif res["Score"]["total"] >= 180:
                chara_rank = 'A'
            else:
                chara_rank = 'B'

            character = res["Character"]
            set_bonus_text = ''
            for q, n in res['Score']['Bonus']:
                set_bonus_text += f'**{q}セット** `{n}`\n'

            file = discord.File('./Tests/Image.png', filename='image.png')

            embed = discord.Embed(title=f'キャラクター評価: {chara_rank}',
                                  description=f'{self.player["Name"]} | 冒険ランク{self.player["Level"]} | 世界ランク{self.player["worldLevel"]}',
                                  color=discord.Color.from_str(character["Color"]))
            embed.set_author(name=f'{character["Name"]}のステータス',
                             icon_url=f'https://enka.network/ui/{character["SideIconName"]}.png')
            embed.add_field(name='セット効果', value=f'{set_bonus_text}')
            embed.set_footer(text=f'Lv.{character["Level"]} ・ 好感度{character["Love"]} ・ '
                                  f'スコア:{res["Score"]["total"]}/{res["Score"]["State"]}換算')
            embed.set_image(url='attachment://image.png')
            await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed, attachments=[file])


async def setup(bot):
    await bot.add_cog(Genshin(bot))
