import os, json, hashlib, requests
from PIL import Image
from io import BytesIO

def cache_image(url):
    cache_dir = "image_cache"
    os.makedirs(cache_dir, exist_ok=True)
    url_hash = hashlib.md5(url.encode()).hexdigest()
    cache_path = os.path.join(cache_dir, f"{url_hash}.png")
    if os.path.exists(cache_path):
        return
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content)).convert("RGBA")
            img.save(cache_path)
            print(f"Cached: {url}")
    except Exception as e:
        print(f"Failed: {url} ({e})")

packs_dir = "data/cardpacks"
for fname in os.listdir(packs_dir):
    if fname.endswith(".json"):
        with open(os.path.join(packs_dir, fname), encoding="utf-8") as f:
            data = json.load(f)
        cards = data["cards"] if isinstance(data, dict) else data
        for card in cards:
            url = card.get("image_url")
            if url and (url.startswith("http://") or url.startswith("https://")):
                cache_image(url)
print("Done pre-caching.")