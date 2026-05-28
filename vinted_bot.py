import discord
from discord.ext import tasks
import requests
import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN  = os.getenv("DISCORD_TOKEN")
CHECK_INTERVAL = 40

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept":          "application/json",
    "Accept-Language": "de-DE,de;q=0.9",
}

LAENDER = ["7", "193", "195", "10", "6", "13"]  # DE, AT, CH, IT, FR, ES

# ─── Brand IDs ────────────────────────────────────────────────────
NIKE    = 53
ADIDAS  = 14
LACOSTE = 60
RL      = 88
TRIKOT_BRANDS = [53, 14, 60, 88, 316, 103, 254]

# ─── Keywords ─────────────────────────────────────────────────────
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

KW_POLOS = ["polo","poloshirt","polo shirt","polo t-shirt","polo hemd","polo top"]

KW_TRIKOTS     = ["trikot","jersey","maglia","maillot","football shirt","soccer shirt",
    "fussballtrikot","fußballtrikot","sporttrikot","kit","spielertrikot"]
KW_TRIKOT_HOSE = ["trikot hose","football shorts","soccer shorts","fußballshorts",
    "pantaloncini","sport shorts","kurze hose","shorts"]
KW_TRIKOT_SET  = ["trikot set","jersey set","football kit","soccer kit","trikot komplett"]

# ─── Verbotene Keywords ───────────────────────────────────────────
VERBOTEN = [
    "schuh","schuhe","sneaker","sneakers","boots","stiefel","slipper","sandale","sandalen",
    "scarpe","scarpa","schoen","schoenen","chaussure","chaussures","zapato","zapatos",
    "zapatilla","zapatillas","air max","air force","dunk","yeezy","campus","gazelle",
    "samba","superstar","stan smith","ultraboost","nmd","converse","vans","timberland",
    "ugg","crocs","birkenstock","loafer","pumps","ballerina",
    "kinder","kinderjacke","kinderhose","baby","babykleidung","kleinkind","junge","mädchen",
    "kids","children","toddler","bambino","bambina","bambini","neonato","enfant","bébé",
    "bebe","niño","niña","infantil",
    "tasche","bag","rucksack","backpack","cap","mütze","beanie","gürtel","belt",
    "schal","socken","socks","handschuhe","uhr","watch","schmuck","kette","ring",
    "brille","parfum","ball","fußball","basketball",
]

VERBOTEN_GROESSEN = {str(i) for i in range(16, 36)} | {
    "86","92","98","104","110","116","122","128","134","140","146","152","158","164","170"}

# ─── Channel IDs laden ────────────────────────────────────────────
def ch(key): return int(os.getenv(key, 0))

# ─── Kategorien ───────────────────────────────────────────────────
CATEGORIES = [
    # NIKE
    {"name":"Nike – Alles",        "brands":[NIKE],  "pmin":None,  "pmax":None,  "kw":None,         "ch":ch("CHANNEL_NIKE"),             "color":0xF5821F},
    {"name":"Nike – 0-10€",        "brands":[NIKE],  "pmin":0.01,  "pmax":10,    "kw":None,         "ch":ch("CHANNEL_NIKE_10"),          "color":0xF5821F},
    {"name":"Nike – 10-20€",       "brands":[NIKE],  "pmin":10.01, "pmax":20,    "kw":None,         "ch":ch("CHANNEL_NIKE_20"),          "color":0xF5821F},
    {"name":"Nike – Trackpants",   "brands":[NIKE],  "pmin":None,  "pmax":None,  "kw":KW_TRACKPANTS,"ch":ch("CHANNEL_NIKE_TRACKPANTS"),  "color":0xF5821F},
    {"name":"Nike – Tracksuits",   "brands":[NIKE],  "pmin":None,  "pmax":None,  "kw":KW_TRACKSUITS,"ch":ch("CHANNEL_NIKE_TRACKSUITS"),  "color":0xF5821F},
    {"name":"Nike – Jacken",       "brands":[NIKE],  "pmin":None,  "pmax":None,  "kw":KW_JACKEN,    "ch":ch("CHANNEL_NIKE_JACKEN"),      "color":0xF5821F},
    {"name":"Nike – Shirts",       "brands":[NIKE],  "pmin":None,  "pmax":None,  "kw":KW_SHIRTS,    "ch":ch("CHANNEL_NIKE_SHIRTS"),      "color":0xF5821F},
    {"name":"Nike – Hoodies",      "brands":[NIKE],  "pmin":None,  "pmax":None,  "kw":KW_HOODIES,   "ch":ch("CHANNEL_NIKE_HOODIES"),     "color":0xF5821F},
    {"name":"Nike – Polos",        "brands":[NIKE],  "pmin":None,  "pmax":None,  "kw":KW_POLOS,     "ch":ch("CHANNEL_NIKE_POLOS"),       "color":0xF5821F},
    # ADIDAS
    {"name":"Adidas – Alles",      "brands":[ADIDAS],"pmin":None,  "pmax":None,  "kw":None,         "ch":ch("CHANNEL_ADIDAS"),           "color":0x000000},
    {"name":"Adidas – 0-15€",      "brands":[ADIDAS],"pmin":0.01,  "pmax":15,    "kw":None,         "ch":ch("CHANNEL_ADIDAS_15"),        "color":0x000000},
    {"name":"Adidas – 15-40€",     "brands":[ADIDAS],"pmin":15.01, "pmax":40,    "kw":None,         "ch":ch("CHANNEL_ADIDAS_40"),        "color":0x000000},
    {"name":"Adidas – Trackpants", "brands":[ADIDAS],"pmin":None,  "pmax":None,  "kw":KW_TRACKPANTS,"ch":ch("CHANNEL_ADIDAS_TRACKPANTS"),"color":0x000000},
    {"name":"Adidas – Tracksuits", "brands":[ADIDAS],"pmin":None,  "pmax":None,  "kw":KW_TRACKSUITS,"ch":ch("CHANNEL_ADIDAS_TRACKSUITS"),"color":0x000000},
    {"name":"Adidas – Jacken",     "brands":[ADIDAS],"pmin":None,  "pmax":None,  "kw":KW_JACKEN,    "ch":ch("CHANNEL_ADIDAS_JACKEN"),    "color":0x000000},
    {"name":"Adidas – Shirts",     "brands":[ADIDAS],"pmin":None,  "pmax":None,  "kw":KW_SHIRTS,    "ch":ch("CHANNEL_ADIDAS_SHIRTS"),    "color":0x000000},
    {"name":"Adidas – Hoodies",    "brands":[ADIDAS],"pmin":None,  "pmax":None,  "kw":KW_HOODIES,   "ch":ch("CHANNEL_ADIDAS_HOODIES"),   "color":0x000000},
    {"name":"Adidas – Polos",      "brands":[ADIDAS],"pmin":None,  "pmax":None,  "kw":KW_POLOS,     "ch":ch("CHANNEL_ADIDAS_POLOS"),     "color":0x000000},
    # LACOSTE
    {"name":"Lacoste – Alles",      "brands":[LACOSTE],"pmin":None,  "pmax":None,  "kw":None,         "ch":ch("CHANNEL_LACOSTE"),             "color":0x00A850},
    {"name":"Lacoste – 0-10€",      "brands":[LACOSTE],"pmin":0.01,  "pmax":10,    "kw":None,         "ch":ch("CHANNEL_LACOSTE_10"),          "color":0x00A850},
    {"name":"Lacoste – 10-20€",     "brands":[LACOSTE],"pmin":10.01, "pmax":20,    "kw":None,         "ch":ch("CHANNEL_LACOSTE_20"),          "color":0x00A850},
    {"name":"Lacoste – 20-40€",     "brands":[LACOSTE],"pmin":20.01, "pmax":40,    "kw":None,         "ch":ch("CHANNEL_LACOSTE_40"),          "color":0x00A850},
    {"name":"Lacoste – Trackpants", "brands":[LACOSTE],"pmin":None,  "pmax":None,  "kw":KW_TRACKPANTS,"ch":ch("CHANNEL_LACOSTE_TRACKPANTS"),  "color":0x00A850},
    {"name":"Lacoste – Tracksuits", "brands":[LACOSTE],"pmin":None,  "pmax":None,  "kw":KW_TRACKSUITS,"ch":ch("CHANNEL_LACOSTE_TRACKSUITS"),  "color":0x00A850},
    {"name":"Lacoste – Jacken",     "brands":[LACOSTE],"pmin":None,  "pmax":None,  "kw":KW_JACKEN,    "ch":ch("CHANNEL_LACOSTE_JACKEN"),      "color":0x00A850},
    {"name":"Lacoste – Shirts",     "brands":[LACOSTE],"pmin":None,  "pmax":None,  "kw":KW_SHIRTS,    "ch":ch("CHANNEL_LACOSTE_SHIRTS"),      "color":0x00A850},
    {"name":"Lacoste – Hoodies",    "brands":[LACOSTE],"pmin":None,  "pmax":None,  "kw":KW_HOODIES,   "ch":ch("CHANNEL_LACOSTE_HOODIES"),     "color":0x00A850},
    {"name":"Lacoste – Polos",      "brands":[LACOSTE],"pmin":None,  "pmax":None,  "kw":KW_POLOS,     "ch":ch("CHANNEL_LACOSTE_POLOS"),       "color":0x00A850},
    # RALPH LAUREN
    {"name":"Ralph Lauren – Alles",     "brands":[RL],"pmin":None,  "pmax":None,  "kw":None,         "ch":ch("CHANNEL_RL"),           "color":0x002868},
    {"name":"Ralph Lauren – 0-10€",     "brands":[RL],"pmin":0.01,  "pmax":10,    "kw":None,         "ch":ch("CHANNEL_RL_10"),        "color":0x002868},
    {"name":"Ralph Lauren – 10-20€",    "brands":[RL],"pmin":10.01, "pmax":20,    "kw":None,         "ch":ch("CHANNEL_RL_20"),        "color":0x002868},
    {"name":"Ralph Lauren – 20-40€",    "brands":[RL],"pmin":20.01, "pmax":40,    "kw":None,         "ch":ch("CHANNEL_RL_40"),        "color":0x002868},
    {"name":"Ralph Lauren – Polos",     "brands":[RL],"pmin":None,  "pmax":None,  "kw":KW_POLOS,     "ch":ch("CHANNEL_RL_POLOS"),     "color":0x002868},
    {"name":"Ralph Lauren – Jacken",    "brands":[RL],"pmin":None,  "pmax":None,  "kw":KW_JACKEN,    "ch":ch("CHANNEL_RL_JACKEN"),    "color":0x002868},
    {"name":"Ralph Lauren – Tracksuit", "brands":[RL],"pmin":None,  "pmax":None,  "kw":KW_TRACKSUITS,"ch":ch("CHANNEL_RL_TRACKSUIT"), "color":0x002868},
    # TRIKOTS
    {"name":"Trikots – Alles","brands":TRIKOT_BRANDS,"pmin":None,"pmax":None,"kw":KW_TRIKOTS,    "ch":ch("CHANNEL_TRIKOTS"),      "color":0x09B1BA},
    {"name":"Trikots – Hose", "brands":TRIKOT_BRANDS,"pmin":None,"pmax":None,"kw":KW_TRIKOT_HOSE,"ch":ch("CHANNEL_TRIKOTS_HOSE"), "color":0x09B1BA},
    {"name":"Trikots – Set",  "brands":TRIKOT_BRANDS,"pmin":None,"pmax":None,"kw":KW_TRIKOT_SET, "ch":ch("CHANNEL_TRIKOTS_SET"),  "color":0x09B1BA},
]

seen_ids: dict[str, set[int]] = {cat["name"]: set() for cat in CATEGORIES}
first_run = True

# ─── API ──────────────────────────────────────────────────────────
def get_cookies():
    try:
        s = requests.Session()
        s.get("https://www.vinted.de", headers=HEADERS, timeout=10)
        return s.cookies.get_dict()
    except:
        return {}

def fetch_items(brand_ids, pmax):
    params = ["order=newest_first", "per_page=30"]
    for b in brand_ids:
        params.append(f"brand_ids[]={b}")
    for l in LAENDER:
        params.append(f"country_ids[]={l}")
    if pmax:
        params.append(f"price_to={pmax}")
    url = "https://www.vinted.de/api/v2/catalog/items?" + "&".join(params)
    try:
        r = requests.get(url, headers=HEADERS, cookies=get_cookies(), timeout=15)
        r.raise_for_status()
        return r.json().get("items", [])
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
    if kw is None:
        return True
    titel = item.get("title", "").lower()
    return any(k in titel for k in kw)

def kleidung_ok(item):
    titel   = item.get("title", "").lower()
    groesse = item.get("size_title", "").strip()
    land    = item.get("user", {}).get("country_iso", "").upper()
    if any(v in titel for v in VERBOTEN):
        return False
    if groesse in VERBOTEN_GROESSEN:
        return False
    if land and land not in {"DE","AT","CH","IT","FR","ES"}:
        return False
    return True

# ─── Embed ────────────────────────────────────────────────────────
def build_embed(item, cat):
    title = item.get("title", "Unbekannt")
    price = item.get("price", {})
    pstr  = f"{price.get('amount','?')} {price.get('currency_code','EUR')}"
    url   = f"https://www.vinted.de/items/{item.get('id')}"
    imgs  = item.get("photos", [])
    img   = imgs[0].get("url") if imgs else None

    e = discord.Embed(title=f"🛍️ {title}", url=url, color=cat["color"],
                      description=f"**{cat['name']}**")
    e.add_field(name="💶 Preis",     value=pstr,                                 inline=True)
    e.add_field(name="📏 Größe",     value=item.get("size_title","—"),           inline=True)
    e.add_field(name="✨ Zustand",   value=item.get("status","—"),               inline=True)
    e.add_field(name="👤 Verkäufer", value=item.get("user",{}).get("login","—"), inline=True)
    e.add_field(name="🔗 Artikel",   value=f"[Auf Vinted ansehen]({url})",       inline=False)
    if img:
        e.set_image(url=img)
    e.set_footer(text=f"Vinted Snipebot • {cat['name']}")
    return e

# ─── Bot ──────────────────────────────────────────────────────────
intents = discord.Intents.default()
client  = discord.Client(intents=intents)

@tasks.loop(seconds=CHECK_INTERVAL)
async def check_all():
    global first_run

    for cat in CATEGORIES:
        if cat["ch"] == 0:
            continue
        channel = client.get_channel(cat["ch"])
        if not channel:
            continue

        items = fetch_items(cat["brands"], cat["pmax"])
        for item in items:
            iid = item.get("id")
            if not iid or iid in seen_ids[cat["name"]]:
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
            await channel.send(embed=build_embed(item, cat))
            print(f"✅ [{cat['name']}] {item.get('title')}")

    first_run = False

@client.event
async def on_ready():
    print(f"✅ Snipebot online: {client.user}")
    print(f"📦 {len(CATEGORIES)} Kategorien | {CHECK_INTERVAL}s Intervall")
    for cat in CATEGORIES:
        status = "✅" if cat["ch"] != 0 else "❌ FEHLT"
        print(f"   {status} {cat['name']}")
    check_all.start()

client.run(DISCORD_TOKEN)
