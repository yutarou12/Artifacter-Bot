import datetime
import json
import os
import random
from io import BytesIO

import aiohttp
import discord
import requests
from PIL import Image
from discord import Embed
from discord.ext import commands

from libs.Convert import icon_convert
from libs.env import API_HOST_NAME, GENERATE_ERROR_CHANNEL_ID, ERROR_CHANNEL_ID


def calculate_score(state, artifact: list) -> int:
    if state == '攻撃':
        # 攻撃力換算
        score = 0
        for art in artifact:
            if art["option"] in ["攻撃パーセンテージ", "会心ダメージ"]:
                score += art["value"]
            elif art["option"] == '会心率':
                score += (art["value"] * 2)
            else:
                continue
        return score
    elif state == 'HP':
        score = 0
        for art in artifact:
            if art["option"] in ["HPパーセンテージ", "会心ダメージ"]:
                score += art["value"]
            elif art["option"] == '会心率':
                score += (art["value"] * 2)
            else:
                continue
        return score
    elif state == '元素熟知':
        score = 0
        for art in artifact:
            if art["option"] == "会心ダメージ":
                score += art["value"]
            elif art["option"] == '会心率':
                score += (art["value"] * 2)
            elif art["option"] == '元素熟知':
                score += (art["value"] * 0.25)
            else:
                continue
        return score
    elif state == 'チャージ':
        score = 0
        for art in artifact:
            if art["option"] in ["元素チャージ効率", "会心ダメージ"]:
                score += art["value"]
            elif art["option"] == '会心率':
                score += (art["value"] * 2)
            else:
                continue
        return score
    elif state == '防御':
        score = 0
        for art in artifact:
            if art["option"] in ["防御パーセンテージ", "会心ダメージ"]:
                score += art["value"]
            elif art["option"] == '会心率':
                score += (art["value"] * 2)
            else:
                continue
        return score
    elif state == '会心':
        score = 0
        for art in artifact:
            if art["option"] in ["会心ダメージ"]:
                score += art["value"]
            elif art["option"] == '会心率':
                score += (art["value"] * 2)
            else:
                continue
        return score


async def generate_error_send(uid, error, ctx: discord.ext.commands.Context) -> None:
    # 画像生成時のエラーを検出・送信 - 2
    ch = await ctx.bot.fetch_channel(GENERATE_ERROR_CHANNEL_ID)
    embed = Embed(title='Generation Error Log')
    embed.set_author(name=f'{ctx.author.display_name} ({ctx.author.id})',
                     icon_url=icon_convert(ctx.author.avatar))
    embed.add_field(name='UID', value=f'`{uid}`', inline=False)
    embed.add_field(name='User', value=f'`{ctx.author.id}`', inline=False)
    embed.add_field(name='Error', value=f'```{error}```', inline=False)

    await ch.send(embed=embed)


async def error_message_send_ch(error_channel, ctx: discord.ext.commands.Context, error) -> None:
    embed_logs = Embed(title='Error Log')
    embed_logs.set_author(name=f'{ctx.author.display_name} ({ctx.author.id})',
                          icon_url=icon_convert(ctx.author.avatar))
    embed_logs.add_field(name='Error', value=f'```{error}```', inline=False)
    if ctx.channel.type == discord.ChannelType.text:
        embed_logs.set_footer(
            text=f'{ctx.channel.name} \nG:{ctx.guild.id} C:{ctx.channel.id}',
            icon_url=icon_convert(ctx.guild.icon))
    else:
        embed_logs.set_footer(text=f"{ctx.author}'s DM_CHANNEL C:{ctx}")
    await error_channel.send(embed=embed_logs)


def get_last_month() -> int:
    today = datetime.datetime.today()
    first_day_of_current_month = today.replace(day=1)
    last_day_of_last_month = first_day_of_current_month - datetime.timedelta(days=1)
    return last_day_of_last_month.month


def get_json():
    if not os.path.exists(f'./data/admin/EquipAffixExcelConfigData-{datetime.datetime.today().month}.json'):
        res = requests.get("https://gitlab.com/Dimbreath/AnimeGameData/-/raw/master/ExcelBinOutput/EquipAffixExcelConfigData.json")
        with open(f'./data/EquipAffixExcelConfigData-{datetime.datetime.today().month}.json', 'w', encoding='utf-8') as f:
            json.dump(res.json(), f, ensure_ascii=False, indent=4)
        os.remove(f'./data/EquipAffixExcelConfigData-{get_last_month()}.json')

    if not os.path.exists(f'./data/admin/ReliquarySetExcelConfigData{datetime.datetime.today().month}.json'):
        res = requests.get("https://gitlab.com/Dimbreath/AnimeGameData/-/raw/master/ExcelBinOutput/ReliquarySetExcelConfigData.json")
        with open(f'./data/ReliquarySetExcelConfigData-{datetime.datetime.today().month}.json', 'w', encoding='utf-8') as f:
            json.dump(res.json(), f, ensure_ascii=False, indent=4)
        os.remove(f'./data/admin/ReliquarySetExcelConfigData-{get_last_month()}.json')

    if not os.path.exists(f'./data/admin/ReliquaryExcelConfigData-{datetime.datetime.today().month}.json'):
        res = requests.get("https://gitlab.com/Dimbreath/AnimeGameData/-/raw/master/ExcelBinOutput/ReliquaryExcelConfigData.json")
        with open(f'./data/admin/ReliquaryExcelConfigData-{datetime.datetime.today().month}.json', 'w', encoding='utf-8') as f:
            json.dump(res.json(), f, ensure_ascii=False, indent=4)
        os.remove(f'./data/admin/ReliquaryExcelConfigData-{get_last_month()}.json')

    if not os.path.exists(f'./data/admin/TextMapJP-{datetime.datetime.today().month}.json'):
        res = requests.get("https://gitlab.com/Dimbreath/AnimeGameData/-/raw/master/TextMap/TextMapJP.json")
        with open(f'./data/admin/TextMapJP-{datetime.datetime.today().month}.json', 'w', encoding='utf-8') as f:
            json.dump(res.json(), f, ensure_ascii=False, indent=4)
        os.remove(f'./data/admin/TextMapJP-{get_last_month()}.json')

    if not os.path.exists(f'./data/admin/WeaponExcelConfigData-{datetime.datetime.today().month}.json'):
        res = requests.get("https://gitlab.com/Dimbreath/AnimeGameData/-/raw/master/ExcelBinOutput/WeaponExcelConfigData.json")
        with open(f'./data/admin/WeaponExcelConfigData-{datetime.datetime.today().month}.json', 'w', encoding='utf-8') as f:
            json.dump(res.json(), f, ensure_ascii=False, indent=4)
        os.remove(f'./data/admin/WeaponExcelConfigData-{get_last_month()}.json')


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='build', hidden=True)
    @commands.is_owner()
    async def cmd_admin_build(self, ctx: commands.Context, character_name, artifact, weapon_=None, c_type='攻撃'):
        """任意のビルド画像を生成します。"""
        get_json()

        with open('./data/characters.json', 'r', encoding='utf-8') as f:
            chara_all_list = json.load(f)

        with open('./data/ja_name.json', 'r', encoding='utf-8') as f:
            ja_name_list = json.load(f)

        with open('./data/append_prop_name.json', 'r', encoding='utf-8') as f:
            append_prop_list = json.load(f)

        with open(f'./data/admin/EquipAffixExcelConfigData-{datetime.datetime.today().month}.json', 'r', encoding='utf-8') as f:
            equip_affix_data = json.load(f)

        with open(f'./data/admin/ReliquarySetExcelConfigData-{datetime.datetime.today().month}.json', 'r', encoding='utf-8') as f:
            reliquary_set_data = json.load(f)

        with open(f'./data/admin/ReliquaryExcelConfigData-{datetime.datetime.today().month}.json', 'r', encoding='utf-8') as f:
            artifact_data = json.load(f)

        with open(f'./data/admin/TextMapJP-{datetime.datetime.today().month}.json', 'r', encoding='utf-8') as f:
            artifact_ja_name_list = json.load(f)

        with open(f'./data/admin/WeaponExcelConfigData-{datetime.datetime.today().month}.json', 'r', encoding='utf-8') as f:
            weapon_data = json.load(f)

        chara_name_list = {}

        for avatar_id, data in chara_all_list.items():
            name_hash = str(data.get("NameTextMapHash"))
            ja_name = ja_name_list.get(name_hash)
            if ja_name:
                chara_name_list[ja_name] = avatar_id

        avatar_id = chara_name_list.get(character_name)
        if not avatar_id:
            return await ctx.send('> キャラクター名が見つかりません。', ephemeral=True)
        else:
            avatar_id = str(avatar_id)

        element_ja = {'Ice': '氷', 'Wind': '風', 'Fire': '炎', 'Electric': '雷', 'Water': '水', 'Rock': '岩',
                      'Grass': '草'}
        element_color = {'Ice': '#00e3ff', 'Wind': '#00ffab', 'Fire': '#ff2727', 'Electric': '#ad10fd',
                         'Water': '#0050ff', 'Rock': '#ffb003', 'Grass': '#2bec0c'}

        chara_base_data = chara_all_list.get(avatar_id)
        generate_data = {}
        generate_data['Character'] = {}
        generate_data['Weapon'] = {}
        generate_data['Artifacts'] = {}
        generate_data['Score'] = {}

        # キャラクター情報
        generate_data['Character']['Id'] = avatar_id
        generate_data['Character']['Element'] = element_ja.get(chara_base_data.get("Element"))
        generate_data['Character']['Color'] = element_color.get(chara_base_data.get("Element"))
        generate_data['Character']['SideIconName'] = chara_base_data.get("SideIconName")
        generate_data['Character']['Costume'] = None
        generate_data['Character']['Name'] = chara_base_data.get("NameTextMapHash")
        generate_data['Character']['Const'] = 6
        generate_data['Character']['Level'] = 90
        generate_data['Character']['Love'] = 10
        generate_data['Character']['Status'] = {}

        # キャラクターステータス情報
        generate_data['Character']['Status']['HP'] = 50000
        generate_data['Character']['Status']['攻撃力'] = 3000
        generate_data['Character']['Status']['防御力'] = 2000
        generate_data['Character']['Status']['会心率'] = 100.0
        generate_data['Character']['Status']['会心ダメージ'] = 200.0
        generate_data['Character']['Status']['元素チャージ効率'] = 200.0
        generate_data['Character']['Status']['元素熟知'] = 500
        generate_data['Character']['Status'][f'{element_ja.get(chara_base_data.get("Element"))}ダメージ'] = 0.0

        # キャラクターベース情報
        generate_data['Character']['Base'] = {
            "HP": 10000,
            "攻撃力": 1000,
            "防御力": 500
        }

        generate_data['Character']['Talent'] = {
            "通常": 10,
            "スキル": 10 + 3 if generate_data['Character']['Const'] >= 3 else 10,
            "爆発": 10 + 3 if generate_data['Character']['Const'] >= 5 else 10,
        }

        weapon_list = {}

        for data in weapon_data:
            name_hash = str(data.get("nameTextMapHash"))
            ja_name = ja_name_list.get(name_hash)
            if ja_name is None:
                continue
            weapon_list[ja_name] = {
                "NameTextMapHash": name_hash,
                "WeaponType": data.get("weaponType"),
                "Rarity": data.get("rankLevel"),
                "Icon": data.get("icon"),
                "WeaponProp": data.get("weaponProp")
            }

        if weapon_ is None:
            weapon_type_list = []
            for w_name, w_data in weapon_list.items():
                if w_data.get("WeaponType") == chara_base_data.get("WeaponType"):
                    weapon_type_list.append(w_name)
            random_weapon_name = random.choice(weapon_type_list)
            weapon = random_weapon_name
        else:
            weapon = weapon_

        weapon_data = weapon_list.get(weapon)
        if not weapon_data:
            return await ctx.send('> 武器が見つかりません。', ephemeral=True)

        weapon_base_attack = 0
        for i in weapon_data.get("WeaponProp"):
            if i["propType"] == "FIGHT_PROP_BASE_ATTACK":
                weapon_base_attack = i["initValue"]
                weapon_data["WeaponProp"].remove(i)
            else:
                weapon_base_attack = 0
        if weapon_data.get("WeaponProp"):
            weapon_sub_op = weapon_data.get("WeaponProp")[0]
        else:
            weapon_sub_op = None

        generate_data['Weapon']['name'] = weapon_data.get("NameTextMapHash")
        generate_data['Weapon']['Icon'] = weapon_data.get("Icon")
        generate_data['Weapon']['Rarity'] = weapon_data.get("Rarity")
        generate_data['Weapon']['Level'] = 90
        generate_data['Weapon']['totu'] = 5
        generate_data['Weapon']['BaseATK'] = weapon_base_attack
        generate_data['Weapon']['Sub'] = {
            "name": append_prop_list.get(weapon_sub_op["propType"]),
            "value": weapon_sub_op["initValue"]
        }

        # 聖遺物情報
        artifact_list = {}
        for n in ['EQUIP_BRACER', 'EQUIP_NECKLACE', 'EQUIP_SHOES', 'EQUIP_RING', 'EQUIP_DRESS']:
            artifact_list[n] = {}
            for data in artifact_data:
                if data.get("equipType") != n:
                    continue
                set_id = data.get("setId")
                equip_affix_id = None
                for d in reliquary_set_data:
                    if d.get("setId") == set_id:
                        equip_affix_id = d.get("equipAffixId")
                        break
                if equip_affix_id is None:
                    continue

                name_hash = None
                for d in equip_affix_data:
                    if d.get("id") == equip_affix_id:
                        name_hash = str(d.get("nameTextMapHash"))
                        break
                if name_hash is None:
                    continue

                ja_name = artifact_ja_name_list.get(name_hash)
                if ja_name is None:
                    continue
                artifact_list[n][ja_name] = {
                    "NameTextMapHash": name_hash,
                    "Icon": data.get("icon"),
                    "Rarity": data.get("rankLevel"),
                    "SetId": data.get("setId"),
                }

        artifact_sub_data = [{"appendPropId": "会心率", "statValue":15}, {"appendPropId": "会心ダメージ", "statValue":20}, {"appendPropId": "攻撃パーセンテージ", "statValue":15}, {"appendPropId": "元素チャージ効率", "statValue":15}]
        artifact_main_data = {
            "EQUIP_BRACER": {"mainPropId": "HP", "statValue":4780},
            "EQUIP_NECKLACE": {"mainPropId": "攻撃力", "statValue": 311},
            "EQUIP_SHOES": {"mainPropId": "元素チャージ効率", "statValue": 46.6},
            "EQUIP_RING": {"mainPropId": "会心率", "statValue": 31.1},
            "EQUIP_DRESS": {"mainPropId": "会心ダメージ", "statValue": 46.6},
        }
        if not artifact_list.get('EQUIP_BRACER').get(artifact):
            return await ctx.send('> 聖遺物が見つかりません。', ephemeral=True)

        generate_data['Artifacts']['flower'] = {}
        bracer_data = artifact_list.get('EQUIP_BRACER').get(artifact)
        generate_data['Artifacts']['flower']['type'] = bracer_data.get("NameTextMapHash")
        generate_data['Artifacts']['flower']['icon'] = bracer_data.get("Icon").replace("Eff_", "")
        generate_data['Artifacts']['flower']['main'] = {}
        generate_data['Artifacts']['flower']['main']['option'] = artifact_main_data.get('EQUIP_BRACER')["mainPropId"]
        generate_data['Artifacts']['flower']['main']['value'] = artifact_main_data.get('EQUIP_BRACER')["statValue"]
        generate_data['Artifacts']['flower']['sub'] = []
        generate_data['Artifacts']['flower']['Level'] = 20
        generate_data['Artifacts']['flower']['rarelity'] = bracer_data.get("Rarity")

        for sub in artifact_sub_data:
            append_data = {
                "option": sub["appendPropId"],
                "value": sub["statValue"]
            }
            generate_data['Artifacts']['flower']['sub'].append(append_data)

        # 羽
        generate_data['Artifacts']['wing'] = {}
        necklace_data = artifact_list.get('EQUIP_NECKLACE').get(artifact)
        generate_data['Artifacts']['wing']['type'] = necklace_data.get("NameTextMapHash")
        generate_data['Artifacts']['wing']['icon'] = necklace_data.get("Icon").replace("Eff_", "")
        generate_data['Artifacts']['wing']['main'] = {}
        generate_data['Artifacts']['wing']['main']['option'] = artifact_main_data.get('EQUIP_NECKLACE').get("mainPropId")
        generate_data['Artifacts']['wing']['main']['value'] = artifact_main_data.get('EQUIP_NECKLACE').get("statValue")
        generate_data['Artifacts']['wing']['sub'] = []
        generate_data['Artifacts']['wing']['Level'] = 20
        generate_data['Artifacts']['wing']['rarelity'] = necklace_data.get("Rarity")

        for sub in artifact_sub_data:
            append_data = {
                "option": sub["appendPropId"],
                "value": sub["statValue"]
            }
            generate_data['Artifacts']['wing']['sub'].append(append_data)

        # 時計
        generate_data['Artifacts']['clock'] = {}
        shoes_data = artifact_list.get('EQUIP_SHOES').get(artifact)
        generate_data['Artifacts']['clock']['type'] = shoes_data.get("NameTextMapHash")
        generate_data['Artifacts']['clock']['icon'] = shoes_data.get("Icon").replace("Eff_", "")
        generate_data['Artifacts']['clock']['main'] = {}
        generate_data['Artifacts']['clock']['main']['option'] = artifact_main_data.get('EQUIP_SHOES').get("mainPropId")
        generate_data['Artifacts']['clock']['main']['value'] = artifact_main_data.get('EQUIP_SHOES').get("statValue")
        generate_data['Artifacts']['clock']['sub'] = []
        generate_data['Artifacts']['clock']['Level'] = 20
        generate_data['Artifacts']['clock']['rarelity'] = shoes_data.get("Rarity")

        for sub in artifact_sub_data:
            append_data = {
                "option": sub["appendPropId"],
                "value": sub["statValue"]
            }
            generate_data['Artifacts']['clock']['sub'].append(append_data)

        # 杯
        generate_data['Artifacts']['cup'] = {}
        ring_data = artifact_list.get('EQUIP_RING').get(artifact)
        generate_data['Artifacts']['cup']['type'] = ring_data.get("NameTextMapHash")
        generate_data['Artifacts']['cup']['icon'] = ring_data.get("Icon").replace("Eff_", "")
        generate_data['Artifacts']['cup']['main'] = {}
        generate_data['Artifacts']['cup']['main']['option'] = artifact_main_data.get('EQUIP_RING').get("mainPropId")
        generate_data['Artifacts']['cup']['main']['value'] = artifact_main_data.get('EQUIP_RING').get("statValue")
        generate_data['Artifacts']['cup']['sub'] = []
        generate_data['Artifacts']['cup']['Level'] = 20
        generate_data['Artifacts']['cup']['rarelity'] = ring_data.get("Rarity")

        for sub in artifact_sub_data:
            append_data = {
                "option": sub["appendPropId"],
                "value": sub["statValue"]
            }
            generate_data['Artifacts']['cup']['sub'].append(append_data)

        # 冠
        generate_data['Artifacts']['crown'] = {}
        dress_data = artifact_list.get('EQUIP_DRESS').get(artifact)
        generate_data['Artifacts']['crown']['type'] = dress_data.get("NameTextMapHash")
        generate_data['Artifacts']['crown']['icon'] = dress_data.get("Icon").replace("Eff_", "")
        generate_data['Artifacts']['crown']['main'] = {}
        generate_data['Artifacts']['crown']['main']['option'] = artifact_main_data.get('EQUIP_DRESS').get("mainPropId")
        generate_data['Artifacts']['crown']['main']['value'] = artifact_main_data.get('EQUIP_DRESS').get("statValue")
        generate_data['Artifacts']['crown']['sub'] = []
        generate_data['Artifacts']['crown']['Level'] = 20
        generate_data['Artifacts']['crown']['rarelity'] = dress_data.get("Rarity")

        for sub in artifact_sub_data:
            append_data = {
                "option": sub["appendPropId"],
                "value": sub["statValue"]
            }
            generate_data['Artifacts']['crown']['sub'].append(append_data)

        generate_data['Score']['State'] = c_type
        generate_data['Score']['flower'] = round(calculate_score(c_type, generate_data['Artifacts']['flower']['sub']), 1)
        generate_data['Score']['wing'] = round(calculate_score(c_type, generate_data['Artifacts']['wing']['sub']), 1)
        generate_data['Score']['clock'] = round(calculate_score(c_type, generate_data['Artifacts']['clock']['sub']), 1)
        generate_data['Score']['cup'] = round(calculate_score(c_type, generate_data['Artifacts']['cup']['sub']), 1)
        generate_data['Score']['crown'] = round(calculate_score(c_type, generate_data['Artifacts']['crown']['sub']), 1)
        generate_data['Score']['total'] = round(
            generate_data['Score']['flower'] + generate_data['Score']['wing'] + generate_data['Score']['clock'] + generate_data['Score']['cup'] +
            generate_data['Score']['crown'], 1)

        async with aiohttp.ClientSession() as session:
            data = {
                "data": generate_data,
                "uid": "admin-build",
            }
            async with session.post(f'http://{API_HOST_NAME}:8080/api/generation', json=data) as r:
                if r.status == 200:
                    image_data = await r.content.read()
                    img = Image.open(BytesIO(image_data))
                    img.save(f'./Tests/admin-build-Image.png')
                elif r.status == 404:
                    await generate_error_send("admin-build", "Error in `/api/generation`\n\nStatus Code: 404", ctx)
                    return await ctx.send(
                        '画像が生成されませんでした。何回も発生する場合は公式サーバーまでお問い合わせください。',
                        ephemeral=True)
                else:
                    error_channel = await ctx.bot.fetch_channel(ERROR_CHANNEL_ID)
                    await error_message_send_ch(error_channel, ctx, await r.content.read())
                    await generate_error_send("admin-build", f"Error in `/api/generation`\n\nStatus Code: {r.status}",
                                              ctx)
                    return await ctx.send('生成できませんでした。', ephemeral=True)

        chara_rank = 'SS'
        character = generate_data["Character"]
        set_bonus_text = ''
        for q, n in generate_data['Score']['Bonus']:
            set_bonus_text += f'**{q}セット** `{n}`\n'

        file = discord.File(f'./Tests/admin-build-Image.png', filename='image.png')

        embed = discord.Embed(title=f'キャラクター評価: {chara_rank}',
                              description=f'ゆう | 冒険ランク60 | 世界ランク9',
                              color=discord.Color.from_str(character["Color"]))
        embed.set_author(name=f'{character["Name"]}のステータス',
                         icon_url=f'https://enka.network/{character["SideIconName"]}')
        embed.add_field(name='セット効果', value=f'{set_bonus_text}')
        embed.set_footer(text=f'Lv.{character["Level"]} ・ 好感度{character["Love"]} ・ '
                              f'スコア:{generate_data["Score"]["total"]}/{generate_data["Score"]["State"]}換算')
        embed.set_image(url='attachment://image.png')
        return await ctx.send(file=file, embed=embed)


async def setup(bot):
    await bot.add_cog(Admin(bot))
