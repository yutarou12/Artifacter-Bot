import requests
import math
import aiohttp

from io import BytesIO
from PIL import Image
from typing import Optional, Mapping

import discord
from discord import app_commands, Embed
from discord.ext import commands

from libs import env
from libs.Convert import fetch_character, icon_convert
from libs.env import API_HOST_NAME


def cooldown_for_everyone_but_guild(interaction: discord.Interaction) -> Optional[app_commands.Cooldown]:
    guild_list = interaction.client.premium_guild_list
    if interaction.guild_id in guild_list:
        return None
    return app_commands.Cooldown(1, 60 * 1)


async def error_message_send_ch(error_channel, interaction, error) -> None:
    embed_logs = Embed(title='Error Log')
    embed_logs.set_author(name=f'{interaction.user.display_name} ({interaction.user.id})',
                          icon_url=icon_convert(interaction.user.avatar))
    embed_logs.add_field(name='Error', value=f'```{error}```', inline=False)
    if interaction.channel.type == discord.ChannelType.text:
        embed_logs.set_footer(
            text=f'{interaction.channel.name} \nG:{interaction.guild_id} C:{interaction.channel_id}',
            icon_url=icon_convert(interaction.guild.icon))
    else:
        embed_logs.set_footer(text=f"{interaction.user}'s DM_CHANNEL C:{interaction.channel_id}")
    await error_channel.send(embed=embed_logs)


user_party_cache: Mapping[int, dict] = {}


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

    @app_commands.command(name='party')
    @app_commands.checks.dynamic_cooldown(cooldown_for_everyone_but_guild, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.rename(uid_='uid')
    async def cmd_party(self, interaction: discord.Interaction, uid_: str = None):
        """UIDからパーティーカードを生成します。"""
        uid = uid_ or await self.bot.db.get_uid_from_user(interaction.user.id)
        if not uid:
            return await interaction.response.send_message('UIDを入れて下さい', ephemeral=True)

        uid = ''.join(str(uid).split())

        await interaction.response.defer()

        user_premium_bool = await self.bot.db.get_premium_user_bool(interaction.user.id)

        async with aiohttp.ClientSession() as session:
            async with session.post(f'http://{API_HOST_NAME}:8080/api/player',
                                    json={"uid": uid, "user_id": interaction.user.id, "profile": user_premium_bool}) as r:
                if r.status == 200:
                    j = await r.json()
                    player = j.get("Player")
                    all_data = j.get("AllData")
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
        first_embed.set_footer(text=f'冒険ランク{player["Level"]}・世界ランク{player["worldLevel"]}')
        first_embed.set_thumbnail(url=f'https://enka.network/ui/{player["ProfilePicture"]}.png')
        if player["NameCard"]:
            first_embed.set_image(url=f'https://enka.network/ui/{player["NameCard"]}.png')

        view = BuildView()
        if player["showAvatarInfo"]:
            view_select = PartyMainSelect(res_data=all_data, uid=uid, player=player, user=interaction.user)
            for i, chara in enumerate(player["showAvatarInfo"]):
                name = fetch_character(str(chara["avatarId"]))
                level = chara["level"]
                view_select.add_option(label=name, description=f'Lv{level}', value=f'{i}')
        else:
            view_select = PartyMainSelect(res_data=all_data, uid=uid, player=player, user=interaction.user)
            view_select.add_option(label='取得できません')

        type_select = PartyTypeSelect(res_data=all_data, uid=uid, player=player, user=interaction.user)
        for t in ["攻撃", "HP", "元素熟知", "チャージ", "防御"]:
                type_select.add_option(label=t, value=f'{t}')

        view.add_item(view_select)
        view.add_item(type_select)
        view.add_item(EndButton(uid=uid, user=interaction.user, label='終了', custom_id='終了'))
        msg = await interaction.followup.send(embed=first_embed, view=view)
        view_re = await view.wait()
        if view_re:
            if user_party_cache.get(interaction.user.id):
                del user_party_cache[interaction.user.id]
            requests.get(f'http://{API_HOST_NAME}:8080/api/team/delete/{uid}')
            return await msg.edit(view=None)

    @app_commands.command(name='build')
    @app_commands.rename(uid_='uid')
    async def cmd_build(self, interaction: discord.Interaction, uid_: str = None):
        """UIDからキャラクターカードを生成できます。"""

        uid = uid_ or await self.bot.db.get_uid_from_user(interaction.user.id)
        if not uid:
            return await interaction.response.send_message('UIDを入れて下さい', ephemeral=True)

        uid = ''.join(str(uid).split())

        await interaction.response.defer()

        user_premium_bool = await self.bot.db.get_premium_user_bool(interaction.user.id)

        async with aiohttp.ClientSession() as session:
            async with session.post(f'http://{API_HOST_NAME}:8080/api/player',
                                    json={"uid": uid, "user_id": interaction.user.id, "profile": user_premium_bool}) as r:
                if r.status == 200:
                    j = await r.json()
                    player = j.get("Player")
                    all_data = j.get("AllData")
                    img_data = j.get("Img")
                elif r.status == 424:
                    return await interaction.followup.send(content='現在APIがメンテナンス中です。\n復旧までしばらくお待ちください。')
                elif r.status == 404:
                    return await interaction.followup.send(content='データが見つかりませんでした。\nUIDを確認してください。')
                else:
                    return await interaction.followup.send(content='何らかの問題でデータが取得できませんでした。')

        first_embed = discord.Embed(title=player["Name"])
        if player["Signature"]:
            first_embed.description = player["Signature"]
        first_embed.add_field(name='深境螺旋', value=player["Tower"])
        if player["Theater"].get("theaterActIndex"):
            first_embed.add_field(name='幻想シアター', value=f'第{player["Theater"].get("theaterActIndex")}幕')
        else:
            first_embed.add_field(name='幻想シアター', value='未記録')
        first_embed.add_field(name='アチーブメント', value=player["Achievement"])
        first_embed.set_footer(text=f'冒険ランク{player["Level"]}・世界ランク{player["worldLevel"]}')
        first_embed.set_thumbnail(url=f'https://enka.network/ui/{player["ProfilePicture"]}.png')
        if player["NameCard"]:
            first_embed.set_image(url=f'https://enka.network/ui/{player["NameCard"]}.png')

        view = BuildView()
        if player["showAvatarInfo"]:
            view_select = FirstSelect(res_data=all_data, uid=uid, player=player, user=interaction.user)
            for i, chara in enumerate(player["showAvatarInfo"]):
                name = fetch_character(str(chara["avatarId"]))
                level = chara["level"]
                view_select.add_option(label=name, description=f'Lv{level}', value=f'{i}')
        else:
            view_select = FirstSelect(res_data=all_data, uid=uid, player=player, user=interaction.user)
            view_select.add_option(label='取得できません')

        view.add_item(view_select)
        view.add_item(BaseButton(uid=uid, player=player, style=discord.ButtonStyle.green, label='ㅤ攻撃ㅤ',
                                 user=interaction.user, custom_id='攻撃'))
        view.add_item(BaseButton(uid=uid, player=player, style=discord.ButtonStyle.green, label='ㅤHPㅤ',
                                 user=interaction.user, custom_id='HP'))
        view.add_item(BaseButton(uid=uid, player=player, style=discord.ButtonStyle.green, label='ㅤチャージㅤ',
                                 user=interaction.user, custom_id='チャージ'))
        view.add_item(BaseButton(uid=uid, player=player, style=discord.ButtonStyle.green, label='ㅤ元素熟知ㅤ',
                                 user=interaction.user, row=2, custom_id='元素熟知'))
        view.add_item(BaseButton(uid=uid, player=player, style=discord.ButtonStyle.green, label='ㅤ防御ㅤ',
                                 user=interaction.user, row=2, custom_id='防御'))
        view.add_item(BaseButton(uid=uid, player=player, style=discord.ButtonStyle.green, label='  会心  ',
                                 user=interaction.user, row=2, custom_id='会心'))
        view.add_item(BaseButton(uid=uid, player=player, style=discord.ButtonStyle.red, label='ㅤ終了ㅤ',
                                 user=interaction.user, row=2, custom_id='終了'))
        if img_data:
            async with aiohttp.ClientSession() as session:
                async with session.post(f'http://{API_HOST_NAME}:8080/api/profile/get',
                                        json={"uid": uid}) as r:
                    saved_image_data = await r.content.read()
                    created_img = Image.open(BytesIO(saved_image_data))
                    created_img.save(f'./Tests/{uid}-Profile.png')
            file = discord.File(f'./Tests/{uid}-Profile.png', filename='Profile.png')
            img_embed = discord.Embed()
            img_embed.set_image(url='attachment://Profile.png')
            msg = await interaction.followup.send(embed=img_embed, file=file, view=view)
        else:
            msg = await interaction.followup.send(embed=first_embed, view=view)
        view_re = await view.wait()
        if view_re:
            requests.get(f'http://{API_HOST_NAME}:8080/api/delete/{uid}')
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
    def __init__(self, res_data, uid, player, user):
        self.res_data = res_data
        self.uid = uid
        self.player = player
        self.user = user
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
            async with session.post(f'http://{API_HOST_NAME}:8080/api/converter', json=data) as r:
                if r.status == 200:
                    res = await r.json()
                else:
                    return await interaction.response.send_message(content='取得できませんでした', ephemeral=True)

        character = res["Character"]
        weapon = res["Weapon"]
        set_bonus_text = ''
        for q, n in res['Score']['Bonus']:
            set_bonus_text += f'**{q}セット** `{n}`\n'
        discord_icon_list_reversed = {
            "HP": {"name": "A_PROP_HP", "id": 1330326300627566662},
            "攻撃力": {"name": "A_PROP_ATTACK", "id": 1330326294327722089},
            "防御力": {"name": "A_PROP_DEFENSE", "id": 1330326297985155164},
            "会心率": {"name": "A_PROP_CRITICAL", "id": 1330326290838065263},
            "会心ダメージ": {"name": "A_PROP_CRITICAL_HURT", "id": 1330326288514289748},
            "元素チャージ効率": {"name": "A_PROP_CHARGE_EFFICIENCY", "id": 1330326304721080320},
            "元素熟知": {"name": "A_PROP_ELEMENT_MASTERY", "id": 1330326296059711568},
            "物理ダメージ": {"name": "A_PROP_PHYSICAL_HURT", "id": 1330374399991222417},
            "炎元素ダメージ": {"name": "E_PROP_FIRE_HURT", "id": 1330373941403062282},
            "雷元素ダメージ": {"name": "E_PROP_ELEC_HURT", "id": 1330373933114982430},
            "水元素ダメージ": {"name": "E_PROP_WATER_HURT", "id": 1330373945010032660},
            "風元素ダメージ": {"name": "E_PROP_WIND_HURT", "id": 1330373931424682137},
            "氷元素ダメージ": {"name": "E_PROP_ICE_HURT", "id": 1330373948289978455},
            "岩元素ダメージ": {"name": "E_PROP_ROCK_HURT", "id": 1330373943412129964},
            "草元素ダメージ": {"name": "E_PROP_GRASS_HURT", "id": 1330373946616446976}
            }

        status_text = list()
        raw_list = list()
        for k, v in character['Status'].items():
            icon = discord_icon_list_reversed.get(k)
            icon_str = f'<:{icon.get("name")}:{icon.get("id")}>'
            if k not in ['HP', '攻撃力', '防御力']:
                status_text.append(f'{icon_str} **{k}**：{v}')
            else:
                raw_list.insert(0, f'{icon_str} **{k}**：{v}')
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

        embed.set_footer(text=f'Lv.{character["Level"]}・好感度{character["Love"]}')
        await interaction.response.edit_message(embed=embed, attachments=[])


class BaseButton(discord.ui.Button):
    def __init__(self, uid, player, user, *args, **kwargs):
        self.chara_data = None
        self.player = player
        self.uid = uid
        self.user = user
        super().__init__(*args, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user == self.user:
            return
        if self.custom_id == '終了':
            self.view.stop()
            requests.get(f'http://{API_HOST_NAME}:8080/api/delete/{self.uid}')
            return await interaction.response.edit_message(view=None)
        else:
            async with aiohttp.ClientSession() as session:
                data = {
                    "types": self.custom_id,
                    "uid": int(self.uid)
                }
                async with session.post(f'http://{API_HOST_NAME}:8080/api/artifacts', json=data) as r:
                    if r.status == 200:
                        res = await r.json()
                    else:
                        return await interaction.response.send_message('先にキャラクターを選択してください。', ephemeral=True)

            await interaction.response.defer()

            async with aiohttp.ClientSession() as session:
                data = {
                    "data": res,
                    "uid": int(self.uid),
                }
                async with session.post(f'http://{API_HOST_NAME}:8080/api/generation', json=data) as r:
                    if r.status == 200:
                        image_data = await r.content.read()
                        img = Image.open(BytesIO(image_data))
                        img.save(f'./Tests/{self.uid}-Image.png')
                    elif r.status == 404:
                        return await interaction.followup.send('画像が生成されませんでした。何回も発生する場合は公式サーバーまでお問い合わせください。', ephemeral=True)
                    else:
                        error_channel = await interaction.client.fetch_channel(env.ERROR_CHANNEL_ID)
                        await error_message_send_ch(error_channel, interaction, await r.content.read())
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
                                  f'スコア:{res["Score"]["total"]}/{res["Score"]["State"]}換算')
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


class PartyMainSelect(discord.ui.Select):
    def __init__(self, res_data, uid, player, user):
        self.res_data = res_data
        self.uid = uid
        self.player = player
        self.user = user
        super().__init__()
        self.placeholder = "メインキャラクターを選択"

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user == self.user:
            return
        view = self.view
        party_sub_select = PartySubSelect(res_data=self.res_data, uid=self.uid, player=self.player, user=self.user, main_index=int(self.values[0]))
        for i, chara in enumerate(self.res_data.get("playerInfo").get("showAvatarInfoList")):
            if i == int(self.values[0]):
                continue
            name = fetch_character(str(chara["avatarId"]))
            level = chara["level"]
            party_sub_select.add_option(label=name, description=f'Lv{level}', value=f'{i}')
        end = EndButton(uid=self.uid, user=interaction.user, custom_id='終了', label='終了')
        if len(view.children) == 3:
            view.remove_item(view.children[2])
            view.add_item(party_sub_select)
            view.add_item(end)
        else:
            view.remove_item(view.children[3])
            view.remove_item(view.children[2])
            view.add_item(party_sub_select)
            view.add_item(end)
        embed = interaction.message.embeds[0]
        embed.description = ""
        embed.clear_fields()
        embed.set_image(url="")
        embed.add_field(name="メインキャラクター",
                        value=f'{fetch_character(self.res_data.get("playerInfo").get("showAvatarInfoList")[int(self.values[0])]["avatarId"])}',
                        inline=False)
        if user_party_cache.get(interaction.user.id):
            user_party_cache[interaction.user.id]["Main"] = int(self.values[0])
            user_party_cache[interaction.user.id]["Sub"] = []
        else:
            user_party_cache[interaction.user.id] = {"Main": int(self.values[0]), "Sub": [], "方法": None}

        return await interaction.response.edit_message(view=view, embed=embed, attachments=[])


class PartySubSelect(discord.ui.Select):
    def __init__(self, res_data, uid, player, user, main_index):
        self.res_data = res_data
        self.uid = uid
        self.player = player
        self.user = user
        self.main_index = main_index
        super().__init__()
        self.placeholder = "サブキャラクターを選択"
        self.max_values = 3

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user == self.user:
            return

        if user_party_cache.get(interaction.user.id):
            user_party_cache[interaction.user.id]["Sub"] = [int(v) for v in self.values]

        u_p_c_l = user_party_cache.get(interaction.user.id)  # user_party_cache_local

        if u_p_c_l and u_p_c_l.get("Sub") and u_p_c_l.get("方法"):
            await interaction.response.defer()
            result = await generate_image(u_p_c_l.get("Sub"), u_p_c_l.get("Main"), self.res_data, self.uid, u_p_c_l.get("方法"), interaction.user.id)
            if result == 1:
                return await interaction.followup.send("情報の正規化に失敗しました。(Convert Error)", ephemeral=True)
            elif result == 2:
                return await interaction.followup.send("情報の標準化に失敗しました。(Artifact Error)", ephemeral=True)
            elif result == 3:
                return await interaction.followup.send("画像の生成に失敗しました。"
                                                       "エラーが多発する場合はサポートサーバーまでお問い合わせ下さい。(Generation Error)",
                                                       ephemeral=True)
            elif result == 4:

                file = discord.File(f'./Tests/{self.uid}-Party.png', filename='party-image.png')

                embed = discord.Embed(title=f'パーティービルド',
                                      description=f'{self.player["Name"]} | 冒険ランク{self.player["Level"]} | 世界ランク{self.player["worldLevel"]}')
                embed.set_image(url='attachment://party-image.png')
                await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed,
                                                        attachments=[file])
        else:
            embed = interaction.message.embeds[0]
            for v in self.values:
                embed.add_field(name="サブキャラクター",
                                value=f'・{fetch_character(self.res_data.get("playerInfo").get("showAvatarInfoList")[int(v)]["avatarId"])}',
                                inline=False)

            await interaction.response.edit_message(embed=embed)


class PartyTypeSelect(discord.ui.Select):
    def __init__(self, res_data, uid, player, user, *args, **kwargs):
        self.res_data = res_data
        self.uid = uid
        self.player = player
        self.user = user
        super().__init__(*args, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user == self.user:
            return

        if user_party_cache.get(interaction.user.id):
            user_party_cache[interaction.user.id]["方法"] = self.values[0]

        u_p_c_l = user_party_cache.get(interaction.user.id)  # user_party_cache_local

        if u_p_c_l and u_p_c_l.get("Sub") and u_p_c_l.get("方法"):
            await interaction.response.defer()
            result = await generate_image(u_p_c_l.get("Sub"), u_p_c_l.get("Main"), self.res_data, self.uid, u_p_c_l.get("方法"), interaction.user.id)
            if result == 1:
                return await interaction.followup.send("情報の正規化に失敗しました。(Convert Error)", ephemeral=True)
            elif result == 2:
                return await interaction.followup.send("情報の標準化に失敗しました。(Artifact Error)", ephemeral=True)
            elif result == 3:
                return await interaction.followup.send("画像の生成に失敗しました。エラーが多発する場合はサポートサーバーまでお問い合わせ下さい。(Generation Error)", ephemeral=True)
            elif result == 4:

                file = discord.File(f'./Tests/{self.uid}-Party.png', filename='party-image.png')

                embed = discord.Embed(title=f'パーティービルド',
                                      description=f'{self.player["Name"]} | 冒険ランク{self.player["Level"]} | 世界ランク{self.player["worldLevel"]}')
                embed.set_image(url='attachment://party-image.png')
                await interaction.followup.edit_message(message_id=interaction.message.id, embed=embed, attachments=[file])
        else:
            embed = interaction.message.embeds[0]
            embed.add_field(name="計算方法",
                            value=f'・{self.values[0]}',
                            inline=False)
            await interaction.response.edit_message(embed=embed, attachments=[])


async def generate_image(sub_chara, main_chara, res_data, uid, gen_type, user_id):
    async with aiohttp.ClientSession() as session:
        all_chara = sub_chara
        all_chara.insert(0, main_chara),
        user_party_cache[user_id]['Sub'] = user_party_cache[user_id]['Sub'][1:]

        data = {
            "data": res_data,
            "index": all_chara,
            "uid": int(uid)
        }
        async with session.post(f'http://{API_HOST_NAME}:8080/api/team/converter', json=data) as r:
            if not r.status == 200:
                return 1

    async with aiohttp.ClientSession() as session:
        data = {
            "types": gen_type,
            "uid": int(uid)
        }
        async with session.post(f'http://{API_HOST_NAME}:8080/api/team/artifacts', json=data) as r:
            if r.status == 200:
                res = await r.json()
            else:
                return 2

    async with aiohttp.ClientSession() as session:
        data = {
            "data": res[0],
            "artifact_data": res[1],
            "uid": int(uid),
        }
        async with session.post(f'http://{API_HOST_NAME}:8080/api/team/generation', json=data) as r:
            if r.status == 200:
                image_data = await r.content.read()
                img = Image.open(BytesIO(image_data))
                img.save(f'./Tests/{uid}-Party.png')
            else:
                return 3
    return 4


class EndButton(discord.ui.Button):
    def __init__(self, uid, user, *args, **kwargs):
        self.chara_data = None
        self.uid = uid
        self.user = user
        super().__init__(*args, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user == self.user:
            return
        if self.custom_id == '終了':
            self.view.stop()
            if user_party_cache.get(interaction.user.id):
                del user_party_cache[interaction.user.id]
            requests.get(f'http://{API_HOST_NAME}:8080/api/team/delete/{self.uid}')
            return await interaction.response.edit_message(view=None)


async def setup(bot):
    await bot.add_cog(Genshin(bot))
