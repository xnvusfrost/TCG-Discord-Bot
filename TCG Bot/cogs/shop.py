import discord
from discord.ext import commands
import os
import json
import asyncio
from utils import user_packs, save_user_packs, load_pack

SHOP_ITEMS_FILE = "data/shop_items.json"

def load_shop_items():
    if os.path.exists(SHOP_ITEMS_FILE):
        with open(SHOP_ITEMS_FILE, "r") as f:
            return json.load(f)
    return {
        "base": {"price": 300},
        "base booster box": {"price": 10500, "box_of": "base"},  # 36 packs, discounted
        "jungle": {"price": 450},
        "jungle booster box": {"price": 15900, "box_of": "jungle"},  # 36 packs, discounted
        "fossil": {"price": 500},
        "fossil booster box": {"price": 17700, "box_of": "fossil"},  # 36 packs, discounted
        "rocket": {"price": 550},
        "rocket booster box": {"price": 19500, "box_of": "rocket"},  # 36 packs, discounted
    }

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.shop_items = load_shop_items()
        self.emoji_map = {
            "base": "1️⃣",
            "base booster box": "2️⃣",
            "jungle": "3️⃣",
            "jungle booster box": "4️⃣",
            "fossil": "5️⃣",
            "fossil booster box": "6️⃣",
            "rocket": "7️⃣",
            "rocket booster box": "8️⃣"
        }
        self.reverse_emoji_map = {v: k for k, v in self.emoji_map.items()}

    @commands.command()
    async def shop(self, ctx):
        def make_embed():
            embed = discord.Embed(title="🛒 Card Pack Shop", color=0x00ff00)
            for pack, emoji in self.emoji_map.items():
                price = self.shop_items[pack]["price"]
                embed.add_field(name=f"{emoji} {pack.title()}", value=f"💰 {price} coins", inline=False)
            embed.set_footer(text="React to buy 1 pack/box. React ❌ to exit. You have 30 seconds.")
            return embed

        emoji_list = list(self.emoji_map.values()) + ["❌"]

        while True:
            message = await ctx.send(embed=make_embed())
            for emoji in emoji_list:
                await message.add_reaction(emoji)

            def check(reaction, user):
                return (
                    user == ctx.author and
                    (str(reaction.emoji) in self.reverse_emoji_map or str(reaction.emoji) == "❌")
                    and reaction.message.id == message.id
                )

            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
                emoji = str(reaction.emoji)
                if emoji == "❌":
                    await message.delete()
                    await ctx.send("🛒 Shop closed.", delete_after=3)
                    break

                pack_name = self.reverse_emoji_map[emoji]
                item = self.shop_items[pack_name]
                price = item["price"]
                user_id = str(ctx.author.id)

                # Use the Currency cog for balance operations
                currency_cog = self.bot.get_cog("Currency")
                if not currency_cog:
                    await ctx.send("Currency system not loaded. Please contact an admin.")
                    await message.delete()
                    break

                user_data = currency_cog.get_balance(user_id)
                balance = user_data["balance"]
                if balance < price:
                    await ctx.send(f"{ctx.author.mention}, you don't have enough coins for {pack_name.title()}!", delete_after=3)
                    await message.delete()
                    continue

                currency_cog.add_balance(user_id, -price)
                packs = user_packs(user_id) or []
                # Ensure packs is always a list of dicts
                if not isinstance(packs, list):
                    packs = []

                if "box_of" in item:
                    pack_to_add = item["box_of"]
                    packs_to_add = 36
                    found = False
                    for pack in packs:
                        if pack.get("pack") == pack_to_add:
                            pack["count"] += packs_to_add
                            found = True
                            break
                    if not found:
                        packs.append({"pack": pack_to_add, "count": packs_to_add})
                    save_user_packs(user_id, packs)
                    await ctx.send(f"{ctx.author.mention}, you bought 1 **{pack_name.title()}**! "
                                   f"That's {packs_to_add} {pack_to_add.title()} packs. Use `!op {pack_to_add}` to open them.", delete_after=5)
                else:
                    found = False
                    for pack in packs:
                        if pack.get("pack") == pack_name:
                            pack["count"] += 1
                            found = True
                            break
                    if not found:
                        packs.append({"pack": pack_name, "count": 1})
                    save_user_packs(user_id, packs)
                    await ctx.send(f"{ctx.author.mention}, you bought 1 **{pack_name.title()}** pack! "
                                   f"Use `!op {pack_name}` to open it later.", delete_after=5)

                await message.delete()  # Delete the old shop embed before showing a new one

            except asyncio.TimeoutError:
                try:
                    await message.edit(embed=discord.Embed(title="🛒 Shop timed out.", color=0xff0000))
                except Exception:
                    pass
                break

async def setup(bot):
    await bot.add_cog(Shop(bot))