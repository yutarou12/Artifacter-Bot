import random
from io import BytesIO

import aiohttp
from PIL import Image
from discord import app_commands, File
from discord.ext import commands
from discord import ui, ButtonStyle, Colour, SelectOption, Interaction, MediaGalleryItem

from libs.Convert import load_characters_by_element, fetch_character, traveler_or_other_name
from libs.Database import Database
from libs.env import API_HOST_NAME


class BackToSettingButton(ui.Button):
    def __init__(self):
        super().__init__(label='最初に戻る', style=ButtonStyle.gray)

    async def callback(self, interaction: commands.Context):
        setting_view = SettingView()
        await interaction.response.edit_message(view=setting_view)


class Rasen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db: Database = bot.db

    class RasenGroup(app_commands.Group):
        def __init__(self):
            super().__init__(name="螺旋", description="螺旋に関するコマンド群です")

    group_rasen = RasenGroup()

    @group_rasen.command(name="生成")
    async def cmd_random_rasen_gene(self, interaction: Interaction):
        """ランダムに螺旋の構成を生成します"""
        db_data = await self.db.get_rasen_character(interaction.user.id)
        if not db_data:
            return await interaction.response.send_message("保有キャラクターが設定されていません。まずは設定を行ってください。", ephemeral=True)

        if len(db_data) < 8:
            return await interaction.response.send_message("保有キャラクターが8体未満です。最低でも8体以上のキャラクターを設定してください。", ephemeral=True)

        random_character = random.sample(db_data, 8)
        async with aiohttp.ClientSession() as session:
            data = {
                "data": random_character
            }
            async with session.post(f'http://{API_HOST_NAME}:8085/api/spiral-generate', json=data) as r:
                if r.status != 200:
                    return await interaction.response.send_message("螺旋編成の生成に失敗しました。", ephemeral=True)
                image_bytes = await r.content.read()
                img = Image.open(BytesIO(image_bytes))

                width, height = img.size
                w, h = width, height // 2

                for i in range(2):
                    box = (0, i * h, w, (i + 1) * h)
                    cropd_img = img.crop(box)
                    cropd_img.save(f'./Tests/{interaction.user.id}-Spiral-Part{i+1}.png')

        view = RasenGenerateView(interaction.user.id)
        first_img = File(f'./Tests/{interaction.user.id}-Spiral-Part1.png', filename='Spiral-Part1.png')
        second_img = File(f'./Tests/{interaction.user.id}-Spiral-Part2.png', filename='Spiral-Part2.png')
        return await interaction.response.send_message(view=view, files=[first_img, second_img])

    @group_rasen.command(name="設定")
    async def cmd_random_rasen_set(self, interaction: Interaction):
        """螺旋の設定を行います"""
        setting_view = SettingView()
        await interaction.response.send_message(view=setting_view)


class RasenGenerateView(ui.LayoutView):
    def __init__(self, user_id):
        super().__init__()

        container = ui.Container(
            ui.TextDisplay(content="# 螺旋編成ランダム生成"),
            ui.Separator(),
            ui.TextDisplay(content='第一層'),
            ui.MediaGallery(MediaGalleryItem(media=f'attachment://Spiral-Part1.png')),
            ui.Separator(),
            ui.TextDisplay(content='第二層'),
            ui.MediaGallery(MediaGalleryItem(media=f'attachment://Spiral-Part2.png')),
            accent_color=Colour.green()
        )

        self.add_item(container)


class CharacterSettingButton(ui.Button):
    def __init__(self):
        super().__init__(label='①', style=ButtonStyle.green)

    async def callback(self, interaction: Interaction):
        data = await interaction.client.db.get_rasen_character(interaction.user.id)
        view = CharacterSettingView('./data/characters.json', data)
        await interaction.response.edit_message(view=view)


class CharacterElementActionRow(ui.ActionRow):
    def __init__(self, select: ui.Select):
        super().__init__()
        self.add_item(select)


class CharacterElementSelect(ui.Select):
    def __init__(self, e, i, characters, data):
        options = [
            SelectOption(
                label=traveler_or_other_name(fetch_character(char['id']), char['icon']) if fetch_character(char['id']) else char['id'],
                value=char['id'],
                description=f"NameHash: {char['name_hash']}",
                emoji=None,  # 必要ならアイコンをemojiに変換
                default=True if char['id'] in data else False
            )
            for char in characters
        ]
        super().__init__(
            placeholder=f"キャラクターを選択",
            min_values=1,
            max_values=len(options),
            options=options,
            custom_id=f"select_{e}_{i}"
        )

    async def callback(self, interaction):
        user_id = interaction.user.id
        selected_ids = self.values
        element_from_custom_id = self.custom_id.split('_')[1]
        # DB保存
        element_chara = load_characters_by_element("./data/characters.json")

        # DBに保存されているキャラクターを取得して辞書形式に変換
        db_chara = await interaction.client.db.get_rasen_character(user_id)
        db_raw_chara = {"Ice": [], "Fire": [], "Water": [], "Wind": [], "Grass": [], "Electric": [], "Rock": []}

        for db_id in db_chara:
            for element, chars in element_chara.items():
                if any(char['id'] == db_id for char in chars):
                    db_raw_chara[element].append(db_id)

        # 選択されたキャラクターで上書き
        db_raw_chara[element_from_custom_id] = selected_ids
        # フラットなリストに変換
        selected_ids = []
        for chara_list in db_raw_chara.values():
            selected_ids.extend(chara_list)

        await interaction.client.db.add_rasen_character(user_id, selected_ids)
        await interaction.response.send_message(f"属性キャラを保存しました: {selected_ids}", ephemeral=True)


class CharacterSettingView(ui.LayoutView):
    row = ui.ActionRow()
    row.add_item(BackToSettingButton())

    def __init__(self, json_path, data):
        super().__init__()
        self.elements = load_characters_by_element(json_path)
        self.selects = {"Ice": [], "Fire": [], "Water": [], "Wind": [], "Grass": [], "Electric": [], "Rock": []}
        for element, chars in self.elements.items():
            # 25個ずつ分割
            for i in range(0, len(chars), 25):
                chunk = chars[i:i + 25]
                self.selects[element].append(CharacterElementActionRow(CharacterElementSelect(element, i, chunk, data)))

        container = ui.Container(
            ui.TextDisplay(content="# 保有キャラクター設定"),
            ui.Section(
                ui.TextDisplay(content='以下のドロップダウンメニューから、\n各属性ごとに保有しているキャラクターを選択してください。\n選択したキャラクターはデータベースに保存されます。'),
                accessory=ui.Thumbnail(media='https://dev.syutarou.xyz/static/img/profile.png')
            ),
            ui.Separator(),
            ui.TextDisplay(content='①炎属性'),
            *list(self.selects["Fire"]),
            ui.Separator(),
            ui.TextDisplay(content='②水属性'),
            *list(self.selects["Water"]),
            ui.Separator(),
            ui.TextDisplay(content='③風属性'),
            *list(self.selects["Wind"]),
            ui.Separator(),
            ui.TextDisplay(content='④雷属性'),
            *list(self.selects["Electric"]),
            ui.Separator(),
            ui.TextDisplay(content='⑤草属性'),
            *list(self.selects["Grass"]),
            ui.Separator(),
            ui.TextDisplay(content='⑥氷属性'),
            *list(self.selects["Ice"]),
            ui.Separator(),
            ui.TextDisplay(content='⑦岩属性'),
            *list(self.selects["Rock"]),
            ui.Separator(),
            accent_color=Colour.green(),

        )
        self.add_item(container)

        self.remove_item(self.row)
        self.add_item(self.row)


class CharacterDeleteButton(ui.Button):
    def __init__(self):
        super().__init__(label='②', style=ButtonStyle.green)

    async def callback(self, interaction: commands.Context):
        view = CharacterDeleteView()
        await interaction.response.edit_message(view=view)


class CharacterDeleteSubmitButton(ui.Button):
    def __init__(self):
        super().__init__(label='削除する', style=ButtonStyle.red)

    async def callback(self, interaction: Interaction):
        user_id = interaction.user.id
        await interaction.client.db.delete_rasen_character(user_id)
        return await interaction.response.edit_message("> 保有キャラクターのデータを削除しました。", view=None)


class CharacterDeleteView(ui.LayoutView):
    row = ui.ActionRow()
    row.add_item(CharacterDeleteSubmitButton())
    row.add_item(BackToSettingButton())

    def __init__(self):
        super().__init__()

        container = ui.Container(
            ui.TextDisplay(content="# 保有キャラクター削除"),
            ui.TextDisplay(content='保有キャラクターのデータを削除します。\n以下のボタンを押すと、保有キャラクターのデータが完全に削除されます。'),
            ui.Separator(),
            ui.TextDisplay(content='### ⚠ 注意: この操作は取り消せません'),
            ui.Separator(),
            accent_color=Colour.red(),
        )
        self.add_item(container)
        self.remove_item(self.row)
        self.add_item(self.row)


class CharacterSaveButton(ui.Button):
    def __init__(self):
        super().__init__(label='③', style=ButtonStyle.green)

    async def callback(self, interaction: commands.Context):
        await interaction.response.send_message("保有キャラクターの設定ボタンが押されました！", ephemeral=True)


class SettingView(ui.LayoutView):

    container = ui.Container(
        ui.TextDisplay(content="# 螺旋編成生成-設定"),
        ui.Section(
            ui.TextDisplay(content='螺旋編成をランダムに生成する際の設定を行います。\n以下の各項目から設定を行ってください。'),
            accessory=ui.Thumbnail(media='https://dev.syutarou.xyz/static/img/profile.png')
        ),
        ui.Separator(),
        ui.Section(
            ui.TextDisplay(content='① 保有キャラクターの設定'),
            accessory=CharacterSettingButton()
        ),
        ui.Section(
            ui.TextDisplay(content='② 保有キャラクターの削除'),
            accessory=CharacterDeleteButton()
        ),
        ui.Section(
            ui.TextDisplay(content='③ 螺旋編成の保存'),
            accessory=CharacterSaveButton()
        ),
        accent_color=Colour.green(),
    )


async def setup(bot):
    await bot.add_cog(Rasen(bot))
