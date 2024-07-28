import io
import os
import json
import aiohttp
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

load_dotenv('config.env')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')
post_confirmation = {}

async def gen(client, message):
    try:
        args = message.command[1:]
        if len(args) != 1:
            await message.reply_text("Please provide only the codename in the format /gen (codename)")
            return
        codename = args[0]
        data, source, changelog, download_url, screenshot_url = await extract(codename)
        if data:
            message_text = await format(data, source, changelog, codename, download_url, screenshot_url)
            with open("banner.jpeg", "rb") as f:
                image = io.BytesIO(f.read())
            keyboard = [
                [
                    InlineKeyboardButton("Post", callback_data="post_yes"),
                    InlineKeyboardButton("Don't", callback_data="post_no")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            sent_message = await message.reply_photo(photo=image, caption=message_text, reply_markup=reply_markup)
            post_confirmation[message.chat.id] = sent_message
        else:
            message_text = f"JSON or enough data not available for this codename: {codename}"
            await message.reply_text(message_text)
    except Exception as e:
        await message.reply_text(f"An error occurred: {str(e)}")

async def gen_callback(client, callback_query):
    chat_id = callback_query.message.chat.id
    try:
        if callback_query.data == "post_yes":
            if chat_id in post_confirmation:
                message = post_confirmation.pop(chat_id)
                await message.edit_reply_markup(reply_markup=None)
                await message.copy(chat_id='@' + CHANNEL_USERNAME, reply_markup=None)
        elif callback_query.data == "post_no":
            if chat_id in post_confirmation:
                post_confirmation.pop(chat_id)
                await callback_query.message.edit_reply_markup(reply_markup=None)
        await callback_query.answer()
    except Exception as e:
        await callback_query.answer("An error occurred", show_alert=True)

async def extract(codename):
    download_url = f"https://sourceforge.net/projects/risingos-official/files/4.x/"
    changelog = f"https://raw.githubusercontent.com/RisingOSS-devices/android_vendor_RisingOTA/fourteen/changelog_{codename}.txt"
    source = "https://github.com/RisingTechOSS/risingOS_changelogs"
    json_url = f"https://raw.githubusercontent.com/RisingOSS-devices/android_vendor_RisingOTA/fourteen/{codename}.json"
    screenshot_url = await get_ss()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(json_url) as response:
                response.raise_for_status()
                text = await response.text()
                data = json.loads(text)
        return data, source, changelog, download_url, screenshot_url
    except (aiohttp.ClientError, json.JSONDecodeError) as e:
        return None, source, changelog, download_url, screenshot_url

async def format(data, source, changelog, codename, download_url, screenshot_url):
    device = data["response"][0]["device"]
    version = data["response"][0]["version"]
    forum = data["response"][0]["forum"]
    telegram = data["response"][0]["telegram"]
    maintainer = data["response"][0]["maintainer"]
    
    screenshot_link = f"<a href=\"{screenshot_url}\">Screenshots</a> | " if screenshot_url else ""
    
    message = (
        f"<b>{device} ({codename})</b>\n"
        f"<b>By:</b> <a href=\"{telegram}\">{maintainer}</a>\n"
        f"<b>Version:</b> <a href=\"{source}\">{version}</a>\n\n"
        f"<b><a href=\"{download_url}\">Download</a> | <a href=\"{changelog}\">Changelogs</a> | {screenshot_link}<a href=\"{forum}\">Support</a></b>\n\n"
        f"#risinginyourarea #UDC #{codename}"
    )
    return message

async def get_ss():
    url = "https://telegram.me/s/RisingOS_news"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                text = await response.text()
                soup = BeautifulSoup(text, "html.parser")
                sections = soup.find_all("div", {"class": "tgme_widget_message_wrap"})
                for section in sections:
                    photos = section.find_all("div", {"class": "tgme_widget_message_photo"})
                    if len(photos) > 2:
                        return section.find("a", {"class": "tgme_widget_message_date"})["href"]
    return None