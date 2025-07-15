import json
import os
import discord
import urllib.parse

DATA_FOLDER = "data"
os.makedirs(DATA_FOLDER, exist_ok=True)

def get_user_folder(user_id):
    folder = os.path.join(DATA_FOLDER, "user", str(user_id))
    os.makedirs(folder, exist_ok=True)
    return folder

def get_user_file(user_id, filename):
    folder = get_user_folder(user_id)
    return os.path.join(folder, filename)

def load_user_file(user_id, filename):
    path = get_user_file(user_id, filename)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_user_file(user_id, filename, data):
    path = get_user_file(user_id, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def user_packs(user_id):
    packs = load_user_file(user_id, "user_packs.json")
    return packs if packs else []

def save_user_packs(user_id, packs):
    save_user_file(user_id, "user_packs.json", packs)

def load_pack(pack_name: str) -> dict:
    pack_path = os.path.join(DATA_FOLDER, "cardpacks", f"{pack_name}.json")
    if not os.path.exists(pack_path):
        return {}
    with open(pack_path, "r") as f:
        return json.load(f)

def add_cards_to_collection(user_id, cards, pack_name):
    user_id = str(user_id)
    user_cards = load_user_file(user_id, "cards.json").get("cards", [])
    user_dupes = load_user_file(user_id, "duplicates.json").get("duplicates", [])

    # Helper: find card in a list by name/number/pack
    def find_card(card_list, card):
        for c in card_list:
            if (
                c.get("name") == card.get("name")
                and c.get("number") == card.get("number")
                and c.get("pack") == pack_name
            ):
                return c
        return None

    for card in cards:
        card_copy = dict(card)
        card_copy["pack"] = pack_name

        # Check if already in collection
        owned = find_card(user_cards, card_copy)
        if owned:
            # Already owned: add to duplicates
            dupe = find_card(user_dupes, card_copy)
            if dupe:
                dupe["count"] = dupe.get("count", 1) + 1
            else:
                dupe_entry = dict(card_copy)
                dupe_entry["count"] = 1
                user_dupes.append(dupe_entry)
        else:
            user_cards.append(card_copy)

    save_user_file(user_id, "cards.json", {"cards": user_cards})
    save_user_file(user_id, "duplicates.json", {"duplicates": user_dupes})

async def export_image_links(bot, channel_id):
    """
    Export image links for each pack into a separate .txt file.
    Each file will be named discord_image_links_<packname>.txt
    """
    packs_dir = os.path.join(DATA_FOLDER, "cardpacks")
    for filename in os.listdir(packs_dir):
        if filename.endswith(".json"):
            packname = filename[:-5]
            path = os.path.join(packs_dir, filename)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cards = data.get("cards", data)  # support both dict with "cards" or list
            links = []
            for card in cards:
                url = card.get("image_url")
                if url:
                    links.append(url)
            # Write to a separate file for each pack
            out_path = f"discord_image_links_{packname}.txt"
            with open(out_path, "w", encoding="utf-8") as out_f:
                out_f.write("\n".join(links))