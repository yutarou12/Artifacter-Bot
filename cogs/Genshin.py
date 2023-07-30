import json
import os
import requests
import math
import aiohttp

from io import BytesIO
from PIL import Image
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from libs.Convert import fetch_character


def cooldown_for_everyone_but_guild(interaction: discord.Interaction) -> Optional[app_commands.Cooldown]:
    guild_list = interaction.client.premium_guild_list
    if interaction.guild_id in guild_list:
        return None
    return app_commands.Cooldown(1, 60 * 3)


class Genshin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='uid')
    async def set_uid(self, interaction: discord.Interaction, uid: str = None):
        """UIDを登録/解除します。build時にUIDを入れなくて済むようになります。"""
        if await self.bot.db.get_uid_from_user(interaction.user.id):
            embed = discord.Embed(title='UID登録解除画面',
                                  description=f'登録を解除しますか？')
        else:
            if not uid:
                return await interaction.response.send_message('UIDを入れて下さい', ephemeral=True)
            check_text = f'ユーザー：{interaction.user.name}\nUID：{uid}'
            embed = discord.Embed(title='UID登録画面',
                                  description=f'以下の内容で登録しますか？\n```\n{check_text}\n```')

        view = CheckView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        await view.wait()
        if view.value is None:
            return
        elif view.value:
            if await self.bot.db.get_uid_from_user(interaction.user.id):
                await self.bot.db.remove_user_uid(interaction.user.id)
            else:
                await self.bot.db.add_user_uid(interaction.user.id, uid)

    @app_commands.command(name='build')
    @app_commands.checks.dynamic_cooldown(cooldown_for_everyone_but_guild, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.rename(uid_='uid')
    async def cmd_build(self, interaction: discord.Interaction, uid_: str = None):
        """UIDからキャラクターカードを生成できます。"""

        uid = uid_ or await self.bot.db.get_uid_from_user(interaction.user.id)
        if not uid:
            return await interaction.response.send_message('UIDを入れて下さい', ephemeral=True)

        uid = ''.join(str(uid).split())

        await interaction.response.defer()

        user_cache_name = await self.bot.db.get_user_cache(interaction.user.id)
        if user_cache_name:
            try:
                with open(f'./data/cache/{user_cache_name}.json', mode='r', encoding='utf-8') as f:
                    user_cache = json.load(f)
            except FileNotFoundError:
                user_cache = {}
        else:
            user_cache = {}

        async with aiohttp.ClientSession() as session:
            async with session.post(f'http://{os.getenv("API_HOST_NAME")}:8080/api/player',
                                    json={"uid": uid, "cache": user_cache}) as r:
                if r.status == 200:
                    j = await r.json()
                    player = j.get("Player")
                    all_data = j.get("AllData")
                    bool_cache = j.get("Cache")
                elif r.status == 424:
                    return await interaction.followup.send(content='現在APIがメンテナンス中です。\n復旧までしばらくお待ちください。')
                elif r.status == 404:
                    return await interaction.followup.send(content='データが見つかりませんでした。\nUIDを確認してください。')
                else:
                    return await interaction.followup.send(content='何らかの問題でデータが取得できませんでした。')

        first_embed = discord.Embed(title=player["Name"])
        if player["Signature"]:
            first_embed.description = player["Signature"]
        first_embed.add_field(name='螺旋', value=player["Tower"])
        first_embed.add_field(name='アチーブメント', value=player["Achievement"])
        first_embed.set_footer(text=f'冒険ランク{player["Level"]}・世界ランク{player["worldLevel"]}{"・キャッシュより" if bool_cache else ""}')
        first_embed.set_thumbnail(url=f'https://enka.network/ui/{player["ProfilePicture"]}.png')
        if player["NameCard"]:
            first_embed.set_image(url=f'https://enka.network/ui/{player["NameCard"]}.png')

        view = BuildView()
        if player["showAvatarInfo"]:
            view_select = FirstSelect(res_data=all_data, uid=uid, player=player, user=interaction.user, cache=bool_cache)
            for i, chara in enumerate(player["showAvatarInfo"]):
                name = fetch_character(str(chara["avatarId"]))
                level = chara["level"]
                view_select.add_option(label=name, description=f'Lv{level}', value=f'{i}')
        else:
            view_select = FirstSelect(res_data=all_data, uid=uid, player=player, user=interaction.user, cache=bool_cache)
            view_select.add_option(label='取得できません')

        view.add_item(view_select)
        view.add_item(BaseButton(uid=uid, player=player, style=discord.ButtonStyle.green, label='ㅤ攻撃ㅤ',
                                 user=interaction.user, custom_id='攻撃', cache=bool_cache))
        view.add_item(BaseButton(uid=uid, player=player, style=discord.ButtonStyle.green, label='ㅤHPㅤ',
                                 user=interaction.user, custom_id='HP', cache=bool_cache))
        view.add_item(BaseButton(uid=uid, player=player, style=discord.ButtonStyle.green, label='ㅤチャージㅤ',
                                 user=interaction.user, custom_id='チャージ', cache=bool_cache))
        view.add_item(BaseButton(uid=uid, player=player, style=discord.ButtonStyle.green, label='ㅤ元素熟知ㅤ',
                                 user=interaction.user, row=2, custom_id='元素熟知', cache=bool_cache))
        view.add_item(BaseButton(uid=uid, player=player, style=discord.ButtonStyle.green, label='ㅤ防御ㅤ',
                                 user=interaction.user, row=2, custom_id='防御', cache=bool_cache))
        view.add_item(BaseButton(uid=uid, player=player, style=discord.ButtonStyle.red, label='ㅤ終了ㅤ',
                                 user=interaction.user, row=2, custom_id='終了', cache=bool_cache))

        msg = await interaction.followup.send(embed=first_embed, view=view)
        if not bool_cache:
            with open(f'./data/cache/{user_cache_name}.json', mode='w') as f:
                json.dump(all_data, f, indent=4)
        view_re = await view.wait()
        if view_re:
            requests.get(f'http://{os.getenv("API_HOST_NAME")}:8080/api/delete/{uid}')
            return await msg.edit(view=None)

    @cmd_build.error
    async def cmd_build_error(self, interaction, error):
        if isinstance(error, app_commands.CommandOnCooldown):
            return await interaction.response.send_message(f'{math.floor(error.retry_after)} 秒後に使うことが出来ます。\n'
                                                           f'過負荷防止の為にクールダウンを設けています。',
                                                           ephemeral=True)
        else:
            raise error


class FirstSelect(discord.ui.Select):
    def __init__(self, res_data, uid, player, user, cache: bool):
        self.res_data = res_data
        self.uid = uid
        self.player = player
        self.user = user
        self.cache = cache
        super().__init__()
        self.placeholder = "キャラクターを選択"

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user == self.user:
            return

        async with aiohttp.ClientSession() as session:
            data = {
                "data": self.res_data,
                "index": int(self.values[0]),
                "uid": int(self.uid)
            }
            async with session.post(f'http://{os.getenv("API_HOST_NAME")}:8080/api/converter', json=data) as r:
                if r.status == 200:
                    res = await r.json()
                else:
                    return await interaction.response.send_message(content='取得できませんでした', ephemeral=True)

        character = res["Character"]
        weapon = res["Weapon"]
        set_bonus_text = ''
        for q, n in res['Score']['Bonus']:
            set_bonus_text += f'**{q}セット** `{n}`\n'
        status_text = list()
        raw_list = list()
        for k, v in character['Status'].items():
            if k not in ['HP', '攻撃力', '防御力']:
                status_text.append(f'**{k}**：{v}')
            else:
                raw_list.insert(0, f'**{k}**：{v}')
        for r in raw_list:
            status_text.insert(0, r)

        embed = discord.Embed(description=f'{self.player["Name"]}・冒険ランク{self.player["Level"]}・世界ランク{self.player["worldLevel"]}',
                              color=discord.Color.from_str(character["Color"]))
        embed.set_author(name=f'{character["Name"]}のステータス',
                         icon_url=f'https://enka.network/ui/{character["SideIconName"]}.png')

        if weapon:
            value_text = f'**基礎攻撃力**：{weapon["BaseATK"]}'
            if weapon.get("Sub"):
                value_text += f'\n**{weapon["Sub"]["name"]}**：{weapon["Sub"]["value"]}'
            embed.add_field(name=f'武器: **Lv{weapon["Level"]} {weapon["name"]}:R{weapon["totu"]}**',
                            value=value_text,
                            inline=False)

        embed.add_field(name='ステータス', value='\n'.join(status_text), inline=False)
        character_talent_list = [str(t) for t in list(character["Talent"].values())]

        embed.add_field(name='天賦レベル', value='/'.join(character_talent_list), inline=False)

        embed.set_footer(text=f'Lv.{character["Level"]}・好感度{character["Love"]}{"・キャッシュより" if self.cache else ""}')
        await interaction.response.edit_message(embed=embed, attachments=[])


class BaseButton(discord.ui.Button):
    def __init__(self, uid, player, user, cache, *args, **kwargs):
        self.chara_data = None
        self.player = player
        self.uid = uid
        self.user = user
        self.cache = cache
        super().__init__(*args, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user == self.user:
            return
        if self.custom_id == '終了':
            self.view.stop()
            requests.get(f'http://{os.getenv("API_HOST_NAME")}:8080/api/delete/{self.uid}')
            return await interaction.response.edit_message(view=None)
        else:
            async with aiohttp.ClientSession() as session:
                data = {
                    "types": self.custom_id,
                    "uid": int(self.uid)
                }
                async with session.post(f'http://{os.getenv("API_HOST_NAME")}:8080/api/artifacts', json=data) as r:
                    if r.status == 200:
                        res = await r.json()
                    else:
                        return await interaction.response.send_message('先にキャラクターを選択してください。', ephemeral=True)

            await interaction.response.defer()

            async with aiohttp.ClientSession() as session:
                data = {
                    "data": res,
                    "guild_id": interaction.guild_id,
                    "uid": int(self.uid),
                }
                async with session.post(f'http://{os.getenv("API_HOST_NAME")}:8080/api/generation', json=data) as r:
                    if r.status == 200:
                        image_data = await r.content.read()
                        img = Image.open(BytesIO(image_data))
                        img.save(f'./Tests/{self.uid}-Image.png')
                    else:
                        return await interaction.followup.send('生成できませんでした。', ephemeral=True)

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

            file = discord.File(f'./Tests/{self.uid}-Image.png', filename='image.png')

            embed = discord.Embed(title=f'キャラクター評価: {chara_rank}',
                                  description=f'{self.player["Name"]} | 冒険ランク{self.player["Level"]} | 世界ランク{self.player["worldLevel"]}',
                                  color=discord.Color.from_str(character["Color"]))
            embed.set_author(name=f'{character["Name"]}のステータス',
                             icon_url=f'https://enka.network/ui/{character["SideIconName"]}.png')
            embed.add_field(name='セット効果', value=f'{set_bonus_text}')
            embed.set_footer(text=f'Lv.{character["Level"]} ・ 好感度{character["Love"]} ・ '
                                  f'スコア:{res["Score"]["total"]}/{res["Score"]["State"]}換算{"・キャッシュより" if self.cache else ""}')
            embed.set_image(url='attachment://image.png')
            await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed, attachments=[file])


class BuildView(discord.ui.View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timeout = 180
        self.value = None


class CheckView(discord.ui.View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.timeout = 120
        self.value = None

    @discord.ui.button(label='OK', style=discord.ButtonStyle.green)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content='完了しました', embed=None, view=None)
        self.value = True
        self.stop()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.red)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('キャンセルしました', ephemeral=True)
        self.value = False
        self.stop()


async def setup(bot):
    await bot.add_cog(Genshin(bot))
