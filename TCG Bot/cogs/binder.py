import discord
from discord.ext import commands
import os
import json
from typing import Optional
import aiohttp
from PIL import Image, ImageOps, UnidentifiedImageError, ImageDraw, ImageFont
import io
import re
import math
import asyncio
import hashlib
from utils import load_user_file

def load_json(filename, default):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                text = f.read().strip()
                if not text:
                    return default
                return json.loads(text)
        except json.JSONDecodeError:
            print(f"[load_json] invalid JSON in {filename!r}")
            return default
    return default

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_pack_cards(pack):
    # Allow only alphanumeric, dash, and underscore in pack names
    if not re.fullmatch(r"[a-z0-9_-]+", pack.lower()):
        return []
    safe_pack = pack.lower()
    safe_dir = os.path.abspath("data/cardpacks")
    path = os.path.abspath(os.path.join(safe_dir, f"{safe_pack}.json"))
    # Ensure the path is within the intended directory
    if not os.path.commonpath([path, safe_dir]) == safe_dir:
        return []
    if not os.path.exists(path):
        return []
    data = load_json(path, {})
    if isinstance(data, dict) and "cards" in data:
        return data["cards"]
    if isinstance(data, list):
        return data
    return []

class Binder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="packbinder")
    async def pack_binder(self, ctx, pack: Optional[str] = None, page: int = 1):
        """Show all cards in a pack as a grid. Owned cards are in color, unowned are shadowed. Shows count for each card."""
        if not pack:
            packs = [f[:-5] for f in os.listdir("data/cardpacks") if f.endswith(".json")]
            return await ctx.send(f"Please specify a pack: {', '.join(sorted(packs))}")
        pack = pack.lower()
        all_cards = load_pack_cards(pack)
        print(f"[DEBUG] Loaded {len(all_cards)} cards from pack '{pack}'")
        if not all_cards:
            return await ctx.send(f"No such pack `{pack}` or pack has no cards.")
        user_id = str(ctx.author.id)
        # Load user's cards and duplicates from new user file storage
        user_cards_data = load_user_file(user_id, "cards.json")
        user_cards = user_cards_data.get("cards", [])
        user_dupes_data = load_user_file(user_id, "duplicates.json")
        user_dupes = user_dupes_data.get("duplicates", [])

        # Build a count dict: (name, number, pack) -> count
        card_counts = {}
        for c in user_cards:
            key = (c.get("name","").lower(), str(c.get("number","")), (c.get("pack") or pack).lower())
            card_counts[key] = 1
        for d in user_dupes:
            key = (d.get("name","").lower(), str(d.get("number","")), (d.get("pack") or pack).lower())
            card_counts[key] = card_counts.get(key, 1) + d.get("count", 1)

        per_page = 12
        total_pages = max(1, math.ceil(len(all_cards) / per_page))
        page = max(1, min(page, total_pages))

        async def fetch_image(session, url, cardname):
            cache_dir = "image_cache"
            os.makedirs(cache_dir, exist_ok=True)
            if url and (url.startswith("http://") or url.startswith("https://")):
                url_hash = hashlib.md5(url.encode()).hexdigest()
                cache_path = os.path.join(cache_dir, f"{url_hash}.png")
                if os.path.exists(cache_path):
                    try:
                        return Image.open(cache_path).convert("RGBA")
                    except Exception as e:
                        print(f"[DEBUG] Failed to load cached image for {cardname}: {e}")
                        return None
                # If not cached, download and cache (should be rare if you pre-cache)
                try:
                    headers = {"User-Agent": "Mozilla/5.0"}
                    async with session.get(url, headers=headers) as resp:
                        if resp.status == 200:
                            img_bytes = await resp.read()
                            img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
                            img.save(cache_path)
                            return img
                except Exception as e:
                    print(f"[DEBUG] Exception fetching image for {cardname}: {e}")
                    return None
            elif url and os.path.isfile(url):
                try:
                    return Image.open(url).convert("RGBA")
                except Exception as e:
                    print(f"[DEBUG] Failed to load local image for {cardname}: {e}")
                    return None
            return None

        async def make_embed(page):
            start = (page - 1) * per_page
            page_cards = all_cards[start:start+per_page]
            imgs = []
            async with aiohttp.ClientSession() as session:
                tasks = []
                for card in page_cards:
                    url = card.get("image_url")
                    tasks.append(fetch_image(session, url, card.get("name", "?")) if url else None)
                results = await asyncio.gather(*[t if t else asyncio.sleep(0, result=None) for t in tasks])
                for idx, card in enumerate(page_cards):
                    key = (card.get("name","").lower(), str(card.get("number","")), pack)
                    img = results[idx]
                    if img is None:
                        print(f"[DEBUG] Using placeholder for {card.get('name')}")
                        img = Image.new("RGBA", (180, 240), (100, 100, 100, 255))
                    count = card_counts.get(key, 0)
                    overlay = Image.new("RGBA", img.size, (0,0,0,0))
                    draw = ImageDraw.Draw(overlay)
                    # --- Draw card number in top left with hashtag ---
                    card_number = f"#{card.get('number', '?')}"
                    try:
                        font_number = ImageFont.truetype("arial.ttf", 40)
                    except Exception:
                        font_number = ImageFont.load_default()
                    num_bbox = draw.textbbox((0, 0), card_number, font=font_number)
                    num_w = num_bbox[2] - num_bbox[0]
                    num_h = num_bbox[3] - num_bbox[1]
                    num_rect_x0 = 8
                    num_rect_y0 = 8
                    num_rect_x1 = num_rect_x0 + num_w + 16
                    num_rect_y1 = num_rect_y0 + num_h + 8
                    draw.rectangle([num_rect_x0, num_rect_y0, num_rect_x1, num_rect_y1], fill=(0,0,0,180))
                    draw.text((num_rect_x0 + 8, num_rect_y0 + 4), card_number, font=font_number, fill=(255,0,0,255))
                    # --- Draw duplicate count in bottom right if more than 1 ---
                    if count > 1:
                        try:
                            font_dup = ImageFont.truetype("arial.ttf", 40)
                        except Exception:
                            font_dup = ImageFont.load_default()
                        dup_text = f"x{count}"
                        dup_bbox = draw.textbbox((0, 0), dup_text, font=font_dup)
                        dup_w = dup_bbox[2] - dup_bbox[0]
                        dup_h = dup_bbox[3] - dup_bbox[1]
                        dup_rect_x1 = img.width - 8
                        dup_rect_y1 = img.height - 8
                        dup_rect_x0 = dup_rect_x1 - dup_w - 16
                        dup_rect_y0 = dup_rect_y1 - dup_h - 8
                        draw.rectangle([dup_rect_x0, dup_rect_y0, dup_rect_x1, dup_rect_y1], fill=(0,0,0,180))
                        draw.text((dup_rect_x0 + 8, dup_rect_y0 + 4), dup_text, font=font_dup, fill=(255,0,0,255))
                    img = Image.alpha_composite(img, overlay)
                    if count == 0:
                        shadow = Image.new("RGBA", img.size, (0, 0, 0, 120))
                        img = img.convert("RGBA")
                        img = Image.blend(img, shadow, 0.6)
                    imgs.append(img)
            while len(imgs) < per_page:
                imgs.append(Image.new("RGBA", (180, 240), (100, 100, 100, 255)))
            cols, rows = 4, 3
            cw, ch = 180, 240
            grid = Image.new("RGBA", (cols * cw, rows * ch), (0, 0, 0, 0))
            for idx, img in enumerate(imgs):
                r, c = divmod(idx, cols)
                x, y = c * cw, r * ch
                resized = img.resize((cw, ch))
                grid.paste(resized, (x, y), resized)
            buf = io.BytesIO()
            grid.save(buf, "PNG")
            buf.seek(0)
            file = discord.File(buf, filename="binder.png")
            embed = discord.Embed(
                title=f"{ctx.author.display_name}'s {pack.title()} Pack Binder (Page {page}/{total_pages})",
                color=discord.Color.blue()
            )
            embed.set_image(url="attachment://binder.png")
            return embed, file

        embed, file = await make_embed(page)
        message = await ctx.send(embed=embed, file=file)
        if total_pages > 1:
            await message.add_reaction("◀️")
            await message.add_reaction("▶️")

            def check(reaction, user):
                return (
                    user == ctx.author
                    and reaction.message.id == message.id
                    and str(reaction.emoji) in ["◀️", "▶️"]
                )

            current_page = page
            while True:
                try:
                    reaction, user = await ctx.bot.wait_for("reaction_add", timeout=60.0, check=check)
                    if str(reaction.emoji) == "▶️" and current_page < total_pages:
                        current_page += 1
                    elif str(reaction.emoji) == "◀️" and current_page > 1:
                        current_page -= 1
                    else:
                        await message.remove_reaction(reaction, user)
                        continue
                    await message.remove_reaction(reaction, user)
                    new_embed, new_file = await make_embed(current_page)
                    await message.edit(embed=new_embed, attachments=[new_file])
                except asyncio.TimeoutError:
                    try:
                        await message.clear_reactions()
                    except Exception:
                        pass
                    break

async def setup(bot):
    await bot.add_cog(Binder(bot))