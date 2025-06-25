# matcher.py
import os
import json
import imagehash
from PIL import Image, ImageChops

HASH_FILE = "data/hashes.json"
DATA_FILE = "data/cards.json"
IMAGE_DIR = "cards"

def crop_borders(image):
    bg = Image.new(image.mode, image.size, image.getpixel((0, 0)))
    diff = ImageChops.difference(image, bg)
    bbox = diff.getbbox()
    if bbox:
        return image.crop(bbox)
    return image

with open(DATA_FILE, "r", encoding="utf-8") as f:
    cards = json.load(f)

hashes = []

for card in cards:
    image_path = os.path.join(IMAGE_DIR, card["image"])
    if not os.path.exists(image_path):
        continue
    try:
        img = Image.open(image_path).convert("RGB")
        img = crop_borders(img)
        hash_val = str(imagehash.phash(img, hash_size=16))  # ← увеличенный хеш
        card["hash"] = hash_val
        hashes.append(card)
    except Exception as e:
        print(f"❌ {card['image']}: {e}")

with open(HASH_FILE, "w", encoding="utf-8") as f:
    json.dump(hashes, f, ensure_ascii=False, indent=2)

print("✅ Хеши обновлены:", len(hashes))
