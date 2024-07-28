import os
import time
import asyncio
import subprocess
from pyrogram import Client

async def shell(client, message):
    authorized_users = os.environ.get("DEVS", "").split(",")
    user_id = str(message.from_user.id)
    if user_id not in authorized_users:
        await message.reply_text("You don't have access to run this command.")
        return

    cmd = message.text.split(maxsplit=1)
    if len(cmd) == 1:
        await message.reply_text("No command to execute was given.")
        return

    cmd = cmd[1]
    start_time = time.time()
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        end_time = time.time()
        ping_time = int((end_time - start_time) * 1000)
        reply = f"<b>Command Output:</b>\n\n`{result.stdout}`"
        if result.stderr:
            reply += f"\n\n<b>Error Output:</b>\n\n`{result.stderr}`"
        reply += f"\n\n<b>Execution Time:</b> {ping_time}ms"
        await message.reply_text(reply)
    except Exception as e:
        await message.reply_text("An error occurred while processing the command.")