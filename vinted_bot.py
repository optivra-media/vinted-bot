"""
Vinted Snipebot – Smart System
================================
- Jede Marke wird einmal pro Runde abgefragt (5 Anfragen total)
- Artikel werden intelligent auf Channels verteilt (kein Doppelpost)
- Priorität: Keyword-Channel > Preis-Channel > Alles-Channel
- Tagsüber schnell, nachts langsam
- Gesehene IDs werden gespeichert (kein Doppelpost nach Neustart)
"""

import discord
from discord.ext import tasks
import requests
import asyncio
import json
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
PROXY_URL     = os.getenv("PROXY_URL")
PROXIES       = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None
SEEN_FILE     = "seen_ids.json"
REQUEST_DELAY = 5  # Sekunden zwischen Marken-Anfragen

# ─── Zeitbasiertes Interval ───────────────────────────────────────
def get_interval() -> int:
    from datetime import datetime
    h = datetime.now().hour
    if 2 <= h < 13:
        return 1200  # 20 Min nachts (02:00–13:00)
    return 60        # 1 Min tagsüber (13:00–02:00)

# ─── Vinted Einstellungen ─────────────────────────────────────────
LAENDER = ["7", "193", "195", "10", "6", "13"]  # DE, AT, CH, IT, FR, ES

NIKE    = 53
ADIDAS  = 14
LACOSTE = 304
RL      = 88
TRIKOT_BRANDS = [53, 14, 304, 88, 316, 103, 254]

# ─── Keywords ─────────────────────────────────────────────────────
KW_TRACKPANTS = ["trackpant","track pant","jogginghose","trainingshose","sporthose",
    "jogger","sweatpant","joggingbroek","pantalon","pantalone","track hose",
    "trackhose","hose","broek","jogging","training pant"]
KW_TRACKSUITS = ["tracksuit","trainingsanzug","jogginganzug","sportanzug","tuta",
    "survêtement","survetement","chandal","trainingspak","track suit",
    "jogging set","sport set","2 teilig","2-teilig","full set","ensemble"]
KW_JACKEN     = ["jacke","jacket","windbreaker","anorak","parka","übergangsjacke",
    "regenjacke","trainingsjacke","zip","giubbotto","veste","blouson",
    "cazadora","chaqueta","coach jacket","track jacket","trackjacket",
    "fleece","softshell","half zip","quarter zip","full zip","winterjacke"]
KW_SHIRTS     = ["t-shirt","tshirt","shirt","longsleeve","long sleeve","tee",
    "maglietta","maglia","t shirt","kurzarm","oberteil","chemise","camiseta"]
KW_HOODIES    = ["hoodie","hoody","sweatshirt","sweater","pullover","pulli",
    "kapuzenpullover","crewneck","crew neck","felpa","sweat","sudadera","kapuze"]
KW_POLOS      = ["polo","poloshirt","polo shirt","polo t-shirt","polo hemd","polo top"]
KW_TRIKOTS     = ["trikot","jersey","maglia","maillot","football shirt","soccer shirt",
    "fussballtrikot","fußballtrikot","sporttrikot","kit","spielertrikot"]
KW_TRIKOT_HOSE = ["trikot hose","football shorts","soccer shorts","fußballshorts",
    "sport shorts","kurze hose","shorts"]
KW_TRIKOT_SET  = ["trikot set","jersey set","football kit","soccer kit","trikot komplett"]

# ─── Filter ───────────────────────────────────────────────────────
VERBOTEN = [
    "schuh","schuhe","stiefel","turnschuh","laufschuh","slipper","sandale","sandalen",
    "sneaker","sneakers","boots","loafer","pumps","ballerina","shoe","shoes","footwear",
    "scarpe","scarpa","stivaletti","zapato","zapatos","zapatilla","zapatillas",
    "chaussure","chaussures","basket","baskets","schoen","schoenen",
    "air max","air force","dunk","yeezy","campus","gazelle","samba",
    "superstar","stan smith","ultraboost","nmd","converse","vans","timberland",
    "ugg","crocs","birkenstock",
    "kinder","kinderjacke","kinderhose","kindershirt","kindermode",
    "baby","babykleidung","babyjacke","babyhose","babybody","kleinkind",
    "kids","children","child","toddler","infant","newborn",
    "bambino","bambina","bambini","neonato","neonata","bimbo","bimba",
    "enfant","bébé","bebe","garçon","fille","niño","niña","infantil",
    "gr. 86","gr. 92","gr. 98","gr. 104","gr. 110","gr. 116","gr. 122",
    "maat 86","maat 92","maat 98","taille 86","taille 92","months old",
    "tasche","bag","rucksack","backpack","cap","mütze","beanie",
    "gürtel","belt","schal","socken","socks","handschuhe",
    "uhr","watch","schmuck","kette","ring","brille","parfum",
    "ball","fußball","basketball","handball",
]

VERBOTEN_GROESSEN = (
    {str(i) for i in range(16, 36)} |
    {"86","92","98","104","110","116","122","128","134","140","146","152","158","164","170",
     "0-3m","3-6m","6-9m","6-12m","9-12m","12-18m","18-24m",
     "1-2y","2-3y","3-4y","4-5y","5-6y","6-7y","7-8y","8-9y","9-10y","10-11y","11-12y"}
)

# ─── Channel IDs ──────────────────────────────────────────────────
def ch(key): return int(os.getenv(key, 0))

CATEGORIES = [
    # NIKE – Keyword Channels (Priorität 1)
    {"name":"Nike – Trackpants",   "brands":[NIKE],  "pmin":None,  "pmax":None, "kw":KW_TRACKPANTS, "ch":ch("CHANNEL_NIKE_TRACKPANTS"),  "color":0xF5821F},
    {"name":"Nike – Tracksuits",   "brands":[NIKE],  "pmin":None,  "pmax":None, "kw":KW_TRACKSUITS, "ch":ch("CHANNEL_NIKE_TRACKSUITS"),  "color":0xF5821F},
    {"name":"Nike – Jacken",       "brands":[NIKE],  "pmin":None,  "pmax":None, "kw":KW_JACKEN,     "ch":ch("CHANNEL_NIKE_JACKEN"),      "color":0xF5821F},
    {"name":"Nike – Shirts",       "brands":[NIKE],  "pmin":None,  "pmax":None, "kw":KW_SHIRTS,     "ch":ch("CHANNEL_NIKE_SHIRTS"),      "color":0xF5821F},
    {"name":"Nike – Hoodies",      "brands":[NIKE],  "pmin":None,  "pmax":None, "kw":KW_HOODIES,    "ch":ch("CHANNEL_NIKE_HOODIES"),     "color":0xF5821F},
    {"name":"Nike – Polos",        "brands":[NIKE],  "pmin":None,  "pmax":None, "kw":KW_POLOS,      "ch":ch("CHANNEL_NIKE_POLOS"),       "color":0xF5821F},
    # NIKE – Preis Channels (Priorität 2)
    {"name":"Nike – 0-10€",        "brands":[NIKE],  "pmin":0.01,  "pmax":10,   "kw":None,          "ch":ch("CHANNEL_NIKE_10"),          "color":0xF5821F},
    {"name":"Nike – 10-20€",       "brands":[NIKE],  "pmin":10.01, "pmax":20,   "kw":None,          "ch":ch("CHANNEL_NIKE_20"),          "color":0xF5821F},
    # NIKE – Alles Channel (Priorität 3)
    {"name":"Nike – Alles",        "brands":[NIKE],  "pmin":None,  "pmax":None, "kw":None,          "ch":ch("CHANNEL_NIKE"),             "color":0xF5821F},

    # ADIDAS – Keyword Channels
    {"name":"Adidas – Trackpants", "brands":[ADIDAS],"pmin":None,  "pmax":None, "kw":KW_TRACKPANTS, "ch":ch("CHANNEL_ADIDAS_TRACKPANTS"),"color":0x000000},
    {"name":"Adidas – Tracksuits", "brands":[ADIDAS],"pmin":None,  "pmax":None, "kw":KW_TRACKSUITS, "ch":ch("CHANNEL_ADIDAS_TRACKSUITS"),"color":0x000000},
    {"name":"Adidas – Jacken",     "brands":[ADIDAS],"pmin":None,  "pmax":None, "kw":KW_JACKEN,     "ch":ch("CHANNEL_ADIDAS_JACKEN"),    "color":0x000000},
    {"name":"Adidas – Shirts",     "brands":[ADIDAS],"pmin":None,  "pmax":None, "kw":KW_SHIRTS,     "ch":ch("CHANNEL_ADIDAS_SHIRTS"),    "color":0x000000},
    {"name":"Adidas – Hoodies",    "brands":[ADIDAS],"pmin":None,  "pmax":None, "kw":KW_HOODIES,    "ch":ch("CHANNEL_ADIDAS_HOODIES"),   "color":0x000000},
    {"name":"Adidas – Polos",      "brands":[ADIDAS],"pmin":None,  "pmax":None, "kw":KW_POLOS,      "ch":ch("CHANNEL_ADIDAS_POLOS"),     "color":0x000000},
    # ADIDAS – Preis Channels
    {"name":"Adidas – 0-15€",      "brands":[ADIDAS],"pmin":0.01,  "pmax":15,   "kw":None,          "ch":ch("CHANNEL_ADIDAS_15"),        "color":0x000000},
    {"name":"Adidas – 15-40€",     "brands":[ADIDAS],"pmin":15.01, "pmax":40,   "kw":None,          "ch":ch("CHANNEL_ADIDAS_40"),        "color":0x000000},
    # ADIDAS – Alles
    {"name":"Adidas – Alles",      "brands":[ADIDAS],"pmin":None,  "pmax":None, "kw":None,          "ch":ch("CHANNEL_ADIDAS"),           "color":0x000000},

    # LACOSTE – Keyword Channels
    {"name":"Lacoste – Trackpants","brands":[LACOSTE],"pmin":None, "pmax":None, "kw":KW_TRACKPANTS, "ch":ch("CHANNEL_LACOSTE_TRACKPANTS"),"color":0x00A850},
    {"name":"Lacoste – Tracksuits","brands":[LACOSTE],"pmin":None, "pmax":None, "kw":KW_TRACKSUITS, "ch":ch("CHANNEL_LACOSTE_TRACKSUITS"),"color":0x00A850},
    {"name":"Lacoste – Jacken",    "brands":[LACOSTE],"pmin":None, "pmax":None, "kw":KW_JACKEN,     "ch":ch("CHANNEL_LACOSTE_JACKEN"),   "color":0x00A850},
    {"name":"Lacoste – Shirts",    "brands":[LACOSTE],"pmin":None, "pmax":None, "kw":KW_SHIRTS,     "ch":ch("CHANNEL_LACOSTE_SHIRTS"),   "color":0x00A850},
    {"name":"Lacoste – Hoodies",   "brands":[LACOSTE],"pmin":None, "pmax":None, "kw":KW_HOODIES,    "ch":ch("CHANNEL_LACOSTE_HOODIES"),  "color":0x00A850},
    {"name":"Lacoste – Polos",     "brands":[LACOSTE],"pmin":None, "pmax":None, "kw":KW_POLOS,      "ch":ch("CHANNEL_LACOSTE_POLOS"),    "color":0x00A850},
    # LACOSTE – Preis Channels
    {"name":"Lacoste – 0-10€",     "brands":[LACOSTE],"pmin":0.01, "pmax":10,   "kw":None,          "ch":ch("CHANNEL_LACOSTE_10"),       "color":0x00A850},
    {"name":"Lacoste – 10-20€",    "brands":[LACOSTE],"pmin":10.01,"pmax":20,   "kw":None,          "ch":ch("CHANNEL_LACOSTE_20"),       "color":0x00A850},
    {"name":"Lacoste – 20-40€",    "brands":[LACOSTE],"pmin":20.01,"pmax":40,   "kw":None,          "ch":ch("CHANNEL_LACOSTE_40"),       "color":0x00A850},
    # LACOSTE – Alles
    {"name":"Lacoste – Alles",     "brands":[LACOSTE],"pmin":None, "pmax":None, "kw":None,          "ch":ch("CHANNEL_LACOSTE"),          "color":0x00A850},

    # RALPH LAUREN – Keyword Channels
    {"name":"Ralph Lauren – Polos",    "brands":[RL],"pmin":None,  "pmax":None, "kw":KW_POLOS,      "ch":ch("CHANNEL_RL_POLOS"),     "color":0x002868},
    {"name":"Ralph Lauren – Jacken",   "brands":[RL],"pmin":None,  "pmax":None, "kw":KW_JACKEN,     "ch":ch("CHANNEL_RL_JACKEN"),    "color":0x002868},
    {"name":"Ralph Lauren – Tracksuit","brands":[RL],"pmin":None,  "pmax":None, "kw":KW_TRACKSUITS, "ch":ch("CHANNEL_RL_TRACKSUIT"), "color":0x002868},
    # RALPH LAUREN – Preis Channels
    {"name":"Ralph Lauren – 0-10€",    "brands":[RL],"pmin":0.01,  "pmax":10,   "kw":None,          "ch":ch("CHANNEL_RL_10"),        "color":0x002868},
    {"name":"Ralph Lauren – 10-20€",   "brands":[RL],"pmin":10.01, "pmax":20,   "kw":None,          "ch":ch("CHANNEL_RL_20"),        "color":0x002868},
    {"name":"Ralph Lauren – 20-40€",   "brands":[RL],"pmin":20.01, "pmax":40,   "kw":None,          "ch":ch("CHANNEL_RL_40"),        "color":0x002868},
    # RALPH LAUREN – Alles
    {"name":"Ralph Lauren – Alles",    "brands":[RL],"pmin":None,  "pmax":None, "kw":None,          "ch":ch("CHANNEL_RL"),           "color":0x002868},

    # TRIKOTS
    {"name":"Trikots – Hose",  "brands":TRIKOT_BRANDS,"pmin":None,"pmax":None,"kw":KW_TRIKOT_HOSE,"ch":ch("CHANNEL_TRIKOTS_HOSE"),"color":0x09B1BA},
    {"name":"Trikots – Set",   "brands":TRIKOT_BRANDS,"pmin":None,"pmax":None,"kw":KW_TRIKOT_SET, "ch":ch("CHANNEL_TRIKOTS_SET"), "color":0x09B1BA},
    {"name":"Trikots – Alles", "brands":TRIKOT_BRANDS,"pmin":None,"pmax":None,"kw":KW_TRIKOTS,    "ch":ch("CHANNEL_TRIKOTS"),     "color":0x09B1BA},
]

# ─── Seen IDs (persistent) ────────────────────────────────────────
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

# Globale gesehene IDs (verhindert Doppelpost über alle Channels)
global_seen: set[int] = {iid for s in seen_ids.values() for iid in s}
first_run = True
cookie_session = None
cookie_counter = 0
COOKIE_REFRESH = 5

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

def _fetch(brand_ids, per_page=10):
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

async def fetch_items(brand_ids, per_page=10):
    try:
        return await asyncio.to_thread(_fetch, brand_ids, per_page)
    except Exception as e:
        print(f"[Fehler] {e}")
        await asyncio.sleep(30)  # 30s warten bei Fehler
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

def kleidung_ok(item):
    titel   = item.get("title","").lower()
    groesse = item.get("size_title","").strip().lower()
    land    = item.get("user",{}).get("country_iso","").upper()
    if any(v in titel for v in VERBOTEN): return False
    if groesse in VERBOTEN_GROESSEN: return False
    if land and land not in {"DE","AT","CH","IT","FR","ES"}: return False
    return True

def find_best_channel(item, brand_ids):
    """Findet den spezifischsten passenden Channel."""
    # Priorität 1: Keyword-Channel
    for cat in CATEGORIES:
        if cat["brands"] != brand_ids and not (len(cat["brands"]) > 1 and brand_ids == TRIKOT_BRANDS):
            continue
        if cat["kw"] is None: continue
        if cat["ch"] == 0: continue
        if not preis_ok(item, cat["pmin"], cat["pmax"]): continue
        if keyword_ok(item, cat["kw"]):
            return cat

    # Priorität 2: Preis-Channel
    for cat in CATEGORIES:
        if cat["brands"] != brand_ids and not (len(cat["brands"]) > 1 and brand_ids == TRIKOT_BRANDS):
            continue
        if cat["kw"] is not None: continue
        if cat["pmin"] is None: continue
        if cat["ch"] == 0: continue
        if preis_ok(item, cat["pmin"], cat["pmax"]):
            return cat

    # Priorität 3: Alles-Channel
    for cat in CATEGORIES:
        if cat["brands"] != brand_ids and not (len(cat["brands"]) > 1 and brand_ids == TRIKOT_BRANDS):
            continue
        if cat["kw"] is not None: continue
        if cat["pmin"] is not None: continue
        if cat["ch"] == 0: continue
        return cat

    return None

# ─── Embed ────────────────────────────────────────────────────────
def build_embed(item, cat):
    title = item.get("title","Unbekannt")
    price = item.get("price",{})
    pstr  = f"{price.get('amount','?')} {price.get('currency_code','EUR')}"
    url   = f"https://www.vinted.de/items/{item.get('id')}"
    imgs  = item.get("photos",[])
    img   = imgs[0].get("url") if imgs else None
    e = discord.Embed(title=f"🛍️ {title}", url=url, color=cat["color"],
                      description=f"**{cat['name']}**")
    e.add_field(name="💶 Preis",     value=pstr,                                  inline=True)
    e.add_field(name="📏 Größe",     value=item.get("size_title","—"),            inline=True)
    e.add_field(name="✨ Zustand",   value=item.get("status","—"),                inline=True)
    e.add_field(name="👤 Verkäufer", value=item.get("user",{}).get("login","—"),  inline=True)
    e.add_field(name="🔗 Artikel",   value=f"[Auf Vinted ansehen]({url})",        inline=False)
    if img: e.set_image(url=img)
    e.set_footer(text=f"Vinted Snipebot • {cat['name']}")
    return e

# ─── Bot ──────────────────────────────────────────────────────────
intents = discord.Intents.default()
client  = discord.Client(intents=intents)

BRAND_REQUESTS = [
    [NIKE],
    [ADIDAS],
    [LACOSTE],
    [RL],
    TRIKOT_BRANDS,
]

@tasks.loop(seconds=60)
async def check_all():
    global first_run, cookie_counter, global_seen

    # Interval dynamisch anpassen
    interval = get_interval()
    if check_all.seconds != interval:
        check_all.change_interval(seconds=interval)
        print(f"[Info] Interval → {interval}s")

    # Cookie erneuern
    cookie_counter += 1
    if cookie_counter >= COOKIE_REFRESH:
        cookie_counter = 0
        await asyncio.to_thread(refresh_session)

    for brand_ids in BRAND_REQUESTS:
        try:
            await asyncio.sleep(REQUEST_DELAY)
            items = await fetch_items(brand_ids, per_page=10)
        except Exception as e:
            print(f"[Fehler] Anfrage übersprungen: {e}")
            continue

        for item in items:
            iid = item.get("id")
            if not iid or iid in global_seen:
                continue
            if not kleidung_ok(item):
                global_seen.add(iid)
                continue

            cat = find_best_channel(item, brand_ids)
            if not cat:
                global_seen.add(iid)
                continue

            global_seen.add(iid)
            seen_ids[cat["name"]].add(iid)

            if first_run:
                continue

            channel = client.get_channel(cat["ch"])
            if not channel:
                continue

            try:
                await channel.send(embed=build_embed(item, cat))
                print(f"✅ [{cat['name']}] {item.get('title')}")
                save_seen()
            except Exception as e:
                print(f"[Fehler] [{cat['name']}]: {e}")

    first_run = False

@client.event
async def on_ready():
    print(f"✅ Snipebot online: {client.user}")
    print(f"📦 {len(CATEGORIES)} Kategorien")
    for cat in CATEGORIES:
        print(f"   {'✅' if cat['ch'] != 0 else '❌'} {cat['name']}")
    check_all.start()

client.run(DISCORD_TOKEN)
