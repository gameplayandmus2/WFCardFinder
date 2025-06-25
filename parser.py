# parser.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import os, json, time, requests
from urllib.parse import urljoin
import hashlib
import os

def get_unique_filename(image_url):
    url_hash = hashlib.md5(image_url.encode("utf-8")).hexdigest()
    ext = os.path.splitext(image_url)[1]
    return f"{url_hash}{ext}"



BASE_URL = "https://waifucards.app/cards?items=120&page={}"
IMAGE_DIR = "cards"
DATA_FILE = "data/cards.json"

os.makedirs("cards", exist_ok=True)
os.makedirs("data", exist_ok=True)

options = Options()
options.add_argument("--headless=new")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

all_cards = []

for page in range(1, 131):
    print(f"Открываем страницу {page}")
    driver.get(BASE_URL.format(page))
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    cards = soup.select("div.card-box")

    print(f"  🔍 Найдено {len(cards)} карточек")

    for card in cards:
        img_tag = card.select_one("img.card-img")
        name_tag = card.select_one("a.card-info-name")
        set_tag = card.select_one("a.card-info-set")
        rarity_tag = card.select_one("a.card-info-rarity span")

        if not img_tag or not name_tag:
            continue

        image_url = urljoin("https://waifucards.app", img_tag["src"])
        filename = get_unique_filename(image_url)
        local_path = os.path.join(IMAGE_DIR, filename)

        if not os.path.exists(local_path):
            try:
                img_data = requests.get(image_url).content
                with open(local_path, "wb") as f:
                    f.write(img_data)
            except Exception as e:
                print("❌ Ошибка скачивания:", image_url, e)
                continue

        card_data = {
            "title": name_tag.text.strip(),
            "set": set_tag.text.strip() if set_tag else "",
            "rarity": rarity_tag.text.strip() if rarity_tag else "",
            "image": filename,
            "url": image_url
        }
        all_cards.append(card_data)

    print(f"✅ Страница {page} обработана")

with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(all_cards, f, ensure_ascii=False, indent=2)

print(f"🎉 Готово. Скачано карт: {len(all_cards)}")
driver.quit()
