import discord
from discord import app_commands, Interaction, Embed, ui, ButtonStyle
from discord.ext import commands


class CacheData(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='設定')
    async def cmd_cache_setting(self, interaction: Interaction):
        """キャッシュ生成の設定を行います"""
        if not await self.bot.db.get_premium_user_bool(interaction.user.id):
            return await interaction.response.send_meesage('この機能はプレミアムユーザー専用です。\nプレミアムユーザーについては公式サーバーまでお問合せください。',
                                                           ephemeral=True)
        embed = Embed(title='キャッシュ機能設定')
        embed.description = '```\n原神のキャラクター情報を取得している「EnkaNetwork」がメンテナンス等で、' \
                            'データを取得出来なかった際に、一番最後に取得したデータからビルド画像を生成する機能です。\n```'
        if not await self.bot.db.get_user_cache(interaction.user.id):
            embed.add_field(name='⚒️ 現在の設定', value='`無効`', inline=False)
        else:
            embed.add_field(name='⚒️ 現在の設定', value='`有効`', inline=False)

        field_2_text = '設定を切り換えるには、「設定を切り換える」を押して下さい。\n「有効」にすると次以降「/build」で取得できたデータが保存されます。\n' \
                       '「無効」にすると、即座に保存されていたデータを抹消します。'
        embed.add_field(name='🔰使い方', value=field_2_text, inline=False)

        view = CacheSettingView(cache_bool=bool(await self.bot.db.get_user_cache(interaction.user.id)))
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        await view.wait()

        if view.value is None:
            return
        elif view.value:
            if await self.bot.db.get_user_cache(interaction.user.id):
                await self.bot.db.remove_user_cache_data(interaction.user.id)
            else:
                await self.bot.db.add_user_cache_data(interaction.user.id)
        else:
            return


class CacheSettingView(ui.View):
    def __init__(self, cache_bool: bool, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache_bool = cache_bool
        self.timeout = 120
        self.value = None

    @discord.ui.button(label='設定を切り換える', style=ButtonStyle.green)
    async def confirm_button(self, interaction: Interaction, button: ui.Button):
        await interaction.response.edit_message(content=f'設定を {"**無効**" if self.cache_bool else "**有効**"} に切り換えました。',
                                                view=None, embed=None)
        self.value = True
        self.stop()

    @discord.ui.button(label='キャンセル', style=ButtonStyle.red)
    async def cancel_button(self, interaction: Interaction, button: ui.Button):
        await interaction.response.edit_message(content='キャンセルしました。', view=None, embed=None)
        self.value = False
        self.stop()


async def setup(bot):
    await bot.add_cog(CacheData(bot))
