import asyncio
from time import monotonic
from pyrogram import filters

async def ping(client, message):
    start = monotonic()
    reply = await message.reply_text("Starting Ping...")
    end = monotonic()
    time = int((end - start) * 1000)
    await reply.edit_text(f'Pong! {time} ms.')