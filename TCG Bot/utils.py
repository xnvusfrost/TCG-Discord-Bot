import json
import os

DATA_FOLDER = "data"
BALANCE_FILE = os.path.join(DATA_FOLDER, "balances.json")
PACKS_FILE = os.path.join(DATA_FOLDER, "user_packs.json")

os.makedirs(DATA_FOLDER, exist_ok=True)

def load_json(filename):
    if not os.path.exists(filename):
        with open(filename, "w") as f:
            json.dump({}, f)
    with open(filename, "r") as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)

def get_balance(user_id) -> int:
    user_id = str(user_id)
    balances = load_json(BALANCE_FILE)
    entry = balances.get(user_id, {})
    if isinstance(entry, dict):
        return entry.get("balance", 0)
    return entry  # fallback for old format

def add_balance(user_id, amount: int):
    user_id = str(user_id)
    balances = load_json(BALANCE_FILE)
    entry = balances.get(user_id, {})
    if not isinstance(entry, dict):
        entry = {"balance": entry, "last_daily": None}
    old_balance = entry.get("balance", 0)
    entry["balance"] = old_balance + amount
    balances[user_id] = entry
    save_json(BALANCE_FILE, balances)

def get_last_daily(user_id):
    user_id = str(user_id)
    balances = load_json(BALANCE_FILE)
    entry = balances.get(user_id, {})
    if isinstance(entry, dict):
        return entry.get("last_daily")
    return None

def set_last_daily(user_id, timestamp):
    user_id = str(user_id)
    balances = load_json(BALANCE_FILE)
    entry = balances.get(user_id, {})
    if not isinstance(entry, dict):
        entry = {"balance": entry, "last_daily": None}
    entry["last_daily"] = timestamp
    balances[user_id] = entry
    save_json(BALANCE_FILE, balances)

def user_packs(user_id) -> list:
    user_id = str(user_id)
    packs = load_json(PACKS_FILE)
    return packs.get(user_id, [])

def save_user_packs(user_id, pack_list: list):
    user_id = str(user_id)
    packs = load_json(PACKS_FILE)
    packs[user_id] = pack_list
    save_json(PACKS_FILE, packs)

def load_pack(pack_name: str) -> dict:
    pack_path = os.path.join("data", "cardpacks", f"{pack_name}.json")
    if not os.path.exists(pack_path):
        return {}
    with open(pack_path, "r") as f:
        return json.load(f)

def add_cards_to_collection(user_id, cards, pack_name):
    user_id = str(user_id)
    users_path = os.path.join("data", "users.json")
    duplicates_path = os.path.join("data", "duplicates.json")

    # Load user collection
    if os.path.exists(users_path):
        with open(users_path, "r") as f:
            users = json.load(f)
    else:
        users = {}

    # Load duplicates
    if os.path.exists(duplicates_path):
        with open(duplicates_path, "r") as f:
            duplicates = json.load(f)
    else:
        duplicates = {}

    user_cards = users.get(user_id, [])
    user_dupes = duplicates.get(user_id, [])

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

    users[user_id] = user_cards
    duplicates[user_id] = user_dupes

    with open(users_path, "w") as f:
        json.dump(users, f, indent=4)
    with open(duplicates_path, "w") as f:
        json.dump(duplicates, f, indent=4)