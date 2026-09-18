import json
import re
import time
from datetime import datetime
import cloudscraper
from bs4 import BeautifulSoup

URL = "https://www.kleinanzeigen.de/s-bestandsliste.html?userId=128825439"
BASE_URL = "https://www.kleinanzeigen.de"
INTERVAL_SECONDS = 3600  # 1 godzina


def fetch_offers():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Pobieranie ogłoszeń...")
    scraper = cloudscraper.create_scraper()
    
    try:
        response = scraper.get(URL, timeout=30)
    except Exception as e:
        print(f"Błąd połączenia: {e}")
        return

    if response.status_code != 200:
        print(f"Błąd HTTP: status {response.status_code}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.find_all("article", class_="aditem")

    offers = []
    for ad in articles:
        ad_id = ad.get("data-adid")
        link_tag = ad.find("a", class_="ellipsis")
        link = BASE_URL + link_tag["href"] if link_tag and link_tag.has_attr("href") else "#"
        title = link_tag.get_text(strip=True) if link_tag else "Kein Titel"

        desc_tag = ad.find("p", class_="aditem-main--middle--description")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        price_tag = ad.find("p", class_="aditem-main--middle--price-shipping--price")
        price = price_tag.get_text(strip=True) if price_tag else "Preis auf Anfrage"

        img_tag = ad.find("img")
        img_src = ""
        if img_tag:
            raw_img = (
                img_tag.get("data-imgsrc")
                or img_tag.get("data-src")
                or img_tag.get("src")
                or ""
            )

            if "rule=" in raw_img:
                img_src = re.sub(r"rule=\$_[\w\.]+", "rule=$_59.JPG", raw_img)
            elif re.search(r"\$_\d+\.JPG", raw_img, re.IGNORECASE):
                img_src = re.sub(r"\$_\d+\.JPG", "$_57.JPG", raw_img, flags=re.IGNORECASE)
            elif "$_" in raw_img:
                img_src = re.sub(r"\$_[\w\.]+", "$_57.JPG", raw_img)
            elif "?" in raw_img:
                img_src = f"{raw_img.split('?')[0]}?rule=$_59.JPG"
            else:
                img_src = raw_img

        if ad_id:
            offers.append({
                "id": ad_id,
                "title": title,
                "description": description,
                "price": price,
                "image": img_src,
                "url": link
            })

    with open("offers.json", "w", encoding="utf-8") as f:
        json.dump(offers, f, ensure_ascii=False, indent=2)

    print(f"Zapisano {len(offers)} ogłoszeń do offers.json.")


if __name__ == "__main__":
    while True:
        try:
            fetch_offers()
        except Exception as e:
            print(f"Nieoczekiwany błąd: {e}")

        print(f"Następne sprawdzenie za 60 minut...\n")
        try:
            time.sleep(INTERVAL_SECONDS)
        except KeyboardInterrupt:
            print("\nZatrzymano działanie skryptu.")
            break
