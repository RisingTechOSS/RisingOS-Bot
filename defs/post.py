import os
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

load_dotenv('config.env')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')
postl_confirmation = {}

@Client.on_message(filters.command("post"))
async def post(client, message):
    try:
        if message.reply_to_message:
            postl_confirmation[message.chat.id] = message.reply_to_message
            keyboard = [[InlineKeyboardButton("Yes", callback_data="postl_yes"),
                        InlineKeyboardButton("No", callback_data="postl_no")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await message.reply_text("Do you want to send this message?", reply_markup=reply_markup)
        else:
            await message.reply_text("Please reply to a message with /post to post it.")
    except Exception as e:
        print(f"Error: {e}")

async def post_callback(client, callback_query):
    chat_id = callback_query.message.chat.id
    try:
        if callback_query.data == "postl_yes":
            if chat_id in postl_confirmation:
                message = postl_confirmation.pop(chat_id)
                await message.copy(chat_id='@' + CHANNEL_USERNAME)
                await send_message(callback_query, "Message sent.")
        elif callback_query.data == "postl_no":
            if chat_id in postl_confirmation:
                postl_confirmation.pop(chat_id)
                await send_message(callback_query, "Message canceled.")
    except Exception as e:
        print(f"Error: {e}")

async def send_message(callback_query, message_text):
    await callback_query.message.edit_text(message_text)