import os
import json

# Map each pack to its links file and JSON file
PACKS = {
    "base": ("imgbb_image_links_base.txt", "base.json"),
    "fossil": ("imgbb_image_links_fossil.txt", "fossil.json"),
    "jungle": ("imgbb_image_links_jungle.txt", "jungle.json"),
    "rocket": ("imgbb_image_links_rocket.txt", "rocket.json")
}

CARDS_DIR = os.path.join(os.getcwd(), "data", "cardpacks")

for pack, (links_file, json_file) in PACKS.items():
    json_path = os.path.join(CARDS_DIR, json_file)
    links_path = os.path.join(os.getcwd(), links_file)

    if not os.path.exists(json_path):
        print(f"❌ JSON file not found: {json_path}")
        continue
    if not os.path.exists(links_path):
        print(f"❌ Links file not found: {links_path}")
        continue

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cards = data["cards"]

    with open(links_path, "r", encoding="utf-8") as f:
        links = [line.strip() for line in f if line.strip()]

    if len(cards) != len(links):
        print(f"❌ {pack}: Number of cards ({len(cards)}) does not match number of links ({len(links)})!")
        continue

    for card, link in zip(cards, links):
        card["image_url"] = link

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"✅ {json_file} updated with ImgBB image links!")