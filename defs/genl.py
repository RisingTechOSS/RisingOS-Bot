import io
import os
import requests
from datetime import datetime
from pyrogram.types import Message
from pyrogram import filters, Client
from pyrogram.errors import MessageNotModified

async def genl(client, message):
    try:
        args = message.command[1:]
        if len(args) != 1:
            await message.reply_text("Please provide only the codename in the format /genl (codename)")
            return
        codename = args[0]
        data, source_changelog, device_changelog = extractl(codename)
        if data:
            message_text = formatl(data, source_changelog, device_changelog, codename)
            with open("banner.jpeg", "rb") as f:
                dummy_image_data = f.read()
            dummy_image_file = io.BytesIO(dummy_image_data)
            dummy_image_file.name = "banner.jpeg"
            await message.reply_photo(photo=dummy_image_file, caption=message_text)
        else:
            message_text = f"JSON or enough data not available for this device.\n\nCheck for {codename}.json file in <a href=\"https://github.com/RisingOSS-devices/android_vendor_RisingOTA.git\">OTA json repo</a>"
            await message.reply_text(message_text, disable_web_page_preview=True)
    except Exception as e:
        await message.reply_text("An error occurred while processing the command.")
        print(f"Error: {e}")

def extractl(codename):
    device_changelog = f"https://raw.githubusercontent.com/RisingOSS-devices/android_vendor_RisingOTA/fourteen/changelog_{codename}.txt"
    source_changelog = "https://github.com/RisingOS-staging/risingOS_changelogs"
    device_json = f"https://raw.githubusercontent.com/RisingOSS-devices/android_vendor_RisingOTA/fourteen/{codename}.json"
    try:
        response = requests.get(device_json)
        response.raise_for_status()
        data = response.json()
        return data, source_changelog, device_changelog
    except (requests.exceptions.HTTPError, requests.exceptions.RequestException, ValueError):
        return None, source_changelog, device_changelog

def formatl(data, source_changelog, device_changelog, codename):
    device = data['response'][0]['device']
    version = data['response'][0]['version']
    forum = data['response'][0]['forum']
    telegram = data['response'][0]['telegram']
    maintainer = data['response'][0]['maintainer']
    release_date = datetime.now().strftime('%d/%m/%Y')
    message = (
        f"#risingOS #UDC #ROM #{codename}\n"
        f"risingOS {version} | Official | Android 14\n"
        f"<b>Supported Device:</b> {device} ({codename})\n"
        f"<b>Released:</b> {release_date}\n"
        f"<b>Maintainer:</b> <a href=\"{telegram}\">{maintainer}</a>\n\n"
        f"<b>▪️Download:</b> VANILLA | CORE | GAPPS\n"
        f"<b>▪️Changelogs:</b> <a href=\"{source_changelog}\">Source</a> | <a href=\"{device_changelog}\">Device</a>\n"
        f"<b>▪️Support group:</b> <a href=\"https://t.me/RisingOSG\">Source</a> | <a href=\"{forum}\">Device</a>\n\n"
        f"<b>Notes:</b>\n•\n\n"
        f"<b>Credits:</b>\n• @not_ayan99 for the banner\n\n"
    )
    return message