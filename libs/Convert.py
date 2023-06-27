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
    character_hash = characters_list.get(str(avatar_id))["nameTextMapHash"] \
        if characters_list.get(str(avatar_id)) else None
    if not character_hash:
        return '名前取得不可'
    return ja_name_list.get(str(character_hash))


def icon_convert(icon: Optional[Asset]) -> str:
    if not icon:
        return 'https://cdn.discordapp.com/embed/avatars/0.png'
    else:
        return icon.replace(format='png').url
