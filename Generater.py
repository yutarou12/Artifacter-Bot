from io import BytesIO
from PIL import Image, ImageFont, ImageDraw, ImageEnhance, ImageFile
import codecs
import json
import os
import itertools
from collections import Counter
import base64

ImageFile.LOAD_TRUNCATED_IMAGES = True


def culculate_op(data: dict):
    cwd = os.path.dirname(os.path.abspath(__file__))
    with codecs.open(f'{cwd}/Assets/duplicate.json', 'r', encoding='utf-8') as f:
        dup = json.load(f)
    with codecs.open(f'{cwd}/Assets/subopM.json', 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    res = [None, None, None, None]
    keymap = list(map(str, data.keys()))

    is_dup = []
    # 重複するものがあるか判定
    for ctg, state in data.items():
        dup_value = dup[ctg]['ov']
        if str(state) in dup_value:
            is_dup.append((ctg, state))

    # フラグの設定
    counter_flag = 0
    dup_ctg = [i[0] for i in is_dup]
    maxium_state_ct = 9

    # 重複が 0 の時の処理
    if not len(is_dup):
        for ctg, state in data.items():
            idx = keymap.index(ctg)
            res[idx] = mapping[ctg][str(state)]
        return res

    # 重複するものが一つの場合
    if len(is_dup) == 1:
        # 重複のないもの
        single_state = {c: s for c, s in data.items() if c not in dup_ctg}
        for ctg, state in single_state.items():
            idx = keymap.index(ctg)
            res[idx] = mapping[ctg][str(state)]
            counter_flag += len(mapping[ctg][str(state)])

        # 重複するもの
        dup_state = {c: s for c, s in data.items() if c in dup_ctg}
        long = maxium_state_ct - counter_flag
        possiblity = []

        for ctg, state in dup_state.items():
            possiblity = dup[ctg][str(state)]
            for p in possiblity:
                if len(p) == long or len(p) == long - 1:
                    idx = keymap.index(ctg)
                    res[idx] = p
                    return res

    # 重複するものが複数の場合
    if len(is_dup) == 2:
        single_state = {c: s for c, s in data.items() if c not in dup_ctg}
        for ctg, state in single_state.items():
            idx = keymap.index(ctg)
            res[idx] = mapping[ctg][str(state)]
            counter_flag += len(mapping[ctg][str(state)])

        dup_state = {c: s for c, s in data.items() if c in dup_ctg}
        long = maxium_state_ct - counter_flag

        sample = [[ctg, state] for ctg, state in dup_state.items()]

        possiblity1 = dup[sample[0][0]][str(sample[0][1])]
        possiblity2 = dup[sample[1][0]][str(sample[1][1])]

        p1 = [len(p) for p in possiblity1]
        p2 = [len(p) for p in possiblity2]

        p = itertools.product(p1, p2)
        r = None
        for v in p:
            if sum(v) == long or sum(v) == long - 1:
                r = v
                break

        idx1 = keymap.index(sample[0][0])
        idx2 = keymap.index(sample[1][0])

        res[idx1] = possiblity1[p1.index(v[0])]
        res[idx2] = possiblity2[p2.index(v[1])]
        return res

    if len(is_dup) == 3:
        single_state = {c: s for c, s in data.items() if c not in dup_ctg}
        for ctg, state in single_state.items():
            idx = keymap.index(ctg)
            res[idx] = mapping[ctg][str(state)]
            counter_flag += len(mapping[ctg][str(state)])

        dup_state = {c: s for c, s in data.items() if c in dup_ctg}
        long = maxium_state_ct - counter_flag

        sample = [[ctg, state] for ctg, state in dup_state.items()]

        possiblity1 = dup[sample[0][0]][str(sample[0][1])]
        possiblity2 = dup[sample[1][0]][str(sample[1][1])]
        possiblity3 = dup[sample[2][0]][str(sample[2][1])]

        p1 = [len(p) for p in possiblity1]
        p2 = [len(p) for p in possiblity2]
        p3 = [len(p) for p in possiblity3]

        p = itertools.product(p1, p2, p3)
        r = None
        for v in p:
            if sum(v) == long or sum(v) == long - 1:
                r = v
                break

        idx1 = keymap.index(sample[0][0])
        idx2 = keymap.index(sample[1][0])
        idx3 = keymap.index(sample[2][0])

        res[idx1] = possiblity1[p1.index(v[0])]
        res[idx2] = possiblity2[p2.index(v[1])]
        res[idx3] = possiblity3[p3.index(v[2])]

        return res

    if len(is_dup) == 4:
        dup_state = {c: s for c, s in data.items() if c in dup_ctg}
        long = maxium_state_ct - counter_flag

        sample = [[ctg, state] for ctg, state in dup_state.items()]

        possiblity1 = dup[sample[0][0]][str(sample[0][1])]
        possiblity2 = dup[sample[1][0]][str(sample[1][1])]
        possiblity3 = dup[sample[2][0]][str(sample[2][1])]
        possiblity4 = dup[sample[3][0]][str(sample[3][1])]

        p1 = [len(p) for p in possiblity1]
        p2 = [len(p) for p in possiblity2]
        p3 = [len(p) for p in possiblity3]
        p4 = [len(p) for p in possiblity4]

        p = itertools.product(p1, p2, p3, p4)
        r = None
        for v in p:
            if sum(v) == long or sum(v) == long - 1:
                r = v
                break

        idx1 = keymap.index(sample[0][0])
        idx2 = keymap.index(sample[1][0])
        idx3 = keymap.index(sample[2][0])
        idx4 = keymap.index(sample[3][0])

        res[idx1] = possiblity1[p1.index(v[0])]
        res[idx2] = possiblity2[p2.index(v[1])]
        res[idx3] = possiblity3[p3.index(v[2])]
        res[idx4] = possiblity4[p4.index(v[3])]

        return res
    return


def read_json(path):
    with codecs.open(path, encoding='utf-8') as f:
        data = json.load(f)
    return data


def generation(data):
    character_data: dict = data.get('Character')
    character_element: str = character_data.get('Element')
    character_name: str = character_data.get('Name')
    character_constellations: int = character_data.get('Const')
    character_level: int = character_data.get('Level')
    friend_ship: int = character_data.get('Love')
    character_status: dict = character_data.get('Status')
    character_base: dict = character_data.get('Base')
    character_talent: dict = character_data.get('Talent')

    weapon: dict = data.get('Weapon')
    weapon_name: str = weapon.get('name')
    weapon_level: int = weapon.get('Level')
    weapon_rank: int = weapon.get('totu')
    weapon_reality: int = weapon.get('rarelity')
    weapon_base_atk: int = weapon.get('BaseATK')
    weapon_sub_op: int = weapon.get('Sub')
    weapon_sub_op_key: str = weapon_sub_op.get('name')
    weapon_sub_op_value: str = weapon_sub_op.get('value')

    score_data: dict = data.get('Score')
    score_cv_basis: str = score_data.get('State')
    score_total: float = score_data.get('total')

    artifacts_data: dict = data.get('Artifacts')

    cwd = os.path.abspath(os.path.dirname(__file__))
    config_font = lambda size: ImageFont.truetype(f'{cwd}/Assets/ja-jp.ttf', size)

    base_image = Image.open(f'{cwd}/Base/{character_element}.png')

    # キャラクター
    character_costume = character_data.get('Costume')
    if character_name in ['蛍', '空']:
        character_image = Image.open(f'{cwd}/character/{character_name}({character_element})/avatar.png').convert("RGBA")
    else:
        if character_costume:
            character_image = Image.open(f'{cwd}/character/{character_name}/{CharacterCostume}.png').convert("RGBA")
        else:
            character_image = Image.open(f'{cwd}/character/{character_name}/avatar.png').convert("RGBA")

    shadow = Image.open(f'{cwd}/Assets/Shadow.png').resize(base_image.size)
    character_image = character_image.crop((289, 0, 1728, 1024))
    character_image = character_image.resize((int(character_image.width * 0.75), int(character_image.height * 0.75)))

    character_avatar_mask = character_image.copy()

    if character_name == 'アルハイゼン':
        character_avatar_mask2 = Image.open(f'{cwd}/Assets/Alhaitham.png').convert('L').resize(character_image.size)
    else:
        character_avatar_mask2 = Image.open(f'{cwd}/Assets/CharacterMask.png').convert('L').resize(character_image.size)
    character_image.putalpha(character_avatar_mask2)

    character_paste = Image.new("RGBA", base_image.size, (255, 255, 255, 0))

    character_paste.paste(character_image, (-160, -45), mask=character_avatar_mask)
    base_image = Image.alpha_composite(base_image, character_paste)
    base_image = Image.alpha_composite(base_image, shadow)

    # 武器
    weapon = Image.open(f'{cwd}/weapon/{weapon_name}.png').convert("RGBA").resize((128, 128))
    weapon_paste = Image.new("RGBA", base_image.size, (255, 255, 255, 0))

    weapon_mask = weapon.copy()
    weapon_paste.paste(weapon, (1430, 50), mask=weapon_mask)

    base_image = Image.alpha_composite(base_image, weapon_paste)

    weapon_r_image = Image.open(f'{cwd}/Assets/Rarelity/{weapon_reality}.png').convert("RGBA")
    weapon_r_image = weapon_r_image.resize((int(weapon_r_image.width * 0.97), int(weapon_r_image.height * 0.97)))
    weapon_r_paste = Image.new("RGBA", base_image.size, (255, 255, 255, 0))
    weapon_r_mask = weapon_r_image.copy()

    weapon_r_paste.paste(weapon_r_image, (1422, 173), mask=weapon_r_mask)
    base_image = Image.alpha_composite(base_image, weapon_r_paste)

    # 天賦
    talent_base = Image.open(f'{cwd}/Assets/TalentBack.png')
    talent_base_paste = Image.new("RGBA", base_image.size, (255, 255, 255, 0))
    talent_base = talent_base.resize((int(talent_base.width / 1.5), int(talent_base.height / 1.5)))

    for i, t in enumerate(['通常', 'スキル', "爆発"]):
        talent_paste = Image.new("RGBA", talent_base.size, (255, 255, 255, 0))
        talent = Image.open(f'{cwd}/character/{character_name}/{t}.png').resize((50, 50)).convert('RGBA')
        talent_mask = talent.copy()
        talent_paste.paste(talent, (talent_paste.width // 2 - 25, talent_paste.height // 2 - 25), mask=talent_mask)

        talent_object = Image.alpha_composite(talent_base, talent_paste)
        talent_base_paste.paste(talent_object, (15, 330 + i * 105))

    base_image = Image.alpha_composite(base_image, talent_base_paste)

    # 凸
    star_base = Image.open(f'{cwd}/命の星座/{character_element}.png').resize((90, 90)).convert('RGBA')
    star_locked = Image.open(f'{cwd}/命の星座/{character_element}LOCK.png').resize((90, 90)).convert('RGBA')
    star_locked_mask = star_locked.copy()

    star_paste = Image.new("RGBA", base_image.size, (255, 255, 255, 0))
    for c in range(1, 7):
        if c > character_constellations:
            star_paste.paste(star_locked, (666, -10 + c * 93), mask=star_locked_mask)
        else:
            chara_star = Image.open(f'{cwd}/character/{character_name}/{c}.png').convert("RGBA").resize((45, 45))
            chara_star_paste = Image.new("RGBA", star_base.size, (255, 255, 255, 0))
            chara_star_mask = chara_star.copy()
            chara_star_paste.paste(chara_star,
                                   (int(chara_star_paste.width / 2) - 25, int(chara_star_paste.height / 2) - 23),
                                   mask=chara_star_mask)

            chara_object = Image.alpha_composite(star_base, chara_star_paste)
            star_paste.paste(chara_object, (666, -10 + c * 93))

    base_image = Image.alpha_composite(base_image, star_paste)
    drew_base = ImageDraw.Draw(base_image)

    drew_base.text((30, 20), character_name, font=config_font(48))
    level_length = drew_base.textlength("Lv." + str(character_level), font=config_font(25))
    friendship_length = drew_base.textlength(str(friend_ship), font=config_font(25))
    drew_base.text((35, 75), "Lv." + str(character_level), font=config_font(25))
    drew_base.rounded_rectangle((35 + level_length + 5, 74, 77 + level_length + friendship_length, 102), radius=2, fill="black")
    friend_ship_icon = Image.open(f'{cwd}/Assets/Love.png').convert("RGBA")
    friend_ship_icon = friend_ship_icon.resize((int(friend_ship_icon.width * (24 / friend_ship_icon.height)), 24))
    friend_mask = friend_ship_icon.copy()
    base_image.paste(friend_ship_icon, (42 + int(level_length), 76), mask=friend_mask)
    drew_base.text((73 + level_length, 74), str(friend_ship), font=config_font(25))

    drew_base.text((42, 397), f'Lv.{character_talent["通常"]}', font=config_font(17),
                   fill='aqua' if character_talent["通常"] >= 10 else None)
    drew_base.text((42, 502), f'Lv.{character_talent["スキル"]}', font=config_font(17),
                   fill='aqua' if character_talent["スキル"] >= 10 else None)
    drew_base.text((42, 607), f'Lv.{character_talent["爆発"]}', font=config_font(17),
                   fill='aqua' if character_talent["爆発"] >= 10 else None)

    def gen_base_text(state):
        sumv = character_status[state]
        plusv = sumv - character_base[state]
        basev = character_base[state]
        return f"+{format(plusv, ',')}",\
            f"{format(basev, ',')}",\
            drew_base.textlength(f"+{format(plusv, ',')}", font=config_font(12)),\
            drew_base.textlength(f"{format(basev, ',')}", font=config_font(12))

    disper = ['会心率', '会心ダメージ', '攻撃パーセンテージ', '防御パーセンテージ', 'HPパーセンテージ', '水元素ダメージ', '物理ダメージ', '風元素ダメージ',
              '岩元素ダメージ', '炎元素ダメージ', '与える治癒効果', '与える治療効果', '雷元素ダメージ', '氷元素ダメージ', '草元素ダメージ',
              '与える治癒効果', '元素チャージ効率']
    state_option = ('HP', '攻撃力', "防御力", "元素熟知", "会心率", "会心ダメージ", "元素チャージ効率")
    for k, v in character_status.items():
        if k in ['氷元素ダメージ', '水元素ダメージ', '岩元素ダメージ', '草元素ダメージ', '風元素ダメージ', '炎元素ダメージ', '物理ダメージ',
                 '与える治癒効果', '雷元素ダメージ'] and v == 0:
            k = f'{character_element}元素ダメージ'
        try:
            i = state_option.index(k)
        except:
            i = 7
            drew_base.text((844, 67 + i * 70), k, font=config_font(26))
            op_icon = Image.open(f'{cwd}/emotes/{k}.png').resize((40, 40))
            op_paste = Image.new('RGBA', base_image.size, (255, 255, 255, 0))
            op_mask = op_icon.copy()
            op_paste.paste(op_icon, (789, 65 + i * 70))
            base_image = Image.alpha_composite(base_image, op_paste)
            drew_base = ImageDraw.Draw(base_image)

        if k not in disper:
            state_len = drew_base.textlength(format(v, ","), config_font(26))
            drew_base.text((1360 - state_len, 67 + i * 70), format(v, ","), font=config_font(26))
        else:
            state_len = drew_base.textlength(f'{float(v)}%', config_font(26))
            drew_base.text((1360 - state_len, 67 + i * 70), f'{float(v)}%', font=config_font(26))

        if k in ['HP', '防御力', '攻撃力']:
            hp_pls, hp_base, hp_size, hp_bsize = gen_base_text(k)
            drew_base.text((1360 - hp_size, 97 + i * 70), hp_pls, fill=(0, 255, 0, 180), font=config_font(12))
            drew_base.text((1360 - hp_size - hp_bsize - 1, 97 + i * 70), hp_base, font=config_font(12), fill=(255, 255, 255, 180))

    drew_base.text((1582, 47), weapon_name, font=config_font(26))
    wlebel_len = drew_base.textlength(f'Lv.{weapon_level}', font=config_font(24))
    drew_base.rounded_rectangle((1582, 80, 1582 + wlebel_len + 4, 108), radius=1, fill='black')
    drew_base.text((1584, 82), f'Lv.{weapon_level}', font=config_font(24))

    base_atk = Image.open(f'{cwd}/emotes/基礎攻撃力.png').resize((23, 23))
    base_atk_mask = base_atk.copy()
    base_image.paste(base_atk, (1600, 120), mask=base_atk_mask)
    drew_base.text((1623, 120), f'基礎攻撃力  {weapon_base_atk}', font=config_font(23))

    option_map = {
        "攻撃パーセンテージ": "攻撃%",
        "防御パーセンテージ": "防御%",
        "元素チャージ効率": "元チャ効率",
        "HPパーセンテージ": "HP%",
    }
    if weapon_sub_op_key is not None:
        base_atk = Image.open(f'{cwd}/emotes/{weapon_sub_op_key}.png').resize((23, 23))
        base_atk_mask = base_atk.copy()
        base_image.paste(base_atk, (1600, 155), mask=base_atk_mask)

        drew_base.text((1623, 155),
                       f'{option_map.get(weapon_sub_op_key) or weapon_sub_op_key}  {str(weapon_sub_op_value) + "%" if weapon_sub_op_key in disper else format(weapon_sub_op_value, ",")}',
                       font=config_font(23))

    drew_base.rounded_rectangle((1430, 45, 1470, 70), radius=1, fill='black')
    drew_base.text((1433, 46), f'R{weapon_rank}', font=config_font(24))

    score_len = drew_base.textlength(f'{score_total}', config_font(75))
    drew_base.text((1652 - score_len // 2, 420), str(score_total), font=config_font(75))
    b_len = drew_base.textlength(f'{score_cv_basis}換算', font=config_font(24))
    drew_base.text((1867 - b_len, 585), f'{score_cv_basis}換算', font=config_font(24))

    if score_total >= 220:
        score_ev = Image.open(f'{cwd}/artifactGrades/SS.png')
    elif score_total >= 200:
        score_ev = Image.open(f'{cwd}/artifactGrades/S.png')
    elif score_total >= 180:
        score_ev = Image.open(f'{cwd}/artifactGrades/A.png')
    else:
        score_ev = Image.open(f'{cwd}/artifactGrades/B.png')

    score_ev = score_ev.resize((score_ev.width // 8, score_ev.height // 8))
    ev_mask = score_ev.copy()

    base_image.paste(score_ev, (1806, 345), mask=ev_mask)

    # 聖遺物
    atf_type = list()
    for i, parts in enumerate(['flower', "wing", "clock", "cup", "crown"]):
        details = artifacts_data.get(parts)

        if not details:
            continue
        atf_type.append(details['type'])
        preview_paste = Image.new('RGBA', base_image.size, (255, 255, 255, 0))
        preview = Image.open(f'{cwd}/Artifact/{details["type"]}/{parts}.png').resize((256, 256))
        enhancer = ImageEnhance.Brightness(preview)
        preview = enhancer.enhance(0.6)
        preview = preview.resize((int(preview.width * 1.3), int(preview.height * 1.3)))
        preview_mask_1 = preview.copy()

        preview_mask = Image.open(f'{cwd}/Assets/ArtifactMask.png').convert('L').resize(preview.size)
        preview.putalpha(preview_mask)
        if parts in ['flower', 'crown']:
            preview_paste.paste(preview, (-37 + 373 * i, 570), mask=preview_mask_1)
        elif parts in ['wing', 'cup']:
            preview_paste.paste(preview, (-36 + 373 * i, 570), mask=preview_mask_1)
        else:
            preview_paste.paste(preview, (-35 + 373 * i, 570), mask=preview_mask_1)
        base_image = Image.alpha_composite(base_image, preview_paste)
        drew_base = ImageDraw.Draw(base_image)

        main_op = details['main']['option']

        main_op_len = drew_base.textlength(option_map.get(main_op) or main_op, font=config_font(29))
        drew_base.text((375 + i * 373 - int(main_op_len), 655), option_map.get(main_op) or main_op, font=config_font(29))
        main_icon = Image.open(f'{cwd}/emotes/{main_op}.png').convert("RGBA").resize((35, 35))
        main_mask = main_icon.copy()
        base_image.paste(main_icon, (340 + i * 373 - int(main_op_len), 655), mask=main_mask)

        mainv = details['main']['value']
        if main_op in disper:
            mainvsize = drew_base.textlength(f'{float(mainv)}%', config_font(49))
            drew_base.text((375 + i * 373 - mainvsize, 690), f'{float(mainv)}%', font=config_font(49))
        else:
            mainvsize = drew_base.textlength(format(mainv, ","), config_font(49))
            drew_base.text((375 + i * 373 - mainvsize, 690), format(mainv, ","), font=config_font(49))
        level_len = drew_base.textlength(f'+{details["Level"]}', config_font(21))
        drew_base.rounded_rectangle((373 + i * 373 - int(level_len), 748, 375 + i * 373, 771), fill='black', radius=2)
        drew_base.text((374 + i * 373 - level_len, 749), f'+{details["Level"]}', font=config_font(21))

        if details['Level'] == 20 and details['rarelity'] == 5:
            c_data = {}
            for a in details["sub"]:
                if a['option'] in disper:
                    c_data[a['option']] = str(float(a["value"]))
                else:
                    c_data[a['option']] = str(a["value"])
            psb = culculate_op(c_data)

        if len(details['sub']) == 0:
            continue

        for a, sub in enumerate(details['sub']):
            sub_op = sub['option']
            sub_val = sub['value']
            if sub_op in ['HP', '攻撃力', '防御力']:
                drew_base.text((79 + 373 * i, 811 + 50 * a), option_map.get(sub_op) or sub_op, font=config_font(25),
                               fill=(255, 255, 255, 190))
            else:
                drew_base.text((79 + 373 * i, 811 + 50 * a), option_map.get(sub_op) or sub_op, font=config_font(25))
            sub_icon = Image.open(f'{cwd}/emotes/{sub_op}.png').resize((30, 30))
            sub_mask = sub_icon.copy()
            base_image.paste(sub_icon, (44 + 373 * i, 811 + 50 * a), mask=sub_mask)
            if sub_op in disper:
                sub_size = drew_base.textlength(f'{float(sub_val)}%', config_font(25))
                drew_base.text((375 + i * 373 - sub_size, 811 + 50 * a), f'{float(sub_val)}%', font=config_font(25))
            else:
                sub_size = drew_base.textlength(format(sub_val, ","), config_font(25))
                if sub_op in ['防御力', '攻撃力', 'HP']:
                    drew_base.text((375 + i * 373 - sub_size, 811 + 50 * a), format(sub_val, ","), font=config_font(25),
                                   fill=(255, 255, 255, 190))
                else:
                    drew_base.text((375 + i * 373 - sub_size, 811 + 50 * a), format(sub_val, ","), font=config_font(25),
                                   fill=(255, 255, 255))

            if details['Level'] == 20 and details['rarelity'] == 5:
                nobi = drew_base.textlength("+".join(map(str, psb[a])), font=config_font(11))
                drew_base.text((375 + i * 373 - nobi, 840 + 50 * a), "+".join(map(str, psb[a])), fill=(255, 255, 255, 160),
                               font=config_font(11))

        score = float(score_data[parts])
        atf_score_len = drew_base.textlength(str(score), config_font(36))
        drew_base.text((380 + i * 373 - atf_score_len, 1016), str(score), font=config_font(36))
        drew_base.text((295 + i * 373 - atf_score_len, 1025), 'Score', font=config_font(27), fill=(160, 160, 160))

        point_refer = {
            "total": {
                "SS": 220,
                "S": 200,
                "A": 180
            },
            "flower": {
                "SS": 50,
                "S": 45,
                "A": 40
            },
            "wing": {
                "SS": 50,
                "S": 45,
                "A": 40
            },
            "clock": {
                "SS": 45,
                "S": 40,
                "A": 35
            },
            "cup": {
                "SS": 45,
                "S": 40,
                "A": 37
            },
            "crown": {
                "SS": 40,
                "S": 35,
                "A": 30
            }
        }

        if score >= point_refer[parts]['SS']:
            score_image = Image.open(f'{cwd}/artifactGrades/SS.png')
        elif score >= point_refer[parts]['S']:
            score_image = Image.open(f'{cwd}/artifactGrades/S.png')
        elif score >= point_refer[parts]['A']:
            score_image = Image.open(f'{cwd}/artifactGrades/A.png')
        else:
            score_image = Image.open(f'{cwd}/artifactGrades/B.png')

        score_image = score_image.resize((score_image.width // 11, score_image.height // 11))
        score_c_mask = score_image.copy()

        base_image.paste(score_image, (85 + 373 * i, 1013), mask=score_c_mask)

    set_bounus = Counter([x for x in atf_type if atf_type.count(x) >= 2])
    for i, (n, q) in enumerate(set_bounus.items()):
        if len(set_bounus) == 2:
            drew_base.text((1536, 243 + i * 35), n, fill=(0, 255, 0), font=config_font(23))
            drew_base.rounded_rectangle((1818, 243 + i * 35, 1862, 266 + i * 35), 1, 'black')
            drew_base.text((1835, 243 + i * 35), str(q), font=config_font(19))
        if len(set_bounus) == 1:
            drew_base.text((1536, 263), n, fill=(0, 255, 0), font=config_font(23))
            drew_base.rounded_rectangle((1818, 263, 1862, 288), 1, 'black')
            drew_base.text((1831, 265), str(q), font=config_font(19))

    premium = read_json(f'{cwd}/Assets/premium.json')
    user_badge = premium.get(f'{data.get("uid")}')
    if user_badge:
        for i, b in enumerate(user_badge):
            badge = Image.open(f'{cwd}/badge/{b}.png').convert('RGBA').resize((38, 38))
            badge_mask = badge.copy()

            base_image.paste(badge, (1843 - i * 45, 533), mask=badge_mask)

    base_image.save(f'{cwd}/Tests/Image.png')

    return pil_to_base64(base_image, format='png')


def pil_to_base64(img, format):
    buffer = BytesIO()
    img.save(buffer, format)
    img_str = base64.b64encode(buffer.getvalue())

    return img_str
