import discord
from discord.ext import commands
import os
import json
import asyncio
import aiohttp
import io
from PIL import Image
from typing import Optional

# Global session tracker for binder sessions
binder_sessions = {} 

class Binder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.users = {}
        self.duplicates = {}
        self.load_data()

    def load_data(self):
        self.users = self.load_json("data/users.json", {})
        self.duplicates = self.load_json("data/duplicates.json", {})

    def load_json(self, filename, default):
        if os.path.exists(filename):
            try:
                with open(filename, "r") as f:
                    text = f.read().strip()
                    if not text:
                        return default
                    return json.loads(text)
            except json.JSONDecodeError:
                print(f"[load_json] invalid JSON in {filename!r}")
                return default
        return default

    def load_pack(self, pack_name):
        path = os.path.join("data/cardpacks", f"{pack_name}.json")
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r") as f:
                text = f.read().strip()
                if not text:
                    return {}
                return json.loads(text)
        except json.JSONDecodeError:
            print(f"[load_pack] invalid JSON in {path!r}")
            return {}

    @commands.command(name="binder")
    async def binder_cmd(self, ctx, pack_name: Optional[str] = None):
        self.load_data()  # <-- Add this line to refresh user data
        valid = [f[:-5] for f in os.listdir("data/cardpacks") if f.endswith('.json')]
        if not pack_name:
            return await ctx.send(f"Please specify a pack: {', '.join(valid)}")
        if pack_name.lower() not in valid:
            return await ctx.send(f"Invalid pack. Available: {', '.join(valid)}")
        pdata = self.load_pack(pack_name.lower())
        if not pdata:
            return await ctx.send(f"Pack {pack_name} empty or invalid.")
        session = BinderSession(ctx, [(pack_name.lower(), pdata)], self.users, self.duplicates)
        await session.start()

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # Route reactions to the correct binder session
        if user.bot:
            return
        session = binder_sessions.get(str(user.id))
        if session and reaction.message.id == session.message.id:
            await session.handle_reaction(reaction, user)
            # Clean up session if message is deleted
            if session.message is None or not session.message.guild:
                binder_sessions.pop(str(user.id), None)

class BinderSession:
    def __init__(self, ctx, packs, users, duplicates=None):
        self.ctx = ctx
        self.user_id = str(ctx.author.id)
        self.packs = packs
        self.users = users
        self.duplicates = duplicates or {}
        self.current_pack_index = 0
        self.current_page = 1
        self.viewing_duplicates = False
        self.message = None
        self.lock = asyncio.Lock()

    async def generate_grid(self):
        pack_name, pack_data = self.packs[self.current_pack_index]
        all_cards = pack_data.get("cards", []) if isinstance(pack_data, dict) else pack_data

        owned = set()  # Always define owned
        if self.viewing_duplicates:
            user_dupes = self.duplicates.get(self.user_id, [])
            cards = [c for c in user_dupes if c.get("pack") == pack_name]
            if not cards:
                return None, "You don't have any duplicate cards in this pack."
        else:
            user_cards = self.users.get(self.user_id, [])
            cards = all_cards
            owned = set(
                (c.get("name"), c.get("number"), c.get("code"))
                for c in user_cards if c.get("pack") == pack_name
            )
            if not cards:
                return None, "No cards found in this pack."

        try:
            cards = sorted(cards, key=lambda c: int(c.get("number", 0)))
        except Exception:
            cards = sorted(cards, key=lambda c: c.get("number", ""))

        per_page = 12
        total_pages = max(1, (len(cards) + per_page - 1) // per_page)
        self.current_page = max(1, min(self.current_page, total_pages))
        start = (self.current_page - 1) * per_page
        page_cards = cards[start:start + per_page]

        imgs = []
        async with aiohttp.ClientSession() as session:
            pack_img = None
            pack_img_url = pack_data.get("pack_image_url") if isinstance(pack_data, dict) else None
            if pack_img_url and not self.viewing_duplicates:
                try:
                    resp = await session.get(pack_img_url)
                    if resp.status == 200:
                        pack_img = Image.open(io.BytesIO(await resp.read())).convert("RGBA")
                except Exception:
                    pack_img = None

            for card in page_cards:
                if not self.viewing_duplicates:
                    is_owned = (card.get("name"), card.get("number"), card.get("code")) in owned
                else:
                    is_owned = True

                url = card.get("image_url") if self.viewing_duplicates or is_owned else None
                img = None
                if url:
                    try:
                        resp = await session.get(url)
                        if resp.status == 200:
                            img = Image.open(io.BytesIO(await resp.read())).convert("RGBA")
                    except Exception:
                        img = None
                if img is None:
                    img = pack_img.copy() if pack_img else Image.new("RGBA", (180, 240), (100, 100, 100, 255))
                imgs.append(img)

        # Always fill the grid with placeholders for missing cards
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

        view_mode = "Duplicates" if self.viewing_duplicates else "Main Binder"
        footer = (f"{view_mode} - Pack: {pack_name.title()} | "
                  f"Page {self.current_page}/{total_pages} | "
                  f"Pack {self.current_pack_index + 1}/{len(self.packs)}")
        return file, footer

    async def start(self):
        async with self.lock:
            file, footer = await self.generate_grid()
            if not file:
                self.message = await self.ctx.send(footer)
                for em in ("◀️", "▶️", "🔁"):
                    await self.message.add_reaction(em)
                binder_sessions[self.user_id] = self
                return
            self.message = await self.ctx.send(file=file, content=footer)
            for em in ("◀️", "▶️", "🔁"):
                await self.message.add_reaction(em)
            binder_sessions[self.user_id] = self

    async def handle_reaction(self, reaction, user):
        if user.bot or str(user.id) != self.user_id or not self.message or reaction.message.id != self.message.id:
            return
        async with self.lock:
            try:
                if self.message:
                    await self.message.remove_reaction(reaction.emoji, user)
            except (discord.NotFound, discord.Forbidden, AttributeError):
                pass

            pack_name, pack_data = self.packs[self.current_pack_index]

            if self.viewing_duplicates:
                user_dupes = self.duplicates.get(self.user_id, [])
                cards = [c for c in user_dupes if c.get("pack") == pack_name]
            else:
                cards = pack_data.get("cards", []) if isinstance(pack_data, dict) else pack_data

            total_pages = max(1, (len(cards) + 11) // 12)

            if reaction.emoji == "▶️":
                if self.current_page < total_pages:
                    self.current_page += 1
                else:
                    self.current_pack_index = (self.current_pack_index + 1) % len(self.packs)
                    self.current_page = 1
            elif reaction.emoji == "◀️":
                if self.current_page > 1:
                    self.current_page -= 1
                else:
                    self.current_pack_index = (self.current_pack_index - 1) % len(self.packs)
                    prev_pack_name, prev_pack_data = self.packs[self.current_pack_index]
                    if self.viewing_duplicates:
                        user_dupes = self.duplicates.get(self.user_id, [])
                        prev_cards = [c for c in user_dupes if c.get("pack") == prev_pack_name]
                    else:
                        prev_cards = (prev_pack_data.get("cards", []) if isinstance(prev_pack_data, dict)
                                      else prev_pack_data)
                    self.current_page = max(1, (len(prev_cards) + 11) // 12)
            elif reaction.emoji == "🔁":
                self.viewing_duplicates = not self.viewing_duplicates
                self.current_page = 1
                self.current_pack_index = 0

            try:
                if self.message:
                    await self.message.delete()
            except (discord.NotFound, AttributeError):
                pass

            file, footer = await self.generate_grid()
            if not file:
                self.message = await self.ctx.send(footer)
                for em in ("◀️", "▶️", "🔁"):
                    await self.message.add_reaction(em)
                return

            self.message = await self.ctx.send(file=file, content=footer)
            for em in ("◀️", "▶️", "🔁"):
                await self.message.add_reaction(em)

# Required for async cog loading in discord.py v2.x
async def setup(bot):
    await bot.add_cog(Binder(bot))

