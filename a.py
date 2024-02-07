import discord
from discord import app_commands
import aiohttp
import json
import asyncio

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

WHITELIST_PATH = 'YOUR JSON FILE PATH'

MOJANG_API_BASE_URL = 'https://api.mojang.com/users/profiles/minecraft/'

def is_already_whitelisted(mcid):
    with open(WHITELIST_PATH, 'r') as f:
        whitelist = json.load(f)
        for entry in whitelist:
            if entry['name'] == mcid:
                return True
        return False

@client.event
async def on_ready():
    print('ログインしました')

    new_activity = f"ある8鯖"
    await client.change_presence(activity=discord.Game(new_activity))

    await tree.sync()

async def fetch_mojang_api(session, url):
    async with session.get(url, timeout=3) as response:
        return await response.json()

@tree.command(name='list', description='ホワイトリストを登録します。')
async def add_to_whitelist(interaction: discord.Interaction, mcid: str):
    if is_already_whitelisted(mcid):
        embed = discord.Embed(
            description=f"⚠️ **{mcid}** さんはすでにホワイトリストに登録されています！",
            color=0xffa500
        )
        await interaction.response.send_message(embed=embed)
        return

    mojang_api_url = MOJANG_API_BASE_URL + mcid
    async with aiohttp.ClientSession() as session:
        try:
            response_data = await asyncio.wait_for(fetch_mojang_api(session, mojang_api_url), timeout=2)
            uuid = response_data.get('id')
            with open(WHITELIST_PATH, 'r+') as f:
                whitelist = json.load(f)
                whitelist.append({
                    'uuid': uuid,
                    'name': mcid
                })
                f.seek(0)
                json.dump(whitelist, f, indent=2)
                f.truncate()

            embed = discord.Embed(
                description=f"✅ **{mcid}** さんをホワイトリストに追加しました。",
                color=0x00ff00
            )
            await interaction.response.send_message(embed=embed)
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title=f"🛑 Mojang APIからの応答がタイムアウトしました。",
                description=f"<@863718856454438922> <@879650957355548703> \n 鯖の処理落ち、ネットワークトラブル、discord.pyおよび使用ライブラリの仕様変更、mojang apiの仕様変更の可能性があります。 \n ご対応をお願いします。",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)
        except aiohttp.ClientError as e:
            embed = discord.Embed(
                description=f"🛑 エラーが発生しました: {e}",
                color=0xff0000
            )
            await interaction.response.send_message(embed=embed)

client.run("YOUR TOKEN")
