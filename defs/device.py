import os
import logging
import requests
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

load_dotenv('config.env')
chat_id = os.getenv('GROUP_ID')
files_storage = {}

async def fetch_rss_feed():
    try:
        response = requests.get('https://sourceforge.net/projects/risingos-official/rss?limit=10000000000000000000')
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return None

async def parse_rss_feed(rss_feed, codename):
    root = ET.fromstring(rss_feed)
    files_by_version = {}
    seen_files = {}
    codename_lower = codename.lower()
    
    for item in root.findall('.//item'):
        title = item.find('title').text.strip()
        link = item.find('link').text.strip()
        title_lower = title.lower()
        
        if codename_lower in title_lower:
            parts = title.split('-')
            if len(parts) > 1:
                version = parts[1]
            else:
                continue

            file_name = title.split('/')[-1]
            if 'gapps' in title_lower:
                variant = 'GAPPS'
            elif 'core' in title_lower:
                variant = 'CORE'
            elif 'vanilla' in title_lower:
                variant = 'VANILLA'
            else:
                continue

            if version not in files_by_version:
                files_by_version[version] = {'GAPPS': {}, 'CORE': {}, 'VANILLA': {}}

            if file_name in seen_files:
                continue

            if variant in files_by_version[version]:
                files_by_version[version][variant][file_name] = link
                seen_files[file_name] = variant
    
    return files_by_version

async def send_split_messages(message_text, message: Message):
    max_length = 4096
    while len(message_text) > max_length:
        split_index = message_text.rfind('\n', 0, max_length)
        if split_index == -1:
            split_index = max_length
        await message.reply(message_text[:split_index], disable_web_page_preview=True)
        message_text = message_text[split_index:]
    if message_text:
        await message.reply(message_text, disable_web_page_preview=True)

async def device(client: Client, message: Message):
    logging.info("Device function called")
    parts = message.text.split(' ', 1)
    
    if len(parts) == 1 or not parts[1].strip():
        await message.reply("Usage: /device [codename] (e.g., /device X00TD)", disable_web_page_preview=True)
    else:
        codename = parts[1].strip()
        logging.info(f"Fetching RSS feed for codename: {codename}")

        rss_feed = await fetch_rss_feed()
        if rss_feed:
            logging.info("RSS feed fetched successfully")
            files_by_version = await parse_rss_feed(rss_feed, codename)
            
            if files_by_version:
                logging.info(f"Files found for {codename}")
                files_storage[message.chat.id] = {"message": message, "files_by_version": files_by_version}
                await send_version_files(files_by_version, message)
            else:
                logging.info(f"No files found for {codename}")
                await message.reply("No files found. Device not supported or typo?", disable_web_page_preview=True)
        else:
            logging.error("Failed to fetch RSS feed")
            await message.reply("Failed to fetch RSS feed.", disable_web_page_preview=True)

async def send_version_files(files_by_version, message: Message):
    keyboard = []
    for version in files_by_version.keys():
        keyboard.append([InlineKeyboardButton(text=f"Version {version}", callback_data=f"version_{version}")])

    if keyboard:
        msg = await message.reply("Select a version:", reply_markup=InlineKeyboardMarkup(keyboard))
        files_storage[message.chat.id] = {"message": msg, "files_by_version": files_by_version}
    else:
        await message.reply("No files found. Device not supported or typo?", disable_web_page_preview=True)

async def device_callback(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    chat_id = callback_query.message.chat.id
    
    if data.startswith("version_"):
        selected_version = data.split("_")[1]
        
        files_data = files_storage.get(chat_id, {})
        files_by_version = files_data.get("files_by_version", {})
        original_message = files_data.get("message", None)
        
        if files_by_version and original_message:
            files = files_by_version.get(selected_version, {})
        
            response_message = f"**Version {selected_version}:**\n"
            for variant in ['GAPPS', 'CORE', 'VANILLA']:
                if files.get(variant):
                    response_message += f"\n__{variant}:__\n"
                    response_message += '\n'.join([f"[{file_name}]({file_link})" for file_name, file_link in files[variant].items()]) + "\n"
            response_message += "\n"

            keyboard = [[InlineKeyboardButton(text="Go Back", callback_data="go_back")]]

            await original_message.edit_text(response_message, reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)

            await callback_query.answer()
        else:
            await callback_query.message.edit_text("No files found.", disable_web_page_preview=True)

    elif data == "go_back":
        files_data = files_storage.get(chat_id, {})
        files_by_version = files_data.get("files_by_version", {})
        original_message = files_data.get("message", None)

        if files_by_version and original_message:
            await original_message.edit_text("Select a version:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text=f"Version {version}", callback_data=f"version_{version}")] for version in files_by_version.keys()]))
        
        await callback_query.answer()