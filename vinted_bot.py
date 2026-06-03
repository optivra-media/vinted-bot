import discord
from discord.ext import tasks
import requests
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN  = os.getenv("DISCORD_TOKEN")
PROXY_URL      = os.getenv("PROXY_URL")
CHECK_INTERVAL = 60   # Basis-Interval (wird dynamisch angepasst)
REQUEST_DELAY  = 8    # 8 Sekunden zwischen Anfragen

def get_interval() -> int:
    from datetime import datetime
    h = datetime.now().hour
    if 2 <= h < 13:
        return 1200  # 20 Minuten nachts
    return 60        # 1 Minute tagsüber

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept":          "application/json",
    "Accept-Language": "de-DE,de;q=0.9",
}

PROXIES = None  # Kein Proxy – Render.com IPs werden nicht geblockt
LAENDER = ["7", "193", "195", "10", "6", "13"]

NIKE    = 53
ADIDAS  = 14
LACOSTE = 304  # Korrekte Lacoste Brand ID
RL      = 88
TRIKOT_BRANDS = [53, 14, 98, 88, 316, 103, 254]

KW_TRACKPANTS = ["trackpant","track pant","jogginghose","trainingshose","sporthose",
    "jogger","sweatpant","joggingbroek","pantalon","pantalone","pantalones",
    "tuta pantalone","track hose","trackhose","hose","broek","jogging","training pant"]
KW_TRACKSUITS = ["tracksuit","trainingsanzug","jogginganzug","sportanzug","tuta",
    "survêtement","survetement","chandal","trainingspak","track suit",
    "jogging set","sport set","2 teilig","2-teilig","full set","set completo","ensemble"]
KW_JACKEN = ["jacke","jacket","windbreaker","anorak","parka","übergangsjacke",
    "regenjacke","trainingsjacke","zip","giubbotto","veste","blouson",
    "cazadora","chaqueta","coach jacket","track jacket","trackjacket",
    "fleece","softshell","half zip","quarter zip","full zip","winterjacke","sportjacke"]
KW_SHIRTS = ["t-shirt","tshirt","shirt","longsleeve","long sleeve","tee",
    "maglietta","maglia","t shirt","kurzarm","oberteil","chemise","camiseta","camisa","sportshirt"]
KW_HOODIES = ["hoodie","hoody","sweatshirt","sweater","pullover","pulli",
    "kapuzenpullover","crewneck","crew neck","felpa","sweat","sudadera","trui","kapuze"]
KW_POLOS   = ["polo","poloshirt","polo shirt","polo t-shirt","polo hemd","polo top"]
KW_TRIKOTS     = ["trikot","jersey","maglia","maillot","football shirt","soccer shirt",
    "fussballtrikot","fußballtrikot","sporttrikot","kit","spielertrikot"]
KW_TRIKOT_HOSE = ["trikot hose","football shorts","soccer shorts","fußballshorts",
    "pantaloncini","sport shorts","kurze hose","shorts"]
KW_TRIKOT_SET  = ["trikot set","jersey set","football kit","soccer kit","trikot komplett"]

VERBOTEN = [
    # Schuhe Deutsch
    "schuh","schuhe","stiefel","turnschuh","laufschuh","slipper",
    "sandale","sandalen","hausschuh","clogs","absatz",
    # Schuhe Englisch
    "sneaker","sneakers","boots","loafer","pumps","ballerina",
    "shoe","shoes","footwear","trainers",
    # Schuhe Italienisch/Spanisch/Französisch/Niederländisch
    "scarpe","scarpa","stivaletti","stivali","sandali",
    "zapato","zapatos","zapatilla","zapatillas","bota","botas",
    "chaussure","chaussures","basket","baskets","schoen","schoenen",
    # Schuh-Modelle
    "air max","air force","dunk","yeezy","campus","gazelle",
    "samba","superstar","stan smith","ultraboost","nmd",
    "converse","vans","timberland","ugg","crocs","birkenstock",
    # Kinder Deutsch
    "kinder","kinderjacke","kinderhose","kindershirt","kindermode",
    "baby","babykleidung","babyjacke","babyhose","babybody",
    "kleinkind","neugeboren","newborn","junge ","mädchen ",
    # Kinder Englisch
    "kids","children","child","toddler","infant","newborn",
    "boys ","girls ","baby boy","baby girl",
    # Kinder Italienisch
    "bambino","bambina","bambini","neonato","neonata",
    "bimbo","bimba","ragazzo","ragazza",
    # Kinder Niederländisch/Französisch/Spanisch
    "kinderen","meisje","jongen","enfant","bébé","bebe",
    "garçon","fille","niño","niña","infantil",
    # Kindergrößen im Titel
    "gr. 86","gr. 92","gr. 98","gr. 104","gr. 110","gr. 116",
    "gr. 122","gr. 128","gr. 134","gr. 140","gr. 146","gr. 152",
    "size 86","size 92","size 98","taille 86","taille 92",
    "maat 86","maat 92","maat 98","mois","months old",
    # Accessoires & Sonstiges
    "tasche","bag","rucksack","backpack","handtasche",
    "cap","mütze","beanie","hut","snapback",
    "gürtel","belt","schal","socken","socks","strümpfe",
    "handschuhe","gloves","unterwäsche","underwear",
    "uhr","watch","schmuck","kette","ring","armband","ohrringe",
    "brille","sunglasses","parfum","cologne",
    "ball","fußball","basketball","handball",
]

VERBOTEN_GROESSEN = (
    {str(i) for i in range(16, 36)} |
    {"86","92","98","104","110","116","122","128",
     "134","140","146","152","158","164","170",
     "0-3m","3-6m","6-9m","6-12m","9-12m","12-18m",
     "18-24m","1-2y","2-3y","3-4y","4-5y","5-6y",
     "6-7y","7-8y","8-9y","9-10y","10-11y","11-12y",}
)

def ch(key): return int(os.getenv(key, 0))

CATEGORIES = [
    # NIKE
    {"name":"Nike – Alles",        "brands":[NIKE],  "pmin":None,  "pmax":None,  "kw":None,          "ch":ch("CHANNEL_NIKE"),             "color":0xF5821F},
    {"name":"Nike – 0-10€",        "brands":[NIKE],  "pmin":0.01,  "pmax":10,    "kw":None,          "ch":ch("CHANNEL_NIKE_10"),          "color":0xF5821F},
    {"name":"Nike – 10-20€",       "brands":[NIKE],  "pmin":10.01, "pmax":20,    "kw":None,          "ch":ch("CHANNEL_NIKE_20"),          "color":0xF5821F},
    {"name":"Nike – Trackpants",   "brands":[NIKE],  "pmin":None,  "pmax":None,  "kw":KW_TRACKPANTS, "ch":ch("CHANNEL_NIKE_TRACKPANTS"),  "color":0xF5821F},
    {"name":"Nike – Tracksuits",   "brands":[NIKE],  "pmin":None,  "pmax":None,  "kw":KW_TRACKSUITS, "ch":ch("CHANNEL_NIKE_TRACKSUITS"),  "color":0xF5821F},
    {"name":"Nike – Jacken",       "brands":[NIKE],  "pmin":None,  "pmax":None,  "kw":KW_JACKEN,     "ch":ch("CHANNEL_NIKE_JACKEN"),      "color":0xF5821F},
    {"name":"Nike – Shirts",       "brands":[NIKE],  "pmin":None,  "pmax":None,  "kw":KW_SHIRTS,     "ch":ch("CHANNEL_NIKE_SHIRTS"),      "color":0xF5821F},
    {"name":"Nike – Hoodies",      "brands":[NIKE],  "pmin":None,  "pmax":None,  "kw":KW_HOODIES,    "ch":ch("CHANNEL_NIKE_HOODIES"),     "color":0xF5821F},
    {"name":"Nike – Polos",        "brands":[NIKE],  "pmin":None,  "pmax":None,  "kw":KW_POLOS,      "ch":ch("CHANNEL_NIKE_POLOS"),       "color":0xF5821F},
    # ADIDAS
    {"name":"Adidas – Alles",      "brands":[ADIDAS],"pmin":None,  "pmax":None,  "kw":None,          "ch":ch("CHANNEL_ADIDAS"),           "color":0x000000},
    {"name":"Adidas – 0-15€",      "brands":[ADIDAS],"pmin":0.01,  "pmax":15,    "kw":None,          "ch":ch("CHANNEL_ADIDAS_15"),        "color":0x000000},
    {"name":"Adidas – 15-40€",     "brands":[ADIDAS],"pmin":15.01, "pmax":40,    "kw":None,          "ch":ch("CHANNEL_ADIDAS_40"),        "color":0x000000},
    {"name":"Adidas – Trackpants", "brands":[ADIDAS],"pmin":None,  "pmax":None,  "kw":KW_TRACKPANTS, "ch":ch("CHANNEL_ADIDAS_TRACKPANTS"),"color":0x000000},
    {"name":"Adidas – Tracksuits", "brands":[ADIDAS],"pmin":None,  "pmax":None,  "kw":KW_TRACKSUITS, "ch":ch("CHANNEL_ADIDAS_TRACKSUITS"),"color":0x000000},
    {"name":"Adidas – Jacken",     "brands":[ADIDAS],"pmin":None,  "pmax":None,  "kw":KW_JACKEN,     "ch":ch("CHANNEL_ADIDAS_JACKEN"),    "color":0x000000},
    {"name":"Adidas – Shirts",     "brands":[ADIDAS],"pmin":None,  "pmax":None,  "kw":KW_SHIRTS,     "ch":ch("CHANNEL_ADIDAS_SHIRTS"),    "color":0x000000},
    {"name":"Adidas – Hoodies",    "brands":[ADIDAS],"pmin":None,  "pmax":None,  "kw":KW_HOODIES,    "ch":ch("CHANNEL_ADIDAS_HOODIES"),   "color":0x000000},
    {"name":"Adidas – Polos",      "brands":[ADIDAS],"pmin":None,  "pmax":None,  "kw":KW_POLOS,      "ch":ch("CHANNEL_ADIDAS_POLOS"),     "color":0x000000},
    # LACOSTE
    {"name":"Lacoste – Alles",      "brands":[LACOSTE],"pmin":None,  "pmax":None,  "kw":None,          "ch":ch("CHANNEL_LACOSTE"),             "color":0x00A850},
    {"name":"Lacoste – 0-10€",      "brands":[LACOSTE],"pmin":0.01,  "pmax":10,    "kw":None,          "ch":ch("CHANNEL_LACOSTE_10"),          "color":0x00A850},
    {"name":"Lacoste – 10-20€",     "brands":[LACOSTE],"pmin":10.01, "pmax":20,    "kw":None,          "ch":ch("CHANNEL_LACOSTE_20"),          "color":0x00A850},
    {"name":"Lacoste – 20-40€",     "brands":[LACOSTE],"pmin":20.01, "pmax":40,    "kw":None,          "ch":ch("CHANNEL_LACOSTE_40"),          "color":0x00A850},
    {"name":"Lacoste – Trackpants", "brands":[LACOSTE],"pmin":None,  "pmax":None,  "kw":KW_TRACKPANTS, "ch":ch("CHANNEL_LACOSTE_TRACKPANTS"),  "color":0x00A850},
    {"name":"Lacoste – Tracksuits", "brands":[LACOSTE],"pmin":None,  "pmax":None,  "kw":KW_TRACKSUITS, "ch":ch("CHANNEL_LACOSTE_TRACKSUITS"),  "color":0x00A850},
    {"name":"Lacoste – Jacken",     "brands":[LACOSTE],"pmin":None,  "pmax":None,  "kw":KW_JACKEN,     "ch":ch("CHANNEL_LACOSTE_JACKEN"),      "color":0x00A850},
    {"name":"Lacoste – Shirts",     "brands":[LACOSTE],"pmin":None,  "pmax":None,  "kw":KW_SHIRTS,     "ch":ch("CHANNEL_LACOSTE_SHIRTS"),      "color":0x00A850},
    {"name":"Lacoste – Hoodies",    "brands":[LACOSTE],"pmin":None,  "pmax":None,  "kw":KW_HOODIES,    "ch":ch("CHANNEL_LACOSTE_HOODIES"),     "color":0x00A850},
    {"name":"Lacoste – Polos",      "brands":[LACOSTE],"pmin":None,  "pmax":None,  "kw":KW_POLOS,      "ch":ch("CHANNEL_LACOSTE_POLOS"),       "color":0x00A850},
    # RALPH LAUREN
    {"name":"Ralph Lauren – Alles",     "brands":[RL],"pmin":None,  "pmax":None,  "kw":None,          "ch":ch("CHANNEL_RL"),           "color":0x002868},
    {"name":"Ralph Lauren – 0-10€",     "brands":[RL],"pmin":0.01,  "pmax":10,    "kw":None,          "ch":ch("CHANNEL_RL_10"),        "color":0x002868},
    {"name":"Ralph Lauren – 10-20€",    "brands":[RL],"pmin":10.01, "pmax":20,    "kw":None,          "ch":ch("CHANNEL_RL_20"),        "color":0x002868},
    {"name":"Ralph Lauren – 20-40€",    "brands":[RL],"pmin":20.01, "pmax":40,    "kw":None,          "ch":ch("CHANNEL_RL_40"),        "color":0x002868},
    {"name":"Ralph Lauren – Polos",     "brands":[RL],"pmin":None,  "pmax":None,  "kw":KW_POLOS,      "ch":ch("CHANNEL_RL_POLOS"),     "color":0x002868},
    {"name":"Ralph Lauren – Jacken",    "brands":[RL],"pmin":None,  "pmax":None,  "kw":KW_JACKEN,     "ch":ch("CHANNEL_RL_JACKEN"),    "color":0x002868},
    {"name":"Ralph Lauren – Tracksuit", "brands":[RL],"pmin":None,  "pmax":None,  "kw":KW_TRACKSUITS, "ch":ch("CHANNEL_RL_TRACKSUIT"), "color":0x002868},
    # TRIKOTS
    {"name":"Trikots – Alles","brands":TRIKOT_BRANDS,"pmin":None,"pmax":None,"kw":KW_TRIKOTS,     "ch":ch("CHANNEL_TRIKOTS"),      "color":0x09B1BA},
    {"name":"Trikots – Hose", "brands":TRIKOT_BRANDS,"pmin":None,"pmax":None,"kw":KW_TRIKOT_HOSE, "ch":ch("CHANNEL_TRIKOTS_HOSE"), "color":0x09B1BA},
    {"name":"Trikots – Set",  "brands":TRIKOT_BRANDS,"pmin":None,"pmax":None,"kw":KW_TRIKOT_SET,  "ch":ch("CHANNEL_TRIKOTS_SET"),  "color":0x09B1BA},
]

seen_ids: dict[str, set[int]] = {cat["name"]: set() for cat in CATEGORIES}
first_run = True
cookie_session = None
cookie_counter = 0
COOKIE_REFRESH = 5  # Alle 5 Durchläufe neuen Cookie holen

def refresh_session():
    global cookie_session
    s = requests.Session()
    if not VINTED_TOKEN:
        s.get("https://www.vinted.de", headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
        }, proxies=PROXIES, timeout=10)
    cookie_session = s
    print("[Info] Session erneuert")

VINTED_TOKEN = os.getenv("VINTED_TOKEN")  # Bearer eyJhbGc...

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

# ─── HTTP (läuft in eigenem Thread) ──────────────────────────────
def _fetch(brand_ids, pmax):
    global cookie_session
    if cookie_session is None:
        refresh_session()
    params = [("order","newest_first"),("per_page","2")]  # Nur 2 Artikel → minimale Bandwidth
    for b in brand_ids: params.append(("brand_ids[]", str(b)))
    for l in LAENDER:   params.append(("country_ids[]", l))
    if pmax: params.append(("price_to", str(pmax)))
    url = "https://www.vinted.de/api/v2/catalog/items"
    r = cookie_session.get(url, headers=API_HEADERS, params=params, proxies=PROXIES, timeout=15)
    r.raise_for_status()
    if not r.text or r.text.strip() == "":
        print(f"[Warnung] Leere Antwort (Status {r.status_code}) – Cookie wird erneuert")
        refresh_session()
        return []
    try:
        data = r.json()
        return data.get("items", [])
    except Exception as e:
        print(f"[Warnung] Kein JSON (Status {r.status_code}): {r.text[:200]}")
        refresh_session()
        return []

async def fetch_items(brand_ids, pmax):
    try:
        return await asyncio.to_thread(_fetch, brand_ids, pmax)
    except Exception as e:
        print(f"[Fehler] {e}")
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
    groesse = item.get("size_title","").strip()
    land    = item.get("user",{}).get("country_iso","").upper()
    if any(v in titel for v in VERBOTEN): return False
    if groesse in VERBOTEN_GROESSEN: return False
    if land and land not in {"DE","AT","CH","IT","FR","ES"}: return False
    return True

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
    e.add_field(name="💶 Preis",     value=pstr,                                 inline=True)
    e.add_field(name="📏 Größe",     value=item.get("size_title","—"),           inline=True)
    e.add_field(name="✨ Zustand",   value=item.get("status","—"),               inline=True)
    e.add_field(name="👤 Verkäufer", value=item.get("user",{}).get("login","—"), inline=True)
    e.add_field(name="🔗 Artikel",   value=f"[Auf Vinted ansehen]({url})",       inline=False)
    if img: e.set_image(url=img)
    e.set_footer(text=f"Vinted Snipebot • {cat['name']}")
    return e

# ─── Bot ──────────────────────────────────────────────────────────
intents = discord.Intents.default()
client  = discord.Client(intents=intents)

@tasks.loop(seconds=60)
async def check_all():
    global first_run, cookie_counter

    # Dynamisches Interval – nachts schlafen
    interval = get_interval()
    if interval != check_all.seconds:
        check_all.change_interval(seconds=interval)
        print(f"[Info] Interval geändert auf {interval}s")

    cookie_counter += 1
    if cookie_counter >= COOKIE_REFRESH:
        cookie_counter = 0
        await asyncio.to_thread(refresh_session)

    # Nur 4 API Anfragen statt 38 – lokal auf Channels verteilen
    brand_requests = [
        ([NIKE],    None),
        ([ADIDAS],  None),
        ([LACOSTE], None),
        ([RL],      None),
        (TRIKOT_BRANDS, None),
    ]

    for brand_ids, pmax in brand_requests:
        try:
            await asyncio.sleep(REQUEST_DELAY)
            items = await fetch_items(brand_ids, pmax)
        except Exception as e:
            print(f"[Fehler] Anfrage fehlgeschlagen: {e}")
            continue

        for item in items:
            iid = item.get("id")

            # Artikel auf alle passenden Kategorien verteilen
            for cat in CATEGORIES:
                if cat["brands"] != brand_ids and not (
                    len(cat["brands"]) > 1 and brand_ids == TRIKOT_BRANDS
                ):
                    continue
                if cat["ch"] == 0:
                    continue
                channel = client.get_channel(cat["ch"])
                if not channel:
                    continue
                if iid in seen_ids[cat["name"]]:
                    continue
                seen_ids[cat["name"]].add(iid)
                if first_run:
                    continue
                if not kleidung_ok(item):
                    continue
                if not preis_ok(item, cat["pmin"], cat["pmax"]):
                    continue
                if not keyword_ok(item, cat["kw"]):
                    continue
                try:
                    await channel.send(embed=build_embed(item, cat))
                    print(f"✅ [{cat['name']}] {item.get('title')}")
                except Exception as e:
                    print(f"[Fehler] Senden fehlgeschlagen [{cat['name']}]: {e}")

    first_run = False

@client.event
async def on_ready():
    print(f"✅ Snipebot online: {client.user}")
    print(f"📦 {len(CATEGORIES)} Kategorien | {CHECK_INTERVAL}s Intervall")
    for cat in CATEGORIES:
        print(f"   {'✅' if cat['ch'] != 0 else '❌'} {cat['name']}")
    check_all.start()

client.run(DISCORD_TOKEN)
