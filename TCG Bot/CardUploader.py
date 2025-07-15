import os
import requests
import base64
import json

IMGBB_API_KEY = "99278c73dc235c2a284509c289cc45cd"  # <-- Replace with your ImgBB API key

# Map each pack to its image folder, output txt, and JSON file
PACKS = {
    "base": ("base_images", "imgbb_image_links_base.txt", "base.json"),
    "fossil": ("fossil_images", "imgbb_image_links_fossil.txt", "fossil.json"),
    "jungle": ("jungle_images", "imgbb_image_links_jungle.txt", "jungle.json"),
    "rocket": ("rocket_images", "imgbb_image_links_rocket.txt", "rocket.json")
}

CARDS_DIR = os.path.join(os.getcwd(), "data", "cardpacks")

def upload_image_to_imgbb(image_path):
    with open(image_path, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode("utf-8")
    response = requests.post(
        "https://api.imgbb.com/1/upload",
        data={
            "key": IMGBB_API_KEY,
            "image": encoded_string
        }
    )
    if response.status_code == 200:
        return response.json()["data"]["url"]
    else:
        print(f"Failed to upload {image_path}: {response.text}")
        return None

for pack, (folder, out_txt, json_file) in PACKS.items():
    links = []
    if not os.path.isdir(folder):
        print(f"❌ Folder not found: {folder}")
        continue
    # Upload images and collect links
    for filename in sorted(os.listdir(folder)):
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
            path = os.path.join(folder, filename)
            print(f"[{pack}] Uploading {filename}...")
            link = upload_image_to_imgbb(path)
            if link:
                links.append(link)
    # Save links to .txt
    with open(out_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(links))
    print(f"✅ Saved {len(links)} links to {out_txt}")

    # Update JSON with image links
    json_path = os.path.join(CARDS_DIR, json_file)
    if not os.path.exists(json_path):
        print(f"❌ JSON file not found: {json_path}")
        continue
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    cards = data["cards"]
    if len(cards) != len(links):
        print(f"❌ {pack}: Number of cards ({len(cards)}) does not match number of links ({len(links)})!")
        continue
    for card, link in zip(cards, links):
        card["image_url"] = link
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"✅ {json_file} updated with ImgBB image links!")