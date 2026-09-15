import json
import re
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
        
        # Bild-URL erfassen (Kleinanzeigen nutzt data-imgsrc für größere Bilder)
        img_tag = ad.find("img")
        img_src = ""
        if img_tag:
            raw_img = (
                img_tag.get("data-imgsrc") 
                or img_tag.get("data-src") 
                or img_tag.get("src") 
                or ""
            )
            
            # Kleinanzeigen Bildregel auf HD ($ _57.JPG) anpassen
            if "rule=" in raw_img:
                img_src = re.sub(r"rule=\$_[\w\.]+", "rule=$_57.JPG", raw_img)
            elif "$_" in raw_img:
                img_src = re.sub(r"\$_[\w\.]+", "$_57.JPG", raw_img)
            elif raw_img:
                img_src = f"{raw_img}?rule=$_57.JPG"
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
    print(f"Erfolg: {len(offers)} Inserate in HD-Qualitaet gespeichert.")
else:
    print(f"Fehler: Statuscode {response.status_code}")
