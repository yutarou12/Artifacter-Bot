import json
import random

import discord
from discord import app_commands, ui
from discord.ext import commands


class Hikyou(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open('./data/week_boss_list.json', 'r', encoding='utf-8') as d:
            boss_list = json.load(d)
        self.boss_list = boss_list

    @app_commands.command(name='週ボス')
    @app_commands.rename(value='選ぶ数')
    async def cmd_hikyou_boss(self, interaction: discord.Interaction, value: int = 3):
        """週ボスをランダムで選ぶだけのコマンドです"""
        if value == 0 or value > len(list(self.boss_list.items())):
            return await interaction.response.send_message(
                f'週ボスの数は、1～{len(list(self.boss_list.items()))}の間で指定してください。', ephemeral=True)
        embed = discord.Embed(title=f'今週の週ボス {value} 戦')
        random_boss = random.sample(list(self.boss_list.items()), k=value)
        for i in random_boss:
            drop_item = "　\n".join(i[1]["ドロップ"])
            embed.add_field(name=i[0],
                            value=f'**__{i[1]["場所"]}__**\n```\n{drop_item}\n```',
                            inline=False)

        view = ui.View()
        view.add_item(InformationButton(label="詳細情報へ"))
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class InformationButton(ui.Button):
    def __init__(self, *args, **kwargs):
        with open('./data/week_boss_list.json', 'r', encoding='utf-8') as d:
            boss_list = json.load(d)
        self.boss_list = boss_list
        super().__init__(*args, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        old_embed = interaction.message.embeds[0]
        embed_list = []
        for e in old_embed.fields:
            boss = self.boss_list.get(e.name)
            embed = discord.Embed(title=e.name)
            chara_text = '\n・'.join(boss.get("キャラクター"))
            item_text = '\n・'.join(boss.get("ドロップ"))
            embed.add_field(name="場所", value=boss.get("場所"), inline=False)
            embed.add_field(name="解放条件", value=boss.get("解放条件"), inline=False)
            embed.add_field(name="素材", value=f'```\n・{item_text}\n```', inline=False)
            embed.add_field(name="対象キャラクター", value=f'```\n・{chara_text}\n```', inline=False)

            embed_list.append(embed)

        return await interaction.response.edit_message(embeds=embed_list, view=None)


async def setup(bot):
    await bot.add_cog(Hikyou(bot))
