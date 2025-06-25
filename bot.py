# bot.py
import os
import json
import faiss
import torch
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, ContextTypes, filters
from transformers import CLIPProcessor, CLIPModel
from urllib.parse import quote
from yolo_detector import detect_card_yolo
from PIL import ImageOps
from dotenv import load_dotenv
load_dotenv()

token = os.getenv("TELEGRAM_TOKEN")

def preprocess_card(card_img: Image.Image) -> Image.Image:
    card_img = card_img.convert("RGB")
    # Центрированное масштабирование до 224x224
    return ImageOps.fit(card_img, (224, 224), Image.BICUBIC, centering=(0.5, 0.5))


# --- Обработка команды /start ---
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот, который распознаёт карточки с сайта [waifucards.app](https://waifucards.app) по фото.\n\n"
        "Просто пришли мне изображение карточки, и я постараюсь найти самые похожие 🎴",
        parse_mode="Markdown"
    )

# --- Настройка модели CLIP ---
device = "cuda" if torch.cuda.is_available() else "cpu"
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32", use_fast=True)

# --- Загрузка индекса ---
DATA = np.load("data/clip_index.npz", allow_pickle=True)
index_vectors = DATA["vectors"]
cards = list(DATA["meta"])

# --- Настройка FAISS ---
dimension = index_vectors.shape[1]
index = faiss.IndexFlatIP(dimension)
index.add(index_vectors)


# --- Поиск топ-N ---
def find_top_matches(image: Image.Image, top_k: int = 3):
    image = preprocess_card(image)
    inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        features = clip_model.get_image_features(**inputs)
    query = features[0].cpu().numpy()
    query = query / np.linalg.norm(query)  # Нормализация
    distances, indices = index.search(query.reshape(1, -1), k=top_k)
    results = [(cards[i], float(distances[0][rank])) for rank, i in enumerate(indices[0])]
    return results


# --- Обработка фото ---
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()
    image_bytes = await file.download_as_bytearray()
    img = Image.open(BytesIO(image_bytes)).convert("RGB")

    cropped_img = detect_card_yolo(img)  # одно изображение, а не список
    if cropped_img is None:
        await update.message.reply_text("❌ Не найдено карточек.")
        return

    with BytesIO() as output:
        cropped_img.save(output, format="PNG")
        output.seek(0)
        await update.message.reply_photo(
            photo=output,
            caption="🔍 Вот что я вырезал с фото:"
        )

    matches = find_top_matches(cropped_img, top_k=3)
    threshold = 0.80  # было 0.20


    found = False
    for idx, (card, score) in enumerate(matches):
        if score < threshold:
            continue
        found = True
        caption = (
            f"{idx + 1}⃣ *{card['title']}*\n"
            f"📦 Set: `{card['set']}`\n"
            f"🌟 Rarity: `{card['rarity']}`\n"
            f"🔗 [Открыть на сайте](https://waifucards.app/set/{card['set']}?character={quote(card['title'])}&rarity={card['rarity']}&items=120)\n"
            f"📈 Совпадение: `{round(score * 100, 2)}%`"
        )
        image_path = os.path.join("cards", card["image"])
        if os.path.exists(image_path):
            await update.message.reply_photo(
                photo=open(image_path, "rb"),
                caption=caption,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(caption, parse_mode="Markdown")

    if not found:
        await update.message.reply_text("❌ Не удалось точно распознать карту. Попробуй другое фото.")

# --- Запуск бота ---
async def main():
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("✅ Бот запущен.")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    import nest_asyncio

    nest_asyncio.apply()
    asyncio.run(main())
