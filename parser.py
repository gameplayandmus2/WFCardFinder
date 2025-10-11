import os
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import hashlib

BASE_URL = "https://waifucards.app/cards?items=120&page={}#cards-box"
OUTPUT_JSON = "data/cards.json"
IMAGES_DIR = "cards"

os.makedirs("cards", exist_ok=True)
os.makedirs("data", exist_ok=True)

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)

all_cards = []

def get_unique_filename(image_url):
    url_hash = hashlib.md5(image_url.encode("utf-8")).hexdigest()
    ext = os.path.splitext(image_url)[1]
    return f"{url_hash}{ext}"

driver.set_page_load_timeout(30)

for page in range(1, 110):
    print(f"📖 Открываем страницу {page}")
    driver.get(BASE_URL.format(page))

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.card-box"))
        )
    except:
        print(f"⚠️ Страница {page} не загрузилась, пропускаем")
        continue

    soup = BeautifulSoup(driver.page_source, "html.parser")
    cards = soup.select("div.card-box")
    print(f"  🔍 Найдено {len(cards)} карточек")

    for card in cards:
        try:
            img_tag = card.select_one("img.card-img")
            name_tag = card.select_one("a.card-info-name")
            series_tag = card.select_one("a.card-info-series")
            set_tag = card.select_one("a.card-info-set")
            rarity_tag = card.select_one("a.card-info-rarity span")
            info_btn = card.select_one('div.card_handlers_btn.info b')
            card_id_tag = info_btn.text.strip() if info_btn else None

            raw_image_url = urljoin("https://waifucards.app", img_tag["src"])
            image_url = raw_image_url.replace("(censored)", "")
            filename = get_unique_filename(image_url)

            image_path = os.path.join(IMAGES_DIR, filename)

            if not os.path.exists(image_path):
                try:
                    img_data = requests.get(image_url, timeout=10).content
                    with open(image_path, "wb") as f:
                        f.write(img_data)
                except Exception as e:
                    print(f"⚠️ Ошибка скачивания {image_url}: {e}")
                    continue

            card_data = {
                "title": name_tag.text.strip() if name_tag else "",
                "series": series_tag.text.strip() if series_tag else "",
                "set": set_tag.text.strip() if set_tag else "",
                "rarity": rarity_tag.text.strip() if rarity_tag else "",
                "image": filename,
                "url": image_url,
                "card_id": card_id_tag
            }

            all_cards.append(card_data)

        except Exception as e:
            print(f"⚠️ Ошибка обработки карточки: {e}")
            continue

    print(f"✅ Страница {page} обработана")

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(all_cards, f, ensure_ascii=False, indent=2)

print(f"💾 Сохранено {len(all_cards)} карточек в {OUTPUT_JSON}")
driver.quit()