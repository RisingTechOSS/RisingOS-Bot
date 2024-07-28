from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

async def start(client: Client, message: Message):
    welcome_message = "Welcome to the risingOSS Bot! How can I assist you today?"
    button = InlineKeyboardButton("Get Started", callback_data="get_started")
    keyboard = InlineKeyboardMarkup([[button]])
    await message.reply_text(welcome_message, reply_markup=keyboard)

async def get_started_callback(client: Client, callback_query: CallbackQuery):
    if callback_query.data == "get_started":
        help_message = """Welcome to the risingOSS Bot! Here are the available commands:
        /gen -  Generate a post with a banner.
        /genl - Generate a legacy post with a banner (depricated).
        /bgen - Generate a high-quality banner.
        /post - Post messages from our maintainers group (depricated).
        /sf - Upload files to SourceForge.net from temporary download links.
        /sv - Save documents to private message through bot.
        /ping - check response time.
        /shell - Devs only.
        /ub - Replace banner (Devs only).
        Feel free to explore and make the most of bot's capabilities."""
        await callback_query.message.edit_text(text=help_message, reply_markup=None)
