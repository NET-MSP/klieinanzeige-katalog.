import json
import re
import sys
import cloudscraper
from bs4 import BeautifulSoup

URL = "https://www.kleinanzeigen.de/s-bestandsliste.html?userId=128825439"
BASE_URL = "https://www.kleinanzeigen.de"


def fetch_offers():
    print(f"Preuzimanje oglasa s: {URL}")
    scraper = cloudscraper.create_scraper(
        browser={
            "browser": "chrome",
            "platform": "windows",
            "desktop": True
        }
    )

    try:
        response = scraper.get(URL, timeout=30)
    except Exception as e:
        print(f"Greska mreze: {e}")
        return False

    if response.status_code != 200:
        print(f"HTTP greska: Status {response.status_code}")
        return False

    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.find_all("article", class_="aditem")

    if not articles:
        print("Nisu pronadeni oglasi (moguca blokada ili promjena HTML strukture).")
        return False

    offers = []
    for ad in articles:
        ad_id = ad.get("data-adid")

        link_tag = ad.find("a", class_="ellipsis") or ad.find("a", href=re.compile(r"/s-anzeige/"))
        link = BASE_URL + link_tag["href"] if link_tag and link_tag.has_attr("href") else "#"
        title = link_tag.get_text(strip=True) if link_tag else "Bez naslova"

        desc_tag = ad.find("p", class_="aditem-main--middle--description")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        price_tag = ad.find("p", class_="aditem-main--middle--price-shipping--price")
        price = price_tag.get_text(strip=True) if price_tag else "Cijena na upit"

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

    print(f"Uspjesno dohvaceno {len(offers)} oglasa.")

    with open("offers.json", "w", encoding="utf-8") as f:
        json.dump(offers, f, ensure_ascii=False, indent=2)

    print("Podaci su spremljeni u datoteku offers.json.")
    return True


if __name__ == "__main__":
    success = fetch_offers()
    if not success:
        sys.exit(1)
