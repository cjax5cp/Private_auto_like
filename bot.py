# -*- coding: utf-8 -*-
"""
ULTRA AUTO LIKE TELEGRAM BOT
Ready version for PRIVATE0011_BOT
"""

import os
import re
import json
import time
import uuid
import html
import random
import string
import threading
import traceback
from math import ceil
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests
import telebot
from telebot import types
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# =============================================================
# ======================== CONFIG AREA =========================
# =============================================================

BOT_TOKEN = "8895378766:AAEUQU5rnS-WfcnOsW5SjD-4i_nYSs63wjY"
OWNER_ID = 6830149432
LIKE_API_URL = "https://like-by-ckrpro-api-ob-54.vercel.app/like?uid={uid}&server_name={region}"
LIKE_API_URL_2 = "https://like-by-ckrpro-api-ob-54.vercel.app/like?uid={uid}&server_name={region}"
BOT_NAME = "PRIVATE Auto Like"
SUPPORT_USERNAME = "@GENIUS0011P"
OFFICIAL_GROUP = "https://t.me/GENIUS0011P"
PAYMENT_TEXT = "@GENIUS0011P"
DEFAULT_AUTOLIKE_TIME = "04:00"
TIMEZONE_NAME = "Asia/Kolkata"

SUPPORTED_REGIONS = [
    "IND", "BR", "US", "SG", "RU", "ID", "TW", "VN", "TH", "PK", "BD", "EUROPE", "ME", "SAC", "NA"
]

DEFAULT_DAILY_BATCH = 500
MAX_BATCH = 500
REQUEST_TIMEOUT = 35
PAGE_SIZE = 5
DB_DIR = "database"

USER_COMMANDS_PRIVATE_ONLY = True

# =============================================================
# ======================== BOT OBJECT ==========================
# =============================================================

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=True, num_threads=8)
scheduler = BackgroundScheduler(timezone=TIMEZONE_NAME)
db_lock = threading.RLock()

# =============================================================
# ========================= DB FILES ===========================
# =============================================================

DB_FILES = {
    "admins": os.path.join(DB_DIR, "admin.json"),
    "likes": os.path.join(DB_DIR, "like.json"),
    "users": os.path.join(DB_DIR, "users.json"),
    "redeem": os.path.join(DB_DIR, "redeem.json"),
    "groups": os.path.join(DB_DIR, "groups.json"),
    "settings": os.path.join(DB_DIR, "settings.json"),
    "verification": os.path.join(DB_DIR, "verification.json"),
    "logs": os.path.join(DB_DIR, "logs.json"),
}

DEFAULT_DB = {
    "admins": {"admins": {}},
    "likes": {"items": {}},
    "users": {"users": {}},
    "redeem": {"codes": {}, "used": {}},
    "groups": {"allowed_groups": [], "log_groups": []},
    "settings": {
        "autolike_time": DEFAULT_AUTOLIKE_TIME,
        "force_verification": False,
        "verification_channel": "",
        "welcome_message": "",
        "welcome_image": "",
        "maintenance": False,
        "daily_reset_date": "",
    },
    "verification": {"verified": {}},
    "logs": {"events": []},
}

# =============================================================
# ======================= JSON DATABASE ========================
# =============================================================

def ensure_db() -> None:
    os.makedirs(DB_DIR, exist_ok=True)
    for key, path in DB_FILES.items():
        if not os.path.exists(path):
            save_json(key, DEFAULT_DB[key])
        else:
            try:
                data = load_json(key)
                if not isinstance(data, dict):
                    save_json(key, DEFAULT_DB[key])
            except Exception:
                backup = f"{path}.broken.{int(time.time())}"
                try:
                    os.rename(path, backup)
                except Exception:
                    pass
                save_json(key, DEFAULT_DB[key])


def load_json(key: str) -> Dict[str, Any]:
    path = DB_FILES[key]
    with db_lock:
        if not os.path.exists(path):
            return json.loads(json.dumps(DEFAULT_DB[key]))
        with open(path, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return json.loads(json.dumps(DEFAULT_DB[key]))


def save_json(key: str, data: Dict[str, Any]) -> None:
    path = DB_FILES[key]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with db_lock:
        tmp = f"{path}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)


def log_event(kind: str, actor: int, details: Dict[str, Any]) -> None:
    logs = load_json("logs")
    events = logs.setdefault("events", [])
    events.append({
        "id": str(uuid.uuid4()),
        "time": now_str(),
        "kind": kind,
        "actor": str(actor),
        "details": details,
    })
    if len(events) > 5000:
        logs["events"] = events[-5000:]
    save_json("logs", logs)

# =============================================================
# ======================== UTILITIES ===========================
# =============================================================

def now() -> datetime:
    return datetime.now()


def now_str() -> str:
    return now().strftime("%Y-%m-%d %H:%M:%S")


def today_str() -> str:
    return date.today().isoformat()


def display_date() -> str:
    return now().strftime("%d-%b-%Y")


def clean_region(region: str) -> str:
    return region.strip().upper()


def is_region(region: str) -> bool:
    return clean_region(region) in SUPPORTED_REGIONS


def only_digits(value: str) -> bool:
    return bool(re.fullmatch(r"\d{5,15}", value or ""))


def fmt_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def esc(x: Any) -> str:
    return html.escape(str(x))


def q(text: str, mono: bool = False) -> str:
    if mono:
        return f"<blockquote><pre>{esc(text)}</pre></blockquote>"
    return f"<blockquote>{text}</blockquote>"


def tiny_caps(text: str) -> str:
    table = str.maketrans({
        "a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ꜰ", "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ",
        "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "ꜱ", "t": "ᴛ",
        "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ",
        "A": "ᴀ", "B": "ʙ", "C": "ᴄ", "D": "ᴅ", "E": "ᴇ", "F": "ꜰ", "G": "ɢ", "H": "ʜ", "I": "ɪ", "J": "ᴊ",
        "K": "ᴋ", "L": "ʟ", "M": "ᴍ", "N": "ɴ", "O": "ᴏ", "P": "ᴘ", "Q": "ǫ", "R": "ʀ", "S": "ꜱ", "T": "ᴛ",
        "U": "ᴜ", "V": "ᴠ", "W": "ᴡ", "X": "x", "Y": "ʏ", "Z": "ᴢ",
    })
    return text.translate(table)


def normalize_time(text: str) -> Optional[str]:
    s = text.strip().lower().replace(" ", "")
    m = re.fullmatch(r"(\d{1,2})(?::(\d{2}))?(am|pm)?", s)
    if not m:
        return None
    hh = int(m.group(1)); mm = int(m.group(2) or 0); ap = m.group(3)
    if mm > 59:
        return None
    if ap:
        if hh < 1 or hh > 12:
            return None
        if ap == "pm" and hh != 12: hh += 12
        if ap == "am" and hh == 12: hh = 0
    if hh > 23:
        return None
    return f"{hh:02d}:{mm:02d}"


def make_code(n: int = 10) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "AL-" + "".join(random.choice(alphabet) for _ in range(n))


def safe_send(chat_id: int, text: str, reply_markup=None, disable_web_page_preview=True):
    try:
        return bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=reply_markup, disable_web_page_preview=disable_web_page_preview)
    except Exception:
        try:
            return bot.send_message(chat_id, re.sub(r"<[^>]+>", "", text), reply_markup=reply_markup)
        except Exception:
            return None


def safe_edit(chat_id: int, message_id: int, text: str, reply_markup=None):
    try:
        return bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=reply_markup)
    except Exception:
        return None

# =============================================================
# ======================= PERMISSIONS ==========================
# =============================================================

def is_owner(user_id: int) -> bool:
    return int(user_id) == int(OWNER_ID)


def get_admin(user_id: int) -> Optional[Dict[str, Any]]:
    data = load_json("admins")
    return data.get("admins", {}).get(str(user_id))


def is_admin(user_id: int) -> bool:
    return is_owner(user_id) or get_admin(user_id) is not None


def admin_tag(user_id: int) -> str:
    if is_owner(user_id):
        return "OWNER"
    adm = get_admin(user_id) or {}
    return adm.get("tag") or adm.get("name") or str(user_id)


def require_admin(message) -> bool:
    if not is_admin(message.from_user.id):
        safe_send(message.chat.id, q("🚫 <b>ACCESS DENIED</b>\nOnly admin can use this command."))
        return False
    return True


def require_owner(message) -> bool:
    if not is_owner(message.from_user.id):
        safe_send(message.chat.id, q("🚫 <b>OWNER ONLY</b>\nThis command is locked."))
        return False
    return True


def is_group_allowed(chat_id: int) -> bool:
    if chat_id > 0:
        return True
    groups = load_json("groups")
    return str(chat_id) in [str(x) for x in groups.get("allowed_groups", [])]

# =============================================================
# ======================== USER DATA ===========================
# =============================================================

def upsert_user(user) -> None:
    users = load_json("users")
    d = users.setdefault("users", {})
    uid = str(user.id)
    old = d.get(uid, {})
    d[uid] = {
        **old,
        "id": uid,
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "username": user.username or "",
        "started": True,
        "last_seen": now_str(),
    }
    save_json("users", users)


def get_user_record(user_id: Any) -> Optional[Dict[str, Any]]:
    users = load_json("users")
    return users.get("users", {}).get(str(user_id))


def user_started(user_id: Any) -> bool:
    rec = get_user_record(user_id)
    return bool(rec and rec.get("started"))


def display_user_name(user_id: Any) -> str:
    rec = get_user_record(user_id) or {}
    if rec.get("username"):
        return "@" + rec["username"]
    name = (rec.get("first_name", "") + " " + rec.get("last_name", "")).strip()
    return name or str(user_id)

# =============================================================
# ====================== FORCE VERIFY ==========================
# =============================================================

def is_verified(user_id: int) -> bool:
    if is_admin(user_id):
        return True
    settings = load_json("settings")
    if not settings.get("force_verification"):
        return True
    verification = load_json("verification")
    return str(user_id) in verification.get("verified", {})


def mark_verified(user_id: int) -> None:
    v = load_json("verification")
    v.setdefault("verified", {})[str(user_id)] = {"time": now_str()}
    save_json("verification", v)


def verification_keyboard() -> types.InlineKeyboardMarkup:
    settings = load_json("settings")
    kb = types.InlineKeyboardMarkup(row_width=1)
    channel = settings.get("verification_channel") or OFFICIAL_GROUP
    if channel:
        url = f"https://t.me/{channel.lstrip('@')}"
        kb.add(types.InlineKeyboardButton("✅ JOIN / VERIFY CHANNEL", url=url))
    kb.add(types.InlineKeyboardButton("🔄 I HAVE JOINED", callback_data="verify_me"))
    return kb


def guard_verified(message) -> bool:
    upsert_user(message.from_user)
    if is_verified(message.from_user.id):
        return True
    safe_send(message.chat.id, q("🔐 <b>FORCE VERIFICATION ENABLED</b>\nJoin the official channel/group then press verify."), verification_keyboard())
    return False

# =============================================================
# ====================== LIKE DB HELPERS =======================
# =============================================================

def all_likes() -> Dict[str, Dict[str, Any]]:
    return load_json("likes").setdefault("items", {})


def save_likes(items: Dict[str, Dict[str, Any]]) -> None:
    data = load_json("likes")
    data["items"] = items
    save_json("likes", data)


def find_like(uid: str) -> Optional[Dict[str, Any]]:
    return all_likes().get(str(uid))


def visible_likes_for_actor(actor_id: int) -> List[Dict[str, Any]]:
    items = list(all_likes().values())
    if is_owner(actor_id):
        return sorted(items, key=lambda x: x.get("created_at", ""))
    return sorted([x for x in items if str(x.get("admin_id")) == str(actor_id)], key=lambda x: x.get("created_at", ""))


def user_likes(user_id: int) -> List[Dict[str, Any]]:
    items = all_likes().values()
    return sorted([x for x in items if str(x.get("user_id")) == str(user_id)], key=lambda x: x.get("created_at", ""))


def admin_likes(admin_id: int) -> List[Dict[str, Any]]:
    return sorted([x for x in all_likes().values() if str(x.get("admin_id")) == str(admin_id)], key=lambda x: x.get("created_at", ""))


def can_manage_like(actor_id: int, item: Dict[str, Any]) -> bool:
    return is_owner(actor_id) or str(item.get("admin_id")) == str(actor_id)


def update_like(uid: str, patch: Dict[str, Any]) -> bool:
    items = all_likes()
    if str(uid) not in items:
        return False
    items[str(uid)].update(patch)
    items[str(uid)]["updated_at"] = now_str()
    save_likes(items)
    return True

# =============================================================
# ======================== API CLIENT ==========================
# =============================================================

def call_like_api(region: str, uid: str) -> Dict[str, Any]:
    url = LIKE_API_URL.format(region=region, uid=uid)
    r = requests.get(url, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json()


def parse_api_for_display(api: Dict[str, Any], fallback_region: str, fallback_uid: str) -> Dict[str, Any]:
    status = fmt_int(api.get("status"), 0)
    return {
        "status": status,
        "player": api.get("PlayerNickname") or "UNKNOWN",
        "uid": api.get("UID") or fallback_uid,
        "region": api.get("Server") or fallback_region,
        "before": fmt_int(api.get("LikesbeforeCommand"), 0),
        "after": fmt_int(api.get("LikesafterCommand"), 0),
        "given": fmt_int(api.get("LikesGivenByAPI"), 0),
        "error": api.get("error", ""),
    }

def call_like_api2(region: str, uid: str) -> Dict[str, Any]:
    url = LIKE_API_URL_2.format(region=region, uid=uid)
    r = requests.get(url, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json()


def parse_api_for_display2(api: Dict[str, Any], fallback_region: str, fallback_uid: str) -> Dict[str, Any]:
    status = fmt_int(api.get("status"), 0)
    return {
        "status": status,
        "player": api.get("PlayerNickname") or "UNKNOWN",
        "uid": api.get("UID") or fallback_uid,
        "region": api.get("Server") or fallback_region,
        "before": fmt_int(api.get("LikesbeforeCommand"), 0),
        "after": fmt_int(api.get("LikesafterCommand"), 0),
        "given": fmt_int(api.get("LikesGivenByAPI"), 0),
        "error": api.get("error", ""),
    }

# =============================================================
# ======================= TELEGRAM UI ==========================
# =============================================================

def main_menu(user_id: int) -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if is_owner(user_id):
        kb.row("❤️ My Likes", "🎁 Redeem")
        kb.row("📋 Plans", "🛠 Help")
        kb.row("👑 Owner Dashboard")
    elif is_admin(user_id):
        kb.row("❤️ My Likes")
        kb.row("➕ Add Autolike", "📣 Broadcast")
        kb.row("🛡 Admin Dashboard")
    else:
        kb.row("❤️ My Likes", "🎁 Redeem")
        kb.row("📋 Plans", "🛠 Help")
    return kb


def admin_dashboard_kb() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("➕ Add Autolike", "📣 Broadcast")
    kb.row("🚀 Autolike Run", "📜 Autolike List")
    kb.row("⬅️ Back")
    return kb


def owner_dashboard_kb() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📊 Admin Stats", "🎁 Redeem Panel")
    kb.row("⏰ Set Time", "🚀 Autolike Run")
    kb.row("📜 Autolike List", "👥 Admins Autolike List")
    kb.row("🔐 Set Force Verification", "⬅️ Back")
    return kb


def list_nav_kb(prefix: str, page: int, total_pages: int, scope: str = "all") -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    prev_page = max(1, page - 1)
    next_page = min(total_pages, page + 1)
    kb.row(
        types.InlineKeyboardButton("◀️ BACK", callback_data=f"{prefix}:{scope}:{prev_page}"),
        types.InlineKeyboardButton("NEXT ▶️", callback_data=f"{prefix}:{scope}:{next_page}"),
    )
    kb.add(types.InlineKeyboardButton("🔄 REFRESH", callback_data=f"{prefix}:{scope}:{page}"))
    return kb

# =============================================================
# ======================== FORMATTERS ==========================
# =============================================================

def success_like_msg(d: Dict[str, Any], item: Optional[Dict[str, Any]] = None) -> str:
    batch = item.get("batch", DEFAULT_DAILY_BATCH) if item else DEFAULT_DAILY_BATCH
    left = item.get("left", 0) if item else 0
    text = (
        "✅ LIKE SENT SUCCESSFULLY!\n\n"
        f"👤 PLAYER: {d['player']}\n"
        f"🌍 REGION: {d['region']}\n"
        f"📊 LIKES BEFORE: {d['before']}\n"
        f"💖 LIKES GIVEN: {d['given']}\n"
        f"✨ LIKES AFTER: {d['after']}\n"
        f"⚙️ BATCH: {batch}\n"
        f"💞 LEFT: {left}\n"
        f"⏰ TIME: {now().strftime('%I:%M:%S %p')} IST"
    )
    return q(text)


def limit_msg(d: Dict[str, Any]) -> str:
    return q(
        "⚠️ LIKE LIMIT REACHED!\n\n"
        f"👤 PLAYER: {esc(d['player'])}\n"
        f"🎮 UID: {esc(d['uid'])}\n"
        f"🌍 REGION: {esc(d['region'])}\n"
        f"💖 LIKES BEFORE: {d['before']}\n"
        f"💖 LIKES GIVEN: {d['given']}\n"
        f"✨ LIKES AFTER: {d['after']}\n"
        f"⏰ TIME: {now().strftime('%I:%M:%S %p')} IST"
    )


def invalid_uid_msg(region: str, uid: str, err: str = "Player not found — check UID and region.") -> str:
    return q(
        "❌ INVALID UID OR REGION!\n\n"
        f"🎮 UID: {esc(uid)}\n"
        f"🌍 REGION: {esc(region)}\n"
        f"📌 ERROR: {esc(err)}"
    )


def add_success_msg(item: Dict[str, Any], before: int, after: int, given: int) -> str:
    text = (
        f"🎉 CONGRATULATIONS !!\n"
        f"✅ YOUR UID {item['uid']}\nSUCCESSFULLY ADDED\n\n"
        f"👤 FREE FIRE NAME : {item.get('player','UNKNOWN')}\n"
        f"🆔 FREE FIRE UID : {item['uid']}\n"
        f"📍 YOUR REGION : {item['region']}\n\n"
        f"📊 LIKES RESULT\n"
        f"➜ BEFORE LIKES : {before}\n"
        f"➜ AFTER LIKES : {after}\n"
        f"➜ LIKES GIVEN BY BOT : {given}\n\n"
        f"💰 SERVICE PACKAGE\n"
        f"➜ YOUR LIKES PLAN : {item['total']}\n"
        f"➜ REMAINING LIKES : {item['left']}\n"
        f"➜ NOW ADDED LIKES : {item['used']}\n\n"
        f"⏰ DAILY AUTOLIKE AT {item.get('run_time', DEFAULT_AUTOLIKE_TIME)} IST\n"
        f"✅ YOU WILL RECEIVE LIKES AUTOMATICALLY\n\n"
        f"📞 SUPPORT : CONTACT ADMIN FOR ANY HELP\n"
        f"🎯 THANK YOU FOR CHOOSING OUR SERVICE"
    )
    return q(text)


def like_item_block(item: Dict[str, Any], number: int, show_admin: bool = False) -> str:
    status = "✅ ACTIVE" if item.get("status") == "active" else "⏸ PAUSED"
    user_display = display_user_name(item.get("user_id"))
    admin_line = f"├🛡 ADMIN: {admin_tag(fmt_int(item.get('admin_id')))}\n" if show_admin else ""
    return (
        f"────── USER {number} ──────\n"
        f"├👤 USER: {user_display}\n"
        f"├🆔 UID: {item.get('uid')}\n"
        f"├🌍 REGION: {item.get('region')}\n"
        f"{admin_line}"
        f"├⚙️ BATCH: {item.get('batch')}\n"
        f"├💖 LEFT: {item.get('left')}\n"
        f"├📊 TOTAL: {item.get('total')}\n"
        f"├📈 USED: {item.get('used')}\n"
        f"├✨ TODAY: {item.get('today', 0)}\n"
        f"└🟢 STATUS: {status}\n"
    )


def format_like_list(items: List[Dict[str, Any]], page: int, title: str, show_admin: bool = False) -> Tuple[str, int]:
    total = len(items)
    pages = max(1, ceil(total / PAGE_SIZE))
    page = max(1, min(page, pages))
    start = (page - 1) * PAGE_SIZE
    chunk = items[start:start + PAGE_SIZE]
    body = f"🤖 {title}\n\n"
    if not chunk:
        body += "NO AUTOLIKE USERS FOUND.\n"
    for i, item in enumerate(chunk, start=start + 1):
        body += like_item_block(item, i, show_admin=show_admin) + "\n"
    body += f"📊 TOTAL AUTOLIKES: {total}\n📄 PAGE: {page}/{pages}"
    return q(body, mono=True), pages


def format_uid_info(item: Dict[str, Any]) -> str:
    status = "✅ ACTIVE" if item.get("status") == "active" else "⏸ PAUSED"
    body = (
        "📋 UID INFORMATION\n\n"
        "────── USER INFO ──────\n"
        f"├👤 USER: {display_user_name(item.get('user_id'))}\n"
        f"├🌍 PLAYER: {item.get('player')}\n"
        f"├🎮 UID: {item.get('uid')}\n"
        f"├🌍 REGION: {item.get('region')}\n"
        f"├📅 ADDED: {item.get('added_date')}\n"
        f"├💖 LIKES LEFT: {item.get('left')}\n"
        f"├📦 TOTAL: {item.get('total')}\n"
        f"├📊 USED: {item.get('used')}\n"
        f"├✨ TODAY: {item.get('today', 0)}\n"
        f"├⚙️ BATCH: {item.get('batch')}\n"
        f"└🟢 STATUS: {status}"
    )
    return q(body, mono=True)


def my_likes_msg(items: List[Dict[str, Any]]) -> str:
    body = "📋 YOUR UIDS\n\n"
    if not items:
        body += "NO UID FOUND FOR YOUR TELEGRAM USER ID."
    for idx, item in enumerate(items, 1):
        body += (
            f"────── UID {idx} ──────\n"
            f"├🌍 REGION: {item.get('region')}\n"
            f"├📅 ADDED: {item.get('added_date')}\n"
            f"├💖 LEFT: {item.get('left')}\n"
            f"├📦 TOTAL: {item.get('total')}\n"
            f"├📊 USED: {item.get('used')}\n"
            f"├⚙️ BATCH: {item.get('batch')}\n"
            f"└🟢 STATUS: {'✅ ACTIVE' if item.get('status') == 'active' else '⏸ PAUSED'}\n\n"
        )
    return q(body, mono=True)


def help_msg(owner: bool = False, admin: bool = False) -> str:
    owner_block = ""
    if owner:
        owner_block = (
            "🛠 OWNER COMMANDS\n\n"
            "/like {REGION} {UID} {BATCH}\n"
            "/autolike list\n/autolike run\n"
            "/autolike add {REGION} {UID} {LIKES} {USER_ID} {ADMIN_ID}\n"
            "/autolike remove {UID}\n/autolike extend {UID} {LIKES}\n"
            "/autolike reduce {UID} {LIKES}\n/autolike batch {UID} {NUM}\n"
            "/autolike pause {UID}\n/autolike resume {UID}\n/autolike info {UID}\n"
            "/setautolikerun 4pm\n/group allow\n/addgroup {GROUP_ID}\n"
            "/setmessage {TEXT}\n/setimage {URL}\n/broadcast {MESSAGE}\n/pin {MESSAGE}\n"
            "/promote {TAG} reply-to-user\n/adminadd {USER_ID} {TAG}\n/adminremove {USER_ID}\n/adminlist\n"
            "/createredeem {CODE} {LIKES} {COUNT}\n/redeemdel {CODE}\n/redeemcheck {CODE}\n"
            "/forceverify on|off [@channel]\n\n"
        )
    elif admin:
        owner_block = (
            "🛠 ADMIN COMMANDS\n\n"
            "/like {REGION} {UID} {BATCH}\n"
            "/autolike list\n/autolike run\n"
            "/autolike add {REGION} {UID} {LIKES} {USER_ID} {ADMIN_ID}\n"
            "/autolike remove {UID}\n/autolike extend {UID} {LIKES}\n"
            "/autolike reduce {UID} {LIKES}\n/autolike batch {UID} {NUM}\n"
            "/autolike pause {UID}\n/autolike resume {UID}\n/autolike info {UID}\n"
            "/broadcast {MESSAGE}\n\n"
        )
    user_block = (
        "👥 USER COMMANDS\n\n"
        "/start\n/help\n/plans\n/status\n"
        "/like {REGION} {UID}  (ONLY IN ALLOWED GROUPS)\n"
        "/mylike\n/myuid\n/redeem {CODE} {REGION} {UID}\n"
    )
    return q(owner_block + user_block, mono=True)


def plans_msg() -> str:
    body = (
        "🔥 FREE FIRE AUTO LIKE SERVICE 🔥\n\n"
        "💸 PRICE LIST (200 LIKES DAILY)\n"
        "₹20   1 DAY   ➜ 200 LIKES\n"
        "₹40   5 DAYS  ➜ 1000 LIKES\n"
        "₹80   10 DAYS ➜ 2000 LIKES\n"
        "₹160  20 DAYS ➜ 4000 LIKES\n"
        "₹240  30 DAYS ➜ 6000 LIKES\n"
        "₹320  40 DAYS ➜ 8000 LIKES\n"
        "₹400  55 DAYS ➜ 10000 LIKES\n\n"
        "⚙️ ALL SERVERS SUPPORTED\n"
        "🇮🇳 IND • 🇧🇷 BR • 🇺🇸 US • 🇸🇬 SG • 🇷🇺 RU • 🇮🇩 ID • 🇹🇼 TW • 🇻🇳 VN • 🇹🇭 TH • 🇵🇰 PK • 🇧🇩 BD • EUROPE • ME • SAC • NA\n\n"
        "✅ 200 REAL LIKES DAILY\n"
        "• SAME TIME DELIVERY EVERY DAY\n"
        "• FULLY AUTOMATIC SYSTEM\n"
        "• SAFE FOR MAIN ACCOUNT\n"
        "• INSTANT START AFTER PAYMENT\n\n"
        "▶️ SEND UID + SERVER AFTER PAYMENT\n"
        "💸 PAYMENT: " + PAYMENT_TEXT + "\n"
        "👥 JOIN OFFICIAL AUTO LIKE GROUP: " + OFFICIAL_GROUP
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🛒 ORDER NOW", url=f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}"))
    return q(body), kb

# =============================================================
# ======================= CORE ACTIONS =========================
# =============================================================

def do_single_like(region: str, uid: str, batch: int = DEFAULT_DAILY_BATCH, item: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
    region = clean_region(region)
    try:
        api = call_like_api(region, uid)
        d = parse_api_for_display(api, region, uid)
        if d["status"] == 1:
            if item is not None:
                given = max(0, d["given"])
                item["left"] = max(0, fmt_int(item.get("left")) - given)
                item["used"] = fmt_int(item.get("used")) + given
                item["today"] = fmt_int(item.get("today")) + given
                item["last_run"] = now_str()
                item["player"] = d["player"] or item.get("player", "UNKNOWN")
                item["likes_before"] = d["before"]
                item["likes_after"] = d["after"]
            return success_like_msg(d, item or {"batch": batch, "left": 0}), {"ok": True, "status": 1, "display": d}
        if d["status"] == 2:
            return limit_msg(d), {"ok": True, "status": 2, "display": d}
        return invalid_uid_msg(region, uid, d.get("error") or "Player not found."), {"ok": False, "status": 0, "display": d}
    except Exception as e:
        return q("❌ API ERROR\n\nService temporarily unavailable."), {"ok": False, "status": -1, "error": str(e)}


def do_single_like2(region: str, uid: str, batch: int = DEFAULT_DAILY_BATCH, item: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
    region = clean_region(region)
    try:
        api = call_like_api2(region, uid)
        p = parse_api_for_display2(api, region, uid)
        if p["status"] == 1:
            if item is not None:
                given = max(0, p["given"])
                item["left"] = max(0, fmt_int(item.get("left")) - given)
                item["used"] = fmt_int(item.get("used")) + given
                item["today"] = fmt_int(item.get("today")) + given
                item["last_run"] = now_str()
                item["player"] = p["player"] or item.get("player", "UNKNOWN")
                item["likes_before"] = p["before"]
                item["likes_after"] = p["after"]
            return success_like_msg(p, item or {"batch": batch, "left": 0}), {"ok": True, "status": 1, "display": p}
        if p["status"] == 2:
            return limit_msg(p), {"ok": True, "status": 2, "display": p}
        return invalid_uid_msg(region, uid, p.get("error") or "Player not found."), {"ok": False, "status": 0, "display": p}
    except Exception as e:
        return q("❌ API ERROR\n\nService temporarily unavailable."), {"ok": False, "status": -1, "error": str(e)}


def notify_user_like(item: Dict[str, Any], msg: str) -> None:
    user_id = fmt_int(item.get("user_id"))
    if user_id and user_started(user_id):
        safe_send(user_id, msg)


def run_autolike(actor_id: int, only_admin: Optional[int] = None, chat_id: Optional[int] = None) -> Dict[str, int]:
    items = all_likes()
    stats = {"total": 0, "sent": 0, "limit": 0, "invalid": 0, "skipped": 0}
    if chat_id:
        safe_send(chat_id, q(f"⚡ <b>AUTOLIKE STARTED</b> • {now().strftime('%I:%M %p')}\n🚀 DAILY SESSION LIVE"))
    for uid, item in list(items.items()):
        if only_admin is not None and not is_owner(actor_id) and str(item.get("admin_id")) != str(only_admin):
            continue
        if only_admin is not None and is_owner(actor_id) and str(item.get("admin_id")) != str(only_admin):
            continue
        if item.get("status") != "active":
            stats["skipped"] += 1; continue
        if fmt_int(item.get("left")) <= 0:
            item["status"] = "completed"; stats["skipped"] += 1; continue
        stats["total"] += 1
        msg, result = do_single_like(item.get("region"), uid, item.get("batch", DEFAULT_DAILY_BATCH), item)
        if result.get("status") == 1: stats["sent"] += 1
        elif result.get("status") == 2: stats["limit"] += 1
        else: stats["invalid"] += 1
        notify_user_like(item, msg)
        if chat_id:
            safe_send(chat_id, msg)
        time.sleep(0.7)
    save_likes(items)
    log_event("autolike_run", actor_id, stats)
    return stats


def reset_daily_if_needed() -> None:
    settings = load_json("settings")
    if settings.get("daily_reset_date") == today_str():
        return
    items = all_likes()
    for item in items.values():
        item["today"] = 0
    save_likes(items)
    settings["daily_reset_date"] = today_str()
    save_json("settings", settings)

# =============================================================
# ====================== COMMAND HANDLERS ======================
# =============================================================

@bot.message_handler(commands=["start"])
def cmd_start(message):
    upsert_user(message.from_user)
    text = (
        f"🎊 WELCOME TO {BOT_NAME} BOT\n\n"
        "🏆 BOT FEATURES:\n"
        "⁉️ DAILY AUTOMATED LIKES\n"
        "🕘 DAILY RESET DATA AT 04:00 IST\n"
        "📡 PREMIUM AND LIMITED FREE FEATURES\n"
        "🎁 REAL TIME STATUS TRACKING\n"
        "🎀 TRUSTED ADMINS\n\n"
        f"👨‍💼 ADMIN: {SUPPORT_USERNAME}\n"
        f"📢 DAILY UPDATES: {OFFICIAL_GROUP}\n\n"
        "✂️ USE /help FOR ALL COMMANDS\n"
        "💵 USE /plans FOR PREMIUM PLANS"
    )
    safe_send(message.chat.id, q(text), main_menu(message.from_user.id))

@bot.message_handler(commands=["help"])
def cmd_help(message):
    upsert_user(message.from_user)
    safe_send(message.chat.id, help_msg(owner=is_owner(message.from_user.id), admin=is_admin(message.from_user.id)), main_menu(message.from_user.id))

@bot.message_handler(commands=["plans"])
def cmd_plans(message):
    upsert_user(message.from_user)
    text, kb = plans_msg()
    safe_send(message.chat.id, text, kb)

@bot.message_handler(commands=["status"])
def cmd_status(message):
    upsert_user(message.from_user)
    settings = load_json("settings")
    total = len(all_likes())
    active = len([x for x in all_likes().values() if x.get("status") == "active"])
    safe_send(message.chat.id, q(f"📊 <b>BOT STATUS</b>\n\nTOTAL AUTOLIKES: {total}\nACTIVE: {active}\nRUN TIME: {settings.get('autolike_time')} IST\nFORCE VERIFY: {settings.get('force_verification')}"))

@bot.message_handler(commands=["like"])
def cmd_like(message):
    upsert_user(message.from_user)
    if not guard_verified(message): return
    if message.chat.id < 0 and not is_group_allowed(message.chat.id):
        safe_send(message.chat.id, q("🚫 <b>GROUP NOT ALLOWED</b>\nAsk owner to use /group allow or /addgroup.")); return
    parts = message.text.split()
    if len(parts) < 3:
        safe_send(message.chat.id, q("Usage: /like {REGION} {UID} {BATCH optional}")); return
    region, uid = clean_region(parts[1]), parts[2]
    batch = fmt_int(parts[3], DEFAULT_DAILY_BATCH) if len(parts) >= 4 else DEFAULT_DAILY_BATCH
    if not is_region(region) or not only_digits(uid):
        safe_send(message.chat.id, q("❌ Invalid format. Example: /like IND 123456789")); return
    msg, result = do_single_like2(region, uid, batch)
    safe_send(message.chat.id, msg)
    log_event("manual_like", message.from_user.id, {"region": region, "uid": uid, "result": result})

@bot.message_handler(commands=["mylike", "myuid"])
def cmd_my_likes(message):
    upsert_user(message.from_user)
    if not guard_verified(message): return
    safe_send(message.chat.id, my_likes_msg(user_likes(message.from_user.id)), main_menu(message.from_user.id))

@bot.message_handler(commands=["autolike"])
def cmd_autolike(message):
    upsert_user(message.from_user)
    if not require_admin(message): return
    parts = message.text.split()
    if len(parts) < 2:
        safe_send(message.chat.id, q("🔧 AUTOLIKE CMDS\n\nautolike list\nautolike run\nautolike add {REGION} {UID} {LIKES} {USER_ID} {ADMIN_ID}\nautolike remove {UID}\nautolike extend {UID} {LIKES}\nautolike reduce {UID} {LIKES}\nautolike batch {UID} {NUM}\nautolike pause {UID}\nautolike resume {UID}\nautolike info {UID}")); return
    action = parts[1].lower()
    actor = message.from_user.id

    if action == "list":
        items = visible_likes_for_actor(actor)
        text, pages = format_like_list(items, 1, "AUTOLIKE USERS", show_admin=is_owner(actor))
        safe_send(message.chat.id, text, list_nav_kb("list", 1, pages, "all"))
        return

    if action == "run":
        if is_owner(actor):
            stats = run_autolike(actor, None, message.chat.id)
        else:
            stats = run_autolike(actor, actor, message.chat.id)
        safe_send(message.chat.id, q(f"✅ AUTOLIKE RUN FINISHED\n\nTOTAL: {stats['total']}\nSENT: {stats['sent']}\nLIMIT: {stats['limit']}\nINVALID: {stats['invalid']}\nSKIPPED: {stats['skipped']}"))
        return

    if action == "add":
        if len(parts) < 7:
            safe_send(message.chat.id, q("Usage: /autolike add {REGION} {UID} {LIKES} {USER_ID} {ADMIN_ID}")); return
        region, uid = clean_region(parts[2]), parts[3]
        likes, user_id, admin_id = fmt_int(parts[4]), fmt_int(parts[5]), fmt_int(parts[6])
        if not is_region(region) or not only_digits(uid) or likes <= 0:
            safe_send(message.chat.id, q("❌ Invalid region, UID or likes.")); return
        if not is_owner(actor) and admin_id != actor:
            safe_send(message.chat.id, q("🚫 Admin can add only with own adminuserid.")); return
        if not is_admin(admin_id):
            safe_send(message.chat.id, q("🚫 Provided adminuserid is not admin.")); return
        if not user_started(user_id):
            safe_send(message.chat.id, q("🚫 Real Telegram user check failed. User must /start the bot first.")); return
        msg, result = do_single_like(region, uid, DEFAULT_DAILY_BATCH)
        d = result.get("display", {})
        if result.get("status") == 0:
            safe_send(message.chat.id, msg); return
        before = d.get("before", 0); after = d.get("after", before); given = max(0, d.get("given", 0))
        item = {
            "uid": uid,
            "region": region,
            "user_id": str(user_id),
            "admin_id": str(admin_id),
            "player": d.get("player") or "UNKNOWN",
            "total": likes,
            "left": max(0, likes - given),
            "used": given,
            "today": given,
            "batch": min(DEFAULT_DAILY_BATCH, MAX_BATCH),
            "status": "active",
            "run_time": load_json("settings").get("autolike_time", DEFAULT_AUTOLIKE_TIME),
            "added_date": display_date(),
            "created_at": now_str(),
            "updated_at": now_str(),
            "last_run": "",
            "likes_before": before,
            "likes_after": after,
        }
        items = all_likes(); items[uid] = item; save_likes(items)
        safe_send(message.chat.id, add_success_msg(item, before, after, given))
        notify_user_like(item, q(f"✅ YOUR UID {uid} HAS BEEN ADDED TO AUTO LIKE\nREGION: {region}\nPLAN: {likes}\nRUN TIME: {item['run_time']} IST"))
        log_event("autolike_add", actor, item)
        return

    if action in ["remove", "pause", "resume", "info"]:
        if len(parts) < 3:
            safe_send(message.chat.id, q(f"Usage: /autolike {action} {{UID}}")); return
        uid = parts[2]
        item = find_like(uid)
        if not item:
            safe_send(message.chat.id, q("❌ UID not found in autolike list.")); return
        if not can_manage_like(actor, item):
            safe_send(message.chat.id, q("🚫 You cannot manage another admin's UID.")); return
        if action == "info":
            safe_send(message.chat.id, format_uid_info(item)); return
        if action == "remove":
            items = all_likes(); items.pop(uid, None); save_likes(items)
            safe_send(message.chat.id, q(f"✅ UID {uid} removed successfully.")); return
        if action == "pause":
            update_like(uid, {"status": "paused"}); safe_send(message.chat.id, q(f"⏸ UID {uid} paused.")); return
        if action == "resume":
            update_like(uid, {"status": "active"}); safe_send(message.chat.id, q(f"✅ UID {uid} resumed.")); return

    if action in ["extend", "reduce", "batch"]:
        if len(parts) < 4:
            safe_send(message.chat.id, q(f"Usage: /autolike {action} {{UID}} {{NUM}}")); return
        uid, num = parts[2], fmt_int(parts[3])
        item = find_like(uid)
        if not item:
            safe_send(message.chat.id, q("❌ UID not found.")); return
        if not can_manage_like(actor, item):
            safe_send(message.chat.id, q("🚫 You cannot manage another admin's UID.")); return
        if action == "extend":
            update_like(uid, {"total": fmt_int(item.get("total")) + num, "left": fmt_int(item.get("left")) + num})
            safe_send(message.chat.id, q(f"✅ UID {uid} extended by {num} likes.")); return
        if action == "reduce":
            update_like(uid, {"total": max(0, fmt_int(item.get("total")) - num), "left": max(0, fmt_int(item.get("left")) - num)})
            safe_send(message.chat.id, q(f"✅ UID {uid} reduced by {num} likes.")); return
        if action == "batch":
            if num < 1 or num > MAX_BATCH:
                safe_send(message.chat.id, q(f"❌ Batch must be 1-{MAX_BATCH}.")); return
            update_like(uid, {"batch": num})
            safe_send(message.chat.id, q(f"✅ UID {uid} batch set to {num}.")); return

    safe_send(message.chat.id, q("❌ Unknown autolike action. Use /autolike for help."))

@bot.message_handler(commands=["setautolikerun"])
def cmd_set_time(message):
    if not require_owner(message): return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        safe_send(message.chat.id, q("Usage: /setautolikerun 4pm")); return
    t = normalize_time(parts[1])
    if not t:
        safe_send(message.chat.id, q("❌ Invalid time. Example: /setautolikerun 4pm or /setautolikerun 04:00")); return
    settings = load_json("settings"); settings["autolike_time"] = t; save_json("settings", settings)
    items = all_likes()
    for it in items.values(): it["run_time"] = t
    save_likes(items)
    schedule_autolike_job()
    safe_send(message.chat.id, q(f"✅ AUTO LIKE RUN TIME SET TO {t} IST FOR ALL SAVED UIDS."))

@bot.message_handler(commands=["createredeem", "redeemgen"])
def cmd_create_redeem(message):
    if not require_owner(message): return
    parts = message.text.split()
    if len(parts) < 4:
        safe_send(message.chat.id, q("Usage: /createredeem {CODE|random} {LIKES} {COUNT}")); return
    code_arg, likes, count = parts[1], fmt_int(parts[2]), fmt_int(parts[3])
    if likes <= 0 or count <= 0:
        safe_send(message.chat.id, q("❌ Likes and count must be positive.")); return
    redeem = load_json("redeem")
    made = []
    for _ in range(count):
        code = make_code() if code_arg.lower() in ["random", "gen", "auto"] else (code_arg if count == 1 else f"{code_arg}-{_+1}")
        redeem.setdefault("codes", {})[code] = {"code": code, "likes": likes, "created_by": str(message.from_user.id), "created_at": now_str(), "used": False, "used_by": ""}
        made.append(code)
    save_json("redeem", redeem)
    safe_send(message.chat.id, q("🎁 REDEEM CODE CREATED\n\n" + "\n".join(made), mono=True))

@bot.message_handler(commands=["redeem"])
def cmd_redeem(message):
    upsert_user(message.from_user)
    if not guard_verified(message): return
    parts = message.text.split()
    if len(parts) < 4:
        safe_send(message.chat.id, q("Usage: /redeem {CODE} {REGION} {UID}")); return
    code, region, uid = parts[1], clean_region(parts[2]), parts[3]
    if not is_region(region) or not only_digits(uid):
        safe_send(message.chat.id, q("❌ Invalid region or UID.")); return
    redeem = load_json("redeem")
    c = redeem.get("codes", {}).get(code)
    if not c or c.get("used"):
        safe_send(message.chat.id, q("❌ Invalid or already used redeem code.")); return
    likes = fmt_int(c.get("likes"))
    fake = f"/autolike add {region} {uid} {likes} {message.from_user.id} {OWNER_ID}"
    message.text = fake
    c["used"] = True; c["used_by"] = str(message.from_user.id); c["used_at"] = now_str(); redeem.setdefault("used", {})[code] = c
    save_json("redeem", redeem)
    cmd_autolike(message)

@bot.message_handler(commands=["redeemdel"])
def cmd_redeem_del(message):
    if not require_owner(message): return
    parts = message.text.split()
    if len(parts) < 2: safe_send(message.chat.id, q("Usage: /redeemdel {CODE}")); return
    data = load_json("redeem"); data.get("codes", {}).pop(parts[1], None); save_json("redeem", data)
    safe_send(message.chat.id, q("✅ Redeem code deleted."))

@bot.message_handler(commands=["redeemcheck"])
def cmd_redeem_check(message):
    if not require_admin(message): return
    parts = message.text.split()
    if len(parts) < 2: safe_send(message.chat.id, q("Usage: /redeemcheck {CODE}")); return
    c = load_json("redeem").get("codes", {}).get(parts[1])
    safe_send(message.chat.id, q(json.dumps(c or {"error":"not found"}, indent=2), mono=True))

@bot.message_handler(commands=["adminadd"])
def cmd_admin_add(message):
    if not require_owner(message): return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        safe_send(message.chat.id, q("Usage: /adminadd {USER_ID} {TAG}")); return
    uid, tag = fmt_int(parts[1]), parts[2]
    if not user_started(uid):
        safe_send(message.chat.id, q("🚫 User must /start bot first.")); return
    data = load_json("admins"); data.setdefault("admins", {})[str(uid)] = {"id": str(uid), "tag": tag, "added_by": str(message.from_user.id), "added_at": now_str()}; save_json("admins", data)
    safe_send(message.chat.id, q(f"✅ ADMIN ADDED\nUSER: {uid}\nTAG: {esc(tag)}"))

@bot.message_handler(commands=["promote"])
def cmd_promote(message):
    if not require_owner(message): return
    if not message.reply_to_message:
        safe_send(message.chat.id, q("Reply to user's message with /promote {TAG}")); return
    parts = message.text.split(maxsplit=1)
    tag = parts[1] if len(parts) > 1 else (message.reply_to_message.from_user.first_name or "ADMIN")
    user = message.reply_to_message.from_user
    upsert_user(user)
    data = load_json("admins"); data.setdefault("admins", {})[str(user.id)] = {"id": str(user.id), "tag": tag, "added_by": str(message.from_user.id), "added_at": now_str()}; save_json("admins", data)
    safe_send(message.chat.id, q(f"✅ PROMOTED\nUSER ID: {user.id}\nTAG: {esc(tag)}"))

@bot.message_handler(commands=["adminremove"])
def cmd_admin_remove(message):
    if not require_owner(message): return
    parts = message.text.split()
    if len(parts) < 2: safe_send(message.chat.id, q("Usage: /adminremove {USER_ID}")); return
    data = load_json("admins"); data.get("admins", {}).pop(str(parts[1]), None); save_json("admins", data)
    safe_send(message.chat.id, q("✅ Admin removed."))

@bot.message_handler(commands=["adminlist"])
def cmd_admin_list(message):
    if not require_owner(message): return
    admins = load_json("admins").get("admins", {})
    body = "🛡 ADMIN LIST\n\n"
    for i, (uid, adm) in enumerate(admins.items(), 1):
        body += f"{i}. {uid} - {adm.get('tag')}\n"
    safe_send(message.chat.id, q(body or "No admins", mono=True))

@bot.message_handler(commands=["broadcast"])
def cmd_broadcast(message):
    if not require_admin(message): return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        safe_send(message.chat.id, q("Usage: /broadcast {MESSAGE}")); return
    msg = q("📣 BROADCAST\n\n" + tiny_caps(parts[1]))
    users = load_json("users").get("users", {})
    sent = 0
    for uid in users.keys():
        if safe_send(int(uid), msg): sent += 1
        time.sleep(0.04)
    safe_send(message.chat.id, q(f"✅ BROADCAST FINISHED\nSENT: {sent}"))

@bot.message_handler(commands=["addgroup"])
def cmd_add_group(message):
    if not require_owner(message): return
    parts = message.text.split()
    gid = str(message.chat.id if len(parts) < 2 else parts[1])
    groups = load_json("groups")
    arr = groups.setdefault("allowed_groups", [])
    if gid not in [str(x) for x in arr]: arr.append(gid)
    save_json("groups", groups)
    safe_send(message.chat.id, q(f"✅ GROUP ALLOWED\nID: {gid}"))

@bot.message_handler(commands=["group"])
def cmd_group(message):
    if not require_owner(message): return
    if "allow" in message.text.lower():
        message.text = f"/addgroup {message.chat.id}"
        cmd_add_group(message)
    else:
        safe_send(message.chat.id, q("Usage: /group allow"))

@bot.message_handler(commands=["forceverify"])
def cmd_forceverify(message):
    if not require_owner(message): return
    parts = message.text.split()
    if len(parts) < 2:
        safe_send(message.chat.id, q("Usage: /forceverify on|off [@channel]")); return
    settings = load_json("settings")
    settings["force_verification"] = parts[1].lower() in ["on", "yes", "true", "1"]
    if len(parts) >= 3: settings["verification_channel"] = parts[2]
    save_json("settings", settings)
    safe_send(message.chat.id, q(f"✅ FORCE VERIFICATION: {settings['force_verification']}\nCHANNEL: {settings.get('verification_channel','')}"))

@bot.message_handler(commands=["setmessage"])
def cmd_setmessage(message):
    if not require_owner(message): return
    txt = message.text.split(maxsplit=1)[1] if len(message.text.split(maxsplit=1)) > 1 else ""
    settings = load_json("settings"); settings["welcome_message"] = txt; save_json("settings", settings)
    safe_send(message.chat.id, q("✅ Message saved."))

@bot.message_handler(commands=["setimage"])
def cmd_setimage(message):
    if not require_owner(message): return
    txt = message.text.split(maxsplit=1)[1] if len(message.text.split(maxsplit=1)) > 1 else ""
    settings = load_json("settings"); settings["welcome_image"] = txt; save_json("settings", settings)
    safe_send(message.chat.id, q("✅ Image URL saved."))

@bot.message_handler(commands=["pin"])
def cmd_pin(message):
    if not require_admin(message): return
    txt = message.text.split(maxsplit=1)[1] if len(message.text.split(maxsplit=1)) > 1 else ""
    m = safe_send(message.chat.id, q(tiny_caps(txt)))
    if m:
        try: bot.pin_chat_message(message.chat.id, m.message_id)
        except Exception: pass

# =============================================================
# ======================== CALLBACKS ===========================
# =============================================================

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    uid = call.from_user.id
    upsert_user(call.from_user)
    data = call.data or ""
    if data == "verify_me":
        mark_verified(uid)
        bot.answer_callback_query(call.id, "Verified saved.")
        safe_edit(call.message.chat.id, call.message.message_id, q("✅ VERIFICATION COMPLETED."), main_menu(uid))
        return
    if data.startswith("list:"):
        _, scope, page_s = data.split(":", 2)
        page = fmt_int(page_s, 1)
        items = visible_likes_for_actor(uid)
        text, pages = format_like_list(items, page, "AUTOLIKE USERS", show_admin=is_owner(uid))
        safe_edit(call.message.chat.id, call.message.message_id, text, list_nav_kb("list", page, pages, scope))
        bot.answer_callback_query(call.id, "Updated")
        return
    if data.startswith("adminlikes:"):
        _, admin_id_s, page_s = data.split(":", 2)
        if not is_owner(uid):
            bot.answer_callback_query(call.id, "Owner only", show_alert=True); return
        page = fmt_int(page_s, 1); admin_id = fmt_int(admin_id_s)
        items = admin_likes(admin_id)
        text, pages = format_like_list(items, page, f"AUTOLIKES BY {admin_tag(admin_id)}", show_admin=True)
        safe_edit(call.message.chat.id, call.message.message_id, text, list_nav_kb("adminlikes", page, pages, str(admin_id)))
        return

# =============================================================
# ====================== TEXT MENU HANDLER =====================
# =============================================================

@bot.message_handler(func=lambda m: True, content_types=["text"])
def text_router(message):
    upsert_user(message.from_user)
    txt = (message.text or "").strip()
    low = txt.lower()
    if low in ["❤️ my likes", "my likes", "mylike", "my uid"]:
        cmd_my_likes(message); return
    if low in ["🎁 redeem", "redeem"]:
        safe_send(message.chat.id, q("🎁 REDEEM FORMAT\n/redeem {CODE} {REGION} {UID}")); return
    if low in ["📋 plans", "plans"]:
        cmd_plans(message); return
    if low in ["🛠 help", "help"]:
        cmd_help(message); return
    if low in ["🛡 admin dashboard", "admindashboard"]:
        if require_admin(message): safe_send(message.chat.id, q("🛡 ADMIN DASHBOARD OPENED"), admin_dashboard_kb()); return
    if low in ["👑 owner dashboard", "ownerdashboard"]:
        if require_owner(message): safe_send(message.chat.id, q("👑 OWNER DASHBOARD OPENED"), owner_dashboard_kb()); return
    if low in ["⬅️ back", "back"]:
        safe_send(message.chat.id, q("🏠 MAIN MENU"), main_menu(message.from_user.id)); return
    if low in ["➕ add autolike", "add autolike"]:
        safe_send(message.chat.id, q("➕ ADD AUTOLIKE FORMAT\n/autolike add {REGION} {UID} {LIKES} {USER_ID} {ADMIN_ID}")); return
    if low in ["📣 broadcast", "broadcast"]:
        safe_send(message.chat.id, q("📣 BROADCAST FORMAT\n/broadcast {MESSAGE}")); return
    if low in ["🚀 autolike run", "autolikerun"]:
        message.text = "/autolike run"; cmd_autolike(message); return
    if low in ["📜 autolike list", "autolikelist"]:
        message.text = "/autolike list"; cmd_autolike(message); return
    if low in ["📊 admin stats", "admin stats"]:
        if not require_owner(message): return
        admins = load_json("admins").get("admins", {})
        body = "📊 ADMIN LIKE STATS\n\n"
        for aid, adm in admins.items():
            count = len(admin_likes(fmt_int(aid)))
            total_left = sum(fmt_int(x.get("left")) for x in admin_likes(fmt_int(aid)))
            body += f"🛡 {adm.get('tag')} ({aid})\nUIDS: {count}\nLEFT: {total_left}\n\n"
        safe_send(message.chat.id, q(body, mono=True)); return
    if low in ["👥 admins autolike list", "admins autolike list"]:
        if not require_owner(message): return
        admins = load_json("admins").get("admins", {})
        kb = types.InlineKeyboardMarkup(row_width=1)
        for aid, adm in admins.items():
            kb.add(types.InlineKeyboardButton(f"{adm.get('tag')} - {aid}", callback_data=f"adminlikes:{aid}:1"))
        safe_send(message.chat.id, q("👥 SELECT ADMIN TO VIEW AUTOLIKE LIST"), kb); return
    if low in ["🎁 redeem panel", "redeem panel"]:
        safe_send(message.chat.id, q("🎁 REDEEM PANEL\n/createredeem random 1000 5\n/redeemcheck CODE\n/redeemdel CODE")); return
    if low in ["⏰ set time", "setime"]:
        safe_send(message.chat.id, q("⏰ SET TIME FORMAT\n/setautolikerun 4pm")); return
    if low in ["🔐 set force verification", "set force verification"]:
        safe_send(message.chat.id, q("🔐 FORCE VERIFY FORMAT\n/forceverify on @channel\n/forceverify off")); return
    if low.startswith("autolike "):
        message.text = "/" + txt
        cmd_autolike(message)
        return
    

# =============================================================
# ======================== SCHEDULER ===========================
# =============================================================

def scheduled_autolike():
    try:
        reset_daily_if_needed()
        run_autolike(OWNER_ID, None, None)
    except Exception:
        log_event("scheduler_error", OWNER_ID, {"trace": traceback.format_exc()})


def schedule_autolike_job():
    try:
        scheduler.remove_job("daily_autolike")
    except Exception:
        pass
    settings = load_json("settings")
    t = settings.get("autolike_time") or DEFAULT_AUTOLIKE_TIME
    hh, mm = [int(x) for x in t.split(":")]
    scheduler.add_job(scheduled_autolike, CronTrigger(hour=hh, minute=mm), id="daily_autolike", replace_existing=True)

# =============================================================
# ========================= BOT COMMAND MENU ===================
# =============================================================

def set_bot_commands():
    commands = [
        types.BotCommand("start", "Open bot main menu"),
        types.BotCommand("help", "Show commands"),
        types.BotCommand("plans", "Show premium plans"),
        types.BotCommand("mylike", "Show your saved UID likes"),
        types.BotCommand("redeem", "Redeem premium code"),
        types.BotCommand("status", "Show bot status"),
        types.BotCommand("like", "Send one-time like"),
        types.BotCommand("autolike", "Admin autolike manager"),
        types.BotCommand("setautolikerun", "Owner set daily run time"),
        types.BotCommand("createredeem", "Owner create redeem code"),
    ]
    try:
        bot.set_my_commands(commands)
    except Exception:
        pass

# =============================================================
# ============================ MAIN ============================
# =============================================================

if __name__ == "__main__":
    ensure_db()
    set_bot_commands()
    schedule_autolike_job()
    scheduler.start()
    print(f"{BOT_NAME} bot running...")
    print(f"Database folder: {os.path.abspath(DB_DIR)}")
    print(f"Daily autolike time: {load_json('settings').get('autolike_time')} IST")
    bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
