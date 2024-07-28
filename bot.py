import os
import io
import time
import aiohttp
import asyncio
import requests
import tempfile
import subprocess
from defs.shell import shell
from defs.ping import ping
from datetime import datetime
from template import *
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

load_dotenv('config.env')
BOT_TOKEN = os.getenv('BOT_TOKEN')
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')
username = os.getenv('SF_USERNAME')
password = os.getenv('SF_PASSWORD')

app = Client("rising", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
allowed_chats = [int(chat_id) for chat_id in os.getenv('ALLOWED_CHATS').split(',')]

post_confirmation = {}
postl_confirmation = {}
sv_confirmation = {}
sf_confirm = {}
download_links = {}
upload_folders = {}
user_filenames = {}
progress_msg = None

@app.on_message(filters.command("start") & filters.chat(allowed_chats))
def start_command(client, message):
    welcome_message = "Welcome to the risingOSS Bot! How can I assist you today?"
    button = InlineKeyboardButton("Get Started", callback_data="get_started")
    keyboard = InlineKeyboardMarkup([[button]])
    message.reply_text(welcome_message, reply_markup=keyboard)

@app.on_callback_query(filters.regex("^get_started$"))
def callback_query(client, callback_query):
    help_message = """Welcome to the risingOSS Bot! Here are the available commands:
/gen -  Generate a post with a banner.
/genl - Generate a legacy post with a banner (depricated).
/bgen - Generate a high-quality banner.
/post - Post messages from our maintainers group (depricated).
/sf - Upload files to SourceForge.net from temporary download links (down for now).
/sv - Save documents to private message through bot.
/ping - check response time.
/shell - Devs only.
/cg - Replace banner (Devs only).
Feel free to explore and make the most of bot's capabilities."""
    callback_query.message.edit_text(text=help_message, reply_markup=None)

@app.on_message(filters.command("bgen") & filters.chat(allowed_chats))
def handle_bgen(client, message):
    try:
        message_text = ' '.join(message.command[1:])
        if not message_text:
            message.reply_text("Please provide a message for the banner in the format /bgen (codename) (maintainer)")
            return
        codename, maintainer = message_text.split(maxsplit=1)
        banner_buffer = generate(codename, maintainer)
        output_filename = f'{codename}.png'
        with open(output_filename, 'wb') as file:
            file.write(banner_buffer.getbuffer())
        message.reply_document(document=open(output_filename, 'rb'), caption=f"Banner for device {codename} & for {maintainer}.")
    except Exception as e:
        message.reply_text(f"An error occurred: {str(e)}")
    finally:
        try:
            os.remove(output_filename)
        except Exception:
            pass

@app.on_message(filters.command("gen") & filters.chat(allowed_chats))
def handle_gen(client, message):
    try:
        args = message.command[1:]
        if len(args) != 1:
            message.reply_text(
                "Please provide only the codename in the format /gen (codename)"
            )
            return
        codename = args[0]
        data, source, changelog, download_url, screenshot_url = extract(codename)
        if data:
            message_text = format(
                data, source, changelog, codename, download_url, screenshot_url
            )
            with open("dummy.png", "rb") as f:
                dummy_image_data = f.read()
            dummy_image_file = io.BytesIO(dummy_image_data)
            dummy_image_file.name = "dummy.png"
            keyboard = [[InlineKeyboardButton("Post", callback_data="post_yes"),
                         InlineKeyboardButton("Don't", callback_data="post_no")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            sent_message = message.reply_photo(photo=dummy_image_file, caption=message_text, reply_markup=reply_markup)
            post_confirmation[message.chat.id] = sent_message
        else:
            message_text = f"JSON or enough data not available for this device.\n\nCheck for {codename}.json file in OTA json repo"
            message.reply_text(message_text, disable_web_page_preview=True)
    except Exception as e:
        message.reply_text("An error occurred while processing the command.")
        print(f"Error: {e}")

@app.on_callback_query(filters.regex("^post_"))
async def post_confirmation_callback(client, callback_query):
    chat_id = callback_query.message.chat.id
    if chat_id in allowed_chats:
        try:
            if callback_query.data == "post_yes":
                if chat_id in post_confirmation:
                    message = post_confirmation.pop(chat_id)
                    await message.edit_reply_markup(reply_markup=None)
                    await message.copy(chat_id='@' + CHANNEL_USERNAME, reply_markup=None)
            elif callback_query.data == "post_no":
                if chat_id in post_confirmation:
                    post_confirmation.pop(chat_id)
                    await callback_query.message.edit_reply_markup(reply_markup=None)  # Remove buttons
        except Exception as e:
            print(f"Error: {e}")

def extract(codename):
    download_url = f"https://sourceforge.net/projects/risingos-official/files/4.x/"
    changelog = f"https://raw.githubusercontent.com/RisingOSS-devices/android_vendor_RisingOTA/fourteen/changelog_{codename}.txt"
    source = "https://github.com/RisingTechOSS/risingOS_changelogs"
    json_url = f"https://raw.githubusercontent.com/RisingOSS-devices/android_vendor_RisingOTA/fourteen/{codename}.json"
    screenshot_url = get_ss()
    try:
        response = requests.get(json_url)
        response.raise_for_status()
        data = response.json()
        return data, source, changelog, download_url, screenshot_url
    except (
        requests.exceptions.HTTPError,
        requests.exceptions.RequestException,
        ValueError,
    ):
        return None, source, changelog, download_url, screenshot_url

def format(data, source, changelog, codename, download_url, screenshot_url):
    device = data["response"][0]["device"]
    version = data["response"][0]["version"]
    forum = data["response"][0]["forum"]
    telegram = data["response"][0]["telegram"]
    maintainer = data["response"][0]["maintainer"]
    message = (
        f"<b>{device} ({codename})</b>\n"
        f"<b>By:</b> <a href=\"{telegram}\">{maintainer}</a>\n"
        f"<b>Version:</b> <a href=\"{source}\">{version}</a>\n\n"
        f"<b><a href=\"{download_url}\">Download</a> | <a href=\"{changelog}\">Changelogs</a> | <a href=\"{screenshot_url}\">Screenshots</a> | <a href=\"{forum}\">Support</a></b>\n\n"
        f"#risinginyourarea #UDC #{codename}"
    )
    return message

def get_ss():
    url = f"https://telegram.me/s/{CHANNEL_USERNAME}"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        sections = soup.find_all("div", {"class": "tgme_widget_message_wrap"})
        for section in sections:
            photos = section.find_all("div", {"class": "tgme_widget_message_photo"})
            if len(photos) > 2:
                message_url = section.find("a", {"class": "tgme_widget_message_date"})["href"]
                return message_url
    return None

@app.on_message(filters.command("genl") & filters.chat(allowed_chats))
def handle_genl(client, message):
    try:
        args = message.command[1:]
        if len(args) != 1:
            message.reply_text("Please provide only the codename in the format /genl (codename)")
            return
        codename = args[0]
        data, source_changelog, device_changelog = extractl(codename)
        if data:
            message_text = formatl(data, source_changelog, device_changelog, codename)
            with open("dummy.png", "rb") as f:
                dummy_image_data = f.read()
            dummy_image_file = io.BytesIO(dummy_image_data)
            dummy_image_file.name = "dummy.png"
            message.reply_photo(photo=dummy_image_file, caption=message_text)
        else:
            message_text = f"JSON or enough data not available for this device.\n\nCheck for {codename}.json file in <a href=\"https://github.com/RisingOSS-devices/android_vendor_RisingOTA.git\">OTA json repo</a>"
            message.reply_text(message_text, disable_web_page_preview=True)
    except Exception as e:
        message.reply_text("An error occurred while processing the command.")
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

@app.on_message(filters.command("sf"))
async def sf(client, message):
    if len(message.command) < 3:
        await message.reply("Use /sf [link] [filename] [CORE/VANILLA/PIXEL]/[codename].")
        return
    download_link = message.command[1]
    filename = message.command[2]
    folder = message.command[3] if len(message.command) >= 4 else None
    if not download_link.startswith(("http://", "https://")):
        download_link = f"https://{download_link}"
    confirm_text = f"Great choice! Are you ready to download and upload the file from this link?\n\n{download_link}"
    confirm_text += f"\nFilename: `{filename}`\nFolder to Upload: {folder if folder else 'the default folder'}"
    confirm_markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Yes", callback_data="confirm"),
          InlineKeyboardButton("No", callback_data="cancel")]]
    )
    msg = await message.reply_text(confirm_text, reply_markup=confirm_markup, disable_web_page_preview=True)

    user_id = message.from_user.id
    sf_confirm[user_id] = msg
    download_links[user_id] = download_link
    upload_folders[user_id] = folder
    user_filenames[user_id] = filename

@app.on_callback_query(filters.regex(r"(confirm|cancel)"))
async def handle_callback_query(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    msg_to_delete = sf_confirm.get(user_id)
    if msg_to_delete is None:
        return
    filename = user_filenames.get(user_id)
    username = callback_query.from_user.username
    user_mention = f"@{username}" if username else f"<a href='tg://user?id={user_id}'>{callback_query.from_user.first_name}</a>"
    start_time = datetime.now()
    if data == "confirm":
        await msg_to_delete.delete()
        download_msg = await callback_query.message.reply_text(f"{user_mention}, Downloading `{filename}` ...")

        download_link = download_links.get(user_id)
        folder = upload_folders.get(user_id)
        filename = user_filenames.get(user_id)
        temp_file_path = await sf_download(download_link, filename)
        download_time = datetime.now() - start_time
        download_time_str = f"{download_time.seconds} seconds"
        await download_msg.delete()
        upload_msg = await callback_query.message.reply_text(f"{user_mention}, `{filename}` downloaded in {download_time_str}. Now uploading...")
        start_time = datetime.now()
        upload_result = await sf_upload(temp_file_path, folder)
        upload_time = datetime.now() - start_time
        upload_time_str = f"{upload_time.seconds} seconds"
        if upload_result:
            await upload_msg.delete()
            uploaded_message = f"{user_mention}, `{filename}` uploaded successfully in {upload_time_str}. Click below to access it."
            keyboard = [[InlineKeyboardButton("Open File", url=f"https://sourceforge.net/projects/risingos-official/files/4.x/{folder if folder else 'the default folder'}/{filename}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await callback_query.message.reply_text(uploaded_message, reply_markup=reply_markup, disable_web_page_preview=True)
            os.remove(temp_file_path)
        if not upload_result:
            await upload_msg.delete()
            await callback_query.message.reply_text("Oops, something went wrong during the upload. Please try again later")
    elif data == "cancel":
        await msg_to_delete.delete()
        await callback_query.message.reply_text("No problem, the operation has been canceled.")
        if user_id in sf_confirm:
            del sf_confirm[user_id]
        if user_id in download_links:
            del download_links[user_id]
        if user_id in upload_folders:
           del upload_folders[user_id]
        if user_id in user_filenames:
           del user_filenames[user_id]

async def sf_download(download_link, filename):
    try:
        process = await asyncio.create_subprocess_shell(
            f"wget -q -O {filename} {download_link}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            print(f"Downloaded to: {filename}")
            return filename
        else:
            print(f"Download failed: {stderr.decode()}")
    except Exception as e:
        print(f"Download failed: {str(e)}")
    return None

async def sf_upload(file_path, folder):
    command = f"sshpass -p {password} rsync -e 'ssh -o StrictHostKeyChecking=no' -avz {file_path} {username}@web.sourceforge.net:/home/frs/project/risingos-official/4.x/{folder}/"
    process = await asyncio.create_subprocess_shell(
        command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    if process.returncode == 0:
        return True
    else:
        print(f"Error: {stderr.decode()}")
        return False

async def handle_confirmation(client, message, confirmation_dict, command_text):
    if message.reply_to_message:
        confirmation_dict[message.chat.id] = message.reply_to_message
        keyboard = [[InlineKeyboardButton("Yes", callback_data=f"{command_text}_yes"),
                    InlineKeyboardButton("No", callback_data=f"{command_text}_no")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await message.reply_text("Do you want to send this message?", reply_markup=reply_markup)
    else:
        await message.reply_text(f"Please reply to a message with /{command_text} to send it.")

async def send_message(callback_query, message_text):
    await callback_query.message.edit_text(message_text)


@app.on_message(filters.command("sv") & filters.chat(allowed_chats))
async def sv_command(client, message):
    try:
        if message.reply_to_message:
            sv_confirmation[message.chat.id] = message
            keyboard = [[InlineKeyboardButton("Yes", callback_data="sv_yes"),
                        InlineKeyboardButton("No", callback_data="sv_no")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await message.reply_text("Do you want to send this message?", reply_markup=reply_markup)

            @app.on_callback_query(filters.regex("^sv_"))
            async def confirmation_callback(client, callback_query):
                chat_id = callback_query.message.chat.id
                if chat_id in allowed_chats:
                    try:
                        if callback_query.data == "sv_yes":
                            if chat_id in sv_confirmation and sv_confirmation[chat_id].reply_to_message:
                                message_to_copy = sv_confirmation[chat_id].reply_to_message
                                await message_to_copy.copy(chat_id=callback_query.from_user.id)
                                await send_message(callback_query, "Message copied.")
                        elif callback_query.data == "sv_no":
                            if chat_id in sv_confirmation:
                                sv_confirmation.pop(chat_id)
                                await send_message(callback_query, "Message copying canceled.")
                    except Exception as e:
                        print(f"Error: {e}")
        else:
            instructions = "To copy a message, reply to it with /sv ."
            await message.reply_text(instructions)
    except Exception as e:
        print(f"Error: {e}")

@app.on_message(filters.command("post") & filters.chat(allowed_chats))
async def postl_command(client, message):
    try:
        if message.reply_to_message:
            postl_confirmation[message.chat.id] = message.reply_to_message
            keyboard = [[InlineKeyboardButton("Yes", callback_data="postl_yes"),
                        InlineKeyboardButton("No", callback_data="postl_no")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await message.reply_text("Do you want to send this message?", reply_markup=reply_markup)

            @app.on_callback_query(filters.regex("^postl_"))
            async def postl_confirmation_callback(client, callback_query):
                chat_id = callback_query.message.chat.id
                if chat_id in allowed_chats:
                    try:
                        if callback_query.data == "postl_yes":
                            if chat_id in postl_confirmation:
                                message = postl_confirmation.pop(chat_id)
                                await message.copy(chat_id='@' + CHANNEL_USERNAME)
                                await send_message(callback_query, "Message sent.")
                        elif callback_query.data == "post_no":
                            if chat_id in post_confirmation:
                                post_confirmation.pop(chat_id)
                                await send_message(callback_query, "Message canceled.")
                    except Exception as e:
                        print(f"Error: {e}")
        else:
            await message.reply_text("Please reply to a message with /post to post it.")
    except Exception as e:
        print(f"Error: {e}")

async def handle_confirmation_callback(client, callback_query, confirmation_dict, target_chat_id, command_prefix):
    chat_id = callback_query.message.chat.id
    if chat_id in allowed_chats:
        try:
            if callback_query.data == f"{command_prefix}_yes":
                if chat_id in confirmation_dict:
                    message = confirmation_dict.pop(chat_id)
                    await message.copy(chat_id=target_chat_id)
                    await send_message(callback_query, "Message copied.")
            elif callback_query.data == f"{command_prefix}_no":
                if chat_id in confirmation_dict:
                    confirmation_dict.pop(chat_id)
                    await send_message(callback_query, "Message canceled.")
        except Exception as e:
            print(f"Error: {e}")

def download_images(app):
    @app.on_message(filters.group & filters.reply & filters.user(authorized_users) & filters.regex(r'^/cg'))
    async def handle_cg_reply(client, message):
        chat_id = message.chat.id
        if chat_id in allowed_chats:
            replied_msg = await message.get_reply_message()
            if replied_msg.media:
                for media in replied_msg.media:
                    if media.photo:
                        path = await client.download_media(media, file_name="dummy.png")
                        print(f"Image downloaded: {path}")
                        break

@app.on_message(filters.command("shell"))
async def handle_shell(client, message):
    await shell(client, message)

@app.on_message(filters.command("ping"))
async def handle_ping(client, message):
    await ping(client, message)

if __name__ == "__main__":
    app.run()
