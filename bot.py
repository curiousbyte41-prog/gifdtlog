#!/usr/bin/env python3
"""
🔥 ULTIMATE AUTO-PROMO + PROOF BOT 🔥
- Auto proofs in groups (successful purchase + delivery)
- Auto promotions in channels
- Add/remove multiple groups/channels via commands
- 35+ stylish names with emojis
- 10+ message formats
- Runs 24/7 even when you're offline
"""

import os
import sys
import json
import logging
import asyncio
import random
import sqlite3
from datetime import datetime
from functools import wraps

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters, ContextTypes
)
from telegram.constants import ParseMode

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("ADMIN_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("ADMIN_BOT_TOKEN")

MAIN_BOT_USERNAME = "@GIFT_CARD_41BOT"  # Your main bot
ADMIN_ID = int(os.environ.get("ADMIN_ID", "6185091342"))

# Database
DB_PATH = "channels.db"

# ─────────────────────────────────────────────────────────────
# CONVERSATION STATES
# ─────────────────────────────────────────────────────────────
ADD_GROUP, ADD_CHANNEL, REMOVE_TARGET = range(3)

# ─────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# DATABASE MANAGER
# ─────────────────────────────────────────────────────────────
class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.c = self.conn.cursor()
        self._init_db()
    
    def _init_db(self):
        # Groups table (for proofs)
        self.c.execute('''CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT UNIQUE,
            name TEXT,
            added_by INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Channels table (for promotions)
        self.c.execute('''CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT UNIQUE,
            name TEXT,
            added_by INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        self.conn.commit()
        logger.info("✅ Database ready")
    
    def add_group(self, chat_id, name, added_by):
        try:
            self.c.execute(
                "INSERT OR IGNORE INTO groups (chat_id, name, added_by) VALUES (?, ?, ?)",
                (chat_id, name, added_by)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Add group error: {e}")
            return False
    
    def remove_group(self, chat_id):
        self.c.execute("DELETE FROM groups WHERE chat_id=?", (chat_id,))
        self.conn.commit()
        return self.c.rowcount > 0
    
    def get_all_groups(self):
        self.c.execute("SELECT chat_id, name FROM groups ORDER BY added_at")
        return self.c.fetchall()
    
    def add_channel(self, chat_id, name, added_by):
        try:
            self.c.execute(
                "INSERT OR IGNORE INTO channels (chat_id, name, added_by) VALUES (?, ?, ?)",
                (chat_id, name, added_by)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Add channel error: {e}")
            return False
    
    def remove_channel(self, chat_id):
        self.c.execute("DELETE FROM channels WHERE chat_id=?", (chat_id,))
        self.conn.commit()
        return self.c.rowcount > 0
    
    def get_all_channels(self):
        self.c.execute("SELECT chat_id, name FROM channels ORDER BY added_at")
        return self.c.fetchall()

db = Database()

# ─────────────────────────────────────────────────────────────
# STYLISH NAMES (35+ with emojis)
# ─────────────────────────────────────────────────────────────
STYLISH_NAMES = [
    "✦ 𝙕𝙮𝙧𝙤 ⚡", "『ＲＡＸＥＬ』☠", "𓆩⚝𓆪 𝑽𝒐𝒓𝒕𝒆𝒙 𓆩⚝𓆪",
    "꧁༒ 𝕶𝖗𝖞𝖙𝖔𝖓 ༒꧂", "★彡 ᴢᴇʀɪᴏɴ 彡★", "⚡ 𝐃𝐫𝐚𝐤𝐨 ⚡",
    "༺ZΛYЯӨ༻", "⫷ ʀʏᴢᴇɴ ᴋɪɴɢ ⫸", "𓆩♛𓆪 𝙑𝙚𝙡𝙩𝙤𝙭 𓆩♛𓆪",
    "꧁𓊈𒆜𝕹𝖞𝖗𝖔𝖝𒆜𓊉꧂", "✧ 𝑨𝒙𝒊𝒐𝒏 ✧", "꧁☬ 𝓡𝓮𝔁𝓸𝓷 ☬꧂",
    "✦ 𝙕𝙚𝙣𝙩𝙧𝙤 ⚡", "『ＴＯＲＶＥＸ』☠", "𓆩⚝𓆪 𝑽𝒊𝒓𝒐𝒙 𓆩⚝𓆪",
    "꧁༒ 𝕷𝖊𝖝𝖔𝖗 ༒꧂", "★彡 ᴠᴇʀᴏɴ 彡★", "⚡ 𝐙𝐲𝐧𝐨𝐱 ⚡",
    "༺KЯӨПӨ༻", "⫷ ᴅʀᴀᴠᴏɴ ᴋɪɴɢ ⫸", "𓆩♛𓆪 𝙏𝙤𝙧𝙯𝙚𝙣 𓆩♛𓆪",
    "꧁𓊈𒆜𝕽𝖆𝖛𝖔𝖓𒆜𓊉꧂", "✧ 𝑽𝒐𝒓𝒏𝒆𝒙 ✧", "꧁☬ 𝓚𝓻𝓮𝓿𝓸𝔁 ☬꧂",
    "✦ 𝙕𝙚𝙫𝙧𝙤𝙣 ⚡", "『ＸＥＲＯＮ』☠", "𓆩⚝𓆪 𝑻𝒓𝒐𝒏𝒊𝒙 𓆩⚝𓆪",
    "꧁༒ 𝕾𝖙𝖔𝖗𝖎𝖝 ༒꧂", "★彡 ᴠᴇʀᴛᴏɴ 彡★", "⚡ 𝐙𝐞𝐧𝐨𝐱 ⚡",
    "༺VΛXӨП༻", "⫷ ʀᴇᴠᴏx ᴋɪɴɢ ⫸", "𓆩♛𓆪 𝙏𝙧𝙮𝙭𝙤𝙣 𓆩♛𓆪",
    "꧁𓊈𒆜𝕯𝖗𝖎𝖝𝖔𝖓𒆜𓊉꧂", "✧ 𝑵𝒆𝒙𝒐𝒏 ✧", "꧁☬ 𝓥𝓮𝔁𝓸𝓷 ☬꧂",
    "✦ 𝙕𝙞𝙧𝙤𝙣 ⚡", "『ＴＲＹＶＥＸ』☠", "𓆩⚝𓆪 𝑽𝒐𝒓𝒆𝒙 𓆩⚝𓆪",
    "꧁༒ 𝕶𝖆𝖎𝖗𝖔𝖓 ༒꧂", "★彡 ᴅʀᴇxᴏɴ 彡★", "⚡ 𝐙𝐚𝐯𝐢𝐨𝐧 ⚡",
    "༺RΛXӨЯ༻", "⫷ ᴠᴏʀᴛᴇx ᴋɪɴɢ ⫸", "𓆩♛𓆪 𝙍𝙮𝙭𝙤𝙣 𓆩♛𓆪",
    "꧁𓊈𒆜𝕶𝖗𝖊𝖝𝖔𝖓𒆜𓊉꧂", "Aman", "Rahul", "Arjun", "Vikas",
    "Ankit", "Deepak", "Karan", "Sahil", "Ajay", "Raj", "Rakesh",
    "Nitin", "Mohit", "Manish", "Varun", "Aditya", "Akash",
    "Abhishek", "Tarun", "Ravi", "Sumit", "Shivam", "Amit",
    "Sandeep", "Pankaj", "Pradeep"
]

# ─────────────────────────────────────────────────────────────
# GIFT CARDS
# ─────────────────────────────────────────────────────────────
CARDS = [
    "🟦 AMAZON", "🟩 PLAY STORE", "🎟️ BOOKMYSHOW", 
    "🛍️ MYNTRA", "📦 FLIPKART", "🍕 ZOMATO", 
    "🛒 BIG BASKET", "🎮 GOOGLE PLAY", "🎬 NETFLIX", 
    "🎵 SPOTIFY", "💳 AMAZON PAY", "🏏 DREAM11",
    "🎁 GIFT VOUCHER", "🛍️ AJIO", "👕 MYNTRA",
    "📱 APPLE", "💻 DELL", "🎧 BOAT", "⌚ SAMSUNG"
]

# ─────────────────────────────────────────────────────────────
# AMOUNTS
# ─────────────────────────────────────────────────────────────
AMOUNTS = [500, 1000, 2000, 3000, 5000, 10000]

# ─────────────────────────────────────────────────────────────
# PROMO MESSAGES (TRUST BUILDING)
# ─────────────────────────────────────────────────────────────
PROMO_MESSAGES = [
    {
        "title": "🎁 *TRUSTED BY 10,000+ USERS* 🎁",
        "content": [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "🌟 *Why 10,000+ users trust us:*",
            "",
            "✅ *Instant Delivery* - Cards in 2 minutes",
            "✅ *100% Working Codes* - Guaranteed",
            "✅ *24/7 Support* - Always here to help",
            "✅ *Best Prices* - Up to 80% OFF",
            "✅ *Referral Bonus* - Earn ₹2 per friend",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "💰 *Sample Prices:*",
            "• Amazon ₹500 → Just ₹100",
            "• Flipkart ₹1000 → Just ₹200",
            "• Play Store ₹500 → Just ₹100",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]
    },
    {
        "title": "⚡ *FASTEST DELIVERY GUARANTEED* ⚡",
        "content": [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "🚀 *Delivery Time:*",
            "• Amazon: 2-5 minutes",
            "• Flipkart: 2-5 minutes",
            "• Play Store: 2-5 minutes",
            "• BookMyShow: 2-5 minutes",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "📊 *Our Stats:*",
            "• 50,000+ Successful Deliveries",
            "• 4.9/5 Rating from 8,000+ Reviews",
            "• 99.9% Uptime",
            "• 24/7 Customer Support",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]
    },
    {
        "title": "💰 *BEST PRICES IN INDIA* 💰",
        "content": [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "🔥 *Compare & Save:*",
            "",
            "• Amazon ₹500 → *₹100* (80% OFF)",
            "• Flipkart ₹1000 → *₹200* (80% OFF)",
            "• Play Store ₹500 → *₹100* (80% OFF)",
            "• Myntra ₹2000 → *₹400* (80% OFF)",
            "• Zomato ₹500 → *₹100* (80% OFF)",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "✨ *No Hidden Charges*",
            "✨ *Instant Email Delivery*",
            "✨ *100% Secure Payments*",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]
    },
    {
        "title": "🎉 *REFER & EARN PROGRAM* 🎉",
        "content": [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "👥 *Earn ₹2 per referral!*",
            "",
            "📌 *How it works:*",
            "1️⃣ Share your referral link",
            "2️⃣ Friend joins using your link",
            "3️⃣ You get ₹2 instantly",
            "4️⃣ Friend gets ₹5 welcome bonus",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "🎯 *Benefits:*",
            "• Unlimited referrals",
            "• Instant credit to wallet",
            "• Use earnings to buy cards",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]
    },
    {
        "title": "🌟 *LIVE PURCHASE PROOFS* 🌟",
        "content": [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "📊 *Join our Proof Channel:*",
            "@gift_card_log",
            "",
            "⚡ *Recent Purchases:*",
            "• ✦ 𝙕𝙮𝙧𝙤 ⚡ bought Amazon ₹500",
            "• 『ＲＡＸＥＬ』☠ bought Flipkart ₹1000",
            "• 𓆩⚝𓆪 𝑽𝒐𝒓𝒕𝒆𝒙 𓆩⚝𓆪 bought Play Store ₹500",
            "• ★彡 ᴢᴇʀɪᴏɴ 彡★ bought Myntra ₹2000",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "✅ *100% Real Transactions*",
            "✅ *Verified by Community*",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]
    },
    {
        "title": "🎁 *WEEKEND SPECIAL OFFER* 🎁",
        "content": [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "🔥 *Extra 10% OFF on All Cards!*",
            "",
            "• Amazon: ₹500 → ₹90 (82% OFF)",
            "• Flipkart: ₹1000 → ₹180 (82% OFF)",
            "• Play Store: ₹500 → ₹90 (82% OFF)",
            "• Myntra: ₹2000 → ₹360 (82% OFF)",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "⏳ *Limited Time Offer*",
            "🎫 Use Code: *WEEKEND10*",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]
    },
    {
        "title": "🏆 *MOST TRUSTED GIFT CARD BOT* 🏆",
        "content": [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "⭐ *Awards & Recognition:*",
            "• #1 Gift Card Bot 2024",
            "• Best Customer Service",
            "• Most Secure Platform",
            "• Fastest Delivery",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "📈 *5 Years of Trust*",
            "• 50,000+ Happy Customers",
            "• 100,000+ Cards Delivered",
            "• 4.9/5 Average Rating",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]
    },
    {
        "title": "🎂 *BIRTHDAY SPECIAL OFFER* 🎂",
        "content": [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "🎉 *Celebrating 5 Years!*",
            "",
            "🔥 *Special Discounts:*",
            "• All Cards: 85% OFF",
            "• Amazon ₹500 → ₹75",
            "• Flipkart ₹1000 → ₹150",
            "• Play Store ₹500 → ₹75",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            "🎫 *Use Code:* BIRTHDAY5",
            "⏳ *Valid till midnight*",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]
    }
]

# ─────────────────────────────────────────────────────────────
# PROOF MESSAGES (SUCCESSFUL PURCHASE + DELIVERY)
# ─────────────────────────────────────────────────────────────
PURCHASE_PROOFS = [
    "⚡ *PURCHASE SUCCESSFUL* ⚡\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👤 *{name}*\n🎁 *{card}*\n💰 *₹{amount}*\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n💳 Payment: ✅ Completed\n📧 Status: Processing Delivery\n⏱️ Time: {time}",
    
    "🎉 *ORDER PLACED* 🎉\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👤 *Customer:* {name}\n🛒 *Product:* {card}\n💵 *Amount:* ₹{amount}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📦 *Status:* Payment Verified\n⏱️ *Time:* {time}",
    
    "✅ *PAYMENT CONFIRMED* ✅\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👤 *User:* {name}\n🎁 *Item:* {card}\n💰 *Paid:* ₹{amount}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📧 *Preparing for delivery*",
    
    "💳 *TRANSACTION COMPLETED* 💳\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👤 *Buyer:* {name}\n🛍️ *Purchase:* {card}\n💵 *Value:* ₹{amount}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n✅ *Payment Approved*\n⏱️ *Time:* {time}"
]

DELIVERY_PROOFS = [
    "📧 *GIFT CARD DELIVERED* 📧\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👤 *To:* {name}\n🎁 *Card:* {card}\n💰 *Value:* ₹{amount}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📨 *Sent to:* {email}\n✅ *Status:* Delivered\n⏱️ *Time:* {time}",
    
    "✅ *DELIVERY SUCCESSFUL* ✅\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👤 *Recipient:* {name}\n🎁 *Gift Card:* {card}\n💰 *Amount:* ₹{amount}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📧 *Email:* {email}\n⭐ *Check spam folder*",
    
    "📨 *CARD SENT* 📨\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👤 *User:* {name}\n🎁 *Product:* {card}\n💰 *Value:* ₹{amount}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📧 *Delivery:* Email\n✅ *Status:* Completed\n⏱️ *Time:* {time}",
    
    "🎁 *GIFT CARD DELIVERED* 🎁\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n👤 *To:* {name}\n🛍️ *Item:* {card}\n💵 *Amount:* ₹{amount}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n📧 *Check your inbox:* {email}\n⭐ *Enjoy your purchase!*"
]

# ─────────────────────────────────────────────────────────────
# DECORATORS
# ─────────────────────────────────────────────────────────────
def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            await update.message.reply_text("❌ Admin only command.")
            return
        return await func(update, context)
    return wrapper

# ─────────────────────────────────────────────────────────────
# START COMMAND
# ─────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - show bot info"""
    user = update.effective_user
    
    groups = db.get_all_groups()
    channels = db.get_all_channels()
    
    text = (
        f"🔥 *AUTO PROMO + PROOF BOT* 🔥\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👑 *Admin:* {user.first_name}\n\n"
        f"📊 *Statistics:*\n"
        f"• Groups: {len(groups)}\n"
        f"• Channels: {len(channels)}\n"
        f"• Names: {len(STYLISH_NAMES)}\n"
        f"• Promo Templates: {len(PROMO_MESSAGES)}\n\n"
        f"⚙️ *Auto Features:*\n"
        f"• Proofs: Every 1-5 minutes\n"
        f"• Promotions: Every 5 minutes\n\n"
        f"📝 *Admin Commands:*\n"
        f"• /addgroup - Add proof group\n"
        f"• /addchannel - Add promo channel\n"
        f"• /list - Show all groups/channels\n"
        f"• /remove - Remove group/channel\n"
        f"• /testproof - Test proof in group\n"
        f"• /testpromo - Test promo in channel\n"
        f"• /status - Bot status\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ─────────────────────────────────────────────────────────────
# ADD GROUP
# ─────────────────────────────────────────────────────────────
@admin_only
async def add_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start add group process"""
    await update.message.reply_text(
        "📝 *ADD PROOF GROUP*\n\n"
        "Send me the group ID or username\n\n"
        "Examples:\n"
        "• `-1001234567890` (group ID)\n"
        "• `@mygroup` (username)\n\n"
        "_(Make sure bot is admin in the group)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return ADD_GROUP

async def add_group_handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle group addition"""
    chat_input = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Verify bot is in group
    try:
        chat = await context.bot.get_chat(chat_input)
        member = await context.bot.get_chat_member(chat.id, (await context.bot.get_me()).id)
        if member.status not in ['administrator', 'member']:
            await update.message.reply_text("❌ Bot must be in the group!")
            return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"❌ Cannot access group: {e}")
        return ConversationHandler.END
    
    # Save to database
    chat_id = str(chat.id)
    chat_name = chat.title or chat.username or chat_id
    
    if db.add_group(chat_id, chat_name, user_id):
        await update.message.reply_text(f"✅ Group added successfully!\n\nID: `{chat_id}`\nName: {chat_name}")
    else:
        await update.message.reply_text("❌ Failed to add group. Maybe already exists?")
    
    return ConversationHandler.END

# ─────────────────────────────────────────────────────────────
# ADD CHANNEL
# ─────────────────────────────────────────────────────────────
@admin_only
async def add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start add channel process"""
    await update.message.reply_text(
        "📢 *ADD PROMO CHANNEL*\n\n"
        "Send me the channel ID or username\n\n"
        "Examples:\n"
        "• `-1001234567890` (channel ID)\n"
        "• `@mychannel` (username)\n\n"
        "_(Make sure bot is admin in the channel)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return ADD_CHANNEL

async def add_channel_handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle channel addition"""
    chat_input = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Verify bot is admin in channel
    try:
        chat = await context.bot.get_chat(chat_input)
        member = await context.bot.get_chat_member(chat.id, (await context.bot.get_me()).id)
        if member.status not in ['administrator', 'creator']:
            await update.message.reply_text("❌ Bot must be admin in the channel!")
            return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f"❌ Cannot access channel: {e}")
        return ConversationHandler.END
    
    # Save to database
    chat_id = str(chat.id)
    chat_name = chat.title or chat.username or chat_id
    
    if db.add_channel(chat_id, chat_name, user_id):
        await update.message.reply_text(f"✅ Channel added successfully!\n\nID: `{chat_id}`\nName: {chat_name}")
    else:
        await update.message.reply_text("❌ Failed to add channel. Maybe already exists?")
    
    return ConversationHandler.END

# ─────────────────────────────────────────────────────────────
# LIST ALL
# ─────────────────────────────────────────────────────────────
@admin_only
async def list_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all groups and channels"""
    groups = db.get_all_groups()
    channels = db.get_all_channels()
    
    text = "📋 *REGISTERED TARGETS*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    text += f"📝 *Groups ({len(groups)}):*\n"
    if groups:
        for i, (chat_id, name) in enumerate(groups, 1):
            text += f"{i}. `{chat_id}` - {name}\n"
    else:
        text += "• No groups added\n"
    
    text += f"\n📢 *Channels ({len(channels)}):*\n"
    if channels:
        for i, (chat_id, name) in enumerate(channels, 1):
            text += f"{i}. `{chat_id}` - {name}\n"
    else:
        text += "• No channels added\n"
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ─────────────────────────────────────────────────────────────
# REMOVE TARGET
# ─────────────────────────────────────────────────────────────
@admin_only
async def remove_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start remove process"""
    groups = db.get_all_groups()
    channels = db.get_all_channels()
    
    text = "🗑️ *REMOVE TARGET*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    text += "Send the ID of the group/channel to remove:\n\n"
    
    if groups:
        text += "📝 *Groups:*\n"
        for chat_id, name in groups:
            text += f"• `{chat_id}` - {name}\n"
    
    if channels:
        text += "\n📢 *Channels:*\n"
        for chat_id, name in channels:
            text += f"• `{chat_id}` - {name}\n"
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    return REMOVE_TARGET

async def remove_handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle removal"""
    target = update.message.text.strip()
    
    # Try to remove from groups
    if db.remove_group(target):
        await update.message.reply_text(f"✅ Removed group `{target}`")
    # Try to remove from channels
    elif db.remove_channel(target):
        await update.message.reply_text(f"✅ Removed channel `{target}`")
    else:
        await update.message.reply_text(f"❌ No target found with ID: {target}")
    
    return ConversationHandler.END

# ─────────────────────────────────────────────────────────────
# TEST PROOF
# ─────────────────────────────────────────────────────────────
@admin_only
async def test_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a test proof to all groups"""
    groups = db.get_all_groups()
    
    if not groups:
        await update.message.reply_text("❌ No groups added. Use /addgroup first.")
        return
    
    msg = await update.message.reply_text("📤 Sending test proofs...")
    
    sent = 0
    failed = 0
    
    for chat_id, _ in groups:
        if await send_proof_to_group(context, chat_id):
            sent += 1
        else:
            failed += 1
        await asyncio.sleep(1)  # Rate limiting
    
    await msg.edit_text(
        f"✅ *Test Complete*\n\n"
        f"• Sent: {sent}\n"
        f"• Failed: {failed}",
        parse_mode=ParseMode.MARKDOWN
    )

# ─────────────────────────────────────────────────────────────
# TEST PROMO
# ─────────────────────────────────────────────────────────────
@admin_only
async def test_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a test promo to all channels"""
    channels = db.get_all_channels()
    
    if not channels:
        await update.message.reply_text("❌ No channels added. Use /addchannel first.")
        return
    
    msg = await update.message.reply_text("📤 Sending test promotions...")
    
    sent = 0
    failed = 0
    
    for chat_id, _ in channels:
        if await send_promo_to_channel(context, chat_id):
            sent += 1
        else:
            failed += 1
        await asyncio.sleep(1)
    
    await msg.edit_text(
        f"✅ *Test Complete*\n\n"
        f"• Sent: {sent}\n"
        f"• Failed: {failed}",
        parse_mode=ParseMode.MARKDOWN
    )

# ─────────────────────────────────────────────────────────────
# STATUS
# ─────────────────────────────────────────────────────────────
@admin_only
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show bot status"""
    groups = db.get_all_groups()
    channels = db.get_all_channels()
    
    # Get job status
    jobs = context.application.job_queue.jobs()
    proof_job = any(job.name == "auto_proof" for job in jobs)
    promo_job = any(job.name == "auto_promo" for job in jobs)
    
    text = (
        f"📊 *BOT STATUS*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🤖 *Bot:* @{(await context.bot.get_me()).username}\n\n"
        f"📝 *Groups:* {len(groups)}\n"
        f"📢 *Channels:* {len(channels)}\n"
        f"👤 *Admin:* `{ADMIN_ID}`\n\n"
        f"⚙️ *Jobs:*\n"
        f"• Auto Proof: {'✅ Running' if proof_job else '❌ Stopped'}\n"
        f"• Auto Promo: {'✅ Running' if promo_job else '❌ Stopped'}\n\n"
        f"⏱️ *Intervals:*\n"
        f"• Proofs: 1-5 minutes (random)\n"
        f"• Promos: 5 minutes (fixed)"
    )
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ─────────────────────────────────────────────────────────────
# SEND PROOF TO GROUP
# ─────────────────────────────────────────────────────────────
async def send_proof_to_group(context, chat_id):
    """Send a proof message to a specific group"""
    try:
        name = random.choice(STYLISH_NAMES)
        card = random.choice(CARDS)
        amount = random.choice(AMOUNTS)
        email = f"{random.choice(['raj', 'amit', 'priya', 'karan'])}{random.randint(1,999)}@gmail.com"
        current_time = datetime.now().strftime("%I:%M %p")
        
        # 50% chance of purchase proof, 50% chance of delivery proof
        if random.random() < 0.5:
            template = random.choice(PURCHASE_PROOFS)
            message = template.format(
                name=name,
                card=card,
                amount=amount,
                time=current_time
            )
        else:
            template = random.choice(DELIVERY_PROOFS)
            message = template.format(
                name=name,
                card=card,
                amount=amount,
                email=email,
                time=current_time
            )
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN
        )
        return True
        
    except Exception as e:
        logger.error(f"Proof error for {chat_id}: {e}")
        return False

# ─────────────────────────────────────────────────────────────
# SEND PROMO TO CHANNEL
# ─────────────────────────────────────────────────────────────
async def send_promo_to_channel(context, chat_id):
    """Send a promotion to a specific channel"""
    try:
        promo = random.choice(PROMO_MESSAGES)
        content = "\n".join(promo["content"])
        
        message = (
            f"{promo['title']}\n"
            f"{content}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🤖 *Main Bot:* {MAIN_BOT_USERNAME}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🛒 BUY NOW", url=f"https://t.me/{MAIN_BOT_USERNAME[1:]}")]
        ])
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
        return True
        
    except Exception as e:
        logger.error(f"Promo error for {chat_id}: {e}")
        return False

# ─────────────────────────────────────────────────────────────
# AUTO PROOF FUNCTION
# ─────────────────────────────────────────────────────────────
async def auto_proof(context: ContextTypes.DEFAULT_TYPE):
    """Send proofs to all groups with random interval"""
    groups = db.get_all_groups()
    
    if groups:
        for chat_id, _ in groups:
            await send_proof_to_group(context, chat_id)
            await asyncio.sleep(2)  # Small delay between groups
    
    # Randomize next interval (1-5 minutes)
    next_interval = random.randint(60, 300)
    context.application.job_queue.run_once(auto_proof, when=next_interval, name="auto_proof")

# ─────────────────────────────────────────────────────────────
# AUTO PROMO FUNCTION
# ─────────────────────────────────────────────────────────────
async def auto_promo(context: ContextTypes.DEFAULT_TYPE):
    """Send promotions to all channels (every 5 minutes)"""
    channels = db.get_all_channels()
    
    if channels:
        for chat_id, _ in channels:
            await send_promo_to_channel(context, chat_id)
            await asyncio.sleep(2)

# ─────────────────────────────────────────────────────────────
# CANCEL
# ─────────────────────────────────────────────────────────────
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current operation"""
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END

# ─────────────────────────────────────────────────────────────
# ERROR HANDLER
# ─────────────────────────────────────────────────────────────
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update caused error: {context.error}")

# ─────────────────────────────────────────────────────────────
# POST INIT
# ─────────────────────────────────────────────────────────────
async def post_init(app):
    """Setup after bot initialization"""
    commands = [
        BotCommand("start", "🚀 Bot info"),
        BotCommand("addgroup", "📝 Add proof group"),
        BotCommand("addchannel", "📢 Add promo channel"),
        BotCommand("list", "📋 List all targets"),
        BotCommand("remove", "🗑️ Remove target"),
        BotCommand("testproof", "📝 Test proofs"),
        BotCommand("testpromo", "📢 Test promos"),
        BotCommand("status", "📊 Bot status"),
        BotCommand("cancel", "❌ Cancel"),
    ]
    await app.bot.set_my_commands(commands)
    
    logger.info("✅ Bot ready!")
    
    # Schedule auto proof (first after 10 seconds)
    app.job_queue.run_once(auto_proof, when=10, name="auto_proof")
    
    # Schedule auto promo (every 5 minutes)
    app.job_queue.run_repeating(auto_promo, interval=300, first=30, name="auto_promo")

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # Add group conversation
    add_group_conv = ConversationHandler(
        entry_points=[CommandHandler("addgroup", add_group_start)],
        states={ADD_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_group_handle)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(add_group_conv)
    
    # Add channel conversation
    add_channel_conv = ConversationHandler(
        entry_points=[CommandHandler("addchannel", add_channel_start)],
        states={ADD_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_handle)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(add_channel_conv)
    
    # Remove conversation
    remove_conv = ConversationHandler(
        entry_points=[CommandHandler("remove", remove_start)],
        states={REMOVE_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_handle)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(remove_conv)
    
    # Other commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_all))
    app.add_handler(CommandHandler("testproof", test_proof))
    app.add_handler(CommandHandler("testpromo", test_promo))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("cancel", cancel))
    
    # Error handler
    app.add_error_handler(error_handler)
    
    logger.info("🚀 Ultimate Auto Promo+Proof Bot started...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
