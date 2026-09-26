# -*- coding: utf-8 -*-
"""
VK-бот 7.0 — страны + экономика + новые игры + Мафия с 18 ролями
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
CFG_VERSION = 7
MUTE_DM_INTERVAL = 300
START_BALANCE = 100
PRIZE_MIN, PRIZE_MAX, PRIZE_COOLDOWN = 1000, 900000, 86400
VIP_PRICE, VIP_DURATION, VIP_BONUS = 1000000, 30*86400, 0.10
ADMIN_ABUSE_TITLE, ADMIN_ABUSE_MSGS = "👑 Admin Abuser", 50

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

RANKS = {  # доступные должности в стране
    "гражданин":      {"name":"👤 Гражданин",       "cost": 0,       "bonus_mult": 1.0},
    "политик":        {"name":"🏛️ Политик",         "cost": 50000,   "bonus_mult": 1.2},
    "сенатор":        {"name":"⚖️ Сенатор",         "cost": 200000,  "bonus_mult": 1.5},
    "министр":        {"name":"💼 Министр",         "cost": 500000,  "bonus_mult": 2.0},
    "главком":        {"name":"🎖️ Главнокомандующий","cost": 1000000, "bonus_mult": 3.0},
    "президент":      {"name":"👑 Президент",       "cost": 0,       "bonus_mult": 5.0},
}

# ================================================================
# БИЗНЕСЫ
# ================================================================
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
    "promo","промо","гражданство","citizenship","паспорт","passport",
    "страна","country","страны","государства",
    "cmd","offer","report","ивент","event","role","build",
]
HELPER_CMDS = PUBLIC_CMDS + ["warn","promolist","createpromo","вайп"]
MODERATOR_CMDS = HELPER_CMDS + ["nick","rnick","unwarn","mute","unmute",
                                 "clear","banlist","tickets","adt"]
ADMIN_CMDS = MODERATOR_CMDS + ["kick","ban","unban","gban","ungban"]
STAFF_CMDS = ADMIN_CMDS + ["loginfo","builds"]
OWNER_CMDS = STAFF_CMDS + ["addstaff","removestaff","setrole","setowner",
                            "setlog","unsetlog","setwarns","setmutetime",
                            "newrole","delrole","createivent","вайп_все"]
GLOBAL_ONLY = ["объявление","announce","рассылка","setpresident","setcommander"]

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
ALL_COMMANDS.update(GLOBAL_ONLY + ["newrole","delrole","createivent","setowner",
                                    "setpresident","setcommander","builds",
                                    "promolist","createpromo","вайп","вайп_все",
                                    "паспорт","passport","гражданство","citizenship",
                                    "страна","country","блэкджек","bj","мины","mines",
                                    "башня","tower","кейс","case","гонка","race",
                                    "рыбалка","fish"])

def suggest_command(cmd):
    m = difflib.get_close_matches(cmd, list(ALL_COMMANDS), n=1, cutoff=0.55)
    return m[0] if m else None

# ================================================================
# КОНФИГ
# ================================================================
DEFAULT_CHAT = {
    "owner":None,"staff":{},"banned":{},"muted":{},"warns":{},
    "nicknames":{},"welcome":True,"user_stats":{},"balance":{},
    "businesses":{},"subs":{},"last_prize":{},"promos_used":{},
    "promos":{},"local_roles":{},"custom_cmds":{},"build_name":None,
}
DEFAULT_CFG = {
    "version":CFG_VERSION,"global_owner":GLOBAL_OWNER_ID,
    "default_mute_minutes":30,"max_warns":3,"log_peer_id":0,
    "roles":DEFAULT_ROLES,"chats":{},"known_peers":[],
    "tickets":{},"next_ticket_id":1,"custom_events":{},
    "countries":{k:{"treasury":0,"president":None,"commander":None,"citizens":[],
                     "army":0} for k in COUNTRIES},
    "citizens":{},  # {uid: {"country":key,"rank":"гражданин","joined_at":ts,"donated":0}}
    "builds":{},"global_promos":{},
}
_cfg_lock = threading.Lock()

def migrate(d):
    d.setdefault("version",1)
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
    # страны
    d.setdefault("countries", {})
    for k in COUNTRIES:
        d["countries"].setdefault(k, {"treasury":0,"president":None,"commander":None,
                                       "citizens":[],"army":0})
    d.setdefault("citizens", {})
    d.setdefault("builds", {}); d.setdefault("global_promos", {})
    for ch in d.get("chats", {}).values():
        for k, v in DEFAULT_CHAT.items():
            ch.setdefault(k, json.loads(json.dumps(v)))
        muted = ch.get("muted", {})
        for uid, val in list(muted.items()):
            if isinstance(val, (int, float)): muted[uid] = {"until":val,"last_dm":0}
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
# БАЗОВЫЕ ХЕЛПЕРЫ
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
    if not is_chat(peer_id): return None
    c = get_chat(peer_id)
    if c.get("owner") == uid: return "owner"
    return c.get("staff", {}).get(str(uid))

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
        return cmd not in ("newrole","delrole","createivent") and cmd not in GLOBAL_ONLY
    rk = c.get("staff", {}).get(str(uid))
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
# СТРАНЫ — ЛОГИКА
# ================================================================
def get_citizenship(uid):
    """Возвращает dict или None."""
    return cfg.get("citizens", {}).get(str(uid))

def set_citizenship(uid, country_key, rank="гражданин"):
    c = cfg.setdefault("citizens", {})
    c[str(uid)] = {"country": country_key, "rank": rank,
                    "joined_at": int(time.time()), "donated": 0}
    country = cfg.setdefault("countries", {}).setdefault(country_key, 
        {"treasury":0,"president":None,"commander":None,"citizens":[],"army":0})
    if uid not in country["citizens"]:
        country["citizens"].append(uid)
    save_cfg(cfg)

def country_income_mult(uid):
    """Множитель дохода от должности."""
    cit = get_citizenship(uid)
    if not cit: return 1.0
    rank = cit.get("rank", "гражданин")
    return RANKS.get(rank, {}).get("bonus_mult", 1.0)

def full_vip_mult(peer_id, uid):
    """Множитель = VIP × должность."""
    return vip_multiplier(peer_id, uid) * country_income_mult(uid)

def cmd_citizenship(peer_id, uid, args):
    if not args:
        cit = get_citizenship(uid)
        if cit:
            cn = COUNTRIES.get(cit["country"], {}).get("name", cit["country"])
            send(peer_id, f"🌍 Вы гражданин {cn}\nДолжность: {RANKS[cit['rank']]['name']}\n\nСменить: /гражданство <страна>")
        else:
            lines = ["🌍 Доступные страны:"]
            for k, c in COUNTRIES.items(): lines.append(f"• {k} — {c['name']}")
            lines.append("\nВступить: /гражданство <название>")
            send(peer_id, "\n".join(lines))
        return
    country_key = args[0].lower()
    if country_key not in COUNTRIES: send(peer_id, "❌ Страна не найдена. Список: /страны"); return
    cit = get_citizenship(uid)
    if cit:
        if cit["country"] == country_key: send(peer_id, "ℹ Вы уже гражданин."); return
        # выйти из старой
        old = cfg["countries"].get(cit["country"], {})
        if uid in old.get("citizens", []): old["citizens"].remove(uid)
        if old.get("president") == uid: old["president"] = None
        if old.get("commander") == uid: old["commander"] = None
    set_citizenship(uid, country_key)
    cn = COUNTRIES[country_key]["name"]
    send(peer_id, f"🎉 Поздравляем! Вы стали гражданином {cn}!\n\n"
                  f"📔 /паспорт — ваш паспорт\n"
                  f"🏛️ /страна {country_key} — статистика страны\n"
                  f"💼 Доступные должности: /гражданство")

def cmd_passport(peer_id, uid, args, reply_msg):
    target = extract_user(" ".join(args), reply_msg) or uid
    cit = get_citizenship(target)
    if not cit:
        if target == uid: send(peer_id, "❌ Вы не гражданин. /гражданство")
        else: send(peer_id, f"❌ {mention(target, peer_id)} не гражданин.")
        return
    country = cfg["countries"].get(cit["country"], {})
    cn = COUNTRIES.get(cit["country"], {}).get("name", cit["country"])
    rank_name = RANKS.get(cit["rank"], {}).get("name", cit["rank"])
    bal = get_balance(peer_id, target)
    prefetch_names([target])
    lines = [
        "📔 ═══ ПАСПОРТ ═══",
        f"👤 Владелец: {mention(target, peer_id)}",
        f"🌍 Страна: {cn}",
        f"🎖️ Должность: {rank_name}",
        f"💰 Баланс: {fmt_num(bal)}",
        f"📅 Вступил: {fmt_dt(cit['joined_at'])}",
        f"💵 Всего вложено: {fmt_num(cit.get('donated', 0))}",
        "",
        "🏛️ О стране:",
        f"👑 Президент: {mention(country.get('president')) if country.get('president') else '—'}",
        f"🎖️ Главком: {mention(country.get('commander')) if country.get('commander') else '—'}",
        f"👥 Граждан: {len(country.get('citizens', []))}",
        f"💰 Казна: {fmt_num(country.get('treasury', 0))}",
    ]
    send(peer_id, "\n".join(lines))

def cmd_country(peer_id, uid, args):
    if not args:
        send(peer_id, "⚠ /страна <название>. Список: /страны"); return
    key = args[0].lower()
    if key not in COUNTRIES: send(peer_id, "❌ Страна не найдена."); return
    country = cfg["countries"].get(key, {})
    cn = COUNTRIES[key]["name"]
    lines = [
        f"🏛️ ═══ {cn} ═══",
        f"👑 Президент: {mention(country.get('president')) if country.get('president') else '—'}",
        f"🎖️ Главком: {mention(country.get('commander')) if country.get('commander') else '—'}",
        f"👥 Граждан: {len(country.get('citizens', []))}",
        f"⚔️ Армия: {country.get('army', 0)} чел.",
        f"💰 Казна: {fmt_num(country.get('treasury', 0))}",
        "",
        "📜 Доступные должности:",
    ]
    for k, r in RANKS.items():
        if r["cost"] > 0:
            lines.append(f"• {r['name']} — {fmt_num(r['cost'])} (×{r['bonus_mult']} доход)")
        else:
            lines.append(f"• {r['name']} — назначается")
    lines.append("\n🌍 /гражданство — стать гражданином")
    send(peer_id, "\n".join(lines))

def cmd_countries(peer_id, uid):
    lines = ["🌍 Страны мира:", ""]
    for k, c in COUNTRIES.items():
        country = cfg["countries"].get(k, {})
        pres = country.get("president")
        pt = f"👑 {mention(pres, peer_id)}" if pres else "❌ нет"
        lines.append(f"{c['name']} — президент: {pt}")
    lines.append("\n📔 /паспорт — ваш паспорт")
    lines.append("🏛️ /страна <название> — подробнее")
    send(peer_id, "\n".join(lines))

def cmd_setpresident(peer_id, uid, args, reply_msg):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔ Только Global."); return
    if not args: send(peer_id, "⚠ /setpresident <страна> @user"); return
    key = args[0].lower()
    if key not in COUNTRIES: send(peer_id, "⚠ Страна не найдена."); return
    target = extract_user(" ".join(args), reply_msg)
    if not target: send(peer_id, "⚠ Укажите @user"); return
    # снять старого
    old = cfg["countries"][key].get("president")
    if old and get_citizenship(old): 
        cfg["citizens"][str(old)]["rank"] = "гражданин"
    # назначить
    if get_citizenship(target) and get_citizenship(target)["country"] != key:
        send(peer_id, "⚠ Пользователь — гражданин другой страны. Сначала /гражданство."); return
    if not get_citizenship(target): set_citizenship(target, key)
    cfg["citizens"][str(target)]["rank"] = "президент"
    cfg["countries"][key]["president"] = target
    save_cfg(cfg)
    send(peer_id, f"👑 {mention(target, peer_id)} — Президент {COUNTRIES[key]['name']}!")
    log_action(uid, f"назначил президента {key}: {mention(target, peer_id)}")

def cmd_setcommander(peer_id, uid, args, reply_msg):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔ Только Global."); return
    if not args: send(peer_id, "⚠ /setcommander <страна> @user"); return
    key = args[0].lower()
    if key not in COUNTRIES: send(peer_id, "⚠ Страна не найдена."); return
    target = extract_user(" ".join(args), reply_msg)
    if not target: send(peer_id, "⚠ Укажите @user"); return
    if get_citizenship(target) and get_citizenship(target)["country"] != key:
        send(peer_id, "⚠ Пользователь из другой страны."); return
    if not get_citizenship(target): set_citizenship(target, key)
    old = cfg["countries"][key].get("commander")
    if old and get_citizenship(old): cfg["citizens"][str(old)]["rank"] = "гражданин"
    cfg["citizens"][str(target)]["rank"] = "главком"
    cfg["countries"][key]["commander"] = target
    save_cfg(cfg)
    send(peer_id, f"🎖️ {mention(target, peer_id)} — Главнокомандующий {COUNTRIES[key]['name']}!")

# ================================================================
# СПРАВКА
# ================================================================
def build_help():
    return f"""📋 Команды:

🎮 ЭКОНОМИКА
/баланс /топ /приз /подписка
/buybiz /mybiz /collect

🎲 ИГРЫ
/казино /дуэль /монетка /кубик /слоты /краш /дартс
/колесо /рулетка /блэкджек /мины /башня /кейс /гонка /рыбалка

🌍 СТРАНЫ
/страны — все страны
/гражданство <страна> — стать гражданином
/паспорт [@user] — паспорт
/страна <название> — статистика
/setpresident <страна> @user — Global
/setcommander <страна> @user — Global

💼 БИЗНЕСЫ — {", ".join(BUSINESSES.keys())}

🎟️ ПРОМОКОДЫ
/promo <код> /createpromo <код> <награда> /promolist

🎭 ИВЕНТЫ — /ивент
/ивент мафия — игра (18 ролей)

🛡️ МОДЕРАЦИЯ
/warn /unwarn /mute /unmute /nick /rnick
/kick /ban /unban /gban /ungban /clear /banlist
/tickets /adt

👑 ВЛАДЕЛЕЦ БЕСЕДЫ
/addstaff @user <роль>
/setrole @user <роль>
/removestaff @user
/newrole <название> <0-100>
/delrole /setwarns /setmutetime /setlog

🌐 GLOBAL
/объявление /createivent /setpresident /setcommander

⚙️ /cmd — переименовать команду
💡 /offer /report — идея / жалоба

💰 Стартовый баланс: {START_BALANCE}
🎁 /приз до {fmt_num(PRIZE_MAX)} раз в 24ч
"""

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
    if not w: send(peer_id, "❌ Нет."); return
    c["muted"][str(w)] = {"until":time.time()+300,"last_dm":0}; save_cfg(cfg)
    send(peer_id, f"🎃 {mention(w,peer_id)} → 🔇 5 мин."); mute_notify_dm(w,5)

def ev_newyear(peer_id):
    c = get_chat(peer_id); un = 0
    for k in list(c["muted"].keys()): del c["muted"][k]; un += 1
    w = _pick(peer_id)
    if w:
        c["nicknames"][str(w)] = "🎄 Снегурочка"; save_cfg(cfg)
        send(peer_id, f"🎄 Снято мьютов: {un}\n{mention(w,peer_id)} → 🎄 Снегурочка")
    else: save_cfg(cfg); send(peer_id, f"🎄 Снято: {un}")

def ev_admin_abuse(peer_id):
    c = get_chat(peer_id); w = _pick(peer_id)
    if not w: send(peer_id, "❌ Нет."); return
    c["nicknames"][str(w)] = ADMIN_ABUSE_TITLE
    stats = c.setdefault("user_stats",{}); key = str(w)
    s = stats.get(key) or {"msg_count":0,"last_text":"","last_at":0}
    s["msg_count"] += ADMIN_ABUSE_MSGS; stats[key] = s; save_cfg(cfg)
    send(peer_id, f"👑 ADMIN ABUSE!\n{mention(w,peer_id)} → {ADMIN_ABUSE_TITLE}\n+{ADMIN_ABUSE_MSGS} сообщений!")

def ev_race(peer_id):
    c = get_chat(peer_id); w = _pick(peer_id)
    if not w: send(peer_id, "❌ Нет."); return
    c["nicknames"][str(w)] = "🏎️ Гонщик"; save_cfg(cfg)
    send(peer_id, f"🏎️ {mention(w,peer_id)} — 🏎️ Гонщик!")

def ev_gold(peer_id):
    w = _pick(peer_id)
    if not w: send(peer_id, "❌ Нет."); return
    b = int(500 * full_vip_mult(peer_id, w)); nb = add_balance(peer_id, w, b)
    send(peer_id, f"💰 {mention(w,peer_id)} — +{fmt_num(b)}!\nБаланс: {fmt_num(nb)}")

def ev_treasure(peer_id):
    w = _pick(peer_id)
    if not w: send(peer_id, "❌ Нет."); return
    b = int(200 * full_vip_mult(peer_id, w)); nb = add_balance(peer_id, w, b)
    send(peer_id, f"🗝 {mention(w,peer_id)} — +{fmt_num(b)}!\nБаланс: {fmt_num(nb)}")

def ev_blackout(peer_id):
    c = get_chat(peer_id); users = get_chat_members(peer_id)
    if not users: send(peer_id, "❌ Нет."); return
    until = time.time() + 120
    for u in users: c["muted"][str(u)] = {"until":until,"last_dm":0}
    save_cfg(cfg); send(peer_id, f"🌑 Блэкаут! {len(users)} в муте на 2 мин.")

def ev_phoenix(peer_id):
    c = get_chat(peer_id); un = 0
    for k in list(c["muted"].keys()): del c["muted"][k]; un += 1
    users = get_chat_members(peer_id)
    if users:
        for w in random.sample(users, min(3,len(users))): c["nicknames"][str(w)] = "🔥 Феникс"
        save_cfg(cfg)
        send(peer_id, f"🔥 Снято: {un}\nТитул 🔥 Феникс: " +
             ", ".join(mention(w,peer_id) for w in random.sample(users, min(3,len(users)))))
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
# МАФИЯ (расширенная — 18 ролей)
# ================================================================
MAFIA_MIN = 4
MAFIA_LOBBY = 60
MAFIA_DAY = 120
MAFIA_VOTE = 60
MAFIA_JOIN_WORDS = {"вступить","я","+","играю","в игре","мафия","го","за"}

# Роли
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
R_POLICE = "👮 Полицейский"  # для малых игр (4-5)
R_JUDGE = "⚖️ Ведущий"  # бот

MAFIA_TEAM = {R_MAFIA, R_DON, R_LOVER, R_LAWYER}
CITY_TEAM = {R_SHERIFF, R_DOCTOR, R_JOURNALIST, R_BEAUTY, R_BOMB, R_WEREWOLF, R_SLEEPWALKER, R_CIVILIAN, R_POLICE}
NEUTRAL_TEAM = {R_MANIAC}

GAMES = {}; GAMES_LOCK = threading.Lock()

def _role_pool(n):
    """Собирает набор ролей по количеству игроков."""
    pool = []
    if n == 4:
        pool = [R_MAFIA, R_POLICE, R_DOCTOR, R_CIVILIAN]
    elif n == 5:
        pool = [R_MAFIA, R_POLICE, R_DOCTOR, R_CIVILIAN, R_CIVILIAN]
    elif n == 6:
        pool = [R_MAFIA, R_DON, R_SHERIFF, R_DOCTOR, R_CIVILIAN, R_CIVILIAN]
    elif n == 7:
        pool = [R_MAFIA, R_DON, R_SHERIFF, R_DOCTOR, R_MANIAC, R_CIVILIAN, R_CIVILIAN]
    elif n == 8:
        pool = [R_MAFIA, R_DON, R_LOVER, R_SHERIFF, R_DOCTOR, R_MANIAC, R_CIVILIAN, R_CIVILIAN]
    elif n == 9:
        pool = [R_MAFIA, R_DON, R_LOVER, R_SHERIFF, R_DOCTOR, R_JOURNALIST, R_MANIAC, R_CIVILIAN, R_CIVILIAN]
    elif n == 10:
        pool = [R_MAFIA, R_DON, R_LOVER, R_LAWYER, R_SHERIFF, R_DOCTOR,
                R_JOURNALIST, R_MANIAC, R_CIVILIAN, R_CIVILIAN]
    elif n == 11:
        pool = [R_MAFIA, R_MAFIA, R_DON, R_LOVER, R_LAWYER, R_SHERIFF, R_DOCTOR,
                R_JOURNALIST, R_MANIAC, R_CIVILIAN, R_CIVILIAN]
    elif n == 12:
        pool = [R_MAFIA, R_MAFIA, R_DON, R_LOVER, R_LAWYER, R_SHERIFF, R_DOCTOR,
                R_JOURNALIST, R_BEAUTY, R_MANIAC, R_CIVILIAN, R_CIVILIAN]
    else:
        # 13+ — всё
        pool = [R_MAFIA, R_MAFIA, R_DON, R_LOVER, R_LAWYER, R_SHERIFF, R_DOCTOR,
                R_JOURNALIST, R_BEAUTY, R_BOMB, R_WEREWOLF, R_SLEEPWALKER,
                R_MANIAC, R_CIVILIAN, R_CIVILIAN, R_CIVILIAN]
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
            "round":0,"_alive_order":[],"lawyer_target":None,"beauty_guest":None,
            "bomb_mines":[],"journalist_pairs":{},
        }
    send(peer_id, f"""🎭 <b>МАФИЯ</b> 🎭
Ведущий — бот. Вступить: напишите «вступить» («я», «+»).
Мин: {MAFIA_MIN} | Сбор: {MAFIA_LOBBY}с

<b>Роли (зависят от кол-ва игроков):</b>
👤 Мирные · 🔫 Мафия · 👑 Дон · 👮 Шериф/Полицейский
💉 Доктор · 🔪 Маньяк · 💋 Любовница · 📰 Журналист
⚖️ Адвокат · 💃 Красотка · 💣 Бомба · 🐺 Оборотень
🌙 Лунатик

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
    pool = _role_pool(len(players))
    roles = dict(zip(players, pool))
    g["players"] = roles; g["alive"] = set(players); g["round"] = 0; g["phase"] = "night"
    names = "\n".join(f"— {get_vk_name(u)}" for u in players)
    for uid, role in roles.items():
        send_dm(uid, f"🎭 Ваша роль: {role}\n\nИграют:\n{names}")
    send(peer_id, f"🎭 Игра началась! {len(players)} игроков. Роли в ЛС.")
    mafia_start_night(peer_id)

def mafia_start_night(peer_id):
    g = GAMES.get(peer_id)
    if not g: return
    if not g["alive"]: GAMES.pop(peer_id,None); return
    g["phase"] = "night"; g["round"] += 1
    g["night_step_idx"] = 0; g["night_step"] = None; g["night_actions"] = {}
    g["waiter_block"] = None; g["votes"] = {}
    g["lawyer_target"] = None; g["beauty_guest"] = None
    send(peer_id, f"🌃 Раунд {g['round']}. Город засыпает...")
    mafia_next_step(peer_id)

# порядок ночных шагов
NIGHT_ORDER = [
    ("mafia", {R_MAFIA, R_DON}, "🔫 Просыпается Мафия..."),
    ("don", {R_DON}, "👑 Дон проверяет..."),
    ("sheriff", {R_SHERIFF, R_POLICE}, "👮 Просыпается Шериф..."),
    ("doctor", {R_DOCTOR}, "💉 Просыпается Доктор..."),
    ("lover", {R_LOVER}, "💋 Просыпается Любовница..."),
    ("journalist", {R_JOURNALIST}, "📰 Просыпается Журналист..."),
    ("lawyer", {R_LAWYER}, "⚖️ Просыпается Адвокат..."),
    ("beauty", {R_BEAUTY}, "💃 Просыпается Красотка..."),
    ("maniac", {R_MANIAC}, "🔪 Просыпается Маньяк..."),
]

def _alive_list(g):
    alive = sorted(g["alive"]); g["_alive_order"] = alive
    return "\n".join(f"{i+1}. {get_vk_name(u)}" for i,u in enumerate(alive))

def mafia_next_step(peer_id):
    g = GAMES.get(peer_id)
    if not g or g["phase"] != "night": return
    roles_present = {g["players"][u] for u in g["alive"]}
    while g["night_step_idx"] < len(NIGHT_ORDER):
        step, roles, _ = NIGHT_ORDER[g["night_step_idx"]]; g["night_step_idx"] += 1
        if roles_present & roles:
            g["night_step"] = step
            mafia_announce(peer_id, step); return
    mafia_resolve(peer_id)

def mafia_announce(peer_id, step):
    g = GAMES.get(peer_id)
    if not g: return
    lst = _alive_list(g)
    if step == "mafia":
        send(peer_id, "🔫 Просыпается Мафия...")
        for u,r in g["players"].items():
            if r in (R_MAFIA, R_DON) and u in g["alive"]:
                send_dm(u, f"🔫 Кого убить:\n\n{lst}\n\nНомер.")
    elif step == "don":
        send(peer_id, "👑 Дон проверяет...")
        for u,r in g["players"].items():
            if r == R_DON and u in g["alive"]:
                send_dm(u, f"👑 Кого проверить (ищем Шерифа):\n\n{lst}\n\nНомер.")
    elif step == "sheriff":
        send(peer_id, "👮 Просыпается Шериф...")
        for u,r in g["players"].items():
            if r in (R_SHERIFF, R_POLICE) and u in g["alive"]:
                send_dm(u, f"👮 Кого проверить:\n\n{lst}\n\nНомер.")
    elif step == "doctor":
        send(peer_id, "💉 Просыпается Доктор...")
        for u,r in g["players"].items():
            if r == R_DOCTOR and u in g["alive"]:
                send_dm(u, f"💉 Кого спасти (можно себя 1 раз):\n\n{lst}\n\nНомер.")
    elif step == "lover":
        send(peer_id, "💋 Просыпается Любовница...")
        for u,r in g["players"].items():
            if r == R_LOVER and u in g["alive"]:
                send_dm(u, f"💋 Кого заблокировать:\n\n{lst}\n\nНомер.")
    elif step == "journalist":
        send(peer_id, "📰 Просыпается Журналист...")
        for u,r in g["players"].items():
            if r == R_JOURNALIST and u in g["alive"]:
                send_dm(u, f"📰 Проверить 2 игрока (в одной ли команде):\n\n{lst}\n\nДва номера через запятую: 2,5")
    elif step == "lawyer":
        send(peer_id, "⚖️ Просыпается Адвокат...")
        for u,r in g["players"].items():
            if r == R_LAWYER and u in g["alive"]:
                send_dm(u, f"⚖️ Кого защитить от казни:\n\n{lst}\n\nНомер.")
    elif step == "beauty":
        send(peer_id, "💃 Просыпается Красотка...")
        for u,r in g["players"].items():
            if r == R_BEAUTY and u in g["alive"]:
                send_dm(u, f"💃 Кого забрать к себе (защита):\n\n{lst}\n\nНомер.")
    elif step == "maniac":
        send(peer_id, "🔪 Просыпается Маньяк...")
        for u,r in g["players"].items():
            if r == R_MANIAC and u in g["alive"]:
                send_dm(u, f"🔪 Кого убить:\n\n{lst}\n\nНомер.")

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
    # проверка кто ходит
    actors = {
        "mafia": (R_MAFIA, R_DON),
        "don": (R_DON,),
        "sheriff": (R_SHERIFF, R_POLICE),
        "doctor": (R_DOCTOR,),
        "lover": (R_LOVER,),
        "journalist": (R_JOURNALIST,),
        "lawyer": (R_LAWYER,),
        "beauty": (R_BEAUTY,),
        "maniac": (R_MANIAC,),
    }
    if role not in actors.get(step, ()): return False
    if step in g["night_actions"]: 
        if step != "mafia": send_dm(uid, "Уже выбрали."); return True
    if step == "journalist":
        pair = mafia_parse_num(text, g, 2)
        if not pair: send_dm(uid, "⚠️ Напишите 2 номера: 2,5"); return True
        g["night_actions"][step] = pair
        a, b = pair
        same = (g["players"][a] in MAFIA_TEAM) == (g["players"][b] in MAFIA_TEAM)
        send_dm(uid, f"📰 {get_vk_name(a)} и {get_vk_name(b)} " +
                     ("в ОДНОЙ команде." if same else "в РАЗНЫХ командах."))
    else:
        t = mafia_parse_num(text, g, 1)
        if not t: send_dm(uid, "⚠️ Напишите номер."); return True
        g["night_actions"][step] = t
        send_dm(uid, f"✅ {get_vk_name(t)}")
        if step == "sheriff":
            if g["players"].get(t) in MAFIA_TEAM:
                send_dm(uid, f"✅ {get_vk_name(t)} — МАФИЯ!")
            else: send_dm(uid, f"❌ {get_vk_name(t)} — не мафия.")
        elif step == "don":
            if g["players"].get(t) in (R_SHERIFF, R_POLICE):
                send_dm(uid, f"👑 {get_vk_name(t)} — ШЕРИФ!")
            else: send_dm(uid, f"👑 {get_vk_name(t)} — не шериф.")
    ann = {
        "mafia":"🔫 Мафия сделала выбор.",
        "don":"👑 Дон сделал выбор.",
        "sheriff":"👮 Шериф сделал выбор.",
        "doctor":"💉 Доктор сделал выбор.",
        "lover":"💋 Любовница сделала выбор.",
        "journalist":"📰 Журналист сделал выбор.",
        "lawyer":"⚖️ Адвокат сделал выбор.",
        "beauty":"💃 Красотка сделала выбор.",
        "maniac":"🔪 Маньяк сделал выбор.",
    }
    send(peer_id, ann.get(step, ""))
    g["night_step"] = None
    mafia_next_step(peer_id)
    return True

def mafia_resolve(peer_id):
    g = GAMES.get(peer_id)
    if not g: return
    send(peer_id, "🌅 Город просыпается...")
    acts = g["night_actions"]
    mafia_t = acts.get("mafia")
    maniac_t = acts.get("maniac")
    doc_t = acts.get("doctor")
    beauty_t = acts.get("beauty")
    # Красотка защищает beauty_t (и себя, если она его спасает)
    protected = set()
    if doc_t: protected.add(doc_t)
    if beauty_t: protected.add(beauty_t)
    
    victims = []
    if mafia_t and mafia_t not in protected: victims.append(mafia_t)
    if maniac_t and maniac_t not in protected and maniac_t not in victims:
        victims.append(maniac_t)
    
    if not victims:
        send(peer_id, "☀️ Этой ночью никто не погиб!")
    else:
        for v in victims:
            g["alive"].discard(v)
            send(peer_id, f"💀 Убит {get_vk_name(v)}. Роль: {g['players'][v]}")
        # Красотка — если её убили, гость тоже умирает
        if beauty_t and beauty_t not in g["alive"] and beauty_t in g["alive"]:
            pass
        if beauty_t and beauty_t in victims and beauty_t in g["alive"]:
            pass
        if beauty_t in victims:
            guest = beauty_t
            # гость — сама красотка (упрощение)
    
    g["lawyer_target"] = acts.get("lawyer")
    g["waiter_block"] = acts.get("lover")  # любовница блокирует голос
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
    if am == 0 and nm == 0:
        mafia_end(peer_id, "🎉 Город победил!"); return True
    if am >= ac + nm and am > 0:
        mafia_end(peer_id, "🔫 Мафия победила!"); return True
    if nm > 0 and len(g["alive"]) == 1:
        mafia_end(peer_id, "🔪 Маньяк победил!"); return True
    return False

def mafia_start_vote(peer_id):
    g = GAMES.get(peer_id)
    if not g or g["phase"] != "day": return
    g["phase"] = "voting"; g["votes"] = {}; g["vote_deadline"] = time.time() + MAFIA_VOTE
    send(peer_id, "🗳️ Голосование! Списки в ЛС.")
    alive = sorted(g["alive"]); g["_alive_order"] = alive
    names = "\n".join(f"{i+1}. {get_vk_name(u)}" for i,u in enumerate(alive))
    for u in alive:
        note = "\n⚠️ Вы лишены голоса (Любовница)." if g.get("waiter_block")==u else ""
        send_dm(u, f"🗳️ Голосуйте:\n\n{names}\n\nНомер или 'пропуск'.{note}")

def mafia_vote_dm(uid, text, peer_id):
    g = GAMES.get(peer_id)
    if not g or g["phase"] != "voting" or uid not in g["alive"]: return False
    if uid in g["votes"]: send_dm(uid, "Уже голосовали."); return True
    t = text.strip().lower()
    if t in ("пропуск","skip","пас","0"):
        g["votes"][uid] = "skip"; send_dm(uid, "✅ Пропуск."); return True
    target = mafia_parse_num(text, g, 1)
    if not target: send_dm(uid, "⚠️ Номер или 'пропуск'."); return True
    if target == uid: send_dm(uid, "⚠️ Не за себя."); return True
    g["votes"][uid] = target
    send_dm(uid, f"✅ За {get_vk_name(target)}."); return True

def mafia_tally(peer_id):
    g = GAMES.get(peer_id)
    if not g: return
    g["phase"] = "ended"; counts = {}; skip = 0
    for voter, tgt in g["votes"].items():
        if voter == g.get("waiter_block"): continue
        if tgt == "skip": skip += 1
        else: counts[tgt] = counts.get(tgt,0) + 1
    if not counts:
        send(peer_id, "🗳️ Все воздержались."); mafia_start_night(peer_id); return
    mx = max(counts.values())
    top = [u for u,c in counts.items() if c == mx]
    if len(top) > 1:
        send(peer_id, "🗳️ Ничья."); mafia_start_night(peer_id); return
    victim = top[0]
    # Адвокат защищает
    if g.get("lawyer_target") == victim:
        send(peer_id, f"⚖️ Адвокат спас {get_vk_name(victim)} от казни!")
        mafia_start_night(peer_id); return
    role = g["players"][victim]; g["alive"].discard(victim)
    if role in MAFIA_TEAM:
        send(peer_id, f"🎉 {get_vk_name(victim)} — был в мафии! ({role})")
    else:
        send(peer_id, f"❌ {get_vk_name(victim)} — {role}.")
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
        cn = COUNTRIES.get(cit["country"], {}).get("name", cit["country"])
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
    lines = ["👮 Состав администрации:", "",
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
    send(peer_id, f"👋 Добро пожаловать, {u}!\n\n📋 /help\n💰 /баланс\n🌍 /гражданство\n🎭 /ивент")

# ================================================================
# ИГРЫ
# ================================================================
def _bet(args, bal):
    for i, a in enumerate(args):
        if a.isdigit() and int(a) > 0:
            b = int(a)
            if b > bal: return None, f"❌ Мало монет ({fmt_num(bal)})."
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
    if not rest: send(peer_id, "⚠ /краш <ставка> <множитель 1.1-10>"); return
    try: t = float(rest[0].replace(",", "."))
    except Exception: send(peer_id, "⚠ Числом."); return
    if not 1.1 <= t <= 10: send(peer_id, "⚠ 1.1-10"); return
    crash = round(random.uniform(1.0, 12.0), 2)
    if t <= crash:
        win = int(b * (t-1) * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, win)
        send(peer_id, f"🚀 {crash}x (цель {t}x)\n🎉 +{fmt_num(win)}\nБаланс: {fmt_num(nb)}")
    else:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"🚀 {crash}x (цель {t}x)\n💀 -{fmt_num(b)}\nБаланс: {fmt_num(nb)}")

def game_darts(peer_id, uid, args):
    bal = get_balance(peer_id, uid); b, _ = _bet(args, bal)
    if b is None: send(peer_id, _); return
    sc = random.randint(0,100)
    if sc >= 90: m, e = 5, "🎯 В яблочко!"
    elif sc >= 70: m, e = 3, "🎯 Отлично!"
    elif sc >= 50: m, e = 2, "🎯 Хорошо"
    elif sc >= 30: m, e = 1, "🎯 Слабо"
    else: m, e = 0, "🎯 Мимо"
    if m:
        w = int(b * m * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, w)
        send(peer_id, f"🎯 {sc}/100 {e}\n💰 +{fmt_num(w)}\nБаланс: {fmt_num(nb)}")
    else:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"🎯 {sc}/100 {e}\n💀 -{fmt_num(b)}\nБаланс: {fmt_num(nb)}")

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
        send(peer_id, f"🎡 {num} {color}\n🎉 x{m}! +{fmt_num(w)}\nБаланс: {fmt_num(nb)}")
    else:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"🎡 {num} {color}\n💀 -{fmt_num(b)}\nБаланс: {fmt_num(nb)}")

def game_roulette(peer_id, uid, args):
    bal = get_balance(peer_id, uid); b, rest = _bet(args, bal)
    if b is None: send(peer_id, rest); return
    if not rest or not rest[0].isdigit(): send(peer_id, "⚠ /рулетка <ставка> <0-36>"); return
    n = int(rest[0])
    if not 0 <= n <= 36: send(peer_id, "⚠ 0-36"); return
    res = random.randint(0,36)
    if res == n:
        w = int(b * 36 * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, w)
        send(peer_id, f"🎰 {res}\n🎉 x36! +{fmt_num(w)}\nБаланс: {fmt_num(nb)}")
    else:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"🎰 {res}\n💀 -{fmt_num(b)}\nБаланс: {fmt_num(nb)}")

def game_bj(peer_id, uid, args):
    """Упрощённый блэкджек — просто 50/50 на сумму."""
    bal = get_balance(peer_id, uid); b, _ = _bet(args, bal)
    if b is None: send(peer_id, _); return
    p = random.randint(15,21); d = random.randint(15,21)
    if p > d:
        w = int(b * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, w)
        send(peer_id, f"🃏 Вы: {p} | Дилер: {d}\n🎉 +{fmt_num(w)}\nБаланс: {fmt_num(nb)}")
    elif p == d:
        send(peer_id, f"🃏 Вы: {p} | Дилер: {d}\n🤝 Ничья\nБаланс: {fmt_num(bal)}")
    else:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"🃏 Вы: {p} | Дилер: {d}\n💀 -{fmt_num(b)}\nБаланс: {fmt_num(nb)}")

def game_mines(peer_id, uid, args):
    bal = get_balance(peer_id, uid); b, _ = _bet(args, bal)
    if b is None: send(peer_id, _); return
    lost = random.random() < 0.35
    if not lost:
        w = int(b * 1.7 * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, w)
        send(peer_id, f"💣 Мины: чисто!\n🎉 +{fmt_num(w)}\nБаланс: {fmt_num(nb)}")
    else:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"💣 Мины: БАБАХ!\n💀 -{fmt_num(b)}\nБаланс: {fmt_num(nb)}")

def game_tower(peer_id, uid, args):
    bal = get_balance(peer_id, uid); b, rest = _bet(args, bal)
    if b is None: send(peer_id, rest); return
    floors = int(rest[0]) if rest and rest[0].isdigit() else 1
    if not 1 <= floors <= 5: floors = 1
    lost = random.random() > 0.6
    if not lost:
        w = int(b * (1 + floors*0.8) * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, w)
        send(peer_id, f"🗼 Башня — {floors} этаж(ей)!\n🎉 +{fmt_num(w)}\nБаланс: {fmt_num(nb)}")
    else:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"🗼 Башня — упали!\n💀 -{fmt_num(b)}\nБаланс: {fmt_num(nb)}")

def game_case(peer_id, uid, args):
    bal = get_balance(peer_id, uid); b, _ = _bet(args, bal)
    if b is None: send(peer_id, _); return
    mult = random.choice([0, 0, 0.5, 1, 1.5, 2, 3, 5, 10])
    if mult == 0:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"📦 Пусто\n💀 -{fmt_num(b)}\nБаланс: {fmt_num(nb)}")
    else:
        w = int(b * (mult-1) * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, w)
        send(peer_id, f"📦 x{mult}! +{fmt_num(w)}\nБаланс: {fmt_num(nb)}")

def game_race(peer_id, uid, args):
    bal = get_balance(peer_id, uid); b, _ = _bet(args, bal)
    if b is None: send(peer_id, _); return
    p = random.random()
    if p < 0.4:
        w = int(b * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, w)
        send(peer_id, f"🏎️ Вы пришли первым!\n🎉 +{fmt_num(w)}\nБаланс: {fmt_num(nb)}")
    else:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"🏎️ Вы проиграли гонку\n💀 -{fmt_num(b)}\nБаланс: {fmt_num(nb)}")

def game_fish(peer_id, uid, args):
    bal = get_balance(peer_id, uid); b, _ = _bet(args, bal)
    if b is None: send(peer_id, _); return
    if random.random() < 0.55:
        w = int(b * 1.8 * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, w)
        send(peer_id, f"🎣 Поймали!\n🎉 +{fmt_num(w)}\nБаланс: {fmt_num(nb)}")
    else:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"🎣 Сорвалась!\n💀 -{fmt_num(b)}\nБаланс: {fmt_num(nb)}")

def cmd_casino(peer_id, uid, args):
    bal = get_balance(peer_id, uid); b, _ = _bet(args, bal)
    if b is None: send(peer_id, _); return
    if random.random() < 0.5:
        w = int(b * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, w)
        send(peer_id, f"🎰 🎉 +{fmt_num(w)}\nБаланс: {fmt_num(nb)}")
    else:
        nb = add_balance(peer_id, uid, -b); send(peer_id, f"🎰 💀 -{fmt_num(b)}\nБаланс: {fmt_num(nb)}")

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
    win = random.choice([uid, t]); lose = t if win == uid else uid
    add_balance(peer_id, uid, -b); add_balance(peer_id, t, -b)
    bonus = int(b * 2 * full_vip_mult(peer_id, win)); nb = add_balance(peer_id, win, bonus)
    send(peer_id, f"⚔️ {mention(uid,peer_id)} vs {mention(t,peer_id)}\n🏆 {mention(win,peer_id)} +{fmt_num(bonus)}\nБаланс: {fmt_num(nb)}")

# ================================================================
# БИЗНЕСЫ / ЭКОНОМИКА
# ================================================================
def cmd_buybiz(peer_id, uid, args):
    c = get_chat(peer_id)
    if not args:
        lines = ["💼 Бизнесы:"]
        for k, v in BUSINESSES.items():
            lines.append(f"{v['emoji']} {k} — {fmt_num(v['price'])} (доход {fmt_num(v['income'])}/час)")
        send(peer_id, "\n".join(lines)); return
    name = args[0].lower()
    if name not in BUSINESSES: send(peer_id, "⚠ Нет такого."); return
    biz = BUSINESSES[name]; bal = get_balance(peer_id, uid)
    if bal < biz["price"]: send(peer_id, f"❌ Нужно {fmt_num(biz['price'])}"); return
    my = c.setdefault("businesses", {}).setdefault(str(uid), {})
    if name in my: send(peer_id, f"⚠ Уже есть."); return
    my[name] = {"bought_at":int(time.time()),"last_collect":int(time.time())}
    add_balance(peer_id, uid, -biz["price"]); save_cfg(cfg)
    send(peer_id, f"✅ Куплен {biz['emoji']} {name}\nДоход: {fmt_num(biz['income'])}/час")

def cmd_mybiz(peer_id, uid):
    c = get_chat(peer_id); my = c.get("businesses", {}).get(str(uid), {})
    if not my: send(peer_id, "📭 Нет бизнесов."); return
    lines = ["💼 Бизнесы:"]; total = 0
    for n, info in my.items():
        b = BUSINESSES.get(n)
        if not b: continue
        h = min((time.time()-info["last_collect"])/3600, 24)
        inc = int(b["income"]*h*full_vip_mult(peer_id, uid))
        lines.append(f"{b['emoji']} {n} — {fmt_num(b['income'])}/час | накоплено {fmt_num(inc)}")
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
    nb = add_balance(peer_id, uid, total); send(peer_id, f"💰 +{fmt_num(total)}\nБаланс: {fmt_num(nb)}")

def cmd_prize(peer_id, uid):
    c = get_chat(peer_id); last = c.get("last_prize", {}); now = int(time.time()); k = str(uid)
    el = now - last.get(k, 0)
    if el < PRIZE_COOLDOWN:
        w = PRIZE_COOLDOWN - el
        send(peer_id, f"⏳ Через {w//3600}ч {w%3600//60}м"); return
    amt = random.randint(PRIZE_MIN, PRIZE_MAX)
    amt = int(amt * full_vip_mult(peer_id, uid)); nb = add_balance(peer_id, uid, amt)
    last[k] = now; c["last_prize"] = last; save_cfg(cfg)
    send(peer_id, f"🎁 +{fmt_num(amt)}!\nБаланс: {fmt_num(nb)}")

def cmd_sub(peer_id, uid):
    c = get_chat(peer_id)
    if is_vip(peer_id, uid):
        send(peer_id, f"👑 VIP до {fmt_dt(c.get('subs',{}).get(str(uid),0))}\n+{int(VIP_BONUS*100)}% к прибыли"); return
    try:
        res = api.groups.isMember(group_id=GROUP_ID, user_id=uid)
        sub = (len(res)>0 and res[0].get("member")==1) if isinstance(res,list) else bool(res)
    except Exception: sub = False
    if not sub:
        send(peer_id, f"❌ Подпишитесь: {COMMUNITY_LINK}\nПотом /подписка"); return
    if c.get("subs", {}).get(str(uid), 0) > 0: send(peer_id, "⚠ Уже получали."); return
    until = int(time.time()) + VIP_DURATION
    c.setdefault("subs", {})[str(uid)] = until
    nb = add_balance(peer_id, uid, VIP_PRICE); save_cfg(cfg)
    send(peer_id, f"👑 VIP до {fmt_dt(until)}\n💰 +{fmt_num(VIP_PRICE)}\n✨ +{int(VIP_BONUS*100)}%")

def cmd_promo(peer_id, uid, args):
    if not args: send(peer_id, "⚠ /promo <код>"); return
    code = args[0].upper(); c = get_chat(peer_id)
    promo = c.get("promos", {}).get(code) or cfg.get("global_promos", {}).get(code)
    if not promo: send(peer_id, "❌ Не найден."); return
    used = c.setdefault("promos_used", {}).setdefault(str(uid), [])
    if code in used: send(peer_id, "⚠ Уже использован."); return
    if promo.get("uses_left",0) <= 0: send(peer_id, "⚠ Исчерпан."); return
    nb = add_balance(peer_id, uid, promo["reward"]); promo["uses_left"] -= 1
    used.append(code); save_cfg(cfg)
    send(peer_id, f"🎟️ +{fmt_num(promo['reward'])}\nБаланс: {fmt_num(nb)}")

def cmd_createpromo(peer_id, uid, args):
    c = get_chat(peer_id)
    if len(args) < 2 or not args[1].isdigit():
        send(peer_id, "⚠ /createpromo <код> <награда>"); return
    code = args[0].upper(); rw = int(args[1])
    if not 100 <= rw <= 1000000: send(peer_id, "⚠ 100-1 000 000"); return
    if code in c.get("promos", {}): send(peer_id, "⚠ Уже есть."); return
    c.setdefault("promos", {})[code] = {"reward":rw,"created_by":uid,
                                         "created_at":int(time.time()),"uses_left":100}
    save_cfg(cfg); send(peer_id, f"✅ Промокод {code} ({fmt_num(rw)})")

def cmd_promolist(peer_id, uid):
    c = get_chat(peer_id); promos = c.get("promos", {}); glob = cfg.get("global_promos", {})
    if not promos and not glob: send(peer_id, "📭 Нет."); return
    lines = ["🎟️ Промокоды:"]
    if promos:
        lines.append("\n📌 Локальные:")
        for code, p in promos.items(): lines.append(f"• {code} — {fmt_num(p['reward'])} ({p['uses_left']})")
    if glob:
        lines.append("\n🌐 Глобальные:")
        for code, p in glob.items(): lines.append(f"• {code} — {fmt_num(p['reward'])} ({p['uses_left']})")
    send(peer_id, "\n".join(lines))

# ================================================================
# ТОП / ВАЙП / БИЛДЫ
# ================================================================
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
    if not data: send(peer_id, "📭 Нет данных."); return
    prefetch_names([int(k) for k,_ in data[:10]])
    lines = [title,""]; medals = ["🥇","🥈","🥉"]
    for i,(uid,v) in enumerate(data[:10]):
        m = medals[i] if i<3 else f"{i+1}."
        lines.append(f"{m} {mention(uid,peer_id)} — {fmt_num(v)}")
    send(peer_id, "\n".join(lines))

def cmd_wipe(peer_id, uid):
    if not is_chat(peer_id): send(peer_id, "❌ Только в беседе."); return
    c = get_chat(peer_id)
    if uid != int(cfg["global_owner"]) and c.get("owner") != uid: send(peer_id, "⛔ Нет прав."); return
    c["balance"] = {}; save_cfg(cfg); send(peer_id, "🧹 Вайп!")

def cmd_wipe_all(peer_id, uid):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔ Global."); return
    for ch in cfg.get("chats",{}).values(): ch["balance"] = {}
    save_cfg(cfg); send(peer_id, "🧹 ГЛОБАЛЬНЫЙ ВАЙП!")

def cmd_build(peer_id, uid, args):
    if not is_chat(peer_id): send(peer_id, "❌ Только в беседе."); return
    c = get_chat(peer_id)
    if uid != int(cfg["global_owner"]) and c.get("owner") != uid: send(peer_id, "⛔ Нет прав."); return
    if not args: send(peer_id, f"🏗️ Сетка: {c.get('build_name') or '—'}\n/build <название>"); return
    name = " ".join(args); c["build_name"] = name
    builds = cfg.setdefault("builds", {}); builds.setdefault(name, [])
    if peer_id not in builds[name]: builds[name].append(peer_id)
    save_cfg(cfg); send(peer_id, f"✅ {name} ({len(builds[name])} бесед)")

def cmd_builds(peer_id, uid):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔ Global."); return
    builds = cfg.get("builds", {})
    if not builds: send(peer_id, "📭 Нет."); return
    lines = ["🏗️ Сетки:"]
    for n, ps in builds.items():
        lines.append(f"📦 {n} — {len(ps)} бесед")
    send(peer_id, "\n".join(lines))

def cmd_cmd(peer_id, uid, args):
    c = get_chat(peer_id)
    if len(args) < 2:
        a = c.get("custom_cmds", {})
        if not a: send(peer_id, "⚙️ /cmd <команда> <новое_имя>"); return
        send(peer_id, "\n".join([f"• /{k} → /{v}" for k,v in a.items()])); return
    if args[0].lower() == "reset":
        k = args[1].lower().lstrip("/"); rem = c.get("custom_cmds", {}).pop(k, None); save_cfg(cfg)
        send(peer_id, f"✅ Удалено." if rem else "⚠ Нет."); return
    orig = args[0].lower().lstrip("/"); alias = args[1].lower().lstrip("/")
    if orig not in ALL_COMMANDS: send(peer_id, f"⚠ /{orig} нет."); return
    if alias in ALL_COMMANDS: send(peer_id, f"⚠ /{alias} занято."); return
    c.setdefault("custom_cmds", {})[alias] = orig; save_cfg(cfg)
    send(peer_id, f"✅ /{alias} = /{orig}")

# ================================================================
# ОСНОВНОЙ ЦИКЛ
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
                    c = get_chat(peer_id)
                    if str(inv) in c.get("banned", {}):
                        cid = chat_id_from_peer(peer_id)
                        if cid:
                            kick_user(cid, inv); send(peer_id, f"🚫 в бане.")
                    else: handle_welcome(peer_id, action)
                continue
            if atype == "chat_kick_user": continue

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
        parts = text.split(); cmd = parts[0][1:].lower(); args = parts[1:]
        reply_msg = msg.get("reply_message")

        if is_chat(peer_id):
            aliases = get_chat(peer_id).get("custom_cmds", {})
            if cmd in aliases: cmd = aliases[cmd]

        if cmd not in ALL_COMMANDS:
            sug = suggest_command(cmd)
            if sug: send(peer_id, f"❓ Может /{sug}\n📋 /help", reply_to=reply_ref)
            else: send(peer_id, f"❌ /{cmd} нет.\n💡 /offer <идея>", reply_to=reply_ref)
            continue

        # === ПУБЛИЧНЫЕ ===
        if cmd == "help": send(peer_id, build_help(), reply_to=reply_ref); continue
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
            send(peer_id, f"💰 {fmt_num(b)} монет{vip}" + (f" ({mention(t,peer_id)})" if t != from_id else ""), reply_to=reply_ref); continue
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
                send(peer_id, "⛔ Владелец беседы.", reply_to=reply_ref); continue
            cmd_createpromo(peer_id, from_id, args); continue
        if cmd == "promolist":
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            c = get_chat(peer_id)
            if from_id != int(cfg["global_owner"]) and c.get("owner") != from_id and not can(from_id,"role",peer_id):
                send(peer_id, "⛔ Нет прав.", reply_to=reply_ref); continue
            cmd_promolist(peer_id, from_id); continue
        if cmd in ("гражданство","citizenship"):
            cmd_citizenship(peer_id, from_id, args); continue
        if cmd in ("паспорт","passport"):
            cmd_passport(peer_id, from_id, args, reply_msg); continue
        if cmd in ("страна","country"):
            cmd_country(peer_id, from_id, args); continue
        if cmd in ("страны","государства"):
            cmd_countries(peer_id, from_id); continue
        if cmd == "build": cmd_build(peer_id, from_id, args); continue
        if cmd == "builds":
            if from_id != int(cfg["global_owner"]): send(peer_id, "⛔ Global.", reply_to=reply_ref); continue
            cmd_builds(peer_id, from_id); continue
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

        # проверка прав
        if not can(from_id, cmd, peer_id):
            send(peer_id, "⛔ Нет прав.", reply_to=reply_ref); continue

        if cmd == "role":
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
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
            send(peer_id, f"✅ Отправлено: {ok}", reply_to=reply_ref); continue

        if cmd == "setpresident":
            cmd_setpresident(peer_id, from_id, args, reply_msg); continue
        if cmd == "setcommander":
            cmd_setcommander(peer_id, from_id, args, reply_msg); continue

        if cmd == "newrole":
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            if len(args) < 2 or not args[-1].isdigit():
                send(peer_id, "⚠ /newrole <название> <0-100>", reply_to=reply_ref); continue
            pr = int(args[-1])
            if not 0 <= pr <= 99: send(peer_id, "⚠ 0-99", reply_to=reply_ref); continue
            name = " ".join(args[:-1]).strip(); key = name.lower()
            c = get_chat(peer_id)
            if key in c.get("local_roles", {}) or key in cfg["roles"]:
                send(peer_id, "⚠ Уже есть.", reply_to=reply_ref); continue
            c.setdefault("local_roles", {})[key] = {"name":name,"priority":pr,
                                                     "commands":commands_for_priority(pr)}
            save_cfg(cfg); send(peer_id, f"✅ Роль «{name}» ({pr})", reply_to=reply_ref); continue

        if cmd == "delrole":
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            if not args: send(peer_id, "⚠ /delrole <название>", reply_to=reply_ref); continue
            name = " ".join(args); key = find_role_by_input(name, peer_id)
            if not key: send(peer_id, "⚠ Нет.", reply_to=reply_ref); continue
            c = get_chat(peer_id)
            if key in c.get("local_roles", {}):
                del c["local_roles"][key]
                for u in [x for x,r in c.get("staff",{}).items() if r==key]: del c["staff"][u]
                save_cfg(cfg); send(peer_id, "🗑 Удалено.", reply_to=reply_ref); continue
            if from_id != int(cfg["global_owner"]): send(peer_id, "⛔ Глоб. роли — Global.", reply_to=reply_ref); continue
            for ch in cfg.get("chats",{}).values():
                for u in [x for x,r in ch.get("staff",{}).items() if r==key]: del ch["staff"][u]
            del cfg["roles"][key]; save_cfg(cfg); send(peer_id, "🗑 Удалено.", reply_to=reply_ref); continue

        if cmd == "createivent":
            if from_id != int(cfg["global_owner"]): send(peer_id, "⛔ Global.", reply_to=reply_ref); continue
            if not args: send(peer_id, "⚠ /createivent <название> | <награда> | <требование>", reply_to=reply_ref); continue
            p = [x.strip() for x in " ".join(args).split("|")]
            if len(p) < 3: send(peer_id, "⚠ 3 части через |", reply_to=reply_ref); continue
            n, r, q = p[0], p[1], p[2]; k = n.lower()
            if k in cfg.get("custom_events", {}): send(peer_id, "⚠ Уже есть.", reply_to=reply_ref); continue
            cfg["custom_events"][k] = {"name":n,"reward":r,"requirement":q,
                                        "created_by":from_id,"created_at":int(time.time())}
            save_cfg(cfg); send(peer_id, f"✅ Ивент «{n}»", reply_to=reply_ref); continue

        if cmd == "tickets":
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            send(peer_id, tickets_text(), reply_to=reply_ref); continue
        if cmd == "adt":
            if len(args) < 2 or not args[0].isdigit():
                send(peer_id, "⚠ /adt <№> <ответ>", reply_to=reply_ref); continue
            ok, e = answer_ticket(args[0], from_id, " ".join(args[1:]))
            send(peer_id, f"✅ Готово." if ok else f"❌ {e}", reply_to=reply_ref); continue

        if cmd == "loginfo":
            send(peer_id, f"📝 Лог: {cfg.get('log_peer_id') or 'нет'}", reply_to=reply_ref); continue
        if cmd == "setlog":
            if from_id != int(cfg["global_owner"]) and not (is_chat(peer_id) and get_chat(peer_id).get("owner")==from_id):
                send(peer_id, "⛔ Нет прав.", reply_to=reply_ref); continue
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            cfg["log_peer_id"] = peer_id; save_cfg(cfg)
            send(peer_id, f"✅ Лог: {peer_id}", reply_to=reply_ref); continue
        if cmd == "unsetlog":
            if from_id != int(cfg["global_owner"]): send(peer_id, "⛔ Global.", reply_to=reply_ref); continue
            cfg["log_peer_id"] = 0; save_cfg(cfg); send(peer_id, "✅ Отключён.", reply_to=reply_ref); continue
        if cmd == "setwarns":
            if from_id != int(cfg["global_owner"]) and not (is_chat(peer_id) and get_chat(peer_id).get("owner")==from_id):
                send(peer_id, "⛔ Нет прав.", reply_to=reply_ref); continue
            if not args or not args[0].isdigit(): send(peer_id, "⚠ /setwarns 3", reply_to=reply_ref); continue
            cfg["max_warns"] = int(args[0]); save_cfg(cfg)
            send(peer_id, f"✅ {cfg['max_warns']}", reply_to=reply_ref); continue
        if cmd == "setmutetime":
            if from_id != int(cfg["global_owner"]) and not (is_chat(peer_id) and get_chat(peer_id).get("owner")==from_id):
                send(peer_id, "⛔ Нет прав.", reply_to=reply_ref); continue
            if not args or not args[0].isdigit(): send(peer_id, "⚠ /setmutetime 30", reply_to=reply_ref); continue
            cfg["default_mute_minutes"] = int(args[0]); save_cfg(cfg)
            send(peer_id, f"✅ {cfg['default_mute_minutes']}", reply_to=reply_ref); continue
        if cmd == "banlist":
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            b = get_chat(peer_id).get("banned", {})
            if not b: send(peer_id, "📭 Нет.", reply_to=reply_ref); continue
            lines = ["🚫 Баны:"]
            for u, i in b.items(): lines.append(f"• {mention(u,peer_id)} — {i.get('reason','—')}")
            send(peer_id, "\n".join(lines), reply_to=reply_ref); continue
        if cmd == "clear":
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            if not args or not args[0].isdigit(): send(peer_id, "⚠ /clear 10", reply_to=reply_ref); continue
            n = min(int(args[0]), 100)
            if n <= 0: send(peer_id, "⚠ N > 0", reply_to=reply_ref); continue
            try:
                hist = api.messages.getHistory(peer_id=peer_id, count=n, rev=1)["items"]
                ids = [str(m["id"]) for m in hist if m["from_id"] != BOT_ID and m.get("id")]
                if not ids: send(peer_id, "ℹ Нечего.", reply_to=reply_ref); continue
                api.messages.delete(message_ids=",".join(ids), delete_for_all=1)
                send(peer_id, f"🧹 {len(ids)}", reply_to=reply_ref)
            except Exception as e: send(peer_id, f"❌ {e}", reply_to=reply_ref)
            continue

        # nick
        if cmd == "nick":
            m = re.search(r"\[id(\d+)\|", text)
            tid = int(m.group(1)) if m else (reply_msg.get("from_id") if reply_msg else None)
            if tid is None: tid = from_id; nn = " ".join(args).strip()
            else:
                pn = [a for a in args if not re.match(r"\[id\d+\|",a) and not re.match(r"@id\d+",a)]
                nn = " ".join(pn).strip()
            if not nn: send(peer_id, "⚠ /nick <ник>", reply_to=reply_ref); continue
            if len(nn) > 32: send(peer_id, "⚠ ≤32.", reply_to=reply_ref); continue
            get_chat(peer_id)["nicknames"][str(tid)] = nn; save_cfg(cfg)
            send(peer_id, f"✅ {nn}", reply_to=reply_ref); continue
        if cmd == "rnick":
            m = re.search(r"\[id(\d+)\|", text)
            tid = int(m.group(1)) if m else (reply_msg.get("from_id") if reply_msg else None)
            if tid is None: tid = from_id
            c = get_chat(peer_id); rem = c["nicknames"].pop(str(tid), None); save_cfg(cfg)
            send(peer_id, "✅ Снят." if rem else "ℹ Нет.", reply_to=reply_ref); continue

        # target
        target = extract_user(text, reply_msg)
        if not target: send(peer_id, "⚠ Укажи.", reply_to=reply_ref); continue
        if target == from_id: send(peer_id, "🤔 Себя нельзя.", reply_to=reply_ref); continue
        if int(target) == int(cfg["global_owner"]) and from_id != int(cfg["global_owner"]):
            send(peer_id, "🌐 Нельзя.", reply_to=reply_ref); continue
        if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue

        c = get_chat(peer_id); cid = chat_id_from_peer(peer_id)

        if cmd == "setowner":
            if from_id != int(cfg["global_owner"]): send(peer_id, "⛔ Global.", reply_to=reply_ref); continue
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
            send(peer_id, "✅ Разбанен." if rem else "ℹ Нет.", reply_to=reply_ref)
        elif cmd == "gban":
            reason = " ".join(args) if args else "—"; k = 0
            for pid in cfg.get("known_peers", []):
                c2 = chat_id_from_peer(pid)
                if not c2: continue
                ok, _ = kick_user(c2, target)
                if ok: k += 1
            for ch in cfg.get("chats",{}).values():
                ch["banned"][str(target)] = {"reason":reason,"by":from_id,"at":int(time.time()),"global":True}
            save_cfg(cfg); send(peer_id, f"🌐 Глобан. Кикнут в {k}.", reply_to=reply_ref)
        elif cmd == "ungban":
            rem = 0
            for ch in cfg.get("chats",{}).values():
                i = ch["banned"].get(str(target))
                if i and i.get("global"): del ch["banned"][str(target)]; rem += 1
            save_cfg(cfg); send(peer_id, f"✅ Снят ({rem})." if rem else "ℹ Нет.", reply_to=reply_ref)
        elif cmd == "kick":
            ok, err = kick_user(cid, target)
            send(peer_id, "👢 Исключён." if ok else f"❌ {err}", reply_to=reply_ref)
        elif cmd == "mute":
            m = cfg["default_mute_minutes"]
            if args and args[0].isdigit():
                m = int(args[0])
                if m <= 0: m = cfg["default_mute_minutes"]
            c["muted"][str(target)] = {"until":time.time()+m*60,"last_dm":time.time()}
            save_cfg(cfg); send(peer_id, f"🔇 {mention(target,peer_id)} {m} мин.", reply_to=reply_ref)
            mute_notify_dm(target, m)
        elif cmd == "unmute":
            rem = c["muted"].pop(str(target), None); save_cfg(cfg)
            if rem:
                send(peer_id, "🔊 Размьючен.", reply_to=reply_ref); send_dm(target, "🔊 Мут снят.")
            else: send(peer_id, "ℹ Нет.", reply_to=reply_ref)
        elif cmd == "warn":
            reason = " ".join(args) if args else "—"
            wr = c["warns"]; wr[str(target)] = wr.get(str(target),0)+1; cnt = wr[str(target)]
            save_cfg(cfg)
            send(peer_id, f"⚠ {mention(target,peer_id)} ({cnt}/{cfg['max_warns']}). {reason}", reply_to=reply_ref)
            if cnt >= cfg["max_warns"]:
                c["muted"][str(target)] = {"until":time.time()+3600,"last_dm":time.time()}
                save_cfg(cfg); send(peer_id, "🔇 Лимит — 60 мин.", reply_to=reply_ref); mute_notify_dm(target, 60)
        elif cmd == "unwarn":
            c["warns"].pop(str(target), None); save_cfg(cfg)
            send(peer_id, "✅ Снято.", reply_to=reply_ref)
        elif cmd in ("addstaff","setrole"):
            if from_id != int(cfg["global_owner"]) and c.get("owner") != from_id:
                send(peer_id, "⛔ Нет прав.", reply_to=reply_ref); continue
            ri = " ".join(args).strip(); rk = find_role_by_input(ri, peer_id)
            if not rk:
                all_roles = dict(cfg["roles"]); all_roles.update(c.get("local_roles", {}))
                avail = ", ".join(v["name"] for v in all_roles.values())
                send(peer_id, f"⚠ Роль «{ri}» не найдена.\nЕсть: {avail}", reply_to=reply_ref); continue
            c["staff"][str(target)] = rk; save_cfg(cfg)
            rname = (c.get("local_roles",{}).get(rk) or cfg["roles"].get(rk,{})).get("name", rk)
            send(peer_id, f"✅ {mention(target,peer_id)} → {rname}", reply_to=reply_ref)
        elif cmd == "removestaff":
            if from_id != int(cfg["global_owner"]) and c.get("owner") != from_id:
                send(peer_id, "⛔ Нет прав.", reply_to=reply_ref); continue
            if str(target) == str(cfg["global_owner"]): send(peer_id, "🌐 Нельзя.", reply_to=reply_ref); continue
            rem = c["staff"].pop(str(target), None); save_cfg(cfg)
            if rem:
                rname = (c.get("local_roles",{}).get(rem) or cfg["roles"].get(rem,{})).get("name", rem)
                send(peer_id, f"❌ Снят с «{rname}»", reply_to=reply_ref)
            else: send(peer_id, "ℹ Без роли.", reply_to=reply_ref)

# ================================================================
if __name__ == "__main__":
    print(f"✅ VK Бот 7.0 запущен (PID={os.getpid()})")
    print(f"   Группа: {GROUP_ID}")
    print("   Жду сообщений...\n")
    try:
        while True:
            try: main()
            except KeyboardInterrupt: print("\n⏹"); break
            except Exception as e:
                print(f"⚠ {e}. Рестарт через 5с..."); time.sleep(5)
    finally:
        try: os.remove(PID_FILE)
        except Exception: pass
