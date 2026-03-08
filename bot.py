#!/usr/bin/env python3
"""
👑 ADMIN CONTROL PANEL BOT
Manage all your bots from one place!
- Channel management
- User management
- Balance management
- Multiple bot support
"""

import os
import sys
import json
import logging
import sqlite3
import asyncio
import csv
from io import StringIO
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
    raise ValueError("❌ ADMIN_BOT_TOKEN not set!")

MASTER_ADMIN_ID = int(os.environ.get("MASTER_ADMIN_ID", "0"))
DATABASE_PATH = os.environ.get("DATABASE_PATH", "admin_bot.db")

# ─────────────────────────────────────────────────────────────
# CONVERSATION STATES
# ─────────────────────────────────────────────────────────────
(
    STATE_ADD_BOT,
    STATE_ADD_CHANNEL,
    STATE_ADD_ADMIN,
    STATE_ADD_BALANCE,
    STATE_REMOVE_BALANCE,
    STATE_BROADCAST,
    STATE_ADD_COUPON,
    STATE_SETTINGS
) = range(8)

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
class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()
    
    def _get_conn(self):
        return sqlite3.connect(self.db_path, timeout=30)
    
    def _init_db(self):
        conn = self._get_conn()
        c = conn.cursor()
        
        # Admins table
        c.execute('''CREATE TABLE IF NOT EXISTS admins (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            added_by INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            permissions TEXT DEFAULT 'all'
        )''')
        
        # Bots table
        c.execute('''CREATE TABLE IF NOT EXISTS bots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_token TEXT UNIQUE,
            bot_username TEXT,
            bot_name TEXT,
            added_by INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            last_used TIMESTAMP
        )''')
        
        # Channels table
        c.execute('''CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT UNIQUE,
            channel_name TEXT,
            bot_id INTEGER,
            added_by INTEGER,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (bot_id) REFERENCES bots(id)
        )''')
        
        # Users table (from all bots)
        c.execute('''CREATE TABLE IF NOT EXISTS bot_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bot_id INTEGER,
            user_id INTEGER,
            username TEXT,
            first_name TEXT,
            balance INTEGER DEFAULT 0,
            last_active TIMESTAMP,
            UNIQUE(bot_id, user_id),
            FOREIGN KEY (bot_id) REFERENCES bots(id)
        )''')
        
        # Transactions log
        c.execute('''CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            action TEXT,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Settings table
        c.execute('''CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            description TEXT
        )''')
        
        # Insert default settings
        default_settings = [
            ('require_verification', '1', 'Require channel join'),
            ('default_referral_bonus', '2', 'Default referral bonus'),
            ('default_welcome_bonus', '5', 'Default welcome bonus'),
            ('maintenance_mode', '0', 'Maintenance mode'),
        ]
        
        for key, value, desc in default_settings:
            c.execute("INSERT OR IGNORE INTO settings (key, value, description) VALUES (?, ?, ?)",
                     (key, value, desc))
        
        conn.commit()
        conn.close()
        logger.info("✅ Admin Bot Database ready")
    
    def execute(self, query, params=(), fetchone=False, fetchall=False, commit=False):
        conn = self._get_conn()
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
            logger.error(f"DB Error: {e}")
            raise
        finally:
            conn.close()
    
    # ── ADMIN METHODS ──────────────────────────────────────
    def is_admin(self, user_id):
        if user_id == MASTER_ADMIN_ID:
            return True
        row = self.execute("SELECT user_id FROM admins WHERE user_id=?", (user_id,), fetchone=True)
        return row is not None
    
    def add_admin(self, user_id, username, added_by):
        self.execute(
            "INSERT OR IGNORE INTO admins (user_id, username, added_by) VALUES (?, ?, ?)",
            (user_id, username, added_by), commit=True
        )
    
    def remove_admin(self, user_id):
        self.execute("DELETE FROM admins WHERE user_id=?", (user_id,), commit=True)
    
    def get_all_admins(self):
        rows = self.execute("SELECT * FROM admins ORDER BY added_at", fetchall=True)
        return [dict(row) for row in rows] if rows else []
    
    # ── BOT METHODS ────────────────────────────────────────
    def add_bot(self, bot_token, bot_username, bot_name, added_by):
        return self.execute(
            "INSERT INTO bots (bot_token, bot_username, bot_name, added_by) VALUES (?, ?, ?, ?)",
            (bot_token, bot_username, bot_name, added_by), commit=True
        )
    
    def get_all_bots(self):
        rows = self.execute("SELECT * FROM bots WHERE is_active=1 ORDER BY added_at", fetchall=True)
        return [dict(row) for row in rows] if rows else []
    
    def get_bot(self, bot_id):
        row = self.execute("SELECT * FROM bots WHERE id=?", (bot_id,), fetchone=True)
        return dict(row) if row else None
    
    def update_bot_status(self, bot_id, is_active):
        self.execute("UPDATE bots SET is_active=? WHERE id=?", (is_active, bot_id), commit=True)
    
    # ── CHANNEL METHODS ────────────────────────────────────
    def add_channel(self, channel_id, channel_name, bot_id, added_by):
        self.execute(
            "INSERT OR IGNORE INTO channels (channel_id, channel_name, bot_id, added_by) VALUES (?, ?, ?, ?)",
            (channel_id, channel_name, bot_id, added_by), commit=True
        )
    
    def get_channels_for_bot(self, bot_id):
        rows = self.execute(
            "SELECT * FROM channels WHERE bot_id=? AND is_active=1 ORDER BY added_at",
            (bot_id,), fetchall=True
        )
        return [dict(row) for row in rows] if rows else []
    
    def remove_channel(self, channel_id):
        self.execute("DELETE FROM channels WHERE channel_id=?", (channel_id,), commit=True)
    
    # ── USER METHODS ───────────────────────────────────────
    def update_user_balance(self, bot_id, user_id, amount, admin_id):
        # Check if user exists
        row = self.execute(
            "SELECT balance FROM bot_users WHERE bot_id=? AND user_id=?",
            (bot_id, user_id), fetchone=True
        )
        
        if row:
            new_balance = row[0] + amount
            self.execute(
                "UPDATE bot_users SET balance=?, last_active=CURRENT_TIMESTAMP WHERE bot_id=? AND user_id=?",
                (new_balance, bot_id, user_id), commit=True
            )
        else:
            self.execute(
                "INSERT INTO bot_users (bot_id, user_id, balance) VALUES (?, ?, ?)",
                (bot_id, user_id, amount), commit=True
            )
        
        # Log action
        self.log_action(admin_id, "update_balance", f"Bot:{bot_id} User:{user_id} Amount:{amount}")
        return True
    
    def get_user_balance(self, bot_id, user_id):
        row = self.execute(
            "SELECT balance FROM bot_users WHERE bot_id=? AND user_id=?",
            (bot_id, user_id), fetchone=True
        )
        return row[0] if row else 0
    
    def search_users(self, bot_id, query):
        rows = self.execute(
            """SELECT user_id, username, first_name, balance FROM bot_users 
               WHERE bot_id=? AND (user_id LIKE ? OR username LIKE ? OR first_name LIKE ?)
               LIMIT 20""",
            (bot_id, f"%{query}%", f"%{query}%", f"%{query}%"), fetchall=True
        )
        return [dict(row) for row in rows] if rows else []
    
    # ── LOG METHODS ────────────────────────────────────────
    def log_action(self, admin_id, action, details):
        self.execute(
            "INSERT INTO admin_logs (admin_id, action, details) VALUES (?, ?, ?)",
            (admin_id, action, details), commit=True
        )
    
    def get_recent_logs(self, limit=50):
        rows = self.execute(
            "SELECT * FROM admin_logs ORDER BY timestamp DESC LIMIT ?",
            (limit,), fetchall=True
        )
        return [dict(row) for row in rows] if rows else []
    
    # ── SETTINGS METHODS ───────────────────────────────────
    def get_setting(self, key, default=None):
        row = self.execute("SELECT value FROM settings WHERE key=?", (key,), fetchone=True)
        return row[0] if row else default
    
    def update_setting(self, key, value):
        self.execute("UPDATE settings SET value=? WHERE key=?", (value, key), commit=True)


db = DatabaseManager(DATABASE_PATH)

# ─────────────────────────────────────────────────────────────
# DECORATORS
# ─────────────────────────────────────────────────────────────
def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if not db.is_admin(user_id):
            await update.message.reply_text("❌ Admin access required.")
            return
        return await func(update, context)
    return wrapper

def master_admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id != MASTER_ADMIN_ID:
            await update.message.reply_text("❌ Master admin only!")
            return
        return await func(update, context)
    return wrapper

# ─────────────────────────────────────────────────────────────
# START COMMAND
# ─────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Add master admin if not exists
    if user.id == MASTER_ADMIN_ID and not db.is_admin(user.id):
        db.add_admin(user.id, user.username, user.id)
    
    if not db.is_admin(user.id):
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return
    
    text = (
        f"👑 *ADMIN CONTROL PANEL*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Welcome back, {user.first_name}!\n\n"
        f"*Available Commands:*\n\n"
        f"📊 `/dashboard` - Main admin dashboard\n"
        f"🤖 `/bots` - Manage connected bots\n"
        f"📢 `/channels` - Manage channels\n"
        f"👥 `/admins` - Manage admins\n"
        f"💰 `/balance` - Manage user balances\n"
        f"📋 `/users` - Search users\n"
        f"📢 `/broadcast` - Broadcast message\n"
        f"📊 `/logs` - View admin logs\n"
        f"⚙️ `/settings` - Bot settings\n"
        f"📥 `/export` - Export data\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ─────────────────────────────────────────────────────────────
# MAIN DASHBOARD
# ─────────────────────────────────────────────────────────────
@admin_only
async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bots = db.get_all_bots()
    admins = db.get_all_admins()
    logs = db.get_recent_logs(5)
    
    text = (
        f"📊 *ADMIN DASHBOARD*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 Connected Bots: *{len(bots)}*\n"
        f"👥 Admins: *{len(admins) + 1}* (incl. master)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"*Recent Activity:*\n"
    )
    
    for log in logs[:3]:
        text += f"• {log['action']} - {log['details'][:30]}...\n"
    
    keyboard = [
        [InlineKeyboardButton("🤖 Manage Bots", callback_data="menu_bots")],
        [InlineKeyboardButton("📢 Manage Channels", callback_data="menu_channels")],
        [InlineKeyboardButton("👥 Manage Admins", callback_data="menu_admins")],
        [InlineKeyboardButton("💰 Balance Management", callback_data="menu_balance")],
        [InlineKeyboardButton("📋 User Search", callback_data="menu_users")],
        [InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings")],
    ]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.MARKDOWN
    )

# ─────────────────────────────────────────────────────────────
# BOT MANAGEMENT
# ─────────────────────────────────────────────────────────────
@admin_only
async def list_bots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bots = db.get_all_bots()
    
    if not bots:
        text = "🤖 *No bots connected yet.*\n\nUse /addbot to add your first bot."
        keyboard = [[InlineKeyboardButton("➕ Add Bot", callback_data="add_bot")]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        return
    
    text = "🤖 *CONNECTED BOTS*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for bot in bots:
        channels = db.get_channels_for_bot(bot['id'])
        text += f"• *{bot['bot_name']}*\n"
        text += f"  📢 @{bot['bot_username']}\n"
        text += f"  📊 {len(channels)} channels\n"
        text += f"  🆔 ID: `{bot['id']}`\n\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ Add Bot", callback_data="add_bot")],
        [InlineKeyboardButton("❌ Remove Bot", callback_data="remove_bot")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

@admin_only
async def add_bot_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🤖 *ADD NEW BOT*\n\n"
        "Please send me your bot token from @BotFather\n\n"
        "Format: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`\n\n"
        "_(Send /cancel to abort)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return STATE_ADD_BOT

async def add_bot_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = update.message.text.strip()
    
    # Verify token
    try:
        app = Application.builder().token(token).build()
        bot_info = await app.bot.get_me()
        bot_username = bot_info.username
        bot_name = bot_info.first_name
    except Exception as e:
        await update.message.reply_text(f"❌ Invalid token: {e}\n\nPlease try again or /cancel")
        return STATE_ADD_BOT
    
    # Save to database
    db.add_bot(token, bot_username, bot_name, update.effective_user.id)
    db.log_action(update.effective_user.id, "add_bot", f"Added @{bot_username}")
    
    await update.message.reply_text(
        f"✅ *Bot added successfully!*\n\n"
        f"Name: {bot_name}\n"
        f"Username: @{bot_username}\n\n"
        f"Use /channels to add verification channels.",
        parse_mode=ParseMode.MARKDOWN
    )
    return ConversationHandler.END

# ─────────────────────────────────────────────────────────────
# CHANNEL MANAGEMENT
# ─────────────────────────────────────────────────────────────
@admin_only
async def manage_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    bots = db.get_all_bots()
    
    if not bots:
        await query.edit_message_text(
            "❌ No bots found. Add a bot first.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")]])
        )
        return
    
    text = "📢 *CHANNEL MANAGEMENT*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\nSelect a bot to manage channels:\n\n"
    
    keyboard = []
    for bot in bots:
        keyboard.append([InlineKeyboardButton(f"🤖 {bot['bot_name']}", callback_data=f"channels_bot_{bot['id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

@admin_only
async def list_bot_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    bot_id = int(query.data.split('_')[2])
    context.user_data['current_bot'] = bot_id
    
    bot = db.get_bot(bot_id)
    channels = db.get_channels_for_bot(bot_id)
    
    text = f"📢 *Channels for {bot['bot_name']}*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if channels:
        for ch in channels:
            text += f"• {ch['channel_name']}\n"
    else:
        text += "No channels added yet.\n"
    
    text += f"\nTotal: {len(channels)} channels"
    
    keyboard = [
        [InlineKeyboardButton("➕ Add Channel", callback_data="add_channel")],
        [InlineKeyboardButton("❌ Remove Channel", callback_data="remove_channel")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_channels")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

@admin_only
async def add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📢 *ADD CHANNEL*\n\n"
        "Send me the channel username or ID\n\n"
        "Examples:\n"
        "• `@my_channel`\n"
        "• `-1001234567890`\n\n"
        "_(Send /cancel to abort)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return STATE_ADD_CHANNEL

async def add_channel_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channel_input = update.message.text.strip()
    bot_id = context.user_data.get('current_bot')
    
    if not bot_id:
        await update.message.reply_text("❌ Session expired. Start over.")
        return ConversationHandler.END
    
    # Format channel
    if not channel_input.startswith('@') and not channel_input.startswith('-'):
        channel_input = '@' + channel_input.lstrip('@')
    
    # Verify bot is admin in channel
    bot = db.get_bot(bot_id)
    if not bot:
        await update.message.reply_text("❌ Bot not found.")
        return ConversationHandler.END
    
    try:
        app = Application.builder().token(bot['bot_token']).build()
        chat = await app.bot.get_chat(channel_input)
        bot_member = await app.bot.get_chat_member(channel_input, (await app.bot.get_me()).id)
        if bot_member.status not in ['administrator', 'creator']:
            await update.message.reply_text("❌ Bot must be admin in the channel!")
            return STATE_ADD_CHANNEL
    except Exception as e:
        await update.message.reply_text(f"❌ Cannot access channel: {e}")
        return STATE_ADD_CHANNEL
    
    # Save channel
    db.add_channel(str(chat.id), f"@{chat.username}" if chat.username else str(chat.title), bot_id, update.effective_user.id)
    db.log_action(update.effective_user.id, "add_channel", f"Added {channel_input} to bot {bot_id}")
    
    await update.message.reply_text(f"✅ Channel added successfully!")
    return ConversationHandler.END

# ─────────────────────────────────────────────────────────────
# ADMIN MANAGEMENT
# ─────────────────────────────────────────────────────────────
@admin_only
async def manage_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admins = db.get_all_admins()
    
    text = "👥 *ADMIN MANAGEMENT*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    text += f"👑 Master Admin: `{MASTER_ADMIN_ID}`\n\n"
    
    if admins:
        text += "*Other Admins:*\n"
        for admin in admins:
            text += f"• `{admin['user_id']}` - @{admin['username'] or 'N/A'}\n"
    else:
        text += "No other admins.\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ Add Admin", callback_data="add_admin")],
        [InlineKeyboardButton("❌ Remove Admin", callback_data="remove_admin")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

@admin_only
async def add_admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "👥 *ADD ADMIN*\n\n"
        "Send me the Telegram User ID of the new admin\n\n"
        "_(Use @userinfobot to get ID)_\n\n"
        "_(Send /cancel to abort)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return STATE_ADD_ADMIN

async def add_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID. Please enter a number.")
        return STATE_ADD_ADMIN
    
    if user_id == MASTER_ADMIN_ID:
        await update.message.reply_text("❌ This is the master admin already!")
        return ConversationHandler.END
    
    # Get user info
    try:
        chat = await context.bot.get_chat(user_id)
        username = chat.username
    except:
        username = None
    
    db.add_admin(user_id, username, update.effective_user.id)
    db.log_action(update.effective_user.id, "add_admin", f"Added admin {user_id}")
    
    await update.message.reply_text(f"✅ Admin {user_id} added successfully!")
    
    # Notify new admin
    try:
        await context.bot.send_message(
            user_id,
            "👑 *You are now an admin!*\n\n"
            f"Use @{context.bot.username} to access admin panel.",
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        pass
    
    return ConversationHandler.END

# ─────────────────────────────────────────────────────────────
# BALANCE MANAGEMENT
# ─────────────────────────────────────────────────────────────
@admin_only
async def balance_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    bots = db.get_all_bots()
    
    if not bots:
        await query.edit_message_text(
            "❌ No bots found. Add a bot first.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")]])
        )
        return
    
    text = "💰 *BALANCE MANAGEMENT*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\nSelect a bot:\n\n"
    
    keyboard = []
    for bot in bots:
        keyboard.append([InlineKeyboardButton(f"🤖 {bot['bot_name']}", callback_data=f"balance_bot_{bot['id']}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="back_dashboard")])
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

@admin_only
async def balance_bot_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    bot_id = int(query.data.split('_')[2])
    context.user_data['balance_bot'] = bot_id
    
    bot = db.get_bot(bot_id)
    
    text = f"💰 *Balance Management - {bot['bot_name']}*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\nChoose action:\n\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ Add Balance", callback_data="add_balance")],
        [InlineKeyboardButton("➖ Remove Balance", callback_data="remove_balance")],
        [InlineKeyboardButton("🔍 Check Balance", callback_data="check_balance")],
        [InlineKeyboardButton("🔙 Back", callback_data="menu_balance")]
    ]
    
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

@admin_only
async def add_balance_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "💰 *ADD BALANCE*\n\n"
        "Send me the user ID and amount in format:\n"
        "`USER_ID AMOUNT`\n\n"
        "Example: `123456789 500`\n\n"
        "_(Send /cancel to abort)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return STATE_ADD_BALANCE

async def add_balance_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        parts = update.message.text.strip().split()
        user_id = int(parts[0])
        amount = int(parts[1])
    except (ValueError, IndexError):
        await update.message.reply_text("❌ Invalid format. Use: USER_ID AMOUNT")
        return STATE_ADD_BALANCE
    
    bot_id = context.user_data.get('balance_bot')
    if not bot_id:
        await update.message.reply_text("❌ Session expired. Start over.")
        return ConversationHandler.END
    
    # Update balance
    db.update_user_balance(bot_id, user_id, amount, update.effective_user.id)
    
    await update.message.reply_text(f"✅ Added ₹{amount} to user {user_id}")
    
    # Try to notify user via the actual bot
    bot = db.get_bot(bot_id)
    try:
        app = Application.builder().token(bot['bot_token']).build()
        await app.bot.send_message(
            user_id,
            f"✅ *Balance Updated!*\n\n💰 *₹{amount}* has been added to your wallet by admin.",
            parse_mode=ParseMode.MARKDOWN
        )
    except:
        pass
    
    return ConversationHandler.END

# ─────────────────────────────────────────────────────────────
# USER SEARCH
# ─────────────────────────────────────────────────────────────
@admin_only
async def search_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "📋 *USER SEARCH*\n\n"
            "Usage: `/search QUERY`\n"
            "Example: `/search 12345` or `/search @username`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    query = context.args[0]
    bots = db.get_all_bots()
    
    results = []
    for bot in bots:
        users = db.search_users(bot['id'], query)
        for user in users:
            results.append((bot, user))
    
    if not results:
        await update.message.reply_text("❌ No users found.")
        return
    
    text = f"📋 *SEARCH RESULTS for '{query}'*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for bot, user in results[:10]:
        text += f"🤖 *{bot['bot_name']}*\n"
        text += f"👤 ID: `{user['user_id']}`\n"
        text += f"📱 @{user['username'] or 'N/A'}\n"
        text += f"💰 Balance: ₹{user['balance']}\n\n"
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ─────────────────────────────────────────────────────────────
# BROADCAST
# ─────────────────────────────────────────────────────────────
@admin_only
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📢 *BROADCAST MESSAGE*\n\n"
        "Send me the message you want to broadcast to all users\n\n"
        "_(Send /cancel to abort)_",
        parse_mode=ParseMode.MARKDOWN
    )
    return STATE_BROADCAST

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    bots = db.get_all_bots()
    
    status_msg = await update.message.reply_text("📢 Broadcasting...")
    
    sent = 0
    failed = 0
    
    for bot in bots:
        try:
            app = Application.builder().token(bot['bot_token']).build()
            # In a real implementation, you'd need to get all users for this bot
            # For now, we'll just send to admin as demo
            await app.bot.send_message(
                update.effective_user.id,
                f"📢 *BROADCAST TEST*\n\n{message}",
                parse_mode=ParseMode.MARKDOWN
            )
            sent += 1
        except:
            failed += 1
    
    await status_msg.edit_text(
        f"✅ *Broadcast Complete*\n\n"
        f"Sent to {sent} bots\n"
        f"Failed: {failed}",
        parse_mode=ParseMode.MARKDOWN
    )
    
    db.log_action(update.effective_user.id, "broadcast", f"Sent to {sent} bots")
    return ConversationHandler.END

# ─────────────────────────────────────────────────────────────
# VIEW LOGS
# ─────────────────────────────────────────────────────────────
@admin_only
async def view_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logs = db.get_recent_logs(20)
    
    text = "📊 *ADMIN LOGS*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for log in logs:
        text += f"• {log['timestamp'][:19]} - {log['action']}\n"
        text += f"  `{log['details'][:50]}`\n\n"
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ─────────────────────────────────────────────────────────────
# EXPORT DATA
# ─────────────────────────────────────────────────────────────
@admin_only
async def export_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bots = db.get_all_bots()
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Bot ID', 'Bot Name', 'Bot Username', 'Added At'])
    
    for bot in bots:
        writer.writerow([bot['id'], bot['bot_name'], bot['bot_username'], bot['added_at']])
    
    output.seek(0)
    
    await update.message.reply_document(
        document=output.getvalue().encode('utf-8'),
        filename='bots_export.csv',
        caption="📊 Bots Export"
    )

# ─────────────────────────────────────────────────────────────
# SETTINGS
# ─────────────────────────────────────────────────────────────
@admin_only
async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    settings = [
        ('require_verification', db.get_setting('require_verification')),
        ('default_referral_bonus', db.get_setting('default_referral_bonus')),
        ('default_welcome_bonus', db.get_setting('default_welcome_bonus')),
        ('maintenance_mode', db.get_setting('maintenance_mode')),
    ]
    
    text = "⚙️ *BOT SETTINGS*\n━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    for key, value in settings:
        text += f"• {key}: `{value}`\n"
    
    text += "\nUse /set KEY VALUE to change settings"
    
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ─────────────────────────────────────────────────────────────
# CANCEL
# ─────────────────────────────────────────────────────────────
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END

# ─────────────────────────────────────────────────────────────
# BUTTON HANDLER
# ─────────────────────────────────────────────────────────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "back_dashboard":
        await dashboard(update, context)
    
    elif data == "menu_bots":
        await list_bots(update, context)
    
    elif data == "add_bot":
        await add_bot_start(update, context)
    
    elif data == "menu_channels":
        await manage_channels(update, context)
    
    elif data.startswith("channels_bot_"):
        await list_bot_channels(update, context)
    
    elif data == "add_channel":
        await add_channel_start(update, context)
    
    elif data == "menu_admins":
        await manage_admins(update, context)
    
    elif data == "add_admin":
        await add_admin_start(update, context)
    
    elif data == "menu_balance":
        await balance_menu(update, context)
    
    elif data.startswith("balance_bot_"):
        await balance_bot_menu(update, context)
    
    elif data == "add_balance":
        await add_balance_start(update, context)

# ─────────────────────────────────────────────────────────────
# ERROR HANDLER
# ─────────────────────────────────────────────────────────────
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update caused error: {context.error}")

# ─────────────────────────────────────────────────────────────
# POST INIT
# ─────────────────────────────────────────────────────────────
async def post_init(app):
    commands = [
        BotCommand("start", "🚀 Start admin panel"),
        BotCommand("dashboard", "📊 Main dashboard"),
        BotCommand("bots", "🤖 Manage bots"),
        BotCommand("channels", "📢 Manage channels"),
        BotCommand("admins", "👥 Manage admins"),
        BotCommand("balance", "💰 Manage balances"),
        BotCommand("search", "🔍 Search users"),
        BotCommand("broadcast", "📢 Broadcast message"),
        BotCommand("logs", "📊 View logs"),
        BotCommand("settings", "⚙️ Bot settings"),
        BotCommand("export", "📥 Export data"),
        BotCommand("cancel", "❌ Cancel"),
    ]
    await app.bot.set_my_commands(commands)
    logger.info("✅ Admin Bot ready!")

# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dashboard", dashboard))
    app.add_handler(CommandHandler("bots", list_bots))
    app.add_handler(CommandHandler("channels", manage_channels))
    app.add_handler(CommandHandler("admins", manage_admins))
    app.add_handler(CommandHandler("balance", balance_menu))
    app.add_handler(CommandHandler("search", search_users))
    app.add_handler(CommandHandler("logs", view_logs))
    app.add_handler(CommandHandler("settings", settings_menu))
    app.add_handler(CommandHandler("export", export_data))
    app.add_handler(CommandHandler("cancel", cancel))
    
    # Add bot conversation
    add_bot_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_bot_start, pattern="^add_bot$")],
        states={STATE_ADD_BOT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_bot_token)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(add_bot_conv)
    
    # Add channel conversation
    add_channel_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_channel_start, pattern="^add_channel$")],
        states={STATE_ADD_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel_input)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(add_channel_conv)
    
    # Add admin conversation
    add_admin_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_admin_start, pattern="^add_admin$")],
        states={STATE_ADD_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_admin_input)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(add_admin_conv)
    
    # Add balance conversation
    add_balance_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_balance_start, pattern="^add_balance$")],
        states={STATE_ADD_BALANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_balance_input)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(add_balance_conv)
    
    # Broadcast conversation
    broadcast_conv = ConversationHandler(
        entry_points=[CommandHandler("broadcast", broadcast_start)],
        states={STATE_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(broadcast_conv)
    
    # Button handler
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Error handler
    app.add_error_handler(error_handler)
    
    logger.info("🚀 Admin Bot started...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
