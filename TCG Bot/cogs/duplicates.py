import discord
from discord.ext import commands
import math
import json
import os
import asyncio
from typing import Optional

class Duplicates(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.duplicates_file = "data/duplicates.json"
        self.load_duplicates()

    def load_duplicates(self):
        if os.path.exists(self.duplicates_file):
            with open(self.duplicates_file, "r") as f:
                self.duplicates = json.load(f)
        else:
            self.duplicates = {}

    def reload_duplicates(self):
        self.load_duplicates()

    @commands.command(name="dup", aliases=["dupes", "duplicates"])
    async def show_duplicates(self, ctx, pack_name: Optional[str] = None):
        self.reload_duplicates()
        user_id = str(ctx.author.id)
        if user_id not in self.duplicates or not self.duplicates[user_id]:
            return await ctx.send(f"{ctx.author.mention}, you don't have any duplicate cards in your binder.")

        # Group duplicates by pack
        pack_groups = {}
        for card in self.duplicates[user_id]:
            pack = (card.get("pack") or "unknown").lower()
            pack_groups.setdefault(pack, []).append(card)

        # If a pack name is given, show only that pack
        if pack_name:
            pack_name_lower = pack_name.lower()
            if pack_name_lower not in pack_groups:
                return await ctx.send(f"{ctx.author.mention}, you have no duplicates in the `{pack_name}` pack.")
            packs_to_show = [(pack_name_lower, pack_groups[pack_name_lower])]
        else:
            # Show all packs, sorted by pack name
            packs_to_show = sorted(pack_groups.items())

        current_pack_index = 0
        current_page = 0

        def format_embed(pack_idx, page_idx):
            pack, cards = packs_to_show[pack_idx]
            cards = sorted(cards, key=lambda c: c.get("name", ""))
            cards_per_page = 20
            total_pages = max(1, (len(cards) + cards_per_page - 1) // cards_per_page)
            start = page_idx * cards_per_page
            end = start + cards_per_page
            page_cards = cards[start:end]

            row_size = 10
            cell_width = 18
            rows = [page_cards[i:i + row_size] for i in range(0, len(page_cards), row_size)]
            while len(rows) < 2:
                rows.append([])

            grid_lines = []
            for row in rows[:2]:
                line = ""
                for card in row:
                    name = card.get("name", "Unknown")
                    count = card.get("count", 1)
                    count_str = f"({count})"
                    max_name_len = cell_width - len(count_str) - 1
                    if len(name) > max_name_len:
                        name = name[:max_name_len - 3] + "..."
                    entry = f"{name} {count_str}"
                    entry = entry.ljust(cell_width)
                    line += entry + "|"
                for _ in range(row_size - len(row)):
                    line += " " * cell_width + "|"
                grid_lines.append(line)

            code_block = "```\n" + "\n".join(grid_lines) + "\n```"
            embed = discord.Embed(
                title=f"{ctx.author.display_name}'s Duplicates - {pack.title()} Pack",
                description=code_block,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"Pack: {pack.title()} • Page {page_idx + 1}/{total_pages} • Pack {pack_idx + 1}/{len(packs_to_show)}")
            return embed, total_pages

        embed, total_pages = format_embed(current_pack_index, current_page)
        message = await ctx.send(embed=embed)

        # Add navigation if needed
        if len(packs_to_show) > 1 or total_pages > 1:
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")
            await message.add_reaction("🔁")  # Switch pack

            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️", "🔁"] and reaction.message.id == message.id

            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)

                    if str(reaction.emoji) == "➡️":
                        if current_page < format_embed(current_pack_index, 0)[1] - 1:
                            current_page += 1
                        elif len(packs_to_show) > 1:
                            # Next pack
                            current_pack_index = (current_pack_index + 1) % len(packs_to_show)
                            current_page = 0
                        else:
                            await message.remove_reaction(reaction, user)
                            continue
                    elif str(reaction.emoji) == "⬅️":
                        if current_page > 0:
                            current_page -= 1
                        elif len(packs_to_show) > 1:
                            # Previous pack
                            current_pack_index = (current_pack_index - 1) % len(packs_to_show)
                            current_page = 0
                        else:
                            await message.remove_reaction(reaction, user)
                            continue
                    elif str(reaction.emoji) == "🔁" and len(packs_to_show) > 1:
                        # Switch pack
                        current_pack_index = (current_pack_index + 1) % len(packs_to_show)
                        current_page = 0

                    embed, total_pages = format_embed(current_pack_index, current_page)
                    await message.edit(embed=embed)
                    try:
                        await message.remove_reaction(reaction, user)
                    except discord.Forbidden:
                        pass

                except asyncio.TimeoutError:
                    try:
                        await message.clear_reactions()
                    except discord.Forbidden:
                        pass
                    break

async def setup(bot):
    await bot.add_cog(Duplicates(bot))