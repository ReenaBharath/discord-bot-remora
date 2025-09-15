import os
import discord
from discord.ext import commands, tasks
from discord.utils import get
import asyncio
from dotenv import load_dotenv
import random
import aiohttp

# =========================
# Load environment variables
# =========================
load_dotenv()

CONFIG = {
    # Discord
    'DISCORD_TOKEN': os.getenv("DISCORD_TOKEN"),

    # Twitch
    'TWITCH_CLIENT_ID': os.getenv("TWITCH_CLIENT_ID"),
    'TWITCH_CLIENT_SECRET': os.getenv("TWITCH_CLIENT_SECRET"),
    'TWITCH_USERNAME': os.getenv("TWITCH_USERNAME"),

    # YouTube
    'YOUTUBE_API_KEY': os.getenv("YOUTUBE_API_KEY"),
    'YOUTUBE_CHANNEL_ID': os.getenv("YOUTUBE_CHANNEL_ID"),

    # TikTok
    'TIKTOK_USERNAME': os.getenv("TIKTOK_USERNAME"),

    # Discord Config
    'COMMAND_PREFIX': os.getenv("COMMAND_PREFIX", "!"),
    'COUNTING_CHANNEL_ID': int(os.getenv("COUNTING_CHANNEL_ID", 0)),
    'MEME_CHANNEL_ID': int(os.getenv("MEME_CHANNEL_ID", 0)),
    'WELCOME_CHANNEL_ID': int(os.getenv("WELCOME_CHANNEL_ID", 0)),  # optional
}

# =========================
# Intents
# =========================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # needed for welcome messages

bot = commands.Bot(command_prefix=CONFIG['COMMAND_PREFIX'], intents=intents)

# =========================
# EVENTS
# =========================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    auto_post_memes.start()   # start auto meme posting
    check_streams.start()     # background task for streams

# =========================
# WELCOME MESSAGE
# =========================
@bot.event
async def on_member_join(member):
    if CONFIG['WELCOME_CHANNEL_ID'] != 0:
        channel = bot.get_channel(CONFIG['WELCOME_CHANNEL_ID'])
    else:
        channel = get(member.guild.text_channels, name="general")  # fallback to #general

    if channel:
        await channel.send(f"👋 Welcome {member.mention} to the server!")

# =========================
# COUNTING GAME
# =========================
last_number = 0
last_user = None

@bot.event
async def on_message(message):
    global last_number, last_user

    if message.author.bot:
        return

    if message.channel.id == CONFIG['COUNTING_CHANNEL_ID'] and CONFIG['COUNTING_CHANNEL_ID'] != 0:
        try:
            number = int(message.content)

            # ✅ Correct number, different user
            if number == last_number + 1 and message.author != last_user:
                last_number = number
                last_user = message.author
                await message.add_reaction("✅")

            # ❌ Same user twice in a row
            elif message.author == last_user:
                await message.channel.send(
                    f"⚠️ {message.author.mention}, you can’t count twice in a row! Resetting back to 1."
                )
                last_number = 0
                last_user = None

            # ❌ Wrong number
            else:
                await message.channel.send(
                    f"❌ Wrong number, {message.author.mention}! Resetting back to 1."
                )
                last_number = 0
                last_user = None

        except ValueError:
            # ❌ Not a number
            await message.channel.send(
                f"❌ {message.author.mention}, only numbers are allowed! Resetting back to 1."
            )
            last_number = 0
            last_user = None

    await bot.process_commands(message)

# =========================
# COMMANDS
# =========================
@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! 🏓 {round(bot.latency * 1000)}ms")

@bot.command()
async def meme(ctx):
    url = "https://www.reddit.com/r/memes/top.json?limit=50&t=day"
    headers = {"User-Agent": "DiscordBot/1.0"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                await ctx.send("❌ Failed to fetch memes from Reddit.")
                return

            data = await resp.json()
            posts = data["data"]["children"]
            memes = [post["data"]["url"] for post in posts if post["data"].get("post_hint") == "image"]

            if memes:
                await ctx.send(random.choice(memes))
            else:
                await ctx.send("No memes found 😢")

# =========================
# BACKGROUND TASKS
# =========================
@tasks.loop(hours=3)  # auto post every 3 hour
async def auto_post_memes():
    channel = bot.get_channel(CONFIG['MEME_CHANNEL_ID'])
    if not channel:
        return

    url = "https://www.reddit.com/r/dankmemes/top.json?limit=50&t=day"
    headers = {"User-Agent": "DiscordBot/1.0"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return

            data = await resp.json()
            posts = data["data"]["children"]
            memes = [post["data"]["url"] for post in posts if post["data"].get("post_hint") == "image"]

            if memes:
                await channel.send(random.choice(memes))

@tasks.loop(minutes=1)
async def check_streams():
    # Placeholder: Add Twitch/YouTube API checks here
    pass

# =========================
# START BOT
# =========================
if __name__ == "__main__":
    token = CONFIG['DISCORD_TOKEN']
    if not token:
        print("❌ DISCORD_TOKEN not set in environment variables!")
    else:
        bot.run(token)
