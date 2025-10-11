import json
import requests
import time

CARDS_FILE = "data/cards.json"
PRICE_URL = "https://waifucards.app/price?id={}"
DELAY = 0.3  # сек между запросами

# Загружаем карточки
with open(CARDS_FILE, "r", encoding="utf-8") as f:
    cards = json.load(f)

for idx, card in enumerate(cards):
    try:
        card_id = card.get("card_id")
        if not card_id:
            print(f"⏭ Пропуск: нет card_id для {card.get('title')}")
            continue

        # Получаем цену с сайта
        resp = requests.get(PRICE_URL.format(card_id))
        if resp.status_code == 200:
            card["price"] = resp.json()
        else:
            print(f"⚠️ Ошибка {resp.status_code} для card_id={card_id}")

        print(f"✅ [{idx+1}/{len(cards)}] {card['title']} — обновлено")

        time.sleep(DELAY)

    except Exception as e:
        print(f"❌ Ошибка при обработке карточки {card.get('title', 'неизвестно')}: {e}")

# Сохраняем обновлённый JSON
with open(CARDS_FILE, "w", encoding="utf-8") as f:
    json.dump(cards, f, ensure_ascii=False, indent=2)

print("\n🎉 Готово. Цены добавлены.")
