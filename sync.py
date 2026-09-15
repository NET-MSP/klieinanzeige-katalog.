import json
import re
import time
import cloudscraper
from bs4 import BeautifulSoup

URL = "https://www.kleinanzeigen.de/s-bestandsliste.html?userId=128825439"
BASE_URL = "https://www.kleinanzeigen.de"

scraper = cloudscraper.create_scraper()
response = scraper.get(URL)

if response.status_code == 200:
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
        
        # Domyślne zdjęcie z listy na wypadek błędu
        img_tag = ad.find("img")
        hd_image = ""
        if img_tag:
            hd_image = img_tag.get("src") or img_tag.get("data-src") or ""

        # Wejście w ogłoszenie po prawdziwe zdjęcie HD
        if link != "#":
            try:
                ad_resp = scraper.get(link)
                if ad_resp.status_code == 200:
                    ad_soup = BeautifulSoup(ad_resp.text, "html.parser")
                    # Szukamy głównego zdjęcia w pełnej rozdzielczości
                    main_img = ad_soup.find("img", id="viewad-image") or ad_soup.find("meta", property="og:image")
                    if main_img:
                        img_url = main_img.get("src") or main_img.get("content") or ""
                        if img_url:
                            # Wymuszenie formatu HD $_59.JPG / $_57.JPG
                            if "?" in img_url:
                                base_part = img_url.split("?")[0]
                                hd_image = f"{base_part}?rule=$_59.JPG"
                            elif "$_" in img_url:
                                hd_image = re.sub(r"\$_[\w\.]+", "$_59.JPG", img_url)
                            else:
                                hd_image = img_url
                time.sleep(0.5)  # Krótka pauza, by nie przeciążać serwera
            except Exception as e:
                print(f"Błąd pobierania zdjęcia dla {ad_id}: {e}")

        if ad_id:
            offers.append({
                "id": ad_id,
                "title": title,
                "description": description,
                "price": price,
                "image": hd_image,
                "url": link
            })

    with open("offers.json", "w", encoding="utf-8") as f:
        json.dump(offers, f, ensure_ascii=False, indent=2)
    print(f"Erfolg: {len(offers)} Inserate mit echten HD-Bildern gespeichert.")
else:
    print(f"Fehler: Statuscode {response.status_code}")
