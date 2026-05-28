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

# ─── Schuhe rausfiltern ───────────────────────────────────────────
SCHUH_KEYWORDS = [
    "schuh", "schuhe", "sneaker", "sneakers", "boots", "stiefel",
    "turnschuh", "laufschuh", "slipper", "sandale", "sandalen",
    "loafer", "mokassin", "ballerina", "pumps", "absatz",
    "air max", "air force", "yeezy", "jordan", "dunk", "blazer shoe",
    "ultraboost", "superstar", "stan smith", "nmd", "forum low",
    "574", "990", "992", "1080", "chuck", "converse", "vans",
    "timberland", "ugg", "crocs", "birkenstock", "clogs"
]

def ist_schuh(item: dict) -> bool:
    titel = item.get("title", "").lower()
    kategorie = str(item.get("catalog_id", ""))
    # Vinted Schuh-Kategorie IDs (Herren+Damen Schuhe)
    schuh_kategorien = {"196", "197", "198", "199", "200", "201", "202",
                        "203", "204", "205", "1037", "1038"}
    if kategorie in schuh_kategorien:
        return True
    return any(keyword in titel for keyword in SCHUH_KEYWORDS)


# ─── Hilfsfunktionen ──────────────────────────────────────────────

def build_url(brand_id: int, price_max: int | None) -> str:
    params = [
        f"brand_ids[]={brand_id}",
        "order=newest_first",
        "per_page=30",
    ]
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
                if not first_run and not ist_schuh(item):
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
