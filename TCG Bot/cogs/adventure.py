import discord
from discord.ext import commands
import random
import os
import asyncio
from utils import load_user_file

# If save_json is defined elsewhere, import it from the correct module, e.g.:
# from another_module import save_json

def save_json(path, data):
    import json
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

class Adventure(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sessions = {}  # user_id -> adventure state

    @commands.group()
    async def adventure(self, ctx):
        """Pokémon Adventure Mini-Game"""
        if ctx.invoked_subcommand is None:
            await ctx.send("Use `!adventure start` to begin your adventure!")

    @adventure.command()
    async def start(self, ctx):
        # Show user's Pokémon cards (not trainers/energy)
        user_id = str(ctx.author.id)
        user_cards_data = load_user_file(user_id, "cards.json")
        user_cards = user_cards_data.get("cards", [])
        # Filter for Pokémon cards (replace with your own logic)
        pokemon_cards = [c for c in user_cards if c.get("type", "").lower() == "pokemon"]
        if not pokemon_cards:
            await ctx.send("You don't have any Pokémon cards to adventure with!")
            return
        card_list = "\n".join(f"{idx+1}. {c['name']} (#{c['number']})" for idx, c in enumerate(pokemon_cards))
        await ctx.send(f"Choose a Pokémon to adventure with using `!adventure pick <number>`:\n{card_list}")
        self.sessions[ctx.author.id] = {"pokemon_cards": pokemon_cards}

    @adventure.command()
    async def pick(self, ctx, number: int):
        session = self.sessions.get(ctx.author.id)
        if not session or "pokemon_cards" not in session:
            await ctx.send("Start an adventure first with `!adventure start`.")
            return
        pokemon_cards = session["pokemon_cards"]
        if not (1 <= number <= len(pokemon_cards)):
            await ctx.send("Invalid number. Please pick a valid Pokémon.")
            return
        chosen = pokemon_cards[number-1]
        self.sessions[ctx.author.id] = {"pokemon": chosen, "step": 0}
        await ctx.send(f"You set out on your adventure with {chosen['name']}!")
        await self.next_event(ctx)

    async def next_event(self, ctx):
        user_id = str(ctx.author.id)
        session = self.sessions.get(ctx.author.id)
        if not session:
            await ctx.send("No adventure in progress.")
            return
        # Randomly pick an event: chest or wild Pokémon
        event = random.choice(["chest", "wild"])
        if event == "chest":
            reward = random.choice(["gold", "pack", "booster"])
            if reward == "gold":
                amount = random.randint(50, 200)
                # Add gold to user inventory
                inv = load_user_file(user_id, "inventory.json")
                inv["gold"] = inv.get("gold", 0) + amount
                save_json(f"data/users/{user_id}/inventory.json", inv)
                await ctx.send(f"You found a chest with {amount} gold! (Now you have {inv['gold']} gold.)")
            elif reward == "pack":
                inv = load_user_file(user_id, "inventory.json")
                inv["packs"] = inv.get("packs", 0) + 1
                save_json(f"data/users/{user_id}/inventory.json", inv)
                await ctx.send("You found a chest with a card pack! (Added to your inventory.)")
            else:
                inv = load_user_file(user_id, "inventory.json")
                inv["boosters"] = inv.get("boosters", 0) + 1
                save_json(f"data/users/{user_id}/inventory.json", inv)
                await ctx.send("You found a chest with a booster box! (Added to your inventory.)")
            await self.next_event(ctx)
        else:
            # Encounter a wild Pokémon (not trainer/energy)
            # Replace with your own logic to pick a random Pokémon card from all packs
            from cogs.binder import load_pack_cards
            all_packs = [f[:-5] for f in os.listdir("data/cardpacks") if f.endswith(".json")]
            all_pokemon = []
            for pack in all_packs:
                for card in load_pack_cards(pack):
                    if card.get("type", "").lower() == "pokemon":
                        all_pokemon.append(card)
            if not all_pokemon:
                await ctx.send("No wild Pokémon found in the world!")
                return
            wild = random.choice(all_pokemon)
            session["wild"] = wild
            await ctx.send(f"A wild {wild['name']} (#{wild['number']}) appeared! Type `!adventure battle` or `!adventure run`.")

    @adventure.command(name="battle")
    async def battle(self, ctx):
        session = self.sessions.get(ctx.author.id)
        if not session or "wild" not in session or "pokemon" not in session:
            await ctx.send("No wild Pokémon to battle. Start an adventure first!")
            return
        # Simple random battle logic
        win = random.choice([True, False])
        if win:
            await ctx.send("You won the battle! Try to catch the Pokémon with `!adventure catch`.")
            session["can_catch"] = True
        else:
            await ctx.send("You lost the battle. Your adventure ends here.")
            del self.sessions[ctx.author.id]

    @adventure.command(name="catch")
    async def catch(self, ctx):
        session = self.sessions.get(ctx.author.id)
        if not session or not session.get("can_catch") or "wild" not in session:
            await ctx.send("You can't catch a Pokémon right now.")
            return
        user_id = str(ctx.author.id)
        wild = session["wild"]
        caught = random.random() < 0.3  # 30% catch chance
        if caught:
            # Add to user's binder (cards.json or duplicates.json)
            user_cards_data = load_user_file(user_id, "cards.json")
            user_cards = user_cards_data.get("cards", [])
            already = any(
                c.get("name", "").lower() == wild.get("name", "").lower() and
                str(c.get("number", "")) == str(wild.get("number", ""))
                for c in user_cards
            )
            if not already:
                user_cards.append(wild)
                user_cards_data["cards"] = user_cards
                save_json(f"data/users/{user_id}/cards.json", user_cards_data)
                await ctx.send(f"You caught {wild['name']}! Added to your binder.")
            else:
                # Add to duplicates
                user_dupes_data = load_user_file(user_id, "duplicates.json")
                user_dupes = user_dupes_data.get("duplicates", [])
                found = False
                for d in user_dupes:
                    if (d.get("name", "").lower() == wild.get("name", "").lower() and
                        str(d.get("number", "")) == str(wild.get("number", ""))):
                        d["count"] = d.get("count", 1) + 1
                        found = True
                        break
                if not found:
                    user_dupes.append({"name": wild["name"], "number": wild["number"], "pack": wild.get("pack"), "count": 1})
                user_dupes_data["duplicates"] = user_dupes
                save_json(f"data/users/{user_id}/duplicates.json", user_dupes_data)
                await ctx.send(f"You caught another {wild['name']}! Added to your duplicates.")
            del self.sessions[ctx.author.id]
        else:
            await ctx.send("The Pokémon escaped!")
            del self.sessions[ctx.author.id]

    @adventure.command(name="run")
    async def run(self, ctx):
        session = self.sessions.get(ctx.author.id)
        if not session:
            await ctx.send("No adventure in progress.")
            return
        await ctx.send("You ran away safely. Onward to the next adventure!")
        await self.next_event(ctx)

async def setup(bot):
    await bot.add_cog(Adventure(bot))