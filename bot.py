#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
████████████████████████████████████████████████████████████████████████████████████████████████████████
█                                                                                                      █
█   ██████╗ ██╗███████╗████████╗     ██████╗ █████╗ ██████╗ ██████╗     �██████╗  ██████╗ ████████╗   █
█  ██╔════╝ ██║██╔════╝╚══██╔══╝    ██╔════╝██╔══██╗██╔══██╗██╔══██╗   ██╔════╝ ██╔═══██╗╚══██╔══╝   █
█  ██║  ███╗██║█████╗     ██║       ██║     ███████║██████╔╝██║  ██║   ██║      ██║   ██║   ██║      █
█  ██║   ██║██║██╔══╝     ██║       ██║     ██╔══██║██╔══██╗██║  ██║   ██║      ██║   ██║   ██║      █
█  ╚██████╔╝██║██║        ██║       ╚██████╗██║  ██║██████╔╝██████╔╝██╗╚██████╗ ╚██████╔╝   ██║      █
█   ╚═════╝ ╚═╝╚═╝        ╚═╝        ╚═════╝╚═╝  ╚═╝╚═════╝ ╚═════╝ ╚═╝ ╚═════╝  ╚═════╝    ╚═╝      █
█                                                                                                      █
████████████████████████████████████████████████████████████████████████████████████████████████████████
█                                                                                                      █
█   ╔══════════════════════════════════════════════════════════════════════════════════════════════╗   █
█   ║                        🎁 ULTIMATE GIFT CARD & RECHARGE BOT v5.0 🎁                          ║   █
█   ╠══════════════════════════════════════════════════════════════════════════════════════════════╣   █
█   ║                     ✦ 35+ GIFT CARDS ✦ 20+ GAMES ✦ ALL RECHARGES ✦                         ║   █
█   ║                     ✦ PREMIUM UI ✦ CINEMATIC ANIMATIONS ✦ 10,000+ LINES ✦                  ║   █
█   ║                     ✦ REAL-TIME PROOFS ✦ STOCK MANAGEMENT ✦ ADMIN PANEL ✦                   ║   █
█   ╚══════════════════════════════════════════════════════════════════════════════════════════════╝   █
█                                                                                                      █
████████████████████████████████████████████████████████████████████████████████████████████████████████
"""

import os
import sys
import json
import time
import math
import random
import asyncio
import logging
import sqlite3
import hashlib
import threading
import csv
import re
import uuid
from datetime import datetime, timedelta, date
from functools import wraps
from io import BytesIO, StringIO
from pathlib import Path
from queue import Queue
from typing import Dict, List, Tuple, Optional, Any, Union
from collections import defaultdict, OrderedDict
from enum import Enum

# ============================================================================
# THIRD PARTY IMPORTS
# ============================================================================

try:
    import qrcode
    from PIL import Image, ImageDraw, ImageFont
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# ============================================================================
# TELEGRAM IMPORTS
# ============================================================================

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters, ContextTypes
)
from telegram.constants import ParseMode
from telegram.error import TelegramError, RetryAfter, TimedOut

# ============================================================================
# CONFIGURATION - ENVIRONMENT VARIABLES
# ============================================================================

def get_env_var(name: str, required: bool = True, default: Any = None) -> Any:
    """Get environment variable with validation"""
    value = os.environ.get(name, default)
    if required and not value:
        raise ValueError(f"❌ {name} environment variable not set!")
    return value

# Core Configuration
BOT_TOKEN = get_env_var("BOT_TOKEN")
BOT_USERNAME = get_env_var("BOT_USERNAME", required=False, default="")
ADMIN_ID = int(get_env_var("ADMIN_ID"))
UPI_ID = get_env_var("UPI_ID")

# Channels
MAIN_CHANNEL = get_env_var("MAIN_CHANNEL", default="@gift_card_main")
PROOF_CHANNEL = get_env_var("PROOF_CHANNEL", default="@gift_card_log")
ADMIN_CHANNEL_ID = int(get_env_var("ADMIN_CHANNEL_ID", default="-1003607749028"))

# Paths
DATABASE_PATH = get_env_var("DATABASE_PATH", default="premium_bot.db")
QR_CODE_PATH = get_env_var("QR_CODE_PATH", default="qr.jpg")
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True, parents=True)

# Webhook (Optional)
WEBHOOK_URL = get_env_var("WEBHOOK_URL", required=False, default="")
WEBHOOK_PORT = int(get_env_var("WEBHOOK_PORT", default="8080"))
WEBHOOK_SECRET = get_env_var("WEBHOOK_SECRET", required=False, default="")

# ============================================================================
# PREMIUM LOGGING SETUP
# ============================================================================

class PremiumLogger:
    """Premium logging with colors and formatting"""
    
    COLORS = {
        'RESET': '\033[0m',
        'BLACK': '\033[30m',
        'RED': '\033[31m',
        'GREEN': '\033[32m',
        'YELLOW': '\033[33m',
        'BLUE': '\033[34m',
        'MAGENTA': '\033[35m',
        'CYAN': '\033[36m',
        'WHITE': '\033[37m',
        'BOLD': '\033[1m',
        'UNDERLINE': '\033[4m'
    }
    
    EMOJI = {
        'INFO': 'ℹ️',
        'SUCCESS': '✅',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🔥',
        'DEBUG': '🐛',
        'PAYMENT': '💰',
        'USER': '👤',
        'ADMIN': '👑',
        'CARD': '🎁',
        'DATABASE': '🗄️',
        'NETWORK': '🌐',
        'ANIMATION': '✨'
    }
    
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Console handler with colors
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(self.PremiumFormatter())
        self.logger.addHandler(console)
        
        # File handler
        log_file = LOG_DIR / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
        ))
        self.logger.addHandler(file_handler)
    
    class PremiumFormatter(logging.Formatter):
        def format(self, record):
            emoji = PremiumLogger.EMOJI.get(record.levelname, '📌')
            color = PremiumLogger.COLORS.get('GREEN' if record.levelname == 'INFO' else 
                                           'YELLOW' if record.levelname == 'WARNING' else
                                           'RED' if record.levelname == 'ERROR' else
                                           'MAGENTA' if record.levelname == 'CRITICAL' else
                                           'CYAN', '')
            reset = PremiumLogger.COLORS['RESET']
            bold = PremiumLogger.COLORS['BOLD']
            
            timestamp = datetime.now().strftime('%H:%M:%S')
            return f"{bold}{color}[{timestamp}] {emoji} {record.getMessage()}{reset}"
    
    def info(self, msg): self.logger.info(msg)
    def success(self, msg): self.logger.info(f"✅ {msg}")
    def warning(self, msg): self.logger.warning(msg)
    def error(self, msg): self.logger.error(msg)
    def critical(self, msg): self.logger.critical(msg)
    def debug(self, msg): self.logger.debug(msg)
    
    def payment(self, msg): self.logger.info(f"💰 {msg}")
    def user(self, msg): self.logger.info(f"👤 {msg}")
    def admin(self, msg): self.logger.info(f"👑 {msg}")
    def card(self, msg): self.logger.info(f"🎁 {msg}")
    def db(self, msg): self.logger.info(f"🗄️ {msg}")
    def animation(self, msg): self.logger.info(f"✨ {msg}")

logger = PremiumLogger(__name__)

# ============================================================================
# BASE CONFIGURATION
# ============================================================================

# Payment Settings
MIN_RECHARGE = 10
MAX_RECHARGE = 100000
FEE_PERCENT = 20
FEE_THRESHOLD = 120

# Bonus Settings
REFERRAL_BONUS = 5
WELCOME_BONUS = 10
DAILY_LOGIN_BONUS = 5
STREAK_BONUS_MULTIPLIER = 1.5

# Auto Posts
POSTS_PER_DAY = 24
POST_INTERVAL = 3600  # 1 hour

# ============================================================================
# GIFT CARDS - PREMIUM COLLECTION (50+ BRANDS)
# ============================================================================

GIFT_CARDS = {
    # 🛒 SHOPPING GIANTS
    "amazon": {
        "id": "amazon",
        "name": "AMAZON", 
        "emoji": "🟦",
        "full_emoji": "🟦🛒",
        "description": "🌐 *Amazon.in - World's Largest Online Store*\n\n✅ Shop millions of products\n✅ Instant delivery on email\n✅ Valid on all Amazon services\n✅ No expiry date\n✅ Amazon Prime eligible\n\n🔥 *Best for:* Electronics, Books, Fashion, Home Appliances",
        "popular": True,
        "trending": True,
        "category": "shopping",
        "brand_color": "#FF9900",
        "rating": 4.9,
        "reviews": 15234
    },
    "flipkart": {
        "id": "flipkart",
        "name": "FLIPKART", 
        "emoji": "📦",
        "full_emoji": "📦🛍️",
        "description": "📦 *Flipkart - India's Shopping Destination*\n\n✅ Electronics, Fashion, Home Appliances\n✅ Instant email delivery\n✅ Valid on all Flipkart products\n✅ Flipkart Plus eligible\n✅ Great for gifting\n\n🔥 *Best for:* Electronics, Fashion, Smartphones",
        "popular": True,
        "trending": True,
        "category": "shopping",
        "brand_color": "#2874F0",
        "rating": 4.8,
        "reviews": 12456
    },
    "myntra": {
        "id": "myntra",
        "name": "MYNTRA", 
        "emoji": "🛍️",
        "full_emoji": "🛍️👗",
        "description": "👗 *Myntra - Fashion Destination*\n\n✅ 2000+ fashion brands\n✅ Latest trends & styles\n✅ Instant email delivery\n✅ End of Reason Sales\n✅ Free shipping on app\n\n🔥 *Best for:* Clothing, Accessories, Footwear",
        "popular": True,
        "trending": True,
        "category": "shopping",
        "brand_color": "#E12B38",
        "rating": 4.7,
        "reviews": 8934
    },
    "ajio": {
        "id": "ajio",
        "name": "AJIO", 
        "emoji": "👕",
        "full_emoji": "👕🛍️",
        "description": "👕 *AJIO - Your Fashion Superstore*\n\n✅ International brands\n✅ Latest collections\n✅ Instant delivery\n✅ Great discounts\n✅ AJIO membership benefits\n\n🔥 *Best for:* Fashion, Lifestyle, Accessories",
        "popular": False,
        "trending": False,
        "category": "shopping",
        "brand_color": "#E65F5F",
        "rating": 4.5,
        "reviews": 3456
    },
    "snapdeal": {
        "id": "snapdeal",
        "name": "SNAPDEAL", 
        "emoji": "🧥",
        "full_emoji": "🧥📦",
        "description": "🧥 *SnapDeal - Value Shopping*\n\n✅ Great deals & discounts\n✅ Multiple categories\n✅ Instant email delivery\n✅ Seller protection\n\n🔥 *Best for:* Fashion, Electronics, Home",
        "popular": False,
        "trending": False,
        "category": "shopping",
        "brand_color": "#E43E3E",
        "rating": 4.3,
        "reviews": 2345
    },
    "croma": {
        "id": "croma",
        "name": "CROMA", 
        "emoji": "💻",
        "full_emoji": "💻🖥️",
        "description": "💻 *Croma - Electronics Superstore*\n\n✅ Latest gadgets & appliances\n✅ Trusted brand\n✅ Instant delivery\n✅ Extended warranty options\n\n🔥 *Best for:* Electronics, Appliances, Gadgets",
        "popular": False,
        "trending": False,
        "category": "shopping",
        "brand_color": "#E31837",
        "rating": 4.6,
        "reviews": 4567
    },
    "reliance": {
        "id": "reliance",
        "name": "RELIANCE DIGITAL", 
        "emoji": "📱",
        "full_emoji": "📱🛒",
        "description": "📱 *Reliance Digital - Tech Superstore*\n\n✅ Wide range of electronics\n✅ Best prices guaranteed\n✅ Instant delivery\n✅ Jio benefits\n\n🔥 *Best for:* Electronics, Mobiles, Appliances",
        "popular": False,
        "trending": False,
        "category": "shopping",
        "brand_color": "#005BBB",
        "rating": 4.5,
        "reviews": 3789
    },
    "tatacliq": {
        "id": "tatacliq",
        "name": "TATA CLIQ", 
        "emoji": "🛍️",
        "full_emoji": "🛍️🔴",
        "description": "🛍️ *Tata CLIQ - Premium Shopping*\n\n✅ Tata Trust\n✅ Premium brands\n✅ Luxury shopping\n✅ Instant delivery\n\n🔥 *Best for:* Luxury, Fashion, Accessories",
        "popular": False,
        "trending": False,
        "category": "shopping",
        "brand_color": "#E41B17",
        "rating": 4.7,
        "reviews": 2890
    },
    "shoppersstop": {
        "id": "shoppersstop",
        "name": "SHOPPERS STOP", 
        "emoji": "👔",
        "full_emoji": "👔🛍️",
        "description": "👔 *Shoppers Stop - Fashion Forward*\n\n✅ Premium fashion brands\n✅ First Citizen rewards\n✅ Instant delivery\n✅ Exclusive collections\n\n🔥 *Best for:* Fashion, Accessories, Beauty",
        "popular": False,
        "trending": False,
        "category": "shopping",
        "brand_color": "#ED1C24",
        "rating": 4.5,
        "reviews": 3124
    },
    
    # 🎮 GAMING POWERHOUSES
    "playstore": {
        "id": "playstore",
        "name": "PLAY STORE", 
        "emoji": "🟩",
        "full_emoji": "🟩🎮",
        "description": "🎮 *Google Play - Ultimate Gaming & Apps*\n\n✅ Millions of apps & games\n✅ In-app purchases\n✅ Movies & books\n✅ Google One eligible\n✅ Family sharing\n\n🔥 *Best for:* Apps, Games, Movies, Books",
        "popular": True,
        "trending": True,
        "category": "gaming",
        "brand_color": "#34A853",
        "rating": 4.9,
        "reviews": 18345
    },
    "xbox": {
        "id": "xbox",
        "name": "XBOX", 
        "emoji": "🎮",
        "full_emoji": "🎮🟢",
        "description": "🎮 *Xbox - Game Pass Ultimate*\n\n✅ Xbox Game Pass\n✅ Live Gold membership\n✅ Latest games\n✅ Cloud gaming\n✅ Play anywhere\n\n🔥 *Best for:* Xbox games, Game Pass, Live Gold",
        "popular": False,
        "trending": True,
        "category": "gaming",
        "brand_color": "#107C10",
        "rating": 4.8,
        "reviews": 6789
    },
    "playstation": {
        "id": "playstation",
        "name": "PLAYSTATION", 
        "emoji": "🎮",
        "full_emoji": "🎮🔵",
        "description": "🎮 *PlayStation - Premium Gaming*\n\n✅ PS Plus membership\n✅ Latest PS5 games\n✅ Discounts on store\n✅ Exclusive content\n✅ Cloud saves\n\n🔥 *Best for:* PlayStation games, PS Plus",
        "popular": False,
        "trending": True,
        "category": "gaming",
        "brand_color": "#003791",
        "rating": 4.9,
        "reviews": 7890
    },
    "nintendo": {
        "id": "nintendo",
        "name": "NINTENDO", 
        "emoji": "🎮",
        "full_emoji": "🎮🔴",
        "description": "🎮 *Nintendo - Family Gaming*\n\n✅ Switch games\n✅ Nintendo Online\n✅ Classic titles\n✅ Indie games\n✅ Family friendly\n\n🔥 *Best for:* Switch games, Nintendo Online",
        "popular": False,
        "trending": False,
        "category": "gaming",
        "brand_color": "#E60012",
        "rating": 4.8,
        "reviews": 4567
    },
    "steam": {
        "id": "steam",
        "name": "STEAM", 
        "emoji": "🎮",
        "full_emoji": "🎮💨",
        "description": "🎮 *Steam - PC Gaming Hub*\n\n✅ Thousands of PC games\n✅ Seasonal sales\n✅ Steam Deck compatible\n✅ Workshop content\n✅ Community features\n\n🔥 *Best for:* PC games, DLC, Software",
        "popular": False,
        "trending": True,
        "category": "gaming",
        "brand_color": "#171A21",
        "rating": 4.8,
        "reviews": 12345
    },
    "epic": {
        "id": "epic",
        "name": "EPIC GAMES", 
        "emoji": "🎮",
        "full_emoji": "🎮⚡",
        "description": "🎮 *Epic Games Store*\n\n✅ Free games weekly\n✅ Great discounts\n✅ Unreal Engine\n✅ Cross-platform\n✅ Exclusive titles\n\n🔥 *Best for:* Epic exclusives, Free games",
        "popular": False,
        "trending": True,
        "category": "gaming",
        "brand_color": "#2A2A2A",
        "rating": 4.7,
        "reviews": 5678
    },
    "rockstar": {
        "id": "rockstar",
        "name": "ROCKSTAR", 
        "emoji": "🎮",
        "full_emoji": "🎮⭐",
        "description": "🎮 *Rockstar Games*\n\n✅ GTA V & Online\n✅ Red Dead Redemption\n✅ Shark Cards\n✅ Gold Bars\n✅ Exclusive content\n\n🔥 *Best for:* GTA, Red Dead, Shark Cards",
        "popular": False,
        "trending": True,
        "category": "gaming",
        "brand_color": "#FCAF17",
        "rating": 4.8,
        "reviews": 8923
    },
    "ubisoft": {
        "id": "ubisoft",
        "name": "UBISOFT", 
        "emoji": "🎮",
        "full_emoji": "🎮🔷",
        "description": "🎮 *Ubisoft - Assassin's Creed*\n\n✅ Ubisoft Connect\n✅ Latest releases\n✅ Season passes\n✅ In-game currency\n✅ Club rewards\n\n🔥 *Best for:* Ubisoft games, Credits",
        "popular": False,
        "trending": False,
        "category": "gaming",
        "brand_color": "#2A2A2A",
        "rating": 4.6,
        "reviews": 4563
    },
    
    # 🎬 ENTERTAINMENT
    "netflix": {
        "id": "netflix",
        "name": "NETFLIX", 
        "emoji": "🎬",
        "full_emoji": "🎬📺",
        "description": "📺 *Netflix - Premium Streaming*\n\n✅ Unlimited movies & shows\n✅ 4K Ultra HD\n✅ No ads\n✅ Download to watch\n✅ Share with family\n\n🔥 *Best for:* Movies, TV Shows, Documentaries",
        "popular": True,
        "trending": True,
        "category": "entertainment",
        "brand_color": "#E50914",
        "rating": 4.9,
        "reviews": 15234
    },
    "primevideo": {
        "id": "primevideo",
        "name": "PRIME VIDEO", 
        "emoji": "🎬",
        "full_emoji": "🎬🔵",
        "description": "🎬 *Amazon Prime Video*\n\n✅ Exclusive Originals\n✅ Latest movies\n✅ Rent or buy\n✅ Prime benefits\n✅ Download offline\n\n🔥 *Best for:* Movies, TV Shows, Originals",
        "popular": False,
        "trending": True,
        "category": "entertainment",
        "brand_color": "#00A8E1",
        "rating": 4.7,
        "reviews": 9234
    },
    "hotstar": {
        "id": "hotstar",
        "name": "HOTSTAR", 
        "emoji": "🎬",
        "full_emoji": "🎬🟠",
        "description": "🎬 *Disney+ Hotstar*\n\n✅ Disney+ content\n✅ Marvel & Star Wars\n✅ Live sports\n✅ Indian content\n✅ Multiple languages\n\n🔥 *Best for:* Disney+, Marvel, Sports, Indian content",
        "popular": False,
        "trending": True,
        "category": "entertainment",
        "brand_color": "#FF6F00",
        "rating": 4.7,
        "reviews": 11345
    },
    "sonyliv": {
        "id": "sonyliv",
        "name": "SONY LIV", 
        "emoji": "🎬",
        "full_emoji": "🎬🟢",
        "description": "🎬 *Sony LIV - Premium Content*\n\n✅ Live sports\n✅ TV shows\n✅ Movies\n✅ Originals\n✅ Multiple languages\n\n🔥 *Best for:* Sports, Shows, Movies",
        "popular": False,
        "trending": False,
        "category": "entertainment",
        "brand_color": "#1BA66B",
        "rating": 4.5,
        "reviews": 4567
    },
    "zeetv": {
        "id": "zeetv",
        "name": "ZEE5", 
        "emoji": "🎬",
        "full_emoji": "🎬🟣",
        "description": "🎬 *ZEE5 - Indian Entertainment*\n\n✅ Originals\n✅ Movies\n✅ TV shows\n✅ Live TV\n✅ Multiple languages\n\n🔥 *Best for:* Indian content, Movies, Shows",
        "popular": False,
        "trending": False,
        "category": "entertainment",
        "brand_color": "#6A1B9A",
        "rating": 4.4,
        "reviews": 3890
    },
    
    # 🎵 MUSIC
    "spotify": {
        "id": "spotify",
        "name": "SPOTIFY", 
        "emoji": "🎵",
        "full_emoji": "🎵🎧",
        "description": "🎵 *Spotify - Music Streaming*\n\n✅ Millions of songs\n✅ Ad-free music\n✅ Download offline\n✅ High quality audio\n✅ Podcasts included\n\n🔥 *Best for:* Music, Podcasts, Audio books",
        "popular": True,
        "trending": True,
        "category": "music",
        "brand_color": "#1DB954",
        "rating": 4.9,
        "reviews": 11234
    },
    "gaana": {
        "id": "gaana",
        "name": "GAANA", 
        "emoji": "🎵",
        "full_emoji": "🎵🟠",
        "description": "🎵 *Gaana - Indian Music*\n\n✅ Bollywood hits\n✅ Regional music\n✅ Podcasts\n✅ Download offline\n✅ High quality\n\n🔥 *Best for:* Bollywood, Regional, Podcasts",
        "popular": False,
        "trending": False,
        "category": "music",
        "brand_color": "#FF6F00",
        "rating": 4.6,
        "reviews": 5678
    },
    "wynk": {
        "id": "wynk",
        "name": "WYNK", 
        "emoji": "🎵",
        "full_emoji": "🎵🔴",
        "description": "🎵 *Wynk Music - Airtel*\n\n✅ Latest songs\n✅ Bollywood hits\n✅ Podcasts\n✅ Download offline\n✅ Airtel benefits\n\n🔥 *Best for:* Bollywood, Regional, Podcasts",
        "popular": False,
        "trending": False,
        "category": "music",
        "brand_color": "#E30046",
        "rating": 4.5,
        "reviews": 4567
    },
    "applemusic": {
        "id": "applemusic",
        "name": "APPLE MUSIC", 
        "emoji": "🎵",
        "full_emoji": "🎵🍎",
        "description": "🎵 *Apple Music - Premium Sound*\n\n✅ 100M+ songs\n✅ Spatial Audio\n✅ Lossless quality\n✅ Music videos\n✅ Exclusive releases\n\n🔥 *Best for:* Music, Spatial Audio, Exclusives",
        "popular": False,
        "trending": True,
        "category": "music",
        "brand_color": "#FA243C",
        "rating": 4.8,
        "reviews": 8923
    },
    
    # 🍕 FOOD & DELIVERY
    "zomato": {
        "id": "zomato",
        "name": "ZOMATO", 
        "emoji": "🍕",
        "full_emoji": "🍕🍔",
        "description": "🍔 *Zomato - Food Delivery*\n\n✅ Order from 1000+ restaurants\n✅ Zomato Gold benefits\n✅ Instant delivery\n✅ Great offers\n✅ Dining out\n\n🔥 *Best for:* Food delivery, Dining, Gold membership",
        "popular": True,
        "trending": True,
        "category": "food",
        "brand_color": "#CB202D",
        "rating": 4.8,
        "reviews": 10234
    },
    "swiggy": {
        "id": "swiggy",
        "name": "SWIGGY", 
        "emoji": "🍔",
        "full_emoji": "🍔🍟",
        "description": "🍔 *Swiggy - Food Delivery*\n\n✅ Fastest delivery\n✅ Swiggy One benefits\n✅ Live order tracking\n✅ Great discounts\n✅ Genie service\n\n🔥 *Best for:* Food delivery, One membership, Instamart",
        "popular": True,
        "trending": True,
        "category": "food",
        "brand_color": "#FC8019",
        "rating": 4.8,
        "reviews": 11234
    },
    "zomatogold": {
        "id": "zomatogold",
        "name": "ZOMATO GOLD", 
        "emoji": "🥡",
        "full_emoji": "🥡⭐",
        "description": "⭐ *Zomato Gold - Premium Dining*\n\n✅ 1+1 on food\n✅ Exclusive offers\n✅ Priority delivery\n✅ Dining discounts\n✅ Partner benefits\n\n🔥 *Best for:* Dining out, Premium benefits",
        "popular": True,
        "trending": True,
        "category": "food",
        "brand_color": "#E23744",
        "rating": 4.7,
        "reviews": 7890
    },
    "dominos": {
        "id": "dominos",
        "name": "DOMINOS", 
        "emoji": "🍕",
        "full_emoji": "🍕🔴",
        "description": "🍕 *Domino's Pizza*\n\n✅ Fresh pizzas\n✅ Track your order\n✅ Great deals\n✅ 30 min delivery\n✅ Sides & desserts\n\n🔥 *Best for:* Pizza, Sides, Deals",
        "popular": False,
        "trending": False,
        "category": "food",
        "brand_color": "#E31837",
        "rating": 4.6,
        "reviews": 5678
    },
    "pizzahut": {
        "id": "pizzahut",
        "name": "PIZZA HUT", 
        "emoji": "🍕",
        "full_emoji": "🍕🟢",
        "description": "🍕 *Pizza Hut - Italian Favorite*\n\n✅ Delicious pizzas\n✅ Sides & desserts\n✅ Meal deals\n✅ Online ordering\n✅ Delivery tracking\n\n🔥 *Best for:* Pizza, Pasta, Sides",
        "popular": False,
        "trending": False,
        "category": "food",
        "brand_color": "#008748",
        "rating": 4.5,
        "reviews": 4567
    },
    "mcdonalds": {
        "id": "mcdonalds",
        "name": "MCDONALD'S", 
        "emoji": "🍔",
        "full_emoji": "🍔🟡",
        "description": "🍔 *McDonald's - Fast Food*\n\n✅ Burgers & fries\n✅ Happy Meals\n✅ Breakfast\n✅ Coffee\n✅ Great deals\n\n🔥 *Best for:* Burgers, Fries, Breakfast",
        "popular": False,
        "trending": False,
        "category": "food",
        "brand_color": "#FFC72C",
        "rating": 4.5,
        "reviews": 6789
    },
    "kfc": {
        "id": "kfc",
        "name": "KFC", 
        "emoji": "🍗",
        "full_emoji": "🍗🔴",
        "description": "🍗 *KFC - Finger Lickin' Good*\n\n✅ Fried chicken\n✅ Bucket meals\n✅ Burgers & wraps\n✅ Sides & desserts\n✅ Exclusive offers\n\n🔥 *Best for:* Chicken, Buckets, Meals",
        "popular": False,
        "trending": False,
        "category": "food",
        "brand_color": "#E41B17",
        "rating": 4.6,
        "reviews": 7890
    },
    
    # 🛒 GROCERY
    "bigbasket": {
        "id": "bigbasket",
        "name": "BIG BASKET", 
        "emoji": "🛒",
        "full_emoji": "🛒🥬",
        "description": "🥬 *BigBasket - Grocery Delivery*\n\n✅ Fresh vegetables\n✅ Daily essentials\n✅ Express delivery\n✅ Great discounts\n✅ Member benefits\n\n🔥 *Best for:* Grocery, Vegetables, Daily needs",
        "popular": True,
        "trending": True,
        "category": "grocery",
        "brand_color": "#A7C83B",
        "rating": 4.7,
        "reviews": 8923
    },
    "grofers": {
        "id": "grofers",
        "name": "GROFERS", 
        "emoji": "🛒",
        "full_emoji": "🛒🟠",
        "description": "🛒 *Grofers - Daily Needs*\n\n✅ Grocery delivery\n✅ Fresh produce\n✅ Home essentials\n✅ Quick delivery\n✅ Great offers\n\n🔥 *Best for:* Grocery, Essentials, Home",
        "popular": False,
        "trending": False,
        "category": "grocery",
        "brand_color": "#F47421",
        "rating": 4.5,
        "reviews": 4567
    },
    "zepto": {
        "id": "zepto",
        "name": "ZEPTO", 
        "emoji": "⚡",
        "full_emoji": "⚡🛒",
        "description": "⚡ *Zepto - 10 Minute Delivery*\n\n✅ Super fast delivery\n✅ Fresh groceries\n✅ Wide selection\n✅ No minimum order\n✅ Great prices\n\n🔥 *Best for:* Quick delivery, Grocery, Essentials",
        "popular": True,
        "trending": True,
        "category": "grocery",
        "brand_color": "#7A2E92",
        "rating": 4.8,
        "reviews": 6789
    },
    "blinkit": {
        "id": "blinkit",
        "name": "BLINKIT", 
        "emoji": "⚡",
        "full_emoji": "⚡🛍️",
        "description": "⚡ *Blinkit - Instant Delivery*\n\n✅ 10 minute delivery\n✅ Wide selection\n✅ Fresh produce\n✅ Daily essentials\n✅ Great app\n\n🔥 *Best for:* Quick delivery, Grocery, Essentials",
        "popular": True,
        "trending": True,
        "category": "grocery",
        "brand_color": "#FBB03B",
        "rating": 4.7,
        "reviews": 7890
    },
    "jiomart": {
        "id": "jiomart",
        "name": "JIO MART", 
        "emoji": "🛒",
        "full_emoji": "🛒🟣",
        "description": "🛒 *JioMart - Reliance Retail*\n\n✅ Wide selection\n✅ Fresh groceries\n✅ Home delivery\n✅ Jio benefits\n✅ Great prices\n\n🔥 *Best for:* Grocery, Essentials, Jio offers",
        "popular": False,
        "trending": False,
        "category": "grocery",
        "brand_color": "#A020F0",
        "rating": 4.6,
        "reviews": 5678
    },
}

# Gift Card Prices
GIFT_PRICES = {
    500: 175,    # 65% OFF
    1000: 350,   # 65% OFF
    2000: 700,   # 65% OFF
    5000: 1750,  # 65% OFF
    10000: 3500, # 65% OFF
    25000: 8750, # 65% OFF
    50000: 17500 # 65% OFF
}

GIFT_DENOMINATIONS = [500, 1000, 2000, 5000, 10000, 25000, 50000]

# ============================================================================
# GAME RECHARGES (FREE FIRE, PUBG, BGMI, ETC.)
# ============================================================================

GAME_RECHARGES = {
    "freefire": {
        "id": "freefire",
        "name": "FREE FIRE", 
        "emoji": "🔫",
        "full_emoji": "🔫🔥",
        "description": "🔥 *Free Fire - Battle Royale*\n\n✅ Diamonds for in-game purchases\n✅ Elite passes\n✅ Bundles & skins\n✅ Fast delivery\n✅ Best rates\n\n🔥 *Best for:* Diamonds, Elite Pass, Skins",
        "popular": True,
        "trending": True,
        "icon": "https://example.com/ff.png"
    },
    "ffmax": {
        "id": "ffmax",
        "name": "FREE FIRE MAX", 
        "emoji": "🔫",
        "full_emoji": "🔫💎",
        "description": "💎 *Free Fire MAX - Enhanced Graphics*\n\n✅ Diamonds transfer from FF\n✅ Better graphics\n✅ Elite passes\n✅ Exclusive content\n✅ Fast delivery\n\n🔥 *Best for:* Diamonds, Elite Pass, Premium content",
        "popular": True,
        "trending": True,
        "icon": "https://example.com/ffmax.png"
    },
    "pubg": {
        "id": "pubg",
        "name": "PUBG MOBILE", 
        "emoji": "🎯",
        "full_emoji": "🎯🪖",
        "description": "🎯 *PUBG Mobile - Battle Royale*\n\n✅ Unknown Cash (UC)\n✅ Royale Pass\n✅ Crates & spins\n✅ Skins & outfits\n✅ Fast delivery\n\n🔥 *Best for:* UC, Royale Pass, Crates",
        "popular": True,
        "trending": True,
        "icon": "https://example.com/pubg.png"
    },
    "bgmi": {
        "id": "bgmi",
        "name": "BGMI", 
        "emoji": "🎯",
        "full_emoji": "🎯🇮🇳",
        "description": "🇮🇳 *BGMI - Battlegrounds Mobile India*\n\n✅ UC for in-game purchases\n✅ Royale Pass\n✅ Crates & spins\n✅ Indian server\n✅ Fast delivery\n\n🔥 *Best for:* UC, Royale Pass, Crates",
        "popular": True,
        "trending": True,
        "icon": "https://example.com/bgmi.png"
    },
    "cod": {
        "id": "cod",
        "name": "CALL OF DUTY", 
        "emoji": "🔫",
        "full_emoji": "🔫🎮",
        "description": "🎮 *Call of Duty Mobile*\n\n✅ CP (COD Points)\n✅ Battle Pass\n✅ Crates\n✅ Skins\n✅ Fast delivery\n\n🔥 *Best for:* CP, Battle Pass, Crates",
        "popular": False,
        "trending": True,
        "icon": "https://example.com/cod.png"
    },
    "dream11": {
        "id": "dream11",
        "name": "DREAM11", 
        "emoji": "🏏",
        "full_emoji": "🏏🎯",
        "description": "🏏 *Dream11 - Fantasy Sports*\n\n✅ Join contests\n✅ Create teams\n✅ Win cash\n✅ Instant joining\n✅ IPL special\n\n🔥 *Best for:* Contest entries, Joining fees",
        "popular": True,
        "trending": True,
        "icon": "https://example.com/dream11.png"
    },
    "my11circle": {
        "id": "my11circle",
        "name": "MY11CIRCLE", 
        "emoji": "🏏",
        "full_emoji": "🏏🔄",
        "description": "🔄 *My11Circle - Fantasy Cricket*\n\n✅ Join leagues\n✅ Create dream team\n✅ Win real cash\n✅ Instant joining\n✅ Great bonuses\n\n🔥 *Best for:* Contest entries, Fantasy cricket",
        "popular": False,
        "trending": False,
        "icon": "https://example.com/my11.png"
    },
    "mobilelegends": {
        "id": "mobilelegends",
        "name": "MOBILE LEGENDS", 
        "emoji": "⚔️",
        "full_emoji": "⚔️🎮",
        "description": "⚔️ *Mobile Legends: Bang Bang*\n\n✅ Diamonds for heroes\n✅ Weekly passes\n✅ Skins & emotes\n✅ Starlight membership\n✅ Fast delivery\n\n🔥 *Best for:* Diamonds, Starlight, Skins",
        "popular": False,
        "trending": True,
        "icon": "https://example.com/mlbb.png"
    },
    "clashofclans": {
        "id": "clashofclans",
        "name": "CLASH OF CLANS", 
        "emoji": "🏰",
        "full_emoji": "🏰⚔️",
        "description": "🏰 *Clash of Clans - Strategy Game*\n\n✅ Gems for builders\n✅ Gold Pass\n✅ Resources packs\n✅ Exclusive items\n✅ Fast delivery\n\n🔥 *Best for:* Gems, Gold Pass, Resource packs",
        "popular": False,
        "trending": False,
        "icon": "https://example.com/coc.png"
    },
    "clashroyale": {
        "id": "clashroyale",
        "name": "CLASH ROYALE", 
        "emoji": "👑",
        "full_emoji": "👑⚔️",
        "description": "👑 *Clash Royale - Card Battle*\n\n✅ Gems for chests\n✅ Pass Royale\n✅ Gold & cards\n✅ Emotes & tower skins\n✅ Fast delivery\n\n🔥 *Best for:* Gems, Pass Royale, Gold",
        "popular": False,
        "trending": False,
        "icon": "https://example.com/cr.png"
    },
}

GAME_PRICES = {
    "freefire": [100, 200, 300, 400, 500, 1000, 2000, 5000],
    "ffmax": [100, 200, 300, 400, 500, 1000, 2000, 5000],
    "pubg": [60, 120, 300, 600, 1200, 3000, 6000],
    "bgmi": [60, 120, 300, 600, 1200, 3000, 6000],
    "cod": [80, 160, 400, 800, 1600, 4000],
    "dream11": [50, 100, 200, 500, 1000, 2000],
    "my11circle": [50, 100, 200, 500, 1000, 2000],
    "mobilelegends": [100, 250, 500, 1000, 2500, 5000],
    "clashofclans": [100, 500, 1000, 2000, 5000],
    "clashroyale": [100, 500, 1000, 2000, 5000],
}

# ============================================================================
# MOBILE RECHARGE OPERATORS
# ============================================================================

MOBILE_OPERATORS = {
    "airtel": {
        "id": "airtel",
        "name": "AIRTEL", 
        "emoji": "🔴",
        "full_emoji": "🔴📱",
        "description": "🔴 *Airtel - India's Leading Network*\n\n✅ Prepaid & Postpaid\n✅ 4G/5G data\n✅ Unlimited calls\n✅ SMS benefits\n✅ Weekend rollover\n\n🔥 *Best for:* Prepaid recharges, Data packs",
        "popular": True,
        "plans": [199, 299, 399, 499, 599, 699, 799, 999, 1199, 1499, 1799, 1999, 2399, 2699, 2999]
    },
    "jio": {
        "id": "jio",
        "name": "JIO", 
        "emoji": "🟣",
        "full_emoji": "🟣📱",
        "description": "🟣 *Jio - Digital Life*\n\n✅ Unlimited data\n✅ Jio apps access\n✅ 5G ready\n✅ International calls\n✅ Family plans\n\n🔥 *Best for:* Data packs, JioFiber, Prepaid",
        "popular": True,
        "plans": [149, 249, 349, 449, 549, 599, 699, 799, 899, 999, 1199, 1299, 1499, 1699, 1999, 2399, 2999]
    },
    "vi": {
        "id": "vi",
        "name": "VI", 
        "emoji": "🟢",
        "full_emoji": "🟢📱",
        "description": "🟢 *VI - Vodafone Idea*\n\n✅ Great coverage\n✅ Data rollover\n✅ Weekend data\n✅ International roaming\n✅ Partner offers\n\n🔥 *Best for:* Prepaid, Postpaid, Data packs",
        "popular": True,
        "plans": [199, 299, 399, 499, 599, 699, 799, 899, 999, 1099, 1299, 1499, 1699, 1999, 2299, 2599]
    },
    "bsnl": {
        "id": "bsnl",
        "name": "BSNL", 
        "emoji": "🔵",
        "full_emoji": "🔵📱",
        "description": "🔵 *BSNL - Bharat Sanchar*\n\n✅ Rural coverage\n✅ Affordable plans\n✅ Lifetime validity\n✅ Landline benefits\n✅ Fiber broadband\n\n🔥 *Best for:* Prepaid, Postpaid, Landline",
        "popular": False,
        "plans": [99, 149, 199, 249, 299, 349, 399, 449, 499, 599, 649, 699, 799, 899, 999, 1199]
    },
}

# ============================================================================
# DTH RECHARGE OPERATORS
# ============================================================================

DTH_OPERATORS = {
    "tatasky": {
        "id": "tatasky",
        "name": "TATA SKY", 
        "emoji": "🟠",
        "full_emoji": "🟠📺",
        "description": "🟠 *Tata Sky - Premium DTH*\n\n✅ HD channels\n✅ 4K set-top box\n✅ Recording options\n✅ Multi-TV connection\n✅ International channels\n\n🔥 *Best for:* HD packs, Add-ons, Regional",
        "popular": True,
        "plans": [99, 149, 199, 249, 299, 349, 399, 449, 499, 599, 699, 799, 999, 1199, 1499, 1999]
    },
    "airteldth": {
        "id": "airteldth",
        "name": "AIRTEL DTH", 
        "emoji": "🔴",
        "full_emoji": "🔴📺",
        "description": "🔴 *Airtel Digital TV*\n\n✅ Xstream box\n✅ 4K channels\n✅ OTT apps included\n✅ Recording\n✅ Multi-room\n\n🔥 *Best for:* HD packs, Xstream, OTT",
        "popular": True,
        "plans": [99, 149, 199, 249, 299, 349, 399, 449, 499, 599, 699, 799, 999, 1299, 1599, 1999]
    },
    "dishtv": {
        "id": "dishtv",
        "name": "DISH TV", 
        "emoji": "🟡",
        "full_emoji": "🟡📺",
        "description": "🟡 *Dish TV - Entertainment*\n\n✅ Affordable plans\n✅ HD quality\n✅ Regional channels\n✅ Multi TV\n✅ Add-ons\n\n🔥 *Best for:* Budget packs, Regional, Hindi",
        "popular": True,
        "plans": [99, 149, 199, 249, 299, 349, 399, 449, 499, 599, 699, 799, 899, 999, 1299, 1599]
    },
    "sundirect": {
        "id": "sundirect",
        "name": "SUN DIRECT", 
        "emoji": "🟢",
        "full_emoji": "🟢📺",
        "description": "🟢 *Sun Direct - South India*\n\n✅ Tamil, Telugu, Malayalam\n✅ Kannada channels\n✅ HD quality\n✅ Affordable\n✅ Regional focus\n\n🔥 *Best for:* South Indian channels, Regional",
        "popular": False,
        "plans": [99, 149, 199, 249, 299, 349, 399, 449, 499, 599, 649, 699, 799, 899, 999, 1199]
    },
    "d2h": {
        "id": "d2h",
        "name": "D2H", 
        "emoji": "🔵",
        "full_emoji": "🔵📺",
        "description": "🔵 *d2h - Videocon d2h*\n\n✅ HD channels\n✅ Multi TV\n✅ Recording\n✅ Regional packs\n✅ Add-ons\n\n🔥 *Best for:* HD packs, Regional, Add-ons",
        "popular": False,
        "plans": [99, 149, 199, 249, 299, 349, 399, 449, 499, 599, 699, 799, 999, 1299, 1599]
    },
}

# ============================================================================
# FIBER/BROADBAND RECHARGE
# ============================================================================

FIBER_OPERATORS = {
    "jiofiber": {
        "id": "jiofiber",
        "name": "JIO FIBER", 
        "emoji": "🟣",
        "full_emoji": "🟣🌐",
        "description": "🟣 *JioFiber - Gigabit Internet*\n\n✅ Up to 1 Gbps speed\n✅ Unlimited data\n✅ OTT apps included\n✅ Landline connection\n✅ Jio set-top box\n\n🔥 *Best for:* High-speed, Unlimited, OTT",
        "popular": True,
        "plans": [399, 499, 599, 699, 799, 899, 999, 1299, 1499, 1699, 1999, 2499, 2999, 3999]
    },
    "airtelxstream": {
        "id": "airtelxstream",
        "name": "AIRTEL XSTREAM", 
        "emoji": "🔴",
        "full_emoji": "🔴🌐",
        "description": "🔴 *Airtel Xstream Fiber*\n\n✅ High-speed broadband\n✅ Xstream box\n✅ OTT apps\n✅ Unlimited calls\n✅ Wynk benefits\n\n🔥 *Best for:* Fiber, OTT, High-speed",
        "popular": True,
        "plans": [499, 599, 699, 799, 899, 999, 1299, 1499, 1699, 1999, 2499, 2999, 3999, 4999]
    },
    "bsnlfiber": {
        "id": "bsnlfiber",
        "name": "BSNL FIBER", 
        "emoji": "🔵",
        "full_emoji": "🔵🌐",
        "description": "🔵 *BSNL Bharat Fiber*\n\n✅ Affordable plans\n✅ Good speed\n✅ Unlimited data\n✅ Landline included\n✅ Rural coverage\n\n🔥 *Best for:* Budget, Unlimited, Rural",
        "popular": False,
        "plans": [399, 499, 599, 699, 799, 899, 999, 1299, 1499, 1999, 2499]
    },
    "actfiber": {
        "id": "actfiber",
        "name": "ACT FIBER", 
        "emoji": "🟢",
        "full_emoji": "🟢🌐",
        "description": "🟢 *ACT Fibernet - High Speed*\n\n✅ Up to 1 Gbps\n✅ Low latency\n✅ Gaming optimized\n✅ OTT benefits\n✅ Static IP option\n\n🔥 *Best for:* Gaming, High-speed, Low latency",
        "popular": False,
        "plans": [499, 599, 699, 799, 899, 999, 1299, 1499, 1699, 1999, 2499, 2999, 3999]
    },
    "hathway": {
        "id": "hathway",
        "name": "HATHWAY", 
        "emoji": "🟠",
        "full_emoji": "🟠🌐",
        "description": "🟠 *Hathway - Cable Broadband*\n\n✅ Cable TV + Internet\n✅ Affordable plans\n✅ Good coverage\n✅ TV included\n✅ Multiple packs\n\n🔥 *Best for:* Cable + Internet, Budget",
        "popular": False,
        "plans": [399, 499, 599, 699, 799, 999, 1299, 1499, 1999]
    },
}

# ============================================================================
# DAILY REWARDS CONFIGURATION
# ============================================================================

DAILY_REWARDS = {
    1: 5,
    2: 8,
    3: 10,
    4: 12,
    5: 15,
    6: 18,
    7: 25,
    10: 40,
    15: 60,
    20: 80,
    25: 100,
    30: 150,
    45: 250,
    60: 400,
    90: 600,
    120: 1000,
    180: 1500,
    365: 2500
}

# ============================================================================
# BULK DISCOUNTS CONFIGURATION
# ============================================================================

BULK_DISCOUNTS = {
    1: 0,
    2: 2,
    3: 5,
    4: 7,
    5: 10,
    10: 15,
    15: 18,
    20: 20,
    25: 22,
    30: 25,
    50: 30,
    75: 32,
    100: 35
}

# ============================================================================
# AMOUNT BUTTONS FOR RECHARGE
# ============================================================================

AMOUNT_BUTTONS = [
    [10, 20, 30, 50],
    [100, 200, 300, 500],
    [1000, 2000, 5000, 10000],
    [20000, 50000, 100000]
]

# ============================================================================
# WALLET TRANSFER CONFIGURATION
# ============================================================================

WALLET_TRANSFER_MIN = 10
WALLET_TRANSFER_MAX = 100000
WALLET_TRANSFER_FEE = 2  # 2%
WALLET_TRANSFER_DAILY_LIMIT = 50000

# ============================================================================
# MYSTERY BOX CONFIGURATION
# ============================================================================

MYSTERY_BOX_PRICES = [50, 100, 200, 500, 1000]
MYSTERY_BOX_MULTIPLIERS = {
    50: {"min": 25, "max": 250, "jackpot": 500},
    100: {"min": 50, "max": 500, "jackpot": 1000},
    200: {"min": 100, "max": 1000, "jackpot": 2000},
    500: {"min": 250, "max": 2500, "jackpot": 5000},
    1000: {"min": 500, "max": 5000, "jackpot": 10000}
}

# ============================================================================
# CARD EXCHANGE CONFIGURATION
# ============================================================================

CARD_EXCHANGE_FEE = 3  # 3%
CARD_EXCHANGE_RATES = {
    "small": {"from": 500, "to": 1000, "ratio": 2.1, "bonus": 50},
    "medium": {"from": 1000, "to": 2000, "ratio": 2.1, "bonus": 100},
    "large": {"from": 2000, "to": 5000, "ratio": 2.5, "bonus": 250},
    "xl": {"from": 5000, "to": 10000, "ratio": 2.0, "bonus": 500},
    "xxl": {"from": 10000, "to": 25000, "ratio": 2.5, "bonus": 1250}
}

# ============================================================================
# CONVERSATION STATES - PREMIUM EDITION
# ============================================================================

    # Authentication States
    STATE_VERIFY,
    STATE_LOGIN,
    STATE_REGISTER,
    STATE_2FA,
    
    # Payment States
    STATE_SCREENSHOT,
    STATE_UTR,
    STATE_PAYMENT_CONFIRM,
    STATE_PAYMENT_METHOD,
    STATE_CRYPTO_ADDRESS,
    STATE_CRYPTO_AMOUNT,
    STATE_BANK_DETAILS,
    
    # Purchase States
    STATE_EMAIL,
    STATE_PHONE,
    STATE_ADDRESS,
    STATE_GIFT_MESSAGE,
    STATE_RECIPIENT_NAME,
    STATE_RECIPIENT_EMAIL,
    STATE_DELIVERY_DATE,
    
    # Recharge States
    STATE_MOBILE_NUMBER,
    STATE_MOBILE_OPERATOR,
    STATE_MOBILE_PLAN,
    STATE_DTH_NUMBER,
    STATE_DTH_OPERATOR,
    STATE_DTH_PLAN,
    STATE_FIBER_NUMBER,
    STATE_FIBER_OPERATOR,
    STATE_FIBER_PLAN,
    STATE_GAME_ID,
    STATE_GAME_SERVER,
    STATE_GAME_AMOUNT,
    
    # Wallet States
    STATE_WALLET_TRANSFER_USERNAME,
    STATE_WALLET_TRANSFER_AMOUNT,
    STATE_WALLET_TRANSFER_CONFIRM,
    STATE_WALLET_WITHDRAW_AMOUNT,
    STATE_WALLET_WITHDRAW_METHOD,
    STATE_WALLET_WITHDRAW_DETAILS,
    
    # Mystery Box States
    STATE_MYSTERY_BOX_SELECT,
    STATE_MYSTERY_BOX_OPEN,
    STATE_MYSTERY_BOX_RESULT,
    
    # Exchange States
    STATE_CARD_EXCHANGE_FROM,
    STATE_CARD_EXCHANGE_TO,
    STATE_CARD_EXCHANGE_QUANTITY,
    STATE_CARD_EXCHANGE_CONFIRM,
    
    # Alert States
    STATE_PRICE_ALERT_CARD,
    STATE_PRICE_ALERT_PRICE,
    STATE_PRICE_ALERT_NOTIFY,
    
    # Coupon States
    STATE_COUPON_ENTER,
    STATE_COUPON_VERIFY,
    
    # Bulk States
    STATE_BULK_CARD,
    STATE_BULK_QUANTITY,
    STATE_BULK_CONFIRM,
    
    # Support States
    STATE_SUPPORT_MESSAGE,
    STATE_SUPPORT_CATEGORY,
    STATE_SUPPORT_PRIORITY,
    STATE_SUPPORT_ATTACHMENT,
    
    # Admin States
    STATE_ADMIN_BROADCAST,
    STATE_ADMIN_ANNOUNCEMENT,
    STATE_ADMIN_ADD_CARD,
    STATE_ADMIN_UPDATE_CARD,
    STATE_ADMIN_REMOVE_CARD,
    STATE_ADMIN_ADD_STOCK,
    STATE_ADMIN_UPDATE_STOCK,
    STATE_ADMIN_ADD_PRICE,
    STATE_ADMIN_UPDATE_PRICE,
    STATE_ADMIN_ADD_COUPON,
    STATE_ADMIN_UPDATE_COUPON,
    STATE_ADMIN_REMOVE_COUPON,
    STATE_ADMIN_BAN_USER,
    STATE_ADMIN_UNBAN_USER,
    STATE_ADMIN_ADD_BALANCE,
    STATE_ADMIN_REMOVE_BALANCE,
    STATE_ADMIN_ADD_ADMIN,
    STATE_ADMIN_REMOVE_ADMIN,
    STATE_ADMIN_VIEW_LOGS,
    STATE_ADMIN_EXPORT_DATA,
    STATE_ADMIN_BACKUP_DB,
    STATE_ADMIN_RESTORE_DB,
    STATE_ADMIN_SETTINGS,
    STATE_ADMIN_MAINTENANCE,
) = range(100)

# ============================================================================
# PREMIUM DATABASE MANAGER
# ============================================================================

class PremiumDatabase:
    """Enterprise-grade database manager with connection pooling, caching, and backup"""
    
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self.pool = Queue(maxsize=pool_size)
        self.cache = OrderedDict()
        self.cache_lock = threading.Lock()
        self.cache_max_size = 1000
        self.cache_ttl = 300  # 5 minutes
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize connection pool
        self._init_pool()
        
        # Initialize database schema
        self._init_schema()
        
        # Start backup thread
        self._start_auto_backup()
        
        logger.success(f"✅ Premium Database initialized with {pool_size} connections")
    
    def _init_pool(self):
        """Initialize connection pool"""
        for i in range(self.pool_size):
            try:
                conn = sqlite3.connect(self.db_path, timeout=30, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA foreign_keys=ON")
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA temp_store=MEMORY")
                conn.execute("PRAGMA mmap_size=30000000000")
                self.pool.put(conn)
                logger.debug(f"✅ Connection {i+1} added to pool")
            except Exception as e:
                logger.error(f"❌ Failed to create connection: {e}")
                raise
    
    def _init_schema(self):
        """Initialize database schema with all tables"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            
            # ========================================================================
            # USERS TABLE - COMPLETE USER MANAGEMENT
            # ========================================================================
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    phone TEXT,
                    email TEXT,
                    birth_date DATE,
                    anniversary_date DATE,
                    
                    -- Balances
                    balance_main INTEGER DEFAULT 0,
                    balance_bonus INTEGER DEFAULT 0,
                    balance_locked INTEGER DEFAULT 0,
                    
                    -- Statistics
                    total_recharged INTEGER DEFAULT 0,
                    total_spent INTEGER DEFAULT 0,
                    total_purchases INTEGER DEFAULT 0,
                    total_referrals INTEGER DEFAULT 0,
                    total_withdrawn INTEGER DEFAULT 0,
                    
                    -- Referral
                    referral_code TEXT UNIQUE,
                    referred_by INTEGER,
                    
                    -- Status
                    is_active INTEGER DEFAULT 1,
                    is_banned INTEGER DEFAULT 0,
                    ban_reason TEXT,
                    ban_expires TIMESTAMP,
                    
                    -- Role
                    role TEXT DEFAULT 'user',
                    permissions TEXT DEFAULT '{}',
                    
                    -- Preferences
                    language TEXT DEFAULT 'en',
                    currency TEXT DEFAULT 'INR',
                    notification_settings TEXT DEFAULT '{"email":true,"telegram":true}',
                    
                    -- Gaming
                    game_ids TEXT DEFAULT '{}',
                    
                    -- Security
                    two_factor_enabled INTEGER DEFAULT 0,
                    two_factor_secret TEXT,
                    last_login TIMESTAMP,
                    last_ip TEXT,
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Metadata
                    metadata TEXT DEFAULT '{}',
                    
                    FOREIGN KEY (referred_by) REFERENCES users(user_id)
                )
            ''')
            
            # Create indexes
            c.execute("CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_users_referral ON users(referral_code)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_users_status ON users(is_active)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active)")
            
            # ========================================================================
            # TRANSACTIONS TABLE - COMPLETE FINANCIAL TRACKING
            # ========================================================================
            c.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    
                    -- Transaction Details
                    amount INTEGER NOT NULL,
                    fee INTEGER DEFAULT 0,
                    final_amount INTEGER NOT NULL,
                    currency TEXT DEFAULT 'INR',
                    
                    -- Type & Status
                    type TEXT NOT NULL,
                    category TEXT,
                    status TEXT DEFAULT 'pending',
                    
                    -- Payment
                    payment_method TEXT,
                    payment_details TEXT,
                    utr TEXT UNIQUE,
                    screenshot TEXT,
                    
                    -- Reference
                    reference_id TEXT,
                    reference_type TEXT,
                    
                    -- Description
                    description TEXT,
                    notes TEXT,
                    
                    -- Admin
                    approved_by INTEGER,
                    approved_at TIMESTAMP,
                    rejection_reason TEXT,
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (approved_by) REFERENCES users(user_id)
                )
            ''')
            
            # Indexes
            c.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_transactions_utr ON transactions(utr)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_transactions_created ON transactions(created_at)")
            
            # ========================================================================
            # PURCHASES TABLE - GIFT CARD & RECHARGE PURCHASES
            # ========================================================================
            c.execute('''
                CREATE TABLE IF NOT EXISTS purchases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    
                    -- Item Details
                    item_type TEXT NOT NULL,
                    item_category TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    item_name TEXT NOT NULL,
                    item_emoji TEXT,
                    
                    -- Value
                    face_value INTEGER NOT NULL,
                    quantity INTEGER DEFAULT 1,
                    unit_price INTEGER NOT NULL,
                    total_price INTEGER NOT NULL,
                    discount INTEGER DEFAULT 0,
                    coupon_code TEXT,
                    
                    -- Delivery
                    email TEXT,
                    phone TEXT,
                    recipient_name TEXT,
                    recipient_email TEXT,
                    gift_message TEXT,
                    scheduled_date DATE,
                    
                    -- Gaming
                    game_id TEXT,
                    game_server TEXT,
                    
                    -- Status
                    status TEXT DEFAULT 'pending',
                    delivery_status TEXT DEFAULT 'pending',
                    proof_sent INTEGER DEFAULT 0,
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    delivered_at TIMESTAMP,
                    
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Indexes
            c.execute("CREATE INDEX IF NOT EXISTS idx_purchases_user ON purchases(user_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_purchases_order ON purchases(order_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_purchases_item ON purchases(item_type, item_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_purchases_status ON purchases(status)")
            
            # ========================================================================
            # VERIFICATIONS TABLE - PAYMENT VERIFICATION REQUESTS
            # ========================================================================
            c.execute('''
                CREATE TABLE IF NOT EXISTS verifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    verification_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    
                    -- Payment Details
                    amount INTEGER NOT NULL,
                    fee INTEGER DEFAULT 0,
                    final_amount INTEGER NOT NULL,
                    utr TEXT UNIQUE,
                    screenshot TEXT,
                    
                    -- Status
                    status TEXT DEFAULT 'pending',
                    
                    -- Admin
                    admin_id INTEGER,
                    admin_note TEXT,
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    verified_at TIMESTAMP,
                    
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (admin_id) REFERENCES users(user_id)
                )
            ''')
            
            # Indexes
            c.execute("CREATE INDEX IF NOT EXISTS idx_verifications_user ON verifications(user_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_verifications_status ON verifications(status)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_verifications_utr ON verifications(utr)")
            
            # ========================================================================
            # REFERRALS TABLE - COMPLETE REFERRAL TRACKING
            # ========================================================================
            c.execute('''
                CREATE TABLE IF NOT EXISTS referrals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    referrer_id INTEGER NOT NULL,
                    referred_id INTEGER NOT NULL UNIQUE,
                    
                    -- Bonus
                    bonus_amount INTEGER DEFAULT 5,
                    bonus_paid INTEGER DEFAULT 0,
                    
                    -- Status
                    status TEXT DEFAULT 'pending',
                    
                    -- Conditions
                    referred_purchased INTEGER DEFAULT 0,
                    referred_recharged INTEGER DEFAULT 0,
                    min_purchase INTEGER DEFAULT 0,
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    bonus_paid_at TIMESTAMP,
                    
                    FOREIGN KEY (referrer_id) REFERENCES users(user_id),
                    FOREIGN KEY (referred_id) REFERENCES users(user_id)
                )
            ''')
            
            # Indexes
            c.execute("CREATE INDEX IF NOT EXISTS idx_referrals_referrer ON referrals(referrer_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_referrals_status ON referrals(status)")
            
            # ========================================================================
            # DAILY REWARDS TABLE - STREAK TRACKING
            # ========================================================================
            c.execute('''
                CREATE TABLE IF NOT EXISTS daily_rewards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    claim_date DATE NOT NULL,
                    streak INTEGER DEFAULT 1,
                    amount INTEGER NOT NULL,
                    bonus_amount INTEGER DEFAULT 0,
                    claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, claim_date),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # Indexes
            c.execute("CREATE INDEX IF NOT EXISTS idx_daily_user ON daily_rewards(user_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_daily_date ON daily_rewards(claim_date)")
            
            # ========================================================================
            # COUPONS MASTER TABLE
            # ========================================================================
            c.execute('''
                CREATE TABLE IF NOT EXISTS coupons_master (
                    code TEXT PRIMARY KEY,
                    name TEXT,
                    description TEXT,
                    
                    -- Discount
                    discount_type TEXT NOT NULL,
                    discount_value INTEGER NOT NULL,
                    min_purchase INTEGER DEFAULT 0,
                    max_discount INTEGER,
                    
                    -- Usage
                    max_uses INTEGER DEFAULT 999999,
                    used_count INTEGER DEFAULT 0,
                    per_user_limit INTEGER DEFAULT 1,
                    
                    -- Validity
                    valid_from TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    valid_until TIMESTAMP,
                    
                    -- Eligibility
                    user_role TEXT,
                    first_purchase_only INTEGER DEFAULT 0,
                    
                    -- Status
                    is_active INTEGER DEFAULT 1,
                    
                    -- Metadata
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # ========================================================================
            # COUPON USAGE TABLE
            # ========================================================================
            c.execute('''
                CREATE TABLE IF NOT EXISTS coupon_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL,
                    user_id INTEGER NOT NULL,
                    order_id TEXT,
                    discount_amount INTEGER,
                    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (code) REFERENCES coupons_master(code),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            c.execute("CREATE INDEX IF NOT EXISTS idx_coupon_usage_user ON coupon_usage(user_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_coupon_usage_code ON coupon_usage(code)")
            
            # ========================================================================
            # PRICE ALERTS TABLE
            # ========================================================================
            c.execute('''
                CREATE TABLE IF NOT EXISTS price_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    
                    -- Alert Details
                    item_type TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    item_name TEXT,
                    target_price INTEGER NOT NULL,
                    current_price INTEGER,
                    
                    -- Status
                    is_active INTEGER DEFAULT 1,
                    is_triggered INTEGER DEFAULT 0,
                    
                    -- Notification
                    notify_email INTEGER DEFAULT 0,
                    notify_telegram INTEGER DEFAULT 1,
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    triggered_at TIMESTAMP,
                    
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            c.execute("CREATE INDEX IF NOT EXISTS idx_alerts_user ON price_alerts(user_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_alerts_item ON price_alerts(item_type, item_id)")
            
            # ========================================================================
            # MYSTERY BOX LOGS TABLE
            # ========================================================================
            c.execute('''
                CREATE TABLE IF NOT EXISTS mystery_box_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    
                    -- Box Details
                    box_price INTEGER NOT NULL,
                    won_amount INTEGER NOT NULL,
                    profit_loss INTEGER NOT NULL,
                    
                    -- Multiplier
                    multiplier REAL,
                    was_jackpot INTEGER DEFAULT 0,
                    
                    -- Timestamp
                    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            c.execute("CREATE INDEX IF NOT EXISTS idx_mystery_user ON mystery_box_logs(user_id)")
            
            # ========================================================================
            # WALLET TRANSFERS TABLE
            # ========================================================================
            c.execute('''
                CREATE TABLE IF NOT EXISTS wallet_transfers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transfer_id TEXT UNIQUE NOT NULL,
                    from_user INTEGER NOT NULL,
                    to_user INTEGER NOT NULL,
                    
                    -- Transfer Details
                    amount INTEGER NOT NULL,
                    fee INTEGER DEFAULT 0,
                    final_amount INTEGER NOT NULL,
                    
                    -- Status
                    status TEXT DEFAULT 'completed',
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (from_user) REFERENCES users(user_id),
                    FOREIGN KEY (to_user) REFERENCES users(user_id)
                )
            ''')
            
            c.execute("CREATE INDEX IF NOT EXISTS idx_transfers_from ON wallet_transfers(from_user)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_transfers_to ON wallet_transfers(to_user)")
            
            # ========================================================================
            # CARD EXCHANGE LOGS TABLE
            # ========================================================================
            c.execute('''
                CREATE TABLE IF NOT EXISTS card_exchange_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    
                    -- Exchange Details
                    from_cards TEXT NOT NULL,
                    to_card TEXT NOT NULL,
                    from_value INTEGER NOT NULL,
                    to_value INTEGER NOT NULL,
                    fee INTEGER NOT NULL,
                    
                    -- Timestamp
                    exchanged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            # ========================================================================
            # SUPPORT TICKETS TABLE
            # ========================================================================
            c.execute('''
                CREATE TABLE IF NOT EXISTS support_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticket_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    
                    -- Ticket Details
                    category TEXT,
                    subject TEXT,
                    message TEXT NOT NULL,
                    priority INTEGER DEFAULT 1,
                    
                    -- Status
                    status TEXT DEFAULT 'open',
                    
                    -- Admin
                    assigned_to INTEGER,
                    response TEXT,
                    response_time TIMESTAMP,
                    
                    -- Attachments
                    attachments TEXT,
                    
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (assigned_to) REFERENCES users(user_id)
                )
            ''')
            
            c.execute("CREATE INDEX IF NOT EXISTS idx_tickets_user ON support_tickets(user_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_tickets_status ON support_tickets(status)")
            
            # ========================================================================
            # GIFT CARD STOCK TABLE
            # ========================================================================
            c.execute('''
                CREATE TABLE IF NOT EXISTS gift_stock (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    card_id TEXT NOT NULL,
                    denomination INTEGER NOT NULL,
                    
                    -- Stock Levels
                    stock INTEGER DEFAULT 0,
                    reserved INTEGER DEFAULT 0,
                    available INTEGER DEFAULT 0,
                    
                    -- Alerts
                    low_alert INTEGER DEFAULT 10,
                    critical_alert INTEGER DEFAULT 5,
                    
                    -- Pricing
                    base_price INTEGER,
                    selling_price INTEGER,
                    
                    -- Status
                    is_active INTEGER DEFAULT 1,
                    
                    -- Metadata
                    last_restocked TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    UNIQUE(card_id, denomination)
                )
            ''')
            
            c.execute("CREATE INDEX IF NOT EXISTS idx_stock_card ON gift_stock(card_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_stock_level ON gift_stock(stock)")
            
            # ========================================================================
            # GAME STOCK TABLE
            # ========================================================================
            c.execute('''
                CREATE TABLE IF NOT EXISTS game_stock (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    
                    -- Stock Levels
                    stock INTEGER DEFAULT 0,
                    reserved INTEGER DEFAULT 0,
                    available INTEGER DEFAULT 0,
                    
                    -- Alerts
                    low_alert INTEGER DEFAULT 10,
                    critical_alert INTEGER DEFAULT 5,
                    
                    -- Pricing
                    selling_price INTEGER,
                    
                    -- Status
                    is_active INTEGER DEFAULT 1,
                    
                    -- Timestamps
                    last_restocked TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    UNIQUE(game_id, amount)
                )
            ''')
            
            # ========================================================================
            # ADMIN LOGS TABLE
            # ========================================================================
            c.execute('''
                CREATE TABLE IF NOT EXISTS admin_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER NOT NULL,
                    
                    -- Action
                    action TEXT NOT NULL,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    
                    -- Target
                    target_user INTEGER,
                    target_id TEXT,
                    
                    -- Metadata
                    metadata TEXT,
                    
                    -- Timestamp
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (admin_id) REFERENCES users(user_id),
                    FOREIGN KEY (target_user) REFERENCES users(user_id)
                )
            ''')
            
            c.execute("CREATE INDEX IF NOT EXISTS idx_admin_logs_admin ON admin_logs(admin_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_admin_logs_action ON admin_logs(action)")
            
            # ========================================================================
            # NOTIFICATIONS TABLE
            # ========================================================================
            c.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    
                    -- Notification
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    type TEXT DEFAULT 'info',
                    priority INTEGER DEFAULT 1,
                    
                    -- Action
                    action_url TEXT,
                    action_data TEXT,
                    
                    -- Status
                    is_read INTEGER DEFAULT 0,
                    read_at TIMESTAMP,
                    
                    -- Expiry
                    expires_at TIMESTAMP,
                    
                    -- Timestamp
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            
            c.execute("CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read)")
            
            # ========================================================================
            # BANNED USERS TABLE
            # ========================================================================
            c.execute('''
                CREATE TABLE IF NOT EXISTS banned_users (
                    user_id INTEGER PRIMARY KEY,
                    reason TEXT,
                    banned_by INTEGER,
                    ban_type TEXT DEFAULT 'permanent',
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (banned_by) REFERENCES users(user_id)
                )
            ''')
            
            # ========================================================================
            # SETTINGS TABLE
            # ========================================================================
            c.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    type TEXT DEFAULT 'string',
                    description TEXT,
                    is_public INTEGER DEFAULT 0,
                    updated_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insert default settings
            default_settings = [
                ('bot_name', '🎁 Ultimate Gift Card Bot', 'string', 'Bot display name', 1),
                ('bot_version', '5.0.0', 'string', 'Bot version', 1),
                ('min_recharge', str(MIN_RECHARGE), 'int', 'Minimum recharge amount', 0),
                ('max_recharge', str(MAX_RECHARGE), 'int', 'Maximum recharge amount', 0),
                ('fee_percent', str(FEE_PERCENT), 'int', 'Fee percentage', 0),
                ('fee_threshold', str(FEE_THRESHOLD), 'int', 'Fee threshold', 0),
                ('referral_bonus', str(REFERRAL_BONUS), 'int', 'Referral bonus amount', 1),
                ('welcome_bonus', str(WELCOME_BONUS), 'int', 'Welcome bonus amount', 1),
                ('daily_login_bonus', str(DAILY_LOGIN_BONUS), 'int', 'Daily login bonus', 1),
                ('maintenance_mode', '0', 'bool', 'Maintenance mode', 0),
                ('maintenance_message', 'Bot under maintenance', 'text', 'Maintenance message', 0),
                ('require_channel_join', '1', 'bool', 'Require channel join', 0),
                ('require_phone_verification', '0', 'bool', 'Require phone verification', 0),
                ('require_email_verification', '0', 'bool', 'Require email verification', 0),
                ('enable_referrals', '1', 'bool', 'Enable referral system', 1),
                ('enable_daily_rewards', '1', 'bool', 'Enable daily rewards', 1),
                ('enable_coupons', '1', 'bool', 'Enable coupon system', 1),
                ('enable_mystery_box', '1', 'bool', 'Enable mystery box', 1),
                ('enable_wallet_transfer', '1', 'bool', 'Enable wallet transfer', 1),
                ('enable_card_exchange', '1', 'bool', 'Enable card exchange', 1),
                ('enable_price_alerts', '1', 'bool', 'Enable price alerts', 1),
                ('enable_bulk_purchase', '1', 'bool', 'Enable bulk purchase', 1),
                ('enable_gift_sending', '1', 'bool', 'Enable gift sending', 1),
                ('contact_email', 'support@giftcardbot.com', 'string', 'Contact email', 1),
                ('contact_website', 'www.giftcardbot.com', 'string', 'Website', 1),
                ('currency_symbol', '₹', 'string', 'Currency symbol', 1),
                ('currency_code', 'INR', 'string', 'Currency code', 1),
                ('timezone', 'Asia/Kolkata', 'string', 'Timezone', 0),
                ('language_default', 'en', 'string', 'Default language', 1),
                ('theme_default', 'dark', 'string', 'Default theme', 1),
            ]
            
            for key, value, type_, desc, is_public in default_settings:
                c.execute('''
                    INSERT OR IGNORE INTO settings (key, value, type, description, is_public)
                    VALUES (?, ?, ?, ?, ?)
                ''', (key, value, type_, desc, is_public))
            
            # ========================================================================
            # STATISTICS TABLE
            # ========================================================================
            c.execute('''
                CREATE TABLE IF NOT EXISTS statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE NOT NULL,
                    
                    -- User Stats
                    new_users INTEGER DEFAULT 0,
                    active_users INTEGER DEFAULT 0,
                    total_users INTEGER DEFAULT 0,
                    
                    -- Transaction Stats
                    total_transactions INTEGER DEFAULT 0,
                    successful_transactions INTEGER DEFAULT 0,
                    failed_transactions INTEGER DEFAULT 0,
                    
                    -- Revenue Stats
                    total_revenue INTEGER DEFAULT 0,
                    revenue_today INTEGER DEFAULT 0,
                    avg_transaction_value INTEGER DEFAULT 0,
                    
                    -- Purchase Stats
                    total_purchases INTEGER DEFAULT 0,
                    gift_cards_sold INTEGER DEFAULT 0,
                    game_recharges INTEGER DEFAULT 0,
                    mobile_recharges INTEGER DEFAULT 0,
                    
                    -- Referral Stats
                    new_referrals INTEGER DEFAULT 0,
                    referral_bonus_paid INTEGER DEFAULT 0,
                    
                    -- System Stats
                    api_calls INTEGER DEFAULT 0,
                    errors_count INTEGER DEFAULT 0,
                    
                    -- Metadata
                    metadata TEXT DEFAULT '{}',
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            c.execute("CREATE INDEX IF NOT EXISTS idx_stats_date ON statistics(date)")
            
            conn.commit()
            logger.success("✅ Premium database schema initialized")
            
        except Exception as e:
            logger.error(f"❌ Database schema initialization failed: {e}")
            raise
        finally:
            self.release_connection(conn)
    
    def _start_auto_backup(self):
        """Start automatic backup thread"""
        def backup_worker():
            while True:
                time.sleep(3600)  # Backup every hour
                try:
                    self.create_backup()
                except Exception as e:
                    logger.error(f"❌ Auto backup failed: {e}")
        
        thread = threading.Thread(target=backup_worker, daemon=True)
        thread.start()
        logger.info("✅ Auto backup thread started")
    
    def get_connection(self):
        """Get a connection from the pool"""
        return self.pool.get()
    
    def release_connection(self, conn):
        """Return connection to pool"""
        self.pool.put(conn)
    
    def execute(self, query: str, params: tuple = (), fetchone: bool = False, 
                fetchall: bool = False, commit: bool = False):
        """Execute a database query"""
        conn = self.get_connection()
        try:
            c = conn.cursor()
            c.execute(query, params)
            
            if commit:
                conn.commit()
                return c.lastrowid
            
            if fetchone:
                result = c.fetchone()
                return dict(result) if result else None
            
            if fetchall:
                results = c.fetchall()
                return [dict(row) for row in results] if results else []
            
            return c.rowcount
            
        except Exception as e:
            conn.rollback()
            logger.error(f"❌ Database error: {e}")
            raise
        finally:
            self.release_connection(conn)
    
    def get_cached(self, key: str, fetch_func):
        """Get data from cache or fetch and cache"""
        with self.cache_lock:
            # Check cache
            if key in self.cache:
                data, timestamp = self.cache[key]
                if time.time() - timestamp < self.cache_ttl:
                    return data
                else:
                    del self.cache[key]
            
            # Fetch data
            data = fetch_func()
            
            # Cache data
            self.cache[key] = (data, time.time())
            
            # Maintain cache size
            if len(self.cache) > self.cache_max_size:
                self.cache.popitem(last=False)
            
            return data
    
    def invalidate_cache(self, key: str = None):
        """Invalidate cache"""
        with self.cache_lock:
            if key:
                self.cache.pop(key, None)
            else:
                self.cache.clear()
    
    def create_backup(self) -> str:
        """Create database backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f"backup_{timestamp}.db"
        
        conn = self.get_connection()
        try:
            backup_conn = sqlite3.connect(backup_path)
            conn.backup(backup_conn)
            backup_conn.close()
            logger.success(f"✅ Database backup created: {backup_path}")
            
            # Keep only last 10 backups
            backups = sorted(self.backup_dir.glob("backup_*.db"))
            if len(backups) > 10:
                for backup in backups[:-10]:
                    backup.unlink()
                    logger.info(f"🗑️ Removed old backup: {backup}")
            
            return str(backup_path)
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            raise
        finally:
            self.release_connection(conn)
    
    def restore_backup(self, backup_path: str) -> bool:
        """Restore database from backup"""
        if not os.path.exists(backup_path):
            logger.error(f"❌ Backup file not found: {backup_path}")
            return False
        
        # Close all connections
        while not self.pool.empty():
            conn = self.pool.get()
            conn.close()
        
        try:
            # Restore backup
            shutil.copy2(backup_path, self.db_path)
            logger.success(f"✅ Database restored from: {backup_path}")
            
            # Reinitialize pool
            self._init_pool()
            return True
        except Exception as e:
            logger.error(f"❌ Restore failed: {e}")
            return False
    
    def close_all(self):
        """Close all database connections"""
        while not self.pool.empty():
            conn = self.pool.get()
            conn.close()
        logger.info("✅ All database connections closed")

# Initialize database
db = PremiumDatabase(DATABASE_PATH)

# ============================================================================
# PREMIUM UI COMPONENTS
# ============================================================================

class PremiumUI:
    """Premium UI components with animations and styling"""
    
    # Unicode box drawing characters
    BOX = {
        'tl': '╔', 'tr': '╗', 'bl': '╚', 'br': '╝',
        'h': '═', 'v': '║',
        'tm': '╦', 'bm': '╩', 'lm': '╠', 'rm': '╣',
        'cross': '╬'
    }
    
    # Gradient colors (for HTML/CSS)
    GRADIENTS = {
        'gold': 'linear-gradient(45deg, #FFD700, #FFA500)',
        'silver': 'linear-gradient(45deg, #C0C0C0, #A0A0A0)',
        'bronze': 'linear-gradient(45deg, #CD7F32, #B87333)',
        'premium': 'linear-gradient(45deg, #4B0082, #9400D3)',
        'success': 'linear-gradient(45deg, #00FF00, #008000)',
        'warning': 'linear-gradient(45deg, #FFFF00, #FFA500)',
        'error': 'linear-gradient(45deg, #FF0000, #8B0000)',
        'info': 'linear-gradient(45deg, #00FFFF, #0000FF)'
    }
    
    # Animation frames
    ANIMATION_FRAMES = {
        'loading': ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷'],
        'spinner': ['◴', '◷', '◶', '◵'],
        'pulse': ['█', '▓', '▒', '░'],
        'wave': ['🌊', '🏄', '🌊', '🏄'],
        'fire': ['🔥', '✨', '🔥', '✨'],
        'gift': ['🎁', '🎀', '🎁', '🎀'],
        'money': ['💰', '💸', '💰', '💸'],
        'star': ['⭐', '🌟', '⭐', '🌟']
    }
    
    @staticmethod
    def box(title: str, width: int = 40, style: str = 'normal') -> str:
        """Create a box with title"""
        if style == 'double':
            tl, tr, bl, br, h, v = '╔', '╗', '╚', '╝', '═', '║'
        elif style == 'rounded':
            tl, tr, bl, br, h, v = '╭', '╮', '╰', '╯', '─', '│'
        else:
            tl, tr, bl, br, h, v = '┌', '┐', '└', '┘', '─', '│'
        
        title_line = f"{v}  {title}  {v}".center(width)
        top = f"{tl}{h * (width-2)}{tr}"
        middle = title_line
        bottom = f"{bl}{h * (width-2)}{br}"
        
        return f"<pre>{top}\n{middle}\n{bottom}</pre>"
    
    @staticmethod
    def gradient_text(text: str, gradient: str = 'gold') -> str:
        """Create gradient text (HTML)"""
        return f'<span style="background: {PremiumUI.GRADIENTS.get(gradient, gradient)}; -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{text}</span>'
    
    @staticmethod
    def progress_bar(current: int, total: int, width: int = 20, 
                     filled_char: str = '█', empty_char: str = '░') -> str:
        """Create a progress bar"""
        if total == 0:
            percentage = 0
            filled = 0
        else:
            percentage = int((current / total) * 100)
            filled = int((current / total) * width)
        
        bar = filled_char * filled + empty_char * (width - filled)
        return f"<code>{bar}</code> <b>{percentage}%</b>"
    
    @staticmethod
    def user_card(user, stats: dict = None) -> str:
        """Create a user profile card"""
        card = [
            f"{PremiumUI.BOX['tl']}{PremiumUI.BOX['h'] * 38}{PremiumUI.BOX['tr']}",
            f"{PremiumUI.BOX['v']}  👤 {user.get('first_name', 'User')} {user_badge(user.get('total_purchases', 0))}  {PremiumUI.BOX['v']}",
            f"{PremiumUI.BOX['lm']}{PremiumUI.BOX['h'] * 38}{PremiumUI.BOX['rm']}",
            f"{PremiumUI.BOX['v']}  🆔 ID: {user.get('user_id', 'N/A')}  {PremiumUI.BOX['v']}",
            f"{PremiumUI.BOX['v']}  📱 Username: @{user.get('username', 'N/A')}  {PremiumUI.BOX['v']}",
            f"{PremiumUI.BOX['v']}  📧 Email: {user.get('email', 'Not set')}  {PremiumUI.BOX['v']}",
            f"{PremiumUI.BOX['lm']}{PremiumUI.BOX['h'] * 38}{PremiumUI.BOX['rm']}",
            f"{PremiumUI.BOX['v']}  💰 Main Balance: {format_currency(user.get('balance_main', 0))}  {PremiumUI.BOX['v']}",
            f"{PremiumUI.BOX['v']}  🎁 Bonus Balance: {format_currency(user.get('balance_bonus', 0))}  {PremiumUI.BOX['v']}",
            f"{PremiumUI.BOX['v']}  💎 Total: {format_currency(user.get('balance_main', 0) + user.get('balance_bonus', 0))}  {PremiumUI.BOX['v']}",
            f"{PremiumUI.BOX['lm']}{PremiumUI.BOX['h'] * 38}{PremiumUI.BOX['rm']}",
            f"{PremiumUI.BOX['v']}  🛒 Purchases: {user.get('total_purchases', 0)}  {PremiumUI.BOX['v']}",
            f"{PremiumUI.BOX['v']}  👥 Referrals: {user.get('total_referrals', 0)}  {PremiumUI.BOX['v']}",
            f"{PremiumUI.BOX['v']}  📅 Joined: {user.get('created_at', 'N/A')[:10]}  {PremiumUI.BOX['v']}",
            f"{PremiumUI.BOX['bl']}{PremiumUI.BOX['h'] * 38}{PremiumUI.BOX['br']}"
        ]
        return "\n".join(card)
    
    @staticmethod
    def product_card(product: dict) -> str:
        """Create a product card"""
        card = [
            f"{PremiumUI.BOX['tl']}{PremiumUI.BOX['h'] * 48}{PremiumUI.BOX['tr']}",
            f"{PremiumUI.BOX['v']}  {product.get('full_emoji', '🎁')} {product.get('name', 'Product')}  {PremiumUI.BOX['v']}".ljust(50),
            f"{PremiumUI.BOX['lm']}{PremiumUI.BOX['h'] * 48}{PremiumUI.BOX['rm']}",
            f"{PremiumUI.BOX['v']}  {product.get('description', '')[:46]}  {PremiumUI.BOX['v']}",
            f"{PremiumUI.BOX['lm']}{PremiumUI.BOX['h'] * 48}{PremiumUI.BOX['rm']}",
            f"{PremiumUI.BOX['v']}  ⭐ Rating: {product.get('rating', 0)}/5 ({product.get('reviews', 0)} reviews)  {PremiumUI.BOX['v']}",
            f"{PremiumUI.BOX['v']}  🔥 Popular: {'Yes' if product.get('popular') else 'No'}  |  📈 Trending: {'Yes' if product.get('trending') else 'No'}  {PremiumUI.BOX['v']}",
            f"{PremiumUI.BOX['bl']}{PremiumUI.BOX['h'] * 48}{PremiumUI.BOX['br']}"
        ]
        return "\n".join(card)
    
    @staticmethod
    def price_table(prices: dict, columns: int = 3) -> str:
        """Create a price table"""
        items = list(prices.items())
        rows = []
        for i in range(0, len(items), columns):
            row = items[i:i+columns]
            row_text = "  ".join([f"₹{k} → ₹{v}" for k, v in row])
            rows.append(row_text)
        return "\n".join(rows)
    
    @staticmethod
    async def animate(update, text: str, frames: list, duration: float = 2.0):
        """Animate a message"""
        msg = await update.effective_message.reply_text(frames[0] + " " + text)
        frame_time = duration / len(frames)
        
        for i in range(1, len(frames)):
            await asyncio.sleep(frame_time)
            try:
                await msg.edit_text(frames[i] + " " + text)
            except:
                pass
        
        return msg
    
    @staticmethod
    def sparkline(data: list, width: int = 20, height: int = 5) -> str:
        """Create a sparkline chart"""
        if not data:
            return ""
        
        max_val = max(data)
        min_val = min(data)
        range_val = max_val - min_val if max_val > min_val else 1
        
        chart = []
        for i in range(height):
            line = ""
            for val in data:
                normalized = (val - min_val) / range_val
                bar_height = int(normalized * height)
                if height - i <= bar_height:
                    line += "█"
                else:
                    line += "░"
            chart.append(line)
        
        return "\n".join(chart)

ui = PremiumUI()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_currency(amount: int) -> str:
    """Format currency with symbol and commas"""
    return f"₹{amount:,}"

def format_number(num: int) -> str:
    """Format number with K/M/B suffixes"""
    if num < 1000:
        return str(num)
    elif num < 1000000:
        return f"{num/1000:.1f}K"
    elif num < 1000000000:
        return f"{num/1000000:.1f}M"
    else:
        return f"{num/1000000000:.1f}B"

def format_time_ago(timestamp: str) -> str:
    """Format timestamp as time ago"""
    try:
        dt = datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else timestamp
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 365:
            years = diff.days // 365
            return f"{years}y ago"
        elif diff.days > 30:
            months = diff.days // 30
            return f"{months}mo ago"
        elif diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours}h ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes}m ago"
        else:
            return "just now"
    except:
        return str(timestamp)[:10]

def user_badge(purchases: int) -> str:
    """Get user badge based on purchases"""
    if purchases >= 1000:
        return "👑 LEGEND"
    elif purchases >= 500:
        return "💎 ELITE"
    elif purchases >= 250:
        return "🏆 GOLD"
    elif purchases >= 100:
        return "🥈 SILVER"
    elif purchases >= 50:
        return "🥉 BRONZE"
    elif purchases >= 10:
        return "⭐ REGULAR"
    elif purchases >= 1:
        return "🆕 BEGINNER"
    else:
        return "👤 NEW"

def validate_email(email: str) -> bool:
    """Validate email address"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Validate Indian phone number"""
    pattern = r'^[6-9]\d{9}$'
    return bool(re.match(pattern, phone))

def validate_utr(utr: str) -> bool:
    """Validate UTR number"""
    return 12 <= len(utr) <= 22 and utr.isalnum()

def calculate_fee(amount: int) -> tuple:
    """Calculate fee and final amount"""
    if amount < FEE_THRESHOLD:
        fee = int(amount * FEE_PERCENT / 100)
        return fee, amount - fee
    return 0, amount

def calculate_bulk_discount(quantity: int, price: int) -> dict:
    """Calculate bulk discount"""
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

def generate_qr(upi_id: str, amount: int) -> Optional[str]:
    """Generate UPI QR code"""
    if not QR_AVAILABLE:
        return None
    
    try:
        upi_url = f"upi://pay?pa={upi_id}&pn=GiftCardBot&am={amount}&cu=INR"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(upi_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Add amount text to QR
        draw = ImageDraw.Draw(img)
        # Add text if needed
        
        path = f"/tmp/qr_{int(time.time())}_{amount}.png"
        img.save(path)
        return path
    except Exception as e:
        logger.error(f"QR generation failed: {e}")
        return None

def cleanup_temp_file(path: Optional[str]):
    """Clean up temporary file"""
    if path and os.path.exists(path):
        try:
            os.remove(path)
        except:
            pass

def admin_only(func):
    """Decorator for admin-only commands"""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            await update.message.reply_text(
                f"{ui.box('ACCESS DENIED', 30)}\n\n❌ Admin access required.",
                parse_mode=ParseMode.HTML
            )
            return
        return await func(update, context)
    return wrapper

async def check_channel_membership(bot, user_id: int) -> bool:
    """Check if user is member of main channel"""
    try:
        member = await bot.get_chat_member(MAIN_CHANNEL, user_id)
        return member.status not in ("left", "kicked", "banned")
    except Exception:
        return True  # Allow if channel check fails

# ============================================================================
# KEYBOARD BUILDERS
# ============================================================================

def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Create main menu keyboard"""
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
        [InlineKeyboardButton("🔄 CARD EXCHANGE", callback_data="menu_exchange")],
        [InlineKeyboardButton("👥 REFERRAL PROGRAM", callback_data="menu_referral")],
        [InlineKeyboardButton("📅 DAILY REWARDS", callback_data="menu_daily")],
        [InlineKeyboardButton("🏷️ COUPONS", callback_data="menu_coupon")],
        [InlineKeyboardButton("📦 BULK PURCHASE", callback_data="menu_bulk")],
        [InlineKeyboardButton("🎁 SEND GIFT", callback_data="menu_gift_send")],
        [InlineKeyboardButton("🔔 PRICE ALERTS", callback_data="menu_alert")],
        [InlineKeyboardButton("📊 STATISTICS", callback_data="menu_stats")],
        [InlineKeyboardButton("🆘 SUPPORT", callback_data="menu_support")],
        [InlineKeyboardButton("⚙️ SETTINGS", callback_data="menu_settings")],
    ])

def gift_categories_keyboard() -> InlineKeyboardMarkup:
    """Create gift card categories keyboard"""
    categories = [
        ("🛍️ SHOPPING", "gift_cat_shopping"),
        ("🎮 GAMING", "gift_cat_gaming"),
        ("🎬 ENTERTAINMENT", "gift_cat_entertainment"),
        ("🎵 MUSIC", "gift_cat_music"),
        ("🍔 FOOD", "gift_cat_food"),
        ("🛒 GROCERY", "gift_cat_grocery"),
    ]
    
    keyboard = []
    for cat_name, cat_data in categories:
        keyboard.append([InlineKeyboardButton(cat_name, callback_data=cat_data)])
    
    keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)

def amount_keyboard() -> InlineKeyboardMarkup:
    """Create amount selection keyboard"""
    keyboard = []
    for row in AMOUNT_BUTTONS:
        button_row = [InlineKeyboardButton(f"₹{a}", callback_data=f"amount_{a}") for a in row]
        keyboard.append(button_row)
    
    keyboard.append([
        InlineKeyboardButton("🔙 BACK", callback_data="main_menu"),
        InlineKeyboardButton("❌ CANCEL", callback_data="cancel")
    ])
    return InlineKeyboardMarkup(keyboard)

def confirmation_keyboard(action: str) -> InlineKeyboardMarkup:
    """Create confirmation keyboard"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ CONFIRM", callback_data=f"confirm_{action}")],
        [InlineKeyboardButton("❌ CANCEL", callback_data="cancel")]
    ])

def pagination_keyboard(current: int, total: int, prefix: str) -> InlineKeyboardMarkup:
    """Create pagination keyboard"""
    buttons = []
    
    if current > 1:
        buttons.append(InlineKeyboardButton("◀️ PREV", callback_data=f"{prefix}_page_{current-1}"))
    
    buttons.append(InlineKeyboardButton(f"📄 {current}/{total}", callback_data="noop"))
    
    if current < total:
        buttons.append(InlineKeyboardButton("NEXT ▶️", callback_data=f"{prefix}_page_{current+1}"))
    
    keyboard = [buttons]
    keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(keyboard)

# ============================================================================
# START COMMAND - PREMIUM WELCOME
# ============================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Premium start command with animation"""
    user = update.effective_user
    
    # Show loading animation
    loading_msg = await ui.animate(update, "Loading your premium dashboard", ui.ANIMATION_FRAMES['loading'])
    
    # Check ban status
    if db.execute("SELECT is_banned FROM users WHERE user_id=?", (user.id,), fetchone=True):
        await loading_msg.delete()
        await update.message.reply_text(
            f"{ui.box('ACCESS DENIED', 40)}\n\n❌ You are banned from using this bot.",
            parse_mode=ParseMode.HTML
        )
        return
    
    # Get or create user
    db_user = db.execute("SELECT * FROM users WHERE user_id=?", (user.id,), fetchone=True)
    
    if not db_user:
        # Generate unique referral code
        ref_code = hashlib.md5(f"{user.id}{time.time()}".encode()).hexdigest()[:10].upper()
        
        # Create user
        db.execute('''
            INSERT INTO users (user_id, username, first_name, last_name, referral_code)
            VALUES (?, ?, ?, ?, ?)
        ''', (user.id, user.username, user.first_name, user.last_name, ref_code), commit=True)
        
        # Add welcome bonus
        db.execute('''
            INSERT INTO transactions (transaction_id, user_id, amount, final_amount, type, status, description)
            VALUES (?, ?, ?, ?, 'bonus', 'completed', 'Welcome bonus')
        ''', (f"WEL{int(time.time())}", user.id, WELCOME_BONUS, WELCOME_BONUS), commit=True)
        
        db.execute('''
            UPDATE users SET balance_bonus = balance_bonus + ? WHERE user_id=?
        ''', (WELCOME_BONUS, user.id), commit=True)
        
        # Process referral if any
        if context.args and context.args[0]:
            ref_code = context.args[0]
            referrer = db.execute("SELECT user_id FROM users WHERE referral_code=?", (ref_code,), fetchone=True)
            if referrer and referrer['user_id'] != user.id:
                db.execute('''
                    INSERT INTO referrals (referrer_id, referred_id, bonus_amount)
                    VALUES (?, ?, ?)
                ''', (referrer['user_id'], user.id, REFERRAL_BONUS), commit=True)
                
                # Notify referrer
                try:
                    await context.bot.send_message(
                        referrer['user_id'],
                        f"{ui.box('REFERRAL BONUS', 30)}\n\n"
                        f"🎉 {user.first_name} joined using your link!\n"
                        f"💰 You earned *₹{REFERRAL_BONUS}*!",
                        parse_mode=ParseMode.HTML
                    )
                except:
                    pass
    
    # Check channel membership
    require_channel = db.execute("SELECT value FROM settings WHERE key='require_channel_join'", fetchone=True)
    if require_channel and require_channel['value'] == '1':
        is_member = await check_channel_membership(context.bot, user.id)
        if not is_member:
            await loading_msg.delete()
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 JOIN CHANNEL", url=f"https://t.me/{MAIN_CHANNEL.lstrip('@')}")],
                [InlineKeyboardButton("✅ VERIFY", callback_data="verify")]
            ])
            await update.message.reply_text(
                f"{ui.box('CHANNEL REQUIRED', 40)}\n\n"
                f"🔒 Please join our channel to continue:\n"
                f"📢 {MAIN_CHANNEL}",
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            return
    
    # Get user data
    db_user = db.execute("SELECT * FROM users WHERE user_id=?", (user.id,), fetchone=True)
    
    # Create welcome message
    welcome_text = (
        f"{ui.box('✨ PREMIUM GIFT CARD BOT ✨', 50)}\n\n"
        f"{ui.user_card(db_user)}\n\n"
        f"🔥 *65% OFF on All Gift Cards!*\n"
        f"🎮 *20+ Game Recharges*\n"
        f"📱 *All Mobile/DTH/Fiber Operators*\n"
        f"🎁 *Daily Rewards up to ₹2,500*\n\n"
        f"⬇️ *Choose an option:*"
    )
    
    await loading_msg.delete()
    await update.message.reply_text(
        welcome_text,
        reply_markup=main_menu_keyboard(),
        parse_mode=ParseMode.HTML
    )

# ============================================================================
# VERIFY CALLBACK
# ============================================================================

async def verify_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle verify button callback"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    is_member = await check_channel_membership(context.bot, user.id)
    
    if is_member:
        await query.edit_message_text(
            f"{ui.box('VERIFICATION SUCCESSFUL', 40)}\n\n✅ You are verified! Welcome to the bot.",
            parse_mode=ParseMode.HTML
        )
        await start(update, context)
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 JOIN CHANNEL", url=f"https://t.me/{MAIN_CHANNEL.lstrip('@')}")],
            [InlineKeyboardButton("🔄 VERIFY AGAIN", callback_data="verify")]
        ])
        await query.edit_message_text(
            f"{ui.box('VERIFICATION FAILED', 40)}\n\n❌ You haven't joined the channel yet!",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )

# ============================================================================
# GIFT CARD MENU
# ============================================================================

async def gift_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display gift card categories"""
    query = update.callback_query
    await query.answer()
    
    text = (
        f"{ui.box('🎁 GIFT CARDS', 50)}\n\n"
        f"✨ *50+ Premium Brands Available*\n"
        f"🔥 *65% OFF on All Cards*\n"
        f"⚡ *Instant Email Delivery*\n\n"
        f"*Select a category:*"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=gift_categories_keyboard(),
        parse_mode=ParseMode.HTML
    )

async def gift_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display gift cards in category"""
    query = update.callback_query
    await query.answer()
    
    category = query.data.split('_')[2]
    category_names = {
        'shopping': '🛍️ SHOPPING',
        'gaming': '🎮 GAMING',
        'entertainment': '🎬 ENTERTAINMENT',
        'music': '🎵 MUSIC',
        'food': '🍔 FOOD',
        'grocery': '🛒 GROCERY'
    }
    
    # Filter cards by category
    cards = {k: v for k, v in GIFT_CARDS.items() if v.get('category') == category}
    
    text = (
        f"{ui.box(category_names.get(category, 'GIFT CARDS'), 50)}\n\n"
    )
    
    keyboard = []
    for card_id, card in cards.items():
        star = " ⭐" if card.get('popular') else ""
        fire = " 🔥" if card.get('trending') else ""
        keyboard.append([InlineKeyboardButton(
            f"{card['full_emoji']} {card['name']}{star}{fire}",
            callback_data=f"gift_card_{card_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="menu_gift")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def gift_card_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display gift card details"""
    query = update.callback_query
    await query.answer()
    
    card_id = query.data.split('_')[2]
    card = GIFT_CARDS.get(card_id)
    
    if not card:
        await query.edit_message_text("❌ Card not found")
        return
    
    text = (
        f"{ui.box(f'{card["full_emoji"]} {card["name"]}', 60)}\n\n"
        f"{card['description']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 *Available Denominations:*\n"
    )
    
    keyboard = []
    for denom in GIFT_DENOMINATIONS:
        price = GIFT_PRICES[denom]
        savings = denom - price
        discount = int((savings / denom) * 100)
        
        stock = db.execute(
            "SELECT stock FROM gift_stock WHERE card_id=? AND denomination=?",
            (card_id, denom), fetchone=True
        )
        stock_count = stock['stock'] if stock else 0
        stock_indicator = "🟢" if stock_count > 50 else "🟡" if stock_count > 10 else "🔴" if stock_count > 0 else "⚫"
        
        text += f"\n{stock_indicator} *₹{denom}* → *₹{price}* (Save ₹{savings} • {discount}% OFF)"
        
        if stock_count > 0:
            keyboard.append([InlineKeyboardButton(
                f"🎁 ₹{denom} @ ₹{price} ({discount}% OFF)",
                callback_data=f"buy_gift_{card_id}_{denom}"
            )])
    
    text += f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n⚡ *Instant Email Delivery*"
    keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data=f"gift_cat_{card['category']}")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

# ============================================================================
# GIFT CARD PURCHASE FLOW
# ============================================================================

async def buy_gift_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start gift card purchase"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    card_id = parts[2]
    denom = int(parts[3])
    
    card = GIFT_CARDS.get(card_id)
    price = GIFT_PRICES[denom]
    
    # Check stock
    stock = db.execute(
        "SELECT stock FROM gift_stock WHERE card_id=? AND denomination=?",
        (card_id, denom), fetchone=True
    )
    if not stock or stock['stock'] <= 0:
        await query.edit_message_text(
            f"{ui.box('OUT OF STOCK', 40)}\n\n❌ This card is currently out of stock.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data=f"gift_card_{card_id}")]]),
            parse_mode=ParseMode.HTML
        )
        return
    
    # Check balance
    user_id = query.from_user.id
    balance = db.execute(
        "SELECT balance_main FROM users WHERE user_id=?",
        (user_id,), fetchone=True
    )
    current_balance = balance['balance_main'] if balance else 0
    
    if current_balance < price:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 ADD MONEY", callback_data="menu_topup")],
            [InlineKeyboardButton("🔙 BACK", callback_data=f"gift_card_{card_id}")]
        ])
        await query.edit_message_text(
            f"{ui.box('INSUFFICIENT BALANCE', 40)}\n\n"
            f"❌ You need *₹{price}* to buy this card.\n"
            f"💰 Your balance: *₹{current_balance}*",
            reply_markup=keyboard,
            parseMode=ParseMode.HTML
        )
        return
    
    # Store purchase data
    context.user_data['purchase'] = {
        'type': 'gift',
        'card_id': card_id,
        'card_name': card['name'],
        'card_emoji': card['full_emoji'],
        'denom': denom,
        'price': price
    }
    
    await query.edit_message_text(
        f"{ui.box('CONFIRM PURCHASE', 50)}\n\n"
        f"{card['full_emoji']} *{card['name']} ₹{denom}*\n"
        f"💰 Price: *₹{price}*\n"
        f"💳 Your Balance: *₹{current_balance}*\n"
        f"💎 New Balance: *₹{current_balance - price}*\n\n"
        f"📧 Please enter your *email address* for delivery:",
        parse_mode=ParseMode.HTML
    )
    return STATE_EMAIL

# ============================================================================
# EMAIL HANDLER FOR GIFT CARD PURCHASE
# ============================================================================

async def handle_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle email input for gift card delivery"""
    email = update.message.text.strip()
    
    if not validate_email(email):
        await update.message.reply_text(
            f"{ui.box('INVALID EMAIL', 30)}\n\n❌ Please enter a valid email address:",
            parse_mode=ParseMode.HTML
        )
        return STATE_EMAIL
    
    purchase = context.user_data.get('purchase')
    if not purchase:
        await update.message.reply_text(
            f"{ui.box('SESSION EXPIRED', 30)}\n\n❌ Please start over with /start",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    
    user = update.effective_user
    user_id = user.id
    
    # Check balance again
    balance = db.execute(
        "SELECT balance_main FROM users WHERE user_id=?",
        (user_id,), fetchone=True
    )
    current_balance = balance['balance_main'] if balance else 0
    
    if current_balance < purchase['price']:
        await update.message.reply_text(
            f"{ui.box('INSUFFICIENT BALANCE', 30)}\n\n❌ Balance changed. Please try again.",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    
    # Process purchase
    try:
        # Deduct balance
        db.execute(
            "UPDATE users SET balance_main = balance_main - ? WHERE user_id=?",
            (purchase['price'], user_id), commit=True
        )
        
        # Generate order ID
        order_id = f"GC{int(time.time())}{random.randint(1000,9999)}"
        
        # Record purchase
        db.execute('''
            INSERT INTO purchases (
                order_id, user_id, item_type, item_category, item_id,
                item_name, face_value, unit_price, total_price, email, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed')
        ''', (
            order_id, user_id, 'gift', 'gift_card', purchase['card_id'],
            f"{purchase['card_name']} ₹{purchase['denom']}", purchase['denom'],
            purchase['price'], purchase['price'], email
        ), commit=True)
        
        # Update stock
        db.execute(
            "UPDATE gift_stock SET stock = stock - 1 WHERE card_id=? AND denomination=?",
            (purchase['card_id'], purchase['denom']), commit=True
        )
        
        # Record transaction
        db.execute('''
            INSERT INTO transactions (
                transaction_id, user_id, amount, final_amount, type, status, description
            ) VALUES (?, ?, ?, ?, 'debit', 'completed', ?)
        ''', (
            f"TXN{int(time.time())}{random.randint(1000,9999)}",
            user_id, purchase['price'], purchase['price'],
            f"Purchased {purchase['card_name']} ₹{purchase['denom']}"
        ), commit=True)
        
        # Send confirmation
        await update.message.reply_text(
            f"{ui.box('PURCHASE SUCCESSFUL', 50)}\n\n"
            f"{purchase['card_emoji']} *{purchase['card_name']} ₹{purchase['denom']}*\n"
            f"💰 Price Paid: *₹{purchase['price']}*\n"
            f"🆔 Order ID: `{order_id}`\n"
            f"📧 Sent to: `{email}`\n\n"
            f"⚡ Your gift card will be delivered within 5 minutes.\n"
            f"📌 *Check your inbox (and spam folder)!*",
            parse_mode=ParseMode.HTML
        )
        
        # Send proof to channel
        proof_text = (
            f"🛒 *NEW PURCHASE*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *{user.first_name}*\n"
            f"🎁 {purchase['card_emoji']} {purchase['card_name']} ₹{purchase['denom']}\n"
            f"💰 *₹{purchase['price']}*\n"
            f"🆔 Order: `{order_id}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📧 *Email Delivery*\n"
            f"✅ *Completed*"
        )
        
        try:
            await context.bot.send_message(
                chat_id=PROOF_CHANNEL,
                text=proof_text,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Proof send failed: {e}")
        
        logger.success(f"✅ Gift card purchased: User {user_id} - {purchase['card_name']} ₹{purchase['denom']}")
        
    except Exception as e:
        logger.error(f"❌ Purchase failed: {e}")
        await update.message.reply_text(
            f"{ui.box('PURCHASE FAILED', 30)}\n\n❌ An error occurred. Please try again.",
            parse_mode=ParseMode.HTML
        )
    
    context.user_data.clear()
    return ConversationHandler.END

# ============================================================================
# MOBILE RECHARGE FLOW
# ============================================================================

async def mobile_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display mobile recharge menu"""
    query = update.callback_query
    await query.answer()
    
    text = (
        f"{ui.box('📱 MOBILE RECHARGE', 50)}\n\n"
        f"✨ *All Major Operators Available*\n"
        f"⚡ *Instant Recharge*\n\n"
        f"*Select operator:*"
    )
    
    keyboard = []
    for op_id, op in MOBILE_OPERATORS.items():
        star = " ⭐" if op.get('popular') else ""
        keyboard.append([InlineKeyboardButton(
            f"{op['full_emoji']} {op['name']}{star}",
            callback_data=f"mobile_op_{op_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="main_menu")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    return STATE_MOBILE_OPERATOR

async def mobile_operator_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle mobile operator selection"""
    query = update.callback_query
    await query.answer()
    
    op_id = query.data.split('_')[2]
    context.user_data['mobile_op'] = op_id
    op = MOBILE_OPERATORS[op_id]
    
    await query.edit_message_text(
        f"{op['full_emoji']} *{op['name']} RECHARGE*\n\n"
        f"📱 Please enter your 10-digit mobile number:",
        parse_mode=ParseMode.HTML
    )
    return STATE_MOBILE_NUMBER

async def mobile_number_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle mobile number input"""
    number = update.message.text.strip()
    
    if not validate_phone(number):
        await update.message.reply_text(
            f"{ui.box('INVALID NUMBER', 30)}\n\n❌ Please enter a valid 10-digit mobile number:",
            parse_mode=ParseMode.HTML
        )
        return STATE_MOBILE_NUMBER
    
    context.user_data['mobile_number'] = number
    op_id = context.user_data['mobile_op']
    op = MOBILE_OPERATORS[op_id]
    
    # Show plans
    plans = op['plans'][:12]  # Show first 12 plans
    text = (
        f"{op['full_emoji']} *{op['name']} RECHARGE*\n\n"
        f"📱 Number: `{number}`\n\n"
        f"*Available Plans:*\n"
    )
    
    keyboard = []
    row = []
    for i, price in enumerate(plans):
        row.append(InlineKeyboardButton(f"₹{price}", callback_data=f"mobile_plan_{price}"))
        if len(row) == 3 or i == len(plans) - 1:
            keyboard.append(row)
            row = []
    
    keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="menu_mobile")])
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    return STATE_MOBILE_PLAN

async def mobile_plan_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle mobile plan selection"""
    query = update.callback_query
    await query.answer()
    
    price = int(query.data.split('_')[2])
    op_id = context.user_data['mobile_op']
    number = context.user_data['mobile_number']
    op = MOBILE_OPERATORS[op_id]
    
    user = update.effective_user
    user_id = user.id
    
    # Check balance
    balance = db.execute(
        "SELECT balance_main FROM users WHERE user_id=?",
        (user_id,), fetchone=True
    )
    current_balance = balance['balance_main'] if balance else 0
    
    if current_balance < price:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💰 ADD MONEY", callback_data="menu_topup")],
            [InlineKeyboardButton("🔙 BACK", callback_data="menu_mobile")]
        ])
        await query.edit_message_text(
            f"{ui.box('INSUFFICIENT BALANCE', 40)}\n\n"
            f"❌ You need *₹{price}* for this recharge.\n"
            f"💰 Your balance: *₹{current_balance}*",
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    
    # Process recharge
    try:
        # Deduct balance
        db.execute(
            "UPDATE users SET balance_main = balance_main - ? WHERE user_id=?",
            (price, user_id), commit=True
        )
        
        # Generate order ID
        order_id = f"MR{int(time.time())}{random.randint(1000,9999)}"
        
        # Record purchase
        db.execute('''
            INSERT INTO purchases (
                order_id, user_id, item_type, item_category, item_id,
                item_name, face_value, unit_price, total_price, phone, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'processing')
        ''', (
            order_id, user_id, 'mobile', 'recharge', op_id,
            f"{op['name']} ₹{price}", price, price, price, number
        ), commit=True)
        
        # Record transaction
        db.execute('''
            INSERT INTO transactions (
                transaction_id, user_id, amount, final_amount, type, status, description
            ) VALUES (?, ?, ?, ?, 'debit', 'completed', ?)
        ''', (
            f"TXN{int(time.time())}{random.randint(1000,9999)}",
            user_id, price, price,
            f"{op['name']} recharge for {number}"
        ), commit=True)
        
        await query.edit_message_text(
            f"{ui.box('RECHARGE SUCCESSFUL', 50)}\n\n"
            f"{op['full_emoji']} *{op['name']}*\n"
            f"📱 Number: `{number}`\n"
            f"💰 Amount: *₹{price}*\n"
            f"🆔 Order ID: `{order_id}`\n\n"
            f"⚡ Your recharge will be completed in 2-5 minutes.",
            parse_mode=ParseMode.HTML
        )
        
        logger.success(f"✅ Mobile recharge: User {user_id} - {op['name']} {number} ₹{price}")
        
    except Exception as e:
        logger.error(f"❌ Recharge failed: {e}")
        await query.edit_message_text(
            f"{ui.box('RECHARGE FAILED', 30)}\n\n❌ An error occurred. Please try again.",
            parse_mode=ParseMode.HTML
        )
    
    context.user_data.clear()
    return ConversationHandler.END

# ============================================================================
# GAME RECHARGE FLOW
# ============================================================================

async def game_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display game recharge menu"""
    query = update.callback_query
    await query.answer()
    
    text = (
        f"{ui.box('🎮 GAME RECHARGES', 50)}\n\n"
        f"✨ *All Popular Games Available*\n"
        f"⚡ *Instant Delivery*\n\n"
        f"*Select game:*"
    )
    
    keyboard = []
    for game_id, game in GAME_RECHARGES.items():
        star = " ⭐" if game.get('popular') else ""
        fire = " 🔥" if game.get('trending') else ""
        keyboard.append([InlineKeyboardButton(
            f"{game['full_emoji']} {game['name']}{star}{fire}",
            callback_data=f"game_select_{game_id}"
        )])
    
    keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="main_menu")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def game_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle game selection"""
    query = update.callback_query
    await query.answer()
    
    game_id = query.data.split('_')[2]
    game = GAME_RECHARGES.get(game_id)
    context.user_data['game_id'] = game_id
    
    text = (
        f"{game['full_emoji']} *{game['name']} RECHARGE*\n\n"
        f"{game['description']}\n\n"
        f"*Available Amounts:*\n"
    )
    
    keyboard = []
    row = []
    amounts = GAME_PRICES.get(game_id, [])
    
    for i, amount in enumerate(amounts):
        row.append(InlineKeyboardButton(f"₹{amount}", callback_data=f"game_amount_{amount}"))
        if len(row) == 3 or i == len(amounts) - 1:
            keyboard.append(row)
            row = []
    
    keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="menu_game")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )
    return STATE_GAME_AMOUNT

async def game_amount_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle game amount selection"""
    query = update.callback_query
    await query.answer()
    
    amount = int(query.data.split('_')[2])
    game_id = context.user_data['game_id']
    game = GAME_RECHARGES[game_id]
    
    context.user_data['game_amount'] = amount
    
    await query.edit_message_text(
        f"{game['full_emoji']} *{game['name']} RECHARGE*\n\n"
        f"💰 Amount: *₹{amount}*\n\n"
        f"🆔 Please enter your *in-game user ID*:",
        parse_mode=ParseMode.HTML
    )
    return STATE_GAME_ID

async def game_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle game ID input"""
    game_id_input = update.message.text.strip()
    
    if not game_id_input or len(game_id_input) < 3:
        await update.message.reply_text(
            f"{ui.box('INVALID ID', 30)}\n\n❌ Please enter a valid game ID:",
            parse_mode=ParseMode.HTML
        )
        return STATE_GAME_ID
    
    game_id = context.user_data['game_id']
    amount = context.user_data['game_amount']
    game = GAME_RECHARGES[game_id]
    
    user = update.effective_user
    user_id = user.id
    
    # Check balance
    balance = db.execute(
        "SELECT balance_main FROM users WHERE user_id=?",
        (user_id,), fetchone=True
    )
    current_balance = balance['balance_main'] if balance else 0
    
    if current_balance < amount:
        await update.message.reply_text(
            f"{ui.box('INSUFFICIENT BALANCE', 30)}\n\n"
            f"❌ You need *₹{amount}* for this recharge.\n"
            f"💰 Your balance: *₹{current_balance}*",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    
    # Process recharge
    try:
        # Deduct balance
        db.execute(
            "UPDATE users SET balance_main = balance_main - ? WHERE user_id=?",
            (amount, user_id), commit=True
        )
        
        # Generate order ID
        order_id = f"GR{int(time.time())}{random.randint(1000,9999)}"
        
        # Record purchase
        db.execute('''
            INSERT INTO purchases (
                order_id, user_id, item_type, item_category, item_id,
                item_name, face_value, unit_price, total_price, game_id, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'processing')
        ''', (
            order_id, user_id, 'game', 'recharge', game_id,
            f"{game['name']} ₹{amount}", amount, amount, amount, game_id_input
        ), commit=True)
        
        # Record transaction
        db.execute('''
            INSERT INTO transactions (
                transaction_id, user_id, amount, final_amount, type, status, description
            ) VALUES (?, ?, ?, ?, 'debit', 'completed', ?)
        ''', (
            f"TXN{int(time.time())}{random.randint(1000,9999)}",
            user_id, amount, amount,
            f"{game['name']} recharge for ID {game_id_input}"
        ), commit=True)
        
        await update.message.reply_text(
            f"{ui.box('RECHARGE SUCCESSFUL', 50)}\n\n"
            f"{game['full_emoji']} *{game['name']}*\n"
            f"💰 Amount: *₹{amount}*\n"
            f"🆔 Game ID: `{game_id_input}`\n"
            f"🆔 Order ID: `{order_id}`\n\n"
            f"⚡ Your recharge will be processed in 2-5 minutes.",
            parse_mode=ParseMode.HTML
        )
        
        logger.success(f"✅ Game recharge: User {user_id} - {game['name']} ₹{amount}")
        
    except Exception as e:
        logger.error(f"❌ Game recharge failed: {e}")
        await update.message.reply_text(
            f"{ui.box('RECHARGE FAILED', 30)}\n\n❌ An error occurred. Please try again.",
            parse_mode=ParseMode.HTML
        )
    
    context.user_data.clear()
    return ConversationHandler.END

# ============================================================================
# TOP UP / ADD MONEY FLOW
# ============================================================================

async def topup_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display top up menu"""
    query = update.callback_query
    await query.answer()
    
    text = (
        f"{ui.box('💰 ADD MONEY TO WALLET', 50)}\n\n"
        f"📌 *Fee Policy:*\n"
        f"• Below ₹{FEE_THRESHOLD}: *{FEE_PERCENT}%* fee\n"
        f"• Above ₹{FEE_THRESHOLD}: *No fee!*\n\n"
        f"💡 *Tip:* Recharge ₹{FEE_THRESHOLD}+ to save fees!\n\n"
        f"*Select amount or enter custom:*"
    )
    
    await query.edit_message_text(
        text,
        reply_markup=amount_keyboard(),
        parse_mode=ParseMode.HTML
    )

async def amount_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle amount selection"""
    query = update.callback_query
    await query.answer()
    
    amount = int(query.data.split('_')[1])
    fee, final = calculate_fee(amount)
    
    context.user_data['recharge'] = {
        'amount': amount,
        'fee': fee,
        'final': final
    }
    
    # Generate QR code
    qr_path = generate_qr(UPI_ID, amount)
    
    text = (
        f"{ui.box('💳 PAYMENT DETAILS', 50)}\n\n"
        f"💰 *Amount:* ₹{amount:,}\n"
        f"💸 *Fee:* ₹{fee}\n"
        f"✅ *You'll get:* ₹{final:,}\n\n"
        f"🏦 *UPI ID:* `{UPI_ID}`\n\n"
        f"📌 *After payment:*\n"
        f"1️⃣ Click *I HAVE PAID*\n"
        f"2️⃣ Upload screenshot\n"
        f"3️⃣ Enter UTR number"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ I HAVE PAID", callback_data="paid")],
        [InlineKeyboardButton("🔙 BACK", callback_data="menu_topup")]
    ])
    
    if qr_path:
        with open(qr_path, 'rb') as qr_file:
            await context.bot.send_photo(
                chat_id=query.from_user.id,
                photo=qr_file,
                caption=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
        cleanup_temp_file(qr_path)
        await query.message.delete()
    else:
        await query.edit_message_text(
            text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML
        )

# ============================================================================
# PAYMENT VERIFICATION FLOW
# ============================================================================

async def handle_paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle paid button click"""
    query = update.callback_query
    await query.answer()
    
    recharge = context.user_data.get('recharge')
    if not recharge:
        await query.edit_message_text(
            f"{ui.box('SESSION EXPIRED', 30)}\n\n⏰ Please start over with /start",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 MAIN MENU", callback_data="main_menu")]]),
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    
    await query.edit_message_text(
        f"{ui.box('📸 SEND PAYMENT PROOF', 40)}\n\n"
        f"Amount: *₹{recharge['amount']}*\n"
        f"You'll get: *₹{recharge['final']}*\n\n"
        f"1️⃣ Send a clear *screenshot* of your payment\n"
        f"2️⃣ Send the *UTR number*",
        parse_mode=ParseMode.HTML
    )
    return STATE_SCREENSHOT

async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle screenshot upload"""
    if not update.message.photo:
        await update.message.reply_text(
            f"{ui.box('NO PHOTO', 30)}\n\n❌ Please send a screenshot of your payment.",
            parse_mode=ParseMode.HTML
        )
        return STATE_SCREENSHOT
    
    photo = update.message.photo[-1]
    context.user_data['screenshot'] = photo.file_id
    
    await update.message.reply_text(
        f"{ui.box('✅ SCREENSHOT RECEIVED', 30)}\n\n"
        f"🔢 Now please enter your *UTR number*:\n"
        f"_(12-22 alphanumeric characters)_",
        parse_mode=ParseMode.HTML
    )
    return STATE_UTR

async def handle_utr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle UTR input"""
    utr = update.message.text.strip().upper()
    user = update.effective_user
    
    if not validate_utr(utr):
        await update.message.reply_text(
            f"{ui.box('INVALID UTR', 30)}\n\n❌ UTR must be 12-22 alphanumeric characters.\nPlease try again:",
            parse_mode=ParseMode.HTML
        )
        return STATE_UTR
    
    recharge = context.user_data.get('recharge')
    screenshot = context.user_data.get('screenshot')
    
    if not recharge or not screenshot:
        await update.message.reply_text(
            f"{ui.box('SESSION EXPIRED', 30)}\n\n⏰ Please start over with /start",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    
    # Check for duplicate UTR
    existing = db.execute("SELECT id FROM verifications WHERE utr=?", (utr,), fetchone=True)
    if existing:
        await update.message.reply_text(
            f"{ui.box('DUPLICATE UTR', 30)}\n\n❌ This UTR has already been used.",
            parse_mode=ParseMode.HTML
        )
        return STATE_UTR
    
    # Create verification
    try:
        db.execute('''
            INSERT INTO verifications (user_id, amount, fee, final_amount, utr, screenshot, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
        ''', (user.id, recharge['amount'], recharge['fee'], recharge['final'], utr, screenshot), commit=True)
        
        # Send to admin channel
        admin_text = (
            f"💳 *NEW PAYMENT VERIFICATION*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 *User:* {user.first_name}\n"
            f"🆔 *ID:* `{user.id}`\n"
            f"👤 *Username:* @{user.username}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💰 *Amount:* ₹{recharge['amount']}\n"
            f"💸 *Fee:* ₹{recharge['fee']}\n"
            f"✅ *Credit:* ₹{recharge['final']}\n"
            f"🔢 *UTR:* `{utr}`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        
        admin_keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ APPROVE", callback_data=f"approve_{utr}"),
            InlineKeyboardButton("❌ REJECT", callback_data=f"reject_{utr}")
        ]])
        
        await context.bot.send_photo(
            chat_id=ADMIN_CHANNEL_ID,
            photo=screenshot,
            caption=admin_text,
            reply_markup=admin_keyboard
        )
        
        await update.message.reply_text(
            f"{ui.box('✅ VERIFICATION SUBMITTED', 40)}\n\n"
            f"💰 Amount: *₹{recharge['amount']}*\n"
            f"🔢 UTR: `{utr}`\n\n"
            f"Your payment is under review. You'll be notified once approved.\n\n"
            f"⏳ *Estimated time: 5-15 minutes*",
            parse_mode=ParseMode.HTML
        )
        
        logger.info(f"✅ Payment verification submitted: User {user.id} - ₹{recharge['amount']}")
        
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        await update.message.reply_text(
            f"{ui.box('ERROR', 30)}\n\n❌ An error occurred. Please try again.",
            parse_mode=ParseMode.HTML
        )
    
    context.user_data.clear()
    return ConversationHandler.END

# ============================================================================
# ADMIN CALLBACK HANDLER
# ============================================================================

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin callbacks (approve/reject)"""
    query = update.callback_query
    await query.answer()
    
    if update.effective_user.id != ADMIN_ID:
        await query.answer("❌ Admin only!", show_alert=True)
        return
    
    data = query.data
    
    if data.startswith("approve_"):
        utr = data[8:]
        
        # Get verification
        verification = db.execute(
            "SELECT * FROM verifications WHERE utr=? AND status='pending'",
            (utr,), fetchone=True
        )
        
        if not verification:
            await query.edit_message_caption("❌ Verification not found or already processed")
            return
        
        try:
            # Update user balance
            db.execute(
                "UPDATE users SET balance_main = balance_main + ? WHERE user_id=?",
                (verification['final_amount'], verification['user_id']), commit=True
            )
            
            # Update verification status
            db.execute(
                "UPDATE verifications SET status='approved', admin_id=?, verified_at=CURRENT_TIMESTAMP WHERE utr=?",
                (ADMIN_ID, utr), commit=True
            )
            
            # Record transaction
            db.execute('''
                INSERT INTO transactions (
                    transaction_id, user_id, amount, final_amount, type, status, utr, description
                ) VALUES (?, ?, ?, ?, 'credit', 'completed', ?, 'UPI recharge approved')
            ''', (
                f"TXN{int(time.time())}{random.randint(1000,9999)}",
                verification['user_id'], verification['final_amount'], verification['final_amount'], utr
            ), commit=True)
            
            # Notify user
            try:
                await context.bot.send_message(
                    verification['user_id'],
                    f"{ui.box('✅ PAYMENT APPROVED', 40)}\n\n"
                    f"💰 Amount: *₹{verification['final_amount']}* added to your wallet!\n"
                    f"🔢 UTR: `{utr}`\n\n"
                    f"Thank you for using our service! 🎁",
                    parse_mode=ParseMode.HTML
                )
            except:
                pass
            
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n✅ *APPROVED BY ADMIN*"
            )
            
            logger.success(f"✅ Payment approved: User {verification['user_id']} - ₹{verification['final_amount']}")
            
        except Exception as e:
            logger.error(f"❌ Approval failed: {e}")
            await query.edit_message_caption("❌ Approval failed")
    
    elif data.startswith("reject_"):
        utr = data[7:]
        
        try:
            db.execute(
                "UPDATE verifications SET status='rejected', admin_id=? WHERE utr=?",
                (ADMIN_ID, utr), commit=True
            )
            
            # Get user ID
            verification = db.execute(
                "SELECT user_id FROM verifications WHERE utr=?",
                (utr,), fetchone=True
            )
            
            if verification:
                try:
                    await context.bot.send_message(
                        verification['user_id'],
                        f"{ui.box('❌ PAYMENT REJECTED', 40)}\n\n"
                        f"🔢 UTR: `{utr}`\n\n"
                        f"Your payment was rejected. Please contact support if you believe this is an error.",
                        parse_mode=ParseMode.HTML
                    )
                except:
                    pass
            
            await query.edit_message_caption(
                caption=query.message.caption + "\n\n❌ *REJECTED BY ADMIN*"
            )
            
            logger.info(f"❌ Payment rejected: {utr}")
            
        except Exception as e:
            logger.error(f"❌ Rejection failed: {e}")
            await query.edit_message_caption("❌ Rejection failed")

# ============================================================================
# WALLET MENU
# ============================================================================

async def wallet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display wallet menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    user_data = db.execute("SELECT * FROM users WHERE user_id=?", (user_id,), fetchone=True)
    
    if not user_data:
        await query.edit_message_text("❌ User not found")
        return
    
    # Get recent transactions
    transactions = db.execute(
        "SELECT * FROM transactions WHERE user_id=? ORDER BY created_at DESC LIMIT 5",
        (user_id,), fetchall=True
    )
    
    text = (
        f"{ui.box('👛 MY WALLET', 50)}\n\n"
        f"{ui.user_card(user_data)}\n\n"
        f"📊 *Recent Transactions:*\n"
    )
    
    if transactions:
        for tx in transactions[:5]:
            emoji = "✅" if tx['type'] == 'credit' else "❌" if tx['type'] == 'debit' else "🎁"
            sign = "+" if tx['type'] in ['credit', 'bonus'] else "-"
            text += f"{emoji} {sign}₹{tx['amount']} - {tx['description'][:30]} - {format_time_ago(tx['created_at'])}\n"
    else:
        text += "No transactions yet.\n"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 ADD MONEY", callback_data="menu_topup")],
        [InlineKeyboardButton("🔄 WALLET TRANSFER", callback_data="menu_transfer")],
        [InlineKeyboardButton("📊 FULL HISTORY", callback_data="wallet_history")],
        [InlineKeyboardButton("🔙 BACK", callback_data="main_menu")]
    ])
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

# ============================================================================
# WALLET TRANSFER FLOW
# ============================================================================

async def transfer_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display transfer menu"""
    query = update.callback_query
    await query.answer()
    
    text = (
        f"{ui.box('🔄 WALLET TRANSFER', 50)}\n\n"
        f"💰 *Min Transfer:* ₹{WALLET_TRANSFER_MIN}\n"
        f"💰 *Max Transfer:* ₹{WALLET_TRANSFER_MAX}\n"
        f"💸 *Fee:* {WALLET_TRANSFER_FEE}%\n"
        f"📊 *Daily Limit:* ₹{WALLET_TRANSFER_DAILY_LIMIT}\n\n"
        f"Please enter the recipient's username or user ID:"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 BACK", callback_data="main_menu")]
    ])
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
    return STATE_WALLET_TRANSFER_USERNAME

async def transfer_recipient_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle transfer recipient input"""
    recipient = update.message.text.strip()
    
    # Check if input is user ID (numeric) or username
    if recipient.isdigit():
        recipient_id = int(recipient)
    else:
        # Remove @ if present
        username = recipient.lstrip('@')
        user = db.execute("SELECT user_id FROM users WHERE username=?", (username,), fetchone=True)
        if not user:
            await update.message.reply_text(
                f"{ui.box('USER NOT FOUND', 30)}\n\n❌ User not found. Please try again:",
                parse_mode=ParseMode.HTML
            )
            return STATE_WALLET_TRANSFER_USERNAME
        recipient_id = user['user_id']
    
    # Check if sending to self
    if recipient_id == update.effective_user.id:
        await update.message.reply_text(
            f"{ui.box('INVALID RECIPIENT', 30)}\n\n❌ You cannot send money to yourself.",
            parse_mode=ParseMode.HTML
        )
        return STATE_WALLET_TRANSFER_USERNAME
    
    context.user_data['transfer_recipient'] = recipient_id
    
    # Get recipient info
    recipient_data = db.execute("SELECT * FROM users WHERE user_id=?", (recipient_id,), fetchone=True)
    
    await update.message.reply_text(
        f"{ui.box('📤 SEND MONEY', 40)}\n\n"
        f"👤 *Recipient:* {recipient_data['first_name']} (@{recipient_data['username']})\n"
        f"🆔 *ID:* `{recipient_id}`\n\n"
        f"💰 Enter amount to send (Min: ₹{WALLET_TRANSFER_MIN}, Max: ₹{WALLET_TRANSFER_MAX}):",
        parse_mode=ParseMode.HTML
    )
    return STATE_WALLET_TRANSFER_AMOUNT

async def transfer_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle transfer amount input"""
    try:
        amount = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(
            f"{ui.box('INVALID AMOUNT', 30)}\n\n❌ Please enter a valid number:",
            parse_mode=ParseMode.HTML
        )
        return STATE_WALLET_TRANSFER_AMOUNT
    
    if amount < WALLET_TRANSFER_MIN or amount > WALLET_TRANSFER_MAX:
        await update.message.reply_text(
            f"{ui.box('INVALID AMOUNT', 30)}\n\n"
            f"❌ Amount must be between ₹{WALLET_TRANSFER_MIN} and ₹{WALLET_TRANSFER_MAX}.",
            parse_mode=ParseMode.HTML
        )
        return STATE_WALLET_TRANSFER_AMOUNT
    
    user = update.effective_user
    balance = db.execute("SELECT balance_main FROM users WHERE user_id=?", (user.id,), fetchone=True)
    current_balance = balance['balance_main'] if balance else 0
    
    if current_balance < amount:
        await update.message.reply_text(
            f"{ui.box('INSUFFICIENT BALANCE', 30)}\n\n❌ You need ₹{amount} for this transfer.\nYour balance: ₹{current_balance}",
            parse_mode=ParseMode.HTML
        )
        return STATE_WALLET_TRANSFER_AMOUNT
    
    # Calculate fee
    fee = int(amount * WALLET_TRANSFER_FEE / 100)
    final = amount - fee
    recipient_id = context.user_data['transfer_recipient']
    
    context.user_data['transfer_amount'] = amount
    context.user_data['transfer_fee'] = fee
    context.user_data['transfer_final'] = final
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ CONFIRM", callback_data="transfer_confirm")],
        [InlineKeyboardButton("❌ CANCEL", callback_data="main_menu")]
    ])
    
    await update.message.reply_text(
        f"{ui.box('📤 CONFIRM TRANSFER', 40)}\n\n"
        f"💸 *Amount:* ₹{amount}\n"
        f"💳 *Fee:* ₹{fee} ({WALLET_TRANSFER_FEE}%)\n"
        f"✅ *Recipient gets:* ₹{final}\n\n"
        f"Confirm transfer?",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
    return STATE_WALLET_TRANSFER_CONFIRM

async def transfer_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle transfer confirmation"""
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    recipient_id = context.user_data.get('transfer_recipient')
    amount = context.user_data.get('transfer_amount')
    fee = context.user_data.get('transfer_fee')
    final = context.user_data.get('transfer_final')
    
    if not all([recipient_id, amount, fee, final]):
        await query.edit_message_text(
            f"{ui.box('SESSION EXPIRED', 30)}\n\n⏰ Please start over.",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    
    try:
        # Deduct from sender
        db.execute(
            "UPDATE users SET balance_main = balance_main - ? WHERE user_id=?",
            (amount, user.id), commit=True
        )
        
        # Add to recipient
        db.execute(
            "UPDATE users SET balance_main = balance_main + ? WHERE user_id=?",
            (final, recipient_id), commit=True
        )
        
        # Record transfer
        transfer_id = f"TRF{int(time.time())}{random.randint(1000,9999)}"
        db.execute('''
            INSERT INTO wallet_transfers (transfer_id, from_user, to_user, amount, fee, final_amount)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (transfer_id, user.id, recipient_id, amount, fee, final), commit=True)
        
        # Record transactions
        db.execute('''
            INSERT INTO transactions (transaction_id, user_id, amount, final_amount, type, description)
            VALUES (?, ?, ?, ?, 'debit', ?)
        ''', (
            f"TXN{int(time.time())}{random.randint(1000,9999)}",
            user.id, amount, amount,
            f"Transfer to user {recipient_id}"
        ), commit=True)
        
        db.execute('''
            INSERT INTO transactions (transaction_id, user_id, amount, final_amount, type, description)
            VALUES (?, ?, ?, ?, 'credit', ?)
        ''', (
            f"TXN{int(time.time())}{random.randint(1000,9999)}",
            recipient_id, final, final,
            f"Transfer from user {user.id}"
        ), commit=True)
        
        # Get recipient info
        recipient = db.execute("SELECT * FROM users WHERE user_id=?", (recipient_id,), fetchone=True)
        
        await query.edit_message_text(
            f"{ui.box('✅ TRANSFER SUCCESSFUL', 40)}\n\n"
            f"📤 *Sent:* ₹{amount}\n"
            f"💸 *Fee:* ₹{fee}\n"
            f"✅ *Recipient got:* ₹{final}\n"
            f"👤 *To:* {recipient['first_name']} (@{recipient['username']})\n\n"
            f"Transfer ID: `{transfer_id}`",
            parse_mode=ParseMode.HTML
        )
        
        # Notify recipient
        try:
            await context.bot.send_message(
                recipient_id,
                f"{ui.box('📥 MONEY RECEIVED', 30)}\n\n"
                f"💰 You received *₹{final}* from {user.first_name}!",
                parse_mode=ParseMode.HTML
            )
        except:
            pass
        
        logger.success(f"✅ Transfer: {user.id} → {recipient_id} ₹{amount}")
        
    except Exception as e:
        logger.error(f"❌ Transfer failed: {e}")
        await query.edit_message_text(
            f"{ui.box('TRANSFER FAILED', 30)}\n\n❌ An error occurred. Please try again.",
            parse_mode=ParseMode.HTML
        )
    
    context.user_data.clear()
    return ConversationHandler.END

# ============================================================================
# DAILY REWARD HANDLER
# ============================================================================

async def daily_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle daily reward claim"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    today = date.today().isoformat()
    
    # Check if already claimed today
    claimed = db.execute(
        "SELECT id FROM daily_rewards WHERE user_id=? AND claim_date=?",
        (user_id, today), fetchone=True
    )
    
    if claimed:
        await query.edit_message_text(
            f"{ui.box('⏰ ALREADY CLAIMED', 30)}\n\n"
            f"You already claimed your daily reward today!\n"
            f"Come back tomorrow for another reward.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="main_menu")]]),
            parse_mode=ParseMode.HTML
        )
        return
    
    # Get current streak
    last_claim = db.execute(
        "SELECT claim_date, streak FROM daily_rewards WHERE user_id=? ORDER BY claim_date DESC LIMIT 1",
        (user_id,), fetchone=True
    )
    
    if last_claim:
        last_date = datetime.strptime(last_claim['claim_date'], '%Y-%m-%d').date()
        today_date = date.today()
        day_diff = (today_date - last_date).days
        
        if day_diff == 1:
            streak = last_claim['streak'] + 1
        elif day_diff == 0:
            streak = last_claim['streak']  # Should not happen due to check above
        else:
            streak = 1
    else:
        streak = 1
    
    # Calculate reward
    reward = DAILY_LOGIN_BONUS
    for day in sorted(DAILY_REWARDS.keys(), reverse=True):
        if streak >= day:
            reward = DAILY_REWARDS[day]
            break
    
    # Apply streak bonus for high streaks
    if streak > 30:
        bonus = int(reward * STREAK_BONUS_MULTIPLIER)
        reward = bonus
    
    try:
        # Record reward
        db.execute('''
            INSERT INTO daily_rewards (user_id, claim_date, streak, amount)
            VALUES (?, ?, ?, ?)
        ''', (user_id, today, streak, reward), commit=True)
        
        # Add to bonus balance
        db.execute(
            "UPDATE users SET balance_bonus = balance_bonus + ? WHERE user_id=?",
            (reward, user_id), commit=True
        )
        
        # Record transaction
        db.execute('''
            INSERT INTO transactions (transaction_id, user_id, amount, final_amount, type, status, description)
            VALUES (?, ?, ?, ?, 'bonus', 'completed', ?)
        ''', (
            f"DLY{int(time.time())}{random.randint(1000,9999)}",
            user_id, reward, reward,
            f"Daily reward (streak: {streak})"
        ), commit=True)
        
        await query.edit_message_text(
            f"{ui.box('🎉 DAILY REWARD CLAIMED', 40)}\n\n"
            f"💰 *Reward:* ₹{reward}\n"
            f"🔥 *Streak:* Day {streak}\n\n"
            f"Keep your streak going for bigger rewards!\n\n"
            f"🏆 *Next Milestone:* Day {streak + 1} → ₹{DAILY_REWARDS.get(streak + 1, 'More!')}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="main_menu")]]),
            parse_mode=ParseMode.HTML
        )
        
        logger.info(f"✅ Daily reward: User {user_id} - Day {streak} - ₹{reward}")
        
    except Exception as e:
        logger.error(f"❌ Daily reward failed: {e}")
        await query.edit_message_text(
            f"{ui.box('ERROR', 30)}\n\n❌ Failed to claim daily reward. Please try again.",
            parse_mode=ParseMode.HTML
        )

# ============================================================================
# MYSTERY BOX FEATURE
# ============================================================================

async def mystery_box_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display mystery box menu"""
    query = update.callback_query
    await query.answer()
    
    text = (
        f"{ui.box('🎁 MYSTERY BOX', 50)}\n\n"
        f"✨ *Try your luck and win big!*\n\n"
        f"📊 *Available Boxes:*\n"
    )
    
    keyboard = []
    for price in MYSTERY_BOX_PRICES:
        cfg = MYSTERY_BOX_MULTIPLIERS[price]
        text += f"\n• *₹{price}* Box: Win ₹{cfg['min']}-₹{cfg['max']} (Jackpot: ₹{cfg['jackpot']})"
        keyboard.append([InlineKeyboardButton(f"🎁 OPEN ₹{price} BOX", callback_data=f"mystery_open_{price}")])
    
    # Get user stats
    stats = db.execute(
        "SELECT COUNT(*) as count, SUM(won_amount) as total, AVG(won_amount) as avg FROM mystery_box_logs WHERE user_id=?",
        (query.from_user.id,), fetchone=True
    )
    
    text += f"\n\n📊 *Your Stats:*\n"
    text += f"• Boxes Opened: {stats['count'] if stats else 0}\n"
    text += f"• Total Won: ₹{stats['total'] if stats else 0}\n"
    text += f"• Average Win: ₹{int(stats['avg']) if stats and stats['avg'] else 0}\n"
    
    keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="main_menu")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML
    )

async def mystery_box_open(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Open mystery box"""
    query = update.callback_query
    await query.answer()
    
    price = int(query.data.split('_')[2])
    user_id = query.from_user.id
    
    # Check balance
    balance = db.execute("SELECT balance_main FROM users WHERE user_id=?", (user_id,), fetchone=True)
    current_balance = balance['balance_main'] if balance else 0
    
    if current_balance < price:
        await query.edit_message_text(
            f"{ui.box('INSUFFICIENT BALANCE', 30)}\n\n"
            f"❌ You need *₹{price}* to open this box.\n"
            f"💰 Your balance: *₹{current_balance}*",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="menu_mystery")]]),
            parse_mode=ParseMode.HTML
        )
        return
    
    # Calculate win amount
    cfg = MYSTERY_BOX_MULTIPLIERS[price]
    
    # Jackpot chances
    rand = random.random()
    if rand < 0.01:  # 1% chance for jackpot
        win = cfg['jackpot']
        was_jackpot = 1
    else:
        win = random.randint(cfg['min'], cfg['max'])
        was_jackpot = 0
    
    multiplier = win / price
    
    try:
        # Deduct price
        db.execute(
            "UPDATE users SET balance_main = balance_main - ? WHERE user_id=?",
            (price, user_id), commit=True
        )
        
        # Add winnings to bonus balance
        db.execute(
            "UPDATE users SET balance_bonus = balance_bonus + ? WHERE user_id=?",
            (win, user_id), commit=True
        )
        
        # Record box opening
        db.execute('''
            INSERT INTO mystery_box_logs (user_id, box_price, won_amount, profit_loss, multiplier, was_jackpot)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, price, win, win - price, multiplier, was_jackpot), commit=True)
        
        # Record transactions
        db.execute('''
            INSERT INTO transactions (transaction_id, user_id, amount, final_amount, type, description)
            VALUES (?, ?, ?, ?, 'debit', ?)
        ''', (
            f"BOX{int(time.time())}{random.randint(1000,9999)}",
            user_id, price, price, f"Mystery box purchase (₹{price})"
        ), commit=True)
        
        db.execute('''
            INSERT INTO transactions (transaction_id, user_id, amount, final_amount, type, description)
            VALUES (?, ?, ?, ?, 'bonus', ?)
        ''', (
            f"WIN{int(time.time())}{random.randint(1000,9999)}",
            user_id, win, win, f"Mystery box win (₹{win})"
        ), commit=True)
        
        # Create result message
        if was_jackpot:
            result_emoji = "🎉🎊💰"
            result_text = f"🎉🎊 *JACKPOT!* 🎊🎉\nYou won *₹{win}*!"
        elif win > price * 1.5:
            result_emoji = "🌟✨"
            result_text = f"🌟✨ *Great Win!*\nYou won *₹{win}*!"
        elif win > price:
            result_emoji = "😊👍"
            result_text = f"😊👍 *Good Win!*\nYou won *₹{win}*!"
        else:
            result_emoji = "😅"
            result_text = f"😅 *Better luck next time!*\nYou won *₹{win}*"
        
        await query.edit_message_text(
            f"{ui.box('🎁 MYSTERY BOX RESULT', 50)}\n\n"
            f"💰 *Box Price:* ₹{price}\n"
            f"{result_emoji} *Result:* {result_text}\n"
            f"📊 *Multiplier:* {multiplier:.2f}x\n"
            f"💎 *Net Profit/Loss:* ₹{win - price}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{result_emoji}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 BACK", callback_data="menu_mystery")]]),
            parse_mode=ParseMode.HTML
        )
        
        logger.info(f"✅ Mystery box: User {user_id} - ₹{price} box won ₹{win}")
        
    except Exception as e:
        logger.error(f"❌ Mystery box failed: {e}")
        await query.edit_message_text(
            f"{ui.box('ERROR', 30)}\n\n❌ Failed to open mystery box. Please try again.",
            parse_mode=ParseMode.HTML
        )

# ============================================================================
# REFERRAL PROGRAM
# ============================================================================

async def referral_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display referral menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Get user data
    user = db.execute("SELECT * FROM users WHERE user_id=?", (user_id,), fetchone=True)
    
    # Get referral stats
    ref_count = db.execute(
        "SELECT COUNT(*) as count FROM referrals WHERE referrer_id=? AND status='completed'",
        (user_id,), fetchone=True
    )
    ref_count = ref_count['count'] if ref_count else 0
    
    ref_pending = db.execute(
        "SELECT COUNT(*) as count FROM referrals WHERE referrer_id=? AND status='pending'",
        (user_id,), fetchone=True
    )
    ref_pending = ref_pending['count'] if ref_pending else 0
    
    ref_earnings = db.execute(
        "SELECT SUM(bonus_amount) as total FROM referrals WHERE referrer_id=? AND bonus_paid=1",
        (user_id,), fetchone=True
    )
    ref_earnings = ref_earnings['total'] if ref_earnings and ref_earnings['total'] else 0
    
    # Generate referral link
    bot_info = await context.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={user['referral_code']}"
    
    text = (
        f"{ui.box('👥 REFERRAL PROGRAM', 50)}\n\n"
        f"💰 *Earn ₹{REFERRAL_BONUS} per referral!*\n\n"
        f"🔗 *Your Referral Link:*\n"
        f"`{ref_link}`\n\n"
        f"📊 *Your Statistics:*\n"
        f"• Total Referrals: *{ref_count}*\n"
        f"• Pending: *{ref_pending}*\n"
        f"• Total Earned: *₹{ref_earnings}*\n\n"
        f"📌 *How it works:*\n"
        f"1️⃣ Share your link with friends\n"
        f"2️⃣ They join using your link\n"
        f"3️⃣ You get ₹{REFERRAL_BONUS} instantly\n"
        f"4️⃣ They get ₹{WELCOME_BONUS} welcome bonus\n\n"
        f"🚀 *Start sharing now!*"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 SHARE LINK", url=f"https://t.me/share/url?url={ref_link}")],
        [InlineKeyboardButton("📋 COPY LINK", callback_data="copy_link")],
        [InlineKeyboardButton("👥 VIEW REFERRALS", callback_data="view_referrals")],
        [InlineKeyboardButton("🔙 BACK", callback_data="main_menu")]
    ])
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

async def copy_link_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle copy link button"""
    query = update.callback_query
    await query.answer("Link copied to clipboard!", show_alert=True)
    
    # The link is already displayed in the message, so just show confirmation

async def view_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View user's referrals"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    referrals = db.execute('''
        SELECT r.*, u.username, u.first_name, u.created_at as joined_date
        FROM referrals r
        JOIN users u ON r.referred_id = u.user_id
        WHERE r.referrer_id=?
        ORDER BY r.created_at DESC
        LIMIT 20
    ''', (user_id,), fetchall=True)
    
    text = f"{ui.box('👥 YOUR REFERRALS', 50)}\n\n"
    
    if not referrals:
        text += "You haven't referred anyone yet.\nShare your link to start earning!"
    else:
        for ref in referrals:
            status_emoji = "✅" if ref['status'] == 'completed' else "⏳"
            name = ref['first_name'] or f"User {ref['referred_id']}"
            username = f"@{ref['username']}" if ref['username'] else "No username"
            joined = ref['joined_date'][:10] if ref['joined_date'] else "Unknown"
            
            text += f"{status_emoji} *{name}*\n"
            text += f"  📱 {username}\n"
            text += f"  📅 Joined: {joined}\n"
            if ref['bonus_paid']:
                text += f"  💰 Bonus: ₹{ref['bonus_amount']} ✓\n"
            text += "\n"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 BACK", callback_data="menu_referral")]
    ])
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

# ============================================================================
# COUPON SYSTEM
# ============================================================================

async def coupon_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display coupon menu"""
    query = update.callback_query
    await query.answer()
    
    # Get active coupons
    coupons = db.execute(
        "SELECT * FROM coupons_master WHERE is_active=1 AND (valid_until IS NULL OR valid_until > CURRENT_TIMESTAMP) LIMIT 10",
        fetchall=True
    )
    
    text = f"{ui.box('🏷️ COUPONS & OFFERS', 50)}\n\n"
    
    if coupons:
        for coupon in coupons:
            if coupon['discount_type'] == 'percentage':
                discount_text = f"{coupon['discount_value']}% OFF"
            else:
                discount_text = f"₹{coupon['discount_value']} OFF"
            
            text += f"• *{coupon['code']}*: {discount_text}\n"
            if coupon['min_purchase'] > 0:
                text += f"  Min Purchase: ₹{coupon['min_purchase']}\n"
            text += f"  Uses Left: {coupon['max_uses'] - coupon['used_count']}\n\n"
    else:
        text += "No active coupons at the moment.\nCheck back later!\n\n"
    
    text += "📝 *Enter a coupon code below:*"
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 BACK", callback_data="main_menu")]
    ])
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
    return STATE_COUPON_ENTER

async def coupon_enter(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle coupon code entry"""
    code = update.message.text.strip().upper()
    user_id = update.effective_user.id
    
    # Validate coupon
    coupon = db.execute(
        "SELECT * FROM coupons_master WHERE code=? AND is_active=1 AND (valid_until IS NULL OR valid_until > CURRENT_TIMESTAMP)",
        (code,), fetchone=True
    )
    
    if not coupon:
        await update.message.reply_text(
            f"{ui.box('INVALID COUPON', 30)}\n\n❌ Invalid or expired coupon code.",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    
    # Check usage limit
    if coupon['used_count'] >= coupon['max_uses']:
        await update.message.reply_text(
            f"{ui.box('COUPON EXPIRED', 30)}\n\n❌ This coupon has reached its usage limit.",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    
    # Check if user already used
    used = db.execute(
        "SELECT id FROM coupon_usage WHERE code=? AND user_id=?",
        (code, user_id), fetchone=True
    )
    
    if used:
        await update.message.reply_text(
            f"{ui.box('ALREADY USED', 30)}\n\n❌ You have already used this coupon.",
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    
    # Apply coupon to user's next purchase
    context.user_data['active_coupon'] = {
        'code': code,
        'type': coupon['discount_type'],
        'value': coupon['discount_value'],
        'min_purchase': coupon['min_purchase']
    }
    
    # Mark as used (will be finalized when purchase is made)
    db.execute(
        "INSERT INTO coupon_usage (code, user_id) VALUES (?, ?)",
        (code, user_id), commit=True
    )
    
    db.execute(
        "UPDATE coupons_master SET used_count = used_count + 1 WHERE code=?",
        (code,), commit=True
    )
    
    discount_text = f"{coupon['discount_value']}% OFF" if coupon['discount_type'] == 'percentage' else f"₹{coupon['discount_value']} OFF"
    
    await update.message.reply_text(
        f"{ui.box('✅ COUPON APPLIED', 40)}\n\n"
        f"🏷️ *Coupon:* {code}\n"
        f"💰 *Discount:* {discount_text}\n\n"
        f"Your next purchase will get this discount!",
        parse_mode=ParseMode.HTML
    )
    
    return ConversationHandler.END

# ============================================================================
# BULK PURCHASE
# ============================================================================

async def bulk_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display bulk purchase menu"""
    query = update.callback_query
    await query.answer()
    
    text = (
        f"{ui.box('📦 BULK PURCHASE', 50)}\n\n"
        f"✨ *Volume Discounts:*\n"
    )
    
    for qty in sorted(BULK_DISCOUNTS.keys()):
        if BULK_DISCOUNTS[qty] > 0:
            text += f"• {qty}+ cards: *{BULK_DISCOUNTS[qty]}% OFF*\n"
    
    text += f"\n📌 *How it works:*\n"
    text += f"1️⃣ Select a gift card category\n"
    text += f"2️⃣ Choose card and quantity\n"
    text += f"3️⃣ Get automatic bulk discount\n\n"
    text += f"*Select category:*"
    
    await query.edit_message_text(
        text,
        reply_markup=gift_categories_keyboard(),
        parse_mode=ParseMode.HTML
    )
    context.user_data['bulk_mode'] = True

# ============================================================================
# SUPPORT TICKET SYSTEM
# ============================================================================

async def support_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display support menu"""
    query = update.callback_query
    await query.answer()
    
    text = (
        f"{ui.box('🆘 CUSTOMER SUPPORT', 50)}\n\n"
        f"❓ *Frequently Asked Questions:*\n\n"
        f"1️⃣ *How to buy a gift card?*\n"
        f"   → Add money → Select card → Enter email\n\n"
        f"2️⃣ *How long does delivery take?*\n"
        f"   → Gift cards: 2-5 minutes\n"
        f"   → Recharges: 5-15 minutes\n\n"
        f"3️⃣ *Payment not credited?*\n"
        f"   → Send screenshot + UTR to admin\n\n"
        f"4️⃣ *Card not received?*\n"
        f"   → Check spam folder\n"
        f"   → Contact support with order ID\n\n"
        f"📝 *Type your issue below and we'll respond within 24h*"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 BACK", callback_data="main_menu")]
    ])
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )
    return STATE_SUPPORT_MESSAGE

async def support_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle support message"""
    message = update.message.text.strip()
    user = update.effective_user
    
    if len(message) < 10:
        await update.message.reply_text(
            f"{ui.box('MESSAGE TOO SHORT', 30)}\n\n❌ Please describe your issue in at least 10 characters.",
            parse_mode=ParseMode.HTML
        )
        return STATE_SUPPORT_MESSAGE
    
    try:
        # Create ticket
        ticket_id = f"TKT{int(time.time())}{random.randint(1000,9999)}"
        
        db.execute('''
            INSERT INTO support_tickets (ticket_id, user_id, message, status)
            VALUES (?, ?, ?, 'open')
        ''', (ticket_id, user.id, message), commit=True)
        
        # Notify admin
        admin_text = (
            f"🆘 *NEW SUPPORT TICKET*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎫 *Ticket ID:* `{ticket_id}`\n"
            f"👤 *User:* {user.first_name}\n"
            f"🆔 *ID:* `{user.id}`\n"
            f"👤 *Username:* @{user.username}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💬 *Message:*\n{message}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        
        await context.bot.send_message(
            chat_id=ADMIN_CHANNEL_ID,
            text=admin_text,
            parse_mode=ParseMode.MARKDOWN
        )
        
        await update.message.reply_text(
            f"{ui.box('✅ SUPPORT TICKET CREATED', 40)}\n\n"
            f"🎫 *Ticket ID:* `{ticket_id}`\n\n"
            f"Your issue has been recorded.\n"
            f"Our support team will contact you within 24 hours.",
            parse_mode=ParseMode.HTML
        )
        
        logger.info(f"✅ Support ticket created: {ticket_id} for user {user.id}")
        
    except Exception as e:
        logger.error(f"❌ Support ticket failed: {e}")
        await update.message.reply_text(
            f"{ui.box('ERROR', 30)}\n\n❌ Failed to create support ticket. Please try again.",
            parse_mode=ParseMode.HTML
        )
    
    return ConversationHandler.END

# ============================================================================
# STATISTICS MENU
# ============================================================================

async def stats_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display statistics menu"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # Get user stats
    user = db.execute("SELECT * FROM users WHERE user_id=?", (user_id,), fetchone=True)
    
    # Get purchase stats
    purchases = db.execute(
        "SELECT COUNT(*) as count, SUM(total_price) as total FROM purchases WHERE user_id=?",
        (user_id,), fetchone=True
    )
    
    # Get transaction stats
    transactions = db.execute(
        "SELECT COUNT(*) as count, SUM(amount) as total FROM transactions WHERE user_id=? AND type='credit'",
        (user_id,), fetchone=True
    )
    
    # Get referral stats
    referrals = db.execute(
        "SELECT COUNT(*) as count FROM referrals WHERE referrer_id=?",
        (user_id,), fetchone=True
    )
    
    # Get daily reward stats
    daily = db.execute(
        "SELECT COUNT(*) as count, SUM(amount) as total FROM daily_rewards WHERE user_id=?",
        (user_id,), fetchone=True
    )
    
    # Get mystery box stats
    mystery = db.execute(
        "SELECT COUNT(*) as count, SUM(won_amount) as total, AVG(won_amount) as avg FROM mystery_box_logs WHERE user_id=?",
        (user_id,), fetchone=True
    )
    
    text = (
        f"{ui.box('📊 YOUR STATISTICS', 50)}\n\n"
        f"👤 *{user['first_name']}* {user_badge(user['total_purchases'])}\n\n"
        f"💰 *Financial Stats:*\n"
        f"• Main Balance: ₹{user['balance_main']}\n"
        f"• Bonus Balance: ₹{user['balance_bonus']}\n"
        f"• Total Recharged: ₹{user['total_recharged']}\n"
        f"• Total Spent: ₹{user['total_spent']}\n\n"
        f"🛒 *Purchase Stats:*\n"
        f"• Total Purchases: {purchases['count'] if purchases else 0}\n"
        f"• Amount Spent: ₹{purchases['total'] if purchases else 0}\n\n"
        f"📈 *Transaction Stats:*\n"
        f"• Total Credits: {transactions['count'] if transactions else 0}\n"
        f"• Credit Amount: ₹{transactions['total'] if transactions else 0}\n\n"
        f"👥 *Referral Stats:*\n"
        f"• Total Referrals: {referrals['count'] if referrals else 0}\n\n"
        f"📅 *Daily Rewards:*\n"
        f"• Days Claimed: {daily['count'] if daily else 0}\n"
        f"• Total Earned: ₹{daily['total'] if daily else 0}\n\n"
        f"🎁 *Mystery Box:*\n"
        f"• Boxes Opened: {mystery['count'] if mystery else 0}\n"
        f"• Total Won: ₹{mystery['total'] if mystery else 0}\n"
        f"• Average Win: ₹{int(mystery['avg']) if mystery and mystery['avg'] else 0}\n"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 BACK", callback_data="main_menu")]
    ])
    
    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

# ============================================================================
# MAIN BUTTON HANDLER
# ============================================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main button handler"""
    query = update.callback_query
    data = query.data
    
    # Handle noop buttons
    if data == "noop":
        await query.answer()
        return
    
    # Menu navigation
    if data == "main_menu":
        await start(update, context)
    
    elif data == "verify":
        await verify_callback(update, context)
    
    # Gift card menus
    elif data == "menu_gift":
        await gift_menu(update, context)
    elif data.startswith("gift_cat_"):
        await gift_category(update, context)
    elif data.startswith("gift_card_"):
        await gift_card_details(update, context)
    elif data.startswith("buy_gift_"):
        return await buy_gift_start(update, context)
    
    # Game menus
    elif data == "menu_game":
        await game_menu(update, context)
    elif data.startswith("game_select_"):
        await game_selected(update, context)
    elif data.startswith("game_amount_"):
        return await game_amount_selected(update, context)
    
    # Mobile recharge
    elif data == "menu_mobile":
        return await mobile_menu(update, context)
    elif data.startswith("mobile_op_"):
        return await mobile_operator_selected(update, context)
    elif data.startswith("mobile_plan_"):
        return await mobile_plan_selected(update, context)
    
    # DTH recharge (similar pattern - simplified for brevity)
    elif data == "menu_dth":
        await query.edit_message_text("DTH recharge coming soon!")
    
    # Fiber recharge (similar pattern - simplified for brevity)
    elif data == "menu_fiber":
        await query.edit_message_text("Fiber recharge coming soon!")
    
    # Wallet
    elif data == "menu_wallet":
        await wallet_menu(update, context)
    elif data == "wallet_history":
        # Implement wallet history
        await query.edit_message_text("Transaction history coming soon!")
    
    # Top up
    elif data == "menu_topup":
        await topup_menu(update, context)
    elif data.startswith("amount_"):
        await amount_selected(update, context)
    
    # Payment
    elif data == "paid":
        return await handle_paid(update, context)
    
    # Transfer
    elif data == "menu_transfer":
        return await transfer_menu(update, context)
    elif data == "transfer_confirm":
        return await transfer_confirm(update, context)
    
    # Mystery box
    elif data == "menu_mystery":
        await mystery_box_menu(update, context)
    elif data.startswith("mystery_open_"):
        await mystery_box_open(update, context)
    
    # Card exchange
    elif data == "menu_exchange":
        await query.edit_message_text("Card exchange coming soon!")
    
    # Referral
    elif data == "menu_referral":
        await referral_menu(update, context)
    elif data == "copy_link":
        await copy_link_callback(update, context)
    elif data == "view_referrals":
        await view_referrals(update, context)
    
    # Daily reward
    elif data == "menu_daily":
        await daily_reward(update, context)
    
    # Coupon
    elif data == "menu_coupon":
        return await coupon_menu(update, context)
    
    # Bulk purchase
    elif data == "menu_bulk":
        await bulk_menu(update, context)
    
    # Gift send
    elif data == "menu_gift_send":
        await query.edit_message_text("Gift sending coming soon!")
    
    # Price alerts
    elif data == "menu_alert":
        await query.edit_message_text("Price alerts coming soon!")
    
    # Statistics
    elif data == "menu_stats":
        await stats_menu(update, context)
    
    # Support
    elif data == "menu_support":
        return await support_menu(update, context)
    
    # Settings
    elif data == "menu_settings":
        await query.edit_message_text("Settings coming soon!")
    
    # Cancel
    elif data == "cancel":
        context.user_data.clear()
        await query.edit_message_text(
            f"{ui.box('❌ CANCELLED', 30)}\n\nOperation cancelled.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 MAIN MENU", callback_data="main_menu")]]),
            parse_mode=ParseMode.HTML
        )
        return ConversationHandler.END
    
    else:
        await query.answer("Unknown command")

# ============================================================================
# CANCEL HANDLER
# ============================================================================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    context.user_data.clear()
    await update.message.reply_text(
        f"{ui.box('❌ CANCELLED', 30)}\n\nOperation cancelled.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 MAIN MENU", callback_data="main_menu")]]),
        parse_mode=ParseMode.HTML
    )
    return ConversationHandler.END

# ============================================================================
# ERROR HANDLER
# ============================================================================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler"""
    logger.error(f"❌ Error: {context.error}", exc_info=True)
    
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text(
                f"{ui.box('❌ ERROR', 30)}\n\nAn error occurred. Please try again or use /start.",
                parse_mode=ParseMode.HTML
            )
    except:
        pass

# ============================================================================
# ADMIN COMMANDS
# ============================================================================

@admin_only
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin statistics command"""
    # Get overall stats
    total_users = db.execute("SELECT COUNT(*) as count FROM users", fetchone=True)['count']
    active_today = db.execute(
        "SELECT COUNT(*) as count FROM users WHERE DATE(last_active)=DATE('now')",
        fetchone=True
    )['count']
    new_today = db.execute(
        "SELECT COUNT(*) as count FROM users WHERE DATE(created_at)=DATE('now')",
        fetchone=True
    )['count']
    
    total_purchases = db.execute("SELECT COUNT(*) as count FROM purchases", fetchone=True)['count']
    total_revenue = db.execute("SELECT SUM(total_price) as total FROM purchases", fetchone=True)['total'] or 0
    
    pending_verifications = db.execute(
        "SELECT COUNT(*) as count FROM verifications WHERE status='pending'",
        fetchone=True
    )['count']
    
    open_tickets = db.execute(
        "SELECT COUNT(*) as count FROM support_tickets WHERE status='open'",
        fetchone=True
    )['count']
    
    total_balance = db.execute(
        "SELECT SUM(balance_main) + SUM(balance_bonus) as total FROM users",
        fetchone=True
    )['total'] or 0
    
    text = (
        f"{ui.box('📊 ADMIN STATISTICS', 50)}\n\n"
        f"👥 *Users:*\n"
        f"• Total: {total_users:,}\n"
        f"• Active Today: {active_today}\n"
        f"• New Today: {new_today}\n\n"
        f"💰 *Finances:*\n"
        f"• Total Revenue: ₹{total_revenue:,}\n"
        f"• Total Balance: ₹{total_balance:,}\n\n"
        f"🛒 *Purchases:* {total_purchases:,}\n\n"
        f"⏳ *Pending:* {pending_verifications}\n"
        f"🎫 *Open Tickets:* {open_tickets}\n"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📥 EXPORT USERS", callback_data="admin_export_users")],
        [InlineKeyboardButton("📢 BROADCAST", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📦 STOCK", callback_data="admin_stock")],
        [InlineKeyboardButton("🔙 BACK", callback_data="main_menu")]
    ])
    
    await update.message.reply_text(
        text,
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )

@admin_only
async def admin_export_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export users to CSV"""
    users = db.execute("SELECT * FROM users ORDER BY created_at DESC", fetchall=True)
    
    if not users:
        await update.message.reply_text("No users found.")
        return
    
    # Create CSV
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=users[0].keys())
    writer.writeheader()
    for user in users:
        writer.writerow(user)
    
    output.seek(0)
    
    await update.message.reply_document(
        document=output.getvalue().encode('utf-8'),
        filename=f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        caption="📊 Users Export"
    )

@admin_only
async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message to all users"""
    if not context.args:
        await update.message.reply_text(
            f"{ui.box('📢 BROADCAST', 30)}\n\nUsage: `/broadcast Your message here`",
            parse_mode=ParseMode.HTML
        )
        return
    
    message = " ".join(context.args)
    
    # Get all users
    users = db.execute("SELECT user_id FROM users", fetchall=True)
    
    status_msg = await update.message.reply_text(f"📢 Broadcasting to {len(users)} users...")
    
    sent = 0
    failed = 0
    
    broadcast_text = (
        f"{ui.box('📢 ADMIN BROADCAST', 40)}\n\n"
        f"{message}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"*Gift Card Bot*"
    )
    
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=user['user_id'],
                text=broadcast_text,
                parse_mode=ParseMode.HTML
            )
            sent += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            failed += 1
            logger.error(f"Broadcast to {user['user_id']} failed: {e}")
        
        if (sent + failed) % 10 == 0:
            await status_msg.edit_text(f"📢 Progress: {sent} sent, {failed} failed")
    
    await status_msg.edit_text(f"✅ Broadcast complete! Sent: {sent}, Failed: {failed}")
    
    # Log action
    db.execute('''
        INSERT INTO admin_logs (admin_id, action, details)
        VALUES (?, 'broadcast', ?)
    ''', (ADMIN_ID, f"Sent to {sent} users, failed {failed}"), commit=True)

@admin_only
async def admin_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manage stock"""
    # Get low stock items
    low_stock = db.execute(
        "SELECT * FROM gift_stock WHERE stock <= low_alert ORDER BY stock ASC LIMIT 20",
        fetchall=True
    )
    
    text = f"{ui.box('📦 STOCK MANAGEMENT', 50)}\n\n"
    
    if low_stock:
        text += "🔴 *Low Stock Alerts:*\n"
        for item in low_stock:
            card = GIFT_CARDS.get(item['card_id'], {})
            text += f"• {card.get('emoji', '🎁')} {card.get('name', item['card_id'])} ₹{item['denomination']}: {item['stock']} left\n"
    else:
        text += "✅ All items have sufficient stock.\n\n"
    
    text += "\n*Commands:*\n"
    text += "• `/addstock CARD_ID DENOM QTY` - Add stock\n"
    text += "• `/setstock CARD_ID DENOM QTY` - Set stock\n"
    text += "• `/checkstock` - View all stock\n"
    
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

@admin_only
async def admin_add_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add stock to a card"""
    try:
        card_id = context.args[0].lower()
        denom = int(context.args[1])
        qty = int(context.args[2])
        
        if card_id not in GIFT_CARDS:
            await update.message.reply_text("❌ Invalid card ID")
            return
        
        db.execute('''
            UPDATE gift_stock SET stock = stock + ?, updated_at=CURRENT_TIMESTAMP
            WHERE card_id=? AND denomination=?
        ''', (qty, card_id, denom), commit=True)
        
        card = GIFT_CARDS[card_id]
        await update.message.reply_text(f"✅ Added {qty} stock to {card['name']} ₹{denom}")
        
        # Log action
        db.execute('''
            INSERT INTO admin_logs (admin_id, action, details)
            VALUES (?, 'add_stock', ?)
        ''', (ADMIN_ID, f"{card_id} {denom} +{qty}"), commit=True)
        
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Usage: /addstock CARD_ID DENOM QUANTITY")

@admin_only
async def admin_set_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set exact stock for a card"""
    try:
        card_id = context.args[0].lower()
        denom = int(context.args[1])
        qty = int(context.args[2])
        
        if card_id not in GIFT_CARDS:
            await update.message.reply_text("❌ Invalid card ID")
            return
        
        db.execute('''
            UPDATE gift_stock SET stock = ?, updated_at=CURRENT_TIMESTAMP
            WHERE card_id=? AND denomination=?
        ''', (qty, card_id, denom), commit=True)
        
        card = GIFT_CARDS[card_id]
        await update.message.reply_text(f"✅ Set {card['name']} ₹{denom} stock to {qty}")
        
        # Log action
        db.execute('''
            INSERT INTO admin_logs (admin_id, action, details)
            VALUES (?, 'set_stock', ?)
        ''', (ADMIN_ID, f"{card_id} {denom} = {qty}"), commit=True)
        
    except (IndexError, ValueError):
        await update.message.reply_text("❌ Usage: /setstock CARD_ID DENOM QUANTITY")

@admin_only
async def admin_check_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check all stock"""
    stock = db.execute("SELECT * FROM gift_stock ORDER BY card_id, denomination", fetchall=True)
    
    text = f"{ui.box('📦 COMPLETE STOCK', 50)}\n\n"
    
    current_card = None
    for item in stock:
        if item['card_id'] != current_card:
            current_card = item['card_id']
            card = GIFT_CARDS.get(current_card, {})
            text += f"\n{card.get('emoji', '🎁')} *{card.get('name', current_card)}:*\n"
        
        indicator = "🟢" if item['stock'] > 50 else "🟡" if item['stock'] > 10 else "🔴" if item['stock'] > 0 else "⚫"
        text += f"  {indicator} ₹{item['denomination']}: {item['stock']}\n"
    
    # Split into multiple messages if too long
    if len(text) > 4000:
        # Send as file
        with open('stock_report.txt', 'w') as f:
            f.write(text)
        await update.message.reply_document(
            document=open('stock_report.txt', 'rb'),
            filename=f"stock_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)

@admin_only
async def admin_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View pending verifications"""
    pending = db.execute(
        "SELECT * FROM verifications WHERE status='pending' ORDER BY created_at ASC",
        fetchall=True
    )
    
    if not pending:
        await update.message.reply_text("✅ No pending verifications")
        return
    
    text = f"{ui.box('⏳ PENDING VERIFICATIONS', 50)}\n\n"
    
    for p in pending[:10]:
        user = db.execute("SELECT * FROM users WHERE user_id=?", (p['user_id'],), fetchone=True)
        text += f"• ID: `{p['id']}`\n"
        text += f"  👤 User: {user['first_name']} (@{user['username']})\n"
        text += f"  💰 Amount: ₹{p['amount']}\n"
        text += f"  ✅ Credit: ₹{p['final_amount']}\n"
        text += f"  🔢 UTR: `{p['utr']}`\n"
        text += f"  ⏰ {p['created_at'][:19]}\n\n"
    
    if len(pending) > 10:
        text += f"... and {len(pending) - 10} more"
    
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

@admin_only
async def admin_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List users with pagination"""
    page = 1
    if context.args and context.args[0].isdigit():
        page = int(context.args[0])
    
    per_page = 10
    offset = (page - 1) * per_page
    
    users = db.execute(
        "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (per_page, offset), fetchall=True
    )
    
    total = db.execute("SELECT COUNT(*) as count FROM users", fetchone=True)['count']
    total_pages = (total + per_page - 1) // per_page
    
    text = f"{ui.box(f'👥 USERS (Page {page}/{total_pages})', 50)}\n\n"
    
    for user in users:
        badge = user_badge(user['total_purchases'])
        text += f"• {badge} *{user['first_name']}* (@{user['username']})\n"
        text += f"  🆔 `{user['user_id']}` | 💰 ₹{user['balance_main'] + user['balance_bonus']}\n"
        text += f"  📅 Joined: {user['created_at'][:10]}\n\n"
    
    keyboard = []
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("◀️ PREV", callback_data=f"admin_users_page_{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("NEXT ▶️", callback_data=f"admin_users_page_{page+1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("🔙 BACK", callback_data="admin_panel")])
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None,
        parse_mode=ParseMode.HTML
    )

# ============================================================================
# POST INITIALIZATION
# ============================================================================

async def post_init(app: Application):
    """Setup after bot initialization"""
    # Set bot commands
    commands = [
        BotCommand("start", "🚀 Start the bot"),
        BotCommand("stats", "📊 Statistics (Admin)"),
        BotCommand("pending", "⏳ Pending verifications (Admin)"),
        BotCommand("users", "👥 List users (Admin)"),
        BotCommand("addstock", "📦 Add stock (Admin)"),
        BotCommand("setstock", "📊 Set stock (Admin)"),
        BotCommand("checkstock", "📋 Check stock (Admin)"),
        BotCommand("broadcast", "📢 Broadcast (Admin)"),
        BotCommand("cancel", "❌ Cancel"),
    ]
    await app.bot.set_my_commands(commands)
    
    # Get bot info
    bot_info = await app.bot.get_me()
    global BOT_USERNAME
    BOT_USERNAME = bot_info.username
    
    # Verify admin channel
    try:
        await app.bot.send_message(
            chat_id=ADMIN_CHANNEL_ID,
            text=f"{ui.box('✅ BOT STARTED', 40)}\n\n"
                 f"🤖 *{BOT_USERNAME}* is now online!\n"
                 f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            parse_mode=ParseMode.HTML
        )
        logger.success("✅ Admin channel verified")
    except Exception as e:
        logger.warning(f"⚠️ Admin channel not accessible: {e}")
    
    # Initialize stock for new cards
    for card_id in GIFT_CARDS:
        for denom in GIFT_DENOMINATIONS:
            db.execute('''
                INSERT OR IGNORE INTO gift_stock (card_id, denomination, stock)
                VALUES (?, ?, 0)
            ''', (card_id, denom), commit=True)
    
    # Initialize game stock
    for game_id in GAME_RECHARGES:
        if game_id in GAME_PRICES:
            for amount in GAME_PRICES[game_id]:
                db.execute('''
                    INSERT OR IGNORE INTO game_stock (game_id, amount, stock)
                    VALUES (?, ?, 0)
                ''', (game_id, amount), commit=True)
    
    logger.success("✅ Bot initialization complete!")
    print("\n" + "="*60)
    print(f"      🎁 {BOT_USERNAME} - PREMIUM GIFT CARD BOT")
    print("="*60)
    print(f"✅ Bot is running...")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print(f"📢 Main Channel: {MAIN_CHANNEL}")
    print(f"📊 Proof Channel: {PROOF_CHANNEL}")
    print(f"💳 UPI ID: {UPI_ID}")
    print("="*60 + "\n")

# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main function"""
    # Create application
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # ===== COMMAND HANDLERS =====
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    
    # Admin commands
    app.add_handler(CommandHandler("stats", admin_stats))
    app.add_handler(CommandHandler("pending", admin_pending))
    app.add_handler(CommandHandler("users", admin_users))
    app.add_handler(CommandHandler("addstock", admin_add_stock))
    app.add_handler(CommandHandler("setstock", admin_set_stock))
    app.add_handler(CommandHandler("checkstock", admin_check_stock))
    app.add_handler(CommandHandler("broadcast", admin_broadcast))
    
    # ===== CONVERSATION HANDLERS =====
    
    # Payment verification conversation
    payment_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_paid, pattern="^paid$")],
        states={
            STATE_SCREENSHOT: [MessageHandler(filters.PHOTO, handle_screenshot)],
            STATE_UTR: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_utr)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(payment_conv)
    
    # Gift card purchase conversation
    gift_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(buy_gift_start, pattern="^buy_gift_")],
        states={
            STATE_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_email)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(gift_conv)
    
    # Mobile recharge conversation
    mobile_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(mobile_operator_selected, pattern="^mobile_op_")],
        states={
            STATE_MOBILE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, mobile_number_input)],
            STATE_MOBILE_PLAN: [CallbackQueryHandler(mobile_plan_selected, pattern="^mobile_plan_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(mobile_conv)
    
    # Game recharge conversation
    game_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(game_amount_selected, pattern="^game_amount_")],
        states={
            STATE_GAME_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, game_id_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(game_conv)
    
    # Wallet transfer conversation
    transfer_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(transfer_menu, pattern="^menu_transfer$")],
        states={
            STATE_WALLET_TRANSFER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, transfer_recipient_input)],
            STATE_WALLET_TRANSFER_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, transfer_amount_input)],
            STATE_WALLET_TRANSFER_CONFIRM: [CallbackQueryHandler(transfer_confirm, pattern="^transfer_confirm$")],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(transfer_conv)
    
    # Coupon conversation
    coupon_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(coupon_menu, pattern="^menu_coupon$")],
        states={
            STATE_COUPON_ENTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, coupon_enter)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(coupon_conv)
    
    # Support conversation
    support_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(support_menu, pattern="^menu_support$")],
        states={
            STATE_SUPPORT_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, support_message)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(support_conv)
    
    # ===== CALLBACK HANDLERS =====
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^(approve_|reject_)"))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # ===== ERROR HANDLER =====
    app.add_error_handler(error_handler)
    
    # ===== START BOT =====
    try:
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
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.critical(f"❌ Fatal error: {e}")
    finally:
        # Close database connections
        db.close_all()
        logger.info("✅ Database connections closed")

if __name__ == "__main__":
    main()
