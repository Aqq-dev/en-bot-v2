import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive
from flask import Flask
import threading

keep_alive()
app = Flask(__name__)
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))
TRACK_CHANNEL_ID = int(os.getenv("TRACK_CHANNEL_ID"))

def create_embed(title: str, description: str, color: discord.Color = discord.Color.blurple()):
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text="dev: @takosu_23532")
    return embed

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Sync failed: {e}")

# ===== メッセージ数カウント =====
@bot.tree.command(name="trackrecord-check", description="指定チャンネルまたは現在のチャンネルのメッセージ数を表示します")
@app_commands.describe(channel="対象チャンネル（省略可）")
async def trackrecord_check(interaction: discord.Interaction, channel: discord.TextChannel = None):
    target_channel = channel or interaction.channel
    count = 0
    async for _ in target_channel.history(limit=None):
        count += 1

    embed = create_embed(
        "実績数",
        f"**{target_channel.mention} のメッセージ数:** {count} 件",
        discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ===== ログ機能 =====
async def send_log(embed: discord.Embed):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        await log_channel.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot:
        return
    embed = create_embed(
        "メッセージ編集",
        f"**ユーザー:** {before.author.mention}\n\n**Before:** {before.content}\n**After:** {after.content}",
        discord.Color.orange()
    )
    await send_log(embed)

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    embed = create_embed(
        "メッセージ削除",
        f"**ユーザー:** {message.author.mention}\n\n**Content:** {message.content}",
        discord.Color.red()
    )
    await send_log(embed)

@bot.event
async def on_guild_channel_create(channel):
    embed = create_embed(
        "チャンネル作成",
        f"**チャンネル:** {channel.mention}",
        discord.Color.green()
    )
    await send_log(embed)

@bot.event
async def on_guild_channel_delete(channel):
    embed = create_embed(
        "チャンネル削除",
        f"**チャンネル名:** {channel.name}",
        discord.Color.dark_red()
    )
    await send_log(embed)

# ===== Flask + Bot 両立 =====
def run_flask():
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    bot.run(TOKEN)
