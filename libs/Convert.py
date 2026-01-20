import json
from typing import Optional
from discord import Asset


def load_json(fp_) -> dict:
    with open(fp_, mode='r', encoding='utf-8') as f:
        res_data = json.load(f)
    return res_data


def fetch_character(avatar_id: str) -> str:
    characters_list = load_json('./data/characters.json')
    ja_name_list = load_json('./data/ja_name.json')
    character_hash = characters_list.get(str(avatar_id))["NameTextMapHash"] \
        if characters_list.get(str(avatar_id)) else None
    if not character_hash:
        return '名前取得不可'
    return ja_name_list.get(str(character_hash))


def icon_convert(icon: Optional[Asset]) -> str:
    if not icon:
        return 'https://cdn.discordapp.com/embed/avatars/0.png'
    else:
        return icon.replace(format='png').url


def medal_emoji_str_convert(medal_id: int) -> str:
    medal_dict = {
        1: '<:LeyLineChallenge_Medal_1:1463116038542721095>',
        2: '<:LeyLineChallenge_Medal_2:1463116014278541355>',
        3: '<:LeyLineChallenge_Medal_3:1463080495826075740>',
        4: '<:LeyLineChallenge_Medal_4:1463080494097764442>',
        5: '<:LeyLineChallenge_Medal_5:1463080492331958384>',
        6: '<:LeyLineChallenge_Medal_6:1463080491031855283>',
        7: '<:LeyLineChallenge_Medal_7:1463080489404469374>',
    }
    return medal_dict.get(medal_id)


def discord_emoji_str_convert(name: str) -> str:
    icon_dict = {
        "HP": "<:A_PROP_HP:1463118298462945280>",
        "攻撃力": "<:A_PROP_ATTACK:1463118246516363418>",
        "防御力": "<:A_PROP_DEFENSE:1463118193202696337>",
        "会心率": "<:A_PROP_CRITICAL:1463118131311673405>",
        "会心ダメージ": "<:A_PROP_CRITICAL_HURT:1463118038118301706>",
        "元素チャージ効率": "<:A_PROP_CHARGE_EFFICIENCY:1463117860107849908>",
        "元素熟知": "<:A_PROP_ELEMENT_MASTERY:1463117703387545600>",
        "物理ダメージ": "<:A_PROP_PHYSICAL_HURT:1463117425313583246>",
        "炎元素ダメージ": "<:E_PROP_FIRE_HURT:1463117401959829544>",
        "雷元素ダメージ": "<:E_PROP_ELEC_HURT:1463117383911866544>",
        "水元素ダメージ": "<:E_PROP_WATER_HURT:1463117367713337608>",
        "風元素ダメージ": "<:E_PROP_WIND_HURT:1463117347253649429>",
        "氷元素ダメージ": "<:E_PROP_ICE_HURT:1463117328353857578>",
        "岩元素ダメージ": "<:E_PROP_ROCK_HURT:1463117304425615453>",
        "草元素ダメージ": "<:E_PROP_GRASS_HURT:1463117283714011178>"
    }

    return icon_dict.get(name)


def load_characters_by_element(json_path):
    with open(json_path, encoding='utf-8', mode='r') as f:
        data = json.load(f)
    elements = {}
    for cid, cdata in data.items():
        element = cdata.get('Element')
        if element is None:
            continue
        if element == "None":
            continue
        if element not in elements:
            elements[element] = []
        elements[element].append({
            'id': cid,
            'name_hash': cdata.get('NameTextMapHash'),
            'icon': cdata.get('SideIconName')
        })
    return elements


def traveler_or_other_name(name: str, icon: str):
    if name == "旅人":
        if icon.split('_')[-1].split('.')[0] == 'PlayerBoy':
            return '空'
        else:
            return '蛍'
    else:
        return name
