"""
Vinted Snipebot – Vollständig kategorisiert
============================================
Channels & Variablen in Railway:

SNIPEBOT NIKE:
  CHANNEL_NIKE                → #nike (alles)
  CHANNEL_NIKE_10             → #nike-10 (0.01–10€)
  CHANNEL_NIKE_20             → #nike-20 (10.01–20€)
  CHANNEL_NIKE_TRACKPANTS     → #nike-trackpants
  CHANNEL_NIKE_TRACKSUITS     → #nike-tracksuits
  CHANNEL_NIKE_JACKEN         → #nike-jacken
  CHANNEL_NIKE_SHIRTS         → #nike-shirts
  CHANNEL_NIKE_HOODIES        → #nike-hoodies
  CHANNEL_NIKE_POLOS          → #nike-polos

SNIPEBOT ADIDAS:
  CHANNEL_ADIDAS              → #adidas (alles)
  CHANNEL_ADIDAS_15           → #adidas-15 (0.01–15€)
  CHANNEL_ADIDAS_40           → #adidas-40 (15.01–40€)
  CHANNEL_ADIDAS_TRACKPANTS   → #adidas-trackpants
  CHANNEL_ADIDAS_TRACKSUITS   → #adidas-tracksuits
  CHANNEL_ADIDAS_JACKEN       → #adidas-jacken
  CHANNEL_ADIDAS_SHIRTS       → #adidas-shirts
  CHANNEL_ADIDAS_HOODIES      → #adidas-hoodies
  CHANNEL_ADIDAS_POLOS        → #adidas-polos

SNIPEBOT LACOSTE:
  CHANNEL_LACOSTE             → #lacoste (alles)
  CHANNEL_LACOSTE_10          → #lacoste-10 (0.01–10€)
  CHANNEL_LACOSTE_20          → #lacoste-20 (10.01–20€)
  CHANNEL_LACOSTE_40          → #lacoste-40 (20.01–40€)
  CHANNEL_LACOSTE_TRACKPANTS  → #lacoste-trackpants
  CHANNEL_LACOSTE_TRACKSUITS  → #lacoste-tracksuits
  CHANNEL_LACOSTE_JACKEN      → #lacoste-jacken
  CHANNEL_LACOSTE_SHIRTS      → #lacoste-shirts
  CHANNEL_LACOSTE_HOODIES     → #lacoste-hoodies
  CHANNEL_LACOSTE_POLOS       → #lacoste-polos

SNIPEBOT RL:
  CHANNEL_RL                  → #ralph-lauren (alles)
  CHANNEL_RL_10               → #ralph-lauren-10 (0.01–10€)
  CHANNEL_RL_20               → #ralph-lauren-20 (10.01–20€)
  CHANNEL_RL_40               → #ralph-lauren-40 (20.01–40€)
  CHANNEL_RL_POLOS            → #ralph-lauren-polos
  CHANNEL_RL_JACKEN           → #ralph-lauren-jacken
  CHANNEL_RL_TRACKSUIT        → #ralph-lauren-tracksuit

SNIPEBOT TRIKOTS:
  CHANNEL_TRIKOTS             → #trikots (alles)
  CHANNEL_TRIKOTS_HOSE        → #trikot-hose
  CHANNEL_TRIKOTS_SET         → #trikot-set
"""

import discord
from discord.ext import tasks
import requests
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN        = os.getenv("DISCORD_TOKEN")
CHECK_INTERVAL       = 40

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "de-DE,de;q=0.9",
}

# ─── Vinted Brand IDs ─────────────────────────────────────────────
BRAND = {
    "nike":         53,
    "adidas":       14,
    "lacoste":      60,
    "ralph_lauren": 88,
}

# Trikot-Marken (viele Marken gleichzeitig)
TRIKOT_BRANDS = [53, 14, 60, 88, 316, 103, 254]  # Nike, Adidas, Lacoste, RL, Champion, Puma, Tommy

# Erlaubte Länder: DE, AT, CH, IT, FR, ES
LAENDER = ["7", "193", "195", "10", "6", "13"]

# ─── Keyword-Filter ───────────────────────────────────────────────
KW_TRACKPANTS = [
    "trackpant", "track pant", "jogginghose", "trainingshose", "sporthose",
    "jogger", "sweatpant", "joggingbroek", "pantalon de survêtement",
    "pantalon survêtement", "pantalon jogging", "tuta pantalone",
    "pantalone tuta", "pantalón chandal", "chandal pantalon",
    "track bottom", "bottoms", "track hose", "trackhose",
]

KW_TRACKSUITS = [
    "tracksuit", "trainingsanzug", "jogginganzug", "sportanzug",
    "tuta", "tuta completa", "survêtement", "survetement",
    "chandal", "trainingspak", "set", "anzug", "komplett",
    "track suit", "jogging set", "sport set",
]

KW_JACKEN = [
    "jacke", "jacket", "windbreaker", "anorak", "parka",
    "übergangsjacke", "regenjacke", "trainingsjacke", "zip",
    "giubbotto", "giubbino", "veste", "blouson", "cazadora",
    "chaqueta", "coach jacket", "track jacket", "trackjacket",
    "fleece jacket", "softshell", "half zip", "quarter zip",
    "full zip", "winterjacke",
]

KW_SHIRTS = [
    "t-shirt", "tshirt", "shirt", "longsleeve", "long sleeve",
    "tee", "maglietta", "maglia", "t shirt", "kurzarm",
    "top ", "maglie", "chemise", "camiseta", "camisa",
]

KW_HOODIES = [
    "hoodie", "hoody", "sweatshirt", "sweater", "pullover",
    "pulli", "kapuzenpullover", "crewneck", "crew neck",
    "felpa", "sweat", "sudadera", "trui", "hoodie zip",
    "half zip hoodie", "quarter zip hoodie",
]

KW_POLOS = [
    "polo", "poloshirt", "polo shirt", "polo t-shirt",
    "polo neck", "polo hemd",
]

KW_TRIKOTS = [
    "trikot", "jersey", "maglia", "maillot", "camiseta",
    "football shirt", "soccer shirt", "fussballtrikot",
    "fußballtrikot", "sporttrikot", "kit",
]

KW_TRIKOT_HOSE = [
    "trikot hose", "sporthose", "shorts trikot", "football shorts",
    "soccer shorts", "fußballshorts", "pantaloncini",
]

KW_TRIKOT_SET = [
    "trikot set", "trikot anzug", "kit komplett", "shirt und hose",
    "jersey set", "football kit", "soccer kit",
]

# ─── Verbotene Keywords (Schuhe, Kinder, Accessoires) ────────────
VERBOTEN = [
    # Schuhe
    "schuh","schuhe","sneaker","sneakers","boots","stiefel","slipper",
    "sandale","sandalen","scarpe","scarpa","schoen","schoenen",
    "chaussure","chaussures","zapato","zapatos","zapatilla","zapatillas",
    "air max","air force","dunk","yeezy","campus","gazelle","samba",
    "superstar","stan smith","ultraboost","nmd","converse","vans",
    "timberland","ugg","crocs","birkenstock","loafer","pumps","ballerina",
    # Kinder
    "kinder","kinderjacke","kinderhose","baby","babykleidung","kleinkind",
    "junge","mädchen","kids","children","toddler","infant","bambino",
    "bambina","bambini","neonato","enfant","bébé","bebe","niño","niña",
    # Accessoires & Sonstiges
    "tasche","bag","rucksack","backpack","cap","mütze","beanie",
    "gürtel","belt","schal","socken","socks","handschuhe","gloves",
    "uhr","watch","schmuck","kette","ring","brille","parfum",
    "ball","fußball","basketball",
]

VERBOTEN_GROESSEN = (
    {str(i) for i in range(16, 36)} |
    {"86","92","98","104","110","116","122","128","134","140",
     "146","152","158","164","170"}
)

ERLAUBTE_GROESSEN = {"xs","s","m","l","xl","xxl","xxxl",
                     "xs/s","s/m","m/l","l/xl","one size"}

# ─── Kategorien ───────────────────────────────────────────────────
def ch(key): return int(os.getenv(key, 0))

CATEGORIES = [
    # ── NIKE ──────────────────────────────────────────────────────
    {"name":"Nike – Alles",        "brands":[BRAND["nike"]], "price_min":None,  "price_max":None,  "keywords":None,          "channel":ch("CHANNEL_NIKE"),              "color":0xF5821F},
    {"name":"Nike – 0-10€",        "brands":[BRAND["nike"]], "price_min":0.01,  "price_max":10,    "keywords":None,          "channel":ch("CHANNEL_NIKE_10"),           "color":0xF5821F},
    {"name":"Nike – 10-20€",       "brands":[BRAND["nike"]], "price_min":10.01, "price_max":20,    "keywords":None,          "channel":ch("CHANNEL_NIKE_20"),           "color":0xF5821F},
    {"name":"Nike – Trackpants",   "brands":[BRAND["nike"]], "price_min":None,  "price_max":None,  "keywords":KW_TRACKPANTS, "channel":ch("CHANNEL_NIKE_TRACKPANTS"),   "color":0xF5821F},
    {"name":"Nike – Tracksuits",   "brands":[BRAND["nike"]], "price_min":None,  "price_max":None,  "keywords":KW_TRACKSUITS, "channel":ch("CHANNEL_NIKE_TRACKSUITS"),   "color":0xF5821F},
    {"name":"Nike – Jacken",       "brands":[BRAND["nike"]], "price_min":None,  "price_max":None,  "keywords":KW_JACKEN,     "channel":ch("CHANNEL_NIKE_JACKEN"),       "color":0xF5821F},
    {"name":"Nike – Shirts",       "brands":[BRAND["nike"]], "price_min":None,  "price_max":None,  "keywords":KW_SHIRTS,     "channel":ch("CHANNEL_NIKE_SHIRTS"),       "color":0xF5821F},
    {"name":"Nike – Hoodies",      "brands":[BRAND["nike"]], "price_min":None,  "price_max":None,  "keywords":KW_HOODIES,    "channel":ch("CHANNEL_NIKE_HOODIES"),      "color":0xF5821F},
    {"name":"Nike – Polos",        "brands":[BRAND["nike"]], "price_min":None,  "price_max":None,  "keywords":KW_POLOS,      "channel":ch("CHANNEL_NIKE_POLOS"),        "color":0xF5821F},
    # ── ADIDAS ────────────────────────────────────────────────────
    {"name":"Adidas – Alles",      "brands":[BRAND["adidas"]], "price_min":None,  "price_max":None,  "keywords":None,          "channel":ch("CHANNEL_ADIDAS"),            "color":0x000000},
    {"name":"Adidas – 0-15€",      "brands":[BRAND["adidas"]], "price_min":0.01,  "price_max":15,    "keywords":None,          "channel":ch("CHANNEL_ADIDAS_15"),         "color":0x000000},
    {"name":"Adidas – 15-40€",     "brands":[BRAND["adidas"]], "price_min":15.01, "price_max":40,    "keywords":None,          "channel":ch("CHANNEL_ADIDAS_40"),         "color":0x000000},
    {"name":"Adidas – Trackpants", "brands":[BRAND["adidas"]], "price_min":None,  "price_max":None,  "keywords":KW_TRACKPANTS, "channel":ch("CHANNEL_ADIDAS_TRACKPANTS"), "color":0x000000},
    {"name":"Adidas – Tracksuits", "brands":[BRAND["adidas"]], "price_min":None,  "price_max":None,  "keywords":KW_TRACKSUITS, "channel":ch("CHANNEL_ADIDAS_TRACKSUITS"), "color":0x000000},
    {"name":"Adidas – Jacken",     "brands":[BRAND["adidas"]], "price_min":None,  "price_max":None,  "keywords":KW_JACKEN,     "channel":ch("CHANNEL_ADIDAS_JACKEN"),     "color":0x000000},
    {"name":"Adidas – Shirts",     "brands":[BRAND["adidas"]], "price_min":None,  "price_max":None,  "keywords":KW_SHIRTS,     "channel":ch("CHANNEL_ADIDAS_SHIRTS"),     "color":0x000000},
    {"name":"Adidas – Hoodies",    "brands":[BRAND["adidas"]], "price_min":None,  "price_max":None,  "keywords":KW_HOODIES,    "channel":ch("CHANNEL_ADIDAS_HOODIES"),    "color":0x000000},
    {"name":"Adidas – Polos",      "brands":[BRAND["adidas"]], "price_min":None,  "price_max":None,  "keywords":KW_POLOS,      "channel":ch("CHANNEL_ADIDAS_POLOS"),      "color":0x000000},
    # ── LACOSTE ───────────────────────────────────────────────────
    {"name":"Lacoste – Alles",      "brands":[BRAND["lacoste"]], "price_min":None,  "price_max":None,  "keywords":None,          "channel":ch("CHANNEL_LACOSTE"),            "color":0x00A850},
    {"name":"Lacoste – 0-10€",      "brands":[BRAND["lacoste"]], "price_min":0.01,  "price_max":10,    "keywords":None,          "channel":ch("CHANNEL_LACOSTE_10"),         "color":0x00A850},
    {"name":"Lacoste – 10-20€",     "brands":[BRAND["lacoste"]], "price_min":10.01, "price_max":20,    "keywords":None,          "channel":ch("CHANNEL_LACOSTE_20"),         "color":0x00A850},
    {"name":"Lacoste – 20-40€",     "brands":[BRAND["lacoste"]], "price_min":20.01, "price_max":40,    "keywords":None,          "channel":ch("CHANNEL_LACOSTE_40"),         "color":0x00A850},
    {"name":"Lacoste – Trackpants", "brands":[BRAND["lacoste"]], "price_min":None,  "price_max":None,  "keywords":KW_TRACKPANTS, "channel":ch("CHANNEL_LACOSTE_TRACKPANTS"), "color":0x00A850},
    {"name":"Lacoste – Tracksuits", "brands":[BRAND["lacoste"]], "price_min":None,  "price_max":None,  "keywords":KW_TRACKSUITS, "channel":ch("CHANNEL_LACOSTE_TRACKSUITS"), "color":0x00A850},
    {"name":"Lacoste – Jacken",     "brands":[BRAND["lacoste"]], "price_min":None,  "price_max":None,  "keywords":KW_JACKEN,     "channel":ch("CHANNEL_LACOSTE_JACKEN"),     "color":0x00A850},
    {"name":"Lacoste – Shirts",     "brands":[BRAND["lacoste"]], "price_min":None,  "price_max":None,  "keywords":KW_SHIRTS,     "channel":ch("CHANNEL_LACOSTE_SHIRTS"),     "color":0x00A850},
    {"name":"Lacoste – Hoodies",    "brands":[BRAND["lacoste"]], "price_min":None,  "price_max":None,  "keywords":KW_HOODIES,    "channel":ch("CHANNEL_LACOSTE_HOODIES"),    "color":0x00A850},
    {"name":"Lacoste – Polos",      "brands":[BRAND["lacoste"]], "price_min":None,  "price_max":None,  "keywords":KW_POLOS,      "channel":ch("CHANNEL_LACOSTE_POLOS"),      "color":0x00A850},
    # ── RALPH LAUREN ──────────────────────────────────────────────
    {"name":"Ralph Lauren – Alles",     "brands":[BRAND["ralph_lauren"]], "price_min":None,  "price_max":None,  "keywords":None,          "channel":ch("CHANNEL_RL"),            "color":0x002868},
    {"name":"Ralph Lauren – 0-10€",     "brands":[BRAND["ralph_lauren"]], "price_min":0.01,  "price_max":10,    "keywords":None,          "channel":ch("CHANNEL_RL_10"),         "color":0x002868},
    {"name":"Ralph Lauren – 10-20€",    "brands":[BRAND["ralph_lauren"]], "price_min":10.01, "price_max":20,    "keywords":None,          "channel":ch("CHANNEL_RL_20"),         "color":0x002868},
    {"name":"Ralph Lauren – 20-40€",    "brands":[BRAND["ralph_lauren"]], "price_min":20.01, "price_max":40,    "keywords":None,          "channel":ch("CHANNEL_RL_40"),         "color":0x002868},
    {"name":"Ralph Lauren – Polos",     "brands":[BRAND["ralph_lauren"]], "price_min":None,  "price_max":None,  "keywords":KW_POLOS,      "channel":ch("CHANNEL_RL_POLOS"),      "color":0x002868},
    {"name":"Ralph Lauren – Jacken",    "brands":[BRAND["ralph_lauren"]], "price_min":None,  "price_max":None,  "keywords":KW_JACKEN,     "channel":ch("CHANNEL_RL_JACKEN"),     "color":0x002868},
    {"name":"Ralph Lauren – Tracksuit", "brands":[BRAND["ralph_lauren"]], "price_min":None,  "price_max":None,  "keywords":KW_TRACKSUITS, "channel":ch("CHANNEL_RL_TRACKSUIT"),  "color":0x002868},
    # ── TRIKOTS (alle Marken) ─────────────────────────────────────
    {"name":"Trikots – Alles",  "brands":TRIKOT_BRANDS, "price_min":None, "price_max":None, "keywords":KW_TRIKOTS,     "channel":ch("CHANNEL_TRIKOTS"),      "color":0x09B1BA},
    {"name":"Trikots – Hose",   "brands":TRIKOT_BRANDS, "price_min":None, "price_max":None, "keywords":KW_TRIKOT_HOSE, "channel":ch("CHANNEL_TRIKOTS_HOSE"), "color":0x09B1BA},
    {"name":"Trikots – Set",    "brands":TRIKOT_BRANDS, "price_min":None, "price_max":None, "keywords":KW_TRIKOT_SET,  "channel":ch("CHANNEL_TRIKOTS_SET"),  "color":0x09B1BA},
]

seen_ids: dict[str, set[int]] = {cat["name"]: set() for cat in CATEGORIES}
first_run = True

# ─── Hilfsfunktionen ──────────────────────────────────────────────
def build_url(brand_ids: list[int], price_min: float | None, price_max: float | None) -> str:
    params = ["order=newest_first", "per_page=30"]
    for bid in brand_ids:
        params.append(f"brand_ids[]={bid}")
    for lid in LAENDER:
        params.append(f"country_ids[]={lid}")
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


def fetch_items(brand_ids: list[int], price_min, price_max) -> list[dict]:
    try:
        r = requests.get(build_url(brand_ids, price_min, price_max),
                         headers=HEADERS, cookies=get_cookies(), timeout=15)
        r.raise_for_status()
        return r.json().get("items", [])
    except Exception as e:
        print(f"[Fehler] {e}")
        return []


def passt_preis(item: dict, price_min, price_max) -> bool:
    try:
        preis = float(item.get("price", {}).get("amount", 0))
        if price_min is not None and preis < price_min:
            return False
        if price_max is not None and preis > price_max:
            return False
        return True
    except:
        return True


def passt_keyword(item: dict, keywords: list | None) -> bool:
    if keywords is None:
        return True
    titel = item.get("title", "").lower()
    return any(kw in titel for kw in keywords)


def ist_kleidung(item: dict) -> bool:
    titel   = item.get("title", "").lower()
    groesse = item.get("size_title", "").strip().lower()

    # Verbotene Keywords
    if any(kw in titel for kw in VERBOTEN):
        return False
    # Verbotene Größen (Schuh/Kinder)
    if groesse in VERBOTEN_GROESSEN:
        return False
    # Land prüfen
    land = item.get("user", {}).get("country_iso", "").upper()
    if land and land not in {"DE","AT","CH","IT","FR","ES"}:
        return False
    return True


def build_embed(item: dict, cat: dict) -> discord.Embed:
    title    = item.get("title", "Unbekannt")
    price    = item.get("price", {})
    pstr     = f"{price.get('amount','?')} {price.get('currency_code','EUR')}"
    url      = f"https://www.vinted.de/items/{item.get('id')}"
    photos   = item.get("photos", [])
    img      = photos[0].get("url") if photos else None

    e = discord.Embed(title=f"🛍️ {title}", url=url, color=cat["color"],
                      description=f"**{cat['name']}**")
    e.add_field(name="💶 Preis",     value=pstr,                                  inline=True)
    e.add_field(name="📏 Größe",     value=item.get("size_title","—"),            inline=True)
    e.add_field(name="✨ Zustand",   value=item.get("status","—"),                inline=True)
    e.add_field(name="👤 Verkäufer", value=item.get("user",{}).get("login","—"),  inline=True)
    e.add_field(name="🔗 Artikel",   value=f"[Auf Vinted ansehen]({url})",        inline=False)
    if img:
        e.set_image(url=img)
    e.set_footer(text=f"Vinted Snipebot • {cat['name']}")
    return e


# ─── Discord ──────────────────────────────────────────────────────
intents = discord.Intents.default()
client  = discord.Client(intents=intents)


@tasks.loop(seconds=CHECK_INTERVAL)
async def check_all():
    global first_run

    for cat in CATEGORIES:
        channel = client.get_channel(cat["channel"])
        if not channel:
            continue

        items    = fetch_items(cat["brands"], cat["price_min"], cat["price_max"])
        new_items = []

        for item in items:
            iid = item.get("id")
            if not iid or iid in seen_ids[cat["name"]]:
                continue
            seen_ids[cat["name"]].add(iid)
            if first_run:
                continue
            if not ist_kleidung(item):
                continue
            if not passt_preis(item, cat["price_min"], cat["price_max"]):
                continue
            if not passt_keyword(item, cat["keywords"]):
                continue
            new_items.append(item)

        for item in new_items:
            await channel.send(embed=build_embed(item, cat))
        if new_items:
            print(f"[{cat['name']}] {len(new_items)} neue Artikel")

    first_run = False


@client.event
async def on_ready():
    print(f"✅ Snipebot online als {client.user}")
    print(f"📦 {len(CATEGORIES)} Kategorien aktiv")
    check_all.start()


client.run(DISCORD_TOKEN)
