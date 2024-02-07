import discord
from discord import app_commands
import aiohttp
import json
import asyncio

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# whitelist.jsonファイルのパスをセットします
WHITELIST_PATH = 'YOUR JSON FILE PATH'

# Mojang APIのベースURLをセットします
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

    # アクティビティを設定
    new_activity = f"ある8鯖"
    await client.change_presence(activity=discord.Game(new_activity))

    # スラッシュコマンドを同期
    await tree.sync()

async def fetch_mojang_api(session, url):
    async with session.get(url, timeout=3) as response:
        return await response.json()

@tree.command(name='list', description='ホワイトリストを登録します。')
async def add_to_whitelist(interaction: discord.Interaction, mcid: str):
    # すでにホワイトリストに登録されているかをチェックします
    if is_already_whitelisted(mcid):
        embed = discord.Embed(
            description=f"⚠️ **{mcid}** さんはすでにホワイトリストに登録されています！",
            color=0xffa500
        )
        await interaction.response.send_message(embed=embed)
        return

    # Mojang APIからUUIDを取得します
    mojang_api_url = MOJANG_API_BASE_URL + mcid
    async with aiohttp.ClientSession() as session:
        try:
            # タイムアウトを設定してAPIからの応答を待ちます
            response_data = await asyncio.wait_for(fetch_mojang_api(session, mojang_api_url), timeout=2)
            uuid = response_data.get('id')
            # whitelist.jsonファイルを読み込み、新しいエントリを追加します
            with open(WHITELIST_PATH, 'r+') as f:
                whitelist = json.load(f)
                whitelist.append({
                    'uuid': uuid,
                    'name': mcid
                })
                # ファイルを書き込みモードで開き、新しいエントリを書き込みます
                f.seek(0)
                json.dump(whitelist, f, indent=2)
                f.truncate()

            # Embedを作成して、指定されたMCIDの追加を通知します
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
