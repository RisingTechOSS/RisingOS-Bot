from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.handlers import CallbackQueryHandler

sv_confirmation = {}

async def sv(client, message):
    try:
        if message.reply_to_message:
            sv_confirmation[message.chat.id] = message
            keyboard = [[InlineKeyboardButton("Yes", callback_data="sv_yes"),
                        InlineKeyboardButton("No", callback_data="sv_no")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await message.reply_text("Do you want to send this message?", reply_markup=reply_markup)
        else:
            instructions = "To copy a message, reply to it with /sv ."
            await message.reply_text(instructions)
    except Exception as e:
        print(f"Error: {e}")

async def sv_callback(client, callback_query):
    chat_id = callback_query.message.chat.id
    try:
        if callback_query.data == "sv_yes":
            if chat_id in sv_confirmation and sv_confirmation[chat_id].reply_to_message:
                message_to_copy = sv_confirmation[chat_id].reply_to_message
                await message_to_copy.copy(chat_id=callback_query.from_user.id)
                await callback_query.edit_message_text("Message copied.")
        elif callback_query.data == "sv_no":
            if chat_id in sv_confirmation:
                sv_confirmation.pop(chat_id)
                await callback_query.edit_message_text("Message copying canceled.")
    except Exception as e:
        print(f"Error: {e}")

async def send_message(callback_query, text):
    await callback_query.edit_message_text(text)