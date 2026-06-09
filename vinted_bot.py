import discord
from discord.ext import tasks, commands
from discord import app_commands
import requests
import asyncio
import json
import os
import io
import time
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN  = os.getenv("DISCORD_TOKEN")
PROXY_URL      = os.getenv("PROXY_URL")
PROXIES        = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None
SEEN_FILE      = "seen_ids.json"
REQUEST_DELAY  = 5
MONITOR_TTL    = 5 * 60 * 60
GUILD_ID       = int(os.getenv("GUILD_ID", 0))
MONITOR_CAT_ID = int(os.getenv("MONITOR_CATEGORY_ID", 0))

LAENDER = ["7", "193", "195", "10", "6", "13"]

# Nur diese Größen erlaubt
ERLAUBTE_GROESSEN = {"xs", "s", "m", "l", "xl", "xs/s", "s/m", "m/l", "l/xl", "one size"}

# ─── Brand IDs ────────────────────────────────────────────────────
NIKE         = 53
ADIDAS       = 14
LACOSTE      = 304
RL           = 88
FRED_PERRY   = 2929
LYLE_SCOTT   = 66644
LONSDALE     = 2193
CP_COMPANY   = 73952
LA_MARTINA   = 97
DOLCE        = 1043
ARMANI       = 5930015
DIESEL       = 161
CALVIN_KLEIN = 255
TOMMY        = 94
STONE_ISLAND = 73306
BURBERRY     = 364
MONCLER      = 6539
LEVIS        = 10
MISS_ME      = 35693
TRUE_REL     = 9075
GSTAR        = 258

BRAND_MAP = {
    "nike": NIKE, "adidas": ADIDAS, "lacoste": LACOSTE,
    "ralph lauren": RL, "rl": RL, "fred perry": FRED_PERRY,
    "lyle scott": LYLE_SCOTT, "lonsdale": LONSDALE,
    "cp company": CP_COMPANY, "la martina": LA_MARTINA,
    "dolce gabbana": DOLCE, "armani": ARMANI, "diesel": DIESEL,
    "calvin klein": CALVIN_KLEIN, "tommy hilfiger": TOMMY, "tommy": TOMMY,
    "stone island": STONE_ISLAND, "burberry": BURBERRY, "moncler": MONCLER,
    "levis": LEVIS, "levi's": LEVIS, "miss me": MISS_ME,
    "true religion": TRUE_REL, "g-star": GSTAR, "gstar": GSTAR,
}

TOP_BRANDS = [NIKE, ADIDAS, LACOSTE, RL, FRED_PERRY, STONE_ISLAND, CP_COMPANY, TOMMY, BURBERRY, MONCLER]
ALL_BRANDS = list(set(BRAND_MAP.values()))

# ─── Keywords ─────────────────────────────────────────────────────
KW_SPORT  = ["trackpant","track pant","jogginghose","trainingshose","sporthose",
    "jogger","sweatpant","hose","jogging","tracksuit","trainingsanzug","jogginganzug",
    "sportanzug","tuta","survetement","chandal","track suit","jogging set","sport set",
    "jacke","jacket","windbreaker","anorak","trainingsjacke","coach jacket","track jacket",
    "hoodie","hoody","sweatshirt","sweater","pullover","kapuzenpullover","crewneck","felpa",
    "t-shirt","tshirt","shirt","longsleeve","tee","maglietta","sportshirt",
    "trikot","jersey","football shirt","soccer shirt","fußballtrikot","kit"]
KW_POLOS   = ["polo","poloshirt","polo shirt","polo t-shirt","polo hemd","polo top"]
KW_JACKEN  = ["jacke","jacket","windbreaker","anorak","parka","übergangsjacke",
    "regenjacke","trainingsjacke","giubbotto","veste","blouson","cazadora",
    "chaqueta","coach jacket","track jacket","fleece","softshell",
    "half zip","quarter zip","full zip","winterjacke"]
KW_TRIKOTS = ["trikot","jersey","maglia","maillot","football shirt","soccer shirt",
    "fussballtrikot","fußballtrikot","sporttrikot","kit","spielertrikot"]
KW_GUERTEL = ["gürtel","belt","cintura","ceinture","cinturón","ledergürtel","stoffgürtel"]
KW_TASCHEN = ["tasche","bag","handtasche","umhängetasche","rucksack","backpack",
    "borsa","zaino","sac","bolso","mochila","tote","shopper"]
KW_CAPS    = ["cap","snapback","baseball cap","trucker cap","fitted cap","dad cap",
    "cappello","casquette","gorra","mütze","beanie","bucket hat"]

# ─── Filter ───────────────────────────────────────────────────────
VERBOTEN_KLEIDUNG = [
    "schuh","schuhe","stiefel","turnschuh","laufschuh","slipper","sandale","sandalen",
    "sneaker","sneakers","boots","loafer","pumps","ballerina","shoe","shoes","footwear",
    "scarpe","scarpa","zapato","zapatos","zapatilla","zapatillas",
    "chaussure","chaussures","schoen","schoenen",
    "air max","air force","dunk","yeezy","campus","gazelle","samba",
    "superstar","stan smith","ultraboost","nmd","converse","vans","timberland","ugg","crocs",
    "kinder","kinderjacke","kinderhose","kindershirt","baby","babykleidung","kleinkind",
    "kids","children","child","toddler","infant","newborn",
    "bambino","bambina","bambini","neonato","bimbo","bimba",
    "enfant","bébé","bebe","garçon","fille","niño","niña","infantil",
    "gr. 86","gr. 92","gr. 98","gr. 104","maat 86","maat 92","months old",
    "years old"," years,","ans,","anni,",
    "parfum","perfume","cologne","eau de","fragrance","duft","deo","deodorant",
    "uhr","watch","orologio","montre","reloj","armbanduhr",
    "schmuck","jewelry","kette","halskette","ring","ohrringe","armband","bracelet",
    "brille","sonnenbrille","sunglasses","lunette","occhiali",
    "portemonnaie","geldbeutel","wallet","gürteltasche","fanny pack",
    "socken","socks","strümpfe","unterwäsche","underwear","slip","boxershorts",
    "ball","fußball","basketball","handball","volleyball","rugby",
    "buch","book","spiel","game","spielzeug","toy","figur","figure",
    "poster","bild","picture","rahmen","frame","vase","kerze","candle",
    "handy","phone","iphone","samsung","laptop","tablet","kabel","cable",
    "schlüssel","keychain","anhänger","charm",
]

VERBOTEN_ACCESSOIRES = [
    "schuh","schuhe","sneaker","sneakers","boots","shoe","shoes",
    "scarpe","scarpa","zapato","zapatos","chaussure","schoen",
    "kinder","baby","kids","children","bambino","bambina","enfant","niño","niña",
]

VERBOTEN_GROESSEN = (
    {str(i) for i in range(16, 36)} |
    {"86","92","98","104","110","116","122","128","134","140","146","152","158","164","170",
     "0-3m","3-6m","6-9m","6-12m","9-12m","12-18m","18-24m",
     "1-2y","2-3y","3-4y","4-5y","5-6y","6-7y","7-8y","8-9y","9-10y","10-11y","11-12y",
     "1-2 years","2-3 years","3-4 years","3-5 years","4-5 years","5-6 years",
     "6-7 years","7-8 years","8-9 years","9-10 years","10-11 years","11-12 years",
     "12-13 years","13-14 years","53 cm","56 cm","62 cm","68 cm","74 cm","80 cm"}
)

# ─── Channel IDs ──────────────────────────────────────────────────
def ch(key): return int(os.getenv(key, 0))

CATEGORIES = [
    {"name":"Under 5€",        "brands":[NIKE],          "pmin":0.01, "pmax":5,    "kw":None,       "ch":ch("CHANNEL_UNDER_5"),      "color":0xFFD700, "typ":"kleidung"},
    {"name":"Under 5€ Adidas", "brands":[ADIDAS],        "pmin":0.01, "pmax":5,    "kw":None,       "ch":ch("CHANNEL_UNDER_5"),      "color":0xFFD700, "typ":"kleidung"},
    {"name":"Under 5€ Lacoste","brands":[LACOSTE],       "pmin":0.01, "pmax":5,    "kw":None,       "ch":ch("CHANNEL_UNDER_5"),      "color":0xFFD700, "typ":"kleidung"},
    {"name":"Under 5€ RL",     "brands":[RL],            "pmin":0.01, "pmax":5,    "kw":None,       "ch":ch("CHANNEL_UNDER_5"),      "color":0xFFD700, "typ":"kleidung"},
    {"name":"Under 5€ Tommy",  "brands":[TOMMY],         "pmin":0.01, "pmax":5,    "kw":None,       "ch":ch("CHANNEL_UNDER_5"),      "color":0xFFD700, "typ":"kleidung"},
    {"name":"Under 10€",       "brands":[NIKE],          "pmin":5.01, "pmax":10,   "kw":None,       "ch":ch("CHANNEL_UNDER_10"),     "color":0xFFD700, "typ":"kleidung"},
    {"name":"Under 10€ Adidas","brands":[ADIDAS],        "pmin":5.01, "pmax":10,   "kw":None,       "ch":ch("CHANNEL_UNDER_10"),     "color":0xFFD700, "typ":"kleidung"},
    {"name":"Under 10€ Lacoste","brands":[LACOSTE],      "pmin":5.01, "pmax":10,   "kw":None,       "ch":ch("CHANNEL_UNDER_10"),     "color":0xFFD700, "typ":"kleidung"},
    {"name":"Under 10€ RL",    "brands":[RL],            "pmin":5.01, "pmax":10,   "kw":None,       "ch":ch("CHANNEL_UNDER_10"),     "color":0xFFD700, "typ":"kleidung"},
    {"name":"Under 10€ Tommy", "brands":[TOMMY],         "pmin":5.01, "pmax":10,   "kw":None,       "ch":ch("CHANNEL_UNDER_10"),     "color":0xFFD700, "typ":"kleidung"},
    {"name":"Nike",            "brands":[NIKE],          "pmin":None, "pmax":20,   "kw":KW_SPORT,   "ch":ch("CHANNEL_NIKE"),         "color":0xF5821F, "typ":"kleidung"},
    {"name":"Adidas",          "brands":[ADIDAS],        "pmin":None, "pmax":20,   "kw":KW_SPORT,   "ch":ch("CHANNEL_ADIDAS"),       "color":0x000000, "typ":"kleidung"},
    {"name":"Lacoste",         "brands":[LACOSTE],       "pmin":None, "pmax":20,   "kw":KW_SPORT,   "ch":ch("CHANNEL_LACOSTE"),      "color":0x00A850, "typ":"kleidung"},
    {"name":"Ralph Lauren",    "brands":[RL],            "pmin":None, "pmax":15,   "kw":None,       "ch":ch("CHANNEL_RL"),           "color":0x002868, "typ":"kleidung"},
    {"name":"Fred Perry",      "brands":[FRED_PERRY],    "pmin":None, "pmax":13,   "kw":None,       "ch":ch("CHANNEL_FRED_PERRY"),   "color":0xCC0000, "typ":"kleidung"},
    {"name":"Lyle Scott",      "brands":[LYLE_SCOTT],    "pmin":None, "pmax":None, "kw":None,       "ch":ch("CHANNEL_LYLE_SCOTT"),   "color":0x1a1a2e, "typ":"kleidung"},
    {"name":"Lonsdale",        "brands":[LONSDALE],      "pmin":None, "pmax":None, "kw":None,       "ch":ch("CHANNEL_LONSDALE"),     "color":0xCC0000, "typ":"kleidung"},
    {"name":"CP Company",      "brands":[CP_COMPANY],    "pmin":None, "pmax":None, "kw":None,       "ch":ch("CHANNEL_CP_COMPANY"),   "color":0x1a1a1a, "typ":"kleidung"},
    {"name":"La Martina",      "brands":[LA_MARTINA],    "pmin":None, "pmax":None, "kw":None,       "ch":ch("CHANNEL_LA_MARTINA"),   "color":0x003580, "typ":"kleidung"},
    {"name":"Dolce Gabbana",   "brands":[DOLCE],         "pmin":None, "pmax":None, "kw":None,       "ch":ch("CHANNEL_DOLCE_GABBANA"),"color":0xFFD700, "typ":"kleidung"},
    {"name":"Armani",          "brands":[ARMANI],        "pmin":None, "pmax":None, "kw":None,       "ch":ch("CHANNEL_ARMANI"),       "color":0x1a1a1a, "typ":"kleidung"},
    {"name":"Diesel",          "brands":[DIESEL],        "pmin":None, "pmax":None, "kw":None,       "ch":ch("CHANNEL_DIESEL"),       "color":0xCC0000, "typ":"kleidung"},
    {"name":"Calvin Klein",    "brands":[CALVIN_KLEIN],  "pmin":None, "pmax":None, "kw":None,       "ch":ch("CHANNEL_CALVIN_KLEIN"), "color":0x000000, "typ":"kleidung"},
    {"name":"Tommy Hilfiger",  "brands":[TOMMY],         "pmin":None, "pmax":None, "kw":None,       "ch":ch("CHANNEL_TOMMY"),        "color":0xCC0000, "typ":"kleidung"},
    {"name":"Stone Island",    "brands":[STONE_ISLAND],  "pmin":None, "pmax":None, "kw":None,       "ch":ch("CHANNEL_STONE_ISLAND"), "color":0x1a1a1a, "typ":"kleidung"},
    {"name":"Burberry",        "brands":[BURBERRY],      "pmin":None, "pmax":None, "kw":None,       "ch":ch("CHANNEL_BURBERRY"),     "color":0xC4A45A, "typ":"kleidung"},
    {"name":"Moncler",         "brands":[MONCLER],       "pmin":None, "pmax":None, "kw":None,       "ch":ch("CHANNEL_MONCLER"),      "color":0x003580, "typ":"kleidung"},
    {"name":"Levis",           "brands":[LEVIS],         "pmin":None, "pmax":None, "kw":None,       "ch":ch("CHANNEL_LEVIS"),        "color":0xCC0000, "typ":"kleidung"},
    {"name":"Miss Me",         "brands":[MISS_ME],       "pmin":None, "pmax":None, "kw":None,       "ch":ch("CHANNEL_MISS_ME"),      "color":0x9b59b6, "typ":"kleidung"},
    {"name":"True Religion",   "brands":[TRUE_REL],      "pmin":None, "pmax":None, "kw":None,       "ch":ch("CHANNEL_TRUE_RELIGION"),"color":0x1a1a1a, "typ":"kleidung"},
    {"name":"G-Star",          "brands":[GSTAR],         "pmin":None, "pmax":None, "kw":None,       "ch":ch("CHANNEL_GSTAR"),        "color":0x000000, "typ":"kleidung"},
    {"name":"Trikot Mix",      "brands":[NIKE,ADIDAS],   "pmin":None, "pmax":20,   "kw":KW_TRIKOTS, "ch":ch("CHANNEL_TRIKOT_MIX"),  "color":0x09B1BA, "typ":"kleidung"},
    {"name":"Polo Mix",        "brands":[LACOSTE,RL,FRED_PERRY,LA_MARTINA,TOMMY], "pmin":None, "pmax":20, "kw":KW_POLOS, "ch":ch("CHANNEL_POLO_MIX"), "color":0x00A850, "typ":"kleidung"},
    {"name":"Jacken Mix",      "brands":[STONE_ISLAND,CP_COMPANY,MONCLER,BURBERRY,TOMMY,RL], "pmin":None, "pmax":35, "kw":KW_JACKEN, "ch":ch("CHANNEL_JACKEN_MIX"), "color":0x1a1a1a, "typ":"kleidung"},
    {"name":"Gürtel",          "brands":ALL_BRANDS,      "pmin":None, "pmax":None, "kw":KW_GUERTEL, "ch":ch("CHANNEL_GUERTEL"),      "color":0x8B4513, "typ":"accessoire"},
    {"name":"Taschen",         "brands":ALL_BRANDS,      "pmin":None, "pmax":None, "kw":KW_TASCHEN, "ch":ch("CHANNEL_TASCHEN"),      "color":0x8B4513, "typ":"accessoire"},
    {"name":"Caps",            "brands":ALL_BRANDS,      "pmin":None, "pmax":None, "kw":KW_CAPS,    "ch":ch("CHANNEL_CAPS"),         "color":0x8B4513, "typ":"accessoire"},
]

# ─── Seen IDs ─────────────────────────────────────────────────────
def load_seen() -> dict:
    try:
        with open(SEEN_FILE, "r") as f:
            data = json.load(f)
            return {k: set(v) for k, v in data.items()}
    except:
        return {}

def save_seen():
    try:
        with open(SEEN_FILE, "w") as f:
            json.dump({k: list(v) for k, v in seen_ids.items()}, f)
    except Exception as e:
        print(f"[Warnung] Speichern fehlgeschlagen: {e}")

seen_ids = load_seen()
for cat in CATEGORIES:
    if cat["name"] not in seen_ids:
        seen_ids[cat["name"]] = set()

global_seen: set[int] = {iid for s in seen_ids.values() for iid in s}
first_run      = True
cookie_session = None
cookie_counter = 0
COOKIE_REFRESH = 5
monitor_sessions: dict[int, dict] = {}

# ─── Image Grid ───────────────────────────────────────────────────
def make_image_grid(img_urls: list) -> io.BytesIO | None:
    try:
        images = []
        for url in img_urls[:3]:
            resp = requests.get(url, timeout=10)
            img  = Image.open(io.BytesIO(resp.content)).convert("RGB")
            img  = img.resize((400, 400))
            images.append(img)
        if not images:
            return None
        grid = Image.new("RGB", (400 * len(images), 400), (20, 20, 20))
        for i, img in enumerate(images):
            grid.paste(img, (i * 400, 0))
        buf = io.BytesIO()
        grid.save(buf, format="JPEG", quality=85)
        buf.seek(0)
        return buf
    except Exception as e:
        print(f"[Warnung] Grid Fehler: {e}")
        return None

# ─── API ──────────────────────────────────────────────────────────
VINTED_TOKEN = os.getenv("VINTED_TOKEN")
API_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    "Referer": "https://www.vinted.de/",
    "Origin": "https://www.vinted.de",
    "Connection": "keep-alive",
    "X-Requested-With": "XMLHttpRequest",
}
if VINTED_TOKEN:
    API_HEADERS["Authorization"] = VINTED_TOKEN

def refresh_session():
    global cookie_session
    s = requests.Session()
    try:
        s.get("https://www.vinted.de", headers={
            "User-Agent": API_HEADERS["User-Agent"],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
        }, proxies=PROXIES, timeout=10)
    except:
        pass
    cookie_session = s
    print("[Info] Session erneuert")

def _fetch(brand_ids, per_page=6):
    global cookie_session
    if cookie_session is None:
        refresh_session()
    params = [("order","newest_first"), ("per_page", str(per_page))]
    for b in brand_ids: params.append(("brand_ids[]", str(b)))
    for l in LAENDER:   params.append(("country_ids[]", l))
    url = "https://www.vinted.de/api/v2/catalog/items"
    r = cookie_session.get(url, headers=API_HEADERS, params=params, proxies=PROXIES, timeout=15)
    r.raise_for_status()
    if not r.text or r.text.strip() == "":
        refresh_session()
        return []
    try:
        return r.json().get("items", [])
    except:
        refresh_session()
        return []

async def fetch_items(brand_ids, per_page=6):
    try:
        return await asyncio.to_thread(_fetch, brand_ids, per_page)
    except Exception as e:
        print(f"[Fehler] {e}")
        await asyncio.sleep(30)
        return []

# ─── Filter ───────────────────────────────────────────────────────
def preis_ok(item, pmin, pmax):
    try:
        p = float(item.get("price", {}).get("amount", 0))
        if pmin and p < pmin: return False
        if pmax and p > pmax: return False
        return True
    except:
        return True

def keyword_ok(item, kw):
    if not kw: return True
    return any(k in item.get("title","").lower() for k in kw)

def groesse_ok(item):
    """Nur S bis XL erlaubt – für alle Kleidungs-Channels."""
    groesse = item.get("size_title","").strip().lower()
    if not groesse:
        return True  # Kein Größenangabe → durchlassen
    return groesse in ERLAUBTE_GROESSEN

def kleidung_ok(item):
    titel   = item.get("title","").lower()
    groesse = item.get("size_title","").strip().lower()
    land    = item.get("user",{}).get("country_iso","").upper()
    if any(v in titel for v in VERBOTEN_KLEIDUNG): return False
    if groesse in VERBOTEN_GROESSEN: return False
    if not groesse_ok(item): return False
    if land and land not in {"DE","AT","CH","IT","FR","ES"}: return False
    return True

def accessoire_ok(item):
    titel = item.get("title","").lower()
    land  = item.get("user",{}).get("country_iso","").upper()
    if any(v in titel for v in VERBOTEN_ACCESSOIRES): return False
    if land and land not in {"DE","AT","CH","IT","FR","ES"}: return False
    return True

def monitor_filter_ok(item, f: dict) -> bool:
    titel   = item.get("title","").lower()
    groesse = item.get("size_title","").strip().lower()
    preis   = float(item.get("price",{}).get("amount", 0))
    if any(v in titel for v in VERBOTEN_KLEIDUNG): return False
    if groesse in VERBOTEN_GROESSEN: return False
    if f.get("pmax") and preis > f["pmax"]: return False
    if f.get("pmin") and preis < f["pmin"]: return False
    if f.get("groesse") and f["groesse"].lower() not in groesse: return False
    if f.get("stichwort") and f["stichwort"].lower() not in titel: return False
    land = item.get("user",{}).get("country_iso","").upper()
    if land and land not in {"DE","AT","CH","IT","FR","ES"}: return False
    return True

# ─── Embed & Send ─────────────────────────────────────────────────
def build_embed(item, cat_name, cat_color):
    title     = item.get("title","Unbekannt")
    price     = item.get("price",{})
    pstr      = f"{price.get('amount','?')} {price.get('currency_code','EUR')}"
    url       = f"https://www.vinted.de/items/{item.get('id')}"
    imgs      = item.get("photos",[])
    brand     = item.get("brand_title","—")
    size      = item.get("size_title","—")
    status    = item.get("status","—")
    seller    = item.get("user",{}).get("login","—")
    seller_id = item.get("user",{}).get("id","")
    seller_url = f"https://www.vinted.de/member/{seller_id}"
    zustand_map = {
        "Neu mit Etikett":   "🔵 Neu mit Etikett",
        "Neu ohne Etikett":  "🟢 Neu ohne Etikett",
        "Sehr gut":          "🟡 Sehr gut",
        "Gut":               "🟠 Gut",
        "Zufriedenstellend": "🔴 Zufriedenstellend",
    }
    status_display = zustand_map.get(status, f"✨ {status}")
    e = discord.Embed(color=cat_color)
    e.set_author(name=f"{cat_name}  •  Vinted Snipebot",
                 icon_url="https://www.vinted.de/favicon.ico")
    e.title = f"**{title}**"
    e.url   = url
    e.description = f"## 💶  {pstr}\n━━━━━━━━━━━━━━━━━━━━━━━━"
    e.add_field(name="🏷️  Marke",     value=f"`{brand}`",                inline=True)
    e.add_field(name="📏  Größe",      value=f"`{size}`",                 inline=True)
    e.add_field(name="✨  Zustand",    value=status_display,              inline=True)
    e.add_field(name="👤  Verkäufer",  value=f"[{seller}]({seller_url})", inline=True)
    e.add_field(name="📦  Kategorie",  value=f"`{cat_name}`",            inline=True)
    e.add_field(name="‎",              value="‎",                         inline=True)
    e.add_field(name="🔗  Zum Artikel",value=f"**[➜ Auf Vinted ansehen]({url})**", inline=False)
    e.set_footer(text="Vinted Snipebot  •  VintedHub")
    return e, imgs

class ArtikelView(discord.ui.View):
    def __init__(self, url: str):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="🛍️ Auf Vinted ansehen", style=discord.ButtonStyle.link, url=url))
        self.add_item(discord.ui.Button(label="❤️ Favorisieren",        style=discord.ButtonStyle.link, url=url))
        self.add_item(discord.ui.Button(label="💳 Sofort kaufen",       style=discord.ButtonStyle.link, url=f"{url}#buy"))

async def send_item(channel, item, cat_name, cat_color):
    main_embed, imgs = build_embed(item, cat_name, cat_color)
    img_urls = [i.get("url","") for i in imgs[:3] if i.get("url")]
    view     = ArtikelView(url=f"https://www.vinted.de/items/{item.get('id')}")
    if len(img_urls) > 1:
        grid = await asyncio.to_thread(make_image_grid, img_urls)
        if grid:
            main_embed.set_image(url="attachment://grid.jpg")
            await channel.send(embed=main_embed, file=discord.File(grid, filename="grid.jpg"), view=view)
            return
    if img_urls:
        main_embed.set_image(url=img_urls[0])
    await channel.send(embed=main_embed, view=view)

# ─── Bot ──────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
bot  = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ─── Slash Commands ───────────────────────────────────────────────
@tree.command(name="monitor", description="Erstelle deinen privaten Vinted Monitor Channel")
@app_commands.describe(
    marke="Markenname (z.B. Nike, Adidas, Lacoste...)",
    max_preis="Maximaler Preis in € (z.B. 20)",
    groesse="Größe filtern (z.B. M, L, XL) – optional",
    stichwort="Stichwort im Titel (z.B. hoodie) – optional"
)
async def monitor_cmd(interaction: discord.Interaction, marke: str, max_preis: float,
                      groesse: str = "", stichwort: str = ""):
    user  = interaction.user
    guild = interaction.guild

    if user.id in monitor_sessions:
        sess   = monitor_sessions[user.id]
        ch_obj = guild.get_channel(sess["channel_id"])
        if ch_obj:
            await interaction.response.send_message(
                f"❌ Du hast bereits einen aktiven Monitor: {ch_obj.mention}\n"
                f"Noch **{int((sess['expires_at'] - time.time()) / 60)} Minuten** aktiv.",
                ephemeral=True)
            return

    brand_id = BRAND_MAP.get(marke.lower())
    if not brand_id:
        await interaction.response.send_message(
            f"❌ Marke `{marke}` nicht gefunden.\nVerfügbar: " +
            ", ".join([f"`{k}`" for k in sorted(BRAND_MAP.keys())]),
            ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    category = guild.get_channel(MONITOR_CAT_ID) if MONITOR_CAT_ID else None
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        user:               discord.PermissionOverwrite(read_messages=True, send_messages=False),
        guild.me:           discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }
    channel_name = f"🔍-monitor-{user.name}".lower().replace(" ", "-")[:100]
    new_channel  = await guild.create_text_channel(
        name=channel_name, category=category, overwrites=overwrites,
        topic=f"Privater Monitor für {user.name} | {marke} | Max {max_preis}€")

    expires_at = time.time() + MONITOR_TTL
    monitor_sessions[user.id] = {
        "channel_id": new_channel.id,
        "brand_id":   brand_id,
        "marke":      marke,
        "pmax":       max_preis,
        "pmin":       None,
        "groesse":    groesse,
        "stichwort":  stichwort,
        "expires_at": expires_at,
        "seen":       set(),
    }

    info = discord.Embed(title="🔍 Dein privater Vinted Monitor", color=0x09B1BA,
                         description="Neue Artikel werden hier automatisch gepostet!")
    info.add_field(name="🏷️ Marke",    value=f"`{marke}`",             inline=True)
    info.add_field(name="💶 Max Preis", value=f"`{max_preis}€`",        inline=True)
    info.add_field(name="📏 Größe",     value=f"`{groesse or 'Alle'}`", inline=True)
    info.add_field(name="🔎 Stichwort", value=f"`{stichwort or 'Keins'}`", inline=True)
    info.add_field(name="⏱️ Läuft ab", value=f"<t:{int(expires_at)}:R>",inline=True)
    info.set_footer(text="Channel wird nach 5 Stunden automatisch gelöscht.")
    await new_channel.send(embed=info)
    await interaction.followup.send(
        f"✅ Dein Monitor wurde erstellt: {new_channel.mention}\nLäuft **5 Stunden**.", ephemeral=True)
    print(f"[Monitor] {user.name} → {marke} max {max_preis}€")

@tree.command(name="monitor-loeschen", description="Lösche deinen privaten Monitor Channel")
async def monitor_delete_cmd(interaction: discord.Interaction):
    user  = interaction.user
    guild = interaction.guild
    if user.id not in monitor_sessions:
        await interaction.response.send_message("❌ Du hast keinen aktiven Monitor.", ephemeral=True)
        return
    sess   = monitor_sessions.pop(user.id)
    ch_obj = guild.get_channel(sess["channel_id"])
    if ch_obj:
        await interaction.response.send_message("✅ Monitor wird gelöscht...", ephemeral=True)
        await asyncio.sleep(2)
        await ch_obj.delete()
    else:
        await interaction.response.send_message("✅ Monitor gelöscht!", ephemeral=True)

@bot.command(name="sync")
async def sync_cmd(ctx):
    guild = discord.Object(id=GUILD_ID)
    tree.copy_global_to(guild=guild)
    await tree.sync(guild=guild)
    await ctx.send("✅ Slash Commands synchronisiert!")

# ─── Loops ────────────────────────────────────────────────────────
@tasks.loop(minutes=1)
async def cleanup_monitors():
    now = time.time()
    to_delete = [uid for uid, s in monitor_sessions.items() if now >= s["expires_at"]]
    for uid in to_delete:
        sess = monitor_sessions.pop(uid)
        for guild in bot.guilds:
            ch_obj = guild.get_channel(sess["channel_id"])
            if ch_obj:
                try:
                    await ch_obj.send("⏱️ **Session abgelaufen.** Channel wird in 10 Sekunden gelöscht. Erstelle mit `/monitor` eine neue Session!")
                    await asyncio.sleep(10)
                    await ch_obj.delete()
                except:
                    pass

@tasks.loop(seconds=55)
async def check_monitors():
    if first_run:
        return
    for uid, sess in list(monitor_sessions.items()):
        try:
            items = await fetch_items([sess["brand_id"]], per_page=10)
        except Exception as e:
            print(f"[Monitor Fehler] Fetch: {e}")
            continue
        for item in items:
            iid = item.get("id")
            if not iid or iid in sess["seen"]:
                continue
            sess["seen"].add(iid)
            if not monitor_filter_ok(item, sess):
                continue
            ch_obj = bot.get_channel(sess["channel_id"])
            if not ch_obj:
                continue
            try:
                await send_item(ch_obj, item, f"🔍 Monitor • {sess['marke']}", 0x09B1BA)
                print(f"[Monitor] ✅ {sess['marke']} → {item.get('title')}")
            except Exception as e:
                print(f"[Monitor Fehler] Send: {e}")

def get_brand_requests():
    seen, result = set(), []
    for cat in CATEGORIES:
        key = tuple(sorted(cat["brands"]))
        if key not in seen:
            seen.add(key)
            result.append(cat["brands"])
    return result

@tasks.loop(seconds=55)
async def check_all():
    global first_run, cookie_counter, global_seen

    cookie_counter += 1
    if cookie_counter >= COOKIE_REFRESH:
        cookie_counter = 0
        await asyncio.to_thread(refresh_session)

    for brand_ids in get_brand_requests():
        try:
            await asyncio.sleep(REQUEST_DELAY)
            items = await fetch_items(brand_ids, per_page=6)
        except Exception as e:
            print(f"[Fehler] Anfrage übersprungen: {e}")
            continue

        for item in items:
            iid = item.get("id")
            if not iid or iid in global_seen:
                continue
            global_seen.add(iid)
            posted = False

            for cat in CATEGORIES:
                if tuple(sorted(cat["brands"])) != tuple(sorted(brand_ids)):
                    continue
                if cat["ch"] == 0:
                    continue
                if iid in seen_ids[cat["name"]]:
                    continue
                if not preis_ok(item, cat["pmin"], cat["pmax"]):
                    continue
                if not keyword_ok(item, cat["kw"]):
                    continue
                if cat["typ"] == "kleidung" and not kleidung_ok(item):
                    continue
                if cat["typ"] == "accessoire" and not accessoire_ok(item):
                    continue

                seen_ids[cat["name"]].add(iid)
                if first_run:
                    continue

                channel = bot.get_channel(cat["ch"])
                if not channel:
                    continue

                try:
                    await send_item(channel, item, cat["name"], cat["color"])
                    print(f"✅ [{cat['name']}] {item.get('title')}")
                    posted = True
                except Exception as e:
                    print(f"[Fehler] [{cat['name']}]: {e}")

            if posted:
                save_seen()

    first_run = False

@bot.event
async def on_ready():
    print(f"✅ Snipebot online: {bot.user}")
    print(f"📦 {len(CATEGORIES)} Kategorien | 55s Intervall")
    for cat in CATEGORIES:
        print(f"   {'✅' if cat['ch'] != 0 else '❌'} {cat['name']}")
    guild = discord.Object(id=GUILD_ID)
    tree.copy_global_to(guild=guild)
    await tree.sync(guild=guild)
    print("✅ Slash Commands synchronisiert")
    check_all.start()
    cleanup_monitors.start()
    check_monitors.start()

bot.run(DISCORD_TOKEN)
