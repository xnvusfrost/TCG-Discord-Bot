import random
import discord
from discord.ext import commands
from typing import Optional
from utils import add_cards_to_collection, user_packs, save_user_packs, load_pack, load_user_file, save_user_file
import os
import json
import time

# --- Pack Energy System ---
MAX_PACK_ENERGY = 2
PACK_ENERGY_REGEN_SECONDS = 12 * 60 * 60  # 12 hours

def get_user_pack_energy(user_id):
    data = load_user_file(user_id, "pack_energy.json")
    now = int(time.time())
    if not data:
        data = {"pack_energy": MAX_PACK_ENERGY, "last_regen": now}
        save_user_file(user_id, "pack_energy.json", data)
    else:
        last_regen = data.get("last_regen", now)
        pack_energy = data.get("pack_energy", MAX_PACK_ENERGY)
        elapsed = now - last_regen
        regen = elapsed // PACK_ENERGY_REGEN_SECONDS
        if regen > 0:
            pack_energy = min(MAX_PACK_ENERGY, pack_energy + regen)
            last_regen = last_regen + regen * PACK_ENERGY_REGEN_SECONDS
            data = {"pack_energy": pack_energy, "last_regen": last_regen}
            save_user_file(user_id, "pack_energy.json", data)
    return data["pack_energy"]

def use_pack_energy(user_id):
    data = load_user_file(user_id, "pack_energy.json")
    now = int(time.time())
    if not data:
        data = {"pack_energy": MAX_PACK_ENERGY, "last_regen": now}
    else:
        last_regen = data.get("last_regen", now)
        pack_energy = data.get("pack_energy", MAX_PACK_ENERGY)
        elapsed = now - last_regen
        regen = elapsed // PACK_ENERGY_REGEN_SECONDS
        if regen > 0:
            pack_energy = min(MAX_PACK_ENERGY, pack_energy + regen)
            last_regen = last_regen + regen * PACK_ENERGY_REGEN_SECONDS
        data = {"pack_energy": pack_energy, "last_regen": last_regen}
    if data["pack_energy"] > 0:
        data["pack_energy"] -= 1
        save_user_file(user_id, "pack_energy.json", data)
        return True
    save_user_file(user_id, "pack_energy.json", data)
    return False
# --- End Pack Energy System ---

# --- Wonderpack Energy System ---
MAX_WONDERPACK_ENERGY = 4  # 4 chances per day
WONDERPACK_ENERGY_REGEN_SECONDS = 6 * 60 * 60  # 6 hours

def get_user_wonderpack_energy(user_id):
    data = load_user_file(user_id, "wonderpack_energy.json")
    now = int(time.time())
    if not data:
        data = {"wonderpack_energy": MAX_WONDERPACK_ENERGY, "last_regen": now}
        save_user_file(user_id, "wonderpack_energy.json", data)
    else:
        last_regen = data.get("last_regen", now)
        wonderpack_energy = data.get("wonderpack_energy", MAX_WONDERPACK_ENERGY)
        elapsed = now - last_regen
        regen = elapsed // WONDERPACK_ENERGY_REGEN_SECONDS
        if regen > 0:
            wonderpack_energy = min(MAX_WONDERPACK_ENERGY, wonderpack_energy + regen)
            last_regen = last_regen + regen * WONDERPACK_ENERGY_REGEN_SECONDS
            data = {"wonderpack_energy": wonderpack_energy, "last_regen": last_regen}
            save_user_file(user_id, "wonderpack_energy.json", data)
    return data["wonderpack_energy"]

def use_wonderpack_energy(user_id):
    data = load_user_file(user_id, "wonderpack_energy.json")
    now = int(time.time())
    if not data:
        data = {"wonderpack_energy": MAX_WONDERPACK_ENERGY, "last_regen": now}
    else:
        last_regen = data.get("last_regen", now)
        wonderpack_energy = data.get("wonderpack_energy", MAX_WONDERPACK_ENERGY)
        elapsed = now - last_regen
        regen = elapsed // WONDERPACK_ENERGY_REGEN_SECONDS
        if regen > 0:
            wonderpack_energy = min(MAX_WONDERPACK_ENERGY, wonderpack_energy + regen)
            last_regen = last_regen + regen * WONDERPACK_ENERGY_REGEN_SECONDS
        data = {"wonderpack_energy": wonderpack_energy, "last_regen": last_regen}
    if data["wonderpack_energy"] > 0:
        data["wonderpack_energy"] -= 1
        save_user_file(user_id, "wonderpack_energy.json", data)
        return True
    save_user_file(user_id, "wonderpack_energy.json", data)
    return False
# --- End Wonderpack Energy System ---

class Packs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_wonderpack = {}

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

    @commands.command(aliases=["fp"])
    async def freepack(self, ctx, *, pack_name: str):
        """Use 1 Pack Energy to get a free pack of your choice (not valid for booster boxes)."""
        forbidden = ["booster box", "boosterbox", "box"]
        if pack_name.lower() in forbidden or "box" in pack_name.lower():
            await ctx.send(f"{ctx.author.mention}, you cannot use Pack Energy on booster boxes.")
            return

        user_id = str(ctx.author.id)
        if use_pack_energy(user_id):
            # Give the user a free pack (add 1 to their unopened packs)
            packs = user_packs(user_id)
            if isinstance(packs, list):
                found = False
                for pack in packs:
                    if pack.get("pack") == pack_name:
                        pack["count"] += 1
                        found = True
                        break
                if not found:
                    packs.append({"pack": pack_name, "count": 1})
            else:
                packs[pack_name] = packs.get(pack_name, 0) + 1
            save_user_packs(user_id, packs)
            await ctx.send(f"{ctx.author.mention} used 1 Pack Energy and received a free '{pack_name}' pack!")
        else:
            await ctx.send(f"{ctx.author.mention}, you don't have enough Pack Energy! Wait for it to recharge.")

    @commands.command(aliases=["pe"])
    async def packenergy(self, ctx):
        """Check your current Pack Energy and time until next recharge."""
        user_id = str(ctx.author.id)
        data = load_user_file(user_id, "pack_energy.json")
        now = int(time.time())
        if not data:
            pack_energy = MAX_PACK_ENERGY
            time_left = 0
        else:
            pack_energy = get_user_pack_energy(user_id)
            last_regen = data.get("last_regen", now)
            current_energy = data.get("pack_energy", MAX_PACK_ENERGY)
            if current_energy < MAX_PACK_ENERGY:
                next_regen = last_regen + PACK_ENERGY_REGEN_SECONDS
                time_left = max(0, next_regen - now)
            else:
                time_left = 0

        if time_left > 0:
            hours = time_left // 3600
            minutes = (time_left % 3600) // 60
            seconds = time_left % 60
            time_str = f"{hours}h {minutes}m {seconds}s"
            await ctx.send(
                f"{ctx.author.mention}, you have {pack_energy}/{MAX_PACK_ENERGY} Pack Energy.\n"
                f"Next energy in: **{time_str}**"
            )
        else:
            await ctx.send(
                f"{ctx.author.mention}, you have {pack_energy}/{MAX_PACK_ENERGY} Pack Energy.\n"
                f"Your energy is full!"
            )

    @commands.command(aliases=["we"])
    async def wonderenergy(self, ctx):
        """Check your current Wonderpack Energy and time until next recharge."""
        user_id = str(ctx.author.id)
        data = load_user_file(user_id, "wonderpack_energy.json")
        now = int(time.time())
        if not data:
            wonderpack_energy = MAX_WONDERPACK_ENERGY
            time_left = 0
        else:
            wonderpack_energy = get_user_wonderpack_energy(user_id)
            last_regen = data.get("last_regen", now)
            current_energy = data.get("wonderpack_energy", MAX_WONDERPACK_ENERGY)
            if current_energy < MAX_WONDERPACK_ENERGY:
                next_regen = last_regen + WONDERPACK_ENERGY_REGEN_SECONDS
                time_left = max(0, next_regen - now)
            else:
                time_left = 0

        if time_left > 0:
            hours = time_left // 3600
            minutes = (time_left % 3600) // 60
            seconds = time_left % 60
            time_str = f"{hours}h {minutes}m {seconds}s"
            await ctx.send(
                f"{ctx.author.mention}, you have {wonderpack_energy}/{MAX_WONDERPACK_ENERGY} Wonderpack Energy.\n"
                f"Next energy in: **{time_str}**"
            )
        else:
            await ctx.send(
                f"{ctx.author.mention}, you have {wonderpack_energy}/{MAX_WONDERPACK_ENERGY} Wonderpack Energy.\n"
                f"Your energy is full!"
            )

    @commands.command(name="wonderpick", aliases=["wp"])
    async def wonderpick(self, ctx):
        """
        Use 1 Wonderpack Energy to be presented with 5 random non-energy cards from a random shop pack.
        React ✅ to shuffle and hide the cards, then pick 1️⃣-5️⃣ to receive a random card.
        Shows images of the cards if available.
        """
        user_id = str(ctx.author.id)
        if user_id in self.pending_wonderpack:
            await ctx.send(f"{ctx.author.mention}, you already have a Wonderpick in progress!")
            return

        if not use_wonderpack_energy(user_id):
            await ctx.send(f"{ctx.author.mention}, you don't have enough Wonderpack Energy! Wait for it to recharge.")
            return

        # --- Get shop packs ---
        shop_packs = ["base", "fossil", "rocket", "jungle"]  # Replace with your actual shop pack names or function

        if not shop_packs:
            await ctx.send("No shop packs available.")
            return

        # Pick a random shop pack
        pack_name = random.choice(shop_packs)
        try:
            pack_data = load_pack(pack_name)
        except Exception:
            await ctx.send("Failed to load a random shop pack.")
            return

        cards = pack_data.get("cards", []) if isinstance(pack_data, dict) else pack_data
        # Exclude energy cards
        non_energy_cards = [card for card in cards if card.get("rarity", "common").lower() != "energy"]
        if len(non_energy_cards) < 5:
            await ctx.send("Not enough non-energy cards in the selected pack.")
            return

        # Randomly pick 5 non-energy cards
        chosen_cards = random.sample(non_energy_cards, 5)

        # Show the cards as images (if available) and ask user to react with ✅ to shuffle and hide
        emoji_list = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        embeds = []
        for i, card in enumerate(chosen_cards):
            name = card.get("name", f"Card {i+1}")
            image_url = card.get("image_url")
            embed = discord.Embed(
                title=f"{emoji_list[i]} {name}",
                description=""
            )
            if image_url:
                embed.set_image(url=image_url)
            else:
                embed.description = "*(No image available)*"
            embeds.append(embed)

        msg = await ctx.send(
            f"{ctx.author.mention}, you used 1 Wonderpack Energy!\n"
            f"Random shop pack: **{pack_name}**\n"
            f"Here are 5 cards. React with ✅ to shuffle and hide the cards, then pick 1️⃣-5️⃣ to receive a random card!",
            embeds=embeds
        )
        await msg.add_reaction("✅")

        # Store the options for the user
        self.pending_wonderpack[user_id] = {
            "pack": pack_name,
            "cards": chosen_cards,
            "msg_id": msg.id,
            "stage": "awaiting_shuffle"
        }

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        emoji_list = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        user_id = str(user.id)
        pending = self.pending_wonderpack.get(user_id)
        if not pending:
            return
        if reaction.message.id != pending["msg_id"]:
            return

        # Stage 1: Awaiting shuffle (✅)
        if pending.get("stage") == "awaiting_shuffle" and str(reaction.emoji) == "✅":
            random.shuffle(pending["cards"])
            pending["stage"] = "awaiting_pick"
            self.pending_wonderpack[user_id] = pending

            # Edit the message to hide the cards and prompt for pick
            try:
                await reaction.message.edit(
                    content=(
                        f"{user.mention}, the cards have been shuffled and hidden!\n"
                        f"React with 1️⃣, 2️⃣, 3️⃣, 4️⃣, or 5️⃣ to pick your card!"
                    ),
                    embeds=[]
                )
            except Exception:
                pass
            for emoji in emoji_list:
                await reaction.message.add_reaction(emoji)
            return

        # Stage 2: Awaiting pick (1️⃣-5️⃣)
        if pending.get("stage") == "awaiting_pick" and str(reaction.emoji) in emoji_list:
            idx = emoji_list.index(str(reaction.emoji))
            selected_card = pending["cards"][idx]

            # Check if the card is a duplicate before adding
            result = add_cards_to_collection(user_id, [selected_card], pending["pack"])
            card_name = selected_card.get('name', str(selected_card))

            # Compose the response message
            if isinstance(result, dict) and result.get("duplicates"):
                await reaction.message.channel.send(
                    f"{user.mention}, you picked **{card_name}** from **{pending['pack']}**!\n"
                    f"That card was already in your binder, so it was added to your **duplicate binder**."
                )
            else:
                await reaction.message.channel.send(
                    f"{user.mention}, you picked **{card_name}** from **{pending['pack']}**!\n"
                    f"That card has been added to your **binder**."
                )
            del self.pending_wonderpack[user_id]

async def setup(bot):
    await bot.add_cog(Packs(bot))