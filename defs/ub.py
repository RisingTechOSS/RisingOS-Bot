from pyrogram import filters, Client
from pyrogram.types import Message
import os
from PIL import Image

authorized_users = os.environ.get("DEVS", "").split(",")

def convert_to_jpeg(image_file):
    with Image.open(image_file) as img:
        if img.mode == "RGBA":
            img = img.convert("RGB")
        jpeg_image_path = os.path.join(os.getcwd(), "banner.jpeg")
        img.save(jpeg_image_path, format="JPEG", quality=85)
    return jpeg_image_path

async def ub(client, message):
    if message.reply_to_message and message.reply_to_message.document:
        file = message.reply_to_message.document
        if file.mime_type in ["image/png", "image/jpeg"]:
            file_id = file.file_id
            file_path = await client.download_media(file_id)
            jpeg_image_path = convert_to_jpeg(file_path)

            os.remove(file_path)
            await message.reply_text(f"Image converted and saved as {jpeg_image_path}.")
        else:
            await message.reply_text("Please reply to a document that is a PNG or JPEG image.")
    else:
        await message.reply_text("Please reply to a document.")