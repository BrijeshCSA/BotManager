# -*- coding: utf-8 -*-
import os, re, sys, json, time, random, threading
import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.exceptions import VkApiError

TOKEN = os.getenv("VK_TOKEN", "").strip()
GROUP_ID = int(os.getenv("VK_GROUP_ID", "241512398"))
GLOBAL_OWNER_ID = int(os.getenv("GLOBAL_OWNER_ID", "1054352381"))
if not TOKEN: print("❌ VK_TOKEN"); sys.exit(1)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
PID_FILE = "/tmp/.bot.pid"
MUTE_DM_INTERVAL = 300
START_BALANCE = 100
PRIZE_MIN, PRIZE_MAX, PRIZE_COOLDOWN = 1000, 900000, 86400
VIP_PRICE, VIP_DURATION, VIP_BONUS = 1000000, 30*86400, 0.10
WAR_COST = 1000000; WAR_CAPTURE_SECONDS = 300; BASE_ARMY = 100000
ARMY_LEVEL_MAX = 10; ARMY_LEVEL_MULT = 1.15
MIL_TASK_COOLDOWN = 3600; MIL_TASK_REWARD = 5000; MIL_TASK_COST = 100000
DRONE_FLIGHT_SECONDS = 300; INTERCEPT_CHANCE = 0.20
IMPROVE_BASE_COST = 500000; IMPROVE_BASE_POINTS = 10
CUSTOMS_RATE = 0.10; SMUGGLE_CHANCE = 0.40; SMUGGLE_FINE = 3

CARGO_TYPES = {"еда":{"price":100,"emoji":"🍞"},"оружие":{"price":5000,"emoji":"🔫"},"ресурсы":{"price":500,"emoji":"⛏"},"топливо":{"price":800,"emoji":"⛽"},"деньги":{"price":1,"emoji":"💰"}}
TRANSPORTS = {"грузовик":{"cost":10000,"capacity":1000,"speed":3600,"emoji":"🚚"},"поезд":{"cost":50000,"capacity":10000,"speed":7200,"emoji":"🚂"},"корабль":{"cost":200000,"capacity":50000,"speed":14400,"emoji":"🚢"},"самолёт":{"cost":500000,"capacity":100000,"speed":1800,"emoji":"✈️"}}
COUNTRIES = {"россия":{"name":"🇷🇺 Россия"},"сша":{"name":"🇺🇸 США"},"китай":{"name":"🇨🇳 Китай"},"германия":{"name":"🇩🇪 Германия"},"япония":{"name":"🇯🇵 Япония"},"франция":{"name":"🇫🇷 Франция"},"великобритания":{"name":"🇬🇧 Великобритания"},"италия":{"name":"🇮🇹 Италия"},"испания":{"name":"🇪🇸 Испания"},"канада":{"name":"🇨🇦 Канада"},"украина":{"name":"🇺🇦 Украина"},"казахстан":{"name":"🇰🇿 Казахстан"},"беларусь":{"name":"🇧🇾 Беларусь"},"польша":{"name":"🇵🇱 Польша"},"турция":{"name":"🇹🇷 Турция"},"индия":{"name":"🇮🇳 Индия"},"бразилия":{"name":"🇧🇷 Бразилия"},"мексика":{"name":"🇲🇽 Мексика"},"австралия":{"name":"🇦🇺 Австралия"},"египет":{"name":"🇪🇬 Египет"},"корея":{"name":"🇰🇷 Корея"},"швеция":{"name":"🇸🇪 Швеция"},"швейцария":{"name":"🇨🇭 Швейцария"},"оаэ":{"name":"🇦🇪 ОАЭ"}}

CITY_NAMES = {
"россия":["Москва","Санкт-Петербург","Новосибирск","Екатеринбург","Казань","Нижний Новгород","Челябинск","Самара","Омск","Ростов-на-Дону","Уфа","Красноярск","Воронеж","Пермь","Волгоград","Краснодар","Саратов","Тюмень","Тольятти","Ижевск","Барнаул","Ульяновск","Иркутск","Хабаровск","Ярославль","Владивосток","Махачкала","Томск","Оренбург","Кемерово","Новокузнецк","Рязань","Астрахань","Пенза","Липецк","Киров","Чебоксары","Балашиха","Курск","Тула"],
"сша":["Вашингтон","Нью-Йорк","Лос-Анджелес","Чикаго","Хьюстон","Финикс","Филадельфия","Сан-Антонио","Сан-Диего","Даллас","Сан-Хосе","Остин","Джэксонвилл","Сан-Франциско","Индианаполис","Колумбус","Форт-Уэрт","Шарлотт","Детройт","Эль-Пасо","Мемфис","Сиэтл","Денвер","Бостон","Нэшвилл","Балтимор","Оклахома","Луисвилл","Портленд","Лас-Вегас","Милуоки","Альбукерке","Тусон","Фресно","Сакраменто","Канзас","Атланта","Майами","Омаха","Кливленд"],
"китай":["Пекин","Шанхай","Гуанчжоу","Шэньчжэнь","Чэнду","Ханчжоу","Ухань","Сиань","Чунцин","Тяньцзинь","Нанкин","Шэньян","Харбин","Циндао","Далянь","Сучжоу","Чанша","Куньмин","Чжэнчжоу","Фучжоу","Цзинань","Хэфэй","Наньчан","Нинбо","Уси","Сямынь","Вэньчжоу","Фошань","Дунгуань","Тайюань","Шицзячжуан","Гуйян","Ланьчжоу","Хайкоу","Урумчи","Хух-Хото","Иньчуань","Синин","Лхаса","Наньнин"],
"япония":["Токио","Осака","Нагоя","Саппоро","Фукуока","Кобе","Киото","Кавасаки","Сайтама","Хиросима","Сэндай","Тиба","Китакюсю","Сакаи","Ниигата","Хамамацу","Кумамото","Сагамихара","Сидзуока","Окаяма","Кагосима","Оита","Нагасаки","Миядзаки","Мацуяма","Каназава","Уцуномия","Тояма","Оцу","Наха","Акита","Мориока","Фукусима","Ямагата","Нагано","Гифу","Фукуи","Тоттори","Мацуэ","Кофу"],
"германия":["Берлин","Гамбург","Мюнхен","Кёльн","Франкфурт","Штутгарт","Дюссельдорф","Дортмунд","Эссен","Лейпциг","Бремен","Дрезден","Ганновер","Нюрнберг","Дуйсбург","Бохум","Вупперталь","Билефельд","Бонн","Мюнстер","Карлсруэ","Мангейм","Аугсбург","Висбаден","Мёнхенгладбах","Гельзенкирхен","Брауншвейг","Хемниц","Киль","Аахен","Галле","Магдебург","Фрайбург","Крефельд","Любек","Оберхаузен","Эрфурт","Майнц","Росток","Кассель"],
"франция":["Париж","Марсель","Лион","Тулуза","Ницца","Нант","Страсбург","Монпелье","Бордо","Лилль","Ренн","Реймс","Сент-Этьен","Тулон","Гавр","Гренобль","Дижон","Анже","Ним","Вильбан","Клермон-Ферран","Ле-Ман","Экс-ан-Прованс","Брест","Тур","Амьен","Лимож","Анси","Мец","Безансон","Орлеан","Руан","Мюлуз","Кан","Нанси","Аржантёй","Рубе","Авиньон","Пуатье","Ла-Рошель"]}

def get_country_cities(k):
    if k in CITY_NAMES: return CITY_NAMES[k][:40]
    return ["Столица"]+[f"Столица {i}-й район" for i in range(1,40)]

WEAPONS = {"танк":{"cost":50000,"power":100,"emoji":"🚜"},"пво":{"cost":40000,"power":80,"emoji":"🚀"},"ракета":{"cost":100000,"power":250,"emoji":"🚀"},"корабль":{"cost":300000,"power":500,"emoji":"⛴"},"самолёт":{"cost":200000,"power":400,"emoji":"✈️"},"бпла":{"cost":30000,"power":50,"emoji":"🛸"}}
RANKS = {"гражданин":{"name":"👤 Гражданин","bonus_mult":1.0},"политик":{"name":"🏛️ Политик","bonus_mult":1.2},"сенатор":{"name":"⚖️ Сенатор","bonus_mult":1.5},"министр":{"name":"💼 Министр","bonus_mult":2.0},"главком":{"name":"🎖️ Главнокомандующий","bonus_mult":3.0},"президент":{"name":"👑 Президент","bonus_mult":5.0}}
GOV_POSITIONS = ["президент","премьер-министр","министр обороны","министр экономики","министр иностранных дел","главнокомандующий","начальник генштаба","сенатор","губернатор","дипломат"]
ARMY_RANKS = ["рядовой","ефрейтор","младший сержант","сержант","старший сержант","прапорщик","лейтенант","капитан","майор","подполковник","полковник","генерал-майор","генерал-лейтенант","генерал-полковник","маршал"]
RANK_REQUIREMENTS = {"ефрейтор":(50,10000),"младший сержант":(150,30000),"сержант":(300,70000),"старший сержант":(500,120000),"прапорщик":(800,200000),"лейтенант":(1200,350000),"капитан":(1800,550000),"майор":(2500,800000),"подполковник":(3500,1200000),"полковник":(5000,1800000),"генерал-майор":(7000,2500000),"генерал-лейтенант":(10000,4000000),"генерал-полковник":(15000,6000000),"маршал":(25000,10000000)}
BUSINESSES = {"киоск":{"price":1000,"income":50,"emoji":"🏪"},"кафе":{"price":5000,"income":250,"emoji":"☕"},"ресторан":{"price":20000,"income":1000,"emoji":"🍽️"},"автомойка":{"price":35000,"income":1800,"emoji":"🚗"},"завод":{"price":100000,"income":5000,"emoji":"🏭"},"банк":{"price":250000,"income":12000,"emoji":"🏦"},"корпорация":{"price":500000,"income":25000,"emoji":"🏢"},"нефтевышка":{"price":1000000,"income":55000,"emoji":"🛢️"},"отель":{"price":300000,"income":15000,"emoji":"🏨"},"аэропорт":{"price":2000000,"income":110000,"emoji":"✈️"}}
BUILDINGS = {"больница":{"cost":200000,"emoji":"🏥"},"завод":{"cost":300000,"emoji":"🏭"},"школа":{"cost":150000,"emoji":"🏫"},"университет":{"cost":500000,"emoji":"🎓"},"электростанция":{"cost":400000,"emoji":"⚡"},"жилой комплекс":{"cost":250000,"emoji":"🏢"},"казарма":{"cost":350000,"emoji":"🏛"},"военный завод":{"cost":600000,"emoji":"🏗"},"верфь":{"cost":800000,"emoji":"⛴"},"аэропорт":{"cost":1000000,"emoji":"✈️"}}

PUBLIC_CMDS = ["help","info","staff","стата","stat","топ","top","баланс","balance","biz","buybiz","mybiz","collect","казино","casino","дуэль","duel","монетка","coin","кубик","dice","слоты","slots","краш","crash","дартс","darts","колесо","wheel","рулетка","roulette","блэкджек","bj","мины","mines","башня","tower","кейс","case","гонка","race","рыбалка","fish","приз","prize","подписка","sub","promo","промо","cmd","offer","report","ивент","event","мафия","mafia","страны","государства","гражданство","citizenship","паспорт","passport","страна","country","граждане","города","казна","правительство","должности","армия","выборы","выдвинуться","голос","компания","регистрация","переименоватьооо","войны","война","захват","контразащита","мир","коалиции","коалиция","коалпомощь","мобилизация","демобилизация","сделать","установить","пво","запуск","задание","выполнитьзадание","госскоманды","донат","сирена","воздухтревога","передать","вернуть","завершить_конфликт","дрон","перехват","улучшить_страну","звание","повысить","очки","граница","виза","перевозка","контрабанда","склад","транспорт","q","rules","раздача","взять"]
HELPER_CMDS = PUBLIC_CMDS + ["warn","promolist","createpromo","вайп"]
MODERATOR_CMDS = HELPER_CMDS + ["nick","rnick","unwarn","mute","unmute","clear","banlist","tickets","adt"]
ADMIN_CMDS = MODERATOR_CMDS + ["kick","ban","unban","gban","ungban"]
STAFF_CMDS = ADMIN_CMDS + ["loginfo","builds"]
GLOBAL_ONLY = ["объявление","announce","рассылка","setpresident","setcommander","grole","removerole","gstaff","устгражданство","устпрезидент","выдать"]

DEFAULT_ROLES = {"head":{"name":"Руководитель","priority":95,"commands":STAFF_CMDS},"deputy_head":{"name":"Зам. Руководителя","priority":90,"commands":STAFF_CMDS},"special_admin":{"name":"Спец. Администратор","priority":85,"commands":STAFF_CMDS},"chief_admin":{"name":"Гл. Администратор","priority":80,"commands":ADMIN_CMDS},"deputy_chief_admin":{"name":"Зам. Гл. Администратора","priority":75,"commands":ADMIN_CMDS},"chief_watcher":{"name":"Гл. Следящий","priority":70,"commands":MODERATOR_CMDS},"deputy_chief_watcher":{"name":"Зам. Гл. Следящего","priority":65,"commands":MODERATOR_CMDS},"admin":{"name":"Администратор","priority":60,"commands":ADMIN_CMDS},"moderator":{"name":"Модератор","priority":50,"commands":MODERATOR_CMDS},"helper":{"name":"Хелпер","priority":20,"commands":HELPER_CMDS}}

def commands_for_priority(p):
    if p >= 70: return list(STAFF_CMDS)
    if p >= 60: return list(ADMIN_CMDS)
    if p >= 40: return list(MODERATOR_CMDS)
    if p >= 20: return list(HELPER_CMDS)
    return list(PUBLIC_CMDS)

ALL_COMMANDS = set(PUBLIC_CMDS)
for _r in DEFAULT_ROLES.values(): ALL_COMMANDS.update(_r.get("commands", []))
ALL_COMMANDS.update(GLOBAL_ONLY)
ALL_COMMANDS.update(["newrole","delrole","createivent","setowner","setrole","removestaff","build","rules","q","раздача","взять"])

DEFAULT_CHAT = {"owner":None,"staff":{},"banned":{},"muted":{},"warns":{},"nicknames":{},"welcome":True,"user_stats":{},"balance":{},"businesses":{},"subs":{},"last_prize":{},"promos_used":{},"promos":{},"local_roles":{},"custom_cmds":{},"build_name":None}

def default_country_data():
    return {"treasury":0,"president":None,"commander":None,"citizens":[],"army":BASE_ARMY,"army_level":1,"weapons":{w:0 for w in WEAPONS},"nukes":0,"cities_unlocked":3,"cities":{},"coalition":None,"wars":[],"tax":5,"government":{},"elections":{"candidates":[],"votes":{},"ends_at":0,"active":False},"projects":[],"companies":{},"mil_task_cooldown":{},"history":[],"destroyed":False,"captured_by":None,"destroyed_at":0,"hostages":[],"activation_points":0,"drones_in_flight":[],"army_ranks":{},"borders_open":True,"border_closed_to":[],"visas":[],"transports":{},"cargo_stock":{t:0 for t in CARGO_TYPES},"cargo_in_transit":[]}

DEFAULT_CFG = {"global_owner":GLOBAL_OWNER_ID,"default_mute_minutes":30,"max_warns":3,"log_peer_id":0,"roles":DEFAULT_ROLES,"global_staff":{},"chats":{},"known_peers":[],"tickets":{},"next_ticket_id":1,"custom_events":{},"countries":{k:default_country_data() for k in COUNTRIES},"citizens":{},"coalitions":{},"wars":[],"builds":{},"global_promos":{},"giveaways":{}}
_cfg_lock = threading.Lock()

def migrate(d):
    for k,v in DEFAULT_CFG.items():
        if k not in d: d[k] = v
    d.setdefault("countries",{})
    for k in COUNTRIES:
        if k not in d["countries"]: d["countries"][k] = default_country_data()
        else:
            base = default_country_data()
            for kk,vv in base.items(): d["countries"][k].setdefault(kk,vv)
            cd = d["countries"][k]
            for cn in get_country_cities(k): cd["cities"].setdefault(cn,{"buildings":[],"pvo":0,"siren":False})
            cd.setdefault("cargo_stock",{t:0 for t in CARGO_TYPES})
    for k in ["citizens","coalitions","builds","global_promos","global_staff","giveaways"]: d.setdefault(k,{})
    d.setdefault("wars",[])
    for ch in d.get("chats",{}).values():
        for k,v in DEFAULT_CHAT.items(): ch.setdefault(k, json.loads(json.dumps(v)))
        muted = ch.get("muted",{})
        for uid,val in list(muted.items()):
            if isinstance(val,(int,float)): muted[uid] = {"until":val,"last_dm":0}
    return d

def load_cfg():
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH,"w",encoding="utf-8") as f: json.dump(DEFAULT_CFG,f,ensure_ascii=False,indent=2)
        return json.loads(json.dumps(DEFAULT_CFG))
    with open(CONFIG_PATH,"r",encoding="utf-8") as f: return migrate(json.load(f))

def save_cfg(d):
    with _cfg_lock:
        with open(CONFIG_PATH,"w",encoding="utf-8") as f: json.dump(d,f,ensure_ascii=False,indent=2)

cfg = load_cfg(); save_cfg(cfg)
print("🔌 VK...")
vk = vk_api.VkApi(token=TOKEN); api = vk.get_api()
try:
    gi = api.groups.getById(group_id=GROUP_ID); print(f"   ✅ {gi[0]['name']}")
except VkApiError as e: print(f"❌ {e}"); sys.exit(1)
longpoll = VkBotLongPoll(vk, group_id=GROUP_ID); print("   ✅ LongPoll")
BOT_ID = -GROUP_ID
# ========== ИМЕНА ==========
_name_cache = {}; _name_lock = threading.Lock()

def prefetch_names(uids):
    uids = [int(u) for u in uids if u and int(u) > 0]; to = []
    with _name_lock:
        for u in uids:
            if u not in _name_cache: to.append(u)
    if not to: return
    try:
        for i in range(0, len(to), 500):
            res = api.users.get(user_ids=",".join(map(str, to[i:i+500])), fields="first_name,last_name")
            with _name_lock:
                for u in res:
                    _name_cache[u["id"]] = f"{u.get('first_name','')} {u.get('last_name','')}".strip() or f"id{u['id']}"
    except: pass

def get_vk_name(uid):
    uid = int(uid)
    with _name_lock:
        if uid in _name_cache: return _name_cache[uid]
    try:
        r = api.users.get(user_ids=uid, fields="first_name,last_name")
        n = f"{r[0].get('first_name','')} {r[0].get('last_name','')}".strip() or f"id{uid}"
    except: n = f"id{uid}"
    with _name_lock: _name_cache[uid] = n
    return n

def mention(uid, peer_id=None):
    uid = int(uid)
    if peer_id and is_chat(peer_id):
        c = get_chat(peer_id)
        if c:
            nick = c.get("nicknames", {}).get(str(uid))
            if nick: return f"[id{uid}|{nick}]"
    return f"[id{uid}|{get_vk_name(uid)}]"

# ========== АНТИДУБЛЬ ==========
_processed = set(); _processed_lock = threading.Lock()

def is_duplicate(peer_id, msg):
    key = (peer_id, msg.get("conversation_message_id") or msg.get("id") or 0, msg.get("from_id"), (msg.get("text") or "")[:40])
    with _processed_lock:
        if key in _processed: return True
        _processed.add(key)
        if len(_processed) > 5000:
            for x in list(_processed)[:2500]: _processed.discard(x)
        return False

# ========== ОТПРАВКА ==========
def send(peer_id, text, reply_to=None):
    kw = {"peer_id": peer_id, "message": text, "random_id": int(time.time()*1000)+random.randint(0,999), "disable_mentions": 0}
    if reply_to:
        try:
            r = int(reply_to)
            if r > 0: kw["reply_to"] = r
        except: pass
    try:
        api.messages.send(**kw)
    except Exception as e:
        if "reply_to" in kw:
            del kw["reply_to"]
            try: api.messages.send(**kw)
            except Exception as e2: print(f"[send] {e2}")
        else:
            print(f"[send] {e}")

def send_dm(uid, text):
    try:
        api.messages.send(peer_id=uid, message=text, random_id=int(time.time()*1000)+random.randint(0,999), disable_mentions=1)
        return True
    except: return False

def log_action(a, text):
    peer = cfg.get("log_peer_id")
    if not peer: return
    try:
        api.messages.send(peer_id=peer, message=f"📝 [id{a}|...] {text}", random_id=int(time.time()*1000))
    except: pass

# ========== ЧАТЫ ==========
def is_chat(p): return p > 2000000000
def chat_id_from_peer(p): return p-2000000000 if p > 2000000000 else None

_admin_cache = {}
WAIT_STAR_TEXT = "⭐ Бот ждёт выдачи звёздочки.\nДайте ему админку: Управление беседой → Участники → назначьте администратором."

def is_bot_admin(peer_id, force=False):
    if not is_chat(peer_id): return False
    now = time.time()
    if not force and peer_id in _admin_cache and now-_admin_cache[peer_id][1] < 30:
        return _admin_cache[peer_id][0]
    try:
        members = api.messages.getConversationMembers(peer_id=peer_id)["items"]
        is_admin = False
        for m in members:
            if m.get("member_id") == BOT_ID:
                is_admin = bool(m.get("is_admin") or m.get("is_owner")); break
    except: is_admin = False
    _admin_cache[peer_id] = (is_admin, now)
    return is_admin

def cache_invalidate_admin(p): _admin_cache.pop(p, None)

def get_chat(peer_id):
    if not is_chat(peer_id): return None
    chats = cfg.setdefault("chats", {}); key = str(peer_id)
    if key not in chats:
        chats[key] = json.loads(json.dumps(DEFAULT_CHAT)); save_cfg(cfg)
    for k, v in DEFAULT_CHAT.items(): chats[key].setdefault(k, json.loads(json.dumps(v)))
    return chats[key]

def track_peer(p):
    if not is_chat(p): return
    kp = cfg.setdefault("known_peers", [])
    if p not in kp:
        kp.append(p); save_cfg(cfg)

def track_message(fid, peer_id, text):
    c = get_chat(peer_id)
    if not c: return
    stats = c.setdefault("user_stats", {}); key = str(fid)
    s = stats.get(key) or {"msg_count": 0, "last_text": "", "last_at": 0}
    s["msg_count"] += 1
    if text: s["last_text"] = text[:120]
    s["last_at"] = int(time.time()); stats[key] = s
    if s["msg_count"] % 10 == 0: add_activation(peer_id, fid, 1)
    if s["msg_count"] % 20 == 0: save_cfg(cfg)

# ========== БАЛАНС ==========
def get_balance(peer_id, uid):
    c = get_chat(peer_id)
    if not c: return 0
    bal = c.setdefault("balance", {}); uid = str(uid)
    if uid not in bal:
        bal[uid] = START_BALANCE; save_cfg(cfg)
    return bal[uid]

def add_balance(peer_id, uid, amount):
    c = get_chat(peer_id)
    if not c: return 0
    bal = c.setdefault("balance", {}); uid = str(uid)
    bal[uid] = max(0, bal.get(uid, START_BALANCE) + amount)
    save_cfg(cfg); return bal[uid]

def is_vip(peer_id, uid):
    c = get_chat(peer_id)
    return c and c.get("subs", {}).get(str(uid), 0) > time.time()

def vip_multiplier(peer_id, uid): return 1 + VIP_BONUS if is_vip(peer_id, uid) else 1.0

# ========== РОЛИ ==========
def get_role_key(uid, peer_id):
    if int(uid) == int(cfg["global_owner"]): return "global"
    grole = cfg.get("global_staff", {}).get(str(uid))
    if not is_chat(peer_id): return grole
    c = get_chat(peer_id)
    if c.get("owner") == uid: return "owner"
    return c.get("staff", {}).get(str(uid)) or grole

def find_role(k, peer_id):
    if not k: return None
    if is_chat(peer_id):
        r = get_chat(peer_id).get("local_roles", {}).get(k)
        if r: return r
    return cfg["roles"].get(k)

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
        return cmd not in ("newrole", "delrole", "createivent", "grole", "removerole", "gstaff") and cmd not in GLOBAL_ONLY
    rk = c.get("staff", {}).get(str(uid)) or cfg.get("global_staff", {}).get(str(uid))
    if not rk: return False
    role = find_role(rk, peer_id)
    return role and cmd in role.get("commands", [])

def find_role_by_input(s, peer_id=None):
    sl = (s or "").lower().strip()
    if not sl: return None
    if is_chat(peer_id):
        for k, v in get_chat(peer_id).get("local_roles", {}).items():
            if k.lower() == sl or v.get("name", "").lower() == sl: return k
    for k in cfg["roles"]:
        if k.lower() == sl: return k
    for k, v in cfg["roles"].items():
        if v.get("name", "").lower() == sl: return k
    if sl.isdigit():
        p = int(sl)
        for k, v in cfg["roles"].items():
            if v.get("priority") == p: return k
    return None

def role_priority(uid, peer_id):
    if uid == int(cfg["global_owner"]): return 999
    if not is_chat(peer_id): return 0
    c = get_chat(peer_id)
    if c.get("owner") == uid: return 100
    rk = c.get("staff", {}).get(str(uid)) or cfg.get("global_staff", {}).get(str(uid))
    r = find_role(rk, peer_id) if rk else None
    return r.get("priority", 0) if r else 0

# ========== ИЗВЛЕЧЕНИЕ ПОЛЬЗОВАТЕЛЯ ==========
def extract_user(text, reply_msg=None):
    m = re.search(r"\[id(\d+)\|", text)
    if m: return int(m.group(1))
    m = re.search(r"@id(\d+)", text)
    if m: return int(m.group(1))
    if reply_msg:
        fid = reply_msg.get("from_id")
        if fid and fid != BOT_ID and fid > 0: return fid
    return None

# ========== УТИЛИТЫ ==========
def kick_user(cid, uid):
    try:
        api.messages.removeChatUser(chat_id=cid, user_id=uid); return True, None
    except Exception as e: return False, str(e)

def delete_msg(mid, cmid=None, peer_id=None):
    if cmid and peer_id:
        try:
            api.messages.delete(conversation_message_ids=cmid, peer_id=peer_id, delete_for_all=1); return True
        except: pass
    if mid and mid > 0:
        try:
            api.messages.delete(message_ids=mid, delete_for_all=1); return True
        except: pass
    return False

def fmt_time(s):
    s = int(s)
    if s < 60: return f"{s} сек"
    if s < 3600: return f"{s//60} мин"
    if s < 86400: return f"{s//3600} ч {s%3600//60} мин"
    return f"{s//86400} д {s%86400//3600} ч"

def fmt_dt(ts): return time.strftime("%d.%m.%Y %H:%M", time.localtime(ts)) if ts else "—"
def fmt_num(n): return f"{int(n):,}".replace(",", " ")

def mute_notify_dm(u, m): send_dm(u, f"🔇 Мут {m} мин.")
def mute_warn_dm(u, r): send_dm(u, f"🔇 В муте. Осталось: {fmt_time(r)}")
def mute_expired_dm(u): send_dm(u, "🔊 Мут снят.")
def get_mute_until(i): return i.get("until", 0) if isinstance(i, dict) else (i or 0)

# ========== СТРАНЫ ==========
def get_country(k): return cfg.get("countries", {}).get(k) if k else None
def country_name(k): return COUNTRIES.get(k, {}).get("name", k)

def get_citizenship(uid): return cfg.get("citizens", {}).get(str(uid))

def set_citizenship(uid, key, rank="гражданин"):
    old = get_citizenship(uid)
    if old and old.get("country") != key:
        oc = get_country(old["country"])
        if oc and uid in oc.get("citizens", []): oc["citizens"].remove(uid)
        if oc and oc.get("president") == uid: oc["president"] = None
        if oc and oc.get("commander") == uid: oc["commander"] = None
    c = cfg.setdefault("citizens", {})
    c[str(uid)] = {"country": key, "rank": rank, "joined_at": int(time.time()), "donated": 0, "hostage_until": 0}
    country = get_country(key)
    if country and uid not in country["citizens"]: country["citizens"].append(uid)
    save_cfg(cfg)

def country_income_mult(uid):
    cit = get_citizenship(uid)
    return RANKS.get(cit.get("rank", "гражданин"), {}).get("bonus_mult", 1.0) if cit else 1.0

def full_vip_mult(peer_id, uid):
    return vip_multiplier(peer_id, uid) * country_income_mult(uid)

def add_activation(peer_id, uid, amount):
    cit = get_citizenship(uid)
    if not cit: return
    c = get_country(cit["country"])
    if not c or c.get("destroyed"): return
    c["activation_points"] = c.get("activation_points", 0) + amount
    save_cfg(cfg)

def country_army_power(k):
    c = get_country(k)
    if not c or c.get("destroyed"): return 0
    base = c.get("army", 0) * (ARMY_LEVEL_MULT ** (c.get("army_level", 1) - 1))
    wp = sum(WEAPONS.get(w, {}).get("power", 0) * cnt for w, cnt in c.get("weapons", {}).items())
    return int(base + wp)

def country_add_history(k, text):
    c = get_country(k)
    if not c: return
    c.setdefault("history", []).insert(0, {"at": int(time.time()), "text": text})
    c["history"] = c["history"][:20]

def broadcast_country(k, text):
    c = get_country(k)
    if not c: return
    for uid in c.get("citizens", []): send_dm(uid, f"🏛 [{country_name(k)}] {text}")
        # ========== ЭКОНОМИКА ==========
def cmd_donate(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠ Только граждане."); return
    if not args or not args[0].isdigit(): send(peer_id, "⚠ /донат <сумма>"); return
    amount = int(args[0])
    if amount <= 0: send(peer_id, "⚠ Сумма > 0"); return
    bal = get_balance(peer_id, uid)
    if bal < amount: send(peer_id, f"❌ У вас {fmt_num(bal)} 💵"); return
    key = cit["country"]; c = get_country(key)
    if c.get("destroyed"): send(peer_id, "❌ Страна уничтожена."); return
    add_balance(peer_id, uid, -amount)
    c["treasury"] = c.get("treasury", 0) + amount
    cfg["citizens"][str(uid)]["donated"] = cfg["citizens"][str(uid)].get("donated", 0) + amount
    c["activation_points"] = c.get("activation_points", 0) + amount // 50000
    save_cfg(cfg)
    send(peer_id, f"💵 +{fmt_num(amount)} в казну {country_name(key)}\n💰 Казна: {fmt_num(c.get('treasury', 0))}")
    broadcast_country(key, f"💵 {mention(uid)}: +{fmt_num(amount)} в казну")

def cmd_transfer(peer_id, uid, args, reply_msg):
    t = extract_user(" ".join(args), reply_msg)
    if not t: send(peer_id, "⚠ /передать @user <сумма>"); return
    if t == uid: send(peer_id, "🤔 Себе нельзя."); return
    amount = None
    for a in args:
        if a.isdigit() and int(a) > 0: amount = int(a); break
    if not amount: send(peer_id, "⚠ Сумма"); return
    bal = get_balance(peer_id, uid)
    if bal < amount: send(peer_id, f"❌ У вас {fmt_num(bal)}"); return
    commission = int(amount * 0.02); final = amount - commission
    add_balance(peer_id, uid, -amount); nb = add_balance(peer_id, t, final)
    save_cfg(cfg)
    send(peer_id, f"💸 {fmt_num(amount)} → {mention(t, peer_id)}\nКомиссия 2%: {fmt_num(commission)}\nПолучено: {fmt_num(final)}")
    send_dm(t, f"💸 +{fmt_num(final)} 💵 от {mention(uid)}")

def cmd_prize(peer_id, uid):
    c = get_chat(peer_id); last = c.get("last_prize", {}); now = int(time.time()); k = str(uid)
    el = now - last.get(k, 0)
    if el < PRIZE_COOLDOWN:
        w = PRIZE_COOLDOWN - el; send(peer_id, f"⏳ Через {w//3600}ч {w%3600//60}м"); return
    amt = int(random.randint(PRIZE_MIN, PRIZE_MAX) * full_vip_mult(peer_id, uid))
    nb = add_balance(peer_id, uid, amt)
    last[k] = now; c["last_prize"] = last
    add_activation(peer_id, uid, 3); save_cfg(cfg)
    send(peer_id, f"🎁 +{fmt_num(amt)}! (+3 очка)\nБаланс: {fmt_num(nb)}")

def cmd_sub(peer_id, uid):
    c = get_chat(peer_id)
    if is_vip(peer_id, uid): send(peer_id, "👑 VIP активен"); return
    try:
        res = api.groups.isMember(group_id=GROUP_ID, user_id=uid)
        sub = (len(res) > 0 and res[0].get("member") == 1) if isinstance(res, list) else bool(res)
    except: sub = False
    if not sub: send(peer_id, f"❌ Подпишитесь: https://vk.com/club{GROUP_ID}"); return
    if c.get("subs", {}).get(str(uid), 0) > 0: send(peer_id, "⚠ Уже получали."); return
    until = int(time.time()) + VIP_DURATION
    c.setdefault("subs", {})[str(uid)] = until
    nb = add_balance(peer_id, uid, VIP_PRICE); save_cfg(cfg)
    send(peer_id, f"👑 VIP на 30 дней!\n💰 +{fmt_num(VIP_PRICE)}")

# ========== БИЗНЕСЫ ==========
def cmd_buybiz(peer_id, uid, args):
    c = get_chat(peer_id)
    if not args:
        lines = ["💼 Бизнесы:"]
        for k, v in BUSINESSES.items():
            lines.append(f"{v['emoji']} {k} — {fmt_num(v['price'])} ({fmt_num(v['income'])}/час)")
        send(peer_id, "\n".join(lines)); return
    name = args[0].lower()
    if name not in BUSINESSES: send(peer_id, "⚠ Нет."); return
    biz = BUSINESSES[name]
    if get_balance(peer_id, uid) < biz["price"]: send(peer_id, f"❌ Нужно {fmt_num(biz['price'])}"); return
    my = c.setdefault("businesses", {}).setdefault(str(uid), {})
    if name in my: send(peer_id, "⚠ Уже."); return
    my[name] = {"bought_at": int(time.time()), "last_collect": int(time.time())}
    add_balance(peer_id, uid, -biz["price"]); save_cfg(cfg)
    send(peer_id, f"✅ {biz['emoji']} {name}")

def cmd_mybiz(peer_id, uid):
    c = get_chat(peer_id); my = c.get("businesses", {}).get(str(uid), {})
    if not my: send(peer_id, "📭 Нет."); return
    lines = ["💼 Бизнесы:"]; total = 0
    for n, info in my.items():
        b = BUSINESSES.get(n)
        if not b: continue
        h = min((time.time() - info["last_collect"]) / 3600, 24)
        inc = int(b["income"] * h * full_vip_mult(peer_id, uid))
        lines.append(f"{b['emoji']} {n} — {fmt_num(b['income'])}/час | {fmt_num(inc)}")
        total += inc
    lines.append(f"\n💰 /collect — {fmt_num(total)}")
    send(peer_id, "\n".join(lines))

def cmd_collect(peer_id, uid):
    c = get_chat(peer_id); my = c.get("businesses", {}).get(str(uid), {})
    if not my: send(peer_id, "❌ Нет."); return
    now = int(time.time()); total = 0
    for n, info in my.items():
        b = BUSINESSES.get(n)
        if not b: continue
        h = min((now - info["last_collect"]) / 3600, 24)
        if h < 0.01: continue
        total += int(b["income"] * h * full_vip_mult(peer_id, uid))
        info["last_collect"] = now
    if total > 0: add_activation(peer_id, uid, total // 10000)
    save_cfg(cfg)
    if total == 0: send(peer_id, "⏳ Мало."); return
    nb = add_balance(peer_id, uid, total)
    send(peer_id, f"💰 +{fmt_num(total)} (+{total//10000} очков)")

def cmd_sellbiz(peer_id, uid, args):
    c = get_chat(peer_id); my = c.get("businesses", {}).get(str(uid), {})
    if not args: send(peer_id, "⚠ /продатьбизнес <название>"); return
    name = args[0].lower()
    if name not in my: send(peer_id, "❌ Нет такого."); return
    b = BUSINESSES.get(name)
    if not b: return
    price = int(b["price"] * 0.7)
    del my[name]; add_balance(peer_id, uid, price); save_cfg(cfg)
    send(peer_id, f"💸 {b['emoji']} {name} продан за {fmt_num(price)} 💵 (70%)")

def cmd_bizlist(peer_id, uid):
    lines = ["💼 Все бизнесы:"]
    for k, v in BUSINESSES.items():
        lines.append(f"{v['emoji']} {k.title()} — {fmt_num(v['price'])} 💵 ({fmt_num(v['income'])}/ч)")
    send(peer_id, "\n".join(lines))

# ========== ПРОМОКОДЫ ==========
def cmd_promo(peer_id, uid, args):
    if not args: send(peer_id, "⚠ /promo <код>"); return
    code = args[0].upper(); c = get_chat(peer_id)
    promo = c.get("promos", {}).get(code) or cfg.get("global_promos", {}).get(code)
    if not promo: send(peer_id, "❌ Не найден."); return
    used = c.setdefault("promos_used", {}).setdefault(str(uid), [])
    if code in used: send(peer_id, "⚠ Использован."); return
    if promo.get("uses_left", 0) <= 0: send(peer_id, "⚠ Исчерпан."); return
    nb = add_balance(peer_id, uid, promo["reward"]); promo["uses_left"] -= 1
    used.append(code); save_cfg(cfg)
    send(peer_id, f"🎟️ +{fmt_num(promo['reward'])}\nБаланс: {fmt_num(nb)}")

def cmd_createpromo(peer_id, uid, args):
    c = get_chat(peer_id)
    if len(args) < 2 or not args[1].isdigit(): send(peer_id, "⚠ /createpromo <код> <награда>"); return
    code = args[0].upper(); rw = int(args[1])
    if not 100 <= rw <= 1000000: send(peer_id, "⚠ 100-1 000 000"); return
    if code in c.get("promos", {}): send(peer_id, "⚠ Есть."); return
    c.setdefault("promos", {})[code] = {"reward": rw, "created_by": uid, "created_at": int(time.time()), "uses_left": 100}
    save_cfg(cfg); send(peer_id, f"✅ Промокод {code}")

def cmd_promolist(peer_id, uid):
    c = get_chat(peer_id); promos = c.get("promos", {}); glob = cfg.get("global_promos", {})
    if not promos and not glob: send(peer_id, "📭 Нет."); return
    lines = ["🎟️ Промокоды:"]
    for code, p in promos.items(): lines.append(f"• {code} — {fmt_num(p['reward'])}")
    for code, p in glob.items(): lines.append(f"🌐 {code} — {fmt_num(p['reward'])}")
    send(peer_id, "\n".join(lines))

# ========== ТОП ==========
def cmd_top_ext(peer_id, args):
    if not is_chat(peer_id): send(peer_id, "❌"); return
    c = get_chat(peer_id); mode = args[0].lower() if args else "баланс"
    if mode in ("баланс", "balance"):
        data = [(k, v) for k, v in c.get("balance", {}).items() if v > 0]; title = "💰 Топ балансов"
        data.sort(key=lambda x: -x[1])
    elif mode in ("сообщения", "msg"):
        data = [(k, v.get("msg_count", 0)) for k, v in c.get("user_stats", {}).items()]; title = "📝 Топ сообщений"
        data.sort(key=lambda x: -x[1])
    elif mode in ("бизнес", "biz"):
        data = [(k, len(v)) for k, v in c.get("businesses", {}).items()]; title = "💼 Топ бизнесов"
        data.sort(key=lambda x: -x[1])
    elif mode in ("варны", "warns"):
        data = [(k, v) for k, v in c.get("warns", {}).items() if v > 0]; title = "⚠️ Топ варнов"
        data.sort(key=lambda x: -x[1])
    else:
        send(peer_id, "⚠ /топ [баланс|сообщения|бизнес|варны]"); return
    if not data: send(peer_id, "📭"); return
    prefetch_names([int(k) for k, _ in data[:10]])
    lines = [title, ""]; medals = ["🥇", "🥈", "🥉"]
    for i, (uid, v) in enumerate(data[:10]):
        m = medals[i] if i < 3 else f"{i+1}."
        lines.append(f"{m} {mention(uid, peer_id)} — {fmt_num(v)}")
    send(peer_id, "\n".join(lines))

def cmd_wipe(peer_id, uid):
    if not is_chat(peer_id): send(peer_id, "❌"); return
    c = get_chat(peer_id)
    if uid != int(cfg["global_owner"]) and c.get("owner") != uid: send(peer_id, "⛔"); return
    c["balance"] = {}; save_cfg(cfg); send(peer_id, "🧹 Вайп!")

def cmd_wipe_all(peer_id, uid):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    for ch in cfg.get("chats", {}).values(): ch["balance"] = {}
    save_cfg(cfg); send(peer_id, "🧹 ГЛОБАЛЬНЫЙ ВАЙП!")

# ========== КАСТОМНЫЕ АЛИАСЫ ==========
def cmd_cmd(peer_id, uid, args):
    c = get_chat(peer_id)
    if len(args) < 2:
        a = c.get("custom_cmds", {})
        if not a: send(peer_id, "⚙️ /cmd <к> <имя>"); return
        send(peer_id, "\n".join(f"• /{k} → /{v}" for k, v in a.items())); return
    if args[0].lower() == "reset":
        k = args[1].lower().lstrip("/"); rem = c.get("custom_cmds", {}).pop(k, None); save_cfg(cfg)
        send(peer_id, "✅" if rem else "⚠"); return
    orig = args[0].lower().lstrip("/"); alias = args[1].lower().lstrip("/")
    if orig not in ALL_COMMANDS: send(peer_id, f"⚠ /{orig} нет."); return
    if alias in ALL_COMMANDS: send(peer_id, f"⚠ /{alias} занято."); return
    c.setdefault("custom_cmds", {})[alias] = orig; save_cfg(cfg)
    send(peer_id, f"✅ /{alias} = /{orig}")

# ========== СТРАНЫ ==========
def cmd_countries(peer_id, uid):
    lines = ["🌍 Страны:", ""]
    for k, c in COUNTRIES.items():
        country = get_country(k) or {}
        if country.get("destroyed"):
            cap = country.get("captured_by")
            lines.append(f"☠️ {c['name']} — УНИЧТОЖЕНА ({country_name(cap) if cap else '?'})")
            continue
        pres = country.get("president")
        lines.append(f"{c['name']} | 👑 {mention(pres, peer_id) if pres else '❌'} | ⚔️ {fmt_num(country.get('army', 0))} | 🏙 {country.get('cities_unlocked', 3)}/40")
    send(peer_id, "\n".join(lines))

def cmd_citizenship(peer_id, uid, args):
    if not args:
        cit = get_citizenship(uid)
        if cit:
            cn = country_name(cit["country"]); rk = RANKS.get(cit["rank"], {}).get("name", cit["rank"])
            host = "\n🔒 ЗАЛОЖНИК!" if cit.get("hostage_until", 0) > time.time() else ""
            send(peer_id, f"🌍 Гражданин {cn}\n🎖️ {rk}{host}"); return
        lines = ["🌍 Страны:"]
        for k, c in COUNTRIES.items():
            country = get_country(k)
            mark = " ☠️" if country and country.get("destroyed") else ""
            lines.append(f"• {k} — {c['name']}{mark}")
        send(peer_id, "\n".join(lines)); return
    key = args[0].lower()
    if key not in COUNTRIES: send(peer_id, "❌"); return
    c = get_country(key)
    if c.get("destroyed"): send(peer_id, "❌ Уничтожена."); return
    cit = get_citizenship(uid)
    if cit and cit["country"] == key: send(peer_id, "ℹ Уже гражданин."); return
    set_citizenship(uid, key)
    c["activation_points"] = c.get("activation_points", 0) + 5; save_cfg(cfg)
    send(peer_id, f"🎉 Гражданин {country_name(key)}! (+5 очков)")
    broadcast_country(key, f"👋 {mention(uid)}")

def cmd_passport(peer_id, uid, args, reply_msg):
    target = extract_user(" ".join(args), reply_msg) or uid
    cit = get_citizenship(target)
    if not cit: send(peer_id, "❌ Не гражданин."); return
    c = get_country(cit["country"]) or {}
    cn = country_name(cit["country"]); rk = RANKS.get(cit["rank"], {}).get("name", cit["rank"])
    bal = get_balance(peer_id, target); prefetch_names([target])
    lines = ["📔 ПАСПОРТ", f"👤 {mention(target, peer_id)}", f"🌍 {cn}", f"🎖️ {rk}", f"💰 {fmt_num(bal)}",
             f"📅 {fmt_dt(cit['joined_at'])}", f"💵 Вложено: {fmt_num(cit.get('donated', 0))}"]
    if cit.get("hostage_until", 0) > time.time(): lines.append(f"🔒 до {fmt_dt(cit['hostage_until'])}")
    lines.extend(["", f"👑 {mention(c.get('president'), peer_id) if c.get('president') else '—'}",
                  f"🎖️ {mention(c.get('commander'), peer_id) if c.get('commander') else '—'}",
                  f"👥 {len(c.get('citizens', []))}", f"💰 {fmt_num(c.get('treasury', 0))} 💵",
                  f"⚔️ {fmt_num(c.get('army', 0))}"])
    send(peer_id, "\n".join(lines))

def cmd_country_info(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not args and not cit: send(peer_id, "⚠ /страна <название>"); return
    key = (args[0].lower() if args else cit["country"])
    if key not in COUNTRIES: send(peer_id, "❌"); return
    c = get_country(key) or {}
    if c.get("destroyed"):
        cap = c.get("captured_by")
        send(peer_id, f"☠️ {country_name(key)} УНИЧТОЖЕНА\n💀 {country_name(cap) if cap else '?'}"); return
    send(peer_id, f"🏛 {country_name(key)}\n👑 {mention(c.get('president'), peer_id) if c.get('president') else '—'}\n"
                  f"🎖️ {mention(c.get('commander'), peer_id) if c.get('commander') else '—'}\n"
                  f"👥 {len(c.get('citizens', []))}\n⚔️ {fmt_num(c.get('army', 0))} (ур.{c.get('army_level', 1)})\n"
                  f"💰 {fmt_num(c.get('treasury', 0))}\n🏙 {c.get('cities_unlocked', 3)}/40 | 🎯 {c.get('activation_points', 0)}\n"
                  f"🤝 {c.get('coalition') or '—'}\n🌉 {'открыта' if c.get('borders_open', True) else 'закрыта'}\n☢️ {c.get('nukes', 0)}")

def cmd_citizens(peer_id, uid, args):
    if not args:
        cit = get_citizenship(uid)
        if not cit: send(peer_id, "⚠ /граждане <страна>"); return
        key = cit["country"]
    else: key = args[0].lower()
    if key not in COUNTRIES: send(peer_id, "❌"); return
    c = get_country(key) or {}; uids = c.get("citizens", [])
    if not uids: send(peer_id, "📭 Нет."); return
    prefetch_names(uids[:30])
    lines = [f"👥 {country_name(key)} ({len(uids)}):"]
    for u in uids[:30]:
        u_cit = get_citizenship(u) or {}
        rk = RANKS.get(u_cit.get("rank", "гражданин"), {}).get("name", "👤")
        lines.append(f"• {mention(u, peer_id)} — {rk}")
    send(peer_id, "\n".join(lines))

def cmd_cities(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    unlocked = c.get("cities_unlocked", 3); cities = get_country_cities(key)
    lines = [f"🏙 Города {country_name(key)} — {unlocked}/40", ""]
    for i, city in enumerate(cities, 1):
        if i <= unlocked:
            cd = c.get("cities", {}).get(city, {})
            bc = len(cd.get("buildings", [])); sr = " 🚨" if cd.get("siren") else ""
            lines.append(f"{i}. ✅ {city} — {bc}{sr}")
        else: lines.append(f"{i}. 🔒 {city}")
    send(peer_id, "\n".join(lines))

def cmd_treasury(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if args and args[0].lower() in ("история", "history"):
        h = c.get("history", [])[:10]
        if not h: send(peer_id, "📭"); return
        send(peer_id, "📜 История:\n" + "\n".join(f"• {fmt_dt(i['at'])} — {i['text']}" for i in h)); return
    send(peer_id, f"💰 Казна {country_name(key)}\nБаланс: {fmt_num(c.get('treasury', 0))} 💵\nНалог: {c.get('tax', 5)}%\nГраждан: {len(c.get('citizens', []))}\n\n💵 /донат")

def cmd_government(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    gov = c.get("government", {})
    lines = [f"🏛 Правительство {country_name(key)}", ""]
    pres = c.get("president"); com = c.get("commander")
    lines.append(f"👑 {mention(pres, peer_id) if pres else '—'}")
    lines.append(f"🎖️ {mention(com, peer_id) if com else '—'}")
    for pos in GOV_POSITIONS:
        if pos in ("президент", "главнокомандующий"): continue
        u = gov.get(pos); lines.append(f"• {pos.title()}: {mention(u, peer_id) if u else '—'}")
    send(peer_id, "\n".join(lines))

def cmd_positions(peer_id, uid, args):
    send(peer_id, "🏛 Должности:\n" + "\n".join(f"• {p.title()}" for p in GOV_POSITIONS))

def cmd_army(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if args and args[0].lower() in ("выйти", "leave"):
        c["army"] = max(0, c.get("army", 0) - 1000); save_cfg(cfg)
        send(peer_id, "🎖️ Уволились (-1000)"); return
    weapons = c.get("weapons", {})
    w_str = "\n".join(f"  {WEAPONS[w]['emoji']} {w.title()}: {cnt}" for w, cnt in weapons.items() if cnt)
    send(peer_id, f"⚔️ Армия {country_name(key)}\n👥 {fmt_num(c.get('army', 0))}\n🎖️ Ур. {c.get('army_level', 1)}/{ARMY_LEVEL_MAX}\n🎯 {fmt_num(country_army_power(key))}\n☢️ {c.get('nukes', 0)}\n\n🔫 Техника:\n{w_str if w_str else '(нет)'}")

def cmd_elections(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    el = c.get("elections", {})
    if not el.get("active"):
        pres = c.get("president")
        send(peer_id, f"🗳️ Выборы неактивны\n👑 {mention(pres, peer_id) if pres else '—'}\n/выдвинуться"); return
    cands = el.get("candidates", []); votes = el.get("votes", {})
    lines = [f"🗳️ ВЫБОРЫ {country_name(key)}", ""]
    for i, cand in enumerate(cands, 1):
        vc = sum(1 for v in votes.values() if v == cand)
        lines.append(f"{i}. {mention(cand, peer_id)} — {vc}")
    lines.append("\n/голос <номер>"); send(peer_id, "\n".join(lines))

def cmd_run_for_president(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    el = c.setdefault("elections", {"candidates": [], "votes": {}, "ends_at": 0, "active": False})
    if el["active"]: send(peer_id, "⚠ Идут."); return
    if uid in el["candidates"]: send(peer_id, "⚠ Уже."); return
    el["candidates"].append(uid)
    if len(el["candidates"]) >= 2 and not el["active"]:
        el["active"] = True; el["ends_at"] = int(time.time()) + 3600; el["votes"] = {}
        broadcast_country(key, "🗳️ ВЫБОРЫ!")
    save_cfg(cfg); send(peer_id, "✅ Выдвинулись!")

def cmd_vote(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    el = c.get("elections", {})
    if not el.get("active"): send(peer_id, "⚠"); return
    if uid in el.get("votes", {}): send(peer_id, "⚠ Уже голосовали."); return
    if not args or not args[0].isdigit(): send(peer_id, "⚠ /голос <номер>"); return
    idx = int(args[0]) - 1; cands = el.get("candidates", [])
    if not 0 <= idx < len(cands): send(peer_id, "⚠"); return
    el["votes"][str(uid)] = cands[idx]; add_activation(peer_id, uid, 2); save_cfg(cfg)
    send(peer_id, f"🗳️ Голос за {mention(cands[idx], peer_id)}! (+2 очка)")

def cmd_tax(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if not args or not args[0].isdigit(): send(peer_id, f"⚠ Сейчас: {c.get('tax', 5)}%"); return
    t = int(args[0])
    if not 1 <= t <= 20: send(peer_id, "⚠ 1-20"); return
    c["tax"] = t; save_cfg(cfg); send(peer_id, f"💰 Налог: {t}%")

def cmd_company(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    comp = c.get("companies", {}).get(str(uid))
    if not comp: send(peer_id, "📭 /регистрация ООО <название>"); return
    send(peer_id, f"🏢 {comp.get('name')}\n🌍 {country_name(key)}\n💰 Налог {c.get('tax', 5)}%")

def cmd_register_company(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if args and args[0].lower() in ("ооо", "ooo"): args = args[1:]
    if not args: send(peer_id, "⚠ /регистрация ООО <название>"); return
    if get_balance(peer_id, uid) < 100000: send(peer_id, "❌ Нужно 100 000"); return
    add_balance(peer_id, uid, -100000)
    c.setdefault("companies", {})[str(uid)] = {"name": " ".join(args), "at": int(time.time())}
    save_cfg(cfg); send(peer_id, "🏢 Компания зарегистрирована!")

def cmd_rename_company(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    comp = c.get("companies", {}).get(str(uid))
    if not comp: send(peer_id, "⚠ Нет."); return
    if not args: send(peer_id, "⚠"); return
    comp["name"] = " ".join(args); save_cfg(cfg)
    send(peer_id, f"✅ → «{comp['name']}»")

def cmd_show_improve(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    unlocked = c.get("cities_unlocked", 3)
    if unlocked >= 40: send(peer_id, "✅ Все 40."); return
    np = IMPROVE_BASE_POINTS * unlocked; nm = IMPROVE_BASE_COST * unlocked
    hp = c.get("activation_points", 0); hm = c.get("treasury", 0)
    nxt = get_country_cities(key)[unlocked]
    send(peer_id, f"🏙 Улучшение {country_name(key)}\nСледующий: {nxt} ({unlocked+1}/40)\n🎯 Очки: {hp}/{np}\n💰 {fmt_num(hm)}/{fmt_num(nm)}\n\n/очки /улучшитьстрану")

def cmd_show_points(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    c = get_country(cit["country"]); pts = c.get("activation_points", 0)
    unlocked = c.get("cities_unlocked", 3); need = IMPROVE_BASE_POINTS * unlocked
    send(peer_id, f"🎯 Очки актива\n🌍 {country_name(cit['country'])}\n💰 {pts}\n🏙 До города: {pts}/{need}\n\n+5 /выполнитьзадание\n+3 /приз\n+1 /дуэль\n+2 /голос\n+5 /построить\n+50 /захват\n+1 /10 сообщений")

def cmd_improve_country(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    unlocked = c.get("cities_unlocked", 3)
    if unlocked >= 40: send(peer_id, "⚠ Максимум."); return
    cost = IMPROVE_BASE_COST * unlocked; need = IMPROVE_BASE_POINTS * unlocked
    if c.get("treasury", 0) < cost: send(peer_id, f"❌ {fmt_num(cost)} 💵"); return
    if c.get("activation_points", 0) < need: send(peer_id, f"❌ {need} очков"); return
    c["treasury"] -= cost; c["activation_points"] -= need; c["cities_unlocked"] = unlocked + 1
    new_city = get_country_cities(key)[unlocked]
    c.setdefault("cities", {})[new_city] = {"buildings": [], "pvo": 0, "siren": False}
    save_cfg(cfg); broadcast_country(key, f"🏙 Открыт город: {new_city}!")

def cmd_buildings(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if not args: send(peer_id, "⚠ /постройки <город>"); return
    city = " ".join(args).title(); cities = get_country_cities(key)
    cm = next((x for x in cities if x.lower() == city.lower()), None)
    if not cm: send(peer_id, "❌"); return
    b = c.get("cities", {}).get(cm, {}).get("buildings", [])
    if not b: send(peer_id, f"🏙 {cm}: нет."); return
    send(peer_id, f"🏙 {cm}:\n" + "\n".join(f"  {BUILDINGS.get(x, {}).get('emoji', '🏢')} {x.title()}" for x in b))

def cmd_build_obj(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if len(args) < 2: send(peer_id, "⚠ /построить <объект> <город>"); return
    b_name = args[0].lower()
    if b_name not in BUILDINGS: send(peer_id, f"⚠ Есть: {', '.join(BUILDINGS.keys())}"); return
    city_name = " ".join(args[1:]).title(); cities = get_country_cities(key)
    cm = next((x for x in cities if x.lower() == city_name.lower()), None)
    if not cm: send(peer_id, "❌"); return
    if cities.index(cm) >= c.get("cities_unlocked", 3): send(peer_id, "❌"); return
    bi = BUILDINGS[b_name]
    if c.get("treasury", 0) < bi["cost"]: send(peer_id, f"❌ {fmt_num(bi['cost'])}"); return
    bl = c.setdefault("cities", {}).setdefault(cm, {}).setdefault("buildings", [])
    if b_name in bl: send(peer_id, "⚠ Уже."); return
    c["treasury"] -= bi["cost"]; bl.append(b_name)
    if b_name == "казарма": c["army"] = c.get("army", 0) + 5000
    add_activation(peer_id, uid, 5); save_cfg(cfg)
    send(peer_id, f"✅ {bi['emoji']} {b_name.title()} в {cm}! +5 очков")

def cmd_state_project(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if len(args) < 2: send(peer_id, "⚠ /госпроект <тип> <название>"); return
    ptype, pname = args[0].lower(), " ".join(args[1:])
    c.setdefault("projects", []).append({"type": ptype, "name": pname, "at": int(time.time())})
    save_cfg(cfg); broadcast_country(key, f"🏛 Госпроект «{pname}»")

def cmd_armament(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if not args or not args[0].isdigit(): send(peer_id, "⚠ /вооружение <сумма>"); return
    amount = int(args[0])
    if c.get("treasury", 0) < amount: send(peer_id, "❌"); return
    c["treasury"] -= amount; bought = []; rem = amount
    for wk, wi in sorted(WEAPONS.items(), key=lambda x: -x[1]["cost"]):
        if rem < wi["cost"]: continue
        cnt = rem // wi["cost"]
        c.setdefault("weapons", {})[wk] = c.get("weapons", {}).get(wk, 0) + cnt
        bought.append(f"{wi['emoji']} {wk.title()} ×{cnt}"); rem -= cnt * wi["cost"]
    save_cfg(cfg); send(peer_id, "🛒 Закупка:\n" + ("\n".join(bought) if bought else "Ничего."))
    # ========== ГРАНИЦЫ / ВИЗЫ ==========
def cmd_border(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key)
    if c.get("president") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if not args:
        closed = c.get("border_closed_to", [])
        state = "🔓 ОТКРЫТА" if c.get("borders_open", True) else "🔒 ЗАКРЫТА"
        lines = [f"🌉 Граница {country_name(key)}: {state}"]
        if closed: lines.append("🚫 Закрыта для: " + ", ".join(country_name(k) for k in closed))
        lines.append("\n/граница открыть|закрыть [страна]")
        send(peer_id, "\n".join(lines)); return
    sub = args[0].lower()
    if sub == "открыть":
        if len(args) >= 2:
            target = args[1].lower()
            if target not in COUNTRIES: send(peer_id, "❌"); return
            closed = c.setdefault("border_closed_to", [])
            if target in closed: closed.remove(target)
            save_cfg(cfg); send(peer_id, f"✅ Открыта для {country_name(target)}")
            broadcast_country(target, f"🌉 {country_name(key)} открыла границу!")
        else:
            c["borders_open"] = True; c["border_closed_to"] = []; save_cfg(cfg)
            send(peer_id, "✅ Граница открыта"); broadcast_country(key, "🌉 Граница открыта!")
    elif sub == "закрыть":
        if len(args) >= 2:
            target = args[1].lower()
            if target not in COUNTRIES: send(peer_id, "❌"); return
            closed = c.setdefault("border_closed_to", [])
            if target not in closed: closed.append(target)
            save_cfg(cfg); send(peer_id, f"🚫 Закрыта для {country_name(target)}")
            broadcast_country(target, f"🚫 {country_name(key)} закрыла границу!")
        else:
            c["borders_open"] = False; save_cfg(cfg)
            send(peer_id, "🚫 Граница закрыта"); broadcast_country(key, "🚫 Граница закрыта!")
    else:
        send(peer_id, "⚠ /граница открыть|закрыть [страна]")

def cmd_visa(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key)
    if c.get("president") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if not args:
        visas = c.get("visas", [])
        if not visas: send(peer_id, "📭 Нет виз."); return
        prefetch_names(visas[:30])
        send(peer_id, "🛂 Виза:\n" + "\n".join(f"• {mention(u, peer_id)}" for u in visas[:30])); return
    sub = args[0].lower()
    if sub == "выдать":
        t = extract_user(" ".join(args))
        if not t: send(peer_id, "⚠"); return
        visas = c.setdefault("visas", [])
        if t in visas: send(peer_id, "⚠ Уже есть."); return
        visas.append(t); save_cfg(cfg)
        send(peer_id, f"🛂 {mention(t, peer_id)} виза выдана")
        send_dm(t, f"🛂 Виза {country_name(key)}")
    elif sub == "забрать":
        t = extract_user(" ".join(args))
        if not t: send(peer_id, "⚠"); return
        visas = c.setdefault("visas", [])
        if t in visas: visas.remove(t); save_cfg(cfg)
        send(peer_id, f"🚫 {mention(t, peer_id)} виза отозвана")
    else:
        send(peer_id, "⚠ /виза выдать|забрать @user")

# ========== ТРАНСПОРТ / СКЛАД / ПЕРЕВОЗКИ ==========
def cmd_transport_buy(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key)
    if c.get("president") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if not args:
        lines = ["🚚 Транспорт:"]
        for t, i in TRANSPORTS.items():
            have = c.get("transports", {}).get(t, 0)
            lines.append(f"{i['emoji']} {t.title()} — {fmt_num(i['cost'])} 💵 ({fmt_num(i['capacity'])}) | у вас: {have}")
        lines.append("\n/транспорт купить <тип>"); send(peer_id, "\n".join(lines)); return
    if args[0].lower() == "купить" and len(args) >= 2:
        t = args[1].lower()
        if t not in TRANSPORTS: send(peer_id, f"⚠ Есть: {', '.join(TRANSPORTS.keys())}"); return
        cost = TRANSPORTS[t]["cost"]
        if c.get("treasury", 0) < cost: send(peer_id, f"❌ Нужно {fmt_num(cost)} 💵"); return
        c["treasury"] -= cost
        c.setdefault("transports", {})[t] = c.get("transports", {}).get(t, 0) + 1; save_cfg(cfg)
        send(peer_id, f"✅ {TRANSPORTS[t]['emoji']} {t.title()} куплен!")
    else:
        send(peer_id, "⚠ /транспорт купить <тип>")

def cmd_stock_add(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key)
    if c.get("president") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if len(args) < 2 or not args[1].isdigit():
        send(peer_id, "⚠ /склад <товар> <кол>\nТовары: " + ", ".join(CARGO_TYPES.keys())); return
    cargo = args[0].lower()
    if cargo not in CARGO_TYPES: send(peer_id, "❌"); return
    amount = int(args[1]); cost = CARGO_TYPES[cargo]["price"] * amount
    if c.get("treasury", 0) < cost: send(peer_id, f"❌ Нужно {fmt_num(cost)} 💵"); return
    c["treasury"] -= cost
    c.setdefault("cargo_stock", {})[cargo] = c.get("cargo_stock", {}).get(cargo, 0) + amount
    save_cfg(cfg); send(peer_id, f"✅ {amount} {cargo} на склад ({fmt_num(cost)} 💵)")

def cmd_stock_view(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key)
    stock = c.get("cargo_stock", {}); transports = c.get("transports", {}); in_transit = c.get("cargo_in_transit", [])
    lines = [f"📦 Склад {country_name(key)}", ""]
    for t, i in CARGO_TYPES.items(): lines.append(f"{i['emoji']} {t.title()}: {fmt_num(stock.get(t, 0))}")
    lines.append(""); lines.append("🚚 Транспорт:")
    for t, i in TRANSPORTS.items():
        cnt = transports.get(t, 0)
        if cnt: lines.append(f"  {i['emoji']} {t.title()}: {cnt}")
    if not any(transports.values()): lines.append("  (нет)")
    if in_transit:
        lines.append(f"\n📦 В пути: {len(in_transit)}")
        for t in in_transit[:5]:
            left = int(t["arrives_at"] - time.time())
            if left > 0: lines.append(f"  {t['cargo']} x{t['amount']} → {country_name(t['to'])} | {fmt_time(left)}")
    send(peer_id, "\n".join(lines))

def cmd_transport_cargo(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key)
    if c.get("president") != uid and c.get("commander") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if len(args) < 4: send(peer_id, "⚠ /перевозка <страна> <товар> <кол> <транспорт>"); return
    target = args[0].lower()
    if target not in COUNTRIES: send(peer_id, "❌"); return
    if target == key: send(peer_id, "⚠"); return
    cargo = args[1].lower()
    if cargo not in CARGO_TYPES: send(peer_id, "❌"); return
    if not args[2].isdigit(): send(peer_id, "⚠"); return
    amount = int(args[2]); transport = args[3].lower()
    if transport not in TRANSPORTS: send(peer_id, "❌"); return
    tc = get_country(target)
    if not tc or tc.get("destroyed"): send(peer_id, "⚠"); return
    if key in tc.get("border_closed_to", []) or not tc.get("borders_open", True):
        send(peer_id, f"🚫 {country_name(target)} закрыла границу."); return
    if c.get("transports", {}).get(transport, 0) < 1:
        send(peer_id, f"❌ Нет {transport}. /транспорт купить {transport}"); return
    if amount > TRANSPORTS[transport]["capacity"]:
        send(peer_id, f"⚠ Максимум {fmt_num(TRANSPORTS[transport]['capacity'])}"); return
    if cargo != "деньги" and c.get("cargo_stock", {}).get(cargo, 0) < amount:
        send(peer_id, f"❌ Мало {cargo}"); return
    if cargo != "деньги": c["cargo_stock"][cargo] -= amount
    total = CARGO_TYPES[cargo]["price"] * amount
    customs = int(total * CUSTOMS_RATE)
    c["treasury"] = max(0, c.get("treasury", 0) - customs)
    tc["treasury"] = tc.get("treasury", 0) + customs
    arrives = int(time.time()) + TRANSPORTS[transport]["speed"]
    c.setdefault("cargo_in_transit", []).append({"to": target, "cargo": cargo, "amount": amount, "transport": transport, "arrives_at": arrives, "customs": customs, "sender": key})
    save_cfg(cfg)
    send(peer_id, f"🚚 {amount} {cargo} → {country_name(target)}\n{TRANSPORTS[transport]['emoji']} {transport.title()}\nПошлина: {fmt_num(customs)} 💵\n⏱ {fmt_time(TRANSPORTS[transport]['speed'])}")
    broadcast_country(target, f"🚚 В пути {amount} {cargo} от {country_name(key)}")

def cargo_ticker():
    while True:
        time.sleep(10)
        try:
            now = time.time(); ch = False
            for key, c in cfg.get("countries", {}).items():
                transit = c.get("cargo_in_transit", [])
                for t in list(transit):
                    if t["arrives_at"] <= now:
                        transit.remove(t); tc = get_country(t["to"])
                        if tc and not tc.get("destroyed"):
                            tc.setdefault("cargo_stock", {})[t["cargo"]] = tc["cargo_stock"].get(t["cargo"], 0) + t["amount"]
                            broadcast_country(t["to"], f"📦 +{t['amount']} {t['cargo']}")
                            broadcast_country(key, f"📦 Доставлено в {country_name(t['to'])}")
                        ch = True
            if ch: save_cfg(cfg)
        except Exception as e: print(f"[cargo] {e}")

threading.Thread(target=cargo_ticker, daemon=True).start()

def cmd_smuggle(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key)
    if c.get("president") != uid and c.get("commander") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if len(args) < 3: send(peer_id, f"⚠ /контрабанда <страна> <товар> <кол>\nШанс: {int(SMUGGLE_CHANCE*100)}%"); return
    target = args[0].lower()
    if target not in COUNTRIES: send(peer_id, "❌"); return
    cargo = args[1].lower()
    if cargo not in CARGO_TYPES: send(peer_id, "❌"); return
    if not args[2].isdigit(): send(peer_id, "⚠"); return
    amount = int(args[2])
    if cargo != "деньги" and c.get("cargo_stock", {}).get(cargo, 0) < amount: send(peer_id, f"❌ Мало {cargo}"); return
    if cargo != "деньги": c["cargo_stock"][cargo] -= amount
    total = CARGO_TYPES[cargo]["price"] * amount
    if random.random() < SMUGGLE_CHANCE:
        tc = get_country(target)
        if tc and not tc.get("destroyed"):
            tc.setdefault("cargo_stock", {})[cargo] = tc["cargo_stock"].get(cargo, 0) + amount
        send(peer_id, f"🕵️ Удача! {amount} {cargo} → {country_name(target)}")
        broadcast_country(key, f"🕵️ Контрабанда в {country_name(target)} прошла!")
    else:
        fine = total * SMUGGLE_FINE
        c["treasury"] = max(0, c.get("treasury", 0) - fine); save_cfg(cfg)
        send(peer_id, f"🚨 Задержано! Штраф: {fmt_num(fine)} 💵")
        broadcast_country(target, f"🚨 {country_name(key)} — контрабанда!")

# ========== ВОЙНА ==========
def cmd_wars(peer_id, uid, args):
    wars = cfg.get("wars", [])
    if not wars: send(peer_id, "☮️ Войн нет."); return
    send(peer_id, "⚔️ Войны:\n" + "\n".join(f"{i}. {country_name(w['a'])} ⚔️ {country_name(w['b'])}" for i, w in enumerate(wars, 1)))

def cmd_declare_war(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if c.get("destroyed"): send(peer_id, "❌"); return
    if not args: send(peer_id, "⚠ /война <страна>"); return
    target = args[0].lower()
    if target not in COUNTRIES or target == key: send(peer_id, "❌"); return
    tc = get_country(target)
    if tc.get("destroyed"): send(peer_id, "⚠"); return
    if c.get("treasury", 0) < WAR_COST: send(peer_id, f"❌ {fmt_num(WAR_COST)} 💵"); return
    for w in cfg.get("wars", []):
        if {w["a"], w["b"]} == {key, target}: send(peer_id, "⚠ Уже идёт."); return
    c["treasury"] -= WAR_COST
    c.setdefault("wars", []).append(target); tc.setdefault("wars", []).append(key)
    cfg.setdefault("wars", []).append({"a": key, "b": target, "started_at": int(time.time())})
    save_cfg(cfg)
    send(peer_id, f"⚔️ {country_name(key)} ОБЪЯВИЛА ВОЙНУ {country_name(target)}!")
    broadcast_country(key, f"⚔️ Война с {country_name(target)}!")
    broadcast_country(target, f"🚨 {country_name(key)} ОБЪЯВИЛА ВОЙНУ!")

def cmd_capture(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if not args: send(peer_id, "⚠ /захват <страна>"); return
    target = args[0].lower()
    if target not in COUNTRIES: send(peer_id, "❌"); return
    war = next((w for w in cfg.get("wars", []) if {w["a"], w["b"]} == {key, target}), None)
    if not war: send(peer_id, "❌ Сначала /война"); return
    send(peer_id, f"⏳ Кампания {WAR_CAPTURE_SECONDS//60} мин...")
    broadcast_country(key, f"⚔️ Кампания против {country_name(target)}!")

    def resolve():
        time.sleep(WAR_CAPTURE_SECONDS)
        ap = country_army_power(key); bp = country_army_power(target)
        ar = random.uniform(0.7, 1.3) * ap; br = random.uniform(0.7, 1.3) * bp * 1.1
        tc = get_country(target); cf = get_country(key)
        if cf.get("destroyed") or tc.get("destroyed"): return
        if ar > br:
            loot = tc.get("treasury", 0); cf["treasury"] = cf.get("treasury", 0) + loot
            tc["treasury"] = 0; tc["army"] = 0; tc["destroyed"] = True
            tc["captured_by"] = key; tc["destroyed_at"] = int(time.time())
            pres = tc.get("president")
            if pres:
                tc.setdefault("hostages", []).append(pres)
                if get_citizenship(pres): cfg["citizens"][str(pres)]["hostage_until"] = int(time.time()) + 86400
                send_dm(pres, "🔒 ВЫ В ЗАЛОЖНИКАХ!")
            for w in list(cfg.get("wars", [])):
                if {w["a"], w["b"]} == {key, target}: cfg["wars"].remove(w)
            if target in cf.get("wars", []): cf["wars"].remove(target)
            if key in tc.get("wars", []): tc["wars"].remove(key)
            cf["activation_points"] = cf.get("activation_points", 0) + 50
            save_cfg(cfg)
            broadcast_country(key, f"🏆 ПОБЕДА! Уничтожена {country_name(target)}! +{fmt_num(loot)} 💵 +50 очков")
            broadcast_country(target, f"☠️ СТРАНА УНИЧТОЖЕНА!")
        else:
            la = int(cf.get("army", 0) * 0.25); cf["army"] = max(0, cf.get("army", 0) - la)
            lb = int(tc.get("army", 0) * 0.1); tc["army"] = max(0, tc.get("army", 0) - lb)
            save_cfg(cfg)
            broadcast_country(key, f"💀 Провал. -{fmt_num(la)}")
            broadcast_country(target, f"🛡️ Отбились!")

    threading.Thread(target=resolve, daemon=True).start()

def cmd_counter_defense(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if c.get("counter_used"): send(peer_id, "⚠"); return
    war = next((w for w in cfg.get("wars", []) if key in (w["a"], w["b"])), None)
    if not war: send(peer_id, "❌"); return
    enemy = war["b"] if war["a"] == key else war["a"]; ec = get_country(enemy)
    if ec.get("destroyed"): send(peer_id, "⚠"); return
    ap = country_army_power(key) * 1.5; bp = country_army_power(enemy)
    if ap > bp:
        loss = int(ec.get("army", 0) * 0.4); ec["army"] = max(0, ec.get("army", 0) - loss)
        loot = int(ec.get("treasury", 0) * 0.25); ec["treasury"] -= loot; c["treasury"] = c.get("treasury", 0) + loot
        c["counter_used"] = True; save_cfg(cfg)
        broadcast_country(key, f"⚡ Контратака! +{fmt_num(loot)}")
    else:
        c["counter_used"] = True; loss = int(c.get("army", 0) * 0.2); c["army"] = max(0, c.get("army", 0) - loss)
        save_cfg(cfg); broadcast_country(key, f"💀 Провал. -{fmt_num(loss)}")

def cmd_peace(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if not args: send(peer_id, "⚠ /мир <страна>"); return
    target = args[0].lower()
    war = next((w for w in cfg.get("wars", []) if {w["a"], w["b"]} == {key, target}), None)
    if not war: send(peer_id, "❌"); return
    tc = get_country(target)
    if c.get("treasury", 0) < 500000 or tc.get("treasury", 0) < 500000: send(peer_id, "❌ Нужно по 500к."); return
    c["treasury"] -= 500000; tc["treasury"] -= 500000
    cfg["wars"].remove(war)
    if target in c.get("wars", []): c["wars"].remove(target)
    if key in tc.get("wars", []): tc["wars"].remove(key)
    save_cfg(cfg)
    broadcast_country(key, f"☮️ Мир с {country_name(target)}")
    broadcast_country(target, f"☮️ Мир с {country_name(key)}")

def cmd_end_conflict(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key)
    if c.get("president") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if not args: send(peer_id, "⚠ /завершить_конфликт <страна>"); return
    target = args[0].lower()
    if target not in COUNTRIES: send(peer_id, "❌"); return
    war = next((w for w in cfg.get("wars", []) if {w["a"], w["b"]} == {key, target}), None)
    if not war: send(peer_id, "❌"); return
    cfg["wars"].remove(war)
    if target in c.get("wars", []): c["wars"].remove(target)
    tc = get_country(target)
    if tc and key in tc.get("wars", []): tc["wars"].remove(key)
    save_cfg(cfg)
    broadcast_country(key, f"☮️ Мир с {country_name(target)}")
    broadcast_country(target, f"☮️ Мир с {country_name(key)}")

# ========== КОАЛИЦИИ ==========
def cmd_coalitions(peer_id, uid, args):
    coal = cfg.get("coalitions", {})
    if not coal: send(peer_id, "📭 Нет."); return
    lines = ["🤝 Коалиции:"]
    for name, data in coal.items():
        lines.append(f"\n🔹 {name} — {len(data.get('members', []))}")
        lines.append(f"  Лидер: {country_name(data.get('leader'))}")
        for m in data.get("members", []): lines.append(f"  {'👑' if m == data.get('leader') else '•'} {country_name(m)}")
    send(peer_id, "\n".join(lines))

def cmd_coalition(peer_id, uid, args, reply_msg):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    coal = cfg.setdefault("coalitions", {})
    if not args:
        mn = c.get("coalition")
        if not mn: send(peer_id, "🤝 Не в коалиции.\n/коалиция <название>"); return
        data = coal.get(mn, {})
        send(peer_id, f"🤝 «{mn}»\n👑 {country_name(data.get('leader'))}\n" + "\n".join(f"  • {country_name(m)}" for m in data.get("members", []))); return
    sub = args[0].lower()
    if sub == "пригласить" and len(args) >= 2:
        mn = c.get("coalition")
        if not mn: send(peer_id, "⚠"); return
        data = coal.get(mn, {})
        if data.get("leader") != key: send(peer_id, "⛔"); return
        target = args[1].lower()
        if target not in COUNTRIES: send(peer_id, "⚠"); return
        if target in data.get("members", []): send(peer_id, "⚠"); return
        data.setdefault("invites", []).append(target); save_cfg(cfg)
        broadcast_country(target, f"🤝 Приглашение в «{mn}»\n/коалиция вступить {mn}"); return
    if sub == "вступить" and len(args) >= 2:
        name = " ".join(args[1:]); data = coal.get(name)
        if not data or key not in data.get("invites", []): send(peer_id, "⚠"); return
        data["invites"].remove(key); data.setdefault("members", []).append(key)
        c["coalition"] = name; save_cfg(cfg); send(peer_id, f"✅ Вступили в «{name}»!"); return
    if sub == "покинуть":
        mn = c.get("coalition")
        if not mn: send(peer_id, "⚠"); return
        data = coal.get(mn, {})
        if key in data.get("members", []): data["members"].remove(key)
        if data.get("leader") == key:
            if data.get("members"): data["leader"] = data["members"][0]
            else: del coal[mn]
        c["coalition"] = None; save_cfg(cfg); send(peer_id, "👋"); return
    if sub == "распустить":
        mn = c.get("coalition")
        if not mn: send(peer_id, "⚠"); return
        data = coal.get(mn, {})
        if data.get("leader") != key: send(peer_id, "⛔"); return
        for m in data.get("members", []):
            mc = get_country(m)
            if mc: mc["coalition"] = None
        del coal[mn]; save_cfg(cfg); send(peer_id, "💥"); return
    name = " ".join(args)
    if name in coal or c.get("coalition"): send(peer_id, "⚠"); return
    coal[name] = {"leader": key, "members": [key], "invites": []}
    c["coalition"] = name; save_cfg(cfg); send(peer_id, f"🤝 «{name}» создана!")

def cmd_coal_help_money(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if len(args) < 2 or not args[1].isdigit(): send(peer_id, "⚠ /коалпомощь <страна> <сумма>"); return
    target = args[0].lower(); amount = int(args[1])
    tc = get_country(target)
    if not tc: send(peer_id, "⚠"); return
    if not c.get("coalition") or c.get("coalition") != tc.get("coalition"): send(peer_id, "⚠ Только союзникам."); return
    if c.get("treasury", 0) < amount: send(peer_id, "❌"); return
    c["treasury"] -= amount; tc["treasury"] = tc.get("treasury", 0) + amount; save_cfg(cfg)
    send(peer_id, f"💵 {fmt_num(amount)} → {country_name(target)}")
    broadcast_country(target, f"💵 +{fmt_num(amount)} от {country_name(key)}")

# ========== АРМИЯ ==========
def cmd_mobilization(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and c.get("commander") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if c.get("mobilized"): send(peer_id, "⚠"); return
    bonus = int(c.get("army", BASE_ARMY) * 0.3); c["army"] = c.get("army", 0) + bonus; c["mobilized"] = True
    c["mobilized_until"] = int(time.time()) + 12 * 3600; save_cfg(cfg)
    broadcast_country(key, f"📣 МОБИЛИЗАЦИЯ! +{fmt_num(bonus)}")

def cmd_demobilization(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and c.get("commander") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if not c.get("mobilized"): send(peer_id, "⚠"); return
    c["mobilized"] = False; c["mobilized_until"] = 0; save_cfg(cfg)
    broadcast_country(key, "📣 Демобилизация.")

def cmd_make_weapon(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and c.get("commander") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if len(args) < 2 or not args[1].isdigit(): send(peer_id, "⚠ /сделать <оружие> <кол>\n" + ", ".join(WEAPONS.keys())); return
    weapon = args[0].lower(); cnt = int(args[1])
    if weapon not in WEAPONS: send(peer_id, "⚠"); return
    cost = WEAPONS[weapon]["cost"] * cnt
    if c.get("treasury", 0) < cost: send(peer_id, f"❌ {fmt_num(cost)}"); return
    c["treasury"] -= cost; c.setdefault("weapons", {})[weapon] = c.get("weapons", {}).get(weapon, 0) + cnt
    save_cfg(cfg); send(peer_id, f"🏭 {cnt} {weapon}")

def cmd_install_pvo(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and c.get("commander") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if len(args) < 2 or not args[-1].isdigit(): send(peer_id, "⚠ /установить пво <город> <кол>"); return
    cnt = int(args[-1]); city = " ".join(args[:-1]).title(); cities = get_country_cities(key)
    cm = next((x for x in cities if x.lower() == city.lower()), None)
    if not cm: send(peer_id, "⚠"); return
    if c.get("weapons", {}).get("пво", 0) < cnt: send(peer_id, "❌"); return
    c["weapons"]["пво"] -= cnt
    c["cities"][cm]["pvo"] = c["cities"].get(cm, {}).get("pvo", 0) + cnt; save_cfg(cfg)
    send(peer_id, f"🚀 {cnt} ПВО в {cm}")

def cmd_pvo_info(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    lines = [f"🚀 ПВО {country_name(key)}", ""]; total = 0
    for city, d in c.get("cities", {}).items():
        pvo = d.get("pvo", 0)
        if pvo: lines.append(f"• {city}: {pvo}"); total += pvo
    lines.append(f"\nСклад: {c.get('weapons', {}).get('пво', 0)}\nВсего: {total}, перехват: {min(90, total//10)}%")
    send(peer_id, "\n".join(lines))

def cmd_launch(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and c.get("commander") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if len(args) < 2: send(peer_id, "⚠ /запуск <оружие> <кол> <страна>"); return
    weapon = args[0].lower()
    if weapon == "ядерная":
        target = args[-1].lower(); tc = get_country(target)
        if not tc: send(peer_id, "⚠"); return
        war = next((w for w in cfg.get("wars", []) if {w["a"], w["b"]} == {key, target}), None)
        if not war: send(peer_id, "❌"); return
        if c.get("nukes", 0) < 1: send(peer_id, "❌"); return
        c["nukes"] -= 1; loss = int(tc.get("army", 0) * 0.5); tc["army"] = max(0, tc.get("army", 0) - loss)
        loot = int(tc.get("treasury", 0) * 0.4); tc["treasury"] -= loot; c["treasury"] = c.get("treasury", 0) + loot
        save_cfg(cfg)
        broadcast_country(key, f"☢️ ЯДЕРНЫЙ УДАР по {country_name(target)}!")
        broadcast_country(target, f"☢️ ЯДЕРНЫЙ УДАР! -{fmt_num(loss)} войск, -{fmt_num(loot)} 💵"); return
    if weapon not in ("ракета", "бпла"): send(peer_id, "⚠"); return
    if len(args) < 3 or not args[1].isdigit(): send(peer_id, "⚠"); return
    cnt = int(args[1]); target = args[2].lower(); tc = get_country(target)
    if not tc: send(peer_id, "⚠"); return
    war = next((w for w in cfg.get("wars", []) if {w["a"], w["b"]} == {key, target}), None)
    if not war: send(peer_id, "❌"); return
    if c.get("weapons", {}).get(weapon, 0) < cnt: send(peer_id, "❌"); return
    c["weapons"][weapon] -= cnt
    pvo = sum(d.get("pvo", 0) for d in tc.get("cities", {}).values())
    intercepted = min(pvo, cnt * 2); hits = max(0, cnt - intercepted)
    power = WEAPONS.get(weapon, {}).get("power", 100) * hits
    loss = min(int(tc.get("army", 0) * (power / 50000)), int(tc.get("army", 0) * 0.3))
    tc["army"] = max(0, tc.get("army", 0) - loss); save_cfg(cfg)
    broadcast_country(key, f"🚀 {cnt} {weapon} по {country_name(target)}. Попаданий: {hits}, сбито: {intercepted}")
    broadcast_country(target, f"🚨 Атака! Сбито: {intercepted}, попаданий: {hits}, -{fmt_num(loss)}")

def cmd_tasks(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    cd = c.get("mil_task_cooldown", {}).get(str(uid), 0)
    if time.time() < cd: send(peer_id, f"⏳ {fmt_time(cd-time.time())}"); return
    send(peer_id, f"📋 Задание\n💰 {fmt_num(MIL_TASK_COST)} 💵\n🎁 +{fmt_num(MIL_TASK_REWARD)} войск, +5 очков\n/выполнитьзадание")

def cmd_do_task(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    cd = c.get("mil_task_cooldown", {}).get(str(uid), 0)
    if time.time() < cd: send(peer_id, f"⏳ {fmt_time(cd-time.time())}"); return
    bal = get_balance(peer_id, uid)
    if bal < MIL_TASK_COST: send(peer_id, f"❌ {fmt_num(MIL_TASK_COST)}"); return
    add_balance(peer_id, uid, -MIL_TASK_COST)
    c["army"] = c.get("army", 0) + MIL_TASK_REWARD
    c["activation_points"] = c.get("activation_points", 0) + 5
    c.setdefault("mil_task_cooldown", {})[str(uid)] = int(time.time() + MIL_TASK_COOLDOWN)
    save_cfg(cfg); send(peer_id, f"✅ +{fmt_num(MIL_TASK_REWARD)} войск, +5 очков")
    broadcast_country(key, f"🎖️ {mention(uid)}: +{fmt_num(MIL_TASK_REWARD)} войск")

def cmd_upgrade_army(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key) or {}
    if c.get("president") != uid and c.get("commander") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    lvl = c.get("army_level", 1)
    if lvl >= ARMY_LEVEL_MAX: send(peer_id, "⚠ Максимум."); return
    cost = 500000 * lvl
    if c.get("treasury", 0) < cost: send(peer_id, f"❌ {fmt_num(cost)}"); return
    c["treasury"] -= cost; c["army_level"] = lvl + 1; save_cfg(cfg)
    broadcast_country(key, f"🎖️ Армия до уровня {lvl+1}!")

# ========== ДРОН / СИРЕНА ==========
def cmd_drone(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key)
    if c.get("president") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if not args:
        drones = c.get("drones_in_flight", [])
        if not drones: send(peer_id, "📭 Нет дронов."); return
        send(peer_id, "🛸 Летящие:\n" + "\n".join(f"→ {country_name(d['target'])}/{d['city']} | {fmt_time(d['arrives_at']-time.time())}" for d in drones if d["arrives_at"] > time.time())); return
    target = args[0].lower()
    if target not in COUNTRIES: send(peer_id, "❌"); return
    tc = get_country(target)
    if not tc or tc.get("destroyed"): send(peer_id, "⚠"); return
    cities = get_country_cities(target); city = random.choice(cities[:tc.get("cities_unlocked", 3)])
    arrives = int(time.time()) + DRONE_FLIGHT_SECONDS
    c.setdefault("drones_in_flight", []).append({"attacker": key, "target": target, "city": city, "arrives_at": arrives})
    save_cfg(cfg)
    send(peer_id, f"🛸 Дрон → {country_name(target)}/{city}\n⏱ {DRONE_FLIGHT_SECONDS//60} мин")
    heads = set()
    if tc.get("president"): heads.add(tc["president"])
    if tc.get("commander"): heads.add(tc["commander"])
    for h in heads: send_dm(h, f"🚨 ВОЗДУШНАЯ ТРЕВОГА!\n🏙 {city}\n⏱ {DRONE_FLIGHT_SECONDS//60} мин\n/перехват")

def cmd_intercept(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key)
    if c.get("president") != uid and c.get("commander") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    found = None
    for ok, o in cfg.get("countries", {}).items():
        for d in o.get("drones_in_flight", []):
            if d["target"] == key and d["arrives_at"] > time.time(): found = (ok, o, d); break
        if found: break
    if not found: send(peer_id, "📭 Нет дронов."); return
    ak, ac, dr = found
    if random.random() < INTERCEPT_CHANCE:
        ac["drones_in_flight"].remove(dr); save_cfg(cfg)
        send(peer_id, "🎯 Перехвачен! (20%)")
        broadcast_country(key, f"🎯 Перехвачен дрон {country_name(ak)}!")
    else:
        send(peer_id, "❌ Промах.")
        broadcast_country(key, "❌ Перехват не удался.")

def drone_ticker():
    while True:
        time.sleep(5)
        try:
            now = time.time(); ch = False
            for key, c in cfg.get("countries", {}).items():
                drones = c.get("drones_in_flight", [])
                for d in list(drones):
                    if d["arrives_at"] <= now:
                        drones.remove(d); tc = get_country(d["target"])
                        if tc:
                            loss = int(tc.get("army", 0) * 0.03); tc["army"] = max(0, tc.get("army", 0) - loss)
                            broadcast_country(d["target"], f"💥 Дрон поразил {d['city']}! -{fmt_num(loss)}")
                        ch = True
            if ch: save_cfg(cfg)
        except Exception as e: print(f"[drone] {e}")

threading.Thread(target=drone_ticker, daemon=True).start()

def cmd_siren(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key)
    if c.get("president") != uid and c.get("commander") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if c.get("destroyed"): send(peer_id, "❌"); return
    if not args: send(peer_id, "⚠ /сирена <город>"); return
    city = " ".join(args).title(); cities = get_country_cities(key)
    cm = next((x for x in cities if x.lower() == city.lower()), None)
    if not cm: send(peer_id, "❌"); return
    if cities.index(cm) >= c.get("cities_unlocked", 3): send(peer_id, "❌"); return
    c["cities"][cm]["siren"] = True; save_cfg(cfg)
    broadcast_country(key, f"🚨🚨🚨 ВОЗДУШНАЯ ТРЕВОГА 🚨🚨🚨\n🏙 {cm}\n⚠️ В укрытие!")

    def clr():
        time.sleep(300)
        cc = get_country(key)
        if cc and cm in cc.get("cities", {}): cc["cities"][cm]["siren"] = False; save_cfg(cfg)
        broadcast_country(key, f"🟢 Отбой в {cm}.")

    threading.Thread(target=clr, daemon=True).start()
    send(peer_id, f"🚨 Тревога в {cm}!")

def cmd_siren_all(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key)
    if c.get("president") != uid and c.get("commander") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    for city in list(c.get("cities", {}).keys()): c["cities"][city]["siren"] = True
    save_cfg(cfg)
    broadcast_country(key, f"🚨🚨🚨 ВСЕОБЩАЯ ТРЕВОГА 🚨🚨🚨\n🌍 {country_name(key)}")

    def clr():
        time.sleep(600); cc = get_country(key)
        if cc:
            for x in cc.get("cities", {}): cc["cities"][x]["siren"] = False
            save_cfg(cfg)
        broadcast_country(key, "🟢 Отбой.")

    threading.Thread(target=clr, daemon=True).start()
    send(peer_id, "🚨 Всеобщая тревога!")

# ========== ЗВАНИЯ ==========
def cmd_show_rank(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key)
    target = extract_user(" ".join(args)) or uid
    ranks = c.get("army_ranks", {}); idx = ranks.get(str(target), 0)
    rank = ARMY_RANKS[idx]; nxt = ARMY_RANKS[idx + 1] if idx + 1 < len(ARMY_RANKS) else None
    lines = [f"🎖️ Звание {mention(target, peer_id)}", f"📌 {rank.title()}"]
    if nxt:
        req = RANK_REQUIREMENTS.get(nxt, (0, 0)); have = c.get("activation_points", 0)
        lines.append(f"⬆️ {nxt.title()}\n🎯 {have}/{req[0]}\n💰 {req[1]}")
    else: lines.append("🏆 Максимум!")
    send(peer_id, "\n".join(lines))

def cmd_promote(peer_id, uid, args):
    cit = get_citizenship(uid)
    if not cit: send(peer_id, "⚠"); return
    key = cit["country"]; c = get_country(key)
    if c.get("president") != uid and c.get("commander") != uid and uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    target = extract_user(" ".join(args))
    if not target: send(peer_id, "⚠ /повысить @user"); return
    t_cit = get_citizenship(target)
    if not t_cit or t_cit["country"] != key: send(peer_id, "⚠ Не гражданин."); return
    ranks = c.setdefault("army_ranks", {}); idx = ranks.get(str(target), 0)
    if idx + 1 >= len(ARMY_RANKS): send(peer_id, "⚠ Уже маршал."); return
    nxt = ARMY_RANKS[idx + 1]; req = RANK_REQUIREMENTS.get(nxt, (0, 0))
    if c.get("activation_points", 0) < req[0]: send(peer_id, f"❌ Нужно {req[0]} очков"); return
    if c.get("treasury", 0) < req[1]: send(peer_id, f"❌ Нужно {fmt_num(req[1])} 💵"); return
    c["treasury"] -= req[1]; ranks[str(target)] = idx + 1; save_cfg(cfg)
    send(peer_id, f"🎖️ {mention(target, peer_id)} — {nxt.title()}!")
    send_dm(target, f"🎖️ {nxt.title()}!")

# ========== ГЛОБАЛЬНЫЕ ==========
def cmd_give(peer_id, uid, args, reply_msg, text):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔ Global."); return
    if not args:
        send(peer_id, "💰 /выдать деньги @user <сумма>\n🔫 /выдать оружие казна <страна> <тип> <кол>\n🎖️ /выдать военных <страна> <кол>\n👑 /выдать вип @user\n☢️ /выдать ядерка <страна> <кол>"); return
    kind = args[0].lower()
    if kind == "деньги":
        if len(args) >= 2 and args[1].lower() in ("казна", "страна"):
            if len(args) < 4 or not args[-1].isdigit(): send(peer_id, "⚠"); return
            key = args[2].lower()
            if key not in COUNTRIES: send(peer_id, "⚠"); return
            amount = int(args[-1]); c = get_country(key)
            c["treasury"] = c.get("treasury", 0) + amount; save_cfg(cfg)
            send(peer_id, f"✅ +{fmt_num(amount)} в {country_name(key)}"); return
        t = extract_user(text, reply_msg)
        if not t: send(peer_id, "⚠ @user"); return
        amount = None
        for a in args:
            if a.isdigit() and int(a) > 0: amount = int(a); break
        if not amount: send(peer_id, "⚠ Сумма"); return
        add_balance(peer_id, t, amount); save_cfg(cfg)
        send(peer_id, f"✅ +{fmt_num(amount)} 💵"); send_dm(t, f"💰 +{fmt_num(amount)} 💵"); return
    if kind == "оружие":
        if len(args) >= 5 and args[1].lower() in ("казна", "страна"):
            key = args[2].lower(); weapon = args[3].lower()
            if not args[4].isdigit(): send(peer_id, "⚠"); return
            cnt = int(args[4])
            if key not in COUNTRIES or weapon not in WEAPONS: send(peer_id, "⚠"); return
            c = get_country(key)
            c.setdefault("weapons", {})[weapon] = c.get("weapons", {}).get(weapon, 0) + cnt; save_cfg(cfg)
            send(peer_id, f"✅ +{cnt} {weapon}"); return
        send(peer_id, "⚠ /выдать оружие казна <страна> <тип> <кол>"); return
    if kind == "военных":
        if len(args) < 3 or not args[-1].isdigit(): send(peer_id, "⚠"); return
        key = args[1].lower()
        if key not in COUNTRIES: send(peer_id, "⚠"); return
        cnt = int(args[-1]); c = get_country(key)
        c["army"] = c.get("army", 0) + cnt; save_cfg(cfg)
        broadcast_country(key, f"🎖️ +{fmt_num(cnt)} войск!"); return
    if kind == "вип":
        t = extract_user(text, reply_msg)
        if not t: send(peer_id, "⚠"); return
        c = get_chat(peer_id)
        if c:
            c.setdefault("subs", {})[str(t)] = int(time.time()) + VIP_DURATION; save_cfg(cfg)
        send(peer_id, f"✅ VIP"); send_dm(t, "👑 VIP 30 дней!"); return
    if kind == "ядерка":
        if len(args) < 3 or not args[-1].isdigit(): send(peer_id, "⚠"); return
        key = args[1].lower()
        if key not in COUNTRIES: send(peer_id, "⚠"); return
        cnt = int(args[-1]); c = get_country(key)
        c["nukes"] = c.get("nukes", 0) + cnt; save_cfg(cfg)
        broadcast_country(key, f"☢️ +{cnt} ядерных!"); return
    send(peer_id, "⚠ Типы: деньги, оружие, военных, вип, ядерка")

def cmd_restore_country(peer_id, uid, args):
    if not is_chat(peer_id): send(peer_id, "❌"); return
    c = get_chat(peer_id)
    if uid != int(cfg["global_owner"]) and c.get("owner") != uid: send(peer_id, "⛔"); return
    if not args:
        destroyed = [k for k, v in cfg.get("countries", {}).items() if v.get("destroyed")]
        if not destroyed: send(peer_id, "📭 Нет."); return
        send(peer_id, "☠️ Уничтоженные:\n" + "\n".join(f"• {country_name(k)}" for k in destroyed) + "\n\n/вернуть <страна>"); return
    key = None
    for a in args:
        if a.lower() in COUNTRIES: key = a.lower(); break
    if not key: send(peer_id, "⚠"); return
    country = get_country(key)
    if not country.get("destroyed"): send(peer_id, "ℹ"); return
    country["destroyed"] = False; country["captured_by"] = None; country["destroyed_at"] = 0
    country["army"] = BASE_ARMY; country["army_level"] = 1; country["treasury"] = 0
    country["weapons"] = {w: 0 for w in WEAPONS}; country["nukes"] = 0
    country["wars"] = []; country["hostages"] = []
    for w in list(cfg.get("wars", [])):
        if key in (w["a"], w["b"]): cfg["wars"].remove(w)
    save_cfg(cfg)
    broadcast_country(key, f"🏛 Страна восстановлена!")
    send(peer_id, f"🏛 {country_name(key)} восстановлена")

def cmd_set_president_global(peer_id, uid, args, reply_msg):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if not args: send(peer_id, "⚠ /устпрезидент @user <страна>"); return
    t = extract_user(" ".join(args), reply_msg)
    if not t: send(peer_id, "⚠"); return
    key = None
    for a in args:
        if a.lower() in COUNTRIES: key = a.lower(); break
    if not key: send(peer_id, "⚠"); return
    if not get_citizenship(t): set_citizenship(t, key)
    cfg["citizens"][str(t)]["rank"] = "президент"
    c = get_country(key); old = c.get("president")
    if old and get_citizenship(old): cfg["citizens"][str(old)]["rank"] = "гражданин"
    c["president"] = t; save_cfg(cfg)
    send(peer_id, f"👑 {mention(t, peer_id)} — президент {country_name(key)}")
    broadcast_country(key, f"👑 Президент: {mention(t)}")

def cmd_set_citizenship_global(peer_id, uid, args, reply_msg):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    if not args: send(peer_id, "⚠ /устгражданство @user <страна>"); return
    t = extract_user(" ".join(args), reply_msg)
    if not t: send(peer_id, "⚠"); return
    key = None
    for a in args:
        if a.lower() in COUNTRIES: key = a.lower(); break
    if not key: send(peer_id, "⚠"); return
    set_citizenship(t, key); send(peer_id, f"✅ {mention(t, peer_id)} — {country_name(key)}")
    send_dm(t, f"🌍 Гражданство {country_name(key)}")

def cmd_gstaff(peer_id, uid):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    gs = cfg.get("global_staff", {})
    if not gs: send(peer_id, "📭"); return
    prefetch_names([int(u) for u in gs.keys()])
    lines = ["🌐 Глобальные роли:"]
    for us, rk in gs.items():
        role = find_role(rk, peer_id); rname = role["name"] if role else rk
        lines.append(f"• {mention(us, peer_id)} — {rname}")
    send(peer_id, "\n".join(lines))

def cmd_grole(peer_id, uid, args, reply_msg, text):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    t = extract_user(text, reply_msg)
    if not t: send(peer_id, "⚠ /grole @user <роль>"); return
    ra = [a for a in args if not re.match(r"\[id\d+\|", a) and not re.match(r"@id\d+", a)]
    ri = " ".join(ra).strip()
    if not ri: send(peer_id, "⚠"); return
    rk = find_role_by_input(ri, peer_id)
    if not rk: send(peer_id, f"⚠ «{ri}» не найдена."); return
    cfg.setdefault("global_staff", {})[str(t)] = rk; save_cfg(cfg)
    rname = cfg["roles"].get(rk, {}).get("name", rk)
    send(peer_id, f"🌐 {mention(t, peer_id)} — {rname}")

def cmd_removerole(peer_id, uid, args, reply_msg, text):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    t = extract_user(text, reply_msg)
    if not t: send(peer_id, "⚠"); return
    rem = cfg.get("global_staff", {}).pop(str(t), None); save_cfg(cfg)
    send(peer_id, "❌" if rem else "ℹ")

def cmd_build_link(peer_id, uid, args):
    if not is_chat(peer_id): send(peer_id, "❌"); return
    c = get_chat(peer_id)
    if uid != int(cfg["global_owner"]) and c.get("owner") != uid: send(peer_id, "⛔"); return
    if not args: send(peer_id, f"🏗️ {c.get('build_name') or '—'}"); return
    name = " ".join(args).strip(); c["build_name"] = name
    builds = cfg.setdefault("builds", {}); builds.setdefault(name, [])
    if peer_id not in builds[name]: builds[name].append(peer_id)
    save_cfg(cfg); send(peer_id, f"🏗️ «{name}» ({len(builds[name])})")

def cmd_builds_list(peer_id, uid):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    builds = cfg.get("builds", {})
    if not builds: send(peer_id, "📭"); return
    send(peer_id, "🏗️ Сетки:\n" + "\n".join(f"📦 «{n}» — {len(p)}" for n, p in builds.items()))
    # ========== ИВЕНТЫ ==========
EVENTS_LIST = {"рулетка":"🎰 Рулетка","дуэль":"⚔️ Дуэль","лотерея":"🎟️ Лотерея","хэллоуин":"🎃 Хэллоуин","новыйгод":"🎄 Новый год","мафия":"🎭 Мафия","admin_abuse":"👑 Admin Abuse","гонка":"🏎️ Гонка","золото":"💰 Золото","клад":"🗝 Клад","блэкаут":"🌑 Блэкаут","феникс":"🔥 Феникс"}
EVENT_TITLES = ["🏆 Победитель","⚔️ Воин","🎟️ Счастливчик","🎄 Снегурочка","🌟 Звезда","👑 Король","🎩 Магистр","🍀 Удачливый","🔥 Горячая штучка","🐉 Дракон","🦊 Хитрец","🌸 Красотка","🏎️ Гонщик","🕵️ Детектив","🧙 Маг","🐺 Вожак"]

def get_chat_members(peer_id):
    try:
        return [m["member_id"] for m in api.messages.getConversationMembers(peer_id=peer_id)["items"] if m["member_id"] > 0 and m["member_id"] != BOT_ID]
    except: return []

def _pick(peer_id):
    u = get_chat_members(peer_id); return random.choice(u) if u else None

def ev_roulette(peer_id):
    c = get_chat(peer_id); w = _pick(peer_id)
    if not w: send(peer_id, "❌ Нет участников."); return
    eff = random.choice(["title","mute","warn","money","nothing"])
    if eff == "title":
        t = random.choice(EVENT_TITLES); c["nicknames"][str(w)] = t; save_cfg(cfg)
        send(peer_id, f"🎰 {mention(w,peer_id)} → {t}")
    elif eff == "mute":
        c["muted"][str(w)] = {"until":time.time()+300,"last_dm":0}; save_cfg(cfg)
        send(peer_id, f"🎰 {mention(w,peer_id)} 🔇 5 мин."); mute_notify_dm(w,5)
    elif eff == "warn":
        wr = c["warns"]; wr[str(w)] = wr.get(str(w),0)+1; save_cfg(cfg)
        send(peer_id, f"🎰 {mention(w,peer_id)} ⚠️ ({wr[str(w)]})")
    elif eff == "money":
        b = int(100*full_vip_mult(peer_id,w)); add_balance(peer_id,w,b)
        send(peer_id, f"🎰 {mention(w,peer_id)} 💰 +{fmt_num(b)}")
    else: send(peer_id, f"🎰 {mention(w,peer_id)} — ничего")

def ev_duel_ev(peer_id):
    c = get_chat(peer_id); users = get_chat_members(peer_id)
    if len(users) < 2: send(peer_id, "❌ ≥2."); return
    a, b = random.sample(users,2); w = random.choice([a,b]); t = random.choice(EVENT_TITLES)
    c["nicknames"][str(w)] = t; save_cfg(cfg)
    send(peer_id, f"⚔️ {mention(a,peer_id)} vs {mention(b,peer_id)}\n🏆 {mention(w,peer_id)} → {t}")

def ev_lottery(peer_id):
    c = get_chat(peer_id); users = get_chat_members(peer_id)
    if len(users) < 3: send(peer_id, "❌ ≥3."); return
    lines = ["🎟️ Лотерея:"]
    for w in random.sample(users,3):
        t = random.choice(EVENT_TITLES); c["nicknames"][str(w)] = t; lines.append(f"— {mention(w,peer_id)} → {t}")
    save_cfg(cfg); send(peer_id, "\n".join(lines))

def ev_halloween(peer_id):
    c = get_chat(peer_id); w = _pick(peer_id)
    if not w: send(peer_id, "❌"); return
    c["muted"][str(w)] = {"until":time.time()+300,"last_dm":0}; save_cfg(cfg)
    send(peer_id, f"🎃 {mention(w,peer_id)} 🔇 5 мин."); mute_notify_dm(w,5)

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
    c["nicknames"][str(w)] = "👑 Admin Abuser"
    stats = c.setdefault("user_stats",{}); key = str(w)
    s = stats.get(key) or {"msg_count":0,"last_text":"","last_at":0}
    s["msg_count"] += 50; stats[key] = s; save_cfg(cfg)
    send(peer_id, f"👑 ADMIN ABUSE!\n{mention(w,peer_id)} → титул 👑 Admin Abuser\n+50 сообщений!")

def ev_race(peer_id):
    c = get_chat(peer_id); w = _pick(peer_id)
    if not w: send(peer_id, "❌"); return
    c["nicknames"][str(w)] = "🏎️ Гонщик"; save_cfg(cfg)
    send(peer_id, f"🏎️ {mention(w,peer_id)} → Гонщик!")

def ev_gold(peer_id):
    w = _pick(peer_id)
    if not w: send(peer_id, "❌"); return
    b = int(500*full_vip_mult(peer_id,w)); nb = add_balance(peer_id,w,b)
    send(peer_id, f"💰 {mention(w,peer_id)} +{fmt_num(b)}\nБаланс: {fmt_num(nb)}")

def ev_treasure(peer_id):
    w = _pick(peer_id)
    if not w: send(peer_id, "❌"); return
    b = int(200*full_vip_mult(peer_id,w)); nb = add_balance(peer_id,w,b)
    send(peer_id, f"🗝 {mention(w,peer_id)} +{fmt_num(b)}\nБаланс: {fmt_num(nb)}")

def ev_blackout(peer_id):
    c = get_chat(peer_id); users = get_chat_members(peer_id)
    if not users: send(peer_id, "❌"); return
    until = time.time()+120
    for u in users: c["muted"][str(u)] = {"until":until,"last_dm":0}
    save_cfg(cfg); send(peer_id, f"🌑 Блэкаут! {len(users)} в муте")

def ev_phoenix(peer_id):
    c = get_chat(peer_id); un = 0
    for k in list(c["muted"].keys()): del c["muted"][k]; un += 1
    users = get_chat_members(peer_id)
    if users:
        winners = random.sample(users, min(3,len(users)))
        for w in winners: c["nicknames"][str(w)] = "🔥 Феникс"
        save_cfg(cfg); send(peer_id, f"🔥 Снято: {un}\nТитул: " + ", ".join(mention(w,peer_id) for w in winners))
    else: save_cfg(cfg); send(peer_id, f"🔥 Снято: {un}")

def ev_custom(peer_id, name):
    ev = cfg.get("custom_events",{}).get(name.lower())
    if not ev: return False
    send(peer_id, f"🎉 {ev['name']}\n🏆 {ev['reward']}\n📋 {ev['requirement']}"); return True

EVENT_HANDLERS = {"рулетка":ev_roulette,"дуэль":ev_duel_ev,"лотерея":ev_lottery,"хэллоуин":ev_halloween,"новыйгод":ev_newyear,"admin_abuse":ev_admin_abuse,"гонка":ev_race,"золото":ev_gold,"клад":ev_treasure,"блэкаут":ev_blackout,"феникс":ev_phoenix}

def run_random_event(peer_id):
    ev = random.choice(list(EVENT_HANDLERS.keys())); send(peer_id, f"🎲 Выпал: {EVENTS_LIST[ev]}")
    try: EVENT_HANDLERS[ev](peer_id)
    except Exception as e: send(peer_id, f"❌ {e}")
    return ev

# ========== МАФИЯ ==========
MAFIA_MIN = 4; MAFIA_LOBBY = 60; MAFIA_DAY = 120; MAFIA_VOTE = 120
MAFIA_JOIN_WORDS = {"вступить","я","+","играю","в игре","мафия","го","за"}
R_MAFIA="🔫 Мафия"; R_DON="👑 Дон"; R_SHERIFF="👮 Шериф"; R_DOCTOR="💉 Доктор"; R_MANIAC="🔪 Маньяк"; R_LOVER="💋 Любовница"; R_JOURNALIST="📰 Журналист"; R_LAWYER="⚖️ Адвокат"; R_BEAUTY="💃 Красотка"; R_BOMB="💣 Бомба"; R_WEREWOLF="🐺 Оборотень"; R_SLEEPWALKER="🌙 Лунатик"; R_CIVILIAN="👤 Мирный"; R_POLICE="👮 Полицейский"
MAFIA_TEAM = {R_MAFIA, R_DON, R_LOVER, R_LAWYER}
CITY_TEAM = {R_SHERIFF,R_DOCTOR,R_JOURNALIST,R_BEAUTY,R_BOMB,R_WEREWOLF,R_SLEEPWALKER,R_CIVILIAN,R_POLICE}
NEUTRAL_TEAM = {R_MANIAC}
GAMES = {}; GAMES_LOCK = threading.Lock()

def _role_pool(n):
    if n == 4: pool = [R_MAFIA, R_POLICE, R_DOCTOR, R_CIVILIAN]
    elif n == 5: pool = [R_MAFIA, R_POLICE, R_DOCTOR, R_CIVILIAN, R_CIVILIAN]
    elif n == 6: pool = [R_MAFIA, R_DON, R_SHERIFF, R_DOCTOR, R_CIVILIAN, R_CIVILIAN]
    elif n == 7: pool = [R_MAFIA, R_DON, R_SHERIFF, R_DOCTOR, R_MANIAC, R_CIVILIAN, R_CIVILIAN]
    elif n == 8: pool = [R_MAFIA, R_DON, R_LOVER, R_SHERIFF, R_DOCTOR, R_MANIAC, R_CIVILIAN, R_CIVILIAN]
    elif n == 9: pool = [R_MAFIA,R_DON,R_LOVER,R_SHERIFF,R_DOCTOR,R_JOURNALIST,R_MANIAC,R_CIVILIAN,R_CIVILIAN]
    elif n == 10: pool = [R_MAFIA,R_DON,R_LOVER,R_LAWYER,R_SHERIFF,R_DOCTOR,R_JOURNALIST,R_MANIAC,R_CIVILIAN,R_CIVILIAN]
    elif n == 11: pool = [R_MAFIA,R_MAFIA,R_DON,R_LOVER,R_LAWYER,R_SHERIFF,R_DOCTOR,R_JOURNALIST,R_MANIAC,R_CIVILIAN,R_CIVILIAN]
    elif n == 12: pool = [R_MAFIA,R_MAFIA,R_DON,R_LOVER,R_LAWYER,R_SHERIFF,R_DOCTOR,R_JOURNALIST,R_BEAUTY,R_MANIAC,R_CIVILIAN,R_CIVILIAN]
    else:
        pool = [R_MAFIA,R_MAFIA,R_DON,R_LOVER,R_LAWYER,R_SHERIFF,R_DOCTOR,R_JOURNALIST,R_BEAUTY,R_BOMB,R_WEREWOLF,R_SLEEPWALKER,R_MANIAC,R_CIVILIAN,R_CIVILIAN,R_CIVILIAN]
        while len(pool) < n: pool.append(R_CIVILIAN)
    random.shuffle(pool); return pool[:n]

def mafia_start(peer_id, host_id):
    with GAMES_LOCK:
        if peer_id in GAMES: send(peer_id, "⚠️ Игра уже идёт."); return
        GAMES[peer_id] = {"phase":"lobby","lobby_players":[host_id],"players":{},"alive":set(),"host":host_id,"lobby_deadline":time.time()+MAFIA_LOBBY,"night_step_idx":0,"night_step":None,"night_actions":{},"day_deadline":0,"vote_deadline":0,"votes":{},"waiter_block":None,"round":0,"_alive_order":[],"lawyer_target":None}
    send(peer_id, f"🎭 МАФИЯ\nВступить: «вступить» / «+» / «я».\nМин: {MAFIA_MIN} | {MAFIA_LOBBY}с\n\n1. {get_vk_name(host_id)}")

def cmd_mafia(peer_id, uid, args):
    mafia_start(peer_id, uid)

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
        send(peer_id, "❌ Мало"); GAMES.pop(peer_id,None); return
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
    g["phase"]="night"; g["round"]+=1; g["night_step_idx"]=0; g["night_step"]=None; g["night_actions"]={}; g["waiter_block"]=None; g["votes"]={}; g["lawyer_target"]=None
    send(peer_id, f"🌃 Раунд {g['round']}. Город засыпает...")
    mafia_next_step(peer_id)

NIGHT_ORDER = [("mafia",{R_MAFIA,R_DON}),("don",{R_DON}),("sheriff",{R_SHERIFF,R_POLICE}),("doctor",{R_DOCTOR}),("lover",{R_LOVER}),("journalist",{R_JOURNALIST}),("lawyer",{R_LAWYER}),("beauty",{R_BEAUTY}),("maniac",{R_MANIAC})]

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
    actors = {"mafia":("🔫 Мафия...",(R_MAFIA,R_DON),"Кого убить"),"don":("👑 Дон...",(R_DON,),"Проверить (Шериф?)"),"sheriff":("👮 Шериф...",(R_SHERIFF,R_POLICE),"Кого проверить"),"doctor":("💉 Доктор...",(R_DOCTOR,),"Кого спасти"),"lover":("💋 Любовница...",(R_LOVER,),"Заблокировать"),"journalist":("📰 Журналист...",(R_JOURNALIST,),"Проверить 2 (2,5)"),"lawyer":("⚖️ Адвокат...",(R_LAWYER,),"Защитить"),"beauty":("💃 Красотка...",(R_BEAUTY,),"Забрать"),"maniac":("🔪 Маньяк...",(R_MANIAC,),"Кого убить")}
    if step not in actors: return
    title, roles, action = actors[step]; send(peer_id, title)
    for u,r in g["players"].items():
        if r in roles and u in g["alive"]: send_dm(u, f"{title}\n{action}:\n\n{lst}\n\nНомер.")

def mafia_parse_num(text, g, count=1):
    nums = re.findall(r"\d+", text)
    if not nums: return None
    order = g.get("_alive_order") or sorted(g["alive"])
    result = []
    for n in nums[:count]:
        i = int(n)-1
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
    actors = {"mafia":(R_MAFIA,R_DON),"don":(R_DON,),"sheriff":(R_SHERIFF,R_POLICE),"doctor":(R_DOCTOR,),"lover":(R_LOVER,),"journalist":(R_JOURNALIST,),"lawyer":(R_LAWYER,),"beauty":(R_BEAUTY,),"maniac":(R_MANIAC,)}
    if role not in actors.get(step, ()): return False
    if step in g["night_actions"] and step != "mafia": send_dm(uid, "Уже."); return True
    if step == "journalist":
        pair = mafia_parse_num(text, g, 2)
        if not pair: send_dm(uid, "⚠ Два номера: 2,5"); return True
        g["night_actions"][step] = pair
        a, b = pair
        same = (g["players"][a] in MAFIA_TEAM) == (g["players"][b] in MAFIA_TEAM)
        send_dm(uid, f"📰 {get_vk_name(a)} и {get_vk_name(b)} — " + ("ОДНА" if same else "РАЗНЫЕ"))
    else:
        t = mafia_parse_num(text, g, 1)
        if not t: send_dm(uid, "⚠ Номер"); return True
        g["night_actions"][step] = t; send_dm(uid, f"✅ {get_vk_name(t)}")
        if step == "sheriff":
            if g["players"].get(t) in MAFIA_TEAM: send_dm(uid, f"✅ {get_vk_name(t)} — МАФИЯ!")
            else: send_dm(uid, f"❌ {get_vk_name(t)} — не мафия")
        elif step == "don":
            if g["players"].get(t) in (R_SHERIFF, R_POLICE): send_dm(uid, f"👑 {get_vk_name(t)} — ШЕРИФ!")
            else: send_dm(uid, f"👑 {get_vk_name(t)} — не шериф")
    ann = {"mafia":"🔫 Мафия сделала выбор.","don":"👑 Дон сделал выбор.","sheriff":"👮 Шериф сделал выбор.","doctor":"💉 Доктор сделал выбор.","lover":"💋 Любовница сделала выбор.","journalist":"📰 Журналист сделал выбор.","lawyer":"⚖️ Адвокат сделал выбор.","beauty":"💃 Красотка сделала выбор.","maniac":"🔪 Маньяк сделал выбор."}
    send(peer_id, ann.get(step, ""))
    g["night_step"] = None; mafia_next_step(peer_id); return True

def mafia_resolve(peer_id):
    g = GAMES.get(peer_id)
    if not g: return
    send(peer_id, "🌅 Город просыпается...")
    acts = g["night_actions"]
    mt = acts.get("mafia"); mn = acts.get("maniac"); dt = acts.get("doctor"); bt = acts.get("beauty")
    prot = set()
    if dt: prot.add(dt)
    if bt: prot.add(bt)
    victims = []
    if mt and mt not in prot: victims.append(mt)
    if mn and mn not in prot and mn not in victims: victims.append(mn)
    if not victims: send(peer_id, "☀️ Никого не убили!")
    else:
        for v in victims: g["alive"].discard(v); send(peer_id, f"💀 Убит {get_vk_name(v)}. Роль: {g['players'][v]}")
    g["lawyer_target"] = acts.get("lawyer"); g["waiter_block"] = acts.get("lover")
    if mafia_check_win(peer_id): return
    g["phase"] = "day"; g["day_deadline"] = time.time() + MAFIA_DAY
    send(peer_id, f"🌞 День! {MAFIA_DAY}с")

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
    g["phase"]="voting"; g["votes"]={}; g["vote_deadline"]=time.time()+MAFIA_VOTE
    send(peer_id, f"🗳️ Голосование! У вас {MAFIA_VOTE//60} мин. Списки в ЛС.")
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
    if t in ("пропуск","skip","пас","0"): g["votes"][uid]="skip"; send_dm(uid,"✅"); return True
    target = mafia_parse_num(text, g, 1)
    if not target: send_dm(uid, "⚠ Номер"); return True
    if target == uid: send_dm(uid, "⚠ Себя нельзя"); return True
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
    if g.get("lawyer_target") == victim: send(peer_id, f"⚖️ Адвокат спас {get_vk_name(victim)}!"); mafia_start_night(peer_id); return
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
        for u,r in g["players"].items(): lines.append(f"— {get_vk_name(u)}: {r}")
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
            now = time.time(); ch = False
            for key,c in cfg.get("countries",{}).items():
                if not c.get("destroyed"): continue
                new_h = []
                for h in c.get("hostages",[]):
                    cit = get_citizenship(h)
                    if cit and cit.get("hostage_until",0) > now: new_h.append(h)
                    else:
                        if cit: cit["hostage_until"] = 0
                        send_dm(h, "🔓 Вас освободили!"); ch = True
                c["hostages"] = new_h
            if ch: save_cfg(cfg)
        except Exception as e: print(f"[hostage] {e}")

threading.Thread(target=hostage_ticker, daemon=True).start()

# ========== СТАТИСТИКА / ИНФО / ТИКЕТЫ ==========
def user_stats_text(uid, peer_id):
    uid = int(uid); role = role_display(uid, peer_id)
    c = get_chat(peer_id) if is_chat(peer_id) else None
    bl = 0; bg = False
    for ch in cfg.get("chats",{}).values():
        i = ch.get("banned",{}).get(str(uid))
        if i:
            bl += 1
            if i.get("global"): bg = True
    warns = 0; mute = False; nick = None
    if c:
        warns = c.get("warns",{}).get(str(uid),0)
        mu = get_mute_until(c.get("muted",{}).get(str(uid)))
        mute = bool(mu and mu > time.time())
        nick = c.get("nicknames",{}).get(str(uid))
    s = (c or {}).get("user_stats",{}).get(str(uid),{})
    bal = get_balance(peer_id, uid) if c else 0
    cit = get_citizenship(uid); ct = "—"
    if cit:
        cn = country_name(cit["country"]); rk = RANKS.get(cit["rank"],{}).get("name", cit["rank"]); ct = f"{cn} ({rk})"
    return "\n".join(["📊 Информация:", f"• {mention(uid,peer_id)}", f"• Роль: {role}", f"• Гражданство: {ct}", f"• VIP: {'✅' if is_vip(peer_id,uid) else 'Нет'}", f"• Баланс: {fmt_num(bal)} 💰", f"• Блокировок: {bl}", f"• Глоб блок: {'Да' if bg else 'Нет'}", f"• Предупреждения: {warns}/{cfg['max_warns']}", f"• Мут: {'Да' if mute else 'Нет'}", f"• Ник: {nick or 'Нет'}", f"• Сообщений: {s.get('msg_count',0)}", f"• Последнее: {s.get('last_text') or '—'}"])

def user_info_text(uid, peer_id):
    role = role_display(uid, peer_id)
    lines = [f"ℹ️ {mention(uid,peer_id)}:", f"• Роль: {role}"]
    c = get_chat(peer_id) if is_chat(peer_id) else None
    if c:
        lines.append(f"• Ник: {c.get('nicknames',{}).get(str(uid), '—')}")
        mu = get_mute_until(c.get("muted",{}).get(str(uid)))
        lines.append(f"• 🔇 Мут: {fmt_time(mu-time.time())}" if mu and mu > time.time() else "• 🔇 Мут: нет")
        w = c.get("warns",{}).get(str(uid),0)
        lines.append(f"• ⚠ Предупреждения: {w}/{cfg['max_warns']}")
        lines.append(f"• 💰 Баланс: {fmt_num(get_balance(peer_id, uid))}")
    return "\n".join(lines)

def build_staff_text(peer_id):
    c = get_chat(peer_id) if is_chat(peer_id) else None
    by_role = {}
    if c:
        for uid, rk in c.get("staff",{}).items(): by_role.setdefault(rk, []).append(uid)
    uids = [cfg["global_owner"]]
    if c:
        if c.get("owner"): uids.append(c["owner"])
        uids += [int(u) for u in c.get("staff",{}).keys()]
    prefetch_names(uids)
    lines = ["👮 Персонал (этот чат):", "", "🌐 Главный владелец:", f"— {mention(cfg['global_owner'], peer_id)}", "", "👑 Владелец беседы:"]
    lines.append(f"— {mention(c['owner'], peer_id)}" if c and c.get("owner") else "— (не назначен)")
    lines.append("")
    all_roles = dict(cfg["roles"])
    if c: all_roles.update(c.get("local_roles",{}))
    for key, role in sorted(all_roles.items(), key=lambda x: -x[1].get("priority",0)):
        lines.append(f"{role['name']}:")
        us = by_role.get(key, [])
        if us:
            for u in us: lines.append(f"— {mention(u, peer_id)}")
        else: lines.append("— ")
        lines.append("")
    return "\n".join(lines).rstrip()

def create_ticket(t, uid, peer_id, text):
    tid = cfg.get("next_ticket_id", 1)
    cfg["tickets"][str(tid)] = {"type":t,"from":uid,"peer_id":peer_id,"text":text,"status":"open","answer":"","answered_by":0,"answered_at":0,"created_at":int(time.time())}
    cfg["next_ticket_id"] = tid+1; save_cfg(cfg); return tid

def tickets_text():
    t = cfg.get("tickets",{})
    if not t: return "📭"
    lines = ["🎫 Тикеты:"]; n = 0
    for tid, info in sorted(t.items(), key=lambda x: int(x[0])):
        if info.get("status") != "open": continue
        emoji = "💡" if info.get("type") == "offer" else "❓"
        lines.append(f"#{tid} {emoji} от {mention(info['from'])} — {fmt_dt(info.get('created_at',0))}\n   {info['text'][:120]}")
        n += 1
    return "\n".join(lines) if n else "📭 Открытых нет."

def answer_ticket(tid, admin_id, txt):
    info = cfg.get("tickets",{}).get(str(tid))
    if not info: return False, "Не найден."
    if info.get("status") == "answered": return False, "Уже."
    info["status"]="answered"; info["answer"]=txt; info["answered_by"]=admin_id; info["answered_at"]=int(time.time()); save_cfg(cfg)
    send_dm(info["from"], f"✅ Ответ #{tid}:\n❓ {info['text'][:200]}\n✅ {txt}")
    try: send(info["peer_id"], f"🎫 Ответ #{tid}")
    except: pass
    return True, "OK"

# ========== ПРИВЕТСТВИЕ ==========
def handle_welcome(peer_id, action):
    if not is_chat(peer_id): return
    inv = action.get("member_id")
    if not inv or inv <= 0: return
    c = get_chat(peer_id)
    if c.get("welcome") is False or inv == BOT_ID: return
    if str(inv) in c.get("banned",{}): return
    prefetch_names([inv])
    nick = c.get("nicknames",{}).get(str(inv))
    u = f"[id{inv}|{nick}]" if nick else f"[id{inv}|{get_vk_name(inv)}]"
    send(peer_id, f"╔══════════════════════╗\n   👋 ДОБРО ПОЖАЛОВАТЬ!\n╚══════════════════════╝\n\n🌟 Рады видеть тебя, {u}!\n\n📋 Что тут:\n├ 🎮 /баланс\n├ 🌍 /гражданство\n├ 🏛 /госскоманды\n├ 🌉 /граница /склад /перевозка\n├ 🎭 /ивент\n└ 📖 /help /rules\n\n⚡ Приятной игры!")

# ========== СПРАВКА ==========
def build_help():
    return f"""📋 Команды:

🎮 /баланс /топ /приз /подписка /buybiz /mybiz /collect /донат /передать

🎲 /казино /дуэль /монетка /кубик /слоты /краш /дартс /колесо /рулетка /блэкджек /мины /башня /кейс /гонка /рыбалка

🌍 /страны /гражданство /паспорт /страна /граждане /города /казна /правительство /армия /выборы /голос /очки
🏛 /госскоманды — все команды страны

🌉 /граница /виза /транспорт /склад /перевозка /контрабанда

⚔️ /войны /война /захват /мир /завершить_конфликт /коалиции /коалиция /коалпомощь
/мобилизация /сделать /пво /запуск /задание /выполнитьзадание
🛸 /дрон /перехват
🚨 /сирена /воздухтревога
🎖️ /звание /повысить

🎟️ /promo /promolist
🎭 /ивент /мафия

🛡️ /warn /unwarn /mute /unmute /nick /rnick /kick /ban /unban /gban /clear /banlist /tickets /adt

👑 /setrole /removestaff /newrole /delrole /setlog /build
/q — покинуть чат
/rules — правила
/раздача <сумма> <s|m|h|d> <текст>
/взять — забрать из раздачи

🌐 GLOBAL /объявление /createivent /grole /removerole /gstaff /builds /устгражданство /устпрезидент /выдать /вернуть

💰 Баланс: {START_BALANCE} | 🎁 /приз до {fmt_num(PRIZE_MAX)}
⚔️ Война: {fmt_num(WAR_COST)} 💵 | 🎖️ Войск: {fmt_num(BASE_ARMY)}
⚠️ 3 варна = исключение"""

def build_gos_cmds():
    return f"""🏛 КОМАНДЫ СТРАНЫ

📖 Гражданство
/страны /гражданство /паспорт /страна /граждане /города /казна /казна история
/правительство /должности /армия /выборы /выдвинуться /голос /очки
/компания /регистрация ООО /донат

⚖️ Правительство
/налоги /назначить /снятьминистра /воинскоезвание
/улучшить_страну /улучшитьстрану /постройки /построить /госпроект /вооружение

⚔️ Армия
/мобилизация /демобилизация /сделать /установить пво /пво
/запуск ракета|бпла <кол> <страна> /запуск ядерная ракета <страна>
/задание → /выполнитьзадание
/upgrade_army /звание /повысить
🛸 /дрон /перехват (20%) /сирена

🌉 Границы
/граница открыть|закрыть [страна]
/виза выдать|забрать @user
/транспорт купить <тип> /склад <товар> <кол> /склад
/перевозка <страна> <товар> <кол> <транспорт>
/контрабанда <страна> <товар> <кол>

Товары: еда, оружие, ресурсы, топливо, деньги
Транспорт: грузовик, поезд, корабль, самолёт
Пошлина: {int(CUSTOMS_RATE*100)}% | Штраф контрабанды: ×{SMUGGLE_FINE}"""
    # ========== ИГРЫ ==========
def _bet(peer_id, uid, args, name):
    if not args or not args[0].isdigit():
        send(peer_id, f"⚠ /{name} <ставка>"); return None
    bet = int(args[0])
    if bet <= 0: send(peer_id, "⚠ Ставка > 0"); return None
    bal = get_balance(peer_id, uid)
    if bal < bet: send(peer_id, f"❌ У вас {fmt_num(bal)} 💵"); return None
    add_balance(peer_id, uid, -bet); return bet

def cmd_casino(peer_id, uid, args):
    bet = _bet(peer_id, uid, args, "казино")
    if not bet: return
    if len(args) < 2 or not args[1].isdigit():
        if random.random() < 0.48:
            w = int(bet*2*full_vip_mult(peer_id, uid)); add_balance(peer_id, uid, w)
            send(peer_id, f"🎰 Удача! +{fmt_num(w)} 💵")
        else:
            send(peer_id, f"🎰 Не повезло. -{fmt_num(bet)} 💵")
        return
    n = random.randint(1, 10); guess = int(args[1])
    if guess == n:
        w = int(bet*5*full_vip_mult(peer_id, uid)); add_balance(peer_id, uid, w)
        send(peer_id, f"🎰 Выпало {n}! 🎉 x5 +{fmt_num(w)} 💵")
    else:
        send(peer_id, f"🎰 Выпало {n}. 💀 -{fmt_num(bet)} 💵")

def cmd_coin(peer_id, uid, args):
    bet = _bet(peer_id, uid, args, "монетка")
    if not bet: return
    side = (args[1].lower() if len(args) > 1 else "орёл")
    if side in ("о", "орёл", "орел", "heads", "h"): side = "орёл"
    elif side in ("р", "решка", "tails", "t"): side = "решка"
    else:
        send(peer_id, "⚠ орёл/решка"); add_balance(peer_id, uid, bet); return
    r = random.choice(["орёл", "решка"])
    if r == side:
        w = int(bet*2*full_vip_mult(peer_id, uid)); add_balance(peer_id, uid, w)
        send(peer_id, f"🪙 {r}! 🎉 +{fmt_num(w)} 💵")
    else:
        send(peer_id, f"🪙 {r}. -{fmt_num(bet)} 💵")

def cmd_dice(peer_id, uid, args):
    bet = _bet(peer_id, uid, args, "кубик")
    if not bet: return
    r = random.randint(1, 6)
    if r >= 5:
        w = int(bet*2*full_vip_mult(peer_id, uid)); add_balance(peer_id, uid, w)
        send(peer_id, f"🎲 {r} — 🎉 +{fmt_num(w)} 💵")
    elif r == 4:
        w = int(bet*1.5*full_vip_mult(peer_id, uid)); add_balance(peer_id, uid, w)
        send(peer_id, f"🎲 {r} — +{fmt_num(w)} 💵")
    else:
        send(peer_id, f"🎲 {r} — -{fmt_num(bet)} 💵")

def cmd_duel(peer_id, uid, args, reply_msg):
    target = extract_user(" ".join(args), reply_msg)
    if not target or target == uid: send(peer_id, "⚠ /дуэль @user <ставка>"); return
    bet = next((int(a) for a in args if a.isdigit() and int(a) > 0), None)
    if not bet: send(peer_id, "⚠ Ставка"); return
    if get_balance(peer_id, uid) < bet or get_balance(peer_id, target) < bet:
        send(peer_id, "❌ У кого-то мало 💵"); return
    win = random.choice([uid, target]); lose = target if win == uid else uid
    add_balance(peer_id, win, bet); add_balance(peer_id, lose, -bet)
    add_activation(peer_id, win, 1); save_cfg(cfg)
    send(peer_id, f"⚔️ Дуэль!\n🏆 {mention(win, peer_id)} +{fmt_num(bet)} 💵\n💀 {mention(lose, peer_id)} -{fmt_num(bet)}")

SLOT_SYMS = ["🍒", "🍋", "🍊", "🍇", "⭐", "💎", "7️⃣"]

def cmd_slots(peer_id, uid, args):
    bet = _bet(peer_id, uid, args, "слоты")
    if not bet: return
    r = [random.choice(SLOT_SYMS) for _ in range(3)]
    line = " | ".join(r)
    if r[0] == r[1] == r[2]:
        mult = 10 if r[0] == "7️⃣" else (7 if r[0] == "💎" else (5 if r[0] == "⭐" else 3))
        w = int(bet*mult*full_vip_mult(peer_id, uid)); add_balance(peer_id, uid, w)
        send(peer_id, f"🎰 {line}\n🎉 x{mult}! +{fmt_num(w)} 💵")
    elif r[0] == r[1] or r[1] == r[2] or r[0] == r[2]:
        w = int(bet*1.5*full_vip_mult(peer_id, uid)); add_balance(peer_id, uid, w)
        send(peer_id, f"🎰 {line}\n✨ x1.5! +{fmt_num(w)} 💵")
    else:
        send(peer_id, f"🎰 {line}\n💀 -{fmt_num(bet)} 💵")

def cmd_crash(peer_id, uid, args):
    bet = _bet(peer_id, uid, args, "краш")
    if not bet: return
    target = 2.0
    if len(args) > 1:
        try: target = max(1.1, min(10.0, float(args[1].replace(",", "."))))
        except: pass
    crash = random.uniform(1.0, 6.0)
    if target <= crash:
        w = int(bet*target*full_vip_mult(peer_id, uid)); add_balance(peer_id, uid, w)
        send(peer_id, f"📈 Краш на x{crash:.2f}\n✅ Забрали x{target:.2f}\n+{fmt_num(w)} 💵")
    else:
        send(peer_id, f"📈 Краш на x{crash:.2f}\n❌ Поздно\n-{fmt_num(bet)} 💵")

def cmd_darts(peer_id, uid, args):
    bet = _bet(peer_id, uid, args, "дартс")
    if not bet: return
    h = random.random()
    if h < 0.10: mult, msg = 5, "🎯 В яблочко!"
    elif h < 0.30: mult, msg = 3, "🎯 Отлично!"
    elif h < 0.60: mult, msg = 2, "🎯 Хорошо"
    elif h < 0.85: mult, msg = 1, "🎯 Попал"
    else: mult, msg = 0, "💨 Мимо"
    if mult:
        w = int(bet*mult*full_vip_mult(peer_id, uid)); add_balance(peer_id, uid, w)
        send(peer_id, f"{msg}\nx{mult}! +{fmt_num(w)} 💵")
    else:
        send(peer_id, f"{msg}\n-{fmt_num(bet)} 💵")

WHEEL = [0, 0.5, 0.5, 1.5, 2, 2, 3, 5, 10]

def cmd_wheel(peer_id, uid, args):
    bet = _bet(peer_id, uid, args, "колесо")
    if not bet: return
    x = random.choice(WHEEL)
    if x == 0:
        send(peer_id, f"🎡 x0 💀 -{fmt_num(bet)} 💵")
    else:
        w = int(bet*x*full_vip_mult(peer_id, uid)); add_balance(peer_id, uid, w)
        send(peer_id, f"🎡 x{x}! +{fmt_num(w)} 💵")

RED = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}

def cmd_roulette(peer_id, uid, args):
    if len(args) < 2 or not args[0].isdigit():
        send(peer_id, "⚠ /рулетка <ставка> <красное|чёрное|зеро|число>"); return
    bet = int(args[0]); choice = args[1].lower()
    if bet <= 0: send(peer_id, "⚠"); return
    if get_balance(peer_id, uid) < bet: send(peer_id, "❌"); return
    add_balance(peer_id, uid, -bet)
    n = random.randint(0, 36)
    color = "зелёное" if n == 0 else ("красное" if n in RED else "чёрное")
    mult = 0
    if choice in ("красное", "красный", "red") and color == "красное": mult = 2
    elif choice in ("чёрное", "черное", "черный", "black") and color == "чёрное": mult = 2
    elif choice in ("зеро", "0", "green", "зелёное") and n == 0: mult = 14
    elif choice.isdigit() and int(choice) == n: mult = 36
    if mult:
        w = int(bet*mult*full_vip_mult(peer_id, uid)); add_balance(peer_id, uid, w)
        send(peer_id, f"🎡 {n} {color}\n🎉 x{mult}! +{fmt_num(w)} 💵")
    else:
        send(peer_id, f"🎡 {n} {color}\n💀 -{fmt_num(bet)} 💵")

def _card(): return random.randint(1, 11)

def cmd_bj(peer_id, uid, args):
    bet = _bet(peer_id, uid, args, "блэкджек")
    if not bet: return
    p = _card() + _card(); d = _card() + _card()
    while p < 17: p += _card()
    while d < 17: d += _card()
    if p > 21:
        send(peer_id, f"🃏 Вы: {p} (перебор)\n💀 -{fmt_num(bet)} 💵"); return
    if d > 21 or p > d:
        w = int(bet*2*full_vip_mult(peer_id, uid)); add_balance(peer_id, uid, w)
        send(peer_id, f"🃏 Вы: {p} | Дилер: {d}\n🎉 +{fmt_num(w)} 💵")
    elif p == d:
        add_balance(peer_id, uid, bet); send(peer_id, f"🃏 Вы: {p} | Дилер: {d}\n🤝 Ничья")
    else:
        send(peer_id, f"🃏 Вы: {p} | Дилер: {d}\n💀 -{fmt_num(bet)} 💵")

def cmd_mines(peer_id, uid, args):
    bet = _bet(peer_id, uid, args, "мины")
    if not bet: return
    if random.random() < 0.6:
        w = int(bet*1.8*full_vip_mult(peer_id, uid)); add_balance(peer_id, uid, w)
        send(peer_id, f"💣 Поле 3x3, выжили! +{fmt_num(w)} 💵")
    else:
        send(peer_id, f"💣 Взрыв! -{fmt_num(bet)} 💵")

def cmd_tower(peer_id, uid, args):
    bet = _bet(peer_id, uid, args, "башня")
    if not bet: return
    floor = 0
    while floor < 5 and random.random() < 0.7: floor += 1
    if floor == 0:
        send(peer_id, f"🏗️ Упали на 0\n💀 -{fmt_num(bet)} 💵"); return
    mult = 1.5 ** floor
    w = int(bet*mult*full_vip_mult(peer_id, uid)); add_balance(peer_id, uid, w)
    send(peer_id, f"🏗️ Этаж {floor}/5\nx{mult:.2f} +{fmt_num(w)} 💵")

CASE_PRIZES = [50, 100, 200, 500, 1000, 5000]

def cmd_case(peer_id, uid, args):
    bet = _bet(peer_id, uid, args, "кейс")
    if not bet: return
    prize = random.choice(CASE_PRIZES)
    w = int(prize*full_vip_mult(peer_id, uid)); add_balance(peer_id, uid, w)
    tag = "🎉" if w >= bet*2 else ""
    send(peer_id, f"🎁 Кейс: +{fmt_num(w)} 💵 {tag}")

def cmd_race(peer_id, uid, args):
    bet = _bet(peer_id, uid, args, "гонка")
    if not bet: return
    me = random.randint(1, 100); op = random.randint(1, 100)
    if me > op:
        w = int(bet*2*full_vip_mult(peer_id, uid)); add_balance(peer_id, uid, w)
        send(peer_id, f"🏎️ Вы {me} vs {op}\n🥇 +{fmt_num(w)} 💵")
    else:
        send(peer_id, f"🏎️ Вы {me} vs {op}\n🥈 -{fmt_num(bet)} 💵")

FISH = [("🐟", 1), ("🐠", 2), ("🦈", 5), ("🐋", 10), ("👟", 0), ("🗑️", 0)]

def cmd_fish(peer_id, uid, args):
    bet = _bet(peer_id, uid, args, "рыбалка")
    if not bet: return
    name, mult = random.choice(FISH)
    if mult:
        w = int(bet*mult*full_vip_mult(peer_id, uid)); add_balance(peer_id, uid, w)
        send(peer_id, f"🎣 {name} x{mult}\n+{fmt_num(w)} 💵")
    else:
        send(peer_id, f"🎣 {name} 💀 -{fmt_num(bet)} 💵")

# ========== Q / RULES ==========
def cmd_quit(peer_id, uid):
    if not is_chat(peer_id): send(peer_id, "❌"); return
    cid = chat_id_from_peer(peer_id)
    if not cid: return
    try:
        api.messages.removeChatUser(chat_id=cid, user_id=BOT_ID)
    except Exception as e: send(peer_id, f"❌ {e}")

def cmd_rules(peer_id, uid):
    send(peer_id, """📜 ПРАВИЛА ЧАТА

1️⃣ Уважайте друг друга.
2️⃣ Без спама, флуда и капса.
3️⃣ Без рекламы и NSFW.
4️⃣ Без попрошайничества.
5️⃣ Подчиняйтесь модерации.
6️⃣ Без обхода мута/бана.

⚠️ 3 предупреждения = исключение.
🛡️ Решения админов окончательные.
📩 /report <текст> — жалоба администрации.""")

# ========== РАЗДАЧА / ВЗЯТЬ ==========
def cmd_giveaway(peer_id, uid, args):
    if len(args) < 3: send(peer_id, "⚠ /раздача <сумма> <s|m|h|d> <текст>"); return
    if not args[0].isdigit(): send(peer_id, "⚠ Сумма"); return
    amount = int(args[0])
    if amount <= 0: send(peer_id, "⚠ > 0"); return
    m = re.match(r"^(\d+)([smhd])$", args[1].lower())
    if not m: send(peer_id, "⚠ Формат: 30s, 5m, 2h, 1d"); return
    secs = int(m.group(1)) * {"s": 1, "m": 60, "h": 3600, "d": 86400}[m.group(2)]
    if secs < 10: send(peer_id, "⚠ Минимум 10с"); return
    if secs > 7*86400: send(peer_id, "⚠ Максимум 7 дней"); return
    text = " ".join(args[2:])[:200]
    if get_balance(peer_id, uid) < amount:
        send(peer_id, f"❌ У вас {fmt_num(get_balance(peer_id, uid))} 💵"); return
    add_balance(peer_id, uid, -amount)
    cfg.setdefault("giveaways", {})[str(peer_id)] = {"host": uid, "pool": amount, "text": text, "ends_at": int(time.time()) + secs, "taken": []}
    save_cfg(cfg)
    send(peer_id, f"🎁 РАЗДАЧА!\n📝 {text}\n💰 Банк: {fmt_num(amount)} 💵\n⏱ {fmt_time(secs)}\n\n/взять — участвовать")

def cmd_take(peer_id, uid, args):
    g = cfg.get("giveaways", {}).get(str(peer_id))
    if not g: send(peer_id, "📭 Активной раздачи нет."); return
    if time.time() > g["ends_at"]: send(peer_id, "⌛ Раздача завершена."); return
    if uid in g["taken"]: send(peer_id, "⚠ Уже участвуете."); return
    g["taken"].append(uid); save_cfg(cfg)
    send(peer_id, f"✅ {mention(uid, peer_id)} участвует! ({len(g['taken'])})")

def giveaway_ticker():
    while True:
        time.sleep(5)
        try:
            now = time.time(); ch = False
            for pid_str, g in list(cfg.get("giveaways", {}).items()):
                if now < g["ends_at"]: continue
                pid = int(pid_str); taken = g["taken"]
                if not taken:
                    add_balance(pid, g["host"], g["pool"])
                    send(pid, "⌛ Раздача завершена. Участников нет — деньги возвращены.")
                else:
                    per = g["pool"] // len(taken); rem = g["pool"] - per*len(taken)
                    lines = [f"🎁 РАЗДАЧА завершена! ({len(taken)} участников)"]
                    for u in taken:
                        add_balance(pid, u, per); lines.append(f"• {mention(u, pid)} +{fmt_num(per)} 💵")
                    if rem: add_balance(pid, taken[0], rem)
                    send(pid, "\n".join(lines))
                cfg["giveaways"].pop(pid_str, None); ch = True
            if ch: save_cfg(cfg)
        except Exception as e: print(f"[giveaway] {e}")

threading.Thread(target=giveaway_ticker, daemon=True).start()
# ========== МОДЕРАЦИЯ ==========
def _need_reply_or_mention(args, reply_msg, peer_id):
    t = extract_user(" ".join(args), reply_msg)
    if not t:
        send(peer_id, "⚠ Укажите @user или ответьте на сообщение."); return None
    if t == BOT_ID: send(peer_id, "🤖 Нельзя применить к боту."); return None
    if t == int(cfg["global_owner"]):
        send(peer_id, "⛔ Нельзя применить к главному владельцу."); return None
    return t

def _check_admin_or_warn(peer_id):
    if not is_bot_admin(peer_id):
        send(peer_id, WAIT_STAR_TEXT); return False
    return True

def cmd_warn(peer_id, uid, args, reply_msg):
    if not is_chat(peer_id): send(peer_id, "❌"); return
    c = get_chat(peer_id)
    t = _need_reply_or_mention(args, reply_msg, peer_id)
    if not t: return
    if c.get("owner") == t or int(cfg["global_owner"]) == t:
        send(peer_id, "⛔ Нельзя."); return
    if c.get("staff", {}).get(str(t)):
        send(peer_id, "⛔ Это модератор."); return
    wr = c.setdefault("warns", {})
    wr[str(t)] = wr.get(str(t), 0) + 1
    cnt = wr[str(t)]
    save_cfg(cfg)
    send(peer_id, f"⚠️ {mention(t, peer_id)} получил предупреждение ({cnt}/{cfg['max_warns']})")
    send_dm(t, f"⚠️ Вам выдано предупреждение в беседе.\nТекущее: {cnt}/{cfg['max_warns']}")
    if cnt >= cfg["max_warns"]:
        if not _check_admin_or_warn(peer_id): return
        cid = chat_id_from_peer(peer_id)
        if cid:
            try:
                api.messages.removeChatUser(chat_id=cid, user_id=t)
                send(peer_id, f"🚪 {mention(t, peer_id)} исключён (лимит варнов).")
                wr[str(t)] = 0; save_cfg(cfg)
            except Exception as e:
                send(peer_id, f"❌ Не удалось исключить: {e}")
                send(peer_id, WAIT_STAR_TEXT)

def cmd_unwarn(peer_id, uid, args, reply_msg):
    if not is_chat(peer_id): send(peer_id, "❌"); return
    c = get_chat(peer_id)
    t = _need_reply_or_mention(args, reply_msg, peer_id)
    if not t: return
    wr = c.setdefault("warns", {}); cur = wr.get(str(t), 0)
    if cur <= 0: send(peer_id, "ℹ У пользователя нет варнов."); return
    wr[str(t)] = cur - 1; save_cfg(cfg)
    send(peer_id, f"✅ {mention(t, peer_id)} — варн снят ({wr[str(t)]}/{cfg['max_warns']})")
    send_dm(t, f"✅ С вас сняли предупреждение. Осталось: {wr[str(t)]}")

def cmd_mute(peer_id, uid, args, reply_msg):
    if not is_chat(peer_id): send(peer_id, "❌"); return
    c = get_chat(peer_id)
    t = _need_reply_or_mention(args, reply_msg, peer_id)
    if not t: return
    if c.get("owner") == t or int(cfg["global_owner"]) == t:
        send(peer_id, "⛔ Нельзя."); return
    minutes = cfg.get("default_mute_minutes", 30)
    nums = [int(a) for a in args if a.isdigit()]
    if nums: minutes = nums[0]
    if minutes < 1 or minutes > 43200: send(peer_id, "⚠ 1–43200 минут"); return
    until = time.time() + minutes*60
    c.setdefault("muted", {})[str(t)] = {"until": until, "last_dm": 0}
    save_cfg(cfg)
    send(peer_id, f"🔇 {mention(t, peer_id)} в муте на {fmt_time(minutes*60)}")
    mute_notify_dm(t, minutes)

def cmd_unmute(peer_id, uid, args, reply_msg):
    if not is_chat(peer_id): send(peer_id, "❌"); return
    c = get_chat(peer_id)
    t = _need_reply_or_mention(args, reply_msg, peer_id)
    if not t: return
    muted = c.get("muted", {})
    if str(t) not in muted: send(peer_id, "ℹ Не в муте."); return
    del muted[str(t)]; save_cfg(cfg)
    send(peer_id, f"🔊 {mention(t, peer_id)} размучен")
    mute_expired_dm(t)

def cmd_nick(peer_id, uid, args, reply_msg):
    if not is_chat(peer_id): send(peer_id, "❌"); return
    c = get_chat(peer_id)
    t = extract_user(" ".join(args), reply_msg) or uid
    if t == BOT_ID: send(peer_id, "🤖"); return
    leftover = [a for a in args if not re.match(r"\[id\d+\|", a) and not re.match(r"@id\d+", a)]
    nick = " ".join(leftover).strip()
    if not nick: send(peer_id, "⚠ /nick @user <ник>"); return
    if len(nick) > 32: send(peer_id, "⚠ Максимум 32 символа."); return
    c.setdefault("nicknames", {})[str(t)] = nick; save_cfg(cfg)
    send(peer_id, f"✅ Ник {mention(t, peer_id)} → «{nick}»")

def cmd_rnick(peer_id, uid, args, reply_msg):
    if not is_chat(peer_id): send(peer_id, "❌"); return
    c = get_chat(peer_id)
    t = extract_user(" ".join(args), reply_msg) or uid
    if str(t) in c.get("nicknames", {}):
        del c["nicknames"][str(t)]; save_cfg(cfg)
        send(peer_id, f"✅ Ник сброшен для {mention(t, peer_id)}")
    else:
        send(peer_id, "ℹ У пользователя нет кастомного ника.")

def cmd_kick(peer_id, uid, args, reply_msg):
    if not is_chat(peer_id): send(peer_id, "❌"); return
    c = get_chat(peer_id)
    t = _need_reply_or_mention(args, reply_msg, peer_id)
    if not t: return
    if c.get("owner") == t: send(peer_id, "⛔ Нельзя."); return
    if not _check_admin_or_warn(peer_id): return
    cid = chat_id_from_peer(peer_id)
    try:
        api.messages.removeChatUser(chat_id=cid, user_id=t)
        send(peer_id, f"🚪 {mention(t, peer_id)} исключён.")
    except Exception as e:
        send(peer_id, f"❌ {e}\n{WAIT_STAR_TEXT}")

def cmd_ban(peer_id, uid, args, reply_msg):
    if not is_chat(peer_id): send(peer_id, "❌"); return
    c = get_chat(peer_id)
    t = _need_reply_or_mention(args, reply_msg, peer_id)
    if not t: return
    if c.get("owner") == t: send(peer_id, "⛔ Нельзя."); return
    reason = " ".join([a for a in args if not re.match(r"\[id\d+\|", a) and not re.match(r"@id\d+", a)])[:200] or "без причины"
    c.setdefault("banned", {})[str(t)] = {"at": int(time.time()), "by": uid, "reason": reason, "global": False}
    save_cfg(cfg)
    if is_bot_admin(peer_id):
        cid = chat_id_from_peer(peer_id)
        try: api.messages.removeChatUser(chat_id=cid, user_id=t)
        except: pass
    send(peer_id, f"🚫 {mention(t, peer_id)} забанен. Причина: {reason}")

def cmd_unban(peer_id, uid, args, reply_msg):
    if not is_chat(peer_id): send(peer_id, "❌"); return
    c = get_chat(peer_id)
    t = extract_user(" ".join(args), reply_msg)
    if not t: send(peer_id, "⚠ Укажите @user"); return
    if str(t) not in c.get("banned", {}): send(peer_id, "ℹ Не в бане."); return
    del c["banned"][str(t)]; save_cfg(cfg)
    send(peer_id, f"✅ {mention(t, peer_id)} разбанен в этом чате.")

def cmd_gban(peer_id, uid, args, reply_msg):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔ Global."); return
    t = extract_user(" ".join(args), reply_msg)
    if not t: send(peer_id, "⚠"); return
    if t == int(cfg["global_owner"]): send(peer_id, "⛔"); return
    reason = " ".join([a for a in args if not re.match(r"\[id\d+\|", a) and not re.match(r"@id\d+", a)])[:200] or "gban"
    for ch in cfg.get("chats", {}).values():
        ch.setdefault("banned", {})[str(t)] = {"at": int(time.time()), "by": uid, "reason": reason, "global": True}
    save_cfg(cfg)
    for p in cfg.get("known_peers", []):
        if not is_bot_admin(p): continue
        cid = chat_id_from_peer(p)
        if not cid: continue
        try: api.messages.removeChatUser(chat_id=cid, user_id=t)
        except: pass
    send(peer_id, f"🌐 {mention(t, peer_id)} ГЛОБАЛЬНО забанен. Причина: {reason}")
    send_dm(t, f"🌐 Вы глобально забанены во всех чатах бота.\nПричина: {reason}")

def cmd_ungban(peer_id, uid, args, reply_msg):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    t = extract_user(" ".join(args), reply_msg)
    if not t: send(peer_id, "⚠"); return
    cnt = 0
    for ch in cfg.get("chats", {}).values():
        if str(t) in ch.get("banned", {}):
            del ch["banned"][str(t)]; cnt += 1
    save_cfg(cfg)
    send(peer_id, f"✅ Снято {cnt} глобальных банов с {mention(t, peer_id)}")

def cmd_clear(peer_id, uid, args):
    if not is_chat(peer_id): send(peer_id, "❌"); return
    if not _check_admin_or_warn(peer_id): return
    cnt = 50
    if args and args[0].isdigit(): cnt = min(200, max(1, int(args[0])))
    try:
        mids = api.messages.getHistory(peer_id=peer_id, count=cnt)["items"]
        ids = [m["id"] for m in mids if m["id"] > 0]
        for i in range(0, len(ids), 100):
            try: api.messages.delete(message_ids=",".join(map(str, ids[i:i+100])), delete_for_all=1)
            except: pass
        send(peer_id, f"🧹 Удалено {len(ids)} сообщений.")
    except Exception as e:
        send(peer_id, f"❌ {e}")

def cmd_banlist(peer_id, uid):
    if not is_chat(peer_id): send(peer_id, "❌"); return
    c = get_chat(peer_id); b = c.get("banned", {})
    if not b: send(peer_id, "📭 Банлист пуст."); return
    prefetch_names([int(k) for k in b.keys()])
    lines = ["🚫 Банлист:"]
    for t, info in b.items():
        g = "🌐" if info.get("global") else ""
        lines.append(f"{g} {mention(t, peer_id)} — {info.get('reason', '?')} ({fmt_dt(info.get('at', 0))})")
    send(peer_id, "\n".join(lines))

def cmd_report(peer_id, uid, args):
    if not is_chat(peer_id): send(peer_id, "❌"); return
    if not args: send(peer_id, "⚠ /report <текст>"); return
    text = " ".join(args)[:400]
    tid = create_ticket("report", uid, peer_id, text)
    send(peer_id, f"✅ Жалоба #{tid} отправлена администрации.")
    if cfg.get("log_peer_id"):
        try:
            api.messages.send(peer_id=cfg["log_peer_id"], message=f"📩 Жалоба #{tid}\nОт: {mention(uid)}\n{text}", random_id=int(time.time()*1000))
        except: pass

def cmd_offer(peer_id, uid, args):
    if not args: send(peer_id, "⚠ /offer <текст>"); return
    text = " ".join(args)[:400]
    tid = create_ticket("offer", uid, peer_id, text)
    send(peer_id, f"✅ Предложение #{tid} отправлено.")

def cmd_adt(peer_id, uid, args):
    if len(args) < 2: send(peer_id, "⚠ /adt <id> <текст>"); return
    try: tid = int(args[0])
    except: send(peer_id, "⚠ Числовой ID."); return
    txt = " ".join(args[1:])[:400]
    ok, msg = answer_ticket(tid, uid, txt)
    send(peer_id, "✅" if ok else f"❌ {msg}")

# ========== РОЛИ ==========
def cmd_setrole(peer_id, uid, args, reply_msg, text):
    if not is_chat(peer_id): send(peer_id, "❌"); return
    c = get_chat(peer_id)
    is_owner = (uid == int(cfg["global_owner"])) or (c.get("owner") == uid)
    if not is_owner: send(peer_id, "⛔"); return
    t = extract_user(text, reply_msg)
    if not t: send(peer_id, "⚠ /setrole @user <роль>"); return
    ra = [a for a in args if not re.match(r"\[id\d+\|", a) and not re.match(r"@id\d+", a)]
    ri = " ".join(ra).strip()
    if not ri: send(peer_id, "⚠"); return
    rk = find_role_by_input(ri, peer_id)
    if not rk: send(peer_id, f"⚠ «{ri}» не найдена."); return
    role = find_role(rk, peer_id)
    if not role: send(peer_id, "⚠"); return
    if not (uid == int(cfg["global_owner"])):
        my_rk = get_role_key(uid, peer_id)
        my_role = find_role(my_rk, peer_id)
        if my_role and role.get("priority", 0) >= my_role.get("priority", 0):
            send(peer_id, "⛔ Нельзя выдать роль не ниже своей."); return
    c.setdefault("staff", {})[str(t)] = rk; save_cfg(cfg)
    send(peer_id, f"✅ {mention(t, peer_id)} — {role['name']}")
    send_dm(t, f"🛡️ Вам выдана роль: {role['name']} в беседе.")

def cmd_removestaff(peer_id, uid, args, reply_msg, text):
    if not is_chat(peer_id): send(peer_id, "❌"); return
    c = get_chat(peer_id)
    if not (uid == int(cfg["global_owner"]) or c.get("owner") == uid): send(peer_id, "⛔"); return
    t = extract_user(text, reply_msg)
    if not t: send(peer_id, "⚠"); return
    rem = c.setdefault("staff", {}).pop(str(t), None); save_cfg(cfg)
    send(peer_id, "❌ Снят." if rem else "ℹ Не было роли.")

def cmd_newrole(peer_id, uid, args):
    if not is_chat(peer_id): send(peer_id, "❌"); return
    c = get_chat(peer_id)
    if not (uid == int(cfg["global_owner"]) or c.get("owner") == uid): send(peer_id, "⛔"); return
    if len(args) < 2: send(peer_id, "⚠ /newrole <key> <Имя> [priority]"); return
    key = args[0].lower()
    if key in cfg["roles"] or key in c.get("local_roles", {}):
        send(peer_id, "⚠ Ключ занят."); return
    name = args[1]
    priority = 10
    if len(args) >= 3 and args[2].isdigit(): priority = int(args[2])
    cmds = commands_for_priority(priority)
    c.setdefault("local_roles", {})[key] = {"name": name, "priority": priority, "commands": cmds}
    save_cfg(cfg)
    send(peer_id, f"✅ Роль «{name}» создана (ключ: {key}, приоритет: {priority}, {len(cmds)} команд)")

def cmd_delrole(peer_id, uid, args):
    if not is_chat(peer_id): send(peer_id, "❌"); return
    c = get_chat(peer_id)
    if not (uid == int(cfg["global_owner"]) or c.get("owner") == uid): send(peer_id, "⛔"); return
    if not args: send(peer_id, "⚠ /delrole <key>"); return
    key = args[0].lower()
    if key not in c.get("local_roles", {}): send(peer_id, "⚠ Нет такой."); return
    del c["local_roles"][key]; save_cfg(cfg)
    send(peer_id, f"🗑️ Роль «{key}» удалена.")

# ========== ЛОГИ ==========
def cmd_setlog(peer_id, uid, args):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔ Global."); return
    if not args:
        cur = cfg.get("log_peer_id")
        send(peer_id, f"📝 Лог-чат: {cur if cur else 'не назначен'}\n/setlog <peer_id> | /setlog off")
        return
    if args[0].lower() in ("off", "выкл", "0"):
        cfg["log_peer_id"] = 0; save_cfg(cfg)
        send(peer_id, "📝 Логи отключены."); return
    try: pid = int(args[0])
    except: send(peer_id, "⚠ Неверный peer_id"); return
    cfg["log_peer_id"] = pid; save_cfg(cfg)
    send(peer_id, f"📝 Лог-чат: {pid}")

def cmd_loginfo(peer_id, uid):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔"); return
    info = {
        "chats": len(cfg.get("chats", {})),
        "citizens": len(cfg.get("citizens", {})),
        "wars": len(cfg.get("wars", [])),
        "countries_destroyed": sum(1 for c in cfg.get("countries", {}).values() if c.get("destroyed")),
        "coalitions": len(cfg.get("coalitions", {})),
        "giveaways": len(cfg.get("giveaways", {})),
        "tickets": len(cfg.get("tickets", {})),
        "log_peer": cfg.get("log_peer_id") or "—",
        "games_running": len(GAMES),
        "version": "1.0",
    }
    send(peer_id, "📊 Статистика:\n" + "\n".join(f"• {k}: {v}" for k, v in info.items()))

# ========== ГЛОБАЛЬНЫЕ ОБЪЯВЛЕНИЯ ==========
def cmd_announce(peer_id, uid, args):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔ Global."); return
    if not args: send(peer_id, "⚠ /объявление <текст>"); return
    text = " ".join(args)[:1000]
    sent = 0
    for p in list(cfg.get("known_peers", [])):
        try:
            api.messages.send(peer_id=p, message=f"📢 ОБЪЯВЛЕНИЕ\n\n{text}", random_id=int(time.time()*1000) + sent, disable_mentions=0)
            sent += 1; time.sleep(0.05)
        except: pass
    send(peer_id, f"📢 Отправлено в {sent} чатов.")

def cmd_broadcast(peer_id, uid, args):
    if uid != int(cfg["global_owner"]): send(peer_id, "⛔ Global."); return
    if not args: send(peer_id, "⚠ /рассылка <текст>"); return
    text = " ".join(args)[:1000]
    uids = set()
    for ch in cfg.get("chats", {}).values():
        uids.update(ch.get("user_stats", {}).keys())
        uids.update(ch.get("balance", {}).keys())
    sent = 0
    for u in uids:
        try:
            uid_i = int(u)
            if uid_i <= 0: continue
            api.messages.send(peer_id=uid_i, message=f"📢 РАССЫЛКА\n\n{text}", random_id=int(time.time()*1000) + sent, disable_mentions=1)
            sent += 1; time.sleep(0.05)
        except: pass
    send(peer_id, f"📢 ЛС отправлено: {sent}")

# ========== ГЛАВНЫЙ ДИСПЕТЧЕР ==========
CMD_MAP = {
    # Экономика
    "баланс": lambda p, u, a, r, t: send(p, f"💰 Баланс: {fmt_num(get_balance(p, u))} 💵"),
    "balance": lambda p, u, a, r, t: send(p, f"💰 Баланс: {fmt_num(get_balance(p, u))} 💵"),
    "донат": cmd_donate, "передать": cmd_transfer,
    "приз": lambda p, u, a, r, t: cmd_prize(p, u),
    "prize": lambda p, u, a, r, t: cmd_prize(p, u),
    "подписка": lambda p, u, a, r, t: cmd_sub(p, u),
    "sub": lambda p, u, a, r, t: cmd_sub(p, u),
    "buybiz": cmd_buybiz, "mybiz": lambda p, u, a, r, t: cmd_mybiz(p, u),
    "collect": lambda p, u, a, r, t: cmd_collect(p, u),
    "promo": cmd_promo, "промо": cmd_promo,
    "createpromo": cmd_createpromo, "promolist": lambda p, u, a, r, t: cmd_promolist(p, u),
    "топ": cmd_top_ext, "top": cmd_top_ext,
    "вайп": lambda p, u, a, r, t: cmd_wipe(p, u),
    "wipeall": lambda p, u, a, r, t: cmd_wipe_all(p, u),
    "cmd": cmd_cmd,
    "продатьбизнес": cmd_sellbiz, "bizlist": lambda p, u, a, r, t: cmd_bizlist(p, u),
    "biz": lambda p, u, a, r, t: cmd_buybiz(p, u, a),

    # Страны
    "страны": lambda p, u, a, r, t: cmd_countries(p, u),
    "государства": lambda p, u, a, r, t: cmd_countries(p, u),
    "гражданство": cmd_citizenship, "citizenship": cmd_citizenship,
    "паспорт": cmd_passport, "passport": cmd_passport,
    "страна": cmd_country_info, "country": cmd_country_info,
    "граждане": cmd_citizens, "города": cmd_cities,
    "казна": cmd_treasury, "правительство": cmd_government,
    "должности": cmd_positions, "армия": cmd_army,
    "выборы": cmd_elections, "выдвинуться": cmd_run_for_president,
    "голос": cmd_vote, "очки": cmd_show_points,
    "улучшить_страну": cmd_show_improve, "улучшитьстрану": cmd_improve_country,
    "постройки": cmd_buildings, "построить": cmd_build_obj,
    "госпроект": cmd_state_project, "вооружение": cmd_armament,
    "налоги": cmd_tax, "компания": cmd_company,
    "регистрация": cmd_register_company, "переименоватьооо": cmd_rename_company,

    # Границы
    "граница": cmd_border, "виза": cmd_visa,
    "транспорт": cmd_transport_buy,
    "склад": lambda p, u, a, r, t: cmd_stock_view(p, u) if not a else cmd_stock_add(p, u, a),
    "перевозка": cmd_transport_cargo, "контрабанда": cmd_smuggle,

    # Война
    "войны": cmd_wars, "война": cmd_declare_war,
    "захват": cmd_capture, "контразащита": cmd_counter_defense,
    "мир": cmd_peace, "завершить_конфликт": cmd_end_conflict,
    "коалиции": cmd_coalitions, "коалиция": cmd_coalition,
    "коалпомощь": cmd_coal_help_money,
    "мобилизация": cmd_mobilization, "демобилизация": cmd_demobilization,
    "сделать": cmd_make_weapon, "пво": cmd_pvo_info,
    "установить": cmd_install_pvo, "запуск": cmd_launch,
    "задание": cmd_tasks, "выполнитьзадание": cmd_do_task,
    "upgrade_army": cmd_upgrade_army,
    "звание": cmd_show_rank, "повысить": cmd_promote,

    # Дрон
    "дрон": cmd_drone, "перехват": cmd_intercept,
    "сирена": cmd_siren, "воздухтревога": cmd_siren_all,

    # Глобал
    "выдать": cmd_give, "вернуть": cmd_restore_country,
    "устпрезидент": cmd_set_president_global,
    "устгражданство": cmd_set_citizenship_global,
    "gstaff": lambda p, u, a, r, t: cmd_gstaff(p, u),
    "grole": cmd_grole, "removerole": cmd_removerole,
    "build": cmd_build_link, "builds": lambda p, u, a, r, t: cmd_builds_list(p, u),
    "объявление": cmd_announce, "announce": cmd_announce,
    "рассылка": cmd_broadcast, "broadcast": cmd_broadcast,
    "setlog": cmd_setlog, "loginfo": lambda p, u, a, r, t: cmd_loginfo(p, u),

    # Модерация
    "warn": cmd_warn, "варн": cmd_warn,
    "unwarn": cmd_unwarn, "анварн": cmd_unwarn,
    "mute": cmd_mute, "мут": cmd_mute,
    "unmute": cmd_unmute, "размут": cmd_unmute,
    "nick": cmd_nick, "rnick": cmd_rnick,
    "kick": cmd_kick, "кик": cmd_kick,
    "ban": cmd_ban, "бан": cmd_ban,
    "unban": cmd_unban, "разбан": cmd_unban,
    "gban": cmd_gban, "ungban": cmd_ungban,
    "clear": cmd_clear, "banlist": lambda p, u, a, r, t: cmd_banlist(p, u),
    "report": cmd_report, "offer": cmd_offer,
    "adt": cmd_adt,
    "tickets": lambda p, u, a, r, t: send(p, tickets_text()),

    # Роли
    "setrole": cmd_setrole, "removestaff": cmd_removestaff,
    "newrole": cmd_newrole, "delrole": cmd_delrole,

    # Игры
    "казино": cmd_casino, "casino": cmd_casino,
    "монетка": cmd_coin, "coin": cmd_coin,
    "кубик": cmd_dice, "dice": cmd_dice,
    "дуэль": cmd_duel, "duel": cmd_duel,
    "слоты": cmd_slots, "slots": cmd_slots,
    "краш": cmd_crash, "crash": cmd_crash,
    "дартс": cmd_darts, "darts": cmd_darts,
    "колесо": cmd_wheel, "wheel": cmd_wheel,
    "рулетка": cmd_roulette, "roulette": cmd_roulette,
    "блэкджек": cmd_bj, "bj": cmd_bj,
    "мины": cmd_mines, "mines": cmd_mines,
    "башня": cmd_tower, "tower": cmd_tower,
    "кейс": cmd_case, "case": cmd_case,
    "гонка": cmd_race, "race": cmd_race,
    "рыбалка": cmd_fish, "fish": cmd_fish,

    # Мафия
    "мафия": cmd_mafia, "mafia": cmd_mafia,

    # Сервис
    "q": lambda p, u, a, r, t: cmd_quit(p, u),
    "rules": lambda p, u, a, r, t: cmd_rules(p, u),
    "раздача": cmd_giveaway,
    "взять": cmd_take,
    "help": lambda p, u, a, r, t: send(p, build_help()),
    "info": lambda p, u, a, r, t: send(p, user_info_text(u, p)),
    "стата": lambda p, u, a, r, t: send(p, user_stats_text(u, p)),
    "stat": lambda p, u, a, r, t: send(p, user_stats_text(u, p)),
    "staff": lambda p, u, a, r, t: send(p, build_staff_text(p)),
    "госскоманды": lambda p, u, a, r, t: send(p, build_gos_cmds()),
    "ивент": lambda p, u, a, r, t: run_random_event(p),
    "event": lambda p, u, a, r, t: run_random_event(p),
}

# ========== ОБРАБОТКА СООБЩЕНИЯ ==========
def handle_message(msg):
    peer_id = msg["peer_id"]
    from_id = msg["from_id"]
    text = (msg.get("text") or "").strip()
    cmid = msg.get("conversation_message_id")
    mid = msg.get("id")
    reply = msg.get("reply_message")
    action = msg.get("action")

    if from_id <= 0: return

    # Служебные действия (вход/выход)
    if action:
        atype = action.get("type")
        if atype == "chat_invite_user":
            inv = action.get("member_id")
            if inv == BOT_ID:
                send(peer_id, "👋 Всем привет! Я бот-игровой. /help — команды.")
            else:
                handle_welcome(peer_id, action)
        return

    if is_duplicate(peer_id, msg): return

    # ЛС — мафия или сервис
    if not is_chat(peer_id):
        if from_id == BOT_ID: return
        if mafia_any_dm(from_id, text): return
        if text.startswith("/") and text[1:].split()[0].lower() == "start":
            send_dm(from_id, "👋 Привет! Команды в чатах. /help в беседе.")
        return

    track_peer(peer_id)
    track_message(from_id, peer_id, text)

    c = get_chat(peer_id)

    # Бан
    if str(from_id) in c.get("banned", {}):
        delete_msg(mid, cmid, peer_id)
        return

    # Присоединение к мафии без слэша
    if not text.startswith("/"):
        if text.lower() in MAFIA_JOIN_WORDS:
            mafia_join(peer_id, from_id)
        return

    parts = text[1:].split()
    if not parts: return
    cmd = parts[0].lower()
    args = parts[1:]

    # Кастомные алиасы
    if cmd in c.get("custom_cmds", {}):
        cmd = c["custom_cmds"][cmd]

    # Мут
    mu = get_mute_until(c.get("muted", {}).get(str(from_id)))
    if mu and mu > time.time() and cmd not in ("unmute", "размут", "help"):
        delete_msg(mid, cmid, peer_id)
        now_ts = time.time()
        info = c["muted"].get(str(from_id))
        if isinstance(info, dict) and now_ts - info.get("last_dm", 0) >= MUTE_DM_INTERVAL:
            info["last_dm"] = now_ts; save_cfg(cfg)
            mute_warn_dm(from_id, mu - now_ts)
        return

    handler = CMD_MAP.get(cmd)
    if not handler: return

    if not can(from_id, cmd, peer_id):
        send(peer_id, "⛔ Нет прав.")
        return

    try:
        handler(peer_id, from_id, args, reply, text)
        log_action(from_id, f"/{cmd}")
    except Exception as e:
        print(f"[cmd:{cmd}] {e}")
        send(peer_id, f"❌ Ошибка: {e}")

# ========== LONGPOLL ==========
def handle_event(event):
    try:
        if event.type == VkBotEventType.MESSAGE_NEW:
            handle_message(event.object.message)
        elif event.type == VkBotEventType.MESSAGE_EVENT:
            pass  # callback кнопок
    except Exception as e:
        print(f"[event] {e}")

def main():
    print("🚀 Бот запущен. Слушаю...")
    try:
        api.messages.setActivity(type="online", peer_id=BOT_ID)
    except: pass
    while True:
        try:
            for event in longpoll.listen():
                handle_event(event)
        except KeyboardInterrupt:
            print("⏹️ Остановлено."); break
        except Exception as e:
            print(f"[lp] {e}. Перезапуск через 5с...")
            time.sleep(5)

if __name__ == "__main__":
    main()
