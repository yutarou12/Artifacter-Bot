from discord import app_commands
from discord.ext import commands
from discord import ui, ButtonStyle, Colour, SelectOption

from libs.Convert import load_characters_by_element
from libs.Database import Database


class Rasen(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db: Database = bot.db

    class RasenGroup(app_commands.Group):
        def __init__(self):
            super().__init__(name="螺旋", description="螺旋に関するコマンド群です")

    group_rasen = RasenGroup()

    @group_rasen.command(name="生成")
    async def cmd_random_rasen_gene(self, interaction: commands.Context):
        """ランダムに螺旋の構成を生成します"""
        await interaction.response.send_message("ランダム螺旋コマンドが実行されました！")

    @group_rasen.command(name="設定")
    async def cmd_random_rasen_set(self, interaction: commands.Context):
        """螺旋の設定を行います"""
        setting_view = SettingView()
        await interaction.response.send_message(view=setting_view)


class CharacterSettingButton(ui.Button):
    def __init__(self):
        super().__init__(label='①', style=ButtonStyle.green)

    async def callback(self, interaction: commands.Context):
        view = CharacterSettingView('./data/characters.json')
        await interaction.response.edit_message(view=view)


class CharacterElementActionRow(ui.ActionRow):
    def __init__(self, select: ui.Select):
        super().__init__()
        self.add_item(select)


class CharacterElementSelect(ui.Select):
    def __init__(self, e, i, characters):
        options = [
            SelectOption(
                label=char['id'],
                value=char['id'],
                description=f"NameHash: {char['name_hash']}",
                emoji=None  # 必要ならアイコンをemojiに変換
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
        # DB保存
        await interaction.client.db.add_rasen_character(user_id, selected_ids)
        await interaction.response.send_message(f"属性キャラを保存しました: {selected_ids}", ephemeral=True)


class BackToSettingButton(ui.Button):
    def __init__(self):
        super().__init__(label='最初に戻る', style=ButtonStyle.gray)

    async def callback(self, interaction: commands.Context):
        setting_view = SettingView()
        await interaction.response.edit_message(view=setting_view)


class CharacterSettingView(ui.LayoutView):
    row = ui.ActionRow()
    row.add_item(BackToSettingButton())

    def __init__(self, json_path):
        super().__init__()
        self.elements = load_characters_by_element(json_path)
        self.selects = {"Ice":[], "Fire":[], "Water":[], "Wind":[], "Grass":[], "Electric":[], "Rock":[]}
        for element, chars in self.elements.items():
            # 25個ずつ分割
            for i in range(0, len(chars), 25):
                chunk = chars[i:i + 25]
                self.selects[element].append(CharacterElementActionRow(CharacterElementSelect(element, i, chunk)))

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
        await interaction.response.send_message("保有キャラクターの設定ボタンが押されました！", ephemeral=True)


class CharacterSaveButton(ui.Button):
    def __init__(self):
        super().__init__(label='③', style=ButtonStyle.green)

    async def callback(self, interaction: commands.Context):
        await interaction.response.send_message("保有キャラクターの設定ボタンが押されました！", ephemeral=True)


class SettingView(ui.LayoutView):

    container = ui.Container(
        ui.TextDisplay(content="螺旋編成生成-設定"),
        ui.Section(
            ui.TextDisplay(content='螺旋編成をランダムに生成する際の設定を行います。\n以下の各項目から設定を行ってください。'),
            accessory=ui.Thumbnail(media='https://dev.syutarou.xyz/static/img/profile.png')
        ),
        ui.Separator(),
        ui.Section(
            ui.TextDisplay(content='①保有キャラクターの設定'),
            accessory=CharacterSettingButton()
        ),
        ui.Section(
            ui.TextDisplay(content='②保有キャラクターの削除'),
            accessory=CharacterDeleteButton()
        ),
        ui.Section(
            ui.TextDisplay(content='③螺旋編成の保存'),
            accessory=CharacterSaveButton()
        ),
        accent_color=Colour.green(),
    )


async def setup(bot):
    await bot.add_cog(Rasen(bot))
