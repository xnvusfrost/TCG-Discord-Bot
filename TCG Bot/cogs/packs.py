import random
import discord
from discord.ext import commands
from typing import Optional
from utils import add_cards_to_collection, get_balance, add_balance, user_packs, save_user_packs, load_pack

class Packs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="op")
    async def open_pack(self, ctx, pack_name: Optional[str] = None, amount: int = 1):
        user_id = str(ctx.author.id)

        packs = user_packs(user_id)
        if not packs:
            return await ctx.send(f"{ctx.author.mention}, you don't have any unopened packs.")

        if not pack_name:
            if isinstance(packs, list):
                user_inventory = {p["pack"]: p["count"] for p in packs}
            else:
                user_inventory = packs
            if not user_inventory:
                return await ctx.send(f"{ctx.author.mention}, you don't have any unopened packs.")
            pack_list = "\n".join(f"`{name}` × {qty}" for name, qty in user_inventory.items())
            return await ctx.send(
                f"{ctx.author.mention}, please specify a pack to open.\nYou own:\n{pack_list}"
            )

        pack_name = pack_name.lower()
        if amount < 1 or amount > 5:
            return await ctx.send(f"{ctx.author.mention}, you can only open between 1 and 5 packs at a time.")

        if isinstance(packs, list):
            user_pack_count = 0
            for pack in packs:
                if pack.get("pack") == pack_name:
                    user_pack_count = pack.get("count", 0)
                    break
        else:
            user_pack_count = packs.get(pack_name, 0)

        if user_pack_count < amount:
            return await ctx.send(f"{ctx.author.mention}, you only have {user_pack_count} `{pack_name}` pack(s).")

        try:
            pack_data = load_pack(pack_name)
        except FileNotFoundError:
            return await ctx.send(f"{ctx.author.mention}, pack `{pack_name}` not found.")

        cards = pack_data.get("cards", []) if isinstance(pack_data, dict) else pack_data
        if not cards:
            return await ctx.send(f"{ctx.author.mention}, no cards found in `{pack_name}` pack.")

        commons = [c for c in cards if c.get("rarity", "common") == "common"]
        uncommons = [c for c in cards if c.get("rarity") == "uncommon"]
        rares = [c for c in cards if c.get("rarity") == "rare"]
        energies = [c for c in cards if c.get("rarity") == "energy"]

        opened_cards = []
        for _ in range(amount):
            if len(commons) < 6 or len(uncommons) < 3 or len(rares) < 1 or len(energies) < 1:
                return await ctx.send(f"{ctx.author.mention}, not enough cards of each rarity in `{pack_name}` pack.")

            selected = []
            selected += random.sample(commons, 6)
            selected += random.sample(uncommons, 3)
            selected += random.sample(rares, 1)
            selected += random.sample(energies, 1)
            opened_cards.extend(selected)

        # Update packs
        if isinstance(packs, list):
            for pack in packs:
                if pack.get("pack") == pack_name:
                    pack["count"] -= amount
                    if pack["count"] <= 0:
                        packs.remove(pack)
                    break
        else:
            packs[pack_name] -= amount
            if packs[pack_name] <= 0:
                del packs[pack_name]

        save_user_packs(user_id, packs)

        # Add opened cards to user's binder collection
        add_cards_to_collection(user_id, opened_cards, pack_name)

        # ✨ Group opened cards by rarity
        grouped = {"common": [], "uncommon": [], "rare": [], "energy": []}
        for card in opened_cards:
            rarity = card.get("rarity", "common")
            name = card.get("name", str(card))
            grouped[rarity].append(name)

        # 🖼️ Format output
        rarity_order = ["common", "uncommon", "rare", "energy"]
        rarity_labels = {
            "common": "🔹 **Common Cards**",
            "uncommon": "🟢 **Uncommon Cards**",
            "rare": "🟣 **Rare Cards**",
            "energy": "🟡 **Energy Cards**"
        }

        result_lines = []
        for rarity in rarity_order:
            if grouped[rarity]:
                names = "\n".join(f"• {n}" for n in grouped[rarity])
                result_lines.append(f"{rarity_labels[rarity]}:\n{names}")

        result_message = "\n\n".join(result_lines)

        await ctx.send(f"{ctx.author.mention}, you opened {amount} `{pack_name}` pack(s) and got:\n\n{result_message}")

async def setup(bot):
    await bot.add_cog(Packs(bot))

