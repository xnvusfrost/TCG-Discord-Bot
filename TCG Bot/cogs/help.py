import discord
from discord.ext import commands
from utils import get_balance, add_balance, user_packs, save_user_packs, load_pack


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
            name="`!dup <pack_name>`, `!dupes <pack_name>`, `!duplicates <pack_name>`, `!d <pack_name>`",
            value="Shows you how many duplicate cards you have in a pack. Example: `!dup base`",
            inline=False
        )
        embed.add_field(
            name="`!op <pack_name>`",
            value="Open a booster pack to collect cards.",
            inline=False
        )
        embed.add_field(
            name="`!shop`",
            value="Shows you what packs you can buy.",
            inline=False
        )
        embed.add_field(
            name="`!daily`",
            value="Allows you to get paid every 24 hours.",
            inline=False
        )
        embed.add_field(
            name="`!bal`",
            value="Shows you how much money you have.",
            inline=False
        )
        embed.add_field(
            name="`!flip <heads/tails> <bet_amount>`",
            value="Flip a coin and bet on the outcome.",
            inline=False
        )
        embed.add_field(
            name="`!fwg <bet_amount>`",
            value="Play Fire Water Grass for a chance to win coins.",
            inline=False
        )
        embed.set_footer(text="Use commands without <> or [] symbols.")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
    
