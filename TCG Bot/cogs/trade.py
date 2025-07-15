import discord
from discord.ext import commands
import asyncio
from utils import load_user_file, save_user_file

class Trade(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="trade")
    async def trade(self, ctx, user: str, 
                    my_card_name: str, my_card_number: str, my_card_pack: str,
                    their_card_name: str, their_card_number: str, their_card_pack: str):
        """
        Trade a card with another user.
        Usage: !trade @user my_card_name my_card_number my_card_pack their_card_name their_card_number their_card_pack
        Example: !trade @Bob Pikachu 58 base Bulbasaur 44 base
        """
        # Try to resolve user as mention or username
        member = None
        if user.startswith("<@") and user.endswith(">"):
            user_id = user.replace("<@", "").replace("!", "").replace(">", "")
            member = ctx.guild.get_member(int(user_id))
        if not member:
            user_lower = user.lower()
            for m in ctx.guild.members:
                if (m.name.lower() == user_lower or
                    m.display_name.lower() == user_lower or
                    f"{m.name}#{m.discriminator}".lower() == user_lower):
                    member = m
                    break
        if not member:
            await ctx.send(f"Could not find user `{user}` in this server.")
            return

        user1_id = str(ctx.author.id)
        user2_id = str(member.id)

        # Load user1's and user2's cards and duplicates
        user1_cards = load_user_file(user1_id, "cards.json").get("cards", [])
        user2_cards = load_user_file(user2_id, "cards.json").get("cards", [])
        user1_dupes = load_user_file(user1_id, "duplicates.json").get("duplicates", [])
        user2_dupes = load_user_file(user2_id, "duplicates.json").get("duplicates", [])

        # Helper to find a card in a list
        def find_card(card_list, name, number, pack):
            for card in card_list:
                if (card.get("name", "").lower() == name.lower() and
                    str(card.get("number", "")) == str(number) and
                    card.get("pack", "").lower() == pack.lower()):
                    return card
            return None

        # Helper to remove a card from a list (by name, number, pack)
        def remove_card(card_list, name, number, pack):
            for i, card in enumerate(card_list):
                if (card.get("name", "").lower() == name.lower() and
                    str(card.get("number", "")) == str(number) and
                    card.get("pack", "").lower() == pack.lower()):
                    del card_list[i]
                    return

        # Find the cards in dupes (must have count > 0)
        my_card = find_card(user1_dupes, my_card_name, my_card_number, my_card_pack)
        their_card = find_card(user2_dupes, their_card_name, their_card_number, their_card_pack)

        if not my_card or my_card.get("count", 0) < 1:
            await ctx.send(f"{ctx.author.mention}, you do not have that card as a duplicate.")
            return
        if not their_card or their_card.get("count", 0) < 1:
            await ctx.send(f"{member.mention} does not have that card as a duplicate.")
            return

        # Ask for confirmation from both users
        await ctx.send(
            f"{ctx.author.mention} wants to trade their duplicate **{my_card_name} #{my_card_number} ({my_card_pack})** "
            f"for {member.mention}'s duplicate **{their_card_name} #{their_card_number} ({their_card_pack})**.\n"
            f"Both users, please confirm by reacting with ✅."
        )
        confirm_msg = await ctx.send("Waiting for both users to confirm...")

        await confirm_msg.add_reaction("✅")

        def check(reaction, reactor):
            return (
                reaction.message.id == confirm_msg.id and
                str(reaction.emoji) == "✅" and
                reactor.id in [ctx.author.id, member.id]
            )

        confirmed = set()
        while len(confirmed) < 2:
            try:
                reaction, reactor = await ctx.bot.wait_for("reaction_add", timeout=60.0, check=check)
                confirmed.add(reactor.id)
            except asyncio.TimeoutError:
                await ctx.send("Trade cancelled due to timeout.")
                return

        # Remove one from each user's dupes
        my_card["count"] -= 1
        their_card["count"] -= 1

        # Remove from dupes if count is now 0
        if my_card["count"] <= 0:
            remove_card(user1_dupes, my_card_name, my_card_number, my_card_pack)
        if their_card["count"] <= 0:
            remove_card(user2_dupes, their_card_name, their_card_number, their_card_pack)

        # Helper: check if user has card in main binder
        def has_in_main_binder(user_cards, card):
            for c in user_cards:
                if (c.get("name", "").lower() == card["name"].lower() and
                    str(c.get("number", "")) == str(card["number"]) and
                    c.get("pack", "").lower() == card["pack"].lower()):
                    return True
            return False

        # Helper: add card to dupes (increment if exists, else add)
        def add_to_dupes(dupes, card):
            for c in dupes:
                if (c.get("name", "").lower() == card["name"].lower() and
                    str(c.get("number", "")) == str(card["number"]) and
                    c.get("pack", "").lower() == card["pack"].lower()):
                    c["count"] += 1
                    return
            new_card = dict(card)
            new_card["count"] = 1
            dupes.append(new_card)

        # Helper: add card to main binder if not present
        def add_to_main_binder(user_cards, card):
            user_cards.append({
                "name": card["name"],
                "number": card["number"],
                "pack": card["pack"]
            })

        # Give each user the other's card
        # For user1 (initiator), receiving their_card
        if has_in_main_binder(user1_cards, their_card):
            add_to_dupes(user1_dupes, their_card)
        else:
            add_to_main_binder(user1_cards, their_card)

        # For user2 (target), receiving my_card
        if has_in_main_binder(user2_cards, my_card):
            add_to_dupes(user2_dupes, my_card)
        else:
            add_to_main_binder(user2_cards, my_card)

        # Save updated files
        save_user_file(user1_id, "cards.json", {"cards": user1_cards})
        save_user_file(user2_id, "cards.json", {"cards": user2_cards})
        save_user_file(user1_id, "duplicates.json", {"duplicates": user1_dupes})
        save_user_file(user2_id, "duplicates.json", {"duplicates": user2_dupes})

        await ctx.send(
            f"Trade complete! {ctx.author.mention} and {member.mention} have swapped their duplicate cards."
        )

async def setup(bot):
    await bot.add_cog(Trade(bot))