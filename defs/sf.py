import os
import asyncio
from dotenv import load_dotenv
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

load_dotenv('config.env')
username = os.getenv('SF_USERNAME')
password = os.getenv('SF_PASSWORD')
sf_confirm = {}
download_links = {}
upload_folders = {}
user_filenames = {}
progress_msg = None

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

async def handle_callback(client, callback_query):
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
