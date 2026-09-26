# -*- coding: utf-8 -*-
"""
VK-бот 9.0 — государства, войны, донат, выдача, сирена, заложники
"""

import os, re, sys, json, time, random, threading, difflib
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.exceptions import VkApiError

# ================================================================
# НАСТРОЙКИ
# ================================================================
TOKEN = os.getenv("VK_TOKEN", "").strip()
GROUP_ID = int(os.getenv("VK_GROUP_ID", "241512398"))
GLOBAL_OWNER_ID = int(os.getenv("GLOBAL_OWNER_ID", "1054352381"))
COMMUNITY_LINK = f"https://vk.com/club{GROUP_ID}"

if not TOKEN: print("❌ VK_TOKEN не задан"); sys.exit(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
PID_FILE = "/tmp/.bot.pid"
CFG_VERSION = 9
MUTE_DM_INTERVAL = 300
START_BALANCE = 100
PRIZE_MIN, PRIZE_MAX, PRIZE_COOLDOWN = 1000, 900000, 86400
VIP_PRICE, VIP_DURATION, VIP_BONUS = 1000000, 30*86400, 0.10
ADMIN_ABUSE_TITLE, ADMIN_ABUSE_MSGS = "👑 Admin Abuser", 50

WAR_COST = 1000000
WAR_CAPTURE_SECONDS = 300
BASE_ARMY = 100000
ARMY_LEVEL_MAX = 10
ARMY_LEVEL_MULT = 1.15
MIL_TASK_COOLDOWN = 3600
MIL_TASK_REWARD = 5000
MIL_TASK_COST = 100000

# ================================================================
# СТРАНЫ
# ================================================================
COUNTRIES = {
    "россия": {"name":"🇷🇺 Россия","bonus":5000},
    "сша": {"name":"🇺🇸 США","bonus":7000},
    "китай": {"name":"🇨🇳 Китай","bonus":6000},
    "германия": {"name":"🇩🇪 Германия","bonus":5500},
    "япония": {"name":"🇯🇵 Япония","bonus":6500},
    "франция": {"name":"🇫🇷 Франция","bonus":5500},
    "великобритания": {"name":"🇬🇧 Великобритания","bonus":6000},
    "италия": {"name":"🇮🇹 Италия","bonus":5000},
    "испания": {"name":"🇪🇸 Испания","bonus":5000},
    "канада": {"name":"🇨🇦 Канада","bonus":5500},
    "украина": {"name":"🇺🇦 Украина","bonus":5000},
    "казахстан": {"name":"🇰🇿 Казахстан","bonus":4500},
    "беларусь": {"name":"🇧🇾 Беларусь","bonus":4500},
    "польша": {"name":"🇵🇱 Польша","bonus":4500},
    "турция": {"name":"🇹🇷 Турция","bonus":4500},
    "индия": {"name":"🇮🇳 Индия","bonus":5000},
    "бразилия": {"name":"🇧🇷 Бразилия","bonus":5000},
    "мексика": {"name":"🇲🇽 Мексика","bonus":4500},
    "австралия": {"name":"🇦🇺 Австралия","bonus":5000},
    "египет": {"name":"🇪🇬 Египет","bonus":4000},
    "корея": {"name":"🇰🇷 Корея","bonus":5500},
    "швеция": {"name":"🇸🇪 Швеция","bonus":5000},
    "швейцария": {"name":"🇨🇭 Швейцария","bonus":5500},
    "оаэ": {"name":"🇦🇪 ОАЭ","bonus":8000},
}

CITIES = [
    "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург",
    "Казань", "Нижний Новгород", "Челябинск", "Самара",
    "Омск", "Ростов-на-Дону", "Уфа", "Красноярск",
    "Воронеж", "Пермь", "Волгоград", "Краснодар",
    "Саратов", "Тюмень", "Тольятти", "Ижевск"
]

BUILDINGS = {
    "больница":      {"cost": 200000, "bonus": "рост +5%",       "emoji":"🏥"},
    "завод":         {"cost": 300000, "bonus": "доход +5%",      "emoji":"🏭"},
    "школа":         {"cost": 150000, "bonus": "грамотность +5%","emoji":"🏫"},
    "университет":   {"cost": 500000, "bonus": "наука +10%",     "emoji":"🎓"},
    "электростанция":{"cost": 400000, "bonus": "энергия +10%",   "emoji":"⚡"},
    "жилой комплекс":{"cost": 250000, "bonus": "население +10%", "emoji":"🏢"},
    "казарма":       {"cost": 350000, "bonus": "+5000 войск",    "emoji":"🏛"},
    "военный завод":{"cost": 600000, "bonus": "техника +10%",   "emoji":"🏗"},
    "верфь":         {"cost": 800000, "bonus": "+1 корабль/час", "emoji":"⛴"},
    "аэропорт":      {"cost": 1000000,"bonus": "доход +15%",     "emoji":"✈️"},
}

WEAPONS = {
    "танк":   {"cost": 50000,  "power": 100, "emoji": "🚜"},
    "пво":    {"cost": 40000,  "power": 80,  "emoji": "🚀"},
    "ракета": {"cost": 100000, "power": 250, "emoji": "🚀"},
    "корабль":{"cost": 300000, "power": 500, "emoji": "⛴"},
    "самолёт":{"cost": 200000, "power": 400, "emoji": "✈️"},
    "бпла":   {"cost": 30000,  "power": 50,  "emoji": "🛸"},
}

RANKS = {
    "гражданин": {"name":"👤 Гражданин","cost":0,"bonus_mult":1.0},
    "политик":   {"name":"🏛️ Политик","cost":50000,"bonus_mult":1.2},
    "сенатор":   {"name":"⚖️ Сенатор","cost":200000,"bonus_mult":1.5},
    "министр":   {"name":"💼 Министр","cost":500000,"bonus_mult":2.0},
    "главком":   {"name":"🎖️ Главнокомандующий","cost":1000000,"bonus_mult":3.0},
    "президент": {"name":"👑 Президент","cost":0,"bonus_mult":5.0},
}

GOV_POSITIONS = [
    "президент", "премьер-министр", "министр обороны", "министр экономики",
    "министр иностранных дел", "главнокомандующий", "начальник генштаба",
    "сенатор", "губернатор", "дипломат"
]

BUSINESSES = {
    "киоск":       {"price": 1000,  "income": 50,   "emoji": "🏪"},
    "кафе":        {"price": 5000,  "income": 250,  "emoji": "☕"},
    "ресторан":    {"price": 20000, "income": 1000, "emoji": "🍽️"},
    "автомойка":   {"price": 35000, "income": 1800, "emoji": "🚗"},
    "завод":       {"price": 100000,"income": 5000, "emoji": "🏭"},
    "банк":        {"price": 250000,"income": 12000,"emoji": "🏦"},
    "корпорация":  {"price": 500000,"income": 25000,"emoji": "🏢"},
    "нефтевышка":  {"price": 1000000,"income": 55000,"emoji": "🛢️"},
    "отель":       {"price": 300000,"income": 15000,"emoji": "🏨"},
    "аэропорт":    {"price": 2000000,"income": 110000,"emoji": "✈️"},
}

# ================================================================
# НАБОРЫ КОМАНД
# ================================================================
PUBLIC_CMDS = [
    "help","info","staff","стата","stat","топ","top",
    "баланс","balance","biz","buybiz","mybiz","collect",
    "казино","casino","дуэль","duel",
    "монетка","coin","кубик","dice","слоты","slots",
    "краш","crash","дартс","darts","колесо","wheel","рулетка","roulette",
    "блэкджек","bj","мины","mines","башня","tower","кейс","case",
    "гонка","race","рыбалка","fish",
    "приз","prize","подписка","sub",
    "promo","промо","cmd","offer","report","ивент","event",
    "страны","государства","гражданство","citizenship","паспорт","passport",
    "страна","country","граждане","города","казна","правительство","должности",
    "армия","выборы","выдвинуться","голос","компания","регистрация",
    "переименоватьооо",
    "войны","война","захват","контразащита","мир",
    "коалиции","коалиция","коалпомощь","военпомощь","помочьвойна",
    "мобилизация","демобилизация","сделать","установить","пво",
    "запуск","задание","выполнитьзадание","задания",
    "госскоманды","донат","сирена","воздухтревога",
]

HELPER_CMDS = PUBLIC_CMDS + ["warn","promolist","createpromo","вайп"]
MODERATOR_CMDS = HELPER_CMDS + ["nick","rnick","unwarn","mute","unmute",
                                 "clear","banlist","tickets","adt"]
ADMIN_CMDS = MODERATOR_CMDS + ["kick","ban","unban","gban","ungban"]
STAFF_CMDS = ADMIN_CMDS + ["loginfo","builds"]
OWNER_CMDS = STAFF_CMDS + ["removestaff","setrole","setowner",
                            "setlog","unsetlog","setwarns","setmutetime",
                            "newrole","delrole","createivent","вайп_все",
                            "налоги","назначить","снятьминистра","воинскоезвание",
                            "улучшитьстрану","постройки","построить","госпроект","вооружение"]

GLOBAL_ONLY = ["объявление","announce","рассылка","setpresident","setcommander",
               "grole","removerole","gstaff","устгражданство","устпрезидент",
               "выдать"]

DEFAULT_ROLES = {
    "head": {"name":"Руководитель","priority":95,"commands":STAFF_CMDS},
    "deputy_head": {"name":"Заместитель Руководителя","priority":90,"commands":STAFF_CMDS},
    "special_admin": {"name":"Специальный Администратор","priority":85,"commands":STAFF_CMDS},
    "chief_admin": {"name":"Главный Администратор","priority":80,"commands":ADMIN_CMDS},
    "deputy_chief_admin": {"name":"Заместитель Главного Администратора","priority":75,"commands":ADMIN_CMDS},
    "chief_watcher": {"name":"Главный Следящий","priority":70,"commands":MODERATOR_CMDS},
    "deputy_chief_watcher": {"name":"Заместитель Главного Следящего","priority":65,"commands":MODERATOR_CMDS},
    "admin": {"name":"Администратор","priority":60,"commands":ADMIN_CMDS},
    "moderator": {"name":"Модератор","priority":50,"commands":MODERATOR_CMDS},
    "helper": {"name":"Хелпер","priority":20,"commands":HELPER_CMDS},
}

def commands_for_priority(p):
    if p >= 70: return list(STAFF_CMDS)
    if p >= 60: return list(ADMIN_CMDS)
    if p >= 40: return list(MODERATOR_CMDS)
    if p >= 20: return list(HELPER_CMDS)
    return list(PUBLIC_CMDS)

ALL_COMMANDS = set(PUBLIC_CMDS)
for _r in DEFAULT_ROLES.values(): ALL_COMMANDS.update(_r.get("commands", []))
ALL_COMMANDS.update(GLOBAL_ONLY + [
    "newrole","delrole","createivent","setowner","setrole","removestaff",
    "setpresident","setcommander","grole","removerole","gstaff",
    "builds","promolist","createpromo","вайп","вайп_все",
    "налоги","назначить","снятьминистра","воинскоезвание","улучшитьстрану",
    "постройки","построить","госпроект","вооружение","устгражданство","устпрезидент",
    "донат","сирена","воздухтревога","выдать","build",
])

# ================================================================
# КОНФИГ
# ================================================================
DEFAULT_CHAT = {
    "owner":None,"staff":{},"banned":{},"muted":{},"warns":{},
    "nicknames":{},"welcome":True,"user_stats":{},"balance":{},
    "businesses":{},"subs":{},"last_prize":{},"promos_used":{},
    "promos":{},"local_roles":{},"custom_cmds":{},"build_name":None,
}

def default_country_data():
    return {
        "treasury": 0,
        "president": None,
        "commander": None,
        "citizens": [],
        "army": BASE_ARMY,
        "army_level": 1,
        "weapons": {w: 0 for w in WEAPONS},
        "nukes": 0,
        "cities_unlocked": 3,
        "cities": {c: {"buildings": [], "pvo": 0, "siren": False} for c in CITIES[:3]},
        "coalition": None,
        "wars": [],
        "tax": 5,
        "government": {},
        "elections": {"candidates": [], "votes": {}, "ends_at": 0, "active": False},
        "projects": [],
        "mil_task_cooldown": {},
        "history": [],
        "destroyed": False,
        "captured_by": None,
        "destroyed_at": 0,
        "hostages": [],
    }

DEFAULT_CFG = {
    "version": CFG_VERSION,
    "global_owner": GLOBAL_OWNER_ID,
    "default_mute_minutes": 30, "max_warns": 3, "log_peer_id": 0,
    "roles": DEFAULT_ROLES, "global_staff": {},
    "chats": {}, "known_peers": [],
    "tickets": {}, "next_ticket_id": 1, "custom_events": {},
    "countries": {k: default_country_data() for k in COUNTRIES},
    "citizens": {},
    "coalitions": {},
    "wars": [],
    "builds": {}, "global_promos": {},
}
_cfg_lock = threading.Lock()

def migrate(d):
    d.setdefault("version", 1)
    for k, v in DEFAULT_CFG.items():
        if k not in d: d[k] = v
    roles = d.get("roles") or {}
    if not all(isinstance(v, dict) and "priority" in v for v in roles.values()):
        d["roles"] = json.loads(json.dumps(DEFAULT_ROLES))
    else:
        for k, v in DEFAULT_ROLES.items():
            if k not in d["roles"]: d["roles"][k] = v
    d.pop("user_stats", None)
    d["version"] = CFG_VERSION
    d.setdefault("countries", {})
    for k in COUNTRIES:
        if k not in d["countries"]:
            d["countries"][k] = default_country_data()
        else:
            base = default_country_data()
            for kk, vv in base.items():
                d["countries"][k].setdefault(kk, vv)
            cd = d["countries"][k]
            for c_name in CITIES:
                cd["cities"].setdefault(c_name, {"buildings": [], "pvo": 0, "siren": False})
    d.setdefault("citizens", {})
    d.setdefault("coalitions", {})
    d.setdefault("wars", [])
    d.setdefault("builds", {}); d.setdefault("global_promos", {})
    d.setdefault("global_staff", {})
    for ch in d.get("chats", {}).values():
        for k, v in DEFAULT_CHAT.items():
            ch.setdefault(k, json.loads(json.dumps(v)))
        muted = ch.get("muted", {})
        for uid, val in list(muted.items()):
            if isinstance(val, (int, float)): muted[uid] = {"until": val, "last_dm": 0}
    return d

def load_cfg():
    if not os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CFG, f, ensure_ascii=False, indent=2)
        except Exception as e: print(f"[cfg] {e}")
        return json.loads(json.dumps(DEFAULT_CFG))
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f: return migrate(json.load(f))
    except Exception as e:
        print(f"[cfg load] {e}"); return json.loads(json.dumps(DEFAULT_CFG))

def save_cfg(d):
    with _cfg_lock:
        try:
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=2)
        except Exception as e: print(f"[cfg save] {e}")

cfg = load_cfg(); save_cfg(cfg)

# ================================================================
# VK
# ================================================================
print("🔌 Подключаюсь к VK...")
vk = vk_api.VkApi(token=TOKEN); api = vk.get_api()
try:
    gi = api.groups.getById(group_id=GROUP_ID)
    print(f"   ✅ Группа: {gi[0]['name']} (id={GROUP_ID})")
except VkApiError as e: print(f"   ❌ {e}"); sys.exit(1)
try:
    longpoll = VkBotLongPoll(vk, group_id=GROUP_ID)
    print("   ✅ Long Poll готов")
except VkApiError as e: print(f"   ❌ LongPoll: {e}"); sys.exit(1)
BOT_ID = -GROUP_ID

# ================================================================
# ИМЕНА
# ================================================================
_name_cache = {}; _name_lock = threading.Lock()

def prefetch_names(uids):
    uids = [int(u) for u in uids if u and int(u) > 0]; to = []
    with _name_lock:
        for u in uids:
            if u not in _name_cache: to.append(u)
    if not to: return
    try:
        for i in range(0, len(to), 500):
            res = api.users.get(user_ids=",".join(map(str, to[i:i+500])),
                                fields="first_name,last_name")
            with _name_lock:
                for u in res:
                    n = f"{u.get('first_name','')} {u.get('last_name','')}".strip()
                    _name_cache[u["id"]] = n or f"id{u['id']}"
    except Exception as e: print(f"[prefetch] {e}")

def get_vk_name(uid):
    uid = int(uid)
    with _name_lock:
        if uid in _name_cache: return _name_cache[uid]
    try:
        r = api.users.get(user_ids=uid, fields="first_name,last_name")
        n = f"{r[0].get('first_name','')} {r[0].get('last_name','')}".strip() if r else f"id{uid}"
        n = n or f"id{uid}"
    except Exception: n = f"id{uid}"
    with _name_lock: _name_cache[uid] = n
    return n

def mention(uid, peer_id=None):
    uid = int(uid)
    if peer_id and is_chat(peer_id):
        c = get_chat(peer_id)
        nick = c.get("nicknames", {}).get(str(uid))
        if nick: return f"[id{uid}|{nick}]"
    return f"[id{uid}|{get_vk_name(uid)}]"

# ================================================================
# ДЕДУПЛИКАЦИЯ
# ================================================================
_processed = set(); _processed_lock = threading.Lock()

def is_duplicate(peer_id, msg):
    cmid = msg.get("conversation_message_id") or msg.get("id") or 0
    text = (msg.get("text") or "")[:40]
    key = (peer_id, cmid, msg.get("from_id"), text)
    with _processed_lock:
        if key in _processed: return True
        _processed.add(key)
        if len(_processed) > 5000:
            for x in list(_processed)[:2500]: _processed.discard(x)
        return False

# ================================================================
# ХЕЛПЕРЫ
# ================================================================
def send(peer_id, text, reply_to=None):
    kw = {"peer_id":peer_id,"message":text,
          "random_id":int(time.time()*1000)+random.randint(0,999),
          "disable_mentions":0}
    if reply_to:
        try:
            r = int(reply_to)
            if r > 0: kw["reply_to"] = r
        except Exception: pass
    try: api.messages.send(**kw)
    except Exception as e:
        print(f"[send] {e}")
        if "reply_to" in kw:
            del kw["reply_to"]
            try: api.messages.send(**kw)
            except Exception as e2: print(f"[send2] {e2}")

def send_dm(uid, text):
    try:
        api.messages.send(peer_id=uid, message=text,
                          random_id=int(time.time()*1000)+random.randint(0,999),
                          disable_mentions=1)
        return True
    except Exception as e:
        print(f"[dm {uid}] {e}"); return False

def log_action(actor_id, text):
    peer = cfg.get("log_peer_id")
    if not peer: return
    try:
        who = "🤖 бот" if actor_id == BOT_ID else f"[id{actor_id}|модератор]"
        api.messages.send(peer_id=peer, message=f"📝 {who}: {text}",
                          random_id=int(time.time()*1000)+random.randint(0,999))
    except Exception as e: print(f"[log] {e}")

def is_chat(peer_id): return peer_id > 2000000000
def chat_id_from_peer(peer_id): return peer_id - 2000000000 if peer_id > 2000000000 else None

_admin_cache = {}
_admin_lock = threading.Lock()
ADMIN_CHECK_TTL = 30

WAIT_STAR_TEXT = """⭐ <b>Бот ждёт выдачи звёздочки</b>

Чтобы я начал работать, назначьте меня <b>администратором беседы</b>:

1️⃣ Управление беседой → Участники
2️⃣ Найдите меня в списке
3️⃣ Назначьте администратором ⭐

После этого все команды станут доступны.

📋 Пока жду — можете посмотреть справку: /help"""

def is_bot_admin(peer_id, force=False):
    if not is_chat(peer_id): return False
    now = time.time()
    with _admin_lock:
        cached = _admin_cache.get(peer_id)
        if cached and not force and now - cached[1] < ADMIN_CHECK_TTL:
            return cached[0]
    try:
        members = api.messages.getConversationMembers(peer_id=peer_id)["items"]
        is_admin = False
        for m in members:
            if m.get("member_id") == BOT_ID:
                is_admin = bool(m.get("is_admin") or m.get("is_owner"))
                break
    except Exception as e:
        print(f"[is_bot_admin] {e}"); is_admin = True
    with _admin_lock:
        _admin_cache[peer_id] = (is_admin, now)
    return is_admin

def cache_invalidate_admin(peer_id):
    with _admin_lock: _admin_cache.pop(peer_id, None)

def get_chat(peer_id):
    if not is_chat(peer_id): return None
    chats = cfg.setdefault("chats", {}); key = str(peer_id)
    if key not in chats:
        chats[key] = json.loads(json.dumps(DEFAULT_CHAT)); save_cfg(cfg)
    for k, v in DEFAULT_CHAT.items():
        chats[key].setdefault(k, json.loads(json.dumps(v)))
    return chats[key]

def track_peer(peer_id):
    if not is_chat(peer_id): return
    kp = cfg.setdefault("known_peers", [])
    if peer_id not in kp:
        kp.append(peer_id); save_cfg(cfg)

def track_message(from_id, peer_id, text):
    c = get_chat(peer_id)
    if not c: return
    stats = c.setdefault("user_stats", {}); key = str(from_id)
    s = stats.get(key) or {"msg_count":0,"last_text":"","last_at":0}
    s["msg_count"] += 1
    if text: s["last_text"] = text[:120]
    s["last_at"] = int(time.time()); stats[key] = s
    if s["msg_count"] % 20 == 0: save_cfg(cfg)

def get_balance(peer_id, uid):
    c = get_chat(peer_id)
    if not c: return 0
    bal = c.setdefault("balance", {}); uid = str(uid)
    if uid not in bal: bal[uid] = START_BALANCE; save_cfg(cfg)
    return bal[uid]

def add_balance(peer_id, uid, amount):
    c = get_chat(peer_id)
    if not c: return 0
    bal = c.setdefault("balance", {}); uid = str(uid)
    bal[uid] = max(0, bal.get(uid, START_BALANCE) + amount)
    save_cfg(cfg); return bal[uid]

def is_vip(peer_id, uid):
    c = get_chat(peer_id)
    if not c: return False
    return c.get("subs", {}).get(str(uid), 0) > time.time()

def vip_multiplier(peer_id, uid): return 1 + VIP_BONUS if is_vip(peer_id, uid) else 1.0

def get_role_key(uid, peer_id):
    if int(uid) == int(cfg["global_owner"]): return "global"
    grole = cfg.get("global_staff", {}).get(str(uid))
    if not is_chat(peer_id): return grole
    c = get_chat(peer_id)
    if c.get("owner") == uid: return "owner"
    local = c.get("staff", {}).get(str(uid))
    if local: return local
    return grole

def find_role(role_key, peer_id):
    if not role_key: return None
    if is_chat(peer_id):
        r = get_chat(peer_id).get("local_roles", {}).get(role_key)
        if r: return r
    return cfg["roles"].get(role_key)

def role_display(uid, peer_id):
    k = get_role_key(uid, peer_id)
    if k == "global": return "🌐 Главный владелец"
    if k == "owner": return "👑 Владелец беседы"
    r = find_role(k, peer_id)
    return r["name"] if r else "нет"

def can(uid, cmd, peer_id):
    if int(uid) == int(cfg["global_owner"]): return True
    if cmd in PUBLIC_CMDS: return True
    if not is_chat(peer_id): return False
    c = get_chat(peer_id)
    if c.get("owner") == uid:
        return cmd not in ("newrole","delrole","createivent","grole","removerole","gstaff") and cmd not in GLOBAL_ONLY
    rk = c.get("staff", {}).get(str(uid)) or cfg.get("global_staff", {}).get(str(uid))
    if not rk: return False
    role = find_role(rk, peer_id)
    return role and cmd in role.get("commands", [])

def extract_user(text, reply_msg=None):
    m = re.search(r"\[id(\d+)\|", text)
    if m: return int(m.group(1))
    m = re.search(r"@id(\d+)", text)
    if m: return int(m.group(1))
    if reply_msg: return reply_msg.get("from_id")
    return None

def kick_user(cid, uid):
    try: api.messages.removeChatUser(chat_id=cid, user_id=uid); return True, None
    except Exception as e: return False, str(e)

def delete_msg(mid, cmid=None, peer_id=None):
    if cmid and peer_id:
        try: api.messages.delete(conversation_message_ids=cmid, peer_id=peer_id, delete_for_all=1); return True
        except Exception as e: print(f"[del] {e}")
    if mid and mid > 0:
        try: api.messages.delete(message_ids=mid, delete_for_all=1); return True
        except Exception: pass
    return False

def fmt_time(s):
    s = int(s)
    if s < 60: return f"{s} сек"
    if s < 3600: return f"{s // 60} мин"
    if s < 86400:
        h = s // 3600; m = s % 3600 // 60
        return f"{h} ч {m} мин" if m else f"{h} ч"
    d = s // 86400; h = s % 86400 // 3600
    return f"{d} д {h} ч" if h else f"{d} д"

def fmt_dt(ts):
    if not ts: return "—"
    return time.strftime("%d.%m.%Y %H:%M", time.localtime(ts))

def fmt_num(n): return f"{int(n):,}".replace(",", " ")

def mute_notify_dm(uid, minutes): send_dm(uid, f"🔇 Мут на {minutes} мин.")
def mute_warn_dm(uid, rem): send_dm(uid, f"🔇 В муте. Осталось: {fmt_time(rem)}")
def mute_expired_dm(uid): send_dm(uid, "🔊 Ваш мут снят.")

def get_mute_until(info):
    return info.get("until", 0) if isinstance(info, dict) else (info or 0)

def find_role_by_input(s, peer_id=None):
    sl = (s or "").lower().strip()
    if not sl: return None
    if is_chat(peer_id):
        for k, v in get_chat(peer_id).get("local_roles", {}).items():
            if k.lower() == sl or v.get("name","").lower() == sl: return k
    for k in cfg["roles"]:
        if k.lower() == sl: return k
    for k, v in cfg["roles"].items():
        if v.get("name", "").lower() == sl: return k
    if sl.isdigit():
        p = int(sl)
        if is_chat(peer_id):
            for k, v in get_chat(peer_id).get("local_roles", {}).items():
                if v.get("priority") == p: return k
        for k, v in cfg["roles"].items():
            if v.get("priority") == p: return k
    return None

# ================================================================
# СТРАНЫ — ХЕЛПЕРЫ
# ================================================================
def get_country(key):
    if not key: return None
    return cfg.get("countries", {}).get(key)

def get_citizenship(uid):
    return cfg.get("citizens", {}).get(str(uid))

def set_citizenship(uid, country_key, rank="гражданин"):
    old = get_citizenship(uid)
    if old and old.get("country") != country_key:
        oc = get_country(old["country"])
        if oc and uid in oc.get("citizens", []): oc["citizens"].remove(uid)
        if oc and oc.get("president") == uid: oc["president"] = None
        if oc and oc.get("commander") == uid: oc["commander"] = None
        if oc:
            for pos, u in list(oc.get("government", {}).items()):
                if u == uid: del oc["government"][pos]
    c = cfg.setdefault("citizens", {})
    c[str(uid)] = {"country": country_key, "rank": rank,
                    "joined_at": int(time.time()), "donated": 0,
                    "hostage_until": 0}
    country = get_country(country_key)
    if country and uid not in country["citizens"]: country["citizens"].append(uid)
    save_cfg(cfg)

def country_income_mult(uid):
    cit = get_citizenship(uid)
    if not cit: return 1.0
    return RANKS.get(cit.get("rank", "гражданин"), {}).get("bonus_mult", 1.0)

def full_vip_mult(peer_id, uid):
    return vip_multiplier(peer_id, uid) * country_income_mult(uid)

def country_army_power(key):
    c = get_country(key)
    if not c or c.get("destroyed"): return 0
    base = c.get("army", 0) * (ARMY_LEVEL_MULT ** (c.get("army_level", 1) - 1))
    wp = sum(WEAPONS.get(w, {}).get("power", 0) * cnt for w, cnt in c.get("weapons", {}).items())
    return int(base + wp)

def country_name(key):
    return COUNTRIES.get(key, {}).get("name", key)

def country_add_history(key, text):
    c = get_country(key)
    if not c: return
    c.setdefault("history", []).insert(0, {"at": int(time.time()), "text": text})
    c["history"] = c["history"][:20]

def broadcast_country(key, text):
    c = get_country(key)
    if not c: return
    for uid in c.get("citizens", []):
        send_dm(uid, f"🏛 [{country_name(key)}] {text}")

# ================================================================
# ДОНАТ / СИРЕНА / ВЫДАТЬ
# ================================================================
def cmd_donate(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit:
        send(peer_id, "⚠ Только граждане могут донатить.\n/гражданство <страна>"); return
    if not args or not args[0].isdigit():
        send(peer_id, "⚠ /донат <сумма>\nПример: /донат 50000"); return
    amount = int(args[0])
    if amount <= 0: send(peer_id, "⚠ Сумма > 0"); return
    bal = get_balance(peer_id, uid)
    if bal < amount:
        send(peer_id, f"❌ У вас {fmt_num(bal)} 💵, не хватает."); return
    key = cit["country"]; c = get_country(key)
    if c.get("destroyed"):
        send(peer_id, "❌ Страна уничтожена — донат невозможен."); return
    add_balance(peer_id, uid, -amount)
    c["treasury"] = c.get("treasury", 0) + amount
    cfg["citizens"][str(uid)]["donated"] = cfg["citizens"][str(uid)].get("donated", 0) + amount
    country_add_history(key, f"{mention(uid)} пожертвовал {fmt_num(amount)} 💵")
    save_cfg(cfg)
    send(peer_id,
         f"💵 Пожертвовано: {fmt_num(amount)} 💵 в казну {country_name(key)}!\n\n"
         f"💰 Казна: {fmt_num(c.get('treasury', 0))}\n"
         f"🎖️ Всего вложено: {fmt_num(cfg['citizens'][str(uid)]['donated'])}")
    broadcast_country(key, f"💵 {mention(uid)} пожертвовал {fmt_num(amount)} 💵 в казну!")

def cmd_siren(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Только граждане."); return
    key = cit["country"]; c = get_country(key)
    if c.get("president") != uid and c.get("commander") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔ Только президент или главком."); return
    if c.get("destroyed"): send(peer_id, "❌ Страна уничтожена."); return
    if not args: send(peer_id, "⚠ /сирена <город>\nПример: /сирена Москва"); return
    city = " ".join(args).title()
    city_match = next((x for x in CITIES if x.lower() == city.lower()), None)
    if not city_match: send(peer_id, "❌ Город не найден."); return
    if CITIES.index(city_match) >= c.get("cities_unlocked", 3):
        send(peer_id, "❌ Город не открыт."); return
    c["cities"][city_match]["siren"] = True
    country_add_history(key, f"воздушная тревога в {city_match}")
    save_cfg(cfg)
    broadcast_country(key,
        f"🚨🚨🚨 ВОЗДУШНАЯ ТРЕВОГА 🚨🚨🚨\n\n"
        f"🏙 Город: {city_match}\n"
        f"🌍 Страна: {country_name(key)}\n\n"
        f"⚠️ Немедленно проследуйте в укрытие!")
    def clear_siren():
        time.sleep(300)
        cc = get_country(key)
        if cc and city_match in cc.get("cities", {}):
            cc["cities"][city_match]["siren"] = False; save_cfg(cfg)
        broadcast_country(key, f"🟢 Отбой тревоги в {city_match}.")
    threading.Thread(target=clear_siren, daemon=True).start()
    send(peer_id, f"🚨 Тревога в {city_match} запущена!")

def cmd_siren_all(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Только граждане."); return
    key = cit["country"]; c = get_country(key)
    if c.get("president") != uid and c.get("commander") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔ Нет прав."); return
    if c.get("destroyed"): send(peer_id, "❌ Страна уничтожена."); return
    for city in list(c.get("cities", {}).keys()):
        c["cities"][city]["siren"] = True
    country_add_history(key, "всеобщая воздушная тревога")
    save_cfg(cfg)
    broadcast_country(key,
        f"🚨🚨🚨 ВСЕОБЩАЯ ВОЗДУШНАЯ ТРЕВОГА 🚨🚨🚨\n\n"
        f"🌍 {country_name(key)}\n⚠️ Всем в укрытие!")
    def clear_all():
        time.sleep(600)
        cc = get_country(key)
        if cc:
            for city in cc.get("cities", {}): cc["cities"][city]["siren"] = False
            save_cfg(cfg)
        broadcast_country(key, "🟢 Отбой тревоги.")
    threading.Thread(target=clear_all, daemon=True).start()
    send(peer_id, "🚨 Всеобщая тревога!")

def cmd_give(peer_id, uid, args, reply_msg, text):
    if uid != int(cfg["global_owner"]):
        send(peer_id, "⛔ Только Главный владелец."); return
    if not args:
        send(peer_id,
             "📋 <b>Выдача ресурсов:</b>\n\n"
             "💰 /выдать деньги @user <сумма>\n"
             "💰 /выдать деньги казна <страна> <сумма>\n"
             "🔫 /выдать оружие @user <тип> <кол>\n"
             "🔫 /выдать оружие казна <страна> <тип> <кол>\n"
             "🎖️ /выдать военных <страна> <кол>\n"
             "👑 /выдать вип @user\n"
             "☢️ /выдать ядерка <страна> <кол>")
        return
    kind = args[0].lower()
    if kind == "деньги":
        if len(args) >= 2 and args[1].lower() in ("казна","страна"):
            if len(args) < 4 or not args[-1].isdigit():
                send(peer_id, "⚠ /выдать деньги казна <страна> <сумма>"); return
            key = args[2].lower()
            if key not in COUNTRIES: send(peer_id, "⚠ Страна не найдена."); return
            amount = int(args[-1])
            c = get_country(key)
            c["treasury"] = c.get("treasury", 0) + amount
            country_add_history(key, f"Global выдал +{fmt_num(amount)}")
            save_cfg(cfg)
            send(peer_id, f"✅ В казну {country_name(key)}: +{fmt_num(amount)} 💵")
            broadcast_country(key, f"💵 Global выдал {fmt_num(amount)} 💵!")
            return
        t = extract_user(text, reply_msg)
        if not t: send(peer_id, "⚠ @user или казна"); return
        amount = None
        for a in args:
            if a.isdigit() and int(a) > 0: amount = int(a); break
        if not amount: send(peer_id, "⚠ Сумма"); return
        nb = add_balance(peer_id, t, amount)
        send(peer_id, f"✅ {mention(t, peer_id)}: +{fmt_num(amount)} 💵")
        send_dm(t, f"💰 Global выдал {fmt_num(amount)} 💵!")
        return
    if kind == "оружие":
        if len(args) >= 2 and args[1].lower() in ("казна","страна"):
            if len(args) < 5: send(peer_id, "⚠ /выдать оружие казна <страна> <тип> <кол>"); return
            key = args[2].lower(); weapon = args[3].lower()
            if not args[4].isdigit(): send(peer_id, "⚠ Кол-во"); return
            cnt = int(args[4])
            if key not in COUNTRIES or weapon not in WEAPONS:
                send(peer_id, "⚠ Страна/оружие не найдены."); return
            c = get_country(key)
            c.setdefault("weapons", {})[weapon] = c.get("weapons", {}).get(weapon, 0) + cnt
            country_add_history(key, f"выдано {cnt} {weapon}")
            save_cfg(cfg)
            send(peer_id, f"✅ {country_name(key)}: +{cnt} {weapon}")
            return
        t = extract_user(text, reply_msg)
        if not t: send(peer_id, "⚠ @user"); return
        weapon = None
        for a in args:
            if a.lower() in WEAPONS: weapon = a.lower(); break
        cnt = None
        for a in args:
            if a.isdigit() and int(a) > 0: cnt = int(a); break
        if not weapon or not cnt: send(peer_id, "⚠ /выдать оружие @user <тип> <кол>"); return
        send(peer_id, f"✅ {mention(t, peer_id)}: +{cnt} {weapon}")
        send_dm(t, f"🔫 Global выдал {cnt} {weapon}!")
        return
    if kind == "военных":
        if len(args) < 3 or not args[-1].isdigit():
            send(peer_id, "⚠ /выдать военных <страна> <кол>"); return
        key = args[1].lower()
        if key not in COUNTRIES: send(peer_id, "⚠ Страна не найдена."); return
        cnt = int(args[-1])
        c = get_country(key)
        c["army"] = c.get("army", 0) + cnt
        country_add_history(key, f"выдано {cnt} войск")
        save_cfg(cfg)
        send(peer_id, f"✅ {country_name(key)}: +{fmt_num(cnt)} войск")
        broadcast_country(key, f"🎖️ Global выдал {fmt_num(cnt)} войск!")
        return
    if kind == "вип":
        t = extract_user(text, reply_msg)
        if not t: send(peer_id, "⚠ @user"); return
        c = get_chat(peer_id)
        if c:
            until = int(time.time()) + VIP_DURATION
            c.setdefault("subs", {})[str(t)] = until; save_cfg(cfg)
        send(peer_id, f"✅ {mention(t, peer_id)} — VIP на 30 дней!")
        send_dm(t, "👑 Global выдал VIP на 30 дней!")
        return
    if kind == "ядерка":
        if len(args) < 3 or not args[-1].isdigit():
            send(peer_id, "⚠ /выдать ядерка <страна> <кол>"); return
        key = args[1].lower()
        if key not in COUNTRIES: send(peer_id, "⚠ Страна не найдена."); return
        cnt = int(args[-1])
        c = get_country(key)
        c["nukes"] = c.get("nukes", 0) + cnt
        country_add_history(key, f"выдано {cnt} ядерных бомб")
        save_cfg(cfg)
        send(peer_id, f"✅ {country_name(key)}: +{cnt} ядерных бомб ☢️")
        broadcast_country(key, f"☢️ Global выдал {cnt} ядерных бомб!")
        return
    send(peer_id, "⚠ Типы: деньги, оружие, военных, вип, ядерка")

# ================================================================
# СТРАНЫ — ОСНОВНЫЕ КОМАНДЫ
# ================================================================
def cmd_countries(peer_id, uid):
    lines = ["🌍 <b>Страны мира:</b>", ""]
    for k, c in COUNTRIES.items():
        country = get_country(k) or {}
        if country.get("destroyed"):
            captor = country.get("captured_by")
            captor_name = country_name(captor) if captor else "?"
            lines.append(f"☠️ {c['name']} — <b>УНИЧТОЖЕНА</b>")
            lines.append(f"   💀 Захвачена: {captor_name}")
            host = country.get("hostages", [])
            if host: lines.append(f"   🔒 Заложников: {len(host)}")
            continue
        pres = country.get("president")
        army = country.get("army", 0)
        cities = country.get("cities_unlocked", 3)
        pres_txt = mention(pres, peer_id) if pres else "❌ нет"
        lines.append(f"{c['name']}")
        lines.append(f"   👑 {pres_txt}")
        lines.append(f"   ⚔️ Армия: {fmt_num(army)} | 🏙 Городов: {cities}/20")
        if country.get("nukes", 0) > 0:
            lines.append(f"   ☢️ Ядерных бомб: {country['nukes']}")
    lines.append("")
    lines.append("📔 /паспорт | 🏛 /страна <название> | 🏛 /госскоманды")
    send(peer_id, "\n".join(lines))

def cmd_citizenship(peer_id, uid, args):
    if not args:
        cit = get_citizenship(uid)
        if cit:
            cn = country_name(cit["country"])
            rank = RANKS.get(cit["rank"], {}).get("name", cit["rank"])
            hostage = cit.get("hostage_until", 0) > time.time()
            extra = "\n🔒 ВЫ В ЗАЛОЖНИКАХ!" if hostage else ""
            send(peer_id, f"🌍 Гражданин {cn}\n🎖️ Должность: {rank}{extra}\n\n📔 /паспорт")
        else:
            lines = ["🌍 Доступные страны:"]
            for k, c in COUNTRIES.items():
                country = get_country(k)
                mark = " ☠️" if country and country.get("destroyed") else ""
                lines.append(f"• {k} — {c['name']}{mark}")
            lines.append("\nВступить: /гражданство <название>")
            send(peer_id, "\n".join(lines))
        return
    key = args[0].lower()
    if key not in COUNTRIES: send(peer_id, "❌ Страна не найдена. /страны"); return
    c = get_country(key)
    if c.get("destroyed"):
        send(peer_id, "❌ Страна уничтожена — нельзя вступить."); return
    cit = get_citizenship(uid)
    if cit and cit["country"] == key:
        send(peer_id, "ℹ Вы уже гражданин."); return
    set_citizenship(uid, key)
    send(peer_id, f"🎉 Вы стали гражданином {country_name(key)}!\n\n📔 /паспорт\n🏛 /страна {key}")
    broadcast_country(key, f"👋 Новый гражданин: {mention(uid)}")

def cmd_passport(peer_id, uid, args, reply_msg):
    target = extract_user(" ".join(args), reply_msg) or uid
    cit = get_citizenship(target)
    if not cit:
        send(peer_id, "❌ Не гражданин."); return
    c = get_country(cit["country"]) or {}
    cn = country_name(cit["country"])
    rank_name = RANKS.get(cit["rank"], {}).get("name", cit["rank"])
    bal = get_balance(peer_id, target)
    prefetch_names([target])
    hostage = cit.get("hostage_until", 0) > time.time()
    lines = [
        "📔 ═══ ПАСПОРТ ═══",
        f"👤 {mention(target, peer_id)}",
        f"🌍 Страна: {cn}",
        f"🎖️ Должность: {rank_name}",
        f"💰 Баланс: {fmt_num(bal)}",
        f"📅 Вступил: {fmt_dt(cit['joined_at'])}",
        f"💵 Вложено: {fmt_num(cit.get('donated', 0))}",
    ]
    if hostage:
        lines.append(f"🔒 ЗАЛОЖНИК до {fmt_dt(cit['hostage_until'])}")
    lines.extend([
        "",
        "🏛 О стране:",
        f"👑 Президент: {mention(c.get('president'), peer_id) if c.get('president') else '—'}",
        f"🎖️ Главком: {mention(c.get('commander'), peer_id) if c.get('commander') else '—'}",
        f"👥 Граждан: {len(c.get('citizens', []))}",
        f"💰 Казна: {fmt_num(c.get('treasury', 0))}",
        f"⚔️ Армия: {fmt_num(c.get('army', 0))} (ур. {c.get('army_level', 1)})",
    ])
    send(peer_id, "\n".join(lines))

def cmd_country_info(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not args and not cit:
        send(peer_id, "⚠ /страна <название>"); return
    key = (args[0].lower() if args else cit["country"])
    if key not in COUNTRIES: send(peer_id, "❌ Не найдена."); return
    c = get_country(key) or {}
    if c.get("destroyed"):
        captor = c.get("captured_by")
        captor_name = country_name(captor) if captor else "?"
        host = c.get("hostages", [])
        lines = [
            f"☠️ ═══ {country_name(key)} — УНИЧТОЖЕНА ═══",
            "",
            f"💀 Захвачена: {captor_name}",
            f"🗓 Дата: {fmt_dt(c.get('destroyed_at', 0))}",
            f"🔒 Заложников: {len(host)}",
            "",
            "📋 /граждане",
        ]
        send(peer_id, "\n".join(lines)); return
    lines = [
        f"🏛 ═══ {country_name(key)} ═══",
        f"👑 Президент: {mention(c.get('president'), peer_id) if c.get('president') else '—'}",
        f"🎖️ Главком: {mention(c.get('commander'), peer_id) if c.get('commander') else '—'}",
        f"👥 Граждан: {len(c.get('citizens', []))}",
        f"⚔️ Армия: {fmt_num(c.get('army', 0))} (ур. {c.get('army_level', 1)})",
        f"🎯 Мощь: {fmt_num(country_army_power(key))}",
        f"💰 Казна: {fmt_num(c.get('treasury', 0))}",
        f"🏙 Городов: {c.get('cities_unlocked', 3)}/20",
        f"💼 Налог: {c.get('tax', 5)}%",
        f"🤝 Коалиция: {c.get('coalition') or '—'}",
        f"⚔️ Войн: {len(c.get('wars', []))}",
        f"☢️ Ядерных бомб: {c.get('nukes', 0)}",
        "",
        "📋 /граждане /города /казна /правительство /армия",
    ]
    send(peer_id, "\n".join(lines))

def cmd_citizens(peer_id, uid, args):
    if not args:
        cit = get_citizenship(uid)
        if not cit: send(peer_id, "⚠ /граждане <страна>"); return
        key = cit["country"]
    else: key = args[0].lower()
    if key not in COUNTRIES: send(peer_id, "❌ Не найдена."); return
    c = get_country(key) or {}
    uids = c.get("citizens", [])
    if not uids: send(peer_id, f"📭 Нет граждан."); return
    prefetch_names(uids[:30])
    lines = [f"👥 Граждане {country_name(key)} ({len(uids)}):", ""]
    for u in uids[:30]:
        u_cit = get_citizenship(u) or {}
        rank = RANKS.get(u_cit.get("rank","гражданин"), {}).get("name", "👤")
        lines.append(f"• {mention(u, peer_id)} — {rank}")
    if len(uids) > 30: lines.append(f"…и ещё {len(uids)-30}")
    send(peer_id, "\n".join(lines))

def cmd_cities(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Стань гражданином."); return
    key = cit["country"]; c = get_country(key) or {}
    unlocked = c.get("cities_unlocked", 3)
    lines = [f"🏙 Города {country_name(key)} — {unlocked}/20", ""]
    for i, city in enumerate(CITIES, 1):
        if i <= unlocked:
            city_data = c.get("cities", {}).get(city, {})
            bcount = len(city_data.get("buildings", []))
            siren = " 🚨" if city_data.get("siren") else ""
            lines.append(f"{i}. ✅ {city} — построек: {bcount}{siren}")
        else: lines.append(f"{i}. 🔒 {city} — закрыто")
    send(peer_id, "\n".join(lines))

def cmd_treasury(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Стань гражданином."); return
    key = cit["country"]; c = get_country(key) or {}
    if args and args[0].lower() in ("история","history","log"):
        h = c.get("history", [])[:10]
        if not h: send(peer_id, "📭 История пуста."); return
        lines = ["📜 История казны:"]
        for item in h: lines.append(f"• {fmt_dt(item['at'])} — {item['text']}")
        send(peer_id, "\n".join(lines)); return
    lines = [
        f"💰 Казна {country_name(key)}",
        "",
        f"Баланс: {fmt_num(c.get('treasury', 0))} 💵",
        f"Налог: {c.get('tax', 5)}%",
        f"Граждан: {len(c.get('citizens', []))}",
        "",
        "💵 /донат <сумма> — пополнить",
        "📜 /казна история",
    ]
    send(peer_id, "\n".join(lines))

def cmd_government(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Стань гражданином."); return
    key = cit["country"]; c = get_country(key) or {}
    gov = c.get("government", {})
    lines = [f"🏛 Правительство {country_name(key)}", ""]
    pres = c.get("president")
    lines.append(f"👑 Президент: {mention(pres, peer_id) if pres else '—'}")
    com = c.get("commander")
    lines.append(f"🎖️ Главком: {mention(com, peer_id) if com else '—'}")
    for pos in GOV_POSITIONS:
        if pos in ("президент","главнокомандующий"): continue
        u = gov.get(pos)
        lines.append(f"• {pos.title()}: {mention(u, peer_id) if u else '—'}")
    send(peer_id, "\n".join(lines))

def cmd_positions(peer_id, uid, args):
    lines = ["🏛 Должности:", ""]
    for pos in GOV_POSITIONS: lines.append(f"• {pos.title()}")
    send(peer_id, "\n".join(lines))

def cmd_army(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Стань гражданином."); return
    key = cit["country"]; c = get_country(key) or {}
    if args and args[0].lower() in ("выйти","leave"):
        c["army"] = max(0, c.get("army", 0) - 1000); save_cfg(cfg)
        send(peer_id, "🎖️ Уволились из армии (-1000)"); return
    weapons = c.get("weapons", {})
    w_str = "\n".join(f"   {WEAPONS[w]['emoji']} {w.title()}: {cnt}" for w, cnt in weapons.items() if cnt)
    lines = [
        f"⚔️ Армия {country_name(key)}",
        "",
        f"👥 Войск: {fmt_num(c.get('army', 0))}",
        f"🎖️ Уровень: {c.get('army_level', 1)}/{ARMY_LEVEL_MAX}",
        f"🎯 Мощь: {fmt_num(country_army_power(key))}",
        f"☢️ Ядерных бомб: {c.get('nukes', 0)}",
        "",
        "🔫 <b>Техника:</b>",
        w_str if w_str else "   (нет)",
    ]
    send(peer_id, "\n".join(lines))

def cmd_elections(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Стань гражданином."); return
    key = cit["country"]; c = get_country(key) or {}
    el = c.get("elections", {})
    if not el.get("active"):
        pres = c.get("president")
        send(peer_id, f"🗳️ Выборы неактивны\n👑 Президент: {mention(pres, peer_id) if pres else '—'}\n\n/выдвинуться"); return
    cands = el.get("candidates", []); votes = el.get("votes", {})
    lines = [f"🗳️ ВЫБОРЫ в {country_name(key)}", ""]
    for i, cand in enumerate(cands, 1):
        vc = sum(1 for v in votes.values() if v == cand)
        lines.append(f"{i}. {mention(cand, peer_id)} — {vc}")
    lines.append(f"\n🗳️ /голос <номер>")
    send(peer_id, "\n".join(lines))

def cmd_run_for_president(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Только граждане."); return
    key = cit["country"]; c = get_country(key) or {}
    el = c.setdefault("elections", {"candidates": [], "votes": {}, "ends_at": 0, "active": False})
    if el["active"]: send(peer_id, "⚠ Выборы идут."); return
    if uid in el["candidates"]: send(peer_id, "⚠ Вы уже кандидат."); return
    el["candidates"].append(uid)
    if len(el["candidates"]) >= 2 and not el["active"]:
        el["active"] = True; el["ends_at"] = int(time.time()) + 3600; el["votes"] = {}
        broadcast_country(key, "🗳️ НАЧАЛИСЬ ВЫБОРЫ!")
    save_cfg(cfg)
    send(peer_id, f"✅ Выдвинулись в президенты!")

def cmd_vote(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Только граждане."); return
    key = cit["country"]; c = get_country(key) or {}
    el = c.get("elections", {})
    if not el.get("active"): send(peer_id, "⚠ Выборы неактивны."); return
    if uid in el.get("votes", {}): send(peer_id, "⚠ Уже голосовали."); return
    if not args or not args[0].isdigit(): send(peer_id, "⚠ /голос <номер>"); return
    idx = int(args[0]) - 1; cands = el.get("candidates", [])
    if not 0 <= idx < len(cands): send(peer_id, "⚠ Неверный номер."); return
    el["votes"][str(uid)] = cands[idx]; save_cfg(cfg)
    send(peer_id, f"🗳️ Голос за {mention(cands[idx], peer_id)}!")

def cmd_tax(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Только граждане."); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔ Только президент."); return
    if not args or not args[0].isdigit():
        send(peer_id, f"⚠ /налоги <1-20>. Сейчас: {c.get('tax', 5)}%"); return
    t = int(args[0])
    if not 1 <= t <= 20: send(peer_id, "⚠ 1-20"); return
    c["tax"] = t; country_add_history(key, f"налог {t}%"); save_cfg(cfg)
    send(peer_id, f"💰 Налог: {t}%")

def cmd_appoint(peer_id, uid, args, reply_msg):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Только граждане."); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔ Только президент."); return
    if not args: send(peer_id, "⚠ /назначить @user <должность>"); return
    t = extract_user(" ".join(args), reply_msg)
    if not t: send(peer_id, "⚠ @user"); return
    pos = None
    for a in args:
        low = a.lower()
        for p in GOV_POSITIONS:
            if p in low or low in p: pos = p; break
        if pos: break
    if not pos: send(peer_id, f"⚠ Должность. Есть: {', '.join(GOV_POSITIONS)}"); return
    t_cit = get_citizenship(t)
    if not t_cit or t_cit["country"] != key: send(peer_id, "⚠ Не гражданин."); return
    c.setdefault("government", {})[pos] = t
    country_add_history(key, f"{mention(t)} на {pos}")
    save_cfg(cfg)
    send(peer_id, f"✅ {mention(t, peer_id)} — {pos.title()}")
    send_dm(t, f"🏛 Назначение на «{pos.title()}» в {country_name(key)}!")

def cmd_remove_minister(peer_id, uid, args, reply_msg):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Только граждане."); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔ Только президент."); return
    t = extract_user(" ".join(args), reply_msg)
    if not t: send(peer_id, "⚠ @user"); return
    removed = []
    for pos, u in list(c.get("government", {}).items()):
        if u == t: del c["government"][pos]; removed.append(pos)
    save_cfg(cfg)
    send(peer_id, f"❌ Снят с: {', '.join(removed)}" if removed else "ℹ Нет должностей.")

def cmd_military_rank(peer_id, uid, args, reply_msg):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Только граждане."); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("commander") != uid and c.get("president") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔ Нет прав."); return
    t = extract_user(" ".join(args), reply_msg)
    if not t: send(peer_id, "⚠ @user"); return
    rank_num = None
    for a in args:
        if a.isdigit() and 1 <= int(a) <= 10: rank_num = int(a); break
    if not rank_num: send(peer_id, "⚠ 1-10"); return
    c.setdefault("mil_ranks", {})[str(t)] = rank_num
    save_cfg(cfg)
    send(peer_id, f"🎖️ {mention(t, peer_id)} — звание {rank_num}")

def cmd_improve_country(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Только граждане."); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔ Только президент."); return
    unlocked = c.get("cities_unlocked", 3)
    if unlocked >= 20: send(peer_id, "⚠ Все 20 открыты."); return
    cost = 500000 * unlocked
    dev_points = len(c.get("government", {})) * 10 + c.get("army_level", 1) * 5
    if c.get("treasury", 0) < cost:
        send(peer_id, f"❌ Нужно {fmt_num(cost)} 💵"); return
    if dev_points < unlocked * 5:
        send(peer_id, f"❌ Нужно минимум {unlocked*5} очков развития (у вас {dev_points})"); return
    c["treasury"] -= cost
    c["cities_unlocked"] = unlocked + 1
    new_city = CITIES[unlocked]
    c.setdefault("cities", {})[new_city] = {"buildings": [], "pvo": 0, "siren": False}
    country_add_history(key, f"открыт {new_city}")
    save_cfg(cfg)
    broadcast_country(key, f"🏙 Открыт город: {new_city}!")

def cmd_buildings(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Только граждане."); return
    key = cit["country"]; c = get_country(key) or {}
    if not args:
        send(peer_id, "⚠ /постройки <город>"); return
    city = " ".join(args).title()
    city_match = next((x for x in CITIES if x.lower() == city.lower()), None)
    if not city_match: send(peer_id, "❌ Город не найден."); return
    if CITIES.index(city_match) >= c.get("cities_unlocked", 3):
        send(peer_id, "❌ Город не открыт."); return
    b = c.get("cities", {}).get(city_match, {}).get("buildings", [])
    if not b: send(peer_id, f"🏙 {city_match}: нет построек."); return
    lines = [f"🏙 {city_match}:"]
    for x in b: lines.append(f"   {BUILDINGS.get(x, {}).get('emoji','🏢')} {x.title()}")
    send(peer_id, "\n".join(lines))

def cmd_build_obj(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Только граждане."); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔ Только президент."); return
    if len(args) < 2: send(peer_id, "⚠ /построить <объект> <город>"); return
    b_name = args[0].lower()
    if b_name not in BUILDINGS:
        send(peer_id, f"⚠ Объект. Есть: {', '.join(BUILDINGS.keys())}"); return
    city_name = " ".join(args[1:]).title()
    city_match = next((x for x in CITIES if x.lower() == city_name.lower()), None)
    if not city_match: send(peer_id, "❌ Город не найден."); return
    if CITIES.index(city_match) >= c.get("cities_unlocked", 3):
        send(peer_id, "❌ Город не открыт."); return
    b_info = BUILDINGS[b_name]
    if c.get("treasury", 0) < b_info["cost"]:
        send(peer_id, f"❌ Нужно {fmt_num(b_info['cost'])} 💵"); return
    b_list = c.setdefault("cities", {}).setdefault(city_match, {}).setdefault("buildings", [])
    if b_name in b_list: send(peer_id, "⚠ Уже построено."); return
    c["treasury"] -= b_info["cost"]
    b_list.append(b_name)
    if b_name == "казарма": c["army"] = c.get("army", 0) + 5000
    country_add_history(key, f"{b_name} в {city_match}")
    save_cfg(cfg)
    send(peer_id, f"✅ {b_info['emoji']} {b_name.title()} в {city_match}!\n➕ {b_info['bonus']}")

def cmd_state_project(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Только граждане."); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔ Только президент."); return
    if len(args) < 2:
        send(peer_id, "⚠ /госпроект <тип> <название>\nТипы: наука, экономика, военный, культурный")
        return
    ptype, pname = args[0].lower(), " ".join(args[1:])
    if ptype not in ("наука","экономика","военный","культурный"):
        send(peer_id, "⚠ Тип неверный."); return
    c.setdefault("projects", []).append({"type": ptype, "name": pname, "at": int(time.time())})
    save_cfg(cfg)
    send(peer_id, f"🏛 Запущен проект «{pname}» ({ptype})")
    broadcast_country(key, f"🏛 Госпроект: «{pname}» ({ptype})")

def cmd_armament(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Только граждане."); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔ Только президент."); return
    if not args or not args[0].isdigit(): send(peer_id, "⚠ /вооружение <сумма>"); return
    amount = int(args[0])
    if c.get("treasury", 0) < amount:
        send(peer_id, f"❌ Мало в казне."); return
    c["treasury"] -= amount
    bought = []; remaining = amount
    for w_key, w_info in sorted(WEAPONS.items(), key=lambda x: -x[1]["cost"]):
        if remaining < w_info["cost"]: continue
        cnt = remaining // w_info["cost"]
        c.setdefault("weapons", {})[w_key] = c.get("weapons", {}).get(w_key, 0) + cnt
        bought.append(f"{w_info['emoji']} {w_key.title()} ×{cnt}")
        remaining -= cnt * w_info["cost"]
    save_cfg(cfg)
    send(peer_id, "🛒 Закупка:\n" + ("\n".join(bought) if bought else "Ничего."))

# ================================================================
# ВОЙНА
# ================================================================
def cmd_wars(peer_id, uid, args):
    wars = cfg.get("wars", [])
    if not wars: send(peer_id, "☮️ Активных войн нет."); return
    lines = ["⚔️ <b>Активные войны:</b>", ""]
    for i, w in enumerate(wars, 1):
        a = country_name(w["a"]); b = country_name(w["b"])
        started = fmt_dt(w.get("started_at", 0))
        lines.append(f"{i}. {a} ⚔️ {b}")
        lines.append(f"   Начало: {started}")
    send(peer_id, "\n".join(lines))

def cmd_declare_war(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Только граждане."); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔ Только президент."); return
    if c.get("destroyed"): send(peer_id, "❌ Страна уничтожена."); return
    if not args: send(peer_id, "⚠ /война <страна>"); return
    target = args[0].lower()
    if target not in COUNTRIES: send(peer_id, "❌ Не найдена."); return
    if target == key: send(peer_id, "⚠ Себя нельзя."); return
    tc = get_country(target)
    if tc.get("destroyed"): send(peer_id, "⚠ Уже уничтожена."); return
    if c.get("treasury", 0) < WAR_COST:
        send(peer_id, f"❌ Нужно {fmt_num(WAR_COST)} 💵 в казне.\nСейчас: {fmt_num(c.get('treasury', 0))}"); return
    for w in cfg.get("wars", []):
        if (w["a"] == key and w["b"] == target) or (w["a"] == target and w["b"] == key):
            send(peer_id, "⚠ Война уже идёт."); return
    c["treasury"] -= WAR_COST
    c.setdefault("wars", []).append(target)
    tc.setdefault("wars", []).append(key)
    cfg.setdefault("wars", []).append({"a": key, "b": target, "started_at": int(time.time()),
                                        "attacker": key, "defender": target})
    country_add_history(key, f"война {country_name(target)}")
    country_add_history(target, f"{country_name(key)} объявила войну")
    save_cfg(cfg)
    send(peer_id, f"⚔️ {country_name(key)} ОБЪЯВИЛА ВОЙНУ {country_name(target)}!")
    broadcast_country(key, f"⚔️ Мы объявили войну {country_name(target)}!")
    broadcast_country(target, f"🚨 {country_name(key)} ОБЪЯВИЛА НАМ ВОЙНУ!")

def cmd_capture(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Только граждане."); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔ Только президент."); return
    if not args: send(peer_id, "⚠ /захват <страна>"); return
    target = args[0].lower()
    if target not in COUNTRIES: send(peer_id, "❌ Не найдена."); return
    war = next((w for w in cfg.get("wars", []) if {w["a"], w["b"]} == {key, target}), None)
    if not war: send(peer_id, "❌ Сначала /война"); return
    send(peer_id, f"⏳ Кампания против {country_name(target)} ({WAR_CAPTURE_SECONDS//60} мин)...")
    broadcast_country(key, f"⚔️ Кампания против {country_name(target)}!")
    def resolve_capture():
        time.sleep(WAR_CAPTURE_SECONDS)
        a_pow = country_army_power(key); b_pow = country_army_power(target)
        a_roll = random.uniform(0.7, 1.3) * a_pow
        b_roll = random.uniform(0.7, 1.3) * b_pow * 1.1
        tc = get_country(target); c_fresh = get_country(key)
        if c_fresh.get("destroyed") or tc.get("destroyed"): return
        if a_roll > b_roll:
            loot = tc.get("treasury", 0)
            c_fresh["treasury"] = c_fresh.get("treasury", 0) + loot
            tc["treasury"] = 0; tc["army"] = 0
            tc["destroyed"] = True
            tc["captured_by"] = key
            tc["destroyed_at"] = int(time.time())
            pres = tc.get("president")
            if pres:
                tc.setdefault("hostages", []).append(pres)
                if get_citizenship(pres):
                    cfg["citizens"][str(pres)]["hostage_until"] = int(time.time()) + 86400
                send_dm(pres,
                    f"🔒 ВЫ В ЗАЛОЖНИКАХ!\n\n"
                    f"Страна {country_name(target)} уничтожена.\n"
                    f"Захватчик: {country_name(key)}\n"
                    f"Освобождение через 24ч.")
            for w in list(cfg.get("wars", [])):
                if {w["a"], w["b"]} == {key, target}: cfg["wars"].remove(w)
            if target in c_fresh.get("wars", []): c_fresh["wars"].remove(target)
            if key in tc.get("wars", []): tc["wars"].remove(key)
            country_add_history(key, f"УНИЧТОЖЕНА {country_name(target)}")
            country_add_history(target, f"УНИЧТОЖЕНА: {country_name(key)}")
            save_cfg(cfg)
            broadcast_country(key, f"🏆🏆🏆 ПОБЕДА! Уничтожена {country_name(target)}! +{fmt_num(loot)} 💵")
            broadcast_country(target, f"☠️☠️☠️ СТРАНА УНИЧТОЖЕНА! Президент в заложниках 24ч.")
        else:
            loss_a = int(c_fresh.get("army", 0) * 0.25)
            c_fresh["army"] = max(0, c_fresh.get("army", 0) - loss_a)
            loss_b = int(tc.get("army", 0) * 0.1)
            tc["army"] = max(0, tc.get("army", 0) - loss_b)
            country_add_history(key, f"поражение от {country_name(target)}")
            save_cfg(cfg)
            broadcast_country(key, f"💀 Кампания провалилась. Потери: {fmt_num(loss_a)}")
            broadcast_country(target, f"🛡️ Отбились от {country_name(key)}!")
    threading.Thread(target=resolve_capture, daemon=True).start()

def cmd_counter_defense(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Только граждане."); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔ Только президент."); return
    if c.get("counter_used"): send(peer_id, "⚠ Уже использовали."); return
    war = next((w for w in cfg.get("wars", []) if key in (w["a"], w["b"])), None)
    if not war: send(peer_id, "❌ Нет войны."); return
    enemy = war["b"] if war["a"] == key else war["a"]
    ec = get_country(enemy)
    if ec.get("destroyed"): send(peer_id, "⚠ Враг уже уничтожен."); return
    a_pow = country_army_power(key) * 1.5
    b_pow = country_army_power(enemy)
    if a_pow > b_pow:
        loss = int(ec.get("army", 0) * 0.4)
        ec["army"] = max(0, ec.get("army", 0) - loss)
        loot = int(ec.get("treasury", 0) * 0.25)
        ec["treasury"] -= loot; c["treasury"] = c.get("treasury", 0) + loot
        c["counter_used"] = True; save_cfg(cfg)
        broadcast_country(key, f"⚡ Контратака успешна! +{fmt_num(loot)} 💵")
        broadcast_country(enemy, f"💀 Контратака! Потери: {fmt_num(loss)}")
    else:
        c["counter_used"] = True
        loss = int(c.get("army", 0) * 0.2); c["army"] = max(0, c.get("army", 0) - loss)
        save_cfg(cfg)
        broadcast_country(key, f"💀 Контратака провалилась. -{fmt_num(loss)}")

def cmd_peace(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Только граждане."); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔ Только президент."); return
    if not args: send(peer_id, "⚠ /мир <страна>"); return
    target = args[0].lower()
    war = next((w for w in cfg.get("wars", []) if {w["a"], w["b"]} == {key, target}), None)
    if not war: send(peer_id, "❌ Войны нет."); return
    tc = get_country(target)
    if c.get("treasury", 0) < 500000 or tc.get("treasury", 0) < 500000:
        send(peer_id, "❌ Нужно по 500к у обеих."); return
    c["treasury"] -= 500000; tc["treasury"] -= 500000
    cfg["wars"].remove(war)
    if target in c.get("wars", []): c["wars"].remove(target)
    if key in tc.get("wars", []): tc["wars"].remove(key)
    country_add_history(key, f"мир {country_name(target)}")
    country_add_history(target, f"мир {country_name(key)}")
    save_cfg(cfg)
    broadcast_country(key, f"☮️ Мир с {country_name(target)}")
    broadcast_country(target, f"☮️ Мир с {country_name(key)}")

# ================================================================
# КОАЛИЦИИ
# ================================================================
def cmd_coalitions(peer_id, uid, args):
    coal = cfg.get("coalitions", {})
    if not coal: send(peer_id, "📭 Коалиций нет."); return
    lines = ["🤝 <b>Коалиции:</b>", ""]
    for name, data in coal.items():
        members = data.get("members", []); leader = data.get("leader")
        lines.append(f"🔹 <b>{name}</b> — {len(members)} стран")
        lines.append(f"   Лидер: {country_name(leader)}")
        for m in members:
            mark = "👑" if m == leader else "•"
            lines.append(f"   {mark} {country_name(m)}")
    send(peer_id, "\n".join(lines))

def cmd_coalition(peer_id, uid, args, reply_msg):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Только граждане."); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔ Только президент."); return
    coal = cfg.setdefault("coalitions", {})
    if not args:
        my_name = c.get("coalition")
        if not my_name:
            send(peer_id, "🤝 Не в коалиции.\n/коалиция <название>\n/коалиции"); return
        data = coal.get(my_name, {})
        send(peer_id, f"🤝 «{my_name}»\n👑 {country_name(data.get('leader'))}\n" +
             "\n".join(f"   • {country_name(m)}" for m in data.get("members", [])))
        return
    sub = args[0].lower()
    if sub == "пригласить" and len(args) >= 2:
        my_name = c.get("coalition")
        if not my_name: send(peer_id, "⚠ Не в коалиции."); return
        data = coal.get(my_name, {})
        if data.get("leader") != key: send(peer_id, "⛔ Только лидер."); return
        target = args[1].lower()
        if target not in COUNTRIES: send(peer_id, "⚠ Страна не найдена."); return
        if target in data.get("members", []): send(peer_id, "⚠ Уже в коалиции."); return
        data.setdefault("invites", []).append(target); save_cfg(cfg)
        send(peer_id, f"📨 Приглашение отправлено {country_name(target)}")
        broadcast_country(target, f"🤝 {country_name(key)} приглашает в «{my_name}»\n/коалиция вступить {my_name}")
        return
    if sub == "вступить" and len(args) >= 2:
        name = " ".join(args[1:]); data = coal.get(name)
        if not data: send(peer_id, "⚠ Нет коалиции."); return
        if key not in data.get("invites", []): send(peer_id, "⚠ Нет приглашения."); return
        data["invites"].remove(key); data.setdefault("members", []).append(key)
        c["coalition"] = name; save_cfg(cfg)
        send(peer_id, f"✅ Вступили в «{name}»!"); return
    if sub == "отклонить" and len(args) >= 2:
        name = " ".join(args[1:]); data = coal.get(name)
        if data and key in data.get("invites", []): data["invites"].remove(key)
        save_cfg(cfg); send(peer_id, f"❌ Отклонено."); return
    if sub == "покинуть":
        my_name = c.get("coalition")
        if not my_name: send(peer_id, "⚠ Не в коалиции."); return
        data = coal.get(my_name, {})
        if key in data.get("members", []): data["members"].remove(key)
        if data.get("leader") == key:
            if data.get("members"): data["leader"] = data["members"][0]
            else: del coal[my_name]
        c["coalition"] = None; save_cfg(cfg)
        send(peer_id, "👋 Покинули."); return
    if sub == "исключить" and len(args) >= 2:
        my_name = c.get("coalition")
        if not my_name: send(peer_id, "⚠ Не в коалиции."); return
        data = coal.get(my_name, {})
        if data.get("leader") != key: send(peer_id, "⛔ Только лидер."); return
        target = args[1].lower()
        if target in data.get("members", []):
            data["members"].remove(target)
            tc = get_country(target)
            if tc: tc["coalition"] = None
            save_cfg(cfg); send(peer_id, f"❌ {country_name(target)} исключён.")
        return
    if sub == "передать" and len(args) >= 2:
        my_name = c.get("coalition")
        if not my_name: send(peer_id, "⚠"); return
        data = coal.get(my_name, {})
        if data.get("leader") != key: send(peer_id, "⛔"); return
        target = args[1].lower()
        if target not in data.get("members", []): send(peer_id, "⚠"); return
        data["leader"] = target; save_cfg(cfg)
        send(peer_id, f"👑 Передано {country_name(target)}"); return
    if sub == "распустить":
        my_name = c.get("coalition")
        if not my_name: send(peer_id, "⚠"); return
        data = coal.get(my_name, {})
        if data.get("leader") != key: send(peer_id, "⛔"); return
        for m in data.get("members", []):
            mc = get_country(m)
            if mc: mc["coalition"] = None
        del coal[my_name]; save_cfg(cfg)
        send(peer_id, "💥 Распущена."); return
    name = " ".join(args)
    if name in coal: send(peer_id, "⚠ Существует."); return
    if c.get("coalition"): send(peer_id, "⚠ Уже в коалиции."); return
    coal[name] = {"leader": key, "members": [key], "invites": []}
    c["coalition"] = name; save_cfg(cfg)
    send(peer_id, f"🤝 «{name}» создана!")

def cmd_coal_help_money(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔"); return
    if len(args) < 2 or not args[1].isdigit(): send(peer_id, "⚠ /коалпомощь <страна> <сумма>"); return
    target = args[0].lower(); amount = int(args[1])
    tc = get_country(target)
    if not tc: send(peer_id, "⚠"); return
    if not c.get("coalition") or c.get("coalition") != tc.get("coalition"):
        send(peer_id, "⚠ Только союзникам."); return
    if c.get("treasury", 0) < amount: send(peer_id, "❌"); return
    c["treasury"] -= amount; tc["treasury"] = tc.get("treasury", 0) + amount
    save_cfg(cfg)
    send(peer_id, f"💵 Передано {fmt_num(amount)} → {country_name(target)}")
    broadcast_country(target, f"💵 Помощь от {country_name(key)}: +{fmt_num(amount)} 💵")

def cmd_mil_help(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔"); return
    if len(args) < 3 or not args[2].isdigit():
        send(peer_id, "⚠ /военпомощь <страна> <оружие> <кол>"); return
    target = args[0].lower(); weapon = args[1].lower(); cnt = int(args[2])
    if weapon not in WEAPONS: send(peer_id, f"⚠ Оружие: {', '.join(WEAPONS.keys())}"); return
    tc = get_country(target)
    if not tc: send(peer_id, "⚠"); return
    if c.get("coalition") != tc.get("coalition") or not c.get("coalition"):
        send(peer_id, "⚠ Только союзникам."); return
    if c.get("weapons", {}).get(weapon, 0) < cnt: send(peer_id, "❌"); return
    c["weapons"][weapon] -= cnt
    tc.setdefault("weapons", {})[weapon] = tc.get("weapons", {}).get(weapon, 0) + cnt
    save_cfg(cfg)
    send(peer_id, f"🚚 {cnt} {weapon} → {country_name(target)}")

def cmd_help_war(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔"); return
    if not args: send(peer_id, "⚠ /помочьвойна <страна>"); return
    ally = args[0].lower()
    if ally not in COUNTRIES: send(peer_id, "⚠"); return
    ally_c = get_country(ally)
    if not ally_c: send(peer_id, "⚠"); return
    if c.get("coalition") != ally_c.get("coalition") or not c.get("coalition"):
        send(peer_id, "⚠ Только союзникам."); return
    ally_wars = ally_c.get("wars", [])
    if not ally_wars: send(peer_id, "⚠ У союзника нет войн."); return
    enemy = ally_wars[0]
    cfg.setdefault("wars", []).append({"a": key, "b": enemy, "started_at": int(time.time()),
                                        "attacker": key, "defender": enemy, "helper": True})
    c.setdefault("wars", []).append(enemy)
    ec = get_country(enemy)
    if ec: ec.setdefault("wars", []).append(key)
    save_cfg(cfg)
    send(peer_id, f"⚔️ Война против {country_name(enemy)} за {country_name(ally)}")

# ================================================================
# АРМИЯ
# ================================================================
def cmd_mobilization(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and c.get("commander") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔"); return
    if c.get("mobilized"): send(peer_id, "⚠ Уже."); return
    bonus = int(c.get("army", BASE_ARMY) * 0.3)
    c["army"] = c.get("army", 0) + bonus
    c["mobilized"] = True
    c["mobilized_until"] = int(time.time()) + 12*3600
    save_cfg(cfg)
    broadcast_country(key, f"📣 МОБИЛИЗАЦИЯ! +{fmt_num(bonus)} войск на 12ч.")

def cmd_demobilization(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and c.get("commander") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔"); return
    if not c.get("mobilized"): send(peer_id, "⚠ Не мобилизованы."); return
    c["mobilized"] = False; c["mobilized_until"] = 0
    save_cfg(cfg)
    broadcast_country(key, "📣 Демобилизация завершена.")

def cmd_make_weapon(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and c.get("commander") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔"); return
    if len(args) < 2 or not args[1].isdigit():
        send(peer_id, "⚠ /сделать <оружие> <кол>\n" + ", ".join(WEAPONS.keys())); return
    weapon = args[0].lower(); cnt = int(args[1])
    if weapon not in WEAPONS: send(peer_id, "⚠"); return
    cost = WEAPONS[weapon]["cost"] * cnt
    if c.get("treasury", 0) < cost:
        send(peer_id, f"❌ Нужно {fmt_num(cost)} 💵"); return
    c["treasury"] -= cost
    c.setdefault("weapons", {})[weapon] = c.get("weapons", {}).get(weapon, 0) + cnt
    save_cfg(cfg)
    send(peer_id, f"🏭 {WEAPONS[weapon]['emoji']} {weapon.title()} ×{cnt}")

def cmd_install_pvo(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and c.get("commander") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔"); return
    if len(args) < 2 or not args[-1].isdigit():
        send(peer_id, "⚠ /установить пво <город> <кол>"); return
    cnt = int(args[-1]); city = " ".join(args[:-1]).title()
    city_match = next((x for x in CITIES if x.lower() == city.lower()), None)
    if not city_match: send(peer_id, "⚠ Город не найден."); return
    if CITIES.index(city_match) >= c.get("cities_unlocked", 3):
        send(peer_id, "⚠ Город не открыт."); return
    if c.get("weapons", {}).get("пво", 0) < cnt:
        send(peer_id, "❌ Мало ПВО (произведите /сделать пво)"); return
    c["weapons"]["пво"] -= cnt
    c["cities"][city_match]["pvo"] = c["cities"].get(city_match, {}).get("pvo", 0) + cnt
    save_cfg(cfg)
    send(peer_id, f"🚀 {cnt} ПВО в {city_match}")

def cmd_pvo_info(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    lines = [f"🚀 ПВО {country_name(key)}", ""]; total = 0
    for city, data in c.get("cities", {}).items():
        pvo = data.get("pvo", 0)
        if pvo: lines.append(f"• {city}: {pvo}"); total += pvo
    lines.append(f"\nСклад: {c.get('weapons', {}).get('пво', 0)}")
    lines.append(f"Всего: {total}, перехват: {min(90, total//10)}%")
    send(peer_id, "\n".join(lines))

def cmd_launch(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and c.get("commander") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔"); return
    if len(args) < 2: send(peer_id, "⚠ /запуск <оружие> <кол> [страна]"); return
    weapon = args[0].lower()
    if weapon not in ("ракета","бпла","ядерная"):
        send(peer_id, "⚠ Оружие: ракета / бпла / ядерная"); return
    if weapon == "ядерная":
        if len(args) < 3 or not args[1] or args[1].lower() != "ракета":
            if len(args) < 2: send(peer_id, "⚠ /запуск ядерная ракета <страна>"); return
        target = args[-1].lower()
        tc = get_country(target)
        if not tc: send(peer_id, "⚠"); return
        war = next((w for w in cfg.get("wars", []) if {w["a"], w["b"]} == {key, target}), None)
        if not war: send(peer_id, "❌ Только против активной войны."); return
        if c.get("nukes", 0) < 1:
            send(peer_id, "❌ Нет ядерных бомб. Произведите или попросите Global."); return
        c["nukes"] -= 1
        loss = int(tc.get("army", 0) * 0.5)
        tc["army"] = max(0, tc.get("army", 0) - loss)
        loot = int(tc.get("treasury", 0) * 0.4)
        tc["treasury"] -= loot; c["treasury"] = c.get("treasury", 0) + loot
        country_add_history(key, f"ядерный удар по {country_name(target)}")
        country_add_history(target, f"ядерный удар {country_name(key)}")
        save_cfg(cfg)
        broadcast_country(key, f"☢️ ЯДЕРНЫЙ УДАР по {country_name(target)}!")
        broadcast_country(target, f"☢️ ЯДЕРНЫЙ УДАР! Потери: {fmt_num(loss)}, {fmt_num(loot)} 💵")
        return
    if len(args) < 3 or not args[1].isdigit():
        send(peer_id, "⚠ /запуск <оружие> <кол> <страна>"); return
    cnt = int(args[1]); target = args[2].lower()
    tc = get_country(target)
    if not tc: send(peer_id, "⚠"); return
    war = next((w for w in cfg.get("wars", []) if {w["a"], w["b"]} == {key, target}), None)
    if not war: send(peer_id, "❌ Только против активной войны."); return
    if c.get("weapons", {}).get(weapon, 0) < cnt:
        send(peer_id, f"❌ Мало {weapon}."); return
    c["weapons"][weapon] -= cnt
    pvo_total = sum(d.get("pvo", 0) for d in tc.get("cities", {}).values())
    intercepted = min(pvo_total, cnt * 2)
    hits = max(0, cnt - intercepted)
    power = WEAPONS.get(weapon, {}).get("power", 100) * hits
    loss = int(tc.get("army", 0) * (power / 50000))
    loss = min(loss, int(tc.get("army", 0) * 0.3))
    tc["army"] = max(0, tc.get("army", 0) - loss)
    save_cfg(cfg)
    broadcast_country(key, f"🚀 {cnt} {weapon} по {country_name(target)}. Попаданий: {hits}, перехвачено: {intercepted}")
    broadcast_country(target, f"🚨 Атака! Перехвачено: {intercepted}, попаданий: {hits}, потери: {fmt_num(loss)}")

def cmd_tasks(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Только граждане."); return
    key = cit["country"]; c = get_country(key) or {}
    cd = c.get("mil_task_cooldown", {}).get(str(uid), 0)
    now = time.time()
    if now < cd:
        send(peer_id, f"⏳ Через {fmt_time(cd-now)}"); return
    send(peer_id,
         f"📋 <b>Военное задание</b>\n\n"
         f"Стоимость: {fmt_num(MIL_TASK_COST)} 💵\n"
         f"Награда: +{fmt_num(MIL_TASK_REWARD)} войск\n"
         f"Кулдаун: 1 час\n\n"
         f"/выполнитьзадание")

def cmd_do_task(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    cd = c.get("mil_task_cooldown", {}).get(str(uid), 0)
    now = time.time()
    if now < cd: send(peer_id, f"⏳ {fmt_time(cd-now)}"); return
    bal = get_balance(peer_id, uid)
    if bal < MIL_TASK_COST:
        send(peer_id, f"❌ Нужно {fmt_num(MIL_TASK_COST)} (у вас {fmt_num(bal)})"); return
    add_balance(peer_id, uid, -MIL_TASK_COST)
    c["army"] = c.get("army", 0) + MIL_TASK_REWARD
    c.setdefault("mil_task_cooldown", {})[str(uid)] = int(now + MIL_TASK_COOLDOWN)
    save_cfg(cfg)
    send(peer_id, f"✅ +{fmt_num(MIL_TASK_REWARD)} войск")
    broadcast_country(key, f"🎖️ {mention(uid)}: +{fmt_num(MIL_TASK_REWARD)} войск")

def cmd_upgrade_army(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and c.get("commander") != uid and uid != int(cfg["global_owner"]):
        send(peer_id, "⛔"); return
    lvl = c.get("army_level", 1)
    if lvl >= ARMY_LEVEL_MAX: send(peer_id, "⚠ Максимум."); return
    cost = 500000 * lvl
    if c.get("treasury", 0) < cost: send(peer_id, f"❌ Нужно {fmt_num(cost)}"); return
    c["treasury"] -= cost; c["army_level"] = lvl + 1
    save_cfg(cfg)
    broadcast_country(key, f"🎖️ Армия улучшена до уровня {lvl+1}!")

# ================================================================
# КОМПАНИЯ / BUILD
# ================================================================
def cmd_company(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    comp = c.get("companies", {}).get(str(uid))
    if not comp: send(peer_id, "📭 Нет компании.\n/регистрация ООО <название>"); return
    send(peer_id, f"🏢 {comp.get('name')}\n🌍 {country_name(key)}\n💰 Налог: {c.get('tax', 5)}%")

def cmd_register_company(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if args and args[0].lower() in ("ооо","ooo"): args = args[1:]
    if not args: send(peer_id, "⚠ /регистрация ООО <название>"); return
    cost = 100000; bal = get_balance(peer_id, uid)
    if bal < cost: send(peer_id, f"❌ Нужно {fmt_num(cost)}"); return
    add_balance(peer_id, uid, -cost)
    c.setdefault("companies", {})[str(uid)] = {"name": " ".join(args), "at": int(time.time())}
    save_cfg(cfg)
    send(peer_id, f"🏢 Компания зарегистрирована!")

def cmd_rename_company(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    comp = c.get("companies", {}).get(str(uid))
    if not comp: send(peer_id, "⚠ Нет компании."); return
    if not args: send(peer_id, "⚠ /переименоватьооо <название>"); return
    comp["name"] = " ".join(args); save_cfg(cfg)
    send(peer_id, f"✅ Переименовано в «{comp['name']}»")

def cmd_build_link(peer_id, uid, args):
    if not is_chat(peer_id): send(peer_id, "❌ Только в беседе."); return
    c = get_chat(peer_id)
    if uid != int(cfg["global_owner"]) and c.get("owner") != uid:
        send(peer_id, "⛔ Только владелец беседы или Global."); return
    if not args:
        cur = c.get("build_name")
        send(peer_id, f"🏗️ Текущая привязка: {cur or '—'}\n\n/build <название>"); return
    name = " ".join(args).strip()
    c["build_name"] = name
    builds = cfg.setdefault("builds", {})
    builds.setdefault(name, [])
    if peer_id not in builds[name]: builds[name].append(peer_id)
    save_cfg(cfg)
    send(peer_id, f"🏗️ Беседа привязана к «{name}»\nВсего в сетке: {len(builds[name])}")

def cmd_builds_list(peer_id, uid):
    if uid != int(cfg["global_owner"]):
        send(peer_id, "⛔ Только Global."); return
    builds = cfg.get("builds", {})
    if not builds: send(peer_id, "📭 Нет привязок."); return
    lines = ["🏗️ Сетки бесед:"]
    for name, peers in builds.items():
        lines.append(f"\n📦 «{name}» — {len(peers)}")
        for pid in peers[:5]: lines.append(f"  • {pid}")
        if len(peers) > 5: lines.append(f"  … и ещё {len(peers)-5}")
    send(peer_id, "\n".join(lines))

def cmd_set_president_global(peer_id, uid, args, reply_msg):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔ Global."); return
    if not args: send(peer_id, "⚠ /устпрезидент @user <страна>"); return
    target = extract_user(" ".join(args), reply_msg)
    if not target: send(peer_id, "⚠ @user"); return
    key = None
    for a in args:
        if a.lower() in COUNTRIES: key = a.lower(); break
    if not key: send(peer_id, "⚠ Страна не найдена."); return
    if not get_citizenship(target): set_citizenship(target, key)
    cfg["citizens"][str(target)]["rank"] = "президент"
    c = get_country(key)
    old = c.get("president")
    if old and get_citizenship(old): cfg["citizens"][str(old)]["rank"] = "гражданин"
    c["president"] = target
    country_add_history(key, f"{mention(target)} — президент")
    save_cfg(cfg)
    send(peer_id, f"👑 {mention(target, peer_id)} — президент {country_name(key)}!")
    broadcast_country(key, f"👑 Новый президент: {mention(target)}")

def cmd_set_citizenship_global(peer_id, uid, args, reply_msg):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔ Global."); return
    if not args: send(peer_id, "⚠ /устгражданство @user <страна>"); return
    target = extract_user(" ".join(args), reply_msg)
    if not target: send(peer_id, "⚠ @user"); return
    key = None
    for a in args:
        if a.lower() in COUNTRIES: key = a.lower(); break
    if not key: send(peer_id, "⚠ Страна не найдена."); return
    set_citizenship(target, key)
    send(peer_id, f"✅ {mention(target, peer_id)} — гражданин {country_name(key)}")
    send_dm(target, f"🌍 Гражданство {country_name(key)} выдано")

def cmd_gstaff(peer_id, uid):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔ Global."); return
    gs = cfg.get("global_staff", {})
    if not gs: send(peer_id, "📭 Нет глобальных ролей."); return
    prefetch_names([int(u) for u in gs.keys()])
    lines = ["🌐 <b>Глобальные роли:</b>", ""]
    for uid_str, rk in gs.items():
        role = find_role(rk, peer_id)
        rname = role["name"] if role else rk
        lines.append(f"• {mention(uid_str, peer_id)} — {rname}")
    send(peer_id, "\n".join(lines))

def cmd_grole(peer_id, uid, args, reply_msg, text):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔ Global."); return
    t = extract_user(text, reply_msg)
    if not t: send(peer_id, "⚠ /grole @user <роль>"); return
    role_args = [a for a in args if not re.match(r"\[id\d+\|", a) and not re.match(r"@id\d+", a)]
    ri = " ".join(role_args).strip()
    if not ri: send(peer_id, "⚠ /grole @user <роль>"); return
    rk = find_role_by_input(ri, peer_id)
    if not rk: send(peer_id, f"⚠ Роль «{ri}» не найдена."); return
    cfg.setdefault("global_staff", {})[str(t)] = rk; save_cfg(cfg)
    rname = cfg["roles"].get(rk, {}).get("name", rk)
    send(peer_id, f"🌐 {mention(t, peer_id)} — {rname} (глобально).")

def cmd_removerole(peer_id, uid, args, reply_msg, text):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔ Global."); return
    t = extract_user(text, reply_msg)
    if not t: send(peer_id, "⚠ /removerole @user"); return
    rem = cfg.get("global_staff", {}).pop(str(t), None); save_cfg(cfg)
    send(peer_id, "❌ Снято." if rem else "ℹ Нет роли.")

# ================================================================
# HELP
# ================================================================
def build_help():
    return f"""📋 Команды бота:

🎮 ЭКОНОМИКА /баланс /топ /приз /подписка /buybiz /mybiz /collect /донат

🎲 ИГРЫ /казино /дуэль /монетка /кубик /слоты /краш /дартс
/колесо /рулетка /блэкджек /мины /башня /кейс /гонка /рыбалка

🌍 ГОСУДАРСТВА
🏛 /госскоманды — ВСЕ команды стран
/страны /гражданство /паспорт /страна /граждане
/города /казна /правительство /должности /армия
/выборы /выдвинуться /голос
/компания /регистрация /переименоватьооо

⚔️ ВОЕННЫЕ
/войны /война /захват /контразащита /мир
/коалиции /коалиция /коалпомощь /военпомощь /помочьвойна
/мобилизация /демобилизация /сделать /пво /установить /запуск
/задание /выполнитьзадание
🚨 /сирена <город> /воздухтревога

🎟️ ПРОМОКОДЫ /promo /createpromo /promolist
🎭 ИВЕНТЫ /ивент /ивент мафия

🛡️ МОДЕРАЦИЯ /warn /unwarn /mute /unmute /nick /rnick
/kick /ban /unban /gban /ungban /clear /banlist
/tickets /adt

👑 ВЛАДЕЛЕЦ БЕСЕДЫ /setrole /removestaff /newrole /delrole
/setwarns /setmutetime /setlog /build

🌐 GLOBAL /объявление /createivent
/grole /removerole /gstaff /builds
/устгражданство /устпрезидент
💎 /выдать деньги|оружие|военных|вип|ядерка

💰 Баланс: {START_BALANCE} | 🎁 /приз до {fmt_num(PRIZE_MAX)}
⚔️ Война: {fmt_num(WAR_COST)} 💵 из казны
🎖️ Войск: {fmt_num(BASE_ARMY)} базово, пополнение через /задание
💵 Пополнить казну: /донат
⭐ Бот требует права администратора в беседе
"""

GOS_CMDS_TEXT = """🏛 <b>КОМАНДЫ СТРАНЫ</b> 🏛

━━━━━━━━━━━━━━━━━━━━━━
📖 <b>1/4 — Гражданство и информация</b>
━━━━━━━━━━━━━━━━━━━━━━
/страны — список государств
/гражданство [страна] — получить/сменить гражданство
/паспорт [пользователь] — паспорт
/страна — информация
/граждане — граждане страны
/города — 20 городов
/казна — казна + /казна история
/правительство /должности
/армия /армия выйти
/выборы /выдвинуться /голос
/компания /регистрация ООО /переименоватьооо
💵 /донат <сумма> — пополнить казну

━━━━━━━━━━━━━━━━━━━━━━
⚖️ <b>2/4 — Правительство и экономика</b>
━━━━━━━━━━━━━━━━━━━━━━
/налоги [1-20]
/назначить @user <должность>
/снятьминистра @user
/воинскоезвание @user [1-10]
/улучшитьстрану
/постройки <город>
/построить <объект> <город>
/госпроект <тип> <название>
/вооружение <сумма>

Служебные (Global):
/устгражданство @user <страна>
/устпрезидент @user <страна>

━━━━━━━━━━━━━━━━━━━━━━
⚔️ <b>3/4 — Армия и удары</b>
━━━━━━━━━━━━━━━━━━━━━━
/мобилизация /демобилизация
/сделать <оружие> <кол>
   {weapons}
/установить пво <город> <кол>
/пво
/запуск ракета <кол> <страна>
/запуск бпла <кол> <страна>
/запуск ядерная ракета <страна>
📋 /задание → /выполнитьзадание (+{task} войск)
🎖️ /upgrade_army
🚨 /сирена <город> /воздухтревога

━━━━━━━━━━━━━━━━━━━━━━
🤝 <b>4/4 — Коалиции и войны</b>
━━━━━━━━━━━━━━━━━━━━━━
/коалиции /коалиция /коалиция <название>
/коалиция пригласить|вступить|отклонить|покинуть
/коалиция исключить|передать|распустить
/коалпомощь <страна> <сумма>
/военпомощь <страна> <оружие> <кол>
/помочьвойна <страна>
/войны
/война <страна> — {war_cost} 💵
/захват <страна> — кампания 5 мин → уничтожение
/контразащита
/мир <страна> — 500к с обеих сторон

☠️ При уничтожении страна исчезает из списка,
   президент — 24ч в заложниках.
"""

def build_gos_cmds():
    return GOS_CMDS_TEXT.format(
        weapons=", ".join(WEAPONS.keys()),
        task=fmt_num(MIL_TASK_REWARD),
        war_cost=fmt_num(WAR_COST)
    )

# ================================================================
# ЗАПУСК
# ================================================================
if __name__ == "__main__":
    print(f"✅ VK Бот 9.0 запущен (PID={os.getpid()})")
    print(f"   Группа: {GROUP_ID}")
    print(f"   Война: {fmt_num(WAR_COST)}")
    print(f"   Армия базово: {fmt_num(BASE_ARMY)}")
    print("   Жду сообщений...\n")
    # ================================================================
# ИВЕНТЫ
# ================================================================
EVENTS_LIST = {
    "рулетка":"🎰 Рулетка","дуэль":"⚔️ Дуэль","лотерея":"🎟️ Лотерея",
    "хэллоуин":"🎃 Хэллоуин","новыйгод":"🎄 Новый год",
    "мафия":"🎭 Мафия","admin_abuse":"👑 Admin Abuse",
    "гонка":"🏎️ Гонка","золото":"💰 Золото","клад":"🗝 Клад",
    "блэкаут":"🌑 Блэкаут","феникс":"🔥 Феникс",
}
EVENT_TITLES = ["🏆 Победитель","⚔️ Воин","🎟️ Счастливчик","🎄 Снегурочка",
                "🌟 Звезда","👑 Король","🎩 Магистр","🍀 Удачливый",
                "🔥 Горячая штучка","🐉 Дракон","🦊 Хитрец","🌸 Красотка",
                "🏎️ Гонщик","🕵️ Детектив","🧙 Маг","🐺 Вожак"]

def get_chat_members(peer_id):
    try:
        return [m["member_id"] for m in api.messages.getConversationMembers(peer_id=peer_id)["items"]
                if m["member_id"] > 0 and m["member_id"] != BOT_ID]
    except Exception: return []

def _pick(peer_id):
    u = get_chat_members(peer_id); return random.choice(u) if u else None

def ev_roulette(peer_id):
    c = get_chat(peer_id); w = _pick(peer_id)
    if not w: send(peer_id, "❌ Нет участников."); return
    eff = random.choice(["title","mute","warn","money","nothing"])
    if eff == "title":
        t = random.choice(EVENT_TITLES); c["nicknames"][str(w)] = t; save_cfg(cfg)
        send(peer_id, f"🎰 {mention(w, peer_id)} → {t}")
    elif eff == "mute":
        c["muted"][str(w)] = {"until":time.time()+300,"last_dm":0}; save_cfg(cfg)
        send(peer_id, f"🎰 {mention(w, peer_id)} — 🔇 5 мин."); mute_notify_dm(w,5)
    elif eff == "warn":
        wr = c["warns"]; wr[str(w)] = wr.get(str(w),0)+1; save_cfg(cfg)
        send(peer_id, f"🎰 {mention(w, peer_id)} — ⚠️ ({wr[str(w)]}/{cfg['max_warns']}).")
    elif eff == "money":
        b = int(100 * full_vip_mult(peer_id, w)); add_balance(peer_id, w, b)
        send(peer_id, f"🎰 {mention(w, peer_id)} — 💰 +{fmt_num(b)}!")
    else: send(peer_id, f"🎰 {mention(w, peer_id)} — ничего 😅")

def ev_duel_ev(peer_id):
    c = get_chat(peer_id); users = get_chat_members(peer_id)
    if len(users) < 2: send(peer_id, "❌ ≥2."); return
    a, b = random.sample(users, 2); w = random.choice([a,b]); t = random.choice(EVENT_TITLES)
    c["nicknames"][str(w)] = t; save_cfg(cfg)
    send(peer_id, f"⚔️ {mention(a,peer_id)} vs {mention(b,peer_id)}\n🏆 {mention(w,peer_id)} → {t}")

def ev_lottery(peer_id):
    c = get_chat(peer_id); users = get_chat_members(peer_id)
    if len(users) < 3: send(peer_id, "❌ ≥3."); return
    lines = ["🎟️ Лотерея:"]
    for w in random.sample(users,3):
        t = random.choice(EVENT_TITLES); c["nicknames"][str(w)] = t
        lines.append(f"— {mention(w,peer_id)} → {t}")
    save_cfg(cfg); send(peer_id, "\n".join(lines))

def ev_halloween(peer_id):
    c = get_chat(peer_id); w = _pick(peer_id)
    if not w: send(peer_id, "❌"); return
    c["muted"][str(w)] = {"until":time.time()+300,"last_dm":0}; save_cfg(cfg)
    send(peer_id, f"🎃 {mention(w,peer_id)} → 🔇 5 мин."); mute_notify_dm(w,5)

def ev_newyear(peer_id):
    c = get_chat(peer_id); un = 0
    for k in list(c["muted"].keys()): del c["muted"][k]; un += 1
    w = _pick(peer_id)
    if w:
        c["nicknames"][str(w)] = "🎄 Снегурочка"; save_cfg(cfg)
        send(peer_id, f"🎄 Снято: {un}\n{mention(w,peer_id)} → 🎄")
    else: save_cfg(cfg); send(peer_id, f"🎄 Снято: {un}")

def ev_admin_abuse(peer_id):
    c = get_chat(peer_id); w = _pick(peer_id)
    if not w: send(peer_id, "❌"); return
    c["nicknames"][str(w)] = ADMIN_ABUSE_TITLE
    stats = c.setdefault("user_stats",{}); key = str(w)
    s = stats.get(key) or {"msg_count":0,"last_text":"","last_at":0}
    s["msg_count"] += ADMIN_ABUSE_MSGS; stats[key] = s; save_cfg(cfg)
    send(peer_id, f"👑 ADMIN ABUSE!\n{mention(w,peer_id)} → {ADMIN_ABUSE_TITLE}\n+{ADMIN_ABUSE_MSGS} сообщений!")

def ev_race(peer_id):
    c = get_chat(peer_id); w = _pick(peer_id)
    if not w: send(peer_id, "❌"); return
    c["nicknames"][str(w)] = "🏎️ Гонщик"; save_cfg(cfg)
    send(peer_id, f"🏎️ {mention(w,peer_id)} — Гонщик!")

def ev_gold(peer_id):
    w = _pick(peer_id)
    if not w: send(peer_id, "❌"); return
    b = int(500 * full_vip_mult(peer_id, w)); nb = add_balance(peer_id, w, b)
    send(peer_id, f"💰 {mention(w,peer_id)} — +{fmt_num(b)}!\nБаланс: {fmt_num(nb)}")

def ev_treasure(peer_id):
    w = _pick(peer_id)
    if not w: send(peer_id, "❌"); return
    b = int(200 * full_vip_mult(peer_id, w)); nb = add_balance(peer_id, w, b)
    send(peer_id, f"🗝 {mention(w,peer_id)} — +{fmt_num(b)}!\nБаланс: {fmt_num(nb)}")

def ev_blackout(peer_id):
    c = get_chat(peer_id); users = get_chat_members(peer_id)
    if not users: send(peer_id, "❌"); return
    until = time.time() + 120
    for u in users: c["muted"][str(u)] = {"until":until,"last_dm":0}
    save_cfg(cfg); send(peer_id, f"🌑 Блэкаут! {len(users)} в муте.")

def ev_phoenix(peer_id):
    c = get_chat(peer_id); un = 0
    for k in list(c["muted"].keys()): del c["muted"][k]; un += 1
    users = get_chat_members(peer_id)
    if users:
        winners = random.sample(users, min(3,len(users)))
        for w in winners: c["nicknames"][str(w)] = "🔥 Феникс"
        save_cfg(cfg)
        send(peer_id, f"🔥 Снято: {un}\nТитул: " + ", ".join(mention(w,peer_id) for w in winners))
    else: save_cfg(cfg); send(peer_id, f"🔥 Снято: {un}")

def ev_custom(peer_id, name):
    ev = cfg.get("custom_events", {}).get(name.lower())
    if not ev: return False
    send(peer_id, f"🎉 {ev['name']}\n🏆 {ev['reward']}\n📋 {ev['requirement']}")
    return True

EVENT_HANDLERS = {
    "рулетка":ev_roulette,"дуэль":ev_duel_ev,"лотерея":ev_lottery,
    "хэллоуин":ev_halloween,"новыйгод":ev_newyear,
    "admin_abuse":ev_admin_abuse,"гонка":ev_race,"золото":ev_gold,
    "клад":ev_treasure,"блэкаут":ev_blackout,"феникс":ev_phoenix,
}

def run_random_event(peer_id):
    ev = random.choice(list(EVENT_HANDLERS.keys()))
    send(peer_id, f"🎲 Выпал: {EVENTS_LIST[ev]}")
    try: EVENT_HANDLERS[ev](peer_id)
    except Exception as e: send(peer_id, f"❌ {e}")
    return ev

# ================================================================
# МАФИЯ
# ================================================================
MAFIA_MIN = 4
MAFIA_LOBBY = 60
MAFIA_DAY = 120
MAFIA_VOTE = 60
MAFIA_JOIN_WORDS = {"вступить","я","+","играю","в игре","мафия","го","за"}

R_MAFIA = "🔫 Мафия"
R_DON = "👑 Дон"
R_SHERIFF = "👮 Шериф"
R_DOCTOR = "💉 Доктор"
R_MANIAC = "🔪 Маньяк"
R_LOVER = "💋 Любовница"
R_JOURNALIST = "📰 Журналист"
R_LAWYER = "⚖️ Адвокат"
R_BEAUTY = "💃 Красотка"
R_BOMB = "💣 Бомба"
R_WEREWOLF = "🐺 Оборотень"
R_SLEEPWALKER = "🌙 Лунатик"
R_CIVILIAN = "👤 Мирный"
R_POLICE = "👮 Полицейский"

MAFIA_TEAM = {R_MAFIA, R_DON, R_LOVER, R_LAWYER}
CITY_TEAM = {R_SHERIFF, R_DOCTOR, R_JOURNALIST, R_BEAUTY, R_BOMB, R_WEREWOLF, R_SLEEPWALKER, R_CIVILIAN, R_POLICE}
NEUTRAL_TEAM = {R_MANIAC}

GAMES = {}; GAMES_LOCK = threading.Lock()

def _role_pool(n):
    if n == 4: pool = [R_MAFIA, R_POLICE, R_DOCTOR, R_CIVILIAN]
    elif n == 5: pool = [R_MAFIA, R_POLICE, R_DOCTOR, R_CIVILIAN, R_CIVILIAN]
    elif n == 6: pool = [R_MAFIA, R_DON, R_SHERIFF, R_DOCTOR, R_CIVILIAN, R_CIVILIAN]
    elif n == 7: pool = [R_MAFIA, R_DON, R_SHERIFF, R_DOCTOR, R_MANIAC, R_CIVILIAN, R_CIVILIAN]
    elif n == 8: pool = [R_MAFIA, R_DON, R_LOVER, R_SHERIFF, R_DOCTOR, R_MANIAC, R_CIVILIAN, R_CIVILIAN]
    elif n == 9: pool = [R_MAFIA, R_DON, R_LOVER, R_SHERIFF, R_DOCTOR, R_JOURNALIST, R_MANIAC, R_CIVILIAN, R_CIVILIAN]
    elif n == 10: pool = [R_MAFIA, R_DON, R_LOVER, R_LAWYER, R_SHERIFF, R_DOCTOR, R_JOURNALIST, R_MANIAC, R_CIVILIAN, R_CIVILIAN]
    elif n == 11: pool = [R_MAFIA, R_MAFIA, R_DON, R_LOVER, R_LAWYER, R_SHERIFF, R_DOCTOR, R_JOURNALIST, R_MANIAC, R_CIVILIAN, R_CIVILIAN]
    elif n == 12: pool = [R_MAFIA, R_MAFIA, R_DON, R_LOVER, R_LAWYER, R_SHERIFF, R_DOCTOR, R_JOURNALIST, R_BEAUTY, R_MANIAC, R_CIVILIAN, R_CIVILIAN]
    else:
        pool = [R_MAFIA, R_MAFIA, R_DON, R_LOVER, R_LAWYER, R_SHERIFF, R_DOCTOR, R_JOURNALIST, R_BEAUTY, R_BOMB, R_WEREWOLF, R_SLEEPWALKER, R_MANIAC, R_CIVILIAN, R_CIVILIAN, R_CIVILIAN]
        while len(pool) < n: pool.append(R_CIVILIAN)
    random.shuffle(pool); return pool[:n]

def mafia_start(peer_id, host_id):
    with GAMES_LOCK:
        if peer_id in GAMES: send(peer_id, "⚠️ Игра уже идёт."); return
        GAMES[peer_id] = {
            "phase":"lobby","lobby_players":[host_id],"players":{},"alive":set(),
            "host":host_id,"lobby_deadline":time.time()+MAFIA_LOBBY,
            "night_step_idx":0,"night_step":None,"night_actions":{},
            "day_deadline":0,"vote_deadline":0,"votes":{},"waiter_block":None,
            "round":0,"_alive_order":[],"lawyer_target":None,
        }
    send(peer_id, f"""🎭 <b>МАФИЯ</b> 🎭
Вступить: «вступить».
Мин: {MAFIA_MIN} | Сбор: {MAFIA_LOBBY}с

Игроки:
1. {get_vk_name(host_id)}""")

def mafia_join(peer_id, uid):
    g = GAMES.get(peer_id)
    if not g or g["phase"] != "lobby" or uid in g["lobby_players"]: return
    g["lobby_players"].append(uid)
    lines = [f"✅ {get_vk_name(uid)} ({len(g['lobby_players'])}):"]
    for i,u in enumerate(g["lobby_players"],1): lines.append(f"{i}. {get_vk_name(u)}")
    send(peer_id, "\n".join(lines))

def mafia_start_game(peer_id):
    g = GAMES.get(peer_id)
    if not g or g["phase"] != "lobby": return
    players = list(g["lobby_players"])
    if len(players) < MAFIA_MIN:
        send(peer_id, f"❌ Мало ({len(players)}/{MAFIA_MIN})"); GAMES.pop(peer_id,None); return
    pool = _role_pool(len(players)); roles = dict(zip(players, pool))
    g["players"] = roles; g["alive"] = set(players); g["round"] = 0; g["phase"] = "night"
    names = "\n".join(f"— {get_vk_name(u)}" for u in players)
    for uid, role in roles.items(): send_dm(uid, f"🎭 Роль: {role}\n\nИграют:\n{names}")
    send(peer_id, f"🎭 Игра началась! {len(players)} игроков.")
    mafia_start_night(peer_id)

def mafia_start_night(peer_id):
    g = GAMES.get(peer_id)
    if not g: return
    if not g["alive"]: GAMES.pop(peer_id,None); return
    g["phase"] = "night"; g["round"] += 1
    g["night_step_idx"] = 0; g["night_step"] = None; g["night_actions"] = {}
    g["waiter_block"] = None; g["votes"] = {}; g["lawyer_target"] = None
    send(peer_id, f"🌃 Раунд {g['round']}. Город засыпает...")
    mafia_next_step(peer_id)

NIGHT_ORDER = [
    ("mafia", {R_MAFIA, R_DON}), ("don", {R_DON}),
    ("sheriff", {R_SHERIFF, R_POLICE}), ("doctor", {R_DOCTOR}),
    ("lover", {R_LOVER}), ("journalist", {R_JOURNALIST}),
    ("lawyer", {R_LAWYER}), ("beauty", {R_BEAUTY}), ("maniac", {R_MANIAC}),
]

def _alive_list(g):
    alive = sorted(g["alive"]); g["_alive_order"] = alive
    return "\n".join(f"{i+1}. {get_vk_name(u)}" for i,u in enumerate(alive))

def mafia_next_step(peer_id):
    g = GAMES.get(peer_id)
    if not g or g["phase"] != "night": return
    roles_present = {g["players"][u] for u in g["alive"]}
    while g["night_step_idx"] < len(NIGHT_ORDER):
        step, roles = NIGHT_ORDER[g["night_step_idx"]]; g["night_step_idx"] += 1
        if roles_present & roles:
            g["night_step"] = step; mafia_announce(peer_id, step); return
    mafia_resolve(peer_id)

def mafia_announce(peer_id, step):
    g = GAMES.get(peer_id)
    if not g: return
    lst = _alive_list(g)
    actors = {
        "mafia":("🔫 Мафия...", (R_MAFIA, R_DON), "Кого убить"),
        "don":("👑 Дон...", (R_DON,), "Кого проверить (Шериф?)"),
        "sheriff":("👮 Шериф...", (R_SHERIFF, R_POLICE), "Кого проверить"),
        "doctor":("💉 Доктор...", (R_DOCTOR,), "Кого спасти"),
        "lover":("💋 Любовница...", (R_LOVER,), "Кого заблокировать"),
        "journalist":("📰 Журналист...", (R_JOURNALIST,), "Проверить 2 (2,5)"),
        "lawyer":("⚖️ Адвокат...", (R_LAWYER,), "Кого защитить"),
        "beauty":("💃 Красотка...", (R_BEAUTY,), "Кого забрать"),
        "maniac":("🔪 Маньяк...", (R_MANIAC,), "Кого убить"),
    }
    if step not in actors: return
    title, roles, action = actors[step]
    send(peer_id, title)
    for u,r in g["players"].items():
        if r in roles and u in g["alive"]:
            send_dm(u, f"{title}\n{action}:\n\n{lst}\n\nНомер.")

def mafia_parse_num(text, g, count=1):
    nums = re.findall(r"\d+", text)
    if not nums: return None
    order = g.get("_alive_order") or sorted(g["alive"])
    result = []
    for n in nums[:count]:
        i = int(n) - 1
        if 0 <= i < len(order): result.append(order[i])
    if count == 1: return result[0] if result else None
    return result if len(result) == count else None

def mafia_night_dm(uid, text, peer_id):
    g = GAMES.get(peer_id)
    if not g or g["phase"] != "night": return False
    step = g["night_step"]
    if not step: return False
    role = g["players"].get(uid)
    if uid not in g["alive"]: return False
    actors = {"mafia":(R_MAFIA,R_DON),"don":(R_DON,),"sheriff":(R_SHERIFF,R_POLICE),
              "doctor":(R_DOCTOR,),"lover":(R_LOVER,),"journalist":(R_JOURNALIST,),
              "lawyer":(R_LAWYER,),"beauty":(R_BEAUTY,),"maniac":(R_MANIAC,)}
    if role not in actors.get(step, ()): return False
    if step in g["night_actions"] and step != "mafia":
        send_dm(uid, "Уже."); return True
    if step == "journalist":
        pair = mafia_parse_num(text, g, 2)
        if not pair: send_dm(uid, "⚠️ Два номера: 2,5"); return True
        g["night_actions"][step] = pair
        a, b = pair
        same = (g["players"][a] in MAFIA_TEAM) == (g["players"][b] in MAFIA_TEAM)
        send_dm(uid, f"📰 {get_vk_name(a)} и {get_vk_name(b)} — " + ("ОДНА команда." if same else "РАЗНЫЕ."))
    else:
        t = mafia_parse_num(text, g, 1)
        if not t: send_dm(uid, "⚠️ Номер."); return True
        g["night_actions"][step] = t; send_dm(uid, f"✅ {get_vk_name(t)}")
        if step == "sheriff":
            if g["players"].get(t) in MAFIA_TEAM: send_dm(uid, f"✅ {get_vk_name(t)} — МАФИЯ!")
            else: send_dm(uid, f"❌ {get_vk_name(t)} — не мафия.")
        elif step == "don":
            if g["players"].get(t) in (R_SHERIFF, R_POLICE): send_dm(uid, f"👑 {get_vk_name(t)} — ШЕРИФ!")
            else: send_dm(uid, f"👑 {get_vk_name(t)} — не шериф.")
    ann = {"mafia":"🔫 Мафия сделала выбор.","don":"👑 Дон сделал выбор.",
           "sheriff":"👮 Шериф сделал выбор.","doctor":"💉 Доктор сделал выбор.",
           "lover":"💋 Любовница сделала выбор.","journalist":"📰 Журналист сделал выбор.",
           "lawyer":"⚖️ Адвокат сделал выбор.","beauty":"💃 Красотка сделала выбор.",
           "maniac":"🔪 Маньяк сделал выбор."}
    send(peer_id, ann.get(step, ""))
    g["night_step"] = None; mafia_next_step(peer_id); return True

def mafia_resolve(peer_id):
    g = GAMES.get(peer_id)
    if not g: return
    send(peer_id, "🌅 Город просыпается...")
    acts = g["night_actions"]
    mafia_t = acts.get("mafia"); maniac_t = acts.get("maniac")
    doc_t = acts.get("doctor"); beauty_t = acts.get("beauty")
    protected = set()
    if doc_t: protected.add(doc_t)
    if beauty_t: protected.add(beauty_t)
    victims = []
    if mafia_t and mafia_t not in protected: victims.append(mafia_t)
    if maniac_t and maniac_t not in protected and maniac_t not in victims: victims.append(maniac_t)
    if not victims: send(peer_id, "☀️ Никого не убили!")
    else:
        for v in victims:
            g["alive"].discard(v)
            send(peer_id, f"💀 Убит {get_vk_name(v)}. Роль: {g['players'][v]}")
    g["lawyer_target"] = acts.get("lawyer"); g["waiter_block"] = acts.get("lover")
    if mafia_check_win(peer_id): return
    g["phase"] = "day"; g["day_deadline"] = time.time() + MAFIA_DAY
    send(peer_id, f"🌞 День! {MAFIA_DAY}с на обсуждение.")

def mafia_check_win(peer_id):
    g = GAMES.get(peer_id)
    if not g: return True
    if not g["alive"]: mafia_end(peer_id, "🎭 Ничья."); return True
    am = sum(1 for u in g["alive"] if g["players"][u] in MAFIA_TEAM)
    ac = sum(1 for u in g["alive"] if g["players"][u] in CITY_TEAM)
    nm = sum(1 for u in g["alive"] if g["players"][u] in NEUTRAL_TEAM)
    if am == 0 and nm == 0: mafia_end(peer_id, "🎉 Город победил!"); return True
    if am >= ac + nm and am > 0: mafia_end(peer_id, "🔫 Мафия победила!"); return True
    if nm > 0 and len(g["alive"]) == 1: mafia_end(peer_id, "🔪 Маньяк победил!"); return True
    return False

def mafia_start_vote(peer_id):
    g = GAMES.get(peer_id)
    if not g or g["phase"] != "day": return
    g["phase"] = "voting"; g["votes"] = {}; g["vote_deadline"] = time.time() + MAFIA_VOTE
    send(peer_id, "🗳️ Голосование! Списки в ЛС.")
    alive = sorted(g["alive"]); g["_alive_order"] = alive
    names = "\n".join(f"{i+1}. {get_vk_name(u)}" for i,u in enumerate(alive))
    for u in alive:
        note = "\n⚠️ Голос отобран." if g.get("waiter_block")==u else ""
        send_dm(u, f"🗳️ Голосуйте:\n\n{names}\n\nНомер или 'пропуск'.{note}")

def mafia_vote_dm(uid, text, peer_id):
    g = GAMES.get(peer_id)
    if not g or g["phase"] != "voting" or uid not in g["alive"]: return False
    if uid in g["votes"]: send_dm(uid, "Уже."); return True
    t = text.strip().lower()
    if t in ("пропуск","skip","пас","0"):
        g["votes"][uid] = "skip"; send_dm(uid, "✅"); return True
    target = mafia_parse_num(text, g, 1)
    if not target: send_dm(uid, "⚠️ Номер."); return True
    if target == uid: send_dm(uid, "⚠️ Себя нельзя."); return True
    g["votes"][uid] = target; send_dm(uid, f"✅ {get_vk_name(target)}"); return True

def mafia_tally(peer_id):
    g = GAMES.get(peer_id)
    if not g: return
    g["phase"] = "ended"; counts = {}; skip = 0
    for voter, tgt in g["votes"].items():
        if voter == g.get("waiter_block"): continue
        if tgt == "skip": skip += 1
        else: counts[tgt] = counts.get(tgt,0) + 1
    if not counts: send(peer_id, "🗳️ Воздержались."); mafia_start_night(peer_id); return
    mx = max(counts.values()); top = [u for u,c in counts.items() if c == mx]
    if len(top) > 1: send(peer_id, "🗳️ Ничья."); mafia_start_night(peer_id); return
    victim = top[0]
    if g.get("lawyer_target") == victim:
        send(peer_id, f"⚖️ Адвокат спас {get_vk_name(victim)}!"); mafia_start_night(peer_id); return
    role = g["players"][victim]; g["alive"].discard(victim)
    if role in MAFIA_TEAM: send(peer_id, f"🎉 {get_vk_name(victim)} — мафия ({role}).")
    else: send(peer_id, f"❌ {get_vk_name(victim)} — {role}.")
    if mafia_check_win(peer_id): return
    mafia_start_night(peer_id)

def mafia_end(peer_id, msg):
    g = GAMES.pop(peer_id, None)
    if msg: send(peer_id, msg)
    if g:
        lines = ["🎭 Все роли:"]
        for u,r in g["players"].items():
            lines.append(f"— {get_vk_name(u)}: {r} ({'жив' if u in g['alive'] else 'мёртв'})")
        send(peer_id, "\n".join(lines))

def mafia_any_dm(uid, text):
    with GAMES_LOCK: games = list(GAMES.items())
    for peer_id, g in games:
        if uid not in g.get("players", {}): continue
        if g["phase"] == "night" and mafia_night_dm(uid, text, peer_id): return True
        if g["phase"] == "voting" and mafia_vote_dm(uid, text, peer_id): return True
    return False

def mafia_ticker():
    while True:
        time.sleep(1)
        try:
            now = time.time()
            for peer_id in list(GAMES.keys()):
                g = GAMES.get(peer_id)
                if not g: continue
                if g["phase"] == "lobby" and now >= g["lobby_deadline"]: mafia_start_game(peer_id)
                elif g["phase"] == "day" and now >= g["day_deadline"]: mafia_start_vote(peer_id)
                elif g["phase"] == "voting" and now >= g["vote_deadline"]: mafia_tally(peer_id)
        except Exception as e: print(f"[ticker] {e}")

threading.Thread(target=mafia_ticker, daemon=True).start()

def hostage_ticker():
    while True:
        time.sleep(60)
        try:
            now = time.time(); changed = False
            for c_key, country in cfg.get("countries", {}).items():
                if not country.get("destroyed"): continue
                new_hostages = []
                for h in country.get("hostages", []):
                    cit = get_citizenship(h)
                    if cit and cit.get("hostage_until", 0) > now:
                        new_hostages.append(h)
                    else:
                        if cit: cit["hostage_until"] = 0
                        send_dm(h, "🔓 Вас освободили! Вы больше не заложник.")
                        changed = True
                country["hostages"] = new_hostages
            if changed: save_cfg(cfg)
        except Exception as e: print(f"[hostage_ticker] {e}")

threading.Thread(target=hostage_ticker, daemon=True).start()

# ================================================================
# СТАТИСТИКА / ИНФО
# ================================================================
def user_stats_text(uid, peer_id):
    uid = int(uid); role = role_display(uid, peer_id)
    c = get_chat(peer_id) if is_chat(peer_id) else None
    bans_local = 0; bans_global = False
    for ch in cfg.get("chats", {}).values():
        i = ch.get("banned", {}).get(str(uid))
        if i:
            bans_local += 1
            if i.get("global"): bans_global = True
    warns = 0; mute = False; nick = None
    if c:
        warns = c.get("warns", {}).get(str(uid), 0)
        mu = get_mute_until(c.get("muted", {}).get(str(uid)))
        mute = bool(mu and mu > time.time())
        nick = c.get("nicknames", {}).get(str(uid))
    s = (c or {}).get("user_stats", {}).get(str(uid), {})
    bal = get_balance(peer_id, uid) if c else 0
    cit = get_citizenship(uid)
    cit_txt = "—"
    if cit:
        cn = country_name(cit["country"])
        rk = RANKS.get(cit["rank"], {}).get("name", cit["rank"])
        cit_txt = f"{cn} ({rk})"
    return "\n".join([
        "📊 Информация:",
        f"• {mention(uid, peer_id)}",
        f"• Роль в чате: {role}",
        f"• Гражданство: {cit_txt}",
        f"• VIP: {'✅' if is_vip(peer_id, uid) else 'Нет'}",
        f"• Баланс: {fmt_num(bal)} 💰",
        f"• Блокировок: {bans_local}",
        f"• Глоб блок: {'Да' if bans_global else 'Нет'}",
        f"• Предупреждения: {warns}/{cfg['max_warns']}",
        f"• Мут: {'Да' if mute else 'Нет'}",
        f"• Ник: {nick or 'Нет'}",
        f"• Сообщений: {s.get('msg_count', 0)}",
        f"• Последнее: {s.get('last_text') or '—'}",
        f"• Когда: {fmt_dt(s.get('last_at', 0))}",
        f"• Бизнесов: {len((c or {}).get('businesses', {}).get(str(uid), {}))}",
    ])

def user_info_text(uid, peer_id):
    role = role_display(uid, peer_id)
    lines = [f"ℹ️ {mention(uid, peer_id)}:", f"• Роль: {role}"]
    c = get_chat(peer_id) if is_chat(peer_id) else None
    if c:
        lines.append(f"• Ник: {c.get('nicknames',{}).get(str(uid), '—')}")
        mu = get_mute_until(c.get("muted", {}).get(str(uid)))
        lines.append(f"• 🔇 Мут: {fmt_time(mu-time.time())}" if mu and mu > time.time() else "• 🔇 Мут: нет")
        w = c.get("warns", {}).get(str(uid), 0)
        lines.append(f"• ⚠️ Предупреждения: {w}/{cfg['max_warns']}")
        b = c.get("banned", {}).get(str(uid))
        lines.append(f"• 🚫 Бан: {'🌐' if b and b.get('global') else '🏠' if b else 'нет'}")
        lines.append(f"• 💰 Баланс: {fmt_num(get_balance(peer_id, uid))}")
    return "\n".join(lines)

def build_staff_text(peer_id):
    c = get_chat(peer_id) if is_chat(peer_id) else None
    by_role = {}
    if c:
        for uid, rk in c.get("staff", {}).items(): by_role.setdefault(rk, []).append(uid)
    uids = [cfg["global_owner"]]
    if c:
        if c.get("owner"): uids.append(c["owner"])
        uids += [int(u) for u in c.get("staff", {}).keys()]
    prefetch_names(uids)
    lines = ["👮 Состав администрации (этот чат):", "",
             "🌐 Главный владелец:", f"— {mention(cfg['global_owner'], peer_id)}", "",
             "👑 Владелец беседы:"]
    lines.append(f"— {mention(c['owner'], peer_id)}" if c and c.get("owner") else "— (не назначен)")
    lines.append("")
    all_roles = dict(cfg["roles"])
    if c: all_roles.update(c.get("local_roles", {}))
    for key, role in sorted(all_roles.items(), key=lambda x: -x[1].get("priority",0)):
        lines.append(f"{role['name']}:")
        us = by_role.get(key, [])
        if us:
            for u in us: lines.append(f"— {mention(u, peer_id)}")
        else: lines.append("— ")
        lines.append("")
    return "\n".join(lines).rstrip()

# ================================================================
# ТИКЕТЫ
# ================================================================
def create_ticket(t, uid, peer_id, text):
    tid = cfg.get("next_ticket_id", 1)
    cfg["tickets"][str(tid)] = {"type":t,"from":uid,"peer_id":peer_id,"text":text,
        "status":"open","answer":"","answered_by":0,"answered_at":0,
        "created_at":int(time.time())}
    cfg["next_ticket_id"] = tid + 1; save_cfg(cfg); return tid

def tickets_text():
    t = cfg.get("tickets", {})
    if not t: return "📭 Тикетов нет."
    lines = ["🎫 Тикеты:", ""]; n = 0
    for tid, info in sorted(t.items(), key=lambda x: int(x[0])):
        if info.get("status") != "open": continue
        emoji = "💡" if info.get("type") == "offer" else "❓"
        lines.append(f"#{tid} {emoji} от {mention(info['from'])} — {fmt_dt(info.get('created_at',0))}\n   {info['text'][:120]}")
        n += 1
    return "\n".join(lines) if n else "📭 Открытых нет."

def answer_ticket(tid, admin_id, txt):
    info = cfg.get("tickets", {}).get(str(tid))
    if not info: return False, "Не найден."
    if info.get("status") == "answered": return False, "Уже отвечено."
    info["status"] = "answered"; info["answer"] = txt
    info["answered_by"] = admin_id; info["answered_at"] = int(time.time()); save_cfg(cfg)
    send_dm(info["from"], f"✅ Ответ #{tid}:\n\n❓ {info['text'][:200]}\n\n✅ {txt}")
    try: send(info["peer_id"], f"🎫 Ответ #{tid}:\n❓ {info['text'][:200]}\n✅ {txt}")
    except Exception: pass
    return True, "OK"

# ================================================================
# ПРИВЕТСТВИЕ
# ================================================================
def handle_welcome(peer_id, action):
    if not is_chat(peer_id): return
    invited = action.get("member_id")
    if not invited or invited <= 0: return
    c = get_chat(peer_id)
    if c.get("welcome") is False or invited == BOT_ID: return
    if str(invited) in c.get("banned", {}): return
    prefetch_names([invited])
    nick = c.get("nicknames", {}).get(str(invited))
    u = f"[id{invited}|{nick}]" if nick else f"[id{invited}|{get_vk_name(invited)}]"
    greeting = f"""╔══════════════════════╗
   👋 <b>ДОБРО ПОЖАЛОВАТЬ!</b>
╚══════════════════════╝

🌟 Рады видеть тебя, {u}!

📋 <b>Что тут есть:</b>
├ 🎮 /баланс — монеты
├ 🏦 /buybiz — бизнес
├ 🌍 /гражданство — стать гражданином
├ 🏛 /госскоманды — все команды стран
├ 🎲 /казино /дуэль — игры
├ 🎁 /приз — до 900 000 💰
├ 🎭 /ивент — ивенты
└ 📖 /help — все команды

💡 Подпишись на сообщество → VIP!
⚡ Приятной игры!"""
    send(peer_id, greeting)

# ================================================================
# ИГРЫ
# ================================================================
def _bet(args, bal):
    for i, a in enumerate(args):
        if a.isdigit() and int(a) > 0:
            b = int(a)
            if b > bal: return None, f"❌ Мало ({fmt_num(bal)})."
            return b, args[:i] + args[i+1:]
    return None, "⚠ Укажите ставку."

def game_coin(peer_id, uid, args):
    bal = get_balance(peer_id, uid); b, rest = _bet(args, bal)
    if b is None: send(peer_id, rest); return
    ch = (rest[0].lower() if rest else "")
    if ch not in ("орёл","орел","решка"): send(peer_id, "⚠ /монетка <ставка> <орёл|решка>"); return
    res = random.choice(["орёл","решка"])
    win = (res == ch) or (res == "орёл" and ch == "орел")
    if win:
        bonus = int(b * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, bonus)
        send(peer_id, f"🪙 {res}\n🎉 +{fmt_num(bonus)}\nБаланс: {fmt_num(nb)}")
    else:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"🪙 {res}\n💀 -{fmt_num(b)}\nБаланс: {fmt_num(nb)}")

def game_dice(peer_id, uid, args):
    bal = get_balance(peer_id, uid); b, rest = _bet(args, bal)
    if b is None: send(peer_id, rest); return
    if not rest or not rest[0].isdigit() or not 1 <= int(rest[0]) <= 6:
        send(peer_id, "⚠ /кубик <ставка> <1-6>"); return
    ch = int(rest[0]); res = random.randint(1,6)
    if res == ch:
        bonus = int(b * 5 * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, bonus)
        send(peer_id, f"🎲 {res}\n🎉 x5! +{fmt_num(bonus)}\nБаланс: {fmt_num(nb)}")
    else:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"🎲 {res}\n💀 -{fmt_num(b)}\nБаланс: {fmt_num(nb)}")

def game_slots(peer_id, uid, args):
    bal = get_balance(peer_id, uid); b, _ = _bet(args, bal)
    if b is None: send(peer_id, _); return
    icons = ["🍒","🍋","💎","7️⃣","⭐","🍀"]
    s = [random.choice(icons) for _ in range(3)]
    line = " | ".join(s)
    if s[0] == s[1] == s[2]:
        m = {"7️⃣":10,"💎":7,"⭐":5,"🍀":4}.get(s[0], 3)
        bonus = int(b * m * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, bonus)
        send(peer_id, f"🎰 {line}\n🎉 x{m}! +{fmt_num(bonus)}\nБаланс: {fmt_num(nb)}")
    elif s[0]==s[1] or s[1]==s[2] or s[0]==s[2]:
        bonus = int(b * 1.5 * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, bonus)
        send(peer_id, f"🎰 {line}\n✨ +{fmt_num(bonus)}\nБаланс: {fmt_num(nb)}")
    else:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"🎰 {line}\n💀 -{fmt_num(b)}\nБаланс: {fmt_num(nb)}")

def game_crash(peer_id, uid, args):
    bal = get_balance(peer_id, uid); b, rest = _bet(args, bal)
    if b is None: send(peer_id, rest); return
    if not rest: send(peer_id, "⚠ /краш <ставка> <1.1-10>"); return
    try: t = float(rest[0].replace(",", "."))
    except Exception: send(peer_id, "⚠ Числом."); return
    if not 1.1 <= t <= 10: send(peer_id, "⚠ 1.1-10"); return
    crash = round(random.uniform(1.0, 12.0), 2)
    if t <= crash:
        win = int(b * (t-1) * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, win)
        send(peer_id, f"🚀 {crash}x (цель {t}x)\n🎉 +{fmt_num(win)}\nБаланс: {fmt_num(nb)}")
    else:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"🚀 {crash}x (цель {t}x)\n💀 -{fmt_num(b)}")

def game_darts(peer_id, uid, args):
    bal = get_balance(peer_id, uid); b, _ = _bet(args, bal)
    if b is None: send(peer_id, _); return
    sc = random.randint(0,100)
    if sc >= 90: m = 5
    elif sc >= 70: m = 3
    elif sc >= 50: m = 2
    elif sc >= 30: m = 1
    else: m = 0
    if m:
        w = int(b * m * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, w)
        send(peer_id, f"🎯 {sc}/100\n💰 +{fmt_num(w)}\nБаланс: {fmt_num(nb)}")
    else:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"🎯 {sc}/100\n💀 -{fmt_num(b)}")

def game_wheel(peer_id, uid, args):
    bal = get_balance(peer_id, uid); b, rest = _bet(args, bal)
    if b is None: send(peer_id, rest); return
    if not rest: send(peer_id, "⚠ /колесо <ставка> <красное|чёрное|число>"); return
    ch = rest[0].lower(); num = random.randint(0,36)
    reds = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
    color = "зелёное" if num == 0 else ("красное" if num in reds else "чёрное")
    m = 0
    if ch in ("красное","красный","к") and color == "красное": m = 2
    elif ch in ("чёрное","черное","ч","черный","чёрный") and color == "чёрное": m = 2
    elif ch.isdigit() and int(ch) == num: m = 36
    if m:
        w = int(b * m * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, w)
        send(peer_id, f"🎡 {num} {color}\n🎉 x{m}! +{fmt_num(w)}")
    else:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"🎡 {num} {color}\n💀 -{fmt_num(b)}")

def game_roulette(peer_id, uid, args):
    bal = get_balance(peer_id, uid); b, rest = _bet(args, bal)
    if b is None: send(peer_id, rest); return
    if not rest or not rest[0].isdigit(): send(peer_id, "⚠ /рулетка <ставка> <0-36>"); return
    n = int(rest[0])
    if not 0 <= n <= 36: send(peer_id, "⚠ 0-36"); return
    res = random.randint(0,36)
    if res == n:
        w = int(b * 36 * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, w)
        send(peer_id, f"🎰 {res}\n🎉 x36! +{fmt_num(w)}")
    else:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"🎰 {res}\n💀 -{fmt_num(b)}")

def game_bj(peer_id, uid, args):
    bal = get_balance(peer_id, uid); b, _ = _bet(args, bal)
    if b is None: send(peer_id, _); return
    p = random.randint(15,21); d = random.randint(15,21)
    if p > d:
        w = int(b * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, w)
        send(peer_id, f"🃏 {p} vs {d}\n🎉 +{fmt_num(w)}")
    elif p == d: send(peer_id, f"🃏 {p} vs {d}\n🤝 Ничья")
    else:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"🃏 {p} vs {d}\n💀 -{fmt_num(b)}")

def game_mines(peer_id, uid, args):
    bal = get_balance(peer_id, uid); b, _ = _bet(args, bal)
    if b is None: send(peer_id, _); return
    if random.random() < 0.65:
        w = int(b * 1.7 * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, w)
        send(peer_id, f"💣 Чисто!\n🎉 +{fmt_num(w)}")
    else:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"💣 БАБАХ!\n💀 -{fmt_num(b)}")

def game_tower(peer_id, uid, args):
    bal = get_balance(peer_id, uid); b, rest = _bet(args, bal)
    if b is None: send(peer_id, rest); return
    floors = int(rest[0]) if rest and rest[0].isdigit() else 1
    if not 1 <= floors <= 5: floors = 1
    if random.random() < 0.6:
        w = int(b * (1 + floors*0.8) * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, w)
        send(peer_id, f"🗼 {floors} этаж(ей)\n🎉 +{fmt_num(w)}")
    else:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"🗼 Упали!\n💀 -{fmt_num(b)}")

def game_case(peer_id, uid, args):
    bal = get_balance(peer_id, uid); b, _ = _bet(args, bal)
    if b is None: send(peer_id, _); return
    mult = random.choice([0, 0, 0.5, 1, 1.5, 2, 3, 5, 10])
    if mult == 0:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"📦 Пусто\n💀 -{fmt_num(b)}")
    else:
        w = int(b * (mult-1) * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, w)
        send(peer_id, f"📦 x{mult}! +{fmt_num(w)}")

def game_race(peer_id, uid, args):
    bal = get_balance(peer_id, uid); b, _ = _bet(args, bal)
    if b is None: send(peer_id, _); return
    if random.random() < 0.4:
        w = int(b * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, w)
        send(peer_id, f"🏎️ Первое!\n🎉 +{fmt_num(w)}")
    else:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"🏎️ Проиграли\n💀 -{fmt_num(b)}")

def game_fish(peer_id, uid, args):
    bal = get_balance(peer_id, uid); b, _ = _bet(args, bal)
    if b is None: send(peer_id, _); return
    if random.random() < 0.55:
        w = int(b * 1.8 * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, w)
        send(peer_id, f"🎣 Поймали!\n🎉 +{fmt_num(w)}")
    else:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"🎣 Сорвалась!\n💀 -{fmt_num(b)}")

def cmd_casino(peer_id, uid, args):
    bal = get_balance(peer_id, uid); b, _ = _bet(args, bal)
    if b is None: send(peer_id, _); return
    if random.random() < 0.5:
        w = int(b * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, w)
        send(peer_id, f"🎰 🎉 +{fmt_num(w)}")
    else:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"🎰 💀 -{fmt_num(b)}")

def cmd_duel_game(peer_id, uid, args, reply_msg):
    t = extract_user(" ".join(args), reply_msg)
    if not t: send(peer_id, "⚠ /дуэль @user <ставка>"); return
    if t == uid: send(peer_id, "🤔 Себя нельзя."); return
    b = None
    for a in args:
        if a.isdigit() and int(a) > 0: b = int(a); break
    if not b: send(peer_id, "⚠ Ставка"); return
    if b > get_balance(peer_id, uid): send(peer_id, "❌ Мало."); return
    if b > get_balance(peer_id, t): send(peer_id, f"❌ У {mention(t,peer_id)} мало."); return
    win = random.choice([uid, t])
    add_balance(peer_id, uid, -b); add_balance(peer_id, t, -b)
    bonus = int(b * 2 * full_vip_mult(peer_id, win)); nb = add_balance(peer_id, win, bonus)
    send(peer_id, f"⚔️ {mention(uid,peer_id)} vs {mention(t,peer_id)}\n🏆 {mention(win,peer_id)} +{fmt_num(bonus)}")

# ================================================================
# БИЗНЕСЫ
# ================================================================
def cmd_buybiz(peer_id, uid, args):
    c = get_chat(peer_id)
    if not args:
        lines = ["💼 Бизнесы:"]
        for k, v in BUSINESSES.items():
            lines.append(f"{v['emoji']} {k} — {fmt_num(v['price'])} ({fmt_num(v['income'])}/час)")
        send(peer_id, "\n".join(lines)); return
    name = args[0].lower()
    if name not in BUSINESSES: send(peer_id, "⚠ Нет такого."); return
    biz = BUSINESSES[name]; bal = get_balance(peer_id, uid)
    if bal < biz["price"]: send(peer_id, f"❌ Нужно {fmt_num(biz['price'])}"); return
    my = c.setdefault("businesses", {}).setdefault(str(uid), {})
    if name in my: send(peer_id, f"⚠ Уже есть."); return
    my[name] = {"bought_at":int(time.time()),"last_collect":int(time.time())}
    add_balance(peer_id, uid, -biz["price"]); save_cfg(cfg)
    send(peer_id, f"✅ Куплен {biz['emoji']} {name}")

def cmd_mybiz(peer_id, uid):
    c = get_chat(peer_id); my = c.get("businesses", {}).get(str(uid), {})
    if not my: send(peer_id, "📭 Нет бизнесов."); return
    lines = ["💼 Бизнесы:"]; total = 0
    for n, info in my.items():
        b = BUSINESSES.get(n)
        if not b: continue
        h = min((time.time()-info["last_collect"])/3600, 24)
        inc = int(b["income"]*h*full_vip_mult(peer_id, uid))
        lines.append(f"{b['emoji']} {n} — {fmt_num(b['income'])}/час | {fmt_num(inc)}")
        total += inc
    lines.append(f"\n💰 /collect — {fmt_num(total)}")
    send(peer_id, "\n".join(lines))

def cmd_collect(peer_id, uid):
    c = get_chat(peer_id); my = c.get("businesses", {}).get(str(uid), {})
    if not my: send(peer_id, "❌ Нет бизнесов."); return
    now = int(time.time()); total = 0
    for n, info in my.items():
        b = BUSINESSES.get(n)
        if not b: continue
        h = min((now-info["last_collect"])/3600, 24)
        if h < 0.01: continue
        total += int(b["income"]*h*full_vip_mult(peer_id, uid))
        info["last_collect"] = now
    save_cfg(cfg)
    if total == 0: send(peer_id, "⏳ Мало времени."); return
    nb = add_balance(peer_id, uid, total); send(peer_id, f"💰 +{fmt_num(total)}")

def cmd_prize(peer_id, uid):
    c = get_chat(peer_id); last = c.get("last_prize", {}); now = int(time.time()); k = str(uid)
    el = now - last.get(k, 0)
    if el < PRIZE_COOLDOWN:
        w = PRIZE_COOLDOWN - el
        send(peer_id, f"⏳ Через {w//3600}ч {w%3600//60}м"); return
    amt = random.randint(PRIZE_MIN, PRIZE_MAX)
    amt = int(amt * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, amt)
    last[k] = now; c["last_prize"] = last; save_cfg(cfg)
    send(peer_id, f"🎁 +{fmt_num(amt)}!")

def cmd_sub(peer_id, uid):
    c = get_chat(peer_id)
    if is_vip(peer_id, uid):
        send(peer_id, f"👑 VIP активен"); return
    try:
        res = api.groups.isMember(group_id=GROUP_ID, user_id=uid)
        sub = (len(res)>0 and res[0].get("member")==1) if isinstance(res,list) else bool(res)
    except Exception: sub = False
    if not sub:
        send(peer_id, f"❌ Подпишитесь: {COMMUNITY_LINK}"); return
    if c.get("subs", {}).get(str(uid), 0) > 0: send(peer_id, "⚠ Уже получали."); return
    until = int(time.time()) + VIP_DURATION
    c.setdefault("subs", {})[str(uid)] = until
    nb = add_balance(peer_id, uid, VIP_PRICE); save_cfg(cfg)
    send(peer_id, f"👑 VIP +{fmt_num(VIP_PRICE)}")

def cmd_promo(peer_id, uid, args):
    if not args: send(peer_id, "⚠ /promo <код>"); return
    code = args[0].upper(); c = get_chat(peer_id)
    promo = c.get("promos", {}).get(code) or cfg.get("global_promos", {}).get(code)
    if not promo: send(peer_id, "❌ Не найден."); return
    used = c.setdefault("promos_used", {}).setdefault(str(uid), [])
    if code in used: send(peer_id, "⚠ Использован."); return
    if promo.get("uses_left",0) <= 0: send(peer_id, "⚠ Исчерпан."); return
    nb = add_balance(peer_id, uid, promo["reward"]); promo["uses_left"] -= 1
    used.append(code); save_cfg(cfg)
    send(peer_id, f"🎟️ +{fmt_num(promo['reward'])}")

def cmd_createpromo(peer_id, uid, args):
    c = get_chat(peer_id)
    if len(args) < 2 or not args[1].isdigit():
        send(peer_id, "⚠ /createpromo <код> <награда>"); return
    code = args[0].upper(); rw = int(args[1])
    if not 100 <= rw <= 1000000: send(peer_id, "⚠ 100-1 000 000"); return
    if code in c.get("promos", {}): send(peer_id, "⚠ Есть."); return
    c.setdefault("promos", {})[code] = {"reward":rw,"created_by":uid,
                                         "created_at":int(time.time()),"uses_left":100}
    save_cfg(cfg); send(peer_id, f"✅ {code}")

def cmd_promolist(peer_id, uid):
    c = get_chat(peer_id); promos = c.get("promos", {}); glob = cfg.get("global_promos", {})
    if not promos and not glob: send(peer_id, "📭 Нет."); return
    lines = ["🎟️ Промокоды:"]
    for code, p in promos.items(): lines.append(f"• {code} — {fmt_num(p['reward'])}")
    for code, p in glob.items(): lines.append(f"🌐 {code} — {fmt_num(p['reward'])}")
    send(peer_id, "\n".join(lines))

def cmd_top(peer_id, args):
    if not is_chat(peer_id): send(peer_id, "❌ Только в беседе."); return
    c = get_chat(peer_id); mode = args[0].lower() if args else "баланс"
    if mode in ("баланс","balance"):
        data = [(k,v) for k,v in c.get("balance",{}).items() if v>0]
        data.sort(key=lambda x:-x[1]); title = "💰 Топ балансов"
    elif mode in ("сообщения","msg"):
        data = [(k,v.get("msg_count",0)) for k,v in c.get("user_stats",{}).items()]
        data.sort(key=lambda x:-x[1]); title = "📝 Топ сообщений"
    elif mode in ("бизнес","biz"):
        data = [(k,len(v)) for k,v in c.get("businesses",{}).items()]
        data.sort(key=lambda x:-x[1]); title = "💼 Топ бизнесов"
    else: send(peer_id, "⚠ /топ [баланс|сообщения|бизнес]"); return
    if not data: send(peer_id, "📭 Нет."); return
    prefetch_names([int(k) for k,_ in data[:10]])
    lines = [title,""]; medals = ["🥇","🥈","🥉"]
    for i,(uid,v) in enumerate(data[:10]):
        m = medals[i] if i<3 else f"{i+1}."
        lines.append(f"{m} {mention(uid,peer_id)} — {fmt_num(v)}")
    send(peer_id, "\n".join(lines))

def cmd_wipe(peer_id, uid):
    if not is_chat(peer_id): send(peer_id, "❌ Только в беседе."); return
    c = get_chat(peer_id)
    if uid != int(cfg["global_owner"]) and c.get("owner") != uid: send(peer_id, "⛔"); return
    c["balance"] = {}; save_cfg(cfg); send(peer_id, "🧹 Вайп!")

def cmd_wipe_all(peer_id, uid):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔ Global."); return
    for ch in cfg.get("chats",{}).values(): ch["balance"] = {}
    save_cfg(cfg); send(peer_id, "🧹 ГЛОБАЛЬНЫЙ ВАЙП!")

def cmd_cmd(peer_id, uid, args):
    c = get_chat(peer_id)
    if len(args) < 2:
        a = c.get("custom_cmds", {})
        if not a: send(peer_id, "⚙️ /cmd <к> <имя>"); return
        send(peer_id, "\n".join([f"• /{k} → /{v}" for k,v in a.items()])); return
    if args[0].lower() == "reset":
        k = args[1].lower().lstrip("/"); rem = c.get("custom_cmds", {}).pop(k, None); save_cfg(cfg)
        send(peer_id, "✅" if rem else "⚠"); return
    orig = args[0].lower().lstrip("/"); alias = args[1].lower().lstrip("/")
    if orig not in ALL_COMMANDS: send(peer_id, f"⚠ /{orig} нет."); return
    if alias in ALL_COMMANDS: send(peer_id, f"⚠ /{alias} занято."); return
    c.setdefault("custom_cmds", {})[alias] = orig; save_cfg(cfg)
    send(peer_id, f"✅ /{alias} = /{orig}")

# ================================================================
# MAIN
# ================================================================
def main():
    for event in longpoll.listen():
        if event.type != VkBotEventType.MESSAGE_NEW: continue
        msg = event.object.message
        peer_id = msg["peer_id"]; from_id = msg["from_id"]
        text = (msg.get("text") or "").strip()
        real_id = msg.get("id") or 0
        cmid = msg.get("conversation_message_id") or 0
        reply_ref = real_id if real_id > 0 else None

        if peer_id == from_id:
            mafia_any_dm(from_id, text); continue

        preview = text[:60].replace("\n"," ")
        print(f"📨 peer={peer_id} from={from_id} id={real_id} cmid={cmid} text={preview!r}")
        if is_duplicate(peer_id, msg): continue

        action = msg.get("action")
        if action:
            atype = action.get("type")
            if atype == "chat_invite_user":
                inv = action.get("member_id")
                if inv and is_chat(peer_id):
                    if int(inv) == int(BOT_ID):
                        cache_invalidate_admin(peer_id)
                        def _check_later(pid):
                            time.sleep(2)
                            try:
                                if not is_bot_admin(pid, force=True):
                                    send(pid, WAIT_STAR_TEXT)
                                else:
                                    send(pid, "⭐ Спасибо за звёздочку!\n\n📋 /help\n🏛 /госскоманды")
                            except Exception as e: print(f"[bot_invite] {e}")
                        threading.Thread(target=_check_later, args=(peer_id,), daemon=True).start()
                        continue
                    c = get_chat(peer_id)
                    if str(inv) in c.get("banned", {}):
                        cid = chat_id_from_peer(peer_id)
                        if cid:
                            kick_user(cid, inv); send(peer_id, f"🚫 в бане.")
                    else: handle_welcome(peer_id, action)
                continue
            if atype == "chat_kick_user": continue
            if atype in ("chat_update", "chat_edit", "chat_title_update"):
                cache_invalidate_admin(peer_id)
                if is_bot_admin(peer_id, force=True):
                    send(peer_id, "⭐ Права получены! /help")
                continue

        track_peer(peer_id)
        if from_id > 0 and is_chat(peer_id): track_message(from_id, peer_id, text)

        g = GAMES.get(peer_id) if is_chat(peer_id) else None
        if g:
            if g["phase"] == "night" and from_id in g["players"] and from_id in g["alive"]:
                delete_msg(real_id, cmid, peer_id); continue
            if g["phase"] == "lobby" and text.lower().strip() in MAFIA_JOIN_WORDS:
                mafia_join(peer_id, from_id); continue

        if is_chat(peer_id):
            c = get_chat(peer_id)
            if str(from_id) in c.get("banned", {}):
                delete_msg(real_id, cmid, peer_id); kick_user(chat_id_from_peer(peer_id), from_id); continue
            muted = c.get("muted", {})
            if str(from_id) in muted:
                info = muted[str(from_id)]
                if isinstance(info, (int, float)): info = {"until":info,"last_dm":0}; muted[str(from_id)] = info
                now = time.time()
                if info["until"] > now:
                    delete_msg(real_id, cmid, peer_id)
                    if now - info.get("last_dm",0) > MUTE_DM_INTERVAL:
                        mute_warn_dm(from_id, info["until"]-now); info["last_dm"] = now; save_cfg(cfg)
                    continue
                else: mute_expired_dm(from_id); del muted[str(from_id)]; save_cfg(cfg)

        if not text.startswith("/"): continue
        if is_chat(peer_id) and not is_bot_admin(peer_id):
            if from_id != BOT_ID:
                send(peer_id, WAIT_STAR_TEXT, reply_to=reply_ref)
            continue

        parts = text.split(); cmd = parts[0][1:].lower(); args = parts[1:]
        reply_msg = msg.get("reply_message")

        if is_chat(peer_id):
            aliases = get_chat(peer_id).get("custom_cmds", {})
            if cmd in aliases: cmd = aliases[cmd]

        if cmd not in ALL_COMMANDS:
            send(peer_id,
                 f"❌ Команды «/{cmd}» не существует.\n\n"
                 f"📋 Все команды: /help\n"
                 f"🏛 Государственные: /госскоманды\n"
                 f"💡 Предложить свою: /offer <описание>",
                 reply_to=reply_ref)
            continue

        if cmd == "help": send(peer_id, build_help(), reply_to=reply_ref); continue
        if cmd == "госскоманды": send(peer_id, build_gos_cmds(), reply_to=reply_ref); continue

        # ГОСУДАРСТВО
        if cmd in ("страны","государства"): cmd_countries(peer_id, from_id); continue
        if cmd in ("гражданство","citizenship"): cmd_citizenship(peer_id, from_id, args); continue
        if cmd in ("паспорт","passport"): cmd_passport(peer_id, from_id, args, reply_msg); continue
        if cmd in ("страна","country"): cmd_country_info(peer_id, from_id, args); continue
        if cmd == "граждане": cmd_citizens(peer_id, from_id, args); continue
        if cmd == "города": cmd_cities(peer_id, from_id, args); continue
        if cmd == "казна": cmd_treasury(peer_id, from_id, args); continue
        if cmd == "правительство": cmd_government(peer_id, from_id, args); continue
        if cmd == "должности": cmd_positions(peer_id, from_id, args); continue
        if cmd == "армия": cmd_army(peer_id, from_id, args); continue
        if cmd == "выборы": cmd_elections(peer_id, from_id, args); continue
        if cmd == "выдвинуться": cmd_run_for_president(peer_id, from_id, args); continue
        if cmd == "голос": cmd_vote(peer_id, from_id, args); continue
        if cmd == "компания": cmd_company(peer_id, from_id, args); continue
        if cmd == "регистрация": cmd_register_company(peer_id, from_id, args); continue
        if cmd == "переименоватьооо": cmd_rename_company(peer_id, from_id, args); continue

        if cmd == "налоги": cmd_tax(peer_id, from_id, args); continue
        if cmd == "назначить": cmd_appoint(peer_id, from_id, args, reply_msg); continue
        if cmd == "снятьминистра": cmd_remove_minister(peer_id, from_id, args, reply_msg); continue
        if cmd == "воинскоезвание": cmd_military_rank(peer_id, from_id, args, reply_msg); continue
        if cmd == "улучшитьстрану": cmd_improve_country(peer_id, from_id, args); continue
        if cmd == "постройки": cmd_buildings(peer_id, from_id, args); continue
        if cmd == "построить": cmd_build_obj(peer_id, from_id, args); continue
        if cmd == "госпроект": cmd_state_project(peer_id, from_id, args); continue
        if cmd == "вооружение": cmd_armament(peer_id, from_id, args); continue

        if cmd == "мобилизация": cmd_mobilization(peer_id, from_id, args); continue
        if cmd == "демобилизация": cmd_demobilization(peer_id, from_id, args); continue
        if cmd == "сделать": cmd_make_weapon(peer_id, from_id, args); continue
        if cmd == "установить": cmd_install_pvo(peer_id, from_id, args); continue
        if cmd == "пво": cmd_pvo_info(peer_id, from_id, args); continue
        if cmd == "запуск": cmd_launch(peer_id, from_id, args); continue
        if cmd in ("задание","задания"): cmd_tasks(peer_id, from_id, args); continue
        if cmd == "выполнитьзадание": cmd_do_task(peer_id, from_id, args); continue
        if cmd == "upgrade_army": cmd_upgrade_army(peer_id, from_id, args); continue

        if cmd == "войны": cmd_wars(peer_id, from_id, args); continue
        if cmd == "война": cmd_declare_war(peer_id, from_id, args); continue
        if cmd == "захват": cmd_capture(peer_id, from_id, args); continue
        if cmd == "контразащита": cmd_counter_defense(peer_id, from_id, args); continue
        if cmd == "мир": cmd_peace(peer_id, from_id, args); continue

        if cmd == "коалиции": cmd_coalitions(peer_id, from_id, args); continue
        if cmd == "коалиция": cmd_coalition(peer_id, from_id, args, reply_msg); continue
        if cmd == "коалпомощь": cmd_coal_help_money(peer_id, from_id, args); continue
        if cmd == "военпомощь": cmd_mil_help(peer_id, from_id, args); continue
        if cmd == "помочьвойна": cmd_help_war(peer_id, from_id, args); continue

        if cmd == "устпрезидент": cmd_set_president_global(peer_id, from_id, args, reply_msg); continue
        if cmd == "устгражданство": cmd_set_citizenship_global(peer_id, from_id, args, reply_msg); continue
        if cmd == "gstaff": cmd_gstaff(peer_id, from_id); continue
        if cmd == "grole": cmd_grole(peer_id, from_id, args, reply_msg, text); continue
        if cmd == "removerole": cmd_removerole(peer_id, from_id, args, reply_msg, text); continue

        if cmd == "донат": cmd_donate(peer_id, from_id, args); continue
        if cmd == "сирена": cmd_siren(peer_id, from_id, args); continue
        if cmd in ("воздухтревога",): cmd_siren_all(peer_id, from_id, args); continue
        if cmd == "выдать": cmd_give(peer_id, from_id, args, reply_msg, text); continue

        if cmd == "build": cmd_build_link(peer_id, from_id, args); continue
        if cmd == "builds": cmd_builds_list(peer_id, from_id); continue

        if cmd == "staff":
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            send(peer_id, build_staff_text(peer_id), reply_to=reply_ref); continue
        if cmd == "info":
            t = extract_user(text, reply_msg)
            if not t: send(peer_id, "⚠ Укажи.", reply_to=reply_ref); continue
            send(peer_id, user_info_text(t, peer_id), reply_to=reply_ref); continue
        if cmd in ("стата","stat"):
            t = extract_user(text, reply_msg) or from_id; prefetch_names([t])
            send(peer_id, user_stats_text(t, peer_id), reply_to=reply_ref); continue
        if cmd in ("balance","баланс"):
            t = extract_user(text, reply_msg) or from_id; b = get_balance(peer_id, t)
            vip = " 👑VIP" if is_vip(peer_id, t) else ""
            send(peer_id, f"💰 {fmt_num(b)} монет{vip}", reply_to=reply_ref); continue
        if cmd in ("топ","top"): cmd_top(peer_id, args); continue
        if cmd in ("casino","казино"):
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            cmd_casino(peer_id, from_id, args); continue
        if cmd in ("дуэль","duel"):
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            cmd_duel_game(peer_id, from_id, args, reply_msg); continue
        if cmd in ("монетка","coin"): game_coin(peer_id, from_id, args); continue
        if cmd in ("кубик","dice"): game_dice(peer_id, from_id, args); continue
        if cmd in ("слоты","slots"): game_slots(peer_id, from_id, args); continue
        if cmd in ("краш","crash"): game_crash(peer_id, from_id, args); continue
        if cmd in ("дартс","darts"): game_darts(peer_id, from_id, args); continue
        if cmd in ("колесо","wheel"): game_wheel(peer_id, from_id, args); continue
        if cmd in ("рулетка","roulette"): game_roulette(peer_id, from_id, args); continue
        if cmd in ("блэкджек","bj"): game_bj(peer_id, from_id, args); continue
        if cmd in ("мины","mines"): game_mines(peer_id, from_id, args); continue
        if cmd in ("башня","tower"): game_tower(peer_id, from_id, args); continue
        if cmd in ("кейс","case"): game_case(peer_id, from_id, args); continue
        if cmd in ("гонка","race"): game_race(peer_id, from_id, args); continue
        if cmd in ("рыбалка","fish"): game_fish(peer_id, from_id, args); continue
        if cmd == "buybiz":
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            cmd_buybiz(peer_id, from_id, args); continue
        if cmd == "mybiz":
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            cmd_mybiz(peer_id, from_id); continue
        if cmd == "collect":
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            cmd_collect(peer_id, from_id); continue
        if cmd in ("приз","prize"):
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            cmd_prize(peer_id, from_id); continue
        if cmd in ("подписка","sub"):
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            cmd_sub(peer_id, from_id); continue
        if cmd in ("promo","промо"):
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            cmd_promo(peer_id, from_id, args); continue
        if cmd == "createpromo":
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            c = get_chat(peer_id)
            if from_id != int(cfg["global_owner"]) and c.get("owner") != from_id:
                send(peer_id, "⛔", reply_to=reply_ref); continue
            cmd_createpromo(peer_id, from_id, args); continue
        if cmd == "promolist":
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            c = get_chat(peer_id)
            if from_id != int(cfg["global_owner"]) and c.get("owner") != from_id and not can(from_id,"role",peer_id):
                send(peer_id, "⛔", reply_to=reply_ref); continue
            cmd_promolist(peer_id, from_id); continue
        if cmd == "вайп": cmd_wipe(peer_id, from_id); continue
        if cmd == "вайп_все": cmd_wipe_all(peer_id, from_id); continue
        if cmd == "cmd":
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            cmd_cmd(peer_id, from_id, args); continue
        if cmd == "offer":
            if not args: send(peer_id, "⚠ /offer <текст>", reply_to=reply_ref); continue
            tid = create_ticket("offer", from_id, peer_id, " ".join(args))
            send(peer_id, f"💡 Тикет #{tid}", reply_to=reply_ref); continue
        if cmd == "report":
            if not args: send(peer_id, "⚠ /report <текст>", reply_to=reply_ref); continue
            tid = create_ticket("report", from_id, peer_id, " ".join(args))
            send(peer_id, f"❓ Тикет #{tid}", reply_to=reply_ref); continue
        if cmd in ("ивент","event"):
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            if not args:
                lines = ["🎉 Ивенты:"]
                for k,v in EVENTS_LIST.items(): lines.append(f"• /ивент {k} — {v}")
                custom = cfg.get("custom_events", {})
                if custom:
                    lines.append("\n🎨 Кастомные:")
                    for k,v in custom.items(): lines.append(f"• /ивент {v['name']} — 🏆 {v['reward']}")
                lines.append("\n🎲 /ивент рандом")
                send(peer_id, "\n".join(lines), reply_to=reply_ref); continue
            ev = args[0].lower()
            if ev in ("рандом","random"): run_random_event(peer_id); continue
            if ev == "мафия": mafia_start(peer_id, from_id); continue
            if ev in EVENT_HANDLERS:
                send(peer_id, f"🎉 {EVENTS_LIST[ev]}")
                try: EVENT_HANDLERS[ev](peer_id)
                except Exception as e: send(peer_id, f"❌ {e}", reply_to=reply_ref)
                continue
            if ev_custom(peer_id, ev): continue
            send(peer_id, "⚠ Не найден.", reply_to=reply_ref); continue

        if not can(from_id, cmd, peer_id):
            send(peer_id, "⛔ Нет прав.", reply_to=reply_ref); continue

        if cmd == "role":
            if not is_chat(peer_id): send(peer_id, "❌", reply_to=reply_ref); continue
            c = get_chat(peer_id)
            lines = ["🎭 Роли:"]
            all_roles = dict(cfg["roles"]); all_roles.update(c.get("local_roles", {}))
            for k, r in sorted(all_roles.items(), key=lambda x: -x[1]["priority"]):
                lines.append(f"• {r['name']} ({r['priority']})")
            send(peer_id, "\n".join(lines), reply_to=reply_ref); continue

        if cmd in ("объявление","announce","рассылка"):
            if from_id != int(cfg["global_owner"]): send(peer_id, "⛔ Global.", reply_to=reply_ref); continue
            if not args: send(peer_id, "⚠ /объявление <текст>", reply_to=reply_ref); continue
            ann = " ".join(args); ok = 0
            for pid in cfg.get("known_peers", []):
                try: api.messages.send(peer_id=pid, message=f"📢 ОБЪЯВЛЕНИЕ\n\n{ann}",
                    random_id=int(time.time()*1000)+ok); ok += 1
                except Exception: pass
            send(peer_id, f"✅ {ok}", reply_to=reply_ref); continue

        if cmd == "newrole":
            if not is_chat(peer_id): send(peer_id, "❌", reply_to=reply_ref); continue
            if len(args) < 2 or not args[-1].isdigit():
                send(peer_id, "⚠ /newrole <название> <0-100>", reply_to=reply_ref); continue
            pr = int(args[-1])
            if not 0 <= pr <= 99: send(peer_id, "⚠ 0-99", reply_to=reply_ref); continue
            name = " ".join(args[:-1]).strip(); key = name.lower()
            c = get_chat(peer_id)
            if key in c.get("local_roles", {}) or key in cfg["roles"]:
                send(peer_id, "⚠ Есть.", reply_to=reply_ref); continue
            c.setdefault("local_roles", {})[key] = {"name":name,"priority":pr,
                                                     "commands":commands_for_priority(pr)}
            save_cfg(cfg); send(peer_id, f"✅ {name} ({pr})", reply_to=reply_ref); continue

        if cmd == "delrole":
            if not is_chat(peer_id): send(peer_id, "❌", reply_to=reply_ref); continue
            if not args: send(peer_id, "⚠ /delrole <название>", reply_to=reply_ref); continue
            name = " ".join(args); key = find_role_by_input(name, peer_id)
            if not key: send(peer_id, "⚠ Нет.", reply_to=reply_ref); continue
            c = get_chat(peer_id)
            if key in c.get("local_roles", {}):
                del c["local_roles"][key]
                for u in [x for x,r in c.get("staff",{}).items() if r==key]: del c["staff"][u]
                save_cfg(cfg); send(peer_id, "🗑", reply_to=reply_ref); continue
            if from_id != int(cfg["global_owner"]): send(peer_id, "⛔ Global.", reply_to=reply_ref); continue
            for ch in cfg.get("chats",{}).values():
                for u in [x for x,r in ch.get("staff",{}).items() if r==key]: del ch["staff"][u]
            del cfg["roles"][key]; save_cfg(cfg); send(peer_id, "🗑", reply_to=reply_ref); continue

        if cmd == "createivent":
            if from_id != int(cfg["global_owner"]): send(peer_id, "⛔ Global.", reply_to=reply_ref); continue
            if not args: send(peer_id, "⚠ /createivent <название> | <награда> | <требование>", reply_to=reply_ref); continue
            p = [x.strip() for x in " ".join(args).split("|")]
            if len(p) < 3: send(peer_id, "⚠ 3 части через |", reply_to=reply_ref); continue
            n, r, q = p[0], p[1], p[2]; k = n.lower()
            if k in cfg.get("custom_events", {}): send(peer_id, "⚠ Есть.", reply_to=reply_ref); continue
            cfg["custom_events"][k] = {"name":n,"reward":r,"requirement":q,
                                        "created_by":from_id,"created_at":int(time.time())}
            save_cfg(cfg); send(peer_id, f"✅ «{n}»", reply_to=reply_ref); continue

        if cmd == "tickets":
            if not is_chat(peer_id): send(peer_id, "❌", reply_to=reply_ref); continue
            send(peer_id, tickets_text(), reply_to=reply_ref); continue
        if cmd == "adt":
            if len(args) < 2 or not args[0].isdigit():
                send(peer_id, "⚠ /adt <№> <ответ>", reply_to=reply_ref); continue
            ok, e = answer_ticket(args[0], from_id, " ".join(args[1:]))
            send(peer_id, "✅" if ok else f"❌ {e}", reply_to=reply_ref); continue

        if cmd == "loginfo":
            send(peer_id, f"📝 {cfg.get('log_peer_id') or 'нет'}", reply_to=reply_ref); continue
        if cmd == "setlog":
            if from_id != int(cfg["global_owner"]) and not (is_chat(peer_id) and get_chat(peer_id).get("owner")==from_id):
                send(peer_id, "⛔", reply_to=reply_ref); continue
            if not is_chat(peer_id): send(peer_id, "❌", reply_to=reply_ref); continue
            cfg["log_peer_id"] = peer_id; save_cfg(cfg)
            send(peer_id, "✅", reply_to=reply_ref); continue
        if cmd == "unsetlog":
            if from_id != int(cfg["global_owner"]): send(peer_id, "⛔", reply_to=reply_ref); continue
            cfg["log_peer_id"] = 0; save_cfg(cfg); send(peer_id, "✅", reply_to=reply_ref); continue
        if cmd == "setwarns":
            if from_id != int(cfg["global_owner"]) and not (is_chat(peer_id) and get_chat(peer_id).get("owner")==from_id):
                send(peer_id, "⛔", reply_to=reply_ref); continue
            if not args or not args[0].isdigit(): send(peer_id, "⚠ /setwarns 3", reply_to=reply_ref); continue
            cfg["max_warns"] = int(args[0]); save_cfg(cfg)
            send(peer_id, f"✅ {cfg['max_warns']}", reply_to=reply_ref); continue
        if cmd == "setmutetime":
            if from_id != int(cfg["global_owner"]) and not (is_chat(peer_id) and get_chat(peer_id).get("owner")==from_id):
                send(peer_id, "⛔", reply_to=reply_ref); continue
            if not args or not args[0].isdigit(): send(peer_id, "⚠ /setmutetime 30", reply_to=reply_ref); continue
            cfg["default_mute_minutes"] = int(args[0]); save_cfg(cfg)
            send(peer_id, "✅", reply_to=reply_ref); continue
        if cmd == "banlist":
            if not is_chat(peer_id): send(peer_id, "❌", reply_to=reply_ref); continue
            b = get_chat(peer_id).get("banned", {})
            if not b: send(peer_id, "📭", reply_to=reply_ref); continue
            lines = ["🚫 Баны:"]
            for u, i in b.items(): lines.append(f"• {mention(u,peer_id)} — {i.get('reason','—')}")
            send(peer_id, "\n".join(lines), reply_to=reply_ref); continue
        if cmd == "clear":
            if not is_chat(peer_id): send(peer_id, "❌", reply_to=reply_ref); continue
            if not args or not args[0].isdigit(): send(peer_id, "⚠ /clear 10", reply_to=reply_ref); continue
            n = min(int(args[0]), 100)
            if n <= 0: send(peer_id, "⚠ N > 0", reply_to=reply_ref); continue
            try:
                hist = api.messages.getHistory(peer_id=peer_id, count=n, rev=1)["items"]
                ids = [str(m["id"]) for m in hist if m["from_id"] != BOT_ID and m.get("id")]
                if not ids: send(peer_id, "ℹ", reply_to=reply_ref); continue
                api.messages.delete(message_ids=",".join(ids), delete_for_all=1)
                send(peer_id, f"🧹 {len(ids)}", reply_to=reply_ref)
            except Exception as e: send(peer_id, f"❌ {e}", reply_to=reply_ref)
            continue

        if cmd == "nick":
            m = re.search(r"\[id(\d+)\|", text)
            tid = int(m.group(1)) if m else (reply_msg.get("from_id") if reply_msg else None)
            if tid is None: tid = from_id; nn = " ".join(args).strip()
            else:
                pn = [a for a in args if not re.match(r"\[id\d+\|",a) and not re.match(r"@id\d+",a)]
                nn = " ".join(pn).strip()
            if not nn: send(peer_id, "⚠ /nick <ник>", reply_to=reply_ref); continue
            if len(nn) > 32: send(peer_id, "⚠ ≤32", reply_to=reply_ref); continue
            get_chat(peer_id)["nicknames"][str(tid)] = nn; save_cfg(cfg)
            send(peer_id, f"✅ {nn}", reply_to=reply_ref); continue
        if cmd == "rnick":
            m = re.search(r"\[id(\d+)\|", text)
            tid = int(m.group(1)) if m else (reply_msg.get("from_id") if reply_msg else None)
            if tid is None: tid = from_id
            c = get_chat(peer_id); rem = c["nicknames"].pop(str(tid), None); save_cfg(cfg)
            send(peer_id, "✅" if rem else "ℹ", reply_to=reply_ref); continue

        target = extract_user(text, reply_msg)
        if not target: send(peer_id, "⚠ Укажи.", reply_to=reply_ref); continue
        if target == from_id: send(peer_id, "🤔 Себя нельзя.", reply_to=reply_ref); continue
        if int(target) == int(cfg["global_owner"]) and from_id != int(cfg["global_owner"]):
            send(peer_id, "🌐 Нельзя.", reply_to=reply_ref); continue
        if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue

        c = get_chat(peer_id); cid = chat_id_from_peer(peer_id)

        if cmd == "setowner":
            if from_id != int(cfg["global_owner"]): send(peer_id, "⛔", reply_to=reply_ref); continue
            c["owner"] = target; save_cfg(cfg)
            send(peer_id, f"👑 {mention(target,peer_id)} — владелец.", reply_to=reply_ref); continue
        if cmd == "ban":
            reason = " ".join(args) if args else "—"
            ok, err = kick_user(cid, target)
            if not ok: send(peer_id, f"❌ {err}", reply_to=reply_ref); continue
            c["banned"][str(target)] = {"reason":reason,"by":from_id,"at":int(time.time()),"global":False}
            save_cfg(cfg); send(peer_id, f"🔨 Забанен.", reply_to=reply_ref)
        elif cmd == "unban":
            rem = c["banned"].pop(str(target), None); save_cfg(cfg)
            send(peer_id, "✅" if rem else "ℹ", reply_to=reply_ref)
        elif cmd == "gban":
            reason = " ".join(args) if args else "—"; k = 0
            for pid in cfg.get("known_peers", []):
                c2 = chat_id_from_peer(pid)
                if not c2: continue
                ok, _ = kick_user(c2, target)
                if ok: k += 1
            for ch in cfg.get("chats",{}).values():
                ch["banned"][str(target)] = {"reason":reason,"by":from_id,"at":int(time.time()),"global":True}
            save_cfg(cfg); send(peer_id, f"🌐 ({k})", reply_to=reply_ref)
        elif cmd == "ungban":
            rem = 0
            for ch in cfg.get("chats",{}).values():
                i = ch["banned"].get(str(target))
                if i and i.get("global"): del ch["banned"][str(target)]; rem += 1
            save_cfg(cfg); send(peer_id, "✅" if rem else "ℹ", reply_to=reply_ref)
        elif cmd == "kick":
            ok, err = kick_user(cid, target)
            send(peer_id, "👢" if ok else f"❌ {err}", reply_to=reply_ref)
        elif cmd == "mute":
            m = cfg["default_mute_minutes"]
            if args and args[0].isdigit():
                m = int(args[0])
                if m <= 0: m = cfg["default_mute_minutes"]
            c["muted"][str(target)] = {"until":time.time()+m*60,"last_dm":time.time()}
            save_cfg(cfg); send(peer_id, f"🔇 {m} мин.", reply_to=reply_ref)
            mute_notify_dm(target, m)
        elif cmd == "unmute":
            rem = c["muted"].pop(str(target), None); save_cfg(cfg)
            if rem:
                send(peer_id, "🔊", reply_to=reply_ref); send_dm(target, "🔊 Мут снят.")
            else: send(peer_id, "ℹ", reply_to=reply_ref)
        elif cmd == "warn":
            reason = " ".join(args) if args else "—"
            wr = c["warns"]; wr[str(target)] = wr.get(str(target),0)+1; cnt = wr[str(target)]
            save_cfg(cfg)
            send(peer_id, f"⚠ ({cnt}/{cfg['max_warns']}) {reason}", reply_to=reply_ref)
            if cnt >= cfg["max_warns"]:
                c["muted"][str(target)] = {"until":time.time()+3600,"last_dm":time.time()}
                save_cfg(cfg); send(peer_id, "🔇 60 мин.", reply_to=reply_ref); mute_notify_dm(target, 60)
        elif cmd == "unwarn":
            c["warns"].pop(str(target), None); save_cfg(cfg)
            send(peer_id, "✅", reply_to=reply_ref)
        elif cmd == "setrole":
            if from_id != int(cfg["global_owner"]) and c.get("owner") != from_id:
                send(peer_id, "⛔", reply_to=reply_ref); continue
            ri = " ".join(args).strip(); rk = find_role_by_input(ri, peer_id)
            if not rk:
                all_roles = dict(cfg["roles"]); all_roles.update(c.get("local_roles", {}))
                send(peer_id, f"⚠ Не найдена. Есть: {', '.join(v['name'] for v in all_roles.values())}",
                     reply_to=reply_ref); continue
            c["staff"][str(target)] = rk; save_cfg(cfg)
            rname = (c.get("local_roles",{}).get(rk) or cfg["roles"].get(rk,{})).get("name", rk)
            send(peer_id, f"✅ {mention(target,peer_id)} — {rname}", reply_to=reply_ref)
        elif cmd == "removestaff":
            if from_id != int(cfg["global_owner"]) and c.get("owner") != from_id:
                send(peer_id, "⛔", reply_to=reply_ref); continue
            if str(target) == str(cfg["global_owner"]): send(peer_id, "🌐", reply_to=reply_ref); continue
            rem = c["staff"].pop(str(target), None); save_cfg(cfg)
            if rem:
                rname = (c.get("local_roles",{}).get(rem) or cfg["roles"].get(rem,{})).get("name", rem)
                send(peer_id, f"❌ {rname}", reply_to=reply_ref)
            else: send(peer_id, "ℹ", reply_to=reply_ref)

# ================================================================
if __name__ == "__main__":
    print(f"✅ VK Бот 9.0 запущен (PID={os.getpid()})")
    print(f"   Группа: {GROUP_ID}")
    print(f"   Война: {fmt_num(WAR_COST)}")
    print(f"   Армия базово: {fmt_num(BASE_ARMY)}")
    print("   Жду сообщений...\n")
    try:
        while True:
            try: main()
            except KeyboardInterrupt: print("\n⏹"); break
            except Exception as e:
                print(f"⚠ {e}. Рестарт 5с..."); time.sleep(5)
    finally:
        try: os.remove(PID_FILE)
        except Exception: pass
