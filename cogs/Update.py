import json
import os
import shutil

import requests
from discord.ext import commands


def add_file(resource: str, version: str, write_data: dict):
    if os.path.exists(f'./data/{resource}.json'):
        shutil.copyfile(f'./data/{resource}.json', f'./data/backup/{resource}-{version}.json')
        os.remove(f'./data/{resource}.json')

    with open(f'./data/{resource}.json', mode='w') as f:
        json.dump(write_data, f, indent=4, ensure_ascii=False)

    return True


class Update(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='update')
    async def update_cmd(self, ctx: commands.Context, version: str = None):
        if not version:
            return await ctx.send('No version')

        res_1 = requests.get(f'http://{os.getenv("API_HOST_NAME")}:8080/api/update/{version}/fetch')
        if res_1.status_code == 404:
            return await ctx.send('404')
        elif res_1.status_code == 200:
            await ctx.send('200')
        else:
            return await ctx.send(f'{res_1.status_code}')

        for file in ["lang", "chara", "pfps", "namecard"]:
            res_2 = requests.get(f'http://{os.getenv("API_HOST_NAME")}:8080/api/update/{version}/{file}')
            res_2.encoding = res_2.apparent_encoding
            if file == 'lang':
                res_data = res_2.json()
                add_file('ja_name', version, res_data)
            elif file == 'chara':
                res_data = res_2.json()
                add_file('characters', version, res_data)
            print(res_2.encoding)
            print(f'完了 - {file}')

        res_3 = requests.get(f'http://{os.getenv("API_HOST_NAME")}:8080/api/update/{version}/images')
        if res_3.status_code == 404:
            print(res_3.content)
            return await ctx.send(f'/api/update/{version}/images - 404')
        elif res_3.status_code == 200:
            print(res_3.content)
            return await ctx.send(f'/api/update/{version}/images - 200')
        else:
            print(res_3.status_code)


async def setup(bot):
    await bot.add_cog(Update(bot))