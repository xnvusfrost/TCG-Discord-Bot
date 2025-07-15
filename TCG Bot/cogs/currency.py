import discord
from discord.ext import commands
from datetime import datetime, timedelta
import random
import asyncio
from utils import load_user_file, save_user_file, user_packs, save_user_packs, load_pack

class Currency(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_balance(self, user_id):
        data = load_user_file(user_id, "balances.json")
        if not data:
            data = {"balance": 0, "last_daily": None}
        return data

    def add_balance(self, user_id, amount):
        user_data = self.get_balance(user_id)
        user_data["balance"] = user_data.get("balance", 0) + amount
        save_user_file(user_id, "balances.json", user_data)

    def set_last_daily(self, user_id):
        user_data = self.get_balance(user_id)
        user_data["last_daily"] = datetime.utcnow().isoformat()
        save_user_file(user_id, "balances.json", user_data)

    def subtract_balance(self, user_id, amount):
        user_data = self.get_balance(user_id)
        user_data["balance"] = max(0, user_data.get("balance", 0) - amount)
        save_user_file(user_id, "balances.json", user_data)

    @commands.command(name="bal")
    async def bal(self, ctx):
        user_data = self.get_balance(str(ctx.author.id))
        amount = user_data.get("balance", 0)
        await ctx.send(f"{ctx.author.mention}, you have 💰 {amount} coins.")

    @commands.command(name="give")
    async def give(self, ctx, member: discord.Member, amount: int):
        if amount <= 0:
            return await ctx.send("Amount must be greater than zero.")
        sender_id = str(ctx.author.id)
        receiver_id = str(member.id)
        if self.get_balance(sender_id).get("balance", 0) < amount:
            return await ctx.send("You don’t have enough coins.")
        self.subtract_balance(sender_id, amount)
        self.add_balance(receiver_id, amount)
        await ctx.send(f"{ctx.author.display_name} gave 💰 {amount} coins to {member.display_name}!")

    @commands.command(name="daily")
    async def daily(self, ctx):
        user_id = str(ctx.author.id)
        user_data = self.get_balance(user_id)
        now = datetime.utcnow()
        last_claimed = user_data.get("last_daily")
        if last_claimed:
            last_time = datetime.fromisoformat(last_claimed)
            if now - last_time < timedelta(hours=24):
                remaining = timedelta(hours=24) - (now - last_time)
                return await ctx.send(f"You've already claimed your daily reward! Try again in {remaining.seconds // 3600}h {(remaining.seconds % 3600) // 60}m.")
        self.add_balance(user_id, 1000)  # Daily reward amount
        self.set_last_daily(user_id)
        await ctx.send(f"{ctx.author.mention}, you claimed your daily reward of 💰 1000 coins!")

    @commands.command(name="flip")
    async def flip_coin(self, ctx, guess: str, amount: int):
        guess = guess.lower()
        if guess not in ["heads", "tails"]:
            return await ctx.send("Guess must be 'heads' or 'tails'.")
        if amount <= 0:
            return await ctx.send("Bet must be greater than zero.")
        if amount > 3000:
            return await ctx.send("The maximum bet is 3000 coins.")
        user_id = str(ctx.author.id)
        balance = self.get_balance(user_id).get("balance", 0)
        if balance < amount:
            return await ctx.send("You don't have enough coins to bet that amount.")

        result = random.choice(["heads", "tails"])
        if guess == result:
            self.add_balance(user_id, amount)
            await ctx.send(f"🪙 It's **{result}**! You won 💰 {amount} coins!")
        else:
            self.subtract_balance(user_id, amount)
            await ctx.send(f"🪙 It's **{result}**! You lost 💰 {amount} coins.")

    @commands.command(name="fwg")
    async def fire_water_grass(self, ctx, amount: int):
        choices = {
            "🔥": "fire",
            "💧": "water",
            "🌿": "grass"
        }
        if amount <= 0:
            return await ctx.send("Bet must be greater than zero.")
        user_id = str(ctx.author.id)
        balance = self.get_balance(user_id).get("balance", 0)
        if balance < amount:
            return await ctx.send("You don't have enough coins to bet that amount.")

        embed = discord.Embed(
            title="Fire 🔥 Water 💧 Grass 🌿",
            description="React with your choice!\n🔥 = Fire\n💧 = Water\n🌿 = Grass",
            color=discord.Color.green()
        )
        message = await ctx.send(embed=embed)
        for emoji in choices:
            await message.add_reaction(emoji)

        def check(reaction, user):
            return (
                user == ctx.author and
                str(reaction.emoji) in choices and
                reaction.message.id == message.id
            )

        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=20.0, check=check)
        except asyncio.TimeoutError:
            await ctx.send("Timed out! No choice made.")
            await message.delete()
            return

        player_choice = choices[str(reaction.emoji)]
        bot_choice = random.choice(list(choices.values()))
        win_map = {
            "fire": "grass",
            "grass": "water",
            "water": "fire"
        }

        result_msg = f"You chose **{player_choice}**. I chose **{bot_choice}**.\n"
        if player_choice == bot_choice:
            result_msg += "It's a tie! No coins won or lost."
        elif win_map[player_choice] == bot_choice:
            self.add_balance(user_id, amount)
            result_msg += f"You win! 💰 {amount} coins added."
        else:
            self.subtract_balance(user_id, amount)
            result_msg += f"You lose! 💰 {amount} coins lost."

        await ctx.send(result_msg)
        await message.delete()

async def setup(bot):
    await bot.add_cog(Currency(bot))