import requests
import json
import os

from collections import Counter


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
            if art["option"] == ["元素チャージ効率", "会心ダメージ"]:
                score += art["value"]
            elif art["option"] == '会心率':
                score += (art["value"] * 2)
            else:
                continue
        return score
    elif state == '防御':
        score = 0
        for art in artifact:
            if art["option"] == ["防御パーセンテージ", "会心ダメージ"]:
                score += art["value"]
            elif art["option"] == '会心率':
                score += (art["value"] * 2)
            else:
                continue
        return score


def load_json(fp_) -> dict:
    with open(fp_, mode='r', encoding='utf-8') as f:
        res_data = json.load(f)
    return res_data


def fetch_character(avatar_id: str) -> str:
    characters_list = load_json('./data/characters.json')
    ja_name_list = load_json('./data/ja_name.json')
    character_hash = characters_list.get(str(avatar_id))["nameTextMapHash"] \
        if characters_list.get(str(avatar_id)) else None
    if not character_hash:
        return '名前取得不可'
    return ja_name_list.get(str(character_hash))


def player_info(uid) -> dict:
    res_data = load_json(f'./data/cache/{uid}.json')
    characters_list = load_json('./data/characters.json')
    namecards_list = load_json('./data/namecards.json')

    data = {}

    player_data = res_data.get("playerInfo")
    if not player_data:
        return {}
    name_card = namecards_list.get(str(player_data["nameCardId"]))
    data['Name'] = player_data["nickname"]
    data['Signature'] = player_data.get("signature")
    data['Level'] = player_data["level"]
    data['worldLevel'] = player_data["worldLevel"]
    data['Achievement'] = player_data["finishAchievementNum"]
    data['Tower'] = f'{player_data["towerFloorIndex"]}層 {player_data["towerLevelIndex"]}間'
    profile_picture = player_data.get("profilePicture")
    data['ProfilePicture'] = characters_list.get(str(profile_picture["avatarId"]))["iconName"]
    data['NameCard'] = name_card["picPath"][-1] if name_card else None
    data['showAvatarInfo'] = player_data.get("showAvatarInfoList")

    return data


def info_convert(uid, chara_index):
    characters_list = load_json('./data/characters.json')
    ja_name_list = load_json('./data/ja_name.json')
    append_prop_list = load_json('./data/append_prop_name.json')
    fight_name_list = load_json('./data/fight_name.json')

    element_ja = {'Ice': '氷', 'Wind': '風', 'Fire': '炎', 'Electric': '雷', 'Water': '水', 'Rock': '岩', 'Grass': '草'}
    element_color = {'Ice': '#00e3ff', 'Wind': '#00ffab', 'Fire': '#ff2727', 'Electric': '#ad10fd',
                     'Water': '#0050ff', 'Rock': '#ffb003', 'Grass': '#2bec0c'}

    # Converted Data
    data = {
        'Character': {},
        'Weapon': {},
        'Score': {},
        'Artifacts': {}
    }

    res_data = load_json(f'./data/cache/{uid}.json')

    # プレイヤー情報の一番最初のキャラを取得 yutarou12→万葉
    character = res_data["avatarInfoList"][chara_index]
    character_id: int = character["avatarId"]

    character_official = characters_list.get(str(character_id))
    chara_hash = character_official["nameTextMapHash"]
    chara_skill_list: list = character_official["skills"]
    chara_talent = character.get("talentIdList")
    chara_name = ja_name_list.get(f'{chara_hash}')

    # キャラクター情報
    data['Character']['Element'] = element_ja.get(character_official["costElemType"])
    data['Character']['Color'] = element_color.get(character_official["costElemType"])
    data['Character']['SideIconName'] = character_official["sideIconName"]
    data['Character']['Name'] = chara_name
    data['Character']['Const'] = 0 if not chara_talent else len(chara_talent)
    data['Character']['Level'] = character["propMap"]["4001"]["val"]
    data['Character']['Love'] = character["fetterInfo"]["expLevel"]
    data['Character']['Status'] = {}

    for key, value in character["fightPropMap"].items():
        key_name = fight_name_list.get(str(key))
        if key_name is None:
            continue
        elif key_name == f'{element_ja.get(character_official["costElemType"])}元素ダメージ':
            data['Character']['Status'][key_name] = round(value * 100, 1)
        elif key_name in ['HP', '攻撃力', '防御力', '元素熟知']:
            data['Character']['Status'][key_name] = round(value)
        elif key_name in ['会心率', '会心ダメージ', '元素チャージ効率']:
            data['Character']['Status'][key_name] = round(value * 100, 1)
        else:
            continue

    data['Character']['Base'] = {
        "HP": round(character["fightPropMap"]["1"]),
        "攻撃力": round(character["fightPropMap"]["4"]),
        "防御力": round(character["fightPropMap"]["7"])
    }
    data['Character']['Talent'] = {
        "通常": character["skillLevelMap"][f'{chara_skill_list[0]}'],
        "スキル": character["skillLevelMap"][f'{chara_skill_list[1]}'],
        "爆発": character["skillLevelMap"][f'{chara_skill_list[2]}']
    }

    # 武器情報
    weapon_item = None
    for i in character["equipList"]:
        if i["flat"]["itemType"] == "ITEM_WEAPON":
            weapon_item = i
            break
    weapon_base_attack = None
    if weapon_item:
        for i in weapon_item["flat"]["weaponStats"]:
            if i["appendPropId"] == "FIGHT_PROP_BASE_ATTACK":
                weapon_base_attack = i["statValue"]
                weapon_item["flat"]["weaponStats"].remove(i)
        if weapon_item["flat"]["weaponStats"]:
            weapon_sub_op = weapon_item["flat"]["weaponStats"][0]
        else:
            weapon_sub_op = None

        data['Weapon']['name'] = ja_name_list.get(weapon_item["flat"]["nameTextMapHash"])
        data['Weapon']['Level'] = weapon_item["weapon"]["level"]
        if weapon_item["weapon"].get("affixMap"):
            data['Weapon']['totu'] = int(list(weapon_item["weapon"]["affixMap"].values())[0]) + 1
        else:
            data['Weapon']['totu'] = 1
        data['Weapon']['rarelity'] = weapon_item["flat"]["rankLevel"]
        data['Weapon']['BaseATK'] = weapon_base_attack
        if weapon_sub_op:
            data['Weapon']['Sub'] = {
                "name": append_prop_list.get(weapon_sub_op["appendPropId"]),
                "value": weapon_sub_op["statValue"]
            }
    if weapon_item:
        character["equipList"].remove(weapon_item)
    bracer_data = {}
    necklace_data = {}
    shoes_data = {}
    ring_data = {}
    dress_data = {}
    for i in character["equipList"]:
        if i["flat"]["equipType"] == "EQUIP_BRACER":
            bracer_data = i
        elif i["flat"]["equipType"] == "EQUIP_NECKLACE":
            necklace_data = i
        elif i["flat"]["equipType"] == "EQUIP_SHOES":
            shoes_data = i
        elif i["flat"]["equipType"] == "EQUIP_RING":
            ring_data = i
        elif i["flat"]["equipType"] == "EQUIP_DRESS":
            dress_data = i

    artifacts_data = {
        'flower': ja_name_list.get(bracer_data["flat"]["setNameTextMapHash"]) if bracer_data else None,
        'wing': ja_name_list.get(necklace_data["flat"]["setNameTextMapHash"]) if necklace_data else None,
        'clock': ja_name_list.get(shoes_data["flat"]["setNameTextMapHash"]) if shoes_data else None,
        'cup': ja_name_list.get(ring_data["flat"]["setNameTextMapHash"]) if ring_data else None,
        'crown': ja_name_list.get(dress_data["flat"]["setNameTextMapHash"]) if dress_data else None
    }

    atf_type = list()
    for parts in ['flower', "wing", "clock", "cup", "crown"]:
        if artifacts_data[parts]:
            atf_type.append(artifacts_data[parts])
        else:
            continue

    set_bounus = Counter([x for x in atf_type if atf_type.count(x) >= 2])
    final_set_bounus = list()
    for n, q in set_bounus.items():
        if len(set_bounus) == 2:
            final_set_bounus.append((q, n))
        if len(set_bounus) == 1:
            final_set_bounus.append((q, n))

    data['Score']['Bonus'] = final_set_bounus

    with open(f'./data/cache/{uid}-character.json', mode='w') as f:
        json.dump(data, f, indent=4)

    backup_list = res_data["avatarInfoList"][chara_index]
    res_data["avatarInfoList"].clear()
    res_data["avatarInfoList"].append(backup_list)
    with open(f'./data/cache/{uid}-fixed.json', mode='w') as f:
        json.dump(res_data, f, indent=4)


def artifacts_convert(uid, c_type):
    ja_name_list = load_json('./data/ja_name.json')
    append_prop_list = load_json('./data/append_prop_name.json')
    data = load_json(f'./data/cache/{uid}-character.json')
    res_data = load_json(f'./data/cache/{uid}-fixed.json')
    character = res_data["avatarInfoList"][0]

    artifacts_list = character["equipList"]

    # 聖遺物
    bracer_data = {}
    necklace_data = {}
    shoes_data = {}
    ring_data = {}
    dress_data = {}
    for i in artifacts_list:
        if i["flat"]["equipType"] == "EQUIP_BRACER":
            bracer_data = i
        elif i["flat"]["equipType"] == "EQUIP_NECKLACE":
            necklace_data = i
        elif i["flat"]["equipType"] == "EQUIP_SHOES":
            shoes_data = i
        elif i["flat"]["equipType"] == "EQUIP_RING":
            ring_data = i
        elif i["flat"]["equipType"] == "EQUIP_DRESS":
            dress_data = i

    # 聖遺物の種類(例：剣闘士のフィナーレ)
    # 花
    data['Artifacts']['flower'] = {}
    flower = data['Artifacts']['flower']
    if bracer_data:
        flower['type'] = ja_name_list.get(bracer_data["flat"]["setNameTextMapHash"])
        flower['main'] = {}
        flower['main']['option'] = append_prop_list.get(bracer_data["flat"]["reliquaryMainstat"]["mainPropId"])
        flower['main']['value'] = bracer_data["flat"]["reliquaryMainstat"]["statValue"]
        flower['sub'] = []
        flower['Level'] = bracer_data["reliquary"]["level"] - 1
        flower['rarelity'] = bracer_data["flat"]["rankLevel"]

        for sub in bracer_data["flat"]["reliquarySubstats"]:
            append_data = {
                "option": append_prop_list.get(sub["appendPropId"]),
                "value": sub["statValue"]
            }
            flower['sub'].append(append_data)
    else:
        flower = {}

    # 羽
    data['Artifacts']['wing'] = {}
    wing = data['Artifacts']['wing']
    if necklace_data:
        wing['type'] = ja_name_list.get(necklace_data["flat"]["setNameTextMapHash"])
        wing['main'] = {}
        wing['main']['option'] = append_prop_list.get(necklace_data["flat"]["reliquaryMainstat"]["mainPropId"])
        wing['main']['value'] = necklace_data["flat"]["reliquaryMainstat"]["statValue"]
        wing['sub'] = []
        wing['Level'] = necklace_data["reliquary"]["level"] - 1
        wing['rarelity'] = necklace_data["flat"]["rankLevel"]

        for sub in necklace_data["flat"]["reliquarySubstats"]:
            append_data = {
                "option": append_prop_list.get(sub["appendPropId"]),
                "value": sub["statValue"]
            }
            wing['sub'].append(append_data)
    else:
        wing = {}

    # 時計
    data['Artifacts']['clock'] = {}
    clock = data['Artifacts']['clock']
    if shoes_data:
        clock['type'] = ja_name_list.get(shoes_data["flat"]["setNameTextMapHash"])
        clock['main'] = {}
        clock['main']['option'] = append_prop_list.get(shoes_data["flat"]["reliquaryMainstat"]["mainPropId"])
        clock['main']['value'] = shoes_data["flat"]["reliquaryMainstat"]["statValue"]
        clock['sub'] = []
        clock['Level'] = shoes_data["reliquary"]["level"] - 1
        clock['rarelity'] = shoes_data["flat"]["rankLevel"]

        for sub in shoes_data["flat"]["reliquarySubstats"]:
            append_data = {
                "option": append_prop_list.get(sub["appendPropId"]),
                "value": sub["statValue"]
            }
            clock['sub'].append(append_data)
    else:
        clock = {}

    # 杯
    data['Artifacts']['cup'] = {}
    cup = data['Artifacts']['cup']
    if ring_data:
        cup['type'] = ja_name_list.get(ring_data["flat"]["setNameTextMapHash"])
        cup['main'] = {}
        cup['main']['option'] = append_prop_list.get(ring_data["flat"]["reliquaryMainstat"]["mainPropId"])
        cup['main']['value'] = ring_data["flat"]["reliquaryMainstat"]["statValue"]
        cup['sub'] = []
        cup['Level'] = ring_data["reliquary"]["level"] - 1
        cup['rarelity'] = ring_data["flat"]["rankLevel"]

        for sub in ring_data["flat"]["reliquarySubstats"]:
            append_data = {
                "option": append_prop_list.get(sub["appendPropId"]),
                "value": sub["statValue"]
            }
            cup['sub'].append(append_data)
    else:
        cup = {}

    # 冠
    data['Artifacts']['crown'] = {}
    crown = data['Artifacts']['crown']
    if dress_data:
        crown['type'] = ja_name_list.get(dress_data["flat"]["setNameTextMapHash"])
        crown['main'] = {}
        crown['main']['option'] = append_prop_list.get(dress_data["flat"]["reliquaryMainstat"]["mainPropId"])
        crown['main']['value'] = dress_data["flat"]["reliquaryMainstat"]["statValue"]
        crown['sub'] = []
        crown['Level'] = dress_data["reliquary"]["level"] - 1
        crown['rarelity'] = dress_data["flat"]["rankLevel"]

        for sub in dress_data["flat"]["reliquarySubstats"]:
            append_data = {
                "option": append_prop_list.get(sub["appendPropId"]),
                "value": sub["statValue"]
            }
            crown['sub'].append(append_data)
    else:
        crown = {}

    data['Score']['State'] = c_type
    data['Score']['flower'] = round(calculate_score(c_type, flower['sub']), 1) if flower else 0
    data['Score']['wing'] = round(calculate_score(c_type, wing['sub']), 1) if wing else 0
    data['Score']['clock'] = round(calculate_score(c_type, clock['sub']), 1) if clock else 0
    data['Score']['cup'] = round(calculate_score(c_type, cup['sub']), 1) if cup else 0
    data['Score']['crown'] = round(calculate_score(c_type, crown['sub']), 1) if crown else 0
    data['Score']['total'] = round(data['Score']['flower'] + data['Score']['wing'] + data['Score']['clock'] + data['Score']['cup'] + data['Score']['crown'], 1)

    return data
