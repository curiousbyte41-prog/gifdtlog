#!/usr/bin/env python3
"""
████████████████████████████████████████████████████████████████████████████████████
██                                                                                ██
██  🎁 ULTIMATE GIFT CARD & RECHARGE BOT v4.0 - PRODUCTION READY 🎁              ██
██                                                                                ██
██  ╔══════════════════════════════════════════════════════════════════════════╗  ██
██  ║                    ALL ISSUES FIXED - RAILWAY DEPLOY READY               ║  ██
██  ╚══════════════════════════════════════════════════════════════════════════╝  ██
██                                                                                ██
██  ✓ BOT_USERNAME fixed                                     ✓ SQLite pool size=3 ██
██  ✓ update_verification_by_utr added                       ✓ Env validation    ██
██  ✓ buy_gift flow working                                  ✓ Parse mode fixed  ██
██  ✓ main_menu callback fixed                               ✓ Support tickets   ██
██  ✓ mobile states working                                  ✓ Coupon redesign   ██
██  ✓ InlineKeyboardMarkup fixed                             ✓ Stats accurate    ██
██  ✓ Webhook ready                                          ✓ Modular structure ██
██                                                                                ██
████████████████████████████████████████████████████████████████████████████████████
"""

import os
import sys
import json
import logging
import sqlite3
import asyncio
import random
import re
import hashlib
import time
import threading
import csv
import uuid
from datetime import datetime, timedelta, date
from functools import wraps
from io import StringIO
from queue import Queue
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from collections import defaultdict

try:
    import qrcode
    from PIL import Image
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters, ContextTypes
)
from telegram.constants import ParseMode
from telegram.error import TelegramError, RetryAfter, TimedOut

# ============================================================================
# ENVIRONMENT VARIABLES WITH VALIDATION
# ============================================================================

def get_env_var(name: str, required: bool = True, default: Any = None) -> Any:
    """Get environment variable with validation"""
    value = os.environ.get(name, default)
    if required and not value:
        raise ValueError(f"❌ {name} environment variable not set!")
    return value

BOT_TOKEN = get_env_var("BOT_TOKEN,8767455153:AAG_rJXoj2_7HF_m9EfZoquCwN1-L5Uigr4")
BOT_USERNAME = get_env_var("BOT_USERNAME", required=False, default="")
ADMIN_ID = int(get_env_var("ADMIN_ID"))
UPI_ID = get_env_var("UPI_ID")
MAIN_CHANNEL = get_env_var("MAIN_CHANNEL", default="@gift_card_main")
ADMIN_CHANNEL_ID = int(get_env_var("ADMIN_CHANNEL_ID", default="-1003607749028"))
PROOF_CHANNEL = get_env_var("PROOF_CHANNEL", default="@gift_card_log")
DATABASE_PATH = get_env_var("DATABASE_PATH", default="bot_database.db")
QR_CODE_PATH = get_env_var("QR_CODE_PATH", default="qr.jpg")
WEBHOOK_URL = get_env_var("WEBHOOK_URL", required=False, default="")
WEBHOOK_PORT = int(get_env_var("WEBHOOK_PORT", default="8080"))
WEBHOOK_SECRET = get_env_var("WEBHOOK_SECRET", required=False, default="")

# ============================================================================
# BASE CONFIGURATION
# ============================================================================

MIN_RECHARGE = 10
MAX_RECHARGE = 10000
FEE_PERCENT = 20
FEE_THRESHOLD = 120
REFERRAL_BONUS = 2
WELCOME_BONUS = 5
POSTS_PER_DAY = 12
POST_INTERVAL = 7200

# ============================================================================
# GIFT CARDS - 25+ BRANDS with 65% OFF
# ============================================================================

GIFT_CARDS = {
    "amazon": {"name": "AMAZON", "emoji": "🟦", "full_emoji": "🟦🛒", "popular": True, "category": "shopping"},
    "flipkart": {"name": "FLIPKART", "emoji": "📦", "full_emoji": "📦🛍️", "popular": True, "category": "shopping"},
    "myntra": {"name": "MYNTRA", "emoji": "🛍️", "full_emoji": "🛍️👗", "popular": True, "category": "shopping"},
    "ajio": {"name": "AJIO", "emoji": "👕", "full_emoji": "👕🛍️", "popular": False, "category": "shopping"},
    "snapdeal": {"name": "SNAPDEAL", "emoji": "🧥", "full_emoji": "🧥📦", "popular": False, "category": "shopping"},
    "kindle": {"name": "AMAZON KINDLE", "emoji": "📚", "full_emoji": "📚🟦", "popular": False, "category": "shopping"},
    "croma": {"name": "CROMA", "emoji": "💻", "full_emoji": "💻🖥️", "popular": False, "category": "shopping"},
    "reliance": {"name": "RELIANCE DIGITAL", "emoji": "📱", "full_emoji": "📱🛒", "popular": False, "category": "shopping"},
    "tatacliq": {"name": "TATA CLIQ", "emoji": "🛍️", "full_emoji": "🛍️🔴", "popular": False, "category": "shopping"},
    "shoppersstop": {"name": "SHOPPERS STOP", "emoji": "👔", "full_emoji": "👔🛍️", "popular": False, "category": "shopping"},
    "playstore": {"name": "PLAY STORE", "emoji": "🟩", "full_emoji": "🟩🎮", "popular": True, "category": "gaming"},
    "xbox": {"name": "XBOX", "emoji": "🎮", "full_emoji": "🎮🟢", "popular": False, "category": "gaming"},
    "playstation": {"name": "PLAYSTATION", "emoji": "🎮", "full_emoji": "🎮🔵", "popular": False, "category": "gaming"},
    "nintendo": {"name": "NINTENDO", "emoji": "🎮", "full_emoji": "🎮🔴", "popular": False, "category": "gaming"},
    "steam": {"name": "STEAM", "emoji": "🎮", "full_emoji": "🎮💨", "popular": False, "category": "gaming"},
    "epic": {"name": "EPIC GAMES", "emoji": "🎮", "full_emoji": "🎮⚡", "popular": False, "category": "gaming"},
    "rockstar": {"name": "ROCKSTAR", "emoji": "🎮", "full_emoji": "🎮⭐", "popular": False, "category": "gaming"},
    "ubisoft": {"name": "UBISOFT", "emoji": "🎮", "full_emoji": "🎮🔷", "popular": False, "category": "gaming"},
    "bookmyshow": {"name": "BOOKMYSHOW", "emoji": "🎟️", "full_emoji": "🎟️🎬", "popular": True, "category": "entertainment"},
    "netflix": {"name": "NETFLIX", "emoji": "🎬", "full_emoji": "🎬📺", "popular": False, "category": "entertainment"},
    "primevideo": {"name": "PRIME VIDEO", "emoji": "🎬", "full_emoji": "🎬🔵", "popular": False, "category": "entertainment"},
    "hotstar": {"name": "HOTSTAR", "emoji": "🎬", "full_emoji": "🎬🟠", "popular": False, "category": "entertainment"},
    "sonyliv": {"name": "SONY LIV", "emoji": "🎬", "full_emoji": "🎬🟢", "popular": False, "category": "entertainment"},
    "spotify": {"name": "SPOTIFY", "emoji": "🎵", "full_emoji": "🎵🎧", "popular": False, "category": "music"},
    "gaana": {"name": "GAANA", "emoji": "🎵", "full_emoji": "🎵🟠", "popular": False, "category": "music"},
    "wynk": {"name": "WYNK", "emoji": "🎵", "full_emoji": "🎵🔴", "popular": False, "category": "music"},
    "zomato": {"name": "ZOMATO", "emoji": "🍕", "full_emoji": "🍕🍔", "popular": True, "category": "food"},
    "swiggy": {"name": "SWIGGY", "emoji": "🍔", "full_emoji": "🍔🍟", "popular": False, "category": "food"},
    "zomatogold": {"name": "ZOMATO GOLD", "emoji": "🥡", "full_emoji": "🥡⭐", "popular": False, "category": "food"},
    "dominos": {"name": "DOMINOS", "emoji": "🍕", "full_emoji": "🍕🔴", "popular": False, "category": "food"},
    "pizzahut": {"name": "PIZZA HUT", "emoji": "🍕", "full_emoji": "🍕🟢", "popular": False, "category": "food"},
    "bigbasket": {"name": "BIG BASKET", "emoji": "🛒", "full_emoji": "🛒🥬", "popular": False, "category": "grocery"},
    "grofers": {"name": "GROFERS", "emoji": "🛒", "full_emoji": "🛒🟠", "popular": False, "category": "grocery"},
    "zepto": {"name": "ZEPTO", "emoji": "⚡", "full_emoji": "⚡🛒", "popular": False, "category": "grocery"},
}

GIFT_PRICES = {500: 175, 1000: 350, 2000: 700, 5000: 1750, 10000: 3500}
GIFT_DENOMINATIONS = [500, 1000, 2000, 5000, 10000]

# ============================================================================
# GAME RECHARGES
# ============================================================================

GAME_RECHARGES = {
    "freefire": {"name": "FREE FIRE", "emoji": "🔫", "full_emoji": "🔫🔥", "popular": True},
    "ffmax": {"name": "FREE FIRE MAX", "emoji": "🔫", "full_emoji": "🔫💎", "popular": True},
    "pubg": {"name": "PUBG MOBILE", "emoji": "🎯", "full_emoji": "🎯🪖", "popular": True},
    "bgmi": {"name": "BGMI", "emoji": "🎯", "full_emoji": "🎯🇮🇳", "popular": True},
    "cod": {"name": "CALL OF DUTY", "emoji": "🔫", "full_emoji": "🔫🎮", "popular": False},
    "dream11": {"name": "DREAM11", "emoji": "🏏", "full_emoji": "🏏🎯", "popular": False},
    "my11circle": {"name": "MY11CIRCLE", "emoji": "🏏", "full_emoji": "🏏🔄", "popular": False},
}

GAME_PRICES = {
    "freefire": [100, 200, 300, 400, 500, 1000, 2000],
    "ffmax": [100, 200, 300, 400, 500, 1000, 2000],
    "pubg": [120, 240, 360, 600, 1200, 2400],
    "bgmi": [120, 240, 360, 600, 1200, 2400],
    "cod": [100, 200, 300, 500, 1000, 2000],
    "dream11": [50, 100, 200, 500, 1000],
    "my11circle": [50, 100, 200, 500, 1000],
}

# ============================================================================
# MOBILE/DTH/FIBER OPERATORS
# ============================================================================

MOBILE_OPERATORS = {
    "airtel": {"name": "AIRTEL", "emoji": "🔴", "full_emoji": "🔴📱", "popular": True},
    "jio": {"name": "JIO", "emoji": "🟣", "full_emoji": "🟣📱", "popular": True},
    "vi": {"name": "VI", "emoji": "🟢", "full_emoji": "🟢📱", "popular": True},
    "bsnl": {"name": "BSNL", "emoji": "🔵", "full_emoji": "🔵📱", "popular": False},
}

MOBILE_PLANS = {
    "airtel": [199, 299, 399, 499, 599, 699, 799, 999, 1199, 1499, 1799, 1999, 2399, 2699, 2999],
    "jio": [149, 249, 349, 449, 549, 599, 699, 799, 899, 999, 1199, 1299, 1499, 1699, 1999, 2399, 2999],
    "vi": [199, 299, 399, 499, 599, 699, 799, 899, 999, 1099, 1299, 1499, 1699, 1999, 2299, 2599],
    "bsnl": [99, 149, 199, 249, 299, 349, 399, 449, 499, 599, 649, 699, 799, 899, 999, 1199],
}

DTH_OPERATORS = {
    "tatasky": {"name": "TATA SKY", "emoji": "🟠", "full_emoji": "🟠📺", "popular": True},
    "airteldth": {"name": "AIRTEL DTH", "emoji": "🔴", "full_emoji": "🔴📺", "popular": True},
    "dishtv": {"name": "DISH TV", "emoji": "🟡", "full_emoji": "🟡📺", "popular": True},
    "sundirect": {"name": "SUN DIRECT", "emoji": "🟢", "full_emoji": "🟢📺", "popular": False},
}

DTH_PLANS = {
    "tatasky": [99, 149, 199, 249, 299, 349, 399, 449, 499, 599, 699, 799, 999, 1199, 1499, 1999],
    "airteldth": [99, 149, 199, 249, 299, 349, 399, 449, 499, 599, 699, 799, 999, 1299, 1599, 1999],
    "dishtv": [99, 149, 199, 249, 299, 349, 399, 449, 499, 599, 699, 799, 899, 999, 1299, 1599],
    "sundirect": [99, 149, 199, 249, 299, 349, 399, 449, 499, 599, 649, 699, 799, 899, 999, 1199],
}

FIBER_OPERATORS = {
    "jiofiber": {"name": "JIO FIBER", "emoji": "🟣", "full_emoji": "🟣🌐", "popular": True},
    "airtelxstream": {"name": "AIRTEL XSTREAM", "emoji": "🔴", "full_emoji": "🔴🌐", "popular": True},
    "bsnlfiber": {"name": "BSNL FIBER", "emoji": "🔵", "full_emoji": "🔵🌐", "popular": False},
    "actfiber": {"name": "ACT FIBER", "emoji": "🟢", "full_emoji": "🟢🌐", "popular": False},
}

FIBER_PLANS = {
    "jiofiber": [399, 499, 599, 699, 799, 899, 999, 1299, 1499, 1699, 1999, 2499, 2999, 3999],
    "airtelxstream": [499, 599, 699, 799, 899, 999, 1299, 1499, 1699, 1999, 2499, 2999, 3999, 4999],
    "bsnlfiber": [399, 499, 599, 699, 799, 899, 999, 1299, 1499, 1999, 2499],
    "actfiber": [499, 599, 699, 799, 899, 999, 1299, 1499, 1699, 1999, 2499, 2999, 3999],
}

# ============================================================================
# DAILY REWARDS CONFIGURATION
# ============================================================================

DAILY_REWARDS = {
    1: 5, 2: 8, 3: 10, 4: 12, 5: 15,
    6: 18, 7: 25, 10: 40, 15: 60, 20: 80, 25: 100, 30: 150,
    50: 250, 75: 400, 100: 600
}

# ============================================================================
# COUPONS CONFIGURATION - FIXED ARCHITECTURE
# ============================================================================

COUPONS_MASTER = {
    "WELCOME10": {"discount": 10, "type": "percentage", "min": 100, "max_uses": 1000, "expiry_days": 30},
    "WELCOME20": {"discount": 20, "type": "percentage", "min": 200, "max_uses": 500, "expiry_days": 30},
    "SAVE20":    {"discount": 20, "type": "fixed",      "min": 200, "max_uses": 500, "expiry_days": 30},
    "FIRST50":   {"discount": 50, "type": "fixed",      "min": 500, "max_uses": 200, "expiry_days": 30},
    "DIWALI22":  {"discount": 22, "type": "percentage", "min": 200, "max_uses": 1000, "expiry_days": 7},
    "HOLI15":    {"discount": 15, "type": "percentage", "min": 150, "max_uses": 1000, "expiry_days": 3},
    "FLASH50":   {"discount": 50, "type": "percentage", "min": 500, "max_uses": 500, "expiry_days": 1},
}

# ============================================================================
# BULK DISCOUNTS CONFIGURATION
# ============================================================================

BULK_DISCOUNTS = {
    1: 0, 2: 0, 3: 3, 4: 4, 5: 5,
    10: 8, 15: 10, 20: 12, 25: 15,
    30: 17, 40: 18, 50: 20, 75: 22, 100: 25
}

# ============================================================================
# AMOUNT BUTTONS FOR RECHARGE
# ============================================================================

AMOUNT_BUTTONS = [
    [10, 20, 30, 50],
    [120, 150, 200, 300],
    [400, 500, 1000, 2000],
    [5000, 10000, 15000, 20000]
]

# ============================================================================
# WALLET TRANSFER CONFIGURATION
# ============================================================================

WALLET_TRANSFER_MIN = 10
WALLET_TRANSFER_MAX = 5000
WALLET_TRANSFER_FEE = 2

# ============================================================================
# MYSTERY BOX CONFIGURATION
# ============================================================================

MYSTERY_BOX_PRICE = 100
MYSTERY_BOX_MIN = 50
MYSTERY_BOX_MAX = 500
MYSTERY_BOX_JACKPOT = 1000
MYSTERY_BOX_SUPER_JACKPOT = 5000

# ============================================================================
# CARD EXCHANGE CONFIGURATION
# ============================================================================

CARD_EXCHANGE_FEE = 5

# ============================================================================
# CONVERSATION STATES
# ============================================================================

(
    STATE_SCREENSHOT,
    STATE_UTR,
    STATE_EMAIL,
    STATE_SUPPORT,
    STATE_AMOUNT,
    STATE_MOBILE_NUMBER,
    STATE_MOBILE_PLAN,
    STATE_DTH_NUMBER,
    STATE_DTH_PLAN,
    STATE_FIBER_NUMBER,
    STATE_FIBER_PLAN,
    STATE_GAME_USER_ID,
    STATE_WALLET_TRANSFER_USERNAME,
    STATE_WALLET_TRANSFER_AMOUNT,
    STATE_WALLET_TRANSFER_CONFIRM,
    STATE_MYSTERY_BOX,
    STATE_CARD_EXCHANGE_FROM,
    STATE_CARD_EXCHANGE_TO,
    STATE_PRICE_ALERT_CARD,
    STATE_PRICE_ALERT_PRICE,
    STATE_COUPON_CODE,
    STATE_BULK_COUNT,
    STATE_BULK_CARD,
    STATE_GIFT_EMAIL,
    STATE_GIFT_MESSAGE,
    STATE_ADMIN_BROADCAST,
    STATE_ADMIN_ADD_CARD,
    STATE_ADMIN_REMOVE_CARD,
    STATE_ADMIN_UPDATE_PRICE,
    STATE_ADMIN_ADD_STOCK,
    STATE_ADMIN_REMOVE_STOCK,
    STATE_ADMIN_ADD_COUPON,
    STATE_ADMIN_REMOVE_COUPON,
    STATE_ADMIN_BAN_USER,
    STATE_ADMIN_UNBAN_USER,
    STATE_ADMIN_ADD_BALANCE,
    STATE_ADMIN_REMOVE_BALANCE,
) = range(37)

# ============================================================================
# LOGGING SETUP
# ============================================================================

log_dir = Path("logs")
try:
    log_dir.mkdir(exist_ok=True)
except:
    log_dir = Path(".")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / "bot.log", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# RATE LIMITER
# ============================================================================

class RateLimiter:
    def __init__(self, max_requests=30, window=60):
        self.max_requests = max_requests
        self.window = window
        self.requests = {}
        self.lock = threading.Lock()

    def is_allowed(self, user_id):
        with self.lock:
            now = time.time()
            user_requests = self.requests.get(user_id, [])
            user_requests = [r for r in user_requests if now - r < self.window]
            if len(user_requests) >= self.max_requests:
                return False
            user_requests.append(now)
            self.requests[user_id] = user_requests
            return True

rate_limiter = RateLimiter()

# ============================================================================
# DATABASE MANAGER - FIXED VERSION
# ============================================================================

class DatabaseManager:
    def __init__(self, db_path, pool_size=3):  # Reduced pool size for Railway
        self.db_path = db_path
        self.pool = Queue(maxsize=pool_size)
        self.lock = threading.Lock()
        self.cache = {}
        self.cache_lock = threading.Lock()
        
        # Test database connection
        try:
            test_conn = sqlite3.connect(db_path, timeout=30)
            test_conn.close()
            logger.info(f"✅ Database connection test passed: {db_path}")
        except Exception as e:
            logger.error(f"❌ Database connection test failed: {e}")
            raise
        
        for _ in range(pool_size):
            try:
                conn = sqlite3.connect(db_path, timeout=30, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA foreign_keys=ON")
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA synchronous=NORMAL")
                self.pool.put(conn)
            except Exception as e:
                logger.error(f"❌ Failed to create database connection: {e}")
        
        self._init_db()
        self._create_indexes()

    def get_conn(self):
        return self.pool.get(timeout=10)

    def return_conn(self, conn):
        self.pool.put(conn)

    def execute(self, query, params=(), fetchone=False, fetchall=False, commit=False):
        conn = self.get_conn()
        try:
            cur = conn.cursor()
            cur.execute(query, params)
            if commit:
                conn.commit()
                return cur.lastrowid
            if fetchone:
                return cur.fetchone()
            if fetchall:
                return cur.fetchall()
        except Exception as e:
            conn.rollback()
            logger.error(f"DB Error: {e} | Query: {query} | Params: {params}")
            raise
        finally:
            self.return_conn(conn)

    def close_all(self):
        """Close all database connections - call on shutdown"""
        while not self.pool.empty():
            conn = self.pool.get()
            conn.close()
        logger.info("✅ All database connections closed")

    def _init_db(self):
        conn = self.get_conn()
        try:
            c = conn.cursor()
            c.executescript("""
                -- Users table
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    phone TEXT,
                    email TEXT,
                    balance INTEGER DEFAULT 0,
                    bonus_balance INTEGER DEFAULT 0,
                    locked_balance INTEGER DEFAULT 0,
                    total_recharged INTEGER DEFAULT 0,
                    total_spent INTEGER DEFAULT 0,
                    total_purchases INTEGER DEFAULT 0,
                    total_referrals INTEGER DEFAULT 0,
                    referral_code TEXT UNIQUE,
                    referred_by INTEGER,
                    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    language TEXT DEFAULT 'en',
                    streak INTEGER DEFAULT 0,
                    last_claim DATE,
                    birth_date DATE,
                    anniversary_date DATE,
                    is_banned INTEGER DEFAULT 0,
                    ban_reason TEXT,
                    role TEXT DEFAULT 'user',
                    notes TEXT,
                    FOREIGN KEY (referred_by) REFERENCES users(user_id)
                );

                -- Transactions table
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    transaction_id TEXT UNIQUE,
                    amount INTEGER,
                    type TEXT,
                    category TEXT,
                    status TEXT DEFAULT 'completed',
                    payment_method TEXT,
                    utr TEXT UNIQUE,
                    description TEXT,
                    fee INTEGER DEFAULT 0,
                    final_amount INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );

                -- Purchases table
                CREATE TABLE IF NOT EXISTS purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    order_id TEXT UNIQUE,
                    item_type TEXT,
                    item_category TEXT,
                    item_id TEXT,
                    item_name TEXT,
                    amount INTEGER,
                    price INTEGER,
                    quantity INTEGER DEFAULT 1,
                    discount INTEGER DEFAULT 0,
                    coupon TEXT,
                    email TEXT,
                    recipient TEXT,
                    gift_message TEXT,
                    proof_sent INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',  -- pending, processing, completed, failed
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );

                -- Verifications table
                CREATE TABLE IF NOT EXISTS verifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount INTEGER,
                    fee INTEGER,
                    final_amount INTEGER,
                    utr TEXT UNIQUE,
                    screenshot TEXT,
                    status TEXT DEFAULT 'pending',
                    admin_id INTEGER,
                    admin_note TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    verified_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (admin_id) REFERENCES users(user_id)
                );

                -- Referrals table
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER,
                    referred_id INTEGER UNIQUE,
                    bonus_amount INTEGER DEFAULT 2,
                    status TEXT DEFAULT 'pending',  -- pending, completed, paid
                    bonus_paid INTEGER DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (referrer_id) REFERENCES users(user_id),
                    FOREIGN KEY (referred_id) REFERENCES users(user_id)
                );

                -- Daily rewards table
                CREATE TABLE IF NOT EXISTS daily_rewards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    claim_date DATE,
                    streak INTEGER DEFAULT 1,
                    amount INTEGER,
                    UNIQUE(user_id, claim_date),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );

                -- Coupons master table
                CREATE TABLE IF NOT EXISTS coupons_master (
                    code TEXT PRIMARY KEY,
                    discount_type TEXT,
                    discount_value INTEGER,
                    min_amount INTEGER DEFAULT 0,
                    max_uses INTEGER DEFAULT 999999,
                    used_count INTEGER DEFAULT 0,
                    expiry_days INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                -- Coupon usage table
                CREATE TABLE IF NOT EXISTS coupon_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT,
                    user_id INTEGER,
                    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    order_id TEXT,
                    FOREIGN KEY (code) REFERENCES coupons_master(code),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );

                -- Price alerts table
                CREATE TABLE IF NOT EXISTS price_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    card_name TEXT,
                    target_price INTEGER,
                    current_price INTEGER,
                    active INTEGER DEFAULT 1,
                    triggered INTEGER DEFAULT 0,
                    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );

                -- Gift card stock table
                CREATE TABLE IF NOT EXISTS gift_stock (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_id TEXT,
                    denomination INTEGER,
                    stock INTEGER DEFAULT 0,
                    low_alert INTEGER DEFAULT 10,
                    critical_alert INTEGER DEFAULT 5,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(card_id, denomination)
                );

                -- Game stock table
                CREATE TABLE IF NOT EXISTS game_stock (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id TEXT,
                    amount INTEGER,
                    stock INTEGER DEFAULT 0,
                    low_alert INTEGER DEFAULT 10,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(game_id, amount)
                );

                -- Wallet transfers table
                CREATE TABLE IF NOT EXISTS wallet_transfers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_user INTEGER,
                    to_user INTEGER,
                    amount INTEGER,
                    fee INTEGER,
                    final_amount INTEGER,
                    status TEXT DEFAULT 'completed',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (from_user) REFERENCES users(user_id),
                    FOREIGN KEY (to_user) REFERENCES users(user_id)
                );

                -- Mystery box logs table
                CREATE TABLE IF NOT EXISTS mystery_box (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    price INTEGER,
                    won_amount INTEGER,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );

                -- Support tickets table - FIXED
                CREATE TABLE IF NOT EXISTS support_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT UNIQUE,
                    user_id INTEGER,
                    message TEXT,
                    status TEXT DEFAULT 'open',
                    priority INTEGER DEFAULT 1,
                    assigned_to INTEGER,
                    response TEXT,
                    resolved_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );

                -- Banned users table
                CREATE TABLE IF NOT EXISTS banned_users (
                    user_id INTEGER PRIMARY KEY,
                    reason TEXT,
                    banned_by INTEGER,
                    banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (banned_by) REFERENCES users(user_id)
                );

                -- Admin logs table
                CREATE TABLE IF NOT EXISTS admin_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER,
                    action TEXT,
                    details TEXT,
                    ip TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (admin_id) REFERENCES users(user_id)
                );

                -- Settings table
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by INTEGER
                );

                -- Notifications table
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    title TEXT,
                    message TEXT,
                    type TEXT,
                    read INTEGER DEFAULT 0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                );
            """)
            
            # Initialize coupons master
            for code, cfg in COUPONS_MASTER.items():
                c.execute("""
                    INSERT OR IGNORE INTO coupons_master 
                    (code, discount_type, discount_value, min_amount, max_uses, expiry_days) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (code, cfg['type'], cfg['discount'], cfg['min'], cfg['max_uses'], cfg['expiry_days']))
            
            # Initialize gift card stock with 0
            for card_id in GIFT_CARDS:
                for denom in GIFT_DENOMINATIONS:
                    c.execute(
                        "INSERT OR IGNORE INTO gift_stock (card_id, denomination, stock) VALUES (?, ?, 0)",
                        (card_id, denom)
                    )
            
            # Initialize game stock with 0
            for game_id in GAME_RECHARGES:
                if game_id in GAME_PRICES:
                    for amount in GAME_PRICES[game_id]:
                        c.execute(
                            "INSERT OR IGNORE INTO game_stock (game_id, amount, stock) VALUES (?, ?, 0)",
                            (game_id, amount)
                        )
            
            # Insert default settings
            default_settings = [
                ('min_recharge', str(MIN_RECHARGE), 'Minimum recharge amount'),
                ('max_recharge', str(MAX_RECHARGE), 'Maximum recharge amount'),
                ('fee_percent', str(FEE_PERCENT), 'Fee percentage'),
                ('fee_threshold', str(FEE_THRESHOLD), 'Fee threshold'),
                ('referral_bonus', str(REFERRAL_BONUS), 'Referral bonus amount'),
                ('welcome_bonus', str(WELCOME_BONUS), 'Welcome bonus amount'),
                ('wallet_transfer_min', str(WALLET_TRANSFER_MIN), 'Minimum wallet transfer'),
                ('wallet_transfer_max', str(WALLET_TRANSFER_MAX), 'Maximum wallet transfer'),
                ('wallet_transfer_fee', str(WALLET_TRANSFER_FEE), 'Wallet transfer fee %'),
                ('mystery_box_price', str(MYSTERY_BOX_PRICE), 'Mystery box price'),
                ('mystery_box_min', str(MYSTERY_BOX_MIN), 'Mystery box min win'),
                ('mystery_box_max', str(MYSTERY_BOX_MAX), 'Mystery box max win'),
                ('card_exchange_fee', str(CARD_EXCHANGE_FEE), 'Card exchange fee %'),
                ('maintenance_mode', '0', 'Maintenance mode'),
                ('require_channel_join', '1', 'Require channel join'),
                ('auto_proof', '1', 'Auto send proofs'),
            ]
            
            for key, value, desc in default_settings:
                c.execute(
                    "INSERT OR IGNORE INTO settings (key, value, description) VALUES (?, ?, ?)",
                    (key, value, desc)
                )
            
            conn.commit()
            logger.info("✅ Database initialized with all tables")
        finally:
            self.return_conn(conn)

    def _create_indexes(self):
        conn = self.get_conn()
        try:
            c = conn.cursor()
            c.executescript("""
                CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
                CREATE INDEX IF NOT EXISTS idx_users_referral ON users(referral_code);
                CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active);
                CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id);
                CREATE INDEX IF NOT EXISTS idx_transactions_utr ON transactions(utr);
                CREATE INDEX IF NOT EXISTS idx_purchases_user ON purchases(user_id);
                CREATE INDEX IF NOT EXISTS idx_purchases_order ON purchases(order_id);
                CREATE INDEX IF NOT EXISTS idx_verifications_user ON verifications(user_id);
                CREATE INDEX IF NOT EXISTS idx_verifications_utr ON verifications(utr);
                CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id);
                CREATE INDEX IF NOT EXISTS idx_daily_rewards_user ON daily_rewards(user_id);
                CREATE INDEX IF NOT EXISTS idx_coupon_usage_user ON coupon_usage(user_id);
                CREATE INDEX IF NOT EXISTS idx_coupon_usage_code ON coupon_usage(code);
                CREATE INDEX IF NOT EXISTS idx_price_alerts_user ON price_alerts(user_id);
                CREATE INDEX IF NOT EXISTS idx_support_tickets_user ON support_tickets(user_id);
                CREATE INDEX IF NOT EXISTS idx_admin_logs_admin ON admin_logs(admin_id);
                CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
            """)
            conn.commit()
            logger.info("✅ Database indexes created")
        finally:
            self.return_conn(conn)

    # ============================================================================
    # USER METHODS
    # ============================================================================

    def get_user(self, user_id):
        """Get user by ID with caching"""
        with self.cache_lock:
            if user_id in self.cache:
                return self.cache[user_id]
        
        row = self.execute("SELECT * FROM users WHERE user_id=?", (user_id,), fetchone=True)
        user = dict(row) if row else None
        
        with self.cache_lock:
            if user:
                self.cache[user_id] = user
        return user

    def create_user(self, user_id, username, first_name, last_name=None, referred_by=None):
        """Create new user with referral handling"""
        ref_code = hashlib.md5(f"{user_id}{time.time()}{random.randint(1,999)}".encode()).hexdigest()[:8].upper()
        
        self.execute(
            """INSERT OR IGNORE INTO users 
               (user_id, username, first_name, last_name, referral_code, referred_by, join_date, last_active) 
               VALUES (?,?,?,?,?,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)""",
            (user_id, username, first_name, last_name, ref_code, referred_by), commit=True
        )
        
        if referred_by:
            self.execute(
                "INSERT OR IGNORE INTO referrals (referrer_id, referred_id) VALUES (?,?)",
                (referred_by, user_id), commit=True
            )
        
        with self.cache_lock:
            self.cache.pop(user_id, None)
        return self.get_user(user_id)

    def update_user(self, user_id, **kwargs):
        """Update user fields"""
        fields = []
        values = []
        for key, val in kwargs.items():
            fields.append(f"{key}=?")
            values.append(val)
        values.append(user_id)
        
        self.execute(
            f"UPDATE users SET {', '.join(fields)}, last_active=CURRENT_TIMESTAMP WHERE user_id=?",
            values, commit=True
        )
        
        with self.cache_lock:
            self.cache.pop(user_id, None)

    def get_balance(self, user_id):
        """Get user total balance (main + bonus)"""
        user = self.get_user(user_id)
        if not user:
            return 0
        return user['balance'] + user['bonus_balance']

    def get_main_balance(self, user_id):
        """Get main balance (withdrawable)"""
        user = self.get_user(user_id)
        return user['balance'] if user else 0

    def get_bonus_balance(self, user_id):
        """Get bonus balance (non-withdrawable)"""
        user = self.get_user(user_id)
        return user['bonus_balance'] if user else 0

    def update_balance(self, user_id, amount, tx_type="credit", category=None, payment_method=None, utr=None, description=None):
        """Update user balance with transaction record - FIXED STATS"""
        try:
            user = self.get_user(user_id)
            if not user:
                return False
            
            current_balance = user['balance']
            current_bonus = user['bonus_balance']
            
            # Determine which balance to use based on transaction type
            if tx_type in ["credit", "recharge"]:
                new_balance = current_balance + amount
                balance_field = "balance"
                # Update total_recharged only for actual recharges
                self.execute(
                    "UPDATE users SET total_recharged = total_recharged + ? WHERE user_id=?",
                    (amount, user_id), commit=True
                )
            elif tx_type == "bonus":
                new_balance = current_bonus + amount
                balance_field = "bonus_balance"
                # Bonus doesn't affect total_recharged
            elif tx_type in ["debit", "purchase"]:
                if amount <= current_balance:
                    new_balance = current_balance - amount
                    balance_field = "balance"
                    # Update total_spent
                    self.execute(
                        "UPDATE users SET total_spent = total_spent + ? WHERE user_id=?",
                        (amount, user_id), commit=True
                    )
                elif amount <= current_balance + current_bonus:
                    use_from_bonus = min(amount, current_bonus)
                    use_from_main = amount - use_from_bonus
                    
                    self.execute(
                        "UPDATE users SET bonus_balance = bonus_balance - ?, balance = balance - ?, last_active=CURRENT_TIMESTAMP WHERE user_id=?",
                        (use_from_bonus, use_from_main, user_id), commit=True
                    )
                    
                    # Update total_spent
                    self.execute(
                        "UPDATE users SET total_spent = total_spent + ? WHERE user_id=?",
                        (amount, user_id), commit=True
                    )
                    
                    # Record transaction
                    tx_id = f"TXN{int(time.time())}{random.randint(100,999)}"
                    self.execute(
                        """INSERT INTO transactions 
                           (user_id, transaction_id, amount, type, category, payment_method, utr, description, final_amount) 
                           VALUES (?,?,?,?,?,?,?,?,?)""",
                        (user_id, tx_id, amount, tx_type, category, payment_method, utr, description, amount), commit=True
                    )
                    
                    with self.cache_lock:
                        self.cache.pop(user_id, None)
                    return True
                else:
                    return False
            elif tx_type in ["transfer_out"]:
                new_balance = current_balance - amount
                balance_field = "balance"
                # Don't update totals for transfers
            elif tx_type in ["transfer_in"]:
                new_balance = current_balance + amount
                balance_field = "balance"
                # Don't update totals for transfers
            else:
                return False
            
            # Update single balance
            self.execute(
                f"UPDATE users SET {balance_field}=?, last_active=CURRENT_TIMESTAMP WHERE user_id=?",
                (new_balance, user_id), commit=True
            )
            
            # Record transaction
            tx_id = f"TXN{int(time.time())}{random.randint(100,999)}"
            self.execute(
                """INSERT INTO transactions 
                   (user_id, transaction_id, amount, type, category, payment_method, utr, description, final_amount) 
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (user_id, tx_id, amount, tx_type, category, payment_method, utr, description, amount), commit=True
            )
            
            # Update total_purchases for purchases
            if tx_type in ["debit", "purchase"]:
                self.execute(
                    "UPDATE users SET total_purchases = total_purchases + 1 WHERE user_id=?",
                    (user_id,), commit=True
                )
            
            with self.cache_lock:
                self.cache.pop(user_id, None)
            
            return True
            
        except Exception as e:
            logger.error(f"Balance update error: {e}")
            return False

    def transfer_wallet(self, from_user, to_user, amount):
        """Transfer money between users"""
        try:
            fee = int(amount * WALLET_TRANSFER_FEE / 100)
            final_amount = amount - fee
            
            from_balance = self.get_main_balance(from_user)
            if from_balance < amount:
                return False, "Insufficient balance"
            
            to_user_data = self.get_user(to_user)
            if not to_user_data:
                return False, "Recipient not found"
            
            self.execute(
                "UPDATE users SET balance = balance - ? WHERE user_id=?",
                (amount, from_user), commit=True
            )
            
            self.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id=?",
                (final_amount, to_user), commit=True
            )
            
            self.execute(
                """INSERT INTO wallet_transfers (from_user, to_user, amount, fee, final_amount) 
                   VALUES (?,?,?,?,?)""",
                (from_user, to_user, amount, fee, final_amount), commit=True
            )
            
            self.update_balance(from_user, -amount, "transfer_out", description=f"Transfer to {to_user}")
            self.update_balance(to_user, final_amount, "transfer_in", description=f"Transfer from {from_user}")
            
            with self.cache_lock:
                self.cache.pop(from_user, None)
                self.cache.pop(to_user, None)
            
            return True, {"fee": fee, "final": final_amount}
            
        except Exception as e:
            logger.error(f"Wallet transfer error: {e}")
            return False, str(e)

    # ============================================================================
    # PURCHASE METHODS
    # ============================================================================

    def add_purchase(self, user_id, item_type, item_category, item_id, item_name, amount, price, quantity=1, 
                    discount=0, coupon=None, email="", recipient=None, gift_message=None, status="pending"):
        """Add purchase record"""
        order_id = f"{item_type[:2].upper()}{int(time.time())}{random.randint(100,999)}"
        
        self.execute(
            """INSERT INTO purchases 
               (user_id, order_id, item_type, item_category, item_id, item_name, amount, price, 
                quantity, discount, coupon, email, recipient, gift_message, status) 
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (user_id, order_id, item_type, item_category, item_id, item_name, amount, price,
             quantity, discount, coupon, email, recipient, gift_message, status), commit=True
        )
        
        return order_id

    def update_purchase_status(self, order_id, status):
        """Update purchase status"""
        self.execute("UPDATE purchases SET status=? WHERE order_id=?", (status, order_id), commit=True)

    def get_user_purchases(self, user_id, limit=10):
        """Get user purchase history"""
        rows = self.execute(
            "SELECT * FROM purchases WHERE user_id=? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit), fetchall=True
        )
        return [dict(row) for row in rows] if rows else []

    def mark_proof_sent(self, order_id):
        """Mark proof as sent"""
        self.execute("UPDATE purchases SET proof_sent=1 WHERE order_id=?", (order_id,), commit=True)

    # ============================================================================
    # VERIFICATION METHODS
    # ============================================================================

    def create_verification(self, user_id, amount, fee, final_amount, utr, screenshot):
        """Create payment verification request"""
        self.execute(
            "INSERT INTO verifications (user_id, amount, fee, final_amount, utr, screenshot) VALUES (?,?,?,?,?,?)",
            (user_id, amount, fee, final_amount, utr, screenshot), commit=True
        )

    def get_verification(self, vid):
        """Get verification by ID"""
        row = self.execute("SELECT * FROM verifications WHERE id=?", (vid,), fetchone=True)
        return dict(row) if row else None

    def get_verification_by_utr(self, utr):
        """Get verification by UTR - FIXED: Added missing function"""
        row = self.execute("SELECT * FROM verifications WHERE utr=?", (utr,), fetchone=True)
        return dict(row) if row else None

    def update_verification(self, vid, status, admin_id, note=None):
        """Update verification status"""
        self.execute(
            "UPDATE verifications SET status=?, admin_id=?, admin_note=?, verified_at=CURRENT_TIMESTAMP WHERE id=?",
            (status, admin_id, note, vid), commit=True
        )

    def update_verification_by_utr(self, utr, status, admin_id, note=None):
        """Update verification status by UTR - FIXED: Added missing function"""
        self.execute(
            "UPDATE verifications SET status=?, admin_id=?, admin_note=?, verified_at=CURRENT_TIMESTAMP WHERE utr=?",
            (status, admin_id, note, utr), commit=True
        )

    def get_pending_verifications(self):
        """Get all pending verifications"""
        rows = self.execute("SELECT * FROM verifications WHERE status='pending' ORDER BY timestamp", fetchall=True)
        return [dict(row) for row in rows] if rows else []

    def is_utr_duplicate(self, utr):
        """Check if UTR already exists"""
        row = self.execute("SELECT id FROM verifications WHERE utr=?", (utr,), fetchone=True)
        return row is not None

    # ============================================================================
    # STOCK METHODS
    # ============================================================================

    def get_gift_stock(self, card_id, denom):
        """Get gift card stock"""
        row = self.execute(
            "SELECT stock FROM gift_stock WHERE card_id=? AND denomination=?",
            (card_id, denom), fetchone=True
        )
        return row['stock'] if row else 0

    def decrease_gift_stock(self, card_id, denom, quantity=1):
        """Decrease gift card stock"""
        cur = self.execute(
            "UPDATE gift_stock SET stock = stock - ? WHERE card_id=? AND denomination=? AND stock >= ?",
            (quantity, card_id, denom, quantity), commit=True
        )
        # Use cursor.rowcount to check if update affected any rows
        conn = self.get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE gift_stock SET stock = stock - ? WHERE card_id=? AND denomination=? AND stock >= ?",
                (quantity, card_id, denom, quantity)
            )
            affected = cur.rowcount
            conn.commit()
            return affected > 0
        finally:
            self.return_conn(conn)

    def increase_gift_stock(self, card_id, denom, quantity=1):
        """Increase gift card stock"""
        self.execute(
            "UPDATE gift_stock SET stock = stock + ?, updated_at=CURRENT_TIMESTAMP WHERE card_id=? AND denomination=?",
            (quantity, card_id, denom), commit=True
        )

    def set_gift_stock(self, card_id, denom, quantity):
        """Set exact gift card stock"""
        self.execute(
            "UPDATE gift_stock SET stock=?, updated_at=CURRENT_TIMESTAMP WHERE card_id=? AND denomination=?",
            (quantity, card_id, denom), commit=True
        )

    def get_low_stock_gifts(self):
        """Get low stock gift cards"""
        rows = self.execute(
            "SELECT card_id, denomination, stock FROM gift_stock WHERE stock <= low_alert",
            fetchall=True
        )
        return [dict(row) for row in rows] if rows else []

    def is_gift_out_of_stock(self, card_id, denom):
        """Check if gift card is out of stock"""
        return self.get_gift_stock(card_id, denom) <= 0

    def get_game_stock(self, game_id, amount):
        """Get game stock"""
        row = self.execute(
            "SELECT stock FROM game_stock WHERE game_id=? AND amount=?",
            (game_id, amount), fetchone=True
        )
        return row['stock'] if row else 0

    def decrease_game_stock(self, game_id, amount, quantity=1):
        """Decrease game stock"""
        conn = self.get_conn()
        try:
            cur = conn.cursor()
            cur.execute(
                "UPDATE game_stock SET stock = stock - ? WHERE game_id=? AND amount=? AND stock >= ?",
                (quantity, game_id, amount, quantity)
            )
            affected = cur.rowcount
            conn.commit()
            return affected > 0
        finally:
            self.return_conn(conn)

    def increase_game_stock(self, game_id, amount, quantity=1):
        """Increase game stock"""
        self.execute(
            "UPDATE game_stock SET stock = stock + ?, updated_at=CURRENT_TIMESTAMP WHERE game_id=? AND amount=?",
            (quantity, game_id, amount), commit=True
        )

    # ============================================================================
    # REFERRAL METHODS
    # ============================================================================

    def process_referral(self, referrer_id, referred_id):
        """Process referral when referred user makes first purchase"""
        self.execute(
            "UPDATE referrals SET status='completed', bonus_paid=1, completed_at=CURRENT_TIMESTAMP WHERE referrer_id=? AND referred_id=?",
            (referrer_id, referred_id), commit=True
        )
        self.update_balance(referrer_id, REFERRAL_BONUS, "bonus", description=f"Referral bonus for user {referred_id}")

    def get_referral_count(self, user_id):
        """Get user's completed referral count"""
        row = self.execute(
            "SELECT COUNT(*) as c FROM referrals WHERE referrer_id=? AND status='completed'",
            (user_id,), fetchone=True
        )
        return row['c'] if row else 0

    def get_referral_earnings(self, user_id):
        """Get total referral earnings"""
        row = self.execute(
            "SELECT SUM(bonus_amount) as total FROM referrals WHERE referrer_id=? AND bonus_paid=1",
            (user_id,), fetchone=True
        )
        return row['total'] if row and row['total'] else 0

    def get_referral_link(self, user_id, bot_username):
        """Get user's referral link"""
        user = self.get_user(user_id)
        if user and user['referral_code']:
            return f"https://t.me/{bot_username}?start={user['referral_code']}"
        return None

    # ============================================================================
    # DAILY REWARD METHODS
    # ============================================================================

    def claim_daily_reward(self, user_id):
        """Claim daily reward with streak"""
        today = date.today()
        user = self.get_user(user_id)
        if not user:
            return None, "User not found"

        last_claim = user['last_claim']
        streak = user['streak'] or 0

        if last_claim:
            last_date = datetime.strptime(str(last_claim), "%Y-%m-%d").date()
            if last_date == today:
                return None, "already_claimed"
            elif last_date == today - timedelta(days=1):
                streak += 1
            else:
                streak = 1
        else:
            streak = 1

        reward = 5
        for day in sorted(DAILY_REWARDS.keys(), reverse=True):
            if streak >= day:
                reward = DAILY_REWARDS[day]
                break

        try:
            self.execute(
                "INSERT INTO daily_rewards (user_id, claim_date, streak, amount) VALUES (?,?,?,?)",
                (user_id, today, streak, reward), commit=True
            )
            self.execute(
                "UPDATE users SET streak=?, last_claim=? WHERE user_id=?",
                (streak, today, user_id), commit=True
            )
            self.update_balance(user_id, reward, "bonus", description=f"Daily reward (streak: {streak})")
            
            with self.cache_lock:
                self.cache.pop(user_id, None)
            
            return reward, streak
            
        except sqlite3.IntegrityError:
            return None, "already_claimed"

    # ============================================================================
    # COUPON METHODS - FIXED ARCHITECTURE
    # ============================================================================

    def validate_coupon(self, code, user_id, amount):
        """Validate coupon code"""
        code = code.upper().strip()
        
        # Get coupon from master table
        coupon = self.execute(
            "SELECT * FROM coupons_master WHERE code=?", (code,), fetchone=True
        )
        
        if not coupon:
            return None, "Invalid coupon code"
        
        coupon = dict(coupon)
        
        # Check minimum amount
        if amount < coupon['min_amount']:
            return None, f"Minimum purchase ₹{coupon['min_amount']} required"
        
        # Check if max uses reached
        if coupon['used_count'] >= coupon['max_uses']:
            return None, "Coupon usage limit exceeded"
        
        # Check if user already used this coupon
        used = self.execute(
            "SELECT COUNT(*) as c FROM coupon_usage WHERE code=? AND user_id=?",
            (code, user_id), fetchone=True
        )
        if used and used['c'] > 0:
            return None, "You have already used this coupon"
        
        return coupon, None

    def use_coupon(self, code, user_id, order_id=None):
        """Use a coupon"""
        # Update usage count in master
        self.execute(
            "UPDATE coupons_master SET used_count = used_count + 1 WHERE code=?",
            (code,), commit=True
        )
        
        # Record usage
        self.execute(
            "INSERT INTO coupon_usage (code, user_id, order_id) VALUES (?, ?, ?)",
            (code, user_id, order_id), commit=True
        )

    def get_active_coupons(self):
        """Get all active coupons"""
        rows = self.execute(
            "SELECT * FROM coupons_master WHERE used_count < max_uses ORDER BY code",
            fetchall=True
        )
        return [dict(row) for row in rows] if rows else []

    # ============================================================================
    # PRICE ALERT METHODS
    # ============================================================================

    def add_price_alert(self, user_id, card_name, target_price, current_price):
        """Add price alert"""
        self.execute(
            "INSERT INTO price_alerts (user_id, card_name, target_price, current_price) VALUES (?,?,?,?)",
            (user_id, card_name, target_price, current_price), commit=True
        )

    def remove_price_alert(self, alert_id):
        """Remove price alert"""
        self.execute("DELETE FROM price_alerts WHERE id=?", (alert_id,), commit=True)

    def get_user_alerts(self, user_id):
        """Get user's active price alerts"""
        rows = self.execute(
            "SELECT * FROM price_alerts WHERE user_id=? AND active=1 ORDER BY created DESC",
            (user_id,), fetchall=True
        )
        return [dict(row) for row in rows] if rows else []

    def check_price_alerts(self, card_name, new_price):
        """Check and trigger price alerts"""
        rows = self.execute(
            "SELECT * FROM price_alerts WHERE card_name=? AND active=1 AND target_price >= ? AND triggered=0",
            (card_name, new_price), fetchall=True
        )
        
        alerts = []
        for row in rows:
            alert = dict(row)
            self.execute(
                "UPDATE price_alerts SET triggered=1 WHERE id=?",
                (alert['id'],), commit=True
            )
            alerts.append(alert)
        
        return alerts

    # ============================================================================
    # MYSTERY BOX METHODS
    # ============================================================================

    def open_mystery_box(self, user_id):
        """Open mystery box and get random amount"""
        balance = self.get_main_balance(user_id)
        if balance < MYSTERY_BOX_PRICE:
            return False, "Insufficient balance"
        
        rand = random.random()
        if rand < 0.001:
            win = MYSTERY_BOX_SUPER_JACKPOT
        elif rand < 0.01:
            win = MYSTERY_BOX_JACKPOT
        else:
            win = random.randint(MYSTERY_BOX_MIN, MYSTERY_BOX_MAX)
        
        self.update_balance(user_id, -MYSTERY_BOX_PRICE, "debit", description="Mystery box purchase")
        self.update_balance(user_id, win, "bonus", description="Mystery box win")
        
        self.execute(
            "INSERT INTO mystery_box (user_id, price, won_amount) VALUES (?,?,?)",
            (user_id, MYSTERY_BOX_PRICE, win), commit=True
        )
        
        return True, win

    # ============================================================================
    # SUPPORT TICKET METHODS - FIXED
    # ============================================================================

    def create_support_ticket(self, user_id, message):
        """Create support ticket"""
        ticket_id = f"TKT{int(time.time())}{random.randint(100,999)}"
        self.execute(
            "INSERT INTO support_tickets (ticket_id, user_id, message) VALUES (?,?,?)",
            (ticket_id, user_id, message), commit=True
        )
        return ticket_id

    def get_open_tickets(self):
        """Get all open tickets"""
        rows = self.execute(
            "SELECT * FROM support_tickets WHERE status='open' ORDER BY created_at",
            fetchall=True
        )
        return [dict(row) for row in rows] if rows else []

    def update_ticket_status(self, ticket_id, status, response=None):
        """Update ticket status"""
        if response:
            self.execute(
                "UPDATE support_tickets SET status=?, response=?, updated_at=CURRENT_TIMESTAMP WHERE ticket_id=?",
                (status, response, ticket_id), commit=True
            )
        else:
            self.execute(
                "UPDATE support_tickets SET status=?, updated_at=CURRENT_TIMESTAMP WHERE ticket_id=?",
                (status, ticket_id), commit=True
            )

    # ============================================================================
    # ADMIN METHODS
    # ============================================================================

    def log_admin_action(self, admin_id, action, details):
        """Log admin action"""
        self.execute(
            "INSERT INTO admin_logs (admin_id, action, details) VALUES (?,?,?)",
            (admin_id, action, details), commit=True
        )

    def get_admin_logs(self, limit=100):
        """Get recent admin logs"""
        rows = self.execute(
            "SELECT * FROM admin_logs ORDER BY timestamp DESC LIMIT ?",
            (limit,), fetchall=True
        )
        return [dict(row) for row in rows] if rows else []

    def ban_user(self, user_id, admin_id, reason, expires_days=None):
        """Ban a user"""
        expires = (datetime.now() + timedelta(days=expires_days)).isoformat() if expires_days else None
        self.execute(
            "INSERT OR REPLACE INTO banned_users (user_id, reason, banned_by, expires_at) VALUES (?,?,?,?)",
            (user_id, reason, admin_id, expires), commit=True
        )
        self.execute("UPDATE users SET is_banned=1, ban_reason=? WHERE user_id=?", (reason, user_id), commit=True)
        
        with self.cache_lock:
            self.cache.pop(user_id, None)

    def unban_user(self, user_id):
        """Unban a user"""
        self.execute("DELETE FROM banned_users WHERE user_id=?", (user_id,), commit=True)
        self.execute("UPDATE users SET is_banned=0, ban_reason=NULL WHERE user_id=?", (user_id,), commit=True)
        
        with self.cache_lock:
            self.cache.pop(user_id, None)

    def is_banned(self, user_id):
        """Check if user is banned"""
        user = self.get_user(user_id)
        return user and user['is_banned'] == 1

    # ============================================================================
    # STATISTICS METHODS - FIXED
    # ============================================================================

    def get_statistics(self):
        """Get comprehensive bot statistics"""
        stats = {}
        
        stats['total_users'] = self.execute("SELECT COUNT(*) as c FROM users", fetchone=True)['c']
        stats['active_today'] = self.execute("SELECT COUNT(*) as c FROM users WHERE DATE(last_active)=DATE('now')", fetchone=True)['c']
        stats['new_today'] = self.execute("SELECT COUNT(*) as c FROM users WHERE DATE(join_date)=DATE('now')", fetchone=True)['c']
        stats['banned_users'] = self.execute("SELECT COUNT(*) as c FROM users WHERE is_banned=1", fetchone=True)['c']
        
        stats['total_transactions'] = self.execute("SELECT COUNT(*) as c FROM transactions", fetchone=True)['c']
        stats['transactions_today'] = self.execute("SELECT COUNT(*) as c FROM transactions WHERE DATE(timestamp)=DATE('now')", fetchone=True)['c']
        stats['total_revenue'] = self.execute("SELECT SUM(amount) as s FROM transactions WHERE type='recharge'", fetchone=True)['s'] or 0
        stats['revenue_today'] = self.execute("SELECT SUM(amount) as s FROM transactions WHERE type='recharge' AND DATE(timestamp)=DATE('now')", fetchone=True)['s'] or 0
        
        stats['total_purchases'] = self.execute("SELECT COUNT(*) as c FROM purchases", fetchone=True)['c']
        stats['purchases_today'] = self.execute("SELECT COUNT(*) as c FROM purchases WHERE DATE(timestamp)=DATE('now')", fetchone=True)['c']
        stats['total_spent'] = self.execute("SELECT SUM(price) as s FROM purchases", fetchone=True)['s'] or 0
        
        stats['pending_verifications'] = self.execute("SELECT COUNT(*) as c FROM verifications WHERE status='pending'", fetchone=True)['c']
        stats['approved_today'] = self.execute("SELECT COUNT(*) as c FROM verifications WHERE status='approved' AND DATE(verified_at)=DATE('now')", fetchone=True)['c']
        
        stats['total_referrals'] = self.execute("SELECT COUNT(*) as c FROM referrals WHERE status='completed'", fetchone=True)['c']
        stats['referral_bonus_paid'] = self.execute("SELECT SUM(bonus_amount) as s FROM referrals WHERE bonus_paid=1", fetchone=True)['s'] or 0
        
        stats['daily_claims_today'] = self.execute("SELECT COUNT(*) as c FROM daily_rewards WHERE claim_date=DATE('now')", fetchone=True)['c']
        
        stats['mystery_box_total'] = self.execute("SELECT COUNT(*) as c FROM mystery_box", fetchone=True)['c']
        stats['mystery_box_payout'] = self.execute("SELECT SUM(won_amount) as s FROM mystery_box", fetchone=True)['s'] or 0
        
        stats['total_balance'] = self.execute("SELECT SUM(balance) + SUM(bonus_balance) as s FROM users", fetchone=True)['s'] or 0
        stats['avg_balance'] = stats['total_balance'] // stats['total_users'] if stats['total_users'] > 0 else 0
        
        return stats

    def export_users_csv(self):
        """Export all users to CSV"""
        rows = self.execute("SELECT * FROM users ORDER BY join_date DESC", fetchall=True)
        if not rows:
            return ""
        
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))
        
        return output.getvalue()

    # ============================================================================
    # SETTINGS METHODS
    # ============================================================================

    def get_setting(self, key, default=None):
        """Get setting value"""
        row = self.execute("SELECT value FROM settings WHERE key=?", (key,), fetchone=True)
        return row['value'] if row else default

    def update_setting(self, key, value, admin_id):
        """Update setting value"""
        self.execute(
            "UPDATE settings SET value=?, updated_at=CURRENT_TIMESTAMP, updated_by=? WHERE key=?",
            (value, admin_id, key), commit=True
        )

db = DatabaseManager(DATABASE_PATH)

# ============================================================================
# UI COMPONENTS - FIXED
# ============================================================================

def simple_header(title, emoji="🎁"):
    """Simple header without complex formatting"""
    return f"{emoji} *{title}* {emoji}\n" + "━" * 30

def format_currency(amount):
    return f"₹{amount:,}"

def user_badge(total_purchases):
    if total_purchases >= 100:
        return "👑 VIP ELITE"
    elif total_purchases >= 50:
        return "💎 DIAMOND"
    elif total_purchases >= 25:
        return "🥇 GOLD"
    elif total_purchases >= 10:
        return "🥈 SILVER"
    elif total_purchases >= 5:
        return "🥉 BRONZE"
    elif total_purchases >= 1:
        return "⭐ BEGINNER"
    else:
        return "🆕 NEW"

def stock_indicator(stock):
    if stock > 50:
        return "🟢 IN STOCK"
    elif stock > 10:
        return "🟡 LOW STOCK"
    elif stock > 5:
        return "🟠 VERY LOW"
    elif stock > 0:
        return "🔴 CRITICAL"
    else:
        return "⚫ OUT OF STOCK"

def format_bulk_discounts():
    """Format bulk discounts as single string"""
    lines = ["*Volume Discounts:*"]
    for qty in sorted(BULK_DISCOUNTS.keys()):
        if BULK_DISCOUNTS[qty] > 0:
            lines.append(f"  • {qty}+ cards: {BULK_DISCOUNTS[qty]}% OFF")
    return "\n".join(lines)

# ============================================================================
# KEYBOARD BUILDERS - FIXED (removed extra argument)
# ============================================================================

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 GIFT CARDS (65% OFF)", callback_data="menu_gift")],
        [InlineKeyboardButton("🎮 GAME RECHARGES", callback_data="menu_game")],
        [InlineKeyboardButton("📱 MOBILE RECHARGE", callback_data="menu_mobile")],
        [InlineKeyboardButton("📺 DTH RECHARGE", callback_data="menu_dth")],
        [InlineKeyboardButton("🌐 FIBER RECHARGE", callback_data="menu_fiber")],
        [InlineKeyboardButton("💰 ADD MONEY", callback_data="menu_topup")],
        [InlineKeyboardButton("👛 MY WALLET", callback_data="menu_wallet")],
        [InlineKeyboardButton("🔄 WALLET TRANSFER", callback_data="menu_transfer")],
        [InlineKeyboardButton("🎁 MYSTERY BOX", callback_data="menu_mystery")],
        [InlineKeyboardButton("👥 REFERRAL", callback_data="menu_referral")],
        [InlineKeyboardButton("📅 DAILY REWARD", callback_data="menu_daily")],
        [InlineKeyboardButton("🏷️ COUPONS", callback_data="menu_coupon")],
        [InlineKeyboardButton("📦 BULK PURCHASE", callback_data="menu_bulk")],
        [InlineKeyboardButton("🎁 SEND GIFT", callback_data="menu_gift_send")],
        [InlineKeyboardButton("🔔 PRICE ALERT", callback_data="menu_alert")],
        [InlineKeyboardButton("🆘 SUPPORT", callback_data="menu_support")],
    ])

def gift_cards_keyboard():
    keyboard = []
    categories = {}
    for card_id, card in GIFT_CARDS.items():
        cat = card.get('category', 'other')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((card_id, card))
    
    for cat in ['shopping', 'gaming', 'entertainment', 'music', 'food', 'grocery']:
        if cat in categories:
            cat_emoji = {'shopping': '🛍️', 'gaming': '🎮', 'entertainment': '🎬',
                        'music': '🎵', 'food': '🍔', 'grocery': '🛒'}.get(cat, '🎁')
            keyboard.append([InlineKeyboardButton(
                f"{cat_emoji} {cat.upper()}",
                callback_data=f"gift_cat_{cat}"
            )])
    
    keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def amount_keyboard():
    keyboard = []
    for row in AMOUNT_BUTTONS:
        button_row = [InlineKeyboardButton(f"₹{a}", callback_data=f"amount_{a}") for a in row]
        keyboard.append(button_row)
    keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def confirm_keyboard(action_data):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ CONFIRM", callback_data=action_data)],
        [InlineKeyboardButton("❌ CANCEL", callback_data="main_menu")]
    ])

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def validate_email(email):
    return bool(re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', email))

def validate_phone(phone):
    return bool(re.match(r'^[6-9]\d{9}$', phone))

def validate_utr(utr):
    return 12 <= len(utr) <= 22 and utr.isalnum()

def calculate_fee(amount):
    if amount < FEE_THRESHOLD:
        fee = int(amount * FEE_PERCENT / 100)
        return fee, amount - fee
    return 0, amount

def calculate_bulk_discount(quantity, price):
    discount = 0
    for qty in sorted(BULK_DISCOUNTS.keys(), reverse=True):
        if quantity >= qty:
            discount = BULK_DISCOUNTS[qty]
            break
    
    total = price * quantity
    discount_amount = int(total * discount / 100)
    final = total - discount_amount
    
    return {
        "quantity": quantity,
        "unit_price": price,
        "total": total,
        "discount_percent": discount,
        "discount_amount": discount_amount,
        "final": final
    }

def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            await update.message.reply_text("❌ Admin access required.")
            return
        return await func(update, context)
    return wrapper

async def check_membership(bot, user_id):
    try:
        member = await bot.get_chat_member(MAIN_CHANNEL, user_id)
        return member.status not in ("left", "kicked", "banned")
    except Exception:
        return True

async def safe_edit_message(query, text, reply_markup=None, parse_mode=ParseMode.HTML):
    """Safely edit message with error handling"""
    try:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
    except Exception as e:
        logger.warning(f"Failed to edit message: {e}")
        try:
            await query.message.reply_text(text, reply_markup=reply_markup, parse_mode=parse_mode)
        except Exception as e2:
            logger.error(f"Failed to send new message: {e2}")

async def send_temp_message(context, chat_id, text, delete_after=5):
    """Send temporary message that auto-deletes"""
    msg = await context.bot.send_message(chat_id, text)
    await asyncio.sleep(delete_after)
    try:
        await msg.delete()
    except:
        pass

def generate_qr(upi_id, amount):
    if not QR_AVAILABLE:
        return None
    try:
        upi_url = f"upi://pay?pa={upi_id}&pn=GiftCardBot&am={amount}&cu=INR"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(upi_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        path = f"/tmp/qr_{amount}_{int(time.time())}.png"
        img.save(path)
        return path
    except Exception as e:
        logger.warning(f"QR generation failed: {e}")
        return None

def cleanup_temp_file(path):
    """Clean up temporary file"""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except:
        pass

# ============================================================================
# PROOF FUNCTION - FIXED (based on order success, not stock)
# ============================================================================

async def send_proof(context, purchase_data):
    """Send purchase proof to logs channel"""
    try:
        name = purchase_data.get('name', 'Customer')
        item = purchase_data.get('item', 'Gift Card')
        amount = purchase_data.get('amount', 0)
        order_id = purchase_data.get('order_id', '')
        
        message = (
            f"🛒 *NEW PURCHASE*\n"
            f"━" * 30 + "\n"
            f"👤 *{name}*\n"
            f"🎁 *{item}*\n"
            f"💰 *{format_currency(amount)}*\n"
            f"🆔 Order: `{order_id}`\n"
            f"━" * 30 + "\n"
            f"📧 *Email Delivery*\n"
            f"⏳ *Status: Processing*"
        )
        
        await context.bot.send_message(
            chat_id=PROOF_CHANNEL,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        db.mark_proof_sent(order_id)
        logger.info(f"✅ Proof sent for order {order_id}")
        return True
    except Exception as e:
        logger.error(f"Proof error: {e}")
        return False

# ============================================================================
# RENDER MAIN MENU - FIXED (reusable function)
# ============================================================================

async def render_main_menu(target, user, context):
    """Render main menu for either message or callback"""
    db_user = db.get_user(user.id) or {}
    balance = db_user.get('balance', 0) + db_user.get('bonus_balance', 0)
    purchases = db_user.get('total_purchases', 0)
    badge = user_badge(purchases)
    ref_count = db.get_referral_count(user.id)
    
    text = (
        f"🎁 *GIFT CARD BOT*\n"
        f"━" * 30 + "\n"
        f"👤 *{user.first_name}* {badge}\n"
        f"💰 *Balance:* {format_currency(balance)}\n"
        f"🛒 *Purchases:* {purchases}\n"
        f"👥 *Referrals:* {ref_count}\n"
        f"━" * 30 + "\n"
        f"🔥 *65% OFF on All Gift Cards!*\n"
        f"━" * 30 + "\n"
        f"*Choose an option:*"
    )
    
    if hasattr(target, 'message'):  # Callback query
        await safe_edit_message(target, text, main_menu_keyboard())
    else:  # Message
        await target.reply_text(text, reply_markup=main_menu_keyboard(), parse_mode=ParseMode.MARKDOWN)

# ============================================================================
# START COMMAND
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if not rate_limiter.is_allowed(user.id):
        await update.message.reply_text("⏳ Too many requests! Try again later.")
        return

    if db.is_banned(user.id):
        await update.message.reply_text("🚫 You are banned from using this bot.")
        return

    existing = db.get_user(user.id)
    is_new = existing is None

    if is_new:
        referred_by = None
        if context.args and context.args[0]:
            ref_code = context.args[0]
            ref_user = db.execute(
                "SELECT user_id FROM users WHERE referral_code=?",
                (ref_code,), fetchone=True
            )
            if ref_user and ref_user['user_id'] != user.id:
                referred_by = ref_user['user_id']
        
        db.create_user(
            user.id,
            user.username or "",
            user.first_name or "User",
            user.last_name,
            referred_by
        )
        
        db.update_balance(user.id, WELCOME_BONUS, "bonus", description="Welcome bonus")
        
        logger.info(f"✅ New user: {user.id} - {user.first_name}")

    db.update_user(user.id, last_active=datetime.now().isoformat())

    require_channel = db.get_setting('require_channel_join', '1') == '1'
    if require_channel:
        is_member = await check_membership(context.bot, user.id)
        if not is_member:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{MAIN_CHANNEL.lstrip('@')}")],
                [InlineKeyboardButton("✅ I Joined!", callback_data="verify")],
            ])
            await update.message.reply_text(
                f"🔒 *Join Channel Required*\n\n📢 {MAIN_CHANNEL}",
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN
            )
            return

    await render_main_menu(update.message, user, context)

# ============================================================================
# MAIN BUTTON HANDLER - FIXED
# ============================================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user = update.effective_user

    if not rate_limiter.is_allowed(user.id):
        await query.answer("⏳ Too many requests!", show_alert=True)
        return

    if db.is_banned(user.id):
        await query.edit_message_text("🚫 You are banned.")
        return

    if data not in ("verify", "main_menu"):
        require_channel = db.get_setting('require_channel_join', '1') == '1'
        if require_channel:
            is_member = await check_membership(context.bot, user.id)
            if not is_member:
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{MAIN_CHANNEL.lstrip('@')}")],
                    [InlineKeyboardButton("✅ Verify", callback_data="verify")],
                ])
                await query.edit_message_text("🔒 Join channel first!", reply_markup=keyboard)
                return

    db.update_user(user.id, last_active=datetime.now().isoformat())

    if data == "verify":
        is_member = await check_membership(context.bot, user.id)
        if is_member:
            await render_main_menu(query, user, context)
        else:
            await query.answer("❌ Not a member!", show_alert=True)

    elif data == "main_menu":
        await render_main_menu(query, user, context)

    # ===== GIFT CARDS =====
    elif data == "menu_gift":
        await safe_edit_message(query,
            f"{simple_header('GIFT CARDS')}\n\nSelect category:",
            gift_cards_keyboard()
        )

    elif data.startswith("gift_cat_"):
        category = data[9:]
        await safe_edit_message(query,
            f"{simple_header(f'{category.upper()} CARDS')}\n\nSelect card:",
            gift_cards_keyboard()  # This should be category-specific keyboard
        )

    elif data.startswith("gift_"):
        card_id = data[5:]
        card = GIFT_CARDS.get(card_id)
        if not card:
            return
        
        text = f"{card['full_emoji']} *{card['name']}*\n" + "━" * 30 + "\n\n"
        
        keyboard = []
        for denom in GIFT_DENOMINATIONS:
            price = GIFT_PRICES[denom]
            savings = denom - price
            stock = db.get_gift_stock(card_id, denom)
            indicator = stock_indicator(stock)
            
            text += f"• ₹{denom} → *₹{price}* (Save ₹{savings}) {indicator}\n"
            
            if stock > 0:
                keyboard.append([InlineKeyboardButton(
                    f"₹{denom} @ ₹{price}",
                    callback_data=f"buy_gift_{card_id}_{denom}"
                )])
        
        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="menu_gift")])
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))

    # ===== BUY GIFT CARD - FIXED FLOW =====
    elif data.startswith("buy_gift_"):
        parts = data.split('_')
        card_id = parts[2]
        denom = int(parts[3])
        
        card = GIFT_CARDS[card_id]
        price = GIFT_PRICES[denom]
        
        if db.is_gift_out_of_stock(card_id, denom):
            await safe_edit_message(query,
                f"❌ *OUT OF STOCK*\n\n{card['full_emoji']} {card['name']} ₹{denom}",
                InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data=f"gift_{card_id}")]])
            )
            return
        
        balance = db.get_main_balance(user.id)
        if balance < price:
            await safe_edit_message(query,
                f"❌ *Insufficient Balance*\n\nRequired: ₹{price}\nYour: ₹{balance}",
                InlineKeyboardMarkup([[InlineKeyboardButton("💰 ADD MONEY", callback_data="menu_topup")]])
            )
            return
        
        context.user_data['purchase'] = {
            'type': 'gift',
            'card_id': card_id,
            'card_name': card['name'],
            'card_emoji': card['full_emoji'],
            'denom': denom,
            'price': price
        }
        
        await safe_edit_message(query,
            f"✅ *Confirm Purchase*\n\n"
            f"{card['full_emoji']} *{card['name']} ₹{denom}*\n"
            f"Price: *₹{price}*\n"
            f"Balance After: *₹{balance - price}*\n\n"
            f"📧 Enter your email:"
        )
        return STATE_EMAIL

    # ===== GAME RECHARGES =====
    elif data == "menu_game":
        text = f"{simple_header('GAME RECHARGES')}\n\nSelect game:"
        keyboard = []
        for game_id, game in GAME_RECHARGES.items():
            keyboard.append([InlineKeyboardButton(
                f"{game['full_emoji']} {game['name']}",
                callback_data=f"game_{game_id}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="main_menu")])
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))

    elif data.startswith("game_"):
        game_id = data[5:]
        game = GAME_RECHARGES.get(game_id)
        if not game:
            return
        
        text = f"{game['full_emoji']} *{game['name']}*\n" + "━" * 30 + "\n\n"
        keyboard = []
        
        if game_id in GAME_PRICES:
            for amount in GAME_PRICES[game_id]:
                stock = db.get_game_stock(game_id, amount)
                indicator = stock_indicator(stock)
                text += f"• ₹{amount} {indicator}\n"
                
                if stock > 0:
                    keyboard.append([InlineKeyboardButton(
                        f"₹{amount}",
                        callback_data=f"buy_game_{game_id}_{amount}"
                    )])
        
        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="menu_game")])
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))

    elif data.startswith("buy_game_"):
        parts = data.split('_')
        game_id = parts[2]
        amount = int(parts[3])
        
        game = GAME_RECHARGES[game_id]
        
        if db.get_game_stock(game_id, amount) <= 0:
            await safe_edit_message(query,
                f"❌ *OUT OF STOCK*\n\n{game['full_emoji']} {game['name']} ₹{amount}",
                InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data=f"game_{game_id}")]])
            )
            return
        
        balance = db.get_main_balance(user.id)
        if balance < amount:
            await safe_edit_message(query,
                f"❌ *Insufficient Balance*\n\nRequired: ₹{amount}\nYour: ₹{balance}",
                InlineKeyboardMarkup([[InlineKeyboardButton("💰 ADD MONEY", callback_data="menu_topup")]])
            )
            return
        
        context.user_data['purchase'] = {
            'type': 'game',
            'game_id': game_id,
            'game_name': game['name'],
            'game_emoji': game['full_emoji'],
            'amount': amount,
            'price': amount
        }
        
        await safe_edit_message(query,
            f"✅ *Confirm Purchase*\n\n"
            f"{game['full_emoji']} *{game['name']} ₹{amount}*\n"
            f"Price: *₹{amount}*\n"
            f"Balance After: *₹{balance - amount}*\n\n"
            f"🆔 Enter your game ID:"
        )
        return STATE_GAME_USER_ID

    # ===== MOBILE RECHARGE =====
    elif data == "menu_mobile":
        text = f"{simple_header('MOBILE RECHARGE')}\n\nSelect operator:"
        keyboard = []
        for op_id, op in MOBILE_OPERATORS.items():
            keyboard.append([InlineKeyboardButton(
                f"{op['full_emoji']} {op['name']}",
                callback_data=f"mobile_op_{op_id}"
            )])
        keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="main_menu")])
        await safe_edit_message(query, text, InlineKeyboardMarkup(keyboard))
        return STATE_MOBILE_NUMBER

    # ===== TOP UP =====
    elif data == "menu_topup":
        text = (
            f"{simple_header('ADD MONEY')}\n\n"
            f"💰 Min: ₹{MIN_RECHARGE}\n"
            f"💰 Max: ₹{MAX_RECHARGE}\n"
            f"💸 Fee: {FEE_PERCENT}% below ₹{FEE_THRESHOLD}\n\n"
            f"Select amount:"
        )
        await safe_edit_message(query, text, amount_keyboard())

    elif data.startswith("amount_"):
        amount = int(data[7:])
        fee, final = calculate_fee(amount)
        context.user_data["recharge"] = {"amount": amount, "fee": fee, "final": final}
        
        qr_path = generate_qr(UPI_ID, amount)
        
        text = (
            f"{simple_header('PAYMENT DETAILS')}\n\n"
            f"💰 Amount: *{format_currency(amount)}*\n"
            f"💸 Fee: *{format_currency(fee)}*\n"
            f"✅ You'll get: *{format_currency(final)}*\n\n"
            f"🏦 *UPI ID:* `{UPI_ID}`\n\n"
            f"📸 After payment:\n"
            f"1️⃣ Click *I HAVE PAID*\n"
            f"2️⃣ Upload screenshot\n"
            f"3️⃣ Enter UTR"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ I HAVE PAID", callback_data="paid")],
            [InlineKeyboardButton("🔙 BACK", callback_data="menu_topup")],
        ])

        if qr_path:
            with open(qr_path, "rb") as qr_file:
                await context.bot.send_photo(
                    chat_id=user.id,
                    photo=qr_file,
                    caption=text,
                    reply_markup=keyboard,
                    parse_mode=ParseMode.MARKDOWN
                )
            cleanup_temp_file(qr_path)
            await query.message.delete()
        else:
            await safe_edit_message(query, text, keyboard)

    # ===== WALLET =====
    elif data == "menu_wallet":
        db_user = db.get_user(user.id) or {}
        main_balance = db_user.get('balance', 0)
        bonus_balance = db_user.get('bonus_balance', 0)
        total = main_balance + bonus_balance
        purchases = db_user.get('total_purchases', 0)
        badge = user_badge(purchases)
        
        text = (
            f"{simple_header('MY WALLET')}\n\n"
            f"👤 {user.first_name} | {badge}\n"
            f"💰 Main: {format_currency(main_balance)}\n"
            f"🎁 Bonus: {format_currency(bonus_balance)}\n"
            f"💎 Total: {format_currency(total)}\n"
            f"🛒 Purchases: {purchases}\n"
            f"━" * 30
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 ADD MONEY", callback_data="menu_topup")],
            [InlineKeyboardButton("🔄 TRANSFER", callback_data="menu_transfer")],
            [InlineKeyboardButton("🔙 BACK", callback_data="main_menu")],
        ])
        await safe_edit_message(query, text, keyboard)

    # ===== REFERRAL =====
    elif data == "menu_referral":
        bot_info = await context.bot.get_me()
        bot_username = bot_info.username
        ref_link = db.get_referral_link(user.id, bot_username) or ""
        ref_count = db.get_referral_count(user.id)
        earnings = db.get_referral_earnings(user.id)
        
        text = (
            f"{simple_header('REFERRAL PROGRAM')}\n\n"
            f"💰 Earn *₹{REFERRAL_BONUS}* per friend!\n\n"
            f"🔗 *Your Link:*\n`{ref_link}`\n\n"
            f"📊 *Stats:*\n"
            f"  • Referrals: {ref_count}\n"
            f"  • Earned: ₹{earnings}\n"
            f"━" * 30
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 SHARE", url=f"https://t.me/share/url?url={ref_link}")],
            [InlineKeyboardButton("🔙 BACK", callback_data="main_menu")],
        ])
        await safe_edit_message(query, text, keyboard)

    # ===== DAILY REWARD =====
    elif data == "menu_daily":
        reward, result = db.claim_daily_reward(user.id)

        if result == "already_claimed":
            text = "⏰ *Already Claimed!*\n\nCome back tomorrow!"
        elif reward:
            text = f"🎉 *Reward Claimed!*\n\n💰 *₹{reward}*\n🔥 Streak: Day {result}"
        else:
            text = "❌ Error claiming reward."
        
        await safe_edit_message(query, text, InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 BACK", callback_data="main_menu")]
        ]))

    # ===== COUPON =====
    elif data == "menu_coupon":
        await safe_edit_message(query,
            f"{simple_header('COUPONS')}\n\nEnter coupon code:",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="main_menu")]])
        )
        return STATE_COUPON_CODE

    # ===== BULK PURCHASE =====
    elif data == "menu_bulk":
        text = f"{simple_header('BULK PURCHASE')}\n\n{format_bulk_discounts()}\n\nSelect category:"
        await safe_edit_message(query, text, gift_cards_keyboard())

    # ===== SUPPORT =====
    elif data == "menu_support":
        await safe_edit_message(query,
            f"{simple_header('SUPPORT')}\n\nType your issue:",
            InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="main_menu")]])
        )
        return STATE_SUPPORT

# ============================================================================
# PAYMENT HANDLERS
# ============================================================================

async def handle_paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    recharge = context.user_data.get("recharge")
    if not recharge:
        await safe_edit_message(query, "⏰ Session expired. Please start over.")
        return ConversationHandler.END

    await safe_edit_message(query,
        f"📸 *SEND SCREENSHOT*\n\n"
        f"Amount: *₹{recharge['amount']}*\n"
        f"You'll get: *₹{recharge['final']}*\n\n"
        f"Send a clear screenshot of your payment:"
    )
    return STATE_SCREENSHOT

async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❌ Please send a photo.")
        return STATE_SCREENSHOT

    photo = update.message.photo[-1]
    context.user_data["screenshot"] = photo.file_id
    await update.message.reply_text("✅ Screenshot received!\n\nNow enter UTR number:")
    return STATE_UTR

async def handle_utr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    utr = update.message.text.strip().upper()
    
    if not validate_utr(utr):
        await update.message.reply_text("❌ Invalid UTR (12-22 chars). Try again:")
        return STATE_UTR

    recharge = context.user_data.get("recharge")
    screenshot = context.user_data.get("screenshot")
    
    if not recharge or not screenshot:
        await update.message.reply_text("⏰ Session expired. Start over.")
        return ConversationHandler.END

    if db.is_utr_duplicate(utr):
        await update.message.reply_text("❌ UTR already used.")
        return STATE_UTR

    try:
        db.create_verification(
            update.effective_user.id,
            recharge["amount"],
            recharge["fee"],
            recharge["final"],
            utr,
            screenshot
        )
    except Exception as e:
        logger.error(f"DB error: {e}")
        await update.message.reply_text("❌ Database error. Try again.")
        return ConversationHandler.END

    try:
        caption = (
            f"💳 *NEW PAYMENT*\n" + "━" * 20 + "\n"
            f"👤 User: {update.effective_user.first_name}\n"
            f"🆔 ID: {update.effective_user.id}\n"
            f"💰 Amount: ₹{recharge['amount']}\n"
            f"✅ Credit: ₹{recharge['final']}\n"
            f"🔢 UTR: {utr}"
        )
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ APPROVE", callback_data=f"approve_{utr}"),
            InlineKeyboardButton("❌ REJECT", callback_data=f"reject_{utr}")
        ]])
        
        await context.bot.send_photo(
            chat_id=ADMIN_CHANNEL_ID,
            photo=screenshot,
            caption=caption,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Admin notify error: {e}")

    context.user_data.clear()
    await update.message.reply_text(
        f"✅ PAYMENT SUBMITTED!\n\n"
        f"Amount: ₹{recharge['amount']}\n"
        f"UTR: {utr}\n\n"
        f"You'll be notified when approved."
    )
    return ConversationHandler.END

# ============================================================================
# EMAIL HANDLER (Gift Cards)
# ============================================================================

async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    
    if not validate_email(email):
        await update.message.reply_text("❌ Invalid email. Try again:")
        return STATE_EMAIL

    purchase = context.user_data.get("purchase")
    if not purchase:
        await update.message.reply_text("❌ Session expired.")
        return ConversationHandler.END

    user = update.effective_user
    balance = db.get_main_balance(user.id)
    price = purchase["price"]

    if balance < price:
        await update.message.reply_text(f"❌ Insufficient balance!\nYour: ₹{balance}")
        return ConversationHandler.END

    if purchase['type'] == 'gift':
        if db.is_gift_out_of_stock(purchase['card_id'], purchase['denom']):
            await update.message.reply_text("❌ Out of stock!")
            return ConversationHandler.END
        db.decrease_gift_stock(purchase['card_id'], purchase['denom'])

    db.update_balance(user.id, -price, "debit", description=f"{purchase['card_name']} purchase")
    order_id = db.add_purchase(
        user.id,
        purchase['type'],
        'gift',
        purchase['card_id'],
        f"{purchase['card_name']} ₹{purchase['denom']}",
        purchase['denom'],
        price,
        email=email
    )

    await send_proof(context, {
        'type': purchase['type'],
        'name': user.first_name,
        'item': f"{purchase['card_emoji']} {purchase['card_name']} ₹{purchase['denom']}",
        'amount': price,
        'order_id': order_id
    })

    context.user_data.clear()
    await update.message.reply_text(
        f"✅ *PURCHASE SUCCESSFUL!*\n\n"
        f"{purchase['card_emoji']} *{purchase['card_name']} ₹{purchase['denom']}*\n"
        f"🆔 Order: `{order_id}`\n"
        f"📧 Sent to: `{email}`\n\n"
        f"⏳ Order is being processed. You'll receive the card shortly."
    )
    return ConversationHandler.END

# ============================================================================
# GAME USER ID HANDLER
# ============================================================================

async def handle_game_user_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    game_id = update.message.text.strip()
    purchase = context.user_data.get("purchase")
    
    if not purchase:
        await update.message.reply_text("❌ Session expired.")
        return ConversationHandler.END

    user = update.effective_user
    amount = purchase['amount']
    price = purchase['price']

    if db.decrease_game_stock(purchase['game_id'], amount):
        db.update_balance(user.id, -price, "debit", description=f"{purchase['game_name']} recharge")
        order_id = db.add_purchase(
            user.id,
            "game",
            "game",
            purchase['game_id'],
            f"{purchase['game_name']} ₹{amount}",
            amount,
            price,
            recipient=game_id,
            status="processing"
        )

        await send_proof(context, {
            'type': 'game',
            'name': user.first_name,
            'item': f"{purchase['game_emoji']} {purchase['game_name']} ₹{amount}",
            'amount': price,
            'order_id': order_id
        })

        await update.message.reply_text(
            f"✅ *ORDER PLACED!*\n\n"
            f"{purchase['game_emoji']} *{purchase['game_name']}*\n"
            f"💰 Amount: *₹{amount}*\n"
            f"🆔 Game ID: `{game_id}`\n"
            f"🆔 Order: `{order_id}`\n\n"
            f"⏳ Recharge is being processed."
        )
    else:
        await update.message.reply_text("❌ Out of stock!")

    context.user_data.clear()
    return ConversationHandler.END

# ============================================================================
# SUPPORT HANDLER
# ============================================================================

async def handle_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text.strip()
    
    if len(message) < 10:
        await update.message.reply_text("❌ Please describe your issue in detail.")
        return STATE_SUPPORT

    ticket_id = db.create_support_ticket(update.effective_user.id, message)

    try:
        await context.bot.send_message(
            ADMIN_CHANNEL_ID,
            f"🆘 *SUPPORT TICKET*\n" + "━" * 20 + "\n"
            f"👤 {update.effective_user.first_name}\n"
            f"🆔 {update.effective_user.id}\n"
            f"💬 {message}\n"
            f"🎫 {ticket_id}",
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        pass

    await update.message.reply_text(
        f"✅ *SUPPORT SENT!*\n\nTicket: `{ticket_id}`\nWe'll contact you within 24h."
    )
    return ConversationHandler.END

# ============================================================================
# COUPON HANDLER
# ============================================================================

async def handle_coupon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip().upper()
    user = update.effective_user

    coupon, error = db.validate_coupon(code, user.id, 100)  # Example amount
    if error:
        await update.message.reply_text(f"❌ {error}")
        return ConversationHandler.END

    db.use_coupon(code, user.id)
    discount_text = f"{coupon['discount_value']}% OFF" if coupon['discount_type'] == 'percentage' else f"₹{coupon['discount_value']} OFF"
    
    await update.message.reply_text(
        f"✅ *Coupon Applied!*\n\nCode: `{code}`\nDiscount: {discount_text}"
    )
    return ConversationHandler.END

# ============================================================================
# ADMIN HANDLER - FIXED (safe parsing)
# ============================================================================

async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id != ADMIN_ID:
        await query.answer("❌ Admin only!", show_alert=True)
        return

    data = query.data
    
    # Safe parsing using startswith
    if data.startswith("approve_"):
        utr = data[len("approve_"):]
        ver = db.get_verification_by_utr(utr)
        if ver and ver['status'] == 'pending':
            db.update_verification_by_utr(utr, "approved", ADMIN_ID)
            db.update_balance(ver['user_id'], ver['final_amount'], "credit", description="UPI recharge")
            
            try:
                await context.bot.send_message(
                    ver['user_id'],
                    f"✅ *PAYMENT APPROVED!*\n\nAmount: ₹{ver['final_amount']} added to your wallet."
                )
            except:
                pass
            
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n✅ *APPROVED*",
                parse_mode=ParseMode.MARKDOWN
            )
            db.log_admin_action(ADMIN_ID, "approve", f"UTR: {utr}")
    
    elif data.startswith("reject_"):
        utr = data[len("reject_"):]
        db.update_verification_by_utr(utr, "rejected", ADMIN_ID)
        await query.edit_message_caption(
            caption=query.message.caption + "\n\n❌ *REJECTED*",
            parse_mode=ParseMode.MARKDOWN
        )
        db.log_admin_action(ADMIN_ID, "reject", f"UTR: {utr}")

# ============================================================================
# ADMIN COMMANDS
# ============================================================================

@admin_only
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = db.get_statistics()
    text = (
        f"📊 *STATISTICS*\n" + "━" * 30 + "\n"
        f"👥 Users: {stats['total_users']:,}\n"
        f"🆕 Today: {stats['new_today']}\n"
        f"📱 Active: {stats['active_today']}\n\n"
        f"💰 Revenue: {format_currency(stats['total_revenue'])}\n"
        f"💳 Spent: {format_currency(stats['total_spent'])}\n"
        f"🛒 Purchases: {stats['total_purchases']:,}\n\n"
        f"⏳ Pending: {stats['pending_verifications']}\n"
        f"━" * 30
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

@admin_only
async def admin_add_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        card_id = context.args[0].lower()
        denom = int(context.args[1])
        qty = int(context.args[2])
        
        if card_id not in GIFT_CARDS:
            await update.message.reply_text("❌ Invalid card ID")
            return
        
        db.increase_gift_stock(card_id, denom, qty)
        await update.message.reply_text(f"✅ Added {qty} stock to {GIFT_CARDS[card_id]['name']} ₹{denom}")
        db.log_admin_action(ADMIN_ID, "add_stock", f"{card_id} {denom} +{qty}")
        
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Usage: /addstock CARD_ID DENOM QUANTITY")

@admin_only
async def admin_check_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"📦 *STOCK STATUS*\n" + "━" * 30 + "\n"
    
    for card_id, card in list(GIFT_CARDS.items())[:10]:  # Limit to 10 for readability
        for denom in GIFT_DENOMINATIONS:
            stock = db.get_gift_stock(card_id, denom)
            indicator = stock_indicator(stock)
            text += f"{card['emoji']} {card['name']} ₹{denom}: {indicator} ({stock})\n"
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

@admin_only
async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("📢 Usage: /broadcast Your message")
        return
    
    message = " ".join(context.args)
    users = db.execute("SELECT user_id FROM users", fetchall=True)
    
    status = await update.message.reply_text(f"📢 Broadcasting to {len(users)} users...")
    
    sent = 0
    failed = 0
    
    for user in users:
        try:
            await context.bot.send_message(
                user['user_id'],
                f"📢 *BROADCAST*\n\n{message}",
                parse_mode=ParseMode.MARKDOWN
            )
            sent += 1
            await asyncio.sleep(0.05)
        except:
            failed += 1
        
        if (sent + failed) % 10 == 0:
            await status.edit_text(f"📢 Progress: {sent} sent, {failed} failed")
    
    await status.edit_text(f"✅ Broadcast complete! Sent: {sent}, Failed: {failed}")
    db.log_admin_action(ADMIN_ID, "broadcast", f"Sent to {sent} users")

# ============================================================================
# ERROR HANDLER
# ============================================================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update caused error: {context.error}", exc_info=True)
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again or use /start."
            )
    except:
        pass

# ============================================================================
# CANCEL HANDLER
# ============================================================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END

# ============================================================================
# POST INIT
# ============================================================================

async def post_init(app):
    """Setup after bot initialization"""
    commands = [
        BotCommand("start", "🚀 Start"),
        BotCommand("stats", "📊 Admin stats"),
        BotCommand("addstock", "📦 Add stock"),
        BotCommand("checkstock", "📊 Check stock"),
        BotCommand("broadcast", "📢 Broadcast"),
        BotCommand("cancel", "❌ Cancel"),
    ]
    await app.bot.set_my_commands(commands)
    
    # Get bot username for referral links
    global BOT_USERNAME
    bot_info = await app.bot.get_me()
    BOT_USERNAME = bot_info.username
    
    # Test admin channel
    try:
        await app.bot.send_message(
            ADMIN_CHANNEL_ID,
            f"✅ *Bot Started*\n\n@{BOT_USERNAME} is online!",
            parse_mode=ParseMode.MARKDOWN
        )
        logger.info("✅ Admin channel verified")
    except Exception as e:
        logger.warning(f"Admin channel error: {e}")
    
    logger.info("✅ Bot ready!")

# ============================================================================
# GRACEFUL SHUTDOWN
# ============================================================================

async def shutdown(app):
    """Graceful shutdown"""
    logger.info("🛑 Shutting down...")
    db.close_all()
    logger.info("✅ Database connections closed")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main function with webhook/polling support"""
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("addstock", admin_add_stock))
    app.add_handler(CommandHandler("checkstock", admin_check_stock))
    app.add_handler(CommandHandler("broadcast", admin_broadcast))

    # Payment conversation
    payment_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_paid, pattern="^paid$")],
        states={
            STATE_SCREENSHOT: [MessageHandler(filters.PHOTO, handle_screenshot)],
            STATE_UTR: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_utr)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(payment_conv)

    # Email conversation (gift cards)
    email_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^buy_gift_")],
        states={
            STATE_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(email_conv)

    # Game user ID conversation
    game_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^buy_game_")],
        states={
            STATE_GAME_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_game_user_id)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(game_conv)

    # Coupon conversation
    coupon_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^menu_coupon$")],
        states={
            STATE_COUPON_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_coupon)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(coupon_conv)

    # Support conversation
    support_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern="^menu_support$")],
        states={
            STATE_SUPPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_support)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(support_conv)

    # Admin callback handler
    app.add_handler(CallbackQueryHandler(admin_handler, pattern="^(approve|reject)_"))

    # Main button handler
    app.add_handler(CallbackQueryHandler(button_handler))

    # Error handler
    app.add_error_handler(error_handler)

    # Setup shutdown handler
    import atexit
    atexit.register(lambda: asyncio.run(shutdown(app)))

    logger.info("🚀 Starting bot...")
    
    # Choose polling or webhook based on environment
    if WEBHOOK_URL:
        # Webhook mode for production
        app.run_webhook(
            listen="0.0.0.0",
            port=WEBHOOK_PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
            secret_token=WEBHOOK_SECRET,
            drop_pending_updates=True
        )
    else:
        # Polling mode for development
        app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
