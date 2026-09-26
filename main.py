# -*- coding: utf-8 -*-
"""
VK-бот 6.0 — модерация + экономика + бизнесы + страны + билды + игры + ивенты
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

if not TOKEN:
    print("❌ Не задан VK_TOKEN"); sys.exit(1)

WELCOME_TEXT = """👋 Добро пожаловать, {user}!

📋 Команды:
/help — все команды
/баланс /топ — экономика
/казино /дуэль /рулетка /краш — игры
/buybiz /mybiz — бизнесы
/приз — ежедневная награда
/подписка — VIP + 1 000 000
/ивент — ивенты
/страны — государства мира"""

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
PID_FILE = "/tmp/.bot.pid"
CFG_VERSION = 6
MUTE_DM_INTERVAL = 300
START_BALANCE = 100
PRIZE_MIN = 1000
PRIZE_MAX = 900000
PRIZE_COOLDOWN = 86400
VIP_PRICE_MSGS = 1000000
VIP_DURATION = 30 * 86400
VIP_BONUS = 0.10
ADMIN_ABUSE_TITLE = "👑 Admin Abuser"
ADMIN_ABUSE_MSGS = 50

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
}

# ================================================================
# СТРАНЫ
# ================================================================
COUNTRIES = {
    "россия":        {"name": "🇷🇺 Россия",         "bonus": 5000},
    "сша":           {"name": "🇺🇸 США",            "bonus": 7000},
    "китай":         {"name": "🇨🇳 Китай",          "bonus": 6000},
    "германия":      {"name": "🇩🇪 Германия",       "bonus": 5500},
    "япония":        {"name": "🇯🇵 Япония",         "bonus": 6500},
    "франция":       {"name": "🇫🇷 Франция",        "bonus": 5500},
    "великобритания":{"name": "🇬🇧 Великобритания", "bonus": 6000},
    "италия":        {"name": "🇮🇹 Италия",         "bonus": 5000},
    "испания":       {"name": "🇪🇸 Испания",        "bonus": 5000},
    "канада":        {"name": "🇨🇦 Канада",         "bonus": 5500},
    "украина":       {"name": "🇺🇦 Украина",        "bonus": 5000},
    "казахстан":     {"name": "🇰🇿 Казахстан",      "bonus": 4500},
    "беларусь":      {"name": "🇧🇾 Беларусь",       "bonus": 4500},
    "польша":        {"name": "🇵🇱 Польша",         "bonus": 4500},
    "турция":        {"name": "🇹🇷 Турция",         "bonus": 4500},
    "индия":         {"name": "🇮🇳 Индия",          "bonus": 5000},
    "бразилия":      {"name": "🇧🇷 Бразилия",       "bonus": 5000},
    "мексика":       {"name": "🇲🇽 Мексика",        "bonus": 4500},
    "австралия":     {"name": "🇦🇺 Австралия",      "bonus": 5000},
    "египет":        {"name": "🇪🇬 Египет",         "bonus": 4000},
    "корея":         {"name": "🇰🇷 Корея",          "bonus": 5500},
    "швеция":        {"name": "🇸🇪 Швеция",         "bonus": 5000},
    "швейцария":     {"name": "🇨🇭 Швейцария",      "bonus": 5500},
    "оаэ":           {"name": "🇦🇪 ОАЭ",            "bonus": 8000},
    "саудовская аравия": {"name": "🇸🇦 Саудовская Аравия", "bonus": 8500},
}

# ================================================================
# НАБОРЫ КОМАНД
# ================================================================
PUBLIC_CMDS = [
    "help", "info", "staff", "стата", "stat", "топ", "top",
    "баланс", "balance", "biz", "buybiz", "mybiz", "collect",
    "казино", "casino", "дуэль", "duel",
    "монетка", "coin", "кубик", "dice", "слоты", "slots",
    "краш", "crash", "дартс", "darts", "колесо", "wheel", "рулетка", "roulette",
    "приз", "prize", "подписка", "sub",
    "promo", "промо",
    "страны", "государства", "cmd",
    "offer", "report", "ивент", "event", "role", "build",
]
HELPER_CMDS = PUBLIC_CMDS + ["warn", "promolist", "createpromo", "вайп"]
MODERATOR_CMDS = HELPER_CMDS + ["nick", "rnick", "unwarn",
                                 "mute", "unmute", "clear", "banlist",
                                 "tickets", "adt"]
ADMIN_CMDS = MODERATOR_CMDS + ["kick", "ban", "unban", "gban", "ungban"]
STAFF_CMDS = ADMIN_CMDS + ["loginfo", "builds"]
OWNER_CMDS = STAFF_CMDS + ["addstaff", "removestaff", "setrole", "setowner",
                            "setlog", "unsetlog", "setwarns", "setmutetime",
                            "newrole", "delrole", "createivent",
                            "setpresident", "вайп_все"]
GLOBAL_ONLY = ["объявление", "announce", "рассылка"]

DEFAULT_ROLES = {
    "head": {"name": "Руководитель", "priority": 95, "commands": STAFF_CMDS},
    "deputy_head": {"name": "Заместитель Руководителя", "priority": 90, "commands": STAFF_CMDS},
    "special_admin": {"name": "Специальный Администратор", "priority": 85, "commands": STAFF_CMDS},
    "chief_admin": {"name": "Главный Администратор", "priority": 80, "commands": ADMIN_CMDS},
    "deputy_chief_admin": {"name": "Заместитель Главного Администратора", "priority": 75, "commands": ADMIN_CMDS},
    "chief_watcher": {"name": "Главный Следящий", "priority": 70, "commands": MODERATOR_CMDS},
    "deputy_chief_watcher": {"name": "Заместитель Главного Следящего", "priority": 65, "commands": MODERATOR_CMDS},
    "admin": {"name": "Администратор", "priority": 60, "commands": ADMIN_CMDS},
    "moderator": {"name": "Модератор", "priority": 50, "commands": MODERATOR_CMDS},
    "helper": {"name": "Хелпер", "priority": 20, "commands": HELPER_CMDS},
}

def commands_for_priority(p):
    if p >= 70: return list(STAFF_CMDS)
    if p >= 60: return list(ADMIN_CMDS)
    if p >= 40: return list(MODERATOR_CMDS)
    if p >= 20: return list(HELPER_CMDS)
    return list(PUBLIC_CMDS)

ALL_COMMANDS = set(PUBLIC_CMDS)
for _r in DEFAULT_ROLES.values(): ALL_COMMANDS.update(_r.get("commands", []))
ALL_COMMANDS.update(GLOBAL_ONLY + ["newrole", "delrole", "createivent", "setowner",
                                    "setpresident", "builds", "promolist",
                                    "createpromo", "вайп", "вайп_все"])

def suggest_command(cmd):
    m = difflib.get_close_matches(cmd, list(ALL_COMMANDS), n=1, cutoff=0.55)
    return m[0] if m else None

# ================================================================
# КОНФИГ
# ================================================================
DEFAULT_CHAT = {
    "owner": None, "staff": {}, "banned": {}, "muted": {}, "warns": {},
    "nicknames": {}, "welcome": True,
    "user_stats": {}, "balance": {},
    "businesses": {}, "subs": {}, "last_prize": {}, "promos_used": {},
    "promos": {}, "local_roles": {}, "custom_cmds": {},
    "build_name": None,
}
DEFAULT_CFG = {
    "version": CFG_VERSION, "global_owner": GLOBAL_OWNER_ID,
    "default_mute_minutes": 30, "max_warns": 3, "log_peer_id": 0,
    "roles": DEFAULT_ROLES, "chats": {}, "known_peers": [],
    "tickets": {}, "next_ticket_id": 1, "custom_events": {},
    "countries": {}, "builds": {}, "global_promos": {},
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
    d.setdefault("countries", {}); d.setdefault("builds", {})
    d.setdefault("global_promos", {})
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
        except Exception as e: print(f"[cfg create] {e}")
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
except VkApiError as e: print(f"   ❌ Long Poll: {e}"); sys.exit(1)
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
    kw = {"peer_id": peer_id, "message": text,
          "random_id": int(time.time() * 1000) + random.randint(0, 999),
          "disable_mentions": 0}
    if reply_to:
        try:
            r = int(reply_to)
            if r > 0: kw["reply_to"] = r
        except Exception: pass
    try: api.messages.send(**kw)
    except Exception as e:
        print(f"[send error] {e}")
        if "reply_to" in kw:
            del kw["reply_to"]
            try: api.messages.send(**kw)
            except Exception as e2: print(f"[send2] {e2}")

def send_dm(uid, text):
    try:
        api.messages.send(peer_id=uid, message=text,
                          random_id=int(time.time() * 1000) + random.randint(0, 999),
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
                          random_id=int(time.time() * 1000) + random.randint(0, 999))
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
    s = stats.get(key) or {"msg_count": 0, "last_text": "", "last_at": 0}
    s["msg_count"] += 1
    if text: s["last_text"] = text[:120]
    s["last_at"] = int(time.time())
    stats[key] = s
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
    bal[uid] = bal.get(uid, START_BALANCE) + amount
    if bal[uid] < 0: bal[uid] = 0
    save_cfg(cfg); return bal[uid]

def is_vip(peer_id, uid):
    c = get_chat(peer_id)
    if not c: return False
    subs = c.get("subs", {}); until = subs.get(str(uid), 0)
    return until > time.time()

def vip_until(peer_id, uid):
    c = get_chat(peer_id)
    if not c: return 0
    return c.get("subs", {}).get(str(uid), 0)

def vip_multiplier(peer_id, uid):
    return 1 + VIP_BONUS if is_vip(peer_id, uid) else 1.0

def get_role_key(uid, peer_id):
    if int(uid) == int(cfg["global_owner"]): return "global"
    if not is_chat(peer_id): return None
    c = get_chat(peer_id)
    if c.get("owner") == uid: return "owner"
    return c.get("staff", {}).get(str(uid))

def find_role(role_key, peer_id):
    if not role_key: return None
    if is_chat(peer_id):
        c = get_chat(peer_id)
        r = c.get("local_roles", {}).get(role_key)
        if r: return r
    return cfg["roles"].get(role_key)

def role_display(uid, peer_id):
    k = get_role_key(uid, peer_id)
    if k == "global": return "🌐 Главный владелец"
    if k == "owner": return "👑 Владелец беседы"
    r = find_role(k, peer_id)
    if r: return r["name"]
    return "нет"

def can(uid, cmd, peer_id):
    if int(uid) == int(cfg["global_owner"]): return True
    if cmd in PUBLIC_CMDS: return True
    if not is_chat(peer_id): return False
    c = get_chat(peer_id)
    if c.get("owner") == uid:
        return cmd not in ("newrole", "delrole", "createivent", "setpresident") and cmd not in GLOBAL_ONLY
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
    try:
        api.messages.removeChatUser(chat_id=cid, user_id=uid); return True, None
    except Exception as e: return False, str(e)

def delete_msg(mid, cmid=None, peer_id=None):
    if cmid and peer_id:
        try: api.messages.delete(conversation_message_ids=cmid, peer_id=peer_id, delete_for_all=1); return True
        except Exception as e: print(f"[del cmid] {e}")
    if mid and mid > 0:
        try: api.messages.delete(message_ids=mid, delete_for_all=1); return True
        except Exception as e: print(f"[del id] {e}")
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

def fmt_num(n):
    return f"{int(n):,}".replace(",", " ")

def mute_notify_dm(uid, minutes): send_dm(uid, f"🔇 Мут на {minutes} мин.")
def mute_warn_dm(uid, rem): send_dm(uid, f"🔇 В муте. Осталось: {fmt_time(rem)}")
def mute_expired_dm(uid): send_dm(uid, "🔊 Ваш мут снят.")

def get_mute_until(info):
    if isinstance(info, dict): return info.get("until", 0)
    return info or 0

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
# СПРАВКА
# ================================================================
def build_help():
    return f"""📋 Команды бота:

🎮 ЭКОНОМИКА
/баланс [@user] — баланс
/топ [баланс|сообщения|бизнес] — топы
/приз — до {fmt_num(PRIZE_MAX)} монет раз в 24ч
/подписка — VIP + {fmt_num(VIP_PRICE_MSGS)}

🎲 ИГРЫ
/казино <ставка> — рулетка ×2
/дуэль @user <ставка> — дуэль
/монетка <ставка> <орёл|решка>
/кубик <ставка> <1-6>
/слоты <ставка>
/краш <ставка> <множитель 1.1-10>
/дартс <ставка>
/колесо <ставка> <цвет|число>
/рулетка <ставка> <число 0-36>

💼 БИЗНЕСЫ
/buybiz <название> — купить
/mybiz — мои бизнесы
/collect — собрать доход
Список: {", ".join(BUSINESSES.keys())}

🌍 СТРАНЫ
/страны / /государства — список
/setpresident <страна> @user — Global

🎟️ ПРОМОКОДЫ
/promo <код> — активировать
/createpromo <код> <награда> — создать (владелец беседы)
/promolist — список (владелец)

🏗️ БИЛДЫ (сетки бесед)
/build <название> — привязать беседу
/builds — список всех сеток (Global)

👥 ОБЩИЕ
/help /info /стата /staff /role /cmd
/offer /report — тикет
/ивент — список /ивент <название>
/ивент мафия — игра

🛡️ МОДЕРАЦИЯ
/warn /unwarn /mute /unmute /nick /rnick
/kick /ban /unban /gban /ungban
/clear N /banlist
/tickets /adt <№> <ответ>

👑 ВЛАДЕЛЕЦ БЕСЕДЫ
/addstaff /removestaff /setrole /setowner
/newrole <название> <0-100>
/delrole /setwarns /setmutetime
/setlog /unsetlog /loginfo
/вайп — очистить балансы беседы

🌐 GLOBAL
/объявление <текст>
/createivent <название> | <награда> | <требование>
/setpresident <страна> @user
/вайп_все — глобальный вайп

💰 Монет: {START_BALANCE} при старте
🎁 VIP +{int(VIP_BONUS*100)}% к прибыли
"""

# ================================================================
# ИВЕНТЫ
# ================================================================
EVENTS_LIST = {
    "рулетка": "🎰 Рулетка", "дуэль": "⚔️ Дуэль", "лотерея": "🎟️ Лотерея",
    "хэллоуин": "🎃 Хэллоуин", "новыйгод": "🎄 Новый год",
    "мафия": "🎭 Мафия (мин. 4)",
    "admin_abuse": "👑 Admin Abuse", "гонка": "🏎️ Гонка",
    "золото": "💰 Золото", "клад": "🗝 Клад",
    "блэкаут": "🌑 Блэкаут", "феникс": "🔥 Феникс",
}
EVENT_TITLES = ["🏆 Победитель", "⚔️ Воин", "🎟️ Счастливчик", "🎄 Снегурочка",
                "🌟 Звезда", "👑 Король", "🎩 Магистр", "🍀 Удачливый",
                "🔥 Горячая штучка", "🐉 Дракон", "🦊 Хитрец", "🌸 Красотка",
                "🏎️ Гонщик", "🕵️ Детектив", "🧙 Маг", "🐺 Вожак"]

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
        c["muted"][str(w)] = {"until": time.time()+300, "last_dm": 0}; save_cfg(cfg)
        send(peer_id, f"🎰 {mention(w, peer_id)} — 🔇 5 мин."); mute_notify_dm(w,5)
    elif eff == "warn":
        wr = c["warns"]; wr[str(w)] = wr.get(str(w),0)+1; save_cfg(cfg)
        send(peer_id, f"🎰 {mention(w, peer_id)} — ⚠️ ({wr[str(w)]}/{cfg['max_warns']}).")
    elif eff == "money":
        bonus = int(100 * vip_multiplier(peer_id, w)); add_balance(peer_id, w, bonus)
        send(peer_id, f"🎰 {mention(w, peer_id)} — 💰 +{bonus} монет!")
    else: send(peer_id, f"🎰 {mention(w, peer_id)} — ничего 😅")

def ev_duel(peer_id):
    c = get_chat(peer_id); users = get_chat_members(peer_id)
    if len(users) < 2: send(peer_id, "❌ Нужно ≥ 2."); return
    a, b = random.sample(users, 2); w = random.choice([a, b]); t = random.choice(EVENT_TITLES)
    c["nicknames"][str(w)] = t; save_cfg(cfg)
    send(peer_id, f"⚔️ {mention(a, peer_id)} vs {mention(b, peer_id)}\n🏆 {mention(w, peer_id)} → {t}")

def ev_lottery(peer_id):
    c = get_chat(peer_id); users = get_chat_members(peer_id)
    if len(users) < 3: send(peer_id, "❌ Нужно ≥ 3."); return
    lines = ["🎟️ Лотерея:"]
    for w in random.sample(users, 3):
        t = random.choice(EVENT_TITLES); c["nicknames"][str(w)] = t
        lines.append(f"— {mention(w, peer_id)} → {t}")
    save_cfg(cfg); send(peer_id, "\n".join(lines))

def ev_halloween(peer_id):
    c = get_chat(peer_id); w = _pick(peer_id)
    if not w: send(peer_id, "❌ Нет участников."); return
    c["muted"][str(w)] = {"until": time.time()+300, "last_dm": 0}; save_cfg(cfg)
    send(peer_id, f"🎃 {mention(w, peer_id)} → 🔇 5 мин."); mute_notify_dm(w,5)

def ev_newyear(peer_id):
    c = get_chat(peer_id); un = 0
    for k in list(c["muted"].keys()): del c["muted"][k]; un += 1
    w = _pick(peer_id)
    if w:
        c["nicknames"][str(w)] = "🎄 Снегурочка"; save_cfg(cfg)
        send(peer_id, f"🎄 Снято мьютов: {un}\n{mention(w, peer_id)} → 🎄 Снегурочка")
    else: save_cfg(cfg); send(peer_id, f"🎄 Снято мьютов: {un}")

def ev_admin_abuse(peer_id):
    c = get_chat(peer_id); w = _pick(peer_id)
    if not w: send(peer_id, "❌ Нет участников."); return
    c["nicknames"][str(w)] = ADMIN_ABUSE_TITLE
    stats = c.setdefault("user_stats", {}); key = str(w)
    s = stats.get(key) or {"msg_count": 0, "last_text": "", "last_at": 0}
    s["msg_count"] += ADMIN_ABUSE_MSGS; stats[key] = s; save_cfg(cfg)
    send(peer_id, f"👑 ADMIN ABUSE!\n{mention(w, peer_id)} → {ADMIN_ABUSE_TITLE}\n+{ADMIN_ABUSE_MSGS} сообщений!")

def ev_race(peer_id):
    c = get_chat(peer_id); w = _pick(peer_id)
    if not w: send(peer_id, "❌ Нет участников."); return
    c["nicknames"][str(w)] = "🏎️ Гонщик"; save_cfg(cfg)
    send(peer_id, f"🏎️ {mention(w, peer_id)} — 🏎️ Гонщик!")

def ev_gold(peer_id):
    w = _pick(peer_id)
    if not w: send(peer_id, "❌ Нет участников."); return
    bonus = int(500 * vip_multiplier(peer_id, w)); nb = add_balance(peer_id, w, bonus)
    send(peer_id, f"💰 {mention(w, peer_id)} — +{bonus}!\nБаланс: {fmt_num(nb)}")

def ev_treasure(peer_id):
    w = _pick(peer_id)
    if not w: send(peer_id, "❌ Нет участников."); return
    bonus = int(200 * vip_multiplier(peer_id, w)); nb = add_balance(peer_id, w, bonus)
    send(peer_id, f"🗝 {mention(w, peer_id)} — +{bonus}!\nБаланс: {fmt_num(nb)}")

def ev_blackout(peer_id):
    c = get_chat(peer_id); users = get_chat_members(peer_id)
    if not users: send(peer_id, "❌ Нет участников."); return
    until = time.time() + 120
    for u in users: c["muted"][str(u)] = {"until": until, "last_dm": 0}
    save_cfg(cfg); send(peer_id, f"🌑 Блэкаут! Все {len(users)} в муте на 2 мин.")

def ev_phoenix(peer_id):
    c = get_chat(peer_id); un = 0
    for k in list(c["muted"].keys()): del c["muted"][k]; un += 1
    users = get_chat_members(peer_id)
    if users:
        for w in random.sample(users, min(3, len(users))): c["nicknames"][str(w)] = "🔥 Феникс"
        save_cfg(cfg)
        send(peer_id, f"🔥 Снято мьютов: {un}\nТитул 🔥 Феникс: " +
             ", ".join(mention(w, peer_id) for w in random.sample(users, min(3, len(users)))))
    else: save_cfg(cfg); send(peer_id, f"🔥 Снято мьютов: {un}")

def ev_custom(peer_id, name):
    ev = cfg.get("custom_events", {}).get(name.lower())
    if not ev: return False
    send(peer_id, f"🎉 {ev['name']}\n🏆 {ev['reward']}\n📋 {ev['requirement']}")
    return True

EVENT_HANDLERS = {
    "рулетка": ev_roulette, "дуэль": ev_duel, "лотерея": ev_lottery,
    "хэллоуин": ev_halloween, "новыйгод": ev_newyear,
    "admin_abuse": ev_admin_abuse, "гонка": ev_race,
    "золото": ev_gold, "клад": ev_treasure,
    "блэкаут": ev_blackout, "феникс": ev_phoenix,
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
MAFIA_MIN_PLAYERS = 4
MAFIA_LOBBY_SECONDS = 60
MAFIA_DAY_DISCUSSION = 120
MAFIA_VOTE_SECONDS = 60
MAFIA_JOIN_WORDS = {"вступить","я","+","играю","в игре","мафия","го","за"}
ROLE_MAFIA="🔫 Мафия"; ROLE_DOCTOR="💉 Доктор"; ROLE_POLICE="👮 Полицейский"
ROLE_WAITER="🍽️ Официант"; ROLE_CIVILIAN="👤 Мирный"
NIGHT_STEPS=["mafia","doctor","police","waiter"]
GAMES = {}; GAMES_LOCK = threading.Lock()

def mafia_start(peer_id, host_id):
    with GAMES_LOCK:
        if peer_id in GAMES: send(peer_id, "⚠️ Игра уже идёт."); return
        GAMES[peer_id] = {"phase":"lobby","lobby_players":[host_id],"players":{},
            "alive":set(),"host":host_id,"lobby_deadline":time.time()+MAFIA_LOBBY_SECONDS,
            "night_step_idx":0,"night_step":None,"night_actions":{},
            "day_deadline":0,"vote_deadline":0,"votes":{},"waiter_block":None,
            "round":0,"_alive_order":[]}
    send(peer_id, f"🎭 МАФИЯ\nВступить: напишите «вступить»\nМин: {MAFIA_MIN_PLAYERS} | Сбор: {MAFIA_LOBBY_SECONDS}с\n\n1. {get_vk_name(host_id)}")

def mafia_join(peer_id, uid):
    g = GAMES.get(peer_id)
    if not g or g["phase"] != "lobby" or uid in g["lobby_players"]: return
    g["lobby_players"].append(uid)
    lines = [f"✅ {get_vk_name(uid)} вступил ({len(g['lobby_players'])}):"]
    for i, u in enumerate(g["lobby_players"], 1): lines.append(f"{i}. {get_vk_name(u)}")
    send(peer_id, "\n".join(lines))

def mafia_start_game(peer_id):
    g = GAMES.get(peer_id)
    if not g or g["phase"] != "lobby": return
    players = list(g["lobby_players"])
    if len(players) < MAFIA_MIN_PLAYERS:
        send(peer_id, f"❌ Мало ({len(players)}/{MAFIA_MIN_PLAYERS})"); GAMES.pop(peer_id, None); return
    n = len(players); mc = 2 if n >= 7 else 1
    pool = [ROLE_MAFIA]*mc + [ROLE_DOCTOR, ROLE_POLICE]
    if n >= 5: pool.append(ROLE_WAITER)
    while len(pool) < n: pool.append(ROLE_CIVILIAN)
    random.shuffle(pool); roles = dict(zip(players, pool))
    g["players"] = roles; g["alive"] = set(players); g["round"] = 0; g["phase"] = "night"
    names = "\n".join(f"— {get_vk_name(u)}" for u in players)
    for uid, role in roles.items(): send_dm(uid, f"🎭 Роль: {role}\n\nИграют:\n{names}")
    send(peer_id, f"🎭 Игра началась! {n} игроков.")
    mafia_start_night(peer_id)

def mafia_start_night(peer_id):
    g = GAMES.get(peer_id)
    if not g: return
    if not g["alive"]: GAMES.pop(peer_id, None); return
    g["phase"]="night"; g["round"]+=1
    g["night_step_idx"]=0; g["night_step"]=None; g["night_actions"]={}
    g["waiter_block"]=None; g["votes"]={}
    send(peer_id, f"🌃 Раунд {g['round']}. Город засыпает..."); mafia_next_step(peer_id)

def _alive_list(g):
    alive = sorted(g["alive"]); g["_alive_order"] = alive
    return "\n".join(f"{i+1}. {get_vk_name(u)}" for i, u in enumerate(alive))

def mafia_next_step(peer_id):
    g = GAMES.get(peer_id)
    if not g or g["phase"] != "night": return
    roles_present = set(g["players"][u] for u in g["alive"])
    while g["night_step_idx"] < len(NIGHT_STEPS):
        step = NIGHT_STEPS[g["night_step_idx"]]; g["night_step_idx"] += 1
        rn = {"mafia":ROLE_MAFIA,"doctor":ROLE_DOCTOR,"police":ROLE_POLICE,"waiter":ROLE_WAITER}[step]
        if rn in roles_present:
            g["night_step"] = step; mafia_announce(peer_id, step); return
    mafia_resolve(peer_id)

def mafia_announce(peer_id, step):
    g = GAMES.get(peer_id)
    if not g: return
    lst = _alive_list(g)
    if step == "mafia":
        send(peer_id, "🌃 Просыпается 🔫 Мафия...")
        for u, r in g["players"].items():
            if r == ROLE_MAFIA and u in g["alive"]:
                send_dm(u, f"🔫 Кого убить:\n\n{lst}\n\nНомер.")
    elif step == "doctor":
        send(peer_id, "💉 Просыпается Доктор...")
        for u, r in g["players"].items():
            if r == ROLE_DOCTOR and u in g["alive"]:
                send_dm(u, f"💉 Кого спасти:\n\n{lst}\n\nНомер.")
    elif step == "police":
        send(peer_id, "👮 Просыпается Полицейский...")
        for u, r in g["players"].items():
            if r == ROLE_POLICE and u in g["alive"]:
                send_dm(u, f"👮 Кого проверить:\n\n{lst}\n\nНомер.")
    elif step == "waiter":
        send(peer_id, "🍽️ Просыпается Официант...")
        for u, r in g["players"].items():
            if r == ROLE_WAITER and u in g["alive"]:
                send_dm(u, f"🍽️ Кого лишить голоса:\n\n{lst}\n\nНомер.")

def mafia_parse(text, g):
    t = text.strip()
    m = re.search(r"\[id(\d+)\|", t)
    if m and int(m.group(1)) in g["alive"]: return int(m.group(1))
    m = re.search(r"@id(\d+)", t)
    if m and int(m.group(1)) in g["alive"]: return int(m.group(1))
    m = re.match(r"^(\d+)$", t)
    if m:
        n = int(m.group(1)); order = g.get("_alive_order") or sorted(g["alive"])
        if 1 <= n <= len(order): return order[n-1]
    return None

def mafia_night_dm(uid, text, peer_id):
    g = GAMES.get(peer_id)
    if not g or g["phase"] != "night": return False
    step = g["night_step"]
    if not step: return False
    need = {"mafia":ROLE_MAFIA,"doctor":ROLE_DOCTOR,"police":ROLE_POLICE,"waiter":ROLE_WAITER}[step]
    if g["players"].get(uid) != need or uid not in g["alive"]: return False
    if step in g["night_actions"]: send_dm(uid, "Уже выбрали."); return True
    t = mafia_parse(text, g)
    if not t: send_dm(uid, "⚠️ Напишите номер."); return True
    g["night_actions"][step] = t; send_dm(uid, f"✅ {get_vk_name(t)}")
    if step == "police":
        if g["players"].get(t) == ROLE_MAFIA: send_dm(uid, f"✅ {get_vk_name(t)} — мафия!")
        else: send_dm(uid, f"❌ {get_vk_name(t)} — не мафия.")
    ann = {"mafia":"🔫 Мафия сделала выбор.","doctor":"💉 Доктор сделал выбор.",
           "police":"👮 Полицейский сделал выбор.","waiter":"🍽️ Официант сделал выбор."}
    send(peer_id, ann.get(step, "")); g["night_step"] = None; mafia_next_step(peer_id); return True

def mafia_resolve(peer_id):
    g = GAMES.get(peer_id)
    if not g: return
    send(peer_id, "🌅 Город просыпается...")
    mt = g["night_actions"].get("mafia"); dt = g["night_actions"].get("doctor")
    if mt:
        if dt == mt: send(peer_id, "☀️ Доктор спас жертву!")
        else:
            g["alive"].discard(mt)
            send(peer_id, f"💀 Убит {get_vk_name(mt)}. Роль: {g['players'][mt]}")
    else: send(peer_id, "☀️ Никто не погиб.")
    g["waiter_block"] = g["night_actions"].get("waiter")
    if mafia_check_win(peer_id): return
    g["phase"]="day"; g["day_deadline"]=time.time()+MAFIA_DAY_DISCUSSION
    send(peer_id, f"🌞 День! {MAFIA_DAY_DISCUSSION}с на обсуждение.")

def mafia_check_win(peer_id):
    g = GAMES.get(peer_id)
    if not g: return True
    if not g["alive"]: mafia_end(peer_id, "🎭 Ничья."); return True
    am = sum(1 for u in g["alive"] if g["players"][u] == ROLE_MAFIA)
    ac = len(g["alive"]) - am
    if am == 0: mafia_end(peer_id, "🎉 Город победил!"); return True
    if am >= ac: mafia_end(peer_id, "🔫 Мафия победила!"); return True
    return False

def mafia_start_vote(peer_id):
    g = GAMES.get(peer_id)
    if not g or g["phase"] != "day": return
    g["phase"]="voting"; g["votes"]={}; g["vote_deadline"]=time.time()+MAFIA_VOTE_SECONDS
    send(peer_id, "🗳️ Голосование! Списки в ЛС.")
    alive = sorted(g["alive"]); g["_alive_order"] = alive
    names = "\n".join(f"{i+1}. {get_vk_name(u)}" for i, u in enumerate(alive))
    for u in alive:
        note = "\n⚠️ Без голоса." if g.get("waiter_block")==u else ""
        send_dm(u, f"🗳️ Голосуйте:\n\n{names}\n\nНомер или 'пропуск'.{note}")

def mafia_vote_dm(uid, text, peer_id):
    g = GAMES.get(peer_id)
    if not g or g["phase"] != "voting" or uid not in g["alive"]: return False
    if uid in g["votes"]: send_dm(uid, "Уже голосовали."); return True
    t = text.strip().lower()
    if t in ("пропуск","skip","пас","0"):
        g["votes"][uid] = "skip"; send_dm(uid, "✅ Пропуск."); return True
    target = mafia_parse(text, g)
    if not target: send_dm(uid, "⚠️ Номер или 'пропуск'."); return True
    if target == uid: send_dm(uid, "⚠️ Не за себя."); return True
    g["votes"][uid] = target; send_dm(uid, f"✅ За {get_vk_name(target)}."); return True

def mafia_tally(peer_id):
    g = GAMES.get(peer_id)
    if not g: return
    g["phase"] = "ended"; counts = {}; skip = 0
    for voter, tgt in g["votes"].items():
        if voter == g.get("waiter_block"): continue
        if tgt == "skip": skip += 1
        else: counts[tgt] = counts.get(tgt, 0) + 1
    if not counts: send(peer_id, f"🗳️ Все воздержались."); mafia_start_night(peer_id); return
    mx = max(counts.values()); top = [u for u, c in counts.items() if c == mx]
    if len(top) > 1:
        send(peer_id, f"🗳️ Ничья."); mafia_start_night(peer_id); return
    victim = top[0]; role = g["players"][victim]; g["alive"].discard(victim)
    if role == ROLE_MAFIA:
        send(peer_id, f"🎉 {get_vk_name(victim)} — мафия! Город победил!")
        mafia_end(peer_id, None)
    else:
        send(peer_id, f"❌ {get_vk_name(victim)} — {role}.")
        if mafia_check_win(peer_id): return
        mafia_start_night(peer_id)

def mafia_end(peer_id, msg):
    g = GAMES.pop(peer_id, None)
    if msg: send(peer_id, msg)
    if g:
        lines = ["🎭 Все роли:"]
        for u, r in g["players"].items():
            lines.append(f"— {get_vk_name(u)}: {r} ({'жив' if u in g['alive'] else 'мёртв'})")
        send(peer_id, "\n".join(lines))

def mafia_any_dm(uid, text):
    with GAMES_LOCK: games = list(GAMES.items())
    for peer_id, g in games:
        if uid not in g.get("players", {}): continue
        if g["phase"] == "night" and mafia_night_dm(uid, text, peer_id): return True
        elif g["phase"] == "voting" and mafia_vote_dm(uid, text, peer_id): return True
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
        info = ch.get("banned", {}).get(str(uid))
        if info:
            bans_local += 1
            if info.get("global"): bans_global = True
    warns = 0; chat_mute = False; nick = None
    if c:
        warns = c.get("warns", {}).get(str(uid), 0)
        mu_until = get_mute_until(c.get("muted", {}).get(str(uid)))
        chat_mute = bool(mu_until and mu_until > time.time())
        nick = c.get("nicknames", {}).get(str(uid))
    s = (c or {}).get("user_stats", {}).get(str(uid), {})
    msg_count = s.get("msg_count", 0); last_text = s.get("last_text") or "—"
    last_at = s.get("last_at", 0); bal = get_balance(peer_id, uid) if c else 0
    vip = "✅ VIP" if is_vip(peer_id, uid) else "Нет"
    biz_count = len(c.get("businesses", {}).get(str(uid), {})) if c else 0
    return "\n".join([
        "📊 Информация:",
        f"• {mention(uid, peer_id)}",
        f"• Роль: {role}",
        f"• VIP: {vip}",
        f"• Блокировок: {bans_local}",
        f"• Глоб блок: {'Да' if bans_global else 'Нет'}",
        f"• Предупреждения: {warns}/{cfg['max_warns']}",
        f"• Мут: {'Да' if chat_mute else 'Нет'}",
        f"• Ник: {nick or 'Нет'}",
        f"• Сообщений: {msg_count}",
        f"• Последнее: {last_text}",
        f"• Когда: {fmt_dt(last_at)}",
        f"• Баланс: {fmt_num(bal)} 💰",
        f"• Бизнесов: {biz_count}",
    ])

def user_info_text(uid, peer_id):
    role = role_display(uid, peer_id)
    lines = [f"ℹ️ {mention(uid, peer_id)}:", f"• Роль: {role}"]
    c = get_chat(peer_id) if is_chat(peer_id) else None
    if c:
        lines.append(f"• Ник: {c.get('nicknames',{}).get(str(uid), '—')}")
        mu_until = get_mute_until(c.get("muted", {}).get(str(uid)))
        lines.append(f"• 🔇 Мут: {fmt_time(mu_until-time.time())}" if mu_until and mu_until > time.time() else "• 🔇 Мут: нет")
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
    uids_fetch = [cfg["global_owner"]]
    if c:
        if c.get("owner"): uids_fetch.append(c["owner"])
        uids_fetch += [int(u) for u in c.get("staff", {}).keys()]
    prefetch_names(uids_fetch)
    lines = ["👮 Состав администрации:", "",
             "🌐 Главный владелец:", f"— {mention(cfg['global_owner'], peer_id)}", "",
             "👑 Владелец беседы:"]
    lines.append(f"— {mention(c['owner'], peer_id)}" if c and c.get("owner") else "— (не назначен)")
    lines.append("")
    all_roles = dict(cfg["roles"])
    if c: all_roles.update(c.get("local_roles", {}))
    for key, role in sorted(all_roles.items(), key=lambda x: -x[1].get("priority", 0)):
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
def create_ticket(ttype, uid, peer_id, text):
    tid = cfg.get("next_ticket_id", 1)
    cfg["tickets"][str(tid)] = {"type":ttype,"from":uid,"peer_id":peer_id,
        "text":text,"status":"open","answer":"","answered_by":0,
        "answered_at":0,"created_at":int(time.time())}
    cfg["next_ticket_id"] = tid + 1; save_cfg(cfg); return tid

def tickets_list_text():
    t = cfg.get("tickets", {})
    if not t: return "📭 Тикетов нет."
    lines = ["🎫 Тикеты:", ""]; n = 0
    for tid, info in sorted(t.items(), key=lambda x: int(x[0])):
        if info.get("status") != "open": continue
        emoji = "💡" if info.get("type") == "offer" else "❓"
        lines.append(f"#{tid} {emoji} от {mention(info['from'])} — {fmt_dt(info.get('created_at',0))}\n   {info['text'][:120]}")
        n += 1
    return "\n".join(lines) if n else "📭 Открытых тикетов нет."

def answer_ticket(tid, admin_id, answer_text):
    info = cfg.get("tickets", {}).get(str(tid))
    if not info: return False, "Тикет не найден."
    if info.get("status") == "answered": return False, "Уже отвечено."
    info["status"]="answered"; info["answer"]=answer_text
    info["answered_by"]=admin_id; info["answered_at"]=int(time.time()); save_cfg(cfg)
    send_dm(info["from"], f"✅ Ответ #{tid}:\n\n❓ {info['text'][:200]}\n\n✅ {answer_text}")
    try:
        send(info["peer_id"], f"🎫 Ответ #{tid}:\n❓ {info['text'][:200]}\n✅ {answer_text}")
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
    send(peer_id, WELCOME_TEXT.format(user=u))

# ================================================================
# ИГРОВЫЕ КОМАНДЫ
# ================================================================
def _bet_parse(args, bal):
    """Возвращает (bet, remaining_args) или (None, error_msg)."""
    for i, a in enumerate(args):
        if a.isdigit() and int(a) > 0:
            bet = int(a)
            if bet > bal: return None, f"❌ У вас только {fmt_num(bal)} 💰"
            return bet, args[:i] + args[i+1:]
    return None, "⚠ Укажите ставку (число > 0)"

def game_coin(peer_id, uid, args):
    bal = get_balance(peer_id, uid)
    bet, rest = _bet_parse(args, bal)
    if bet is None: send(peer_id, rest); return
    choice = (rest[0].lower() if rest else "")
    if choice not in ("орёл","орел","решка"):
        send(peer_id, "⚠ /монетка <ставка> <орёл|решка>"); return
    res = random.choice(["орёл","решка"])
    if res == choice or (res == "орёл" and choice == "орел"):
        bonus = int(bet * vip_multiplier(peer_id, uid))
        nb = add_balance(peer_id, uid, bonus)
        send(peer_id, f"🪙 Выпало: {res}\n🎉 +{fmt_num(bonus)}!\nБаланс: {fmt_num(nb)}")
    else:
        nb = add_balance(peer_id, uid, -bet)
        send(peer_id, f"🪙 Выпало: {res}\n💀 -{fmt_num(bet)}\nБаланс: {fmt_num(nb)}")

def game_dice(peer_id, uid, args):
    bal = get_balance(peer_id, uid)
    bet, rest = _bet_parse(args, bal)
    if bet is None: send(peer_id, rest); return
    if not rest or not rest[0].isdigit() or not 1 <= int(rest[0]) <= 6:
        send(peer_id, "⚠ /кубик <ставка> <1-6>"); return
    choice = int(rest[0]); res = random.randint(1, 6)
    if res == choice:
        bonus = int(bet * 5 * vip_multiplier(peer_id, uid))
        nb = add_balance(peer_id, uid, bonus)
        send(peer_id, f"🎲 Выпало: {res}\n🎉 x5! +{fmt_num(bonus)}!\nБаланс: {fmt_num(nb)}")
    else:
        nb = add_balance(peer_id, uid, -bet)
        send(peer_id, f"🎲 Выпало: {res}\n💀 -{fmt_num(bet)}\nБаланс: {fmt_num(nb)}")

def game_slots(peer_id, uid, args):
    bal = get_balance(peer_id, uid)
    bet, _ = _bet_parse(args, bal)
    if bet is None: send(peer_id, _); return
    icons = ["🍒","🍋","💎","7️⃣","⭐","🍀"]
    s = [random.choice(icons) for _ in range(3)]
    line = " | ".join(s)
    if s[0] == s[1] == s[2]:
        mult = {"7️⃣": 10, "💎": 7, "⭐": 5, "🍀": 4}.get(s[0], 3)
        bonus = int(bet * mult * vip_multiplier(peer_id, uid))
        nb = add_balance(peer_id, uid, bonus)
        send(peer_id, f"🎰 {line}\n🎉 x{mult}! +{fmt_num(bonus)}!\nБаланс: {fmt_num(nb)}")
    elif s[0] == s[1] or s[1] == s[2] or s[0] == s[2]:
        bonus = int(bet * 1.5 * vip_multiplier(peer_id, uid))
        nb = add_balance(peer_id, uid, bonus)
        send(peer_id, f"🎰 {line}\n✨ 2 совпало! +{fmt_num(bonus)}\nБаланс: {fmt_num(nb)}")
    else:
        nb = add_balance(peer_id, uid, -bet)
        send(peer_id, f"🎰 {line}\n💀 -{fmt_num(bet)}\nБаланс: {fmt_num(nb)}")

def game_crash(peer_id, uid, args):
    bal = get_balance(peer_id, uid)
    bet, rest = _bet_parse(args, bal)
    if bet is None: send(peer_id, rest); return
    if not rest:
        send(peer_id, "⚠ /краш <ставка> <множитель 1.1-10>"); return
    try: target = float(rest[0].replace(",", "."))
    except Exception: send(peer_id, "⚠ Множитель числом."); return
    if not 1.1 <= target <= 10: send(peer_id, "⚠ Множитель 1.1-10"); return
    crash_point = round(random.uniform(1.0, 12.0), 2)
    if target <= crash_point:
        win = int(bet * (target - 1) * vip_multiplier(peer_id, uid))
        nb = add_balance(peer_id, uid, win)
        send(peer_id, f"🚀 Краш: {crash_point}x (цель {target}x)\n🎉 +{fmt_num(win)}!\nБаланс: {fmt_num(nb)}")
    else:
        nb = add_balance(peer_id, uid, -bet)
        send(peer_id, f"🚀 Краш: {crash_point}x (цель {target}x)\n💀 -{fmt_num(bet)}\nБаланс: {fmt_num(nb)}")

def game_darts(peer_id, uid, args):
    bal = get_balance(peer_id, uid)
    bet, _ = _bet_parse(args, bal)
    if bet is None: send(peer_id, _); return
    score = random.randint(0, 100)
    if score >= 90:
        mult = 5; emoji = "🎯 В яблочко!"
    elif score >= 70: mult = 3; emoji = "🎯 Отлично!"
    elif score >= 50: mult = 2; emoji = "🎯 Хорошо!"
    elif score >= 30: mult = 1; emoji = "🎯 Мимо яблочка"
    else: mult = 0; emoji = "🎯 Мимо!"
    if mult:
        win = int(bet * mult * vip_multiplier(peer_id, uid))
        nb = add_balance(peer_id, uid, win)
        send(peer_id, f"🎯 {score}/100 {emoji}\n💰 +{fmt_num(win)}\nБаланс: {fmt_num(nb)}")
    else:
        nb = add_balance(peer_id, uid, -bet)
        send(peer_id, f"🎯 {score}/100 {emoji}\n💀 -{fmt_num(bet)}\nБаланс: {fmt_num(nb)}")

def game_wheel(peer_id, uid, args):
    bal = get_balance(peer_id, uid)
    bet, rest = _bet_parse(args, bal)
    if bet is None: send(peer_id, rest); return
    if not rest: send(peer_id, "⚠ /колесо <ставка> <красное|чёрное|число 0-36>"); return
    choice = rest[0].lower()
    num = random.randint(0, 36)
    reds = {1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36}
    if num == 0: color = "зелёное"
    elif num in reds: color = "красное"
    else: color = "чёрное"
    win = 0; mult = 0
    if choice in ("красное","красный","к") and color == "красное": mult = 2
    elif choice in ("чёрное","черное","ч","черный","чёрный") and color == "чёрное": mult = 2
    elif choice.isdigit() and int(choice) == num: mult = 36
    if mult:
        win = int(bet * mult * vip_multiplier(peer_id, uid))
        nb = add_balance(peer_id, uid, win)
        send(peer_id, f"🎡 Выпало: {num} {color}\n🎉 x{mult}! +{fmt_num(win)}!\nБаланс: {fmt_num(nb)}")
    else:
        nb = add_balance(peer_id, uid, -bet)
        send(peer_id, f"🎡 Выпало: {num} {color}\n💀 -{fmt_num(bet)}\nБаланс: {fmt_num(nb)}")

def game_roulette(peer_id, uid, args):
    bal = get_balance(peer_id, uid)
    bet, rest = _bet_parse(args, bal)
    if bet is None: send(peer_id, rest); return
    if not rest or not rest[0].isdigit():
        send(peer_id, "⚠ /рулетка <ставка> <число 0-36>"); return
    num = int(rest[0])
    if not 0 <= num <= 36: send(peer_id, "⚠ Число 0-36"); return
    res = random.randint(0, 36)
    if res == num:
        win = int(bet * 36 * vip_multiplier(peer_id, uid))
        nb = add_balance(peer_id, uid, win)
        send(peer_id, f"🎰 Выпало: {res}\n🎉 x36! +{fmt_num(win)}!\nБаланс: {fmt_num(nb)}")
    else:
        nb = add_balance(peer_id, uid, -bet)
        send(peer_id, f"🎰 Выпало: {res}\n💀 -{fmt_num(bet)}\nБаланс: {fmt_num(nb)}")

def cmd_casino(peer_id, uid, args):
    bal = get_balance(peer_id, uid)
    bet, _ = _bet_parse(args, bal)
    if bet is None: send(peer_id, _); return
    if random.random() < 0.5:
        bonus = int(bet * vip_multiplier(peer_id, uid))
        nb = add_balance(peer_id, uid, bonus)
        send(peer_id, f"🎰 🎉 ВЫИГРЫШ! +{fmt_num(bonus)}\nБаланс: {fmt_num(nb)}")
    else:
        nb = add_balance(peer_id, uid, -bet)
        send(peer_id, f"🎰 💀 Проигрыш -{fmt_num(bet)}\nБаланс: {fmt_num(nb)}")

def cmd_duel_game(peer_id, uid, args, reply_msg):
    target = extract_user(" ".join(args), reply_msg)
    if not target: send(peer_id, "⚠ /дуэль @user <ставка>"); return
    if target == uid: send(peer_id, "🤔 Нельзя с собой."); return
    bet = None
    for a in args:
        if a.isdigit() and int(a) > 0: bet = int(a); break
    if not bet: send(peer_id, "⚠ Укажите ставку"); return
    if bet > get_balance(peer_id, uid): send(peer_id, "❌ Мало монет."); return
    if bet > get_balance(peer_id, target): send(peer_id, f"❌ У {mention(target, peer_id)} мало."); return
    winner = random.choice([uid, target])
    loser = target if winner == uid else uid
    add_balance(peer_id, uid, -bet); add_balance(peer_id, target, -bet)
    bonus = int(bet * 2 * vip_multiplier(peer_id, winner))
    nb = add_balance(peer_id, winner, bonus)
    send(peer_id,
         f"⚔️ {mention(uid, peer_id)} vs {mention(target, peer_id)}\n"
         f"Ставка: {fmt_num(bet)}\n🏆 {mention(winner, peer_id)}\n"
         f"💰 +{fmt_num(bonus)} → {fmt_num(nb)}")

# ================================================================
# ЭКОНОМИКА: бизнесы, приз, подписка, промо
# ================================================================
def cmd_buybiz(peer_id, uid, args):
    c = get_chat(peer_id)
    if not args: 
        lines = ["💼 Бизнесы для покупки:"]
        for k, v in BUSINESSES.items():
            lines.append(f"{v['emoji']} {k} — {fmt_num(v['price'])} 💰 (доход {fmt_num(v['income'])}/час)")
        send(peer_id, "\n".join(lines)); return
    name = args[0].lower()
    if name not in BUSINESSES:
        send(peer_id, f"⚠ Бизнес «{name}» не найден."); return
    biz = BUSINESSES[name]; bal = get_balance(peer_id, uid)
    if bal < biz["price"]:
        send(peer_id, f"❌ Нужно {fmt_num(biz['price'])}, у вас {fmt_num(bal)}"); return
    my = c.setdefault("businesses", {}).setdefault(str(uid), {})
    if name in my:
        send(peer_id, f"⚠ У вас уже есть {name}."); return
    my[name] = {"bought_at": int(time.time()), "last_collect": int(time.time())}
    add_balance(peer_id, uid, -biz["price"]); save_cfg(cfg)
    send(peer_id, f"✅ Куплен {biz['emoji']} {name}!\nДоход: {fmt_num(biz['income'])}/час\n/collect — собрать")

def cmd_mybiz(peer_id, uid):
    c = get_chat(peer_id)
    my = c.get("businesses", {}).get(str(uid), {})
    if not my: send(peer_id, "📭 У вас нет бизнесов.\n/buybiz — купить"); return
    lines = ["💼 Ваши бизнесы:"]
    total = 0
    for name, info in my.items():
        biz = BUSINESSES.get(name)
        if not biz: continue
        elapsed = int(time.time()) - info["last_collect"]
        hours = elapsed / 3600
        income = int(biz["income"] * min(hours, 24) * vip_multiplier(peer_id, uid))
        lines.append(f"{biz['emoji']} {name} — {fmt_num(biz['income'])}/час\n   Накоплено: {fmt_num(income)}")
        total += income
    lines.append(f"\n💰 Собрать: {fmt_num(total)}")
    lines.append("/collect")
    send(peer_id, "\n".join(lines))

def cmd_collect(peer_id, uid):
    c = get_chat(peer_id)
    my = c.get("businesses", {}).get(str(uid), {})
    if not my: send(peer_id, "❌ У вас нет бизнесов."); return
    now = int(time.time()); total = 0
    for name, info in my.items():
        biz = BUSINESSES.get(name)
        if not biz: continue
        elapsed = now - info["last_collect"]
        hours = min(elapsed / 3600, 24)
        if hours < 0.01: continue
        total += int(biz["income"] * hours * vip_multiplier(peer_id, uid))
        info["last_collect"] = now
    save_cfg(cfg)
    if total == 0: send(peer_id, "⏳ Слишком мало времени прошло. Подождите."); return
    nb = add_balance(peer_id, uid, total)
    send(peer_id, f"💰 Собрано: {fmt_num(total)}\nБаланс: {fmt_num(nb)}")

def cmd_prize(peer_id, uid):
    c = get_chat(peer_id); last = c.get("last_prize", {})
    now = int(time.time()); key = str(uid)
    elapsed = now - last.get(key, 0)
    if elapsed < PRIZE_COOLDOWN:
        wait = PRIZE_COOLDOWN - elapsed
        h = wait // 3600; m = wait % 3600 // 60
        send(peer_id, f"⏳ Следующий /приз через {h}ч {m}м"); return
    amount = random.randint(PRIZE_MIN, PRIZE_MAX)
    amount = int(amount * vip_multiplier(peer_id, uid))
    nb = add_balance(peer_id, uid, amount)
    last[key] = now; c["last_prize"] = last; save_cfg(cfg)
    send(peer_id, f"🎁 Ежедневный приз!\n💰 +{fmt_num(amount)} монет!\nБаланс: {fmt_num(nb)}\n\nВозвращайтесь через 24 часа.")

def cmd_sub(peer_id, uid):
    c = get_chat(peer_id)
    if is_vip(peer_id, uid):
        until = vip_until(peer_id, uid)
        send(peer_id, f"👑 Вы VIP до {fmt_dt(until)}\nБонус +{int(VIP_BONUS*100)}% к прибыли")
        return
    try:
        res = api.groups.isMember(group_id=GROUP_ID, user_id=uid)
        sub = (len(res) > 0 and res[0].get("member") == 1) if isinstance(res, list) else bool(res)
    except Exception: sub = False
    if not sub:
        send(peer_id,
             f"❌ Вы не подписаны на сообщество.\n\n"
             f"1. Подпишитесь: {COMMUNITY_LINK}\n"
             f"2. Вернитесь и напишите /подписка")
        return
    if c.get("subs", {}).get(str(uid), 0) > 0:
        send(peer_id, "⚠ Вы уже получали VIP."); return
    until = int(time.time()) + VIP_DURATION
    c.setdefault("subs", {})[str(uid)] = until
    nb = add_balance(peer_id, uid, VIP_PRICE_MSGS)
    save_cfg(cfg)
    send(peer_id,
         f"👑 VIP активирован до {fmt_dt(until)}\n"
         f"💰 +{fmt_num(VIP_PRICE_MSGS)} монет!\n"
         f"✨ Бонус +{int(VIP_BONUS*100)}% к прибыли")

def cmd_promo(peer_id, uid, args):
    if not args: send(peer_id, "⚠ /promo <код>"); return
    code = args[0].upper(); c = get_chat(peer_id)
    # ищем локальный или глобальный
    promo = c.get("promos", {}).get(code) or cfg.get("global_promos", {}).get(code)
    if not promo: send(peer_id, "❌ Промокод не найден."); return
    used = c.get("promos_used", {}).setdefault(str(uid), [])
    if code in used: send(peer_id, "⚠ Вы уже использовали этот промокод."); return
    if promo.get("uses_left", 0) <= 0: send(peer_id, "⚠ Промокод исчерпан."); return
    nb = add_balance(peer_id, uid, promo["reward"])
    promo["uses_left"] -= 1
    used.append(code); save_cfg(cfg)
    send(peer_id, f"🎟️ Промокод активирован!\n💰 +{fmt_num(promo['reward'])}\nБаланс: {fmt_num(nb)}")

def cmd_createpromo(peer_id, uid, args):
    c = get_chat(peer_id)
    if len(args) < 2 or not args[1].isdigit():
        send(peer_id, "⚠ /createpromo <код> <награда>\nПример: /createpromo SUMMER 5000"); return
    code = args[0].upper(); reward = int(args[1])
    if not 100 <= reward <= 1000000:
        send(peer_id, "⚠ Награда 100 - 1 000 000"); return
    if code in c.get("promos", {}):
        send(peer_id, "⚠ Такой промокод уже есть."); return
    c.setdefault("promos", {})[code] = {
        "reward": reward, "created_by": uid, "created_at": int(time.time()),
        "uses_left": 100,
    }
    save_cfg(cfg)
    send(peer_id, f"✅ Промокод {code} создан.\nНаграда: {fmt_num(reward)} 💰\nЛимит: 100 активаций")

def cmd_promolist(peer_id, uid):
    c = get_chat(peer_id)
    promos = c.get("promos", {})
    glob = cfg.get("global_promos", {})
    if not promos and not glob: send(peer_id, "📭 Промокодов нет."); return
    lines = ["🎟️ Промокоды:"]
    if promos:
        lines.append("\n📌 Локальные:")
        for code, p in promos.items():
            lines.append(f"• {code} — {fmt_num(p['reward'])} ({p['uses_left']} осталось)")
    if glob:
        lines.append("\n🌐 Глобальные:")
        for code, p in glob.items():
            lines.append(f"• {code} — {fmt_num(p['reward'])} ({p['uses_left']} осталось)")
    send(peer_id, "\n".join(lines))

# ================================================================
# ТОП / ВАЙП / БИЛДЫ / СТРАНЫ
# ================================================================
def cmd_top(peer_id, args):
    if not is_chat(peer_id): send(peer_id, "❌ Только в беседе."); return
    c = get_chat(peer_id)
    mode = args[0].lower() if args else "баланс"
    if mode in ("баланс","balance","деньги","money"):
        data = [(k, v) for k, v in c.get("balance", {}).items() if int(v) > 0]
        data.sort(key=lambda x: -x[1]); title = "💰 Топ по балансу"
    elif mode in ("сообщения","msg","msgs","messages"):
        data = [(k, v.get("msg_count", 0)) for k, v in c.get("user_stats", {}).items()]
        data.sort(key=lambda x: -x[1]); title = "📝 Топ по сообщениям"
    elif mode in ("бизнес","biz","business"):
        data = [(k, len(v)) for k, v in c.get("businesses", {}).items()]
        data.sort(key=lambda x: -x[1]); title = "💼 Топ по бизнесам"
    else:
        send(peer_id, "⚠ /топ [баланс|сообщения|бизнес]"); return
    if not data: send(peer_id, "📭 Нет данных."); return
    prefetch_names([int(k) for k, _ in data[:10]])
    lines = [title, ""]
    medals = ["🥇","🥈","🥉"]
    for i, (uid, val) in enumerate(data[:10]):
        medal = medals[i] if i < 3 else f"{i+1}."
        lines.append(f"{medal} {mention(uid, peer_id)} — {fmt_num(val)}")
    send(peer_id, "\n".join(lines))

def cmd_wipe(peer_id, uid):
    if not is_chat(peer_id): send(peer_id, "❌ Только в беседе."); return
    c = get_chat(peer_id)
    if uid != int(cfg["global_owner"]) and c.get("owner") != uid:
        send(peer_id, "⛔ Нет прав."); return
    c["balance"] = {}; save_cfg(cfg)
    send(peer_id, "🧹 Балансы беседы очищены!"); log_action(uid, f"вайп балансов {peer_id}")

def cmd_wipe_all(peer_id, uid):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔ Только Global."); return
    for ch in cfg.get("chats", {}).values(): ch["balance"] = {}
    save_cfg(cfg); send(peer_id, "🧹 ГЛОБАЛЬНЫЙ ВАЙП! Все балансы обнулены.")

def cmd_build(peer_id, uid, args):
    if not is_chat(peer_id): send(peer_id, "❌ Только в беседе."); return
    c = get_chat(peer_id)
    if uid != int(cfg["global_owner"]) and c.get("owner") != uid:
        send(peer_id, "⛔ Только владелец беседы."); return
    if not args: 
        cur = c.get("build_name")
        send(peer_id, f"🏗️ Текущая сетка: {cur or 'не задана'}\n\n/build <название> — привязать"); return
    name = " ".join(args).strip()
    c["build_name"] = name
    builds = cfg.setdefault("builds", {})
    builds.setdefault(name, [])
    if peer_id not in builds[name]: builds[name].append(peer_id)
    save_cfg(cfg)
    send(peer_id, f"🏗️ Беседа привязана к сетке «{name}»\nВсего в сетке: {len(builds[name])} бесед")

def cmd_builds(peer_id, uid):
    if uid != int(cfg["global_owner"]) and not is_chat(peer_id):
        send(peer_id, "❌ Только для Global."); return
    builds = cfg.get("builds", {})
    if not builds: send(peer_id, "📭 Сеток нет."); return
    lines = ["🏗️ Сетки бесед:"]
    for name, peers in builds.items():
        lines.append(f"\n📦 «{name}» — {len(peers)} бесед")
        for pid in peers[:5]:
            lines.append(f"  • {pid}")
        if len(peers) > 5: lines.append(f"  … и ещё {len(peers)-5}")
    send(peer_id, "\n".join(lines))

def cmd_countries(peer_id, uid):
    countries = cfg.get("countries", {})
    lines = ["🌍 Страны мира:", ""]
    for key, c in COUNTRIES.items():
        info = countries.get(key, {})
        pres = info.get("president")
        if pres:
            pres_txt = f"👑 {mention(pres, peer_id)}"
        else:
            pres_txt = "❌ нет"
        lines.append(f"{c['name']} — {pres_txt}")
    lines.append("")
    lines.append("Доступные для назначения: " + ", ".join(COUNTRIES.keys()))
    lines.append("Назначить: /setpresident <страна> @user (Global)")
    send(peer_id, "\n".join(lines))

def cmd_setpresident(peer_id, uid, args, reply_msg):
    if uid != int(cfg["global_owner"]):
        send(peer_id, "⛔ Только Global."); return
    if len(args) < 1:
        send(peer_id, "⚠ /setpresident <страна> @user"); return
    country = args[0].lower()
    if country not in COUNTRIES:
        send(peer_id, f"⚠ Страна не найдена. Доступно: {', '.join(COUNTRIES.keys())}"); return
    target = extract_user(" ".join(args), reply_msg)
    if not target: send(peer_id, "⚠ Укажите @user"); return
    cfg.setdefault("countries", {})[country] = {
        "president": target, "set_at": int(time.time()), "set_by": uid,
    }
    save_cfg(cfg)
    send(peer_id, f"👑 {mention(target, peer_id)} — Президент {COUNTRIES[country]['name']}!")
    log_action(uid, f"назначил {mention(target, peer_id)} президентом {country}")

def cmd_cmd(peer_id, uid, args):
    c = get_chat(peer_id)
    if len(args) < 2:
        aliases = c.get("custom_cmds", {})
        if not aliases:
            send(peer_id, "⚙️ Кастомных команд нет.\nИспользование: /cmd <команда> <новое_имя>"); return
        lines = ["⚙️ Кастомные команды:"]
        for a, o in aliases.items(): lines.append(f"• /{a} → /{o}")
        lines.append("\n/cmd reset <имя> — сбросить")
        send(peer_id, "\n".join(lines)); return
    if args[0].lower() == "reset":
        alias = args[1].lower().lstrip("/")
        removed = c.get("custom_cmds", {}).pop(alias, None); save_cfg(cfg)
        send(peer_id, f"✅ Удалено: /{alias}" if removed else f"⚠ Не найдено."); return
    orig = args[0].lower().lstrip("/"); alias = args[1].lower().lstrip("/")
    if orig not in ALL_COMMANDS: send(peer_id, f"⚠ /{orig} не существует."); return
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

        preview = text[:60].replace("\n", " ")
        print(f"📨 peer={peer_id} from={from_id} id={real_id} cmid={cmid} text={preview!r}")

        if is_duplicate(peer_id, msg): continue

        action = msg.get("action")
        if action:
            atype = action.get("type")
            if atype == "chat_invite_user":
                invited = action.get("member_id")
                if invited and is_chat(peer_id):
                    c = get_chat(peer_id)
                    if str(invited) in c.get("banned", {}):
                        cid = chat_id_from_peer(peer_id)
                        if cid:
                            kick_user(cid, invited)
                            send(peer_id, f"🚫 {mention(invited, peer_id)} в бане.")
                    else: handle_welcome(peer_id, action)
                continue
            if atype == "chat_kick_user": continue

        track_peer(peer_id)
        if from_id > 0 and is_chat(peer_id): track_message(from_id, peer_id, text)

        # мафия
        g = GAMES.get(peer_id) if is_chat(peer_id) else None
        if g:
            if g["phase"] == "night" and from_id in g["players"] and from_id in g["alive"]:
                delete_msg(real_id, cmid, peer_id); continue
            if g["phase"] == "lobby" and text.lower().strip() in MAFIA_JOIN_WORDS:
                mafia_join(peer_id, from_id); continue

        # бан/мут
        if is_chat(peer_id):
            c = get_chat(peer_id)
            if str(from_id) in c.get("banned", {}):
                delete_msg(real_id, cmid, peer_id)
                kick_user(chat_id_from_peer(peer_id), from_id); continue
            muted = c.get("muted", {})
            if str(from_id) in muted:
                info = muted[str(from_id)]
                if isinstance(info, (int, float)): info = {"until": info, "last_dm": 0}; muted[str(from_id)] = info
                now = time.time()
                if info["until"] > now:
                    delete_msg(real_id, cmid, peer_id)
                    if now - info.get("last_dm", 0) > MUTE_DM_INTERVAL:
                        mute_warn_dm(from_id, info["until"] - now)
                        info["last_dm"] = now; save_cfg(cfg)
                    continue
                else: mute_expired_dm(from_id); del muted[str(from_id)]; save_cfg(cfg)

        if not text.startswith("/"): continue
        parts = text.split(); cmd = parts[0][1:].lower(); args = parts[1:]
        reply_msg = msg.get("reply_message")

        # алиасы
        if is_chat(peer_id):
            aliases = get_chat(peer_id).get("custom_cmds", {})
            if cmd in aliases: cmd = aliases[cmd]

        if cmd not in ALL_COMMANDS:
            sug = suggest_command(cmd)
            if sug: send(peer_id, f"❓ Может /{sug}\n📋 /help", reply_to=reply_ref)
            else: send(peer_id, f"❌ Команды /{cmd} нет.\n💡 /offer <идея>", reply_to=reply_ref)
            continue

        # === ПУБЛИЧНЫЕ ===
        if cmd == "help":
            send(peer_id, build_help(), reply_to=reply_ref); continue
        if cmd == "staff":
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            send(peer_id, build_staff_text(peer_id), reply_to=reply_ref); continue
        if cmd == "info":
            t = extract_user(text, reply_msg)
            if not t: send(peer_id, "⚠ Укажи пользователя.", reply_to=reply_ref); continue
            send(peer_id, user_info_text(t, peer_id), reply_to=reply_ref); continue
        if cmd in ("стата","stat"):
            t = extract_user(text, reply_msg) or from_id; prefetch_names([t])
            send(peer_id, user_stats_text(t, peer_id), reply_to=reply_ref); continue
        if cmd in ("balance","баланс"):
            t = extract_user(text, reply_msg) or from_id
            b = get_balance(peer_id, t)
            vip = " 👑VIP" if is_vip(peer_id, t) else ""
            if t == from_id: send(peer_id, f"💰 Ваш баланс: {fmt_num(b)} монет{vip}", reply_to=reply_ref)
            else: send(peer_id, f"💰 {mention(t, peer_id)}: {fmt_num(b)} монет{vip}", reply_to=reply_ref)
            continue
        if cmd in ("топ","top"):
            cmd_top(peer_id, args); continue
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
                send(peer_id, "⛔ Только владелец беседы.", reply_to=reply_ref); continue
            cmd_createpromo(peer_id, from_id, args); continue
        if cmd == "promolist":
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            c = get_chat(peer_id)
            if from_id != int(cfg["global_owner"]) and c.get("owner") != from_id and not can(from_id, "role", peer_id):
                send(peer_id, "⛔ Нет прав.", reply_to=reply_ref); continue
            cmd_promolist(peer_id, from_id); continue
        if cmd in ("страны","государства"):
            cmd_countries(peer_id, from_id); continue
        if cmd == "build":
            cmd_build(peer_id, from_id, args); continue
        if cmd == "builds":
            if from_id != int(cfg["global_owner"]):
                send(peer_id, "⛔ Только Global.", reply_to=reply_ref); continue
            cmd_builds(peer_id, from_id); continue
        if cmd in ("вайп",):
            cmd_wipe(peer_id, from_id); continue
        if cmd == "вайп_все":
            cmd_wipe_all(peer_id, from_id); continue
        if cmd == "cmd":
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            cmd_cmd(peer_id, from_id, args); continue
        if cmd == "offer":
            if not args: send(peer_id, "⚠ /offer <текст>", reply_to=reply_ref); continue
            tid = create_ticket("offer", from_id, peer_id, " ".join(args))
            send(peer_id, f"💡 Тикет #{tid}.", reply_to=reply_ref)
            log_action(from_id, f"тикет #{tid}"); continue
        if cmd == "report":
            if not args: send(peer_id, "⚠ /report <текст>", reply_to=reply_ref); continue
            tid = create_ticket("report", from_id, peer_id, " ".join(args))
            send(peer_id, f"❓ Тикет #{tid}.", reply_to=reply_ref); continue
        if cmd in ("ивент","event"):
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            if not args:
                lines = ["🎉 Ивенты:"]
                for k, v in EVENTS_LIST.items(): lines.append(f"• /ивент {k} — {v}")
                custom = cfg.get("custom_events", {})
                if custom:
                    lines.append("\n🎨 Кастомные:")
                    for k, v in custom.items(): lines.append(f"• /ивент {v['name']} — 🏆 {v['reward']}")
                lines.append("\n🎲 /ивент рандом")
                send(peer_id, "\n".join(lines), reply_to=reply_ref); continue
            ev = args[0].lower()
            if ev in ("рандом","random","ранд"): run_random_event(peer_id); continue
            if ev == "мафия":
                if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
                mafia_start(peer_id, from_id); continue
            if ev in EVENT_HANDLERS:
                send(peer_id, f"🎉 {EVENTS_LIST[ev]}")
                try: EVENT_HANDLERS[ev](peer_id)
                except Exception as e: send(peer_id, f"❌ {e}", reply_to=reply_ref)
                continue
            if ev_custom(peer_id, ev): continue
            send(peer_id, f"⚠ Не найден.", reply_to=reply_ref); continue

        # === ПРОВЕРКА ПРАВ ===
        if not can(from_id, cmd, peer_id):
            send(peer_id, "⛔ Нет прав.", reply_to=reply_ref); continue

        # === ROLE ===
        if cmd == "role":
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            c = get_chat(peer_id)
            lines = ["🎭 Роли в этой беседе:"]
            all_roles = dict(cfg["roles"]); all_roles.update(c.get("local_roles", {}))
            for k, r in sorted(all_roles.items(), key=lambda x: -x[1]["priority"]):
                lines.append(f"• {r['name']} (приоритет {r['priority']})")
            send(peer_id, "\n".join(lines), reply_to=reply_ref); continue

        # === ГЛОБАЛЬНЫЕ ===
        if cmd in ("объявление","announce","рассылка"):
            if from_id != int(cfg["global_owner"]): send(peer_id, "⛔ Только Global.", reply_to=reply_ref); continue
            if not args: send(peer_id, "⚠ /объявление <текст>", reply_to=reply_ref); continue
            ann = " ".join(args); ok = 0
            for pid in cfg.get("known_peers", []):
                try: api.messages.send(peer_id=pid, message=f"📢 ОБЪЯВЛЕНИЕ\n\n{ann}",
                    random_id=int(time.time()*1000)+ok); ok += 1
                except Exception: pass
            send(peer_id, f"✅ Отправлено: {ok}", reply_to=reply_ref); continue

        if cmd == "setpresident":
            cmd_setpresident(peer_id, from_id, args, reply_msg); continue

        if cmd == "newrole":
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            if len(args) < 2 or not args[-1].isdigit():
                send(peer_id, "⚠ /newrole <название> <0-100>", reply_to=reply_ref); continue
            pr = int(args[-1])
            if not (0 <= pr <= 100) or pr == 100:
                send(peer_id, "⚠ 0-99", reply_to=reply_ref); continue
            name = " ".join(args[:-1]).strip(); key = name.lower()
            c = get_chat(peer_id)
            if key in c.get("local_roles", {}) or key in cfg["roles"]:
                send(peer_id, f"⚠ Уже есть.", reply_to=reply_ref); continue
            c.setdefault("local_roles", {})[key] = {"name": name, "priority": pr,
                                                    "commands": commands_for_priority(pr)}
            save_cfg(cfg)
            send(peer_id, f"✅ Роль «{name}» создана в этом чате ({pr}).", reply_to=reply_ref); continue

        if cmd == "delrole":
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            if not args: send(peer_id, "⚠ /delrole <название>", reply_to=reply_ref); continue
            name = " ".join(args); key = find_role_by_input(name, peer_id)
            if not key: send(peer_id, f"⚠ Не найдена.", reply_to=reply_ref); continue
            c = get_chat(peer_id)
            if key in c.get("local_roles", {}):
                del c["local_roles"][key]
                for u in [x for x, r in c.get("staff", {}).items() if r == key]: del c["staff"][u]
                save_cfg(cfg); send(peer_id, f"🗑 Роль удалена.", reply_to=reply_ref); continue
            if from_id != int(cfg["global_owner"]): send(peer_id, "⛔ Глоб. роли — только Global.", reply_to=reply_ref); continue
            for ch in cfg.get("chats", {}).values():
                for u in [x for x, r in ch.get("staff", {}).items() if r == key]: del ch["staff"][u]
            del cfg["roles"][key]; save_cfg(cfg)
            send(peer_id, f"🗑 Глоб. роль удалена.", reply_to=reply_ref); continue

        if cmd == "createivent":
            if from_id != int(cfg["global_owner"]): send(peer_id, "⛔ Только Global.", reply_to=reply_ref); continue
            if not args: send(peer_id, "⚠ /createivent <название> | <награда> | <требование>", reply_to=reply_ref); continue
            parts_ev = [p.strip() for p in " ".join(args).split("|")]
            if len(parts_ev) < 3: send(peer_id, "⚠ Нужно 3 части через |", reply_to=reply_ref); continue
            name, reward, req = parts_ev[0], parts_ev[1], parts_ev[2]; key = name.lower()
            if key in cfg.get("custom_events", {}): send(peer_id, "⚠ Уже есть.", reply_to=reply_ref); continue
            cfg["custom_events"][key] = {"name": name, "reward": reward, "requirement": req,
                                          "created_by": from_id, "created_at": int(time.time())}
            save_cfg(cfg)
            send(peer_id, f"✅ Ивент «{name}» создан.", reply_to=reply_ref); continue

        # === ТИКЕТЫ ===
        if cmd == "tickets":
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            send(peer_id, tickets_list_text(), reply_to=reply_ref); continue
        if cmd == "adt":
            if len(args) < 2 or not args[0].isdigit():
                send(peer_id, "⚠ /adt <номер> <ответ>", reply_to=reply_ref); continue
            ok, msg_ans = answer_ticket(args[0], from_id, " ".join(args[1:]))
            send(peer_id, f"✅ Отправлен." if ok else f"❌ {msg_ans}", reply_to=reply_ref); continue

        # === УТИЛИТЫ ===
        if cmd == "loginfo":
            send(peer_id, f"📝 Лог: {cfg.get('log_peer_id') or 'не задана'}", reply_to=reply_ref); continue
        if cmd == "setlog":
            if from_id != int(cfg["global_owner"]) and not (is_chat(peer_id) and get_chat(peer_id).get("owner") == from_id):
                send(peer_id, "⛔ Нет прав.", reply_to=reply_ref); continue
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            cfg["log_peer_id"] = peer_id; save_cfg(cfg)
            send(peer_id, f"✅ Лог: {peer_id}", reply_to=reply_ref); continue
        if cmd == "unsetlog":
            if from_id != int(cfg["global_owner"]): send(peer_id, "⛔ Global only.", reply_to=reply_ref); continue
            cfg["log_peer_id"] = 0; save_cfg(cfg); send(peer_id, "✅ Лог отключён.", reply_to=reply_ref); continue
        if cmd == "setwarns":
            if from_id != int(cfg["global_owner"]) and not (is_chat(peer_id) and get_chat(peer_id).get("owner") == from_id):
                send(peer_id, "⛔ Нет прав.", reply_to=reply_ref); continue
            if not args or not args[0].isdigit(): send(peer_id, "⚠ /setwarns 3", reply_to=reply_ref); continue
            cfg["max_warns"] = int(args[0]); save_cfg(cfg)
            send(peer_id, f"✅ Лимит: {cfg['max_warns']}", reply_to=reply_ref); continue
        if cmd == "setmutetime":
            if from_id != int(cfg["global_owner"]) and not (is_chat(peer_id) and get_chat(peer_id).get("owner") == from_id):
                send(peer_id, "⛔ Нет прав.", reply_to=reply_ref); continue
            if not args or not args[0].isdigit(): send(peer_id, "⚠ /setmutetime 30", reply_to=reply_ref); continue
            cfg["default_mute_minutes"] = int(args[0]); save_cfg(cfg)
            send(peer_id, f"✅ Мут: {cfg['default_mute_minutes']}", reply_to=reply_ref); continue
        if cmd == "banlist":
            if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue
            b = get_chat(peer_id).get("banned", {})
            if not b: send(peer_id, "📭 Пусто.", reply_to=reply_ref); continue
            lines = ["🚫 Забаненные:"]
            for u, i in b.items(): lines.append(f"• {mention(u, peer_id)} — {i.get('reason','—')}")
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
                parts_n = [a for a in args if not re.match(r"\[id\d+\|", a) and not re.match(r"@id\d+", a)]
                nn = " ".join(parts_n).strip()
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

        # команды с target
        target = extract_user(text, reply_msg)
        if not target: send(peer_id, "⚠ Укажи пользователя.", reply_to=reply_ref); continue
        if target == from_id: send(peer_id, "🤔 Нельзя к себе.", reply_to=reply_ref); continue
        if int(target) == int(cfg["global_owner"]) and from_id != int(cfg["global_owner"]):
            send(peer_id, "🌐 Нельзя.", reply_to=reply_ref); continue
        if not is_chat(peer_id): send(peer_id, "❌ Только в беседе.", reply_to=reply_ref); continue

        c = get_chat(peer_id); cid = chat_id_from_peer(peer_id)

        if cmd == "setowner":
            if from_id != int(cfg["global_owner"]): send(peer_id, "⛔ Global only.", reply_to=reply_ref); continue
            c["owner"] = target; save_cfg(cfg)
            send(peer_id, f"👑 {mention(target, peer_id)} — Владелец.", reply_to=reply_ref); continue
        if cmd == "ban":
            reason = " ".join(args) if args else "без причины"
            ok, err = kick_user(cid, target)
            if not ok: send(peer_id, f"❌ {err}", reply_to=reply_ref); continue
            c["banned"][str(target)] = {"reason": reason, "by": from_id, "at": int(time.time()), "global": False}
            save_cfg(cfg); send(peer_id, f"🔨 {mention(target, peer_id)} забанен.", reply_to=reply_ref)
        elif cmd == "unban":
            rem = c["banned"].pop(str(target), None); save_cfg(cfg)
            send(peer_id, "✅ Разбанен." if rem else "ℹ Нет.", reply_to=reply_ref)
        elif cmd == "gban":
            reason = " ".join(args) if args else "без причины"; kicked = 0
            for pid in cfg.get("known_peers", []):
                c2 = chat_id_from_peer(pid)
                if not c2: continue
                ok, _ = kick_user(c2, target)
                if ok: kicked += 1
            for ch in cfg.get("chats", {}).values():
                ch["banned"][str(target)] = {"reason": reason, "by": from_id, "at": int(time.time()), "global": True}
            save_cfg(cfg); send(peer_id, f"🌐 Глобан. Кикнут: {kicked}.", reply_to=reply_ref)
        elif cmd == "ungban":
            rem = 0
            for ch in cfg.get("chats", {}).values():
                i = ch["banned"].get(str(target))
                if i and i.get("global"): del ch["banned"][str(target)]; rem += 1
            save_cfg(cfg)
            send(peer_id, f"✅ Снят ({rem})." if rem else "ℹ Нет.", reply_to=reply_ref)
        elif cmd == "kick":
            ok, err = kick_user(cid, target)
            send(peer_id, "👢 Исключён." if ok else f"❌ {err}", reply_to=reply_ref)
        elif cmd == "mute":
            minutes = cfg["default_mute_minutes"]
            if args and args[0].isdigit():
                minutes = int(args[0])
                if minutes <= 0: minutes = cfg["default_mute_minutes"]
            c["muted"][str(target)] = {"until": time.time() + minutes * 60, "last_dm": time.time()}
            save_cfg(cfg); send(peer_id, f"🔇 {mention(target, peer_id)} {minutes} мин.", reply_to=reply_ref)
            mute_notify_dm(target, minutes)
        elif cmd == "unmute":
            rem = c["muted"].pop(str(target), None); save_cfg(cfg)
            if rem:
                send(peer_id, f"🔊 Размьючен.", reply_to=reply_ref); send_dm(target, "🔊 Мут снят.")
            else: send(peer_id, "ℹ Не в муте.", reply_to=reply_ref)
        elif cmd == "warn":
            reason = " ".join(args) if args else "без причины"
            wr = c["warns"]; wr[str(target)] = wr.get(str(target), 0) + 1; cnt = wr[str(target)]
            save_cfg(cfg)
            send(peer_id, f"⚠ {mention(target, peer_id)} ({cnt}/{cfg['max_warns']}). {reason}", reply_to=reply_ref)
            if cnt >= cfg["max_warns"]:
                c["muted"][str(target)] = {"until": time.time() + 3600, "last_dm": time.time()}
                save_cfg(cfg); send(peer_id, f"🔇 Лимит — 60 мин.", reply_to=reply_ref)
                mute_notify_dm(target, 60)
        elif cmd == "unwarn":
            c["warns"].pop(str(target), None); save_cfg(cfg)
            send(peer_id, "✅ Снято.", reply_to=reply_ref)
        elif cmd in ("addstaff", "setrole"):
            if from_id != int(cfg["global_owner"]) and c.get("owner") != from_id:
                send(peer_id, "⛔ Нет прав.", reply_to=reply_ref); continue
            ri = " ".join(args).strip(); rk = find_role_by_input(ri, peer_id)
            if not rk:
                all_roles = dict(cfg["roles"]); all_roles.update(c.get("local_roles", {}))
                avail = ", ".join(v["name"] for v in all_roles.values())
                send(peer_id, f"⚠ Не найдена. Есть: {avail}", reply_to=reply_ref); continue
            c["staff"][str(target)] = rk; save_cfg(cfg)
            rname = (c.get("local_roles", {}).get(rk) or cfg["roles"].get(rk, {})).get("name", rk)
            send(peer_id, f"✅ {mention(target, peer_id)} → {rname}.", reply_to=reply_ref)
        elif cmd == "removestaff":
            if from_id != int(cfg["global_owner"]) and c.get("owner") != from_id:
                send(peer_id, "⛔ Нет прав.", reply_to=reply_ref); continue
            if str(target) == str(cfg["global_owner"]): send(peer_id, "🌐 Нельзя.", reply_to=reply_ref); continue
            rem = c["staff"].pop(str(target), None); save_cfg(cfg)
            if rem:
                rname = (c.get("local_roles", {}).get(rem) or cfg["roles"].get(rem, {})).get("name", rem)
                send(peer_id, f"❌ Снят с «{rname}».", reply_to=reply_ref)
            else: send(peer_id, "ℹ Без роли.", reply_to=reply_ref)

# ================================================================
if __name__ == "__main__":
    print(f"✅ VK Бот 6.0 запущен (PID={os.getpid()})")
    print(f"   Группа: {GROUP_ID}")
    print("   Жду сообщений...\n")
    try:
        while True:
            try: main()
            except KeyboardInterrupt: print("\n⏹ Стоп."); break
            except Exception as e:
                print(f"⚠ {e}. Рестарт через 5с..."); time.sleep(5)
    finally:
        try: os.remove(PID_FILE)
        except Exception: pass
