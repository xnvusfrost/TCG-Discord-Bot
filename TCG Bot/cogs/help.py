import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="tcghelp")
    async def help_command(self, ctx):
        embed = discord.Embed(
            title="📘 Help - List of Commands",
            description="Here's a list of commands you can use:",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="`!binder <pack_name>`",
            value="View your card collection by pack and page.\nExample: `!binder base`",
            inline=False
        )
        embed.add_field(
            name="`!op <pack_name> [amount]`",
            value="Open 1-5 booster packs to collect cards. Example: `!op base 3`",
            inline=False
        )
        embed.add_field(
            name="`!shop`",
            value="Shows what packs you can buy.",
            inline=False
        )
        embed.add_field(
            name="`!give @user <amount>`",
            value="Give coins to another user. Example: `!give @Ash 100`",
            inline=False
        )
        embed.add_field(
            name="`!daily`",
            value="Claim your daily reward (every 24 hours).",
            inline=False
        )
        embed.add_field(
            name="`!bal`",
            value="Shows how much money you have.",
            inline=False
        )
        embed.add_field(
            name="`!flip <heads/tails> <bet_amount>`",
            value="Flip a coin and bet on the outcome. Example: `!flip heads 100`",
            inline=False
        )
        embed.add_field(
            name="`!fwg <bet_amount>`",
            value="Play Fire Water Grass for a chance to win coins. Example: `!fwg 100`",
            inline=False
        )
        embed.add_field(
            name="`!wonderpick`, `!wp`",
            value="Randomly pick 1 of 5 cards to add to your binder.",
            inline=False
        )
        embed.add_field(
            name="`!wonderenergy`, `!we`",
            value="Shows your Wonderpack Energy and next recharge time.",
            inline=False
        )
        embed.add_field(
            name="`!packenergy`, `!pe`",
            value="Shows your Pack Energy and next recharge time.",
            inline=False
        )
        embed.add_field(
            name="`!freepack <pack_name>`, `!fp <pack_name>`",
            value="Use 1 Pack Energy to get a free pack (not valid for booster boxes).",
            inline=False
        )
        embed.add_field(
            name="`!trade @user <your_card> for <their_card>`",
            value="Trade cards with another user. Example: `!trade @Ash base.001.alakazam for base.004.charizard`",
            inline=False
        )
        embed.set_footer(text="Use commands without <> or [] symbols. [] means optional, <> means required.")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
    
