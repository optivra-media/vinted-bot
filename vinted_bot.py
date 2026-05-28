"""
Vinted Discord Bot – Feste Kategorien & Channels
=================================================
Jede Kategorie postet automatisch in ihren eigenen Discord-Channel.

KATEGORIEN:
  Nike (alles)     → CHANNEL_NIKE
  Nike unter 10€   → CHANNEL_NIKE_10
  Nike unter 20€   → CHANNEL_NIKE_20
  Adidas (alles)   → CHANNEL_ADIDAS
  Adidas unter 15€ → CHANNEL_ADIDAS_15
  Adidas unter 40€ → CHANNEL_ADIDAS_40

SETUP:
  pip install discord.py requests python-dotenv

  .env Datei:
    DISCORD_TOKEN=dein_bot_token

    CHANNEL_NIKE=111111111111
    CHANNEL_NIKE_10=222222222222
    CHANNEL_NIKE_20=333333333333
    CHANNEL_ADIDAS=444444444444
    CHANNEL_ADIDAS_15=555555555555
    CHANNEL_ADIDAS_40=666666666666

  Bot starten:
    python vinted_bot.py
"""

import discord
from discord.ext import tasks
import requests
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHECK_INTERVAL_SECONDS = 40  # 40s – gute Balance zwischen Geschwindigkeit und IP-Schutz

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "de-DE,de;q=0.9",
}

# ─── Kategorien-Konfiguration ─────────────────────────────────────
# brand_id: Nike=53, Adidas=14
# price_max: None = kein Limit

CATEGORIES = [
    {
        "name":      "Nike – Alles",
        "brand_id":  53,
        "price_max": None,
        "channel":   int(os.getenv("CHANNEL_NIKE", 0)),
        "color":     0xF5821F,  # Nike Orange
    },
    {
        "name":      "Nike – unter 10€",
        "brand_id":  53,
        "price_max": 10,
        "channel":   int(os.getenv("CHANNEL_NIKE_10", 0)),
        "color":     0xF5821F,
    },
    {
        "name":      "Nike – unter 20€",
        "brand_id":  53,
        "price_max": 20,
        "channel":   int(os.getenv("CHANNEL_NIKE_20", 0)),
        "color":     0xF5821F,
    },
    {
        "name":      "Adidas – Alles",
        "brand_id":  14,
        "price_max": None,
        "channel":   int(os.getenv("CHANNEL_ADIDAS", 0)),
        "color":     0x000000,  # Adidas Schwarz
    },
    {
        "name":      "Adidas – unter 15€",
        "brand_id":  14,
        "price_max": 15,
        "channel":   int(os.getenv("CHANNEL_ADIDAS_15", 0)),
        "color":     0x000000,
    },
    {
        "name":      "Adidas – unter 40€",
        "brand_id":  14,
        "price_max": 40,
        "channel":   int(os.getenv("CHANNEL_ADIDAS_40", 0)),
        "color":     0x000000,
    },
]

# Gesehene Artikel-IDs pro Kategorie (verhindert Doppelposts)
seen_ids: dict[str, set[int]] = {cat["name"]: set() for cat in CATEGORIES}
first_run = True

# ─── Nur Kleidung erlauben (Whitelist-Ansatz) ─────────────────────
# Vinted Kategorie-IDs die ERLAUBT sind (nur Kleidung)
# Herren, Damen, Kinder Kleidung – KEINE Schuhe, Taschen, Accessoires
ERLAUBTE_KATEGORIEN = {
    # Herren Kleidung
    "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14",
    "15", "16", "17", "18", "19", "20", "21", "22", "1175",
    # Damen Kleidung
    "1037", "1038", "1039", "1040", "1041", "1042", "1043",
    "1044", "1045", "1046", "1047", "1048", "1049", "1050",
    # Kinder Kleidung → ENTFERNT
}

# Keywords die erlaubte Kleidungsstücke beschreiben
KLEIDUNGS_KEYWORDS = [
    # Oberteile
    "hoodie", "hoody", "sweatshirt", "sweater", "pullover", "pulli",
    "t-shirt", "tshirt", "shirt", "longsleeve", "top", "polo",
    # Jacken & Mäntel
    "jacke", "jacket", "mantel", "coat", "parka", "windbreaker",
    "anorak", "fleece", "daunenjacke", "regenjacke", "übergangsjacke",
    "veste", "jas",
    # Hosen
    "hose", "jeans", "jogger", "jogginghose", "trainingshose",
    "shorts", "short", "bermuda", "chino", "cargo", "leggings",
    "broek", "pantalon",
    # Weitere Kleidung
    "hemd", "bluse", "kleid", "rock", "overall", "jumpsuit",
    "body", "unterhemd", "tank", "trikot", "jersey", "uniform",
    "anzug", "suit", "blazer", "sakko", "weste",
    # Sport
    "trainingsanzug", "sportanzug", "tracksuit", "trainingsjacke",
    "sporthose", "sportshirt", "trikot",
]

# Keywords die NICHT erlaubt sind (Schuhe, Gegenstände etc.)
VERBOTEN_KEYWORDS = [
    # Schuhe (alle Sprachen)
    "schuh", "schuhe", "sneaker", "sneakers", "boots", "stiefel",
    "turnschuh", "laufschuh", "slipper", "sandale", "sandalen",
    "scarpe", "scarpa", "schoen", "schoenen", "chaussure", "zapatos",
    "loafer", "pumps", "ballerina", "clogs", "hausschuh",
    "air max", "air force", "dunk", "yeezy", "campus", "gazelle",
    "samba", "superstar", "stan smith", "ultraboost", "nmd",
    "574", "990", "992", "converse", "vans", "timberland", "ugg",
    # Sport-Gegenstände
    "ball", "fußball", "basketball", "handball", "volleyball",
    "tennisball", "rugby", "puck",
    # Taschen & Accessoires
    "tasche", "bag", "rucksack", "backpack", "handtasche",
    "geldbeutel", "portemonnaie", "wallet", "gürteltasche",
    "cap", "mütze", "beanie", "hut", "gürtel", "belt",
    "schal", "handschuhe", "socken", "socks", "unterwäsche",
    # Sonstiges
    "uhr", "watch", "schmuck", "kette", "ring", "armband",
    "brille", "sunglasses", "parfum", "cologne",
    # Kinder
    "kinder", "baby", "bambino", "bambina", "enfant", "kind",
    "junior", "kids", "maat 1", "maat 2", "taille 1", "taille 2",
]

# Schuhgrößen (numerisch, EU) → fast immer Schuhe
SCHUH_GROESSEN = {str(i) for i in range(16, 50)}


def ist_kleidung(item: dict) -> bool:
    """Gibt True zurück wenn der Artikel Kleidung ist – alles andere wird geblockt."""
    titel     = item.get("title", "").lower()
    groesse   = item.get("size_title", "").strip()
    kat_id    = str(item.get("catalog_id", ""))

    # 0. Land prüfen
    land = item.get("user", {}).get("country_iso", "")
    if land and land.upper() not in ERLAUBTE_LAENDER:
        return False

    # 1. Verbotene Keywords im Titel → sofort blocken
    if any(kw in titel for kw in VERBOTEN_KEYWORDS):
        return False

    # 2. Numerische Größe (z.B. 19, 24, 42, 44) → wahrscheinlich Schuh → blocken
    if groesse in SCHUH_GROESSEN:
        return False

    # 3. Erlaubte Vinted-Kategorie → durchlassen
    if kat_id in ERLAUBTE_KATEGORIEN:
        return True

    # 4. Kleidungs-Keyword im Titel → durchlassen
    if any(kw in titel for kw in KLEIDUNGS_KEYWORDS):
        return True

    # 5. Größen die typisch für Kleidung sind → durchlassen
    kleidungs_groessen = {"xs", "s", "m", "l", "xl", "xxl", "xxxl",
                          "xs/s", "s/m", "m/l", "l/xl", "one size"}
    if groesse.lower() in kleidungs_groessen:
        return True

    # 6. Im Zweifel: blocken
    return False


# ─── Hilfsfunktionen ──────────────────────────────────────────────

# Erlaubte Länder-Codes
ERLAUBTE_LAENDER = {"DE", "AT", "CH", "IT", "FR", "ES"}

def build_url(brand_id: int, price_max: int | None) -> str:
    # Vinted Länder-IDs: DE=7, AT=193, CH=195, IT=10, FR=6, ES=13
    laender_ids = ["7", "193", "195", "10", "6", "13"]
    params = [
        f"brand_ids[]={brand_id}",
        "order=newest_first",
        "per_page=30",
    ] + [f"country_ids[]={lid}" for lid in laender_ids]
    if price_max is not None:
        params.append(f"price_to={price_max}")
    return "https://www.vinted.de/api/v2/catalog/items?" + "&".join(params)


def get_cookies() -> dict:
    try:
        s = requests.Session()
        s.get("https://www.vinted.de", headers=HEADERS, timeout=10)
        return s.cookies.get_dict()
    except:
        return {}


def fetch_items(brand_id: int, price_max: int | None) -> list[dict]:
    url = build_url(brand_id, price_max)
    cookies = get_cookies()
    try:
        r = requests.get(url, headers=HEADERS, cookies=cookies, timeout=15)
        r.raise_for_status()
        return r.json().get("items", [])
    except Exception as e:
        print(f"[Fehler] {e}")
        return []


def build_embed(item: dict, cat: dict) -> discord.Embed:
    title     = item.get("title", "Unbekannt")
    price     = item.get("price", {})
    price_str = f"{price.get('amount', '?')} {price.get('currency_code', 'EUR')}"
    item_url  = f"https://www.vinted.de/items/{item.get('id')}"
    photos    = item.get("photos", [])
    img_url   = photos[0].get("url") if photos else None

    embed = discord.Embed(
        title=f"🛍️ {title}",
        url=item_url,
        color=cat["color"],
        description=f"**Kategorie:** {cat['name']}"
    )
    embed.add_field(name="💶 Preis",   value=price_str,                       inline=True)
    embed.add_field(name="📏 Größe",   value=item.get("size_title", "—"),     inline=True)
    embed.add_field(name="✨ Zustand", value=item.get("status", "—"),         inline=True)
    embed.add_field(name="👤 Verkäufer", value=item.get("user", {}).get("login", "—"), inline=True)
    embed.add_field(name="🔗 Artikel", value=f"[Auf Vinted ansehen]({item_url})", inline=False)

    if img_url:
        embed.set_image(url=img_url)
    embed.set_footer(text=f"Vinted Bot • {cat['name']}")
    return embed


# ─── Discord Client ───────────────────────────────────────────────

intents = discord.Intents.default()
client  = discord.Client(intents=intents)


@tasks.loop(seconds=CHECK_INTERVAL_SECONDS)
async def check_all_categories():
    global first_run

    cookies = get_cookies()  # Einmal pro Runde holen

    for cat in CATEGORIES:
        channel = client.get_channel(cat["channel"])
        if not channel:
            print(f"[Warnung] Channel für '{cat['name']}' nicht gefunden (ID: {cat['channel']})")
            continue

        items = fetch_items(cat["brand_id"], cat["price_max"])
        new_items = []

        for item in items:
            iid = item.get("id")
            if iid and iid not in seen_ids[cat["name"]]:
                seen_ids[cat["name"]].add(iid)
                if not first_run and ist_kleidung(item):
                    new_items.append(item)

        if new_items:
            print(f"[{cat['name']}] {len(new_items)} neue Artikel")
            for item in new_items:
                await channel.send(embed=build_embed(item, cat))

    first_run = False


@client.event
async def on_ready():
    print(f"✅ Bot gestartet als: {client.user}")
    print(f"📦 {len(CATEGORIES)} Kategorien aktiv:")
    for cat in CATEGORIES:
        limit = f"unter {cat['price_max']}€" if cat["price_max"] else "kein Preislimit"
        print(f"   • {cat['name']} ({limit}) → Channel {cat['channel']}")
    check_all_categories.start()


client.run(DISCORD_TOKEN)
