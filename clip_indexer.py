# clip_indexer.py
import os
import json
import torch
import numpy as np
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from tqdm import tqdm

DATA_FILE = "data/cards.json"
IMAGE_DIR = "cards"
INDEX_FILE = "data/clip_index.npz"

device = "cuda" if torch.cuda.is_available() else "cpu"
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

with open(DATA_FILE, "r", encoding="utf-8") as f:
    cards = json.load(f)

embeddings = []
metainfo = []

for card in tqdm(cards, desc="🔍 Генерация эмбеддингов"):
    img_path = os.path.join(IMAGE_DIR, card["image"])
    if not os.path.exists(img_path):
        continue
    try:
        image = Image.open(img_path).convert("RGB")
        inputs = processor(images=image, return_tensors="pt").to(device)
        with torch.no_grad():
            features = model.get_image_features(**inputs)
        embedding = features[0].cpu().numpy()
        embeddings.append(embedding)
        metainfo.append(card)
    except Exception as e:
        print(f"❌ Ошибка: {card['image']} — {e}")

# после получения списка embeddings, например:
embeddings = [emb / np.linalg.norm(emb) for emb in embeddings]

# затем сохрани
np.savez_compressed(INDEX_FILE, vectors=np.stack(embeddings), meta=metainfo)
print(f"✅ Сохранено: {len(embeddings)} эмбеддингов в {INDEX_FILE}")
