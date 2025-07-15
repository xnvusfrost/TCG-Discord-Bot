import os
import sys
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from typing import cast
import traceback

# Load .env file
load_dotenv()

# Use cast to ensure type checker knows TOKEN is a str
TOKEN = cast(str, os.getenv("DISCORD_TOKEN"))

# Optional runtime check (recommended for safety)
if not TOKEN:
    print("❌ DISCORD_TOKEN is not set.")
    sys.exit(1)

# Setup intents and bot
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

COGS = [
    "cogs.binder",
    "cogs.currency",
    "cogs.help",
    "cogs.packs",
    "cogs.shop",
    "cogs.trade",
    "cogs.adventure"
]

@bot.event
async def on_ready():
    if bot.user is not None:
        print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    else:
        print("✅ Logged in, but bot user is None.")

async def main():
    async with bot:
        for cog in COGS:
            try:
                await bot.load_extension(cog)
                print(f"✅ Loaded cog: {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")
                traceback.print_exc()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())