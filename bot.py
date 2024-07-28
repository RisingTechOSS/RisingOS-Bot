import os
from dotenv import load_dotenv
from pyrogram import Client, filters
from defs.start import start, get_started_callback
from defs.gen import gen, gen_callback
from defs.sf import sf, handle_callback
from defs.sv import sv, sv_callback
from defs.post import post, post_callback
from defs.bgen import bgen
from defs.genl import genl
from defs.ping import ping
from defs.ub import ub

load_dotenv('config.env')
BOT_TOKEN = os.getenv('BOT_TOKEN')
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
allowed_chats = [int(chat_id) for chat_id in os.getenv('ALLOWED_CHATS').split(',')]

app = Client("rising", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start") & filters.chat(allowed_chats))
async def start_handler(client, message):
    await start(client, message)

@app.on_callback_query(filters.regex("^get_started$"))
async def callback_query_handler(client, callback_query):
    await get_started_callback(client, callback_query)

@app.on_message(filters.command("gen") & filters.chat(allowed_chats))
async def handle_gen(client, message):
    await gen(client, message)

@app.on_callback_query(filters.regex("^post_"))
async def post_confirmation_callback(client, callback_query):
    await gen_callback(client, callback_query)

@app.on_message(filters.command("sf") & filters.chat(allowed_chats))
async def handle_sf(client, message):
    await sf(client, message)

@app.on_callback_query(filters.regex(r"(confirm|cancel)"))
async def handle_callback_query(client, callback_query):
    await handle_callback(client, callback_query)

@app.on_message(filters.command("sv") & filters.chat(allowed_chats))
async def handle_sv(client, message):
    await sv(client, message)

@app.on_callback_query(filters.regex("^sv_"))
async def sv_confirmation_callback(client, callback_query):
    await sv_callback(client, callback_query)

@app.on_message(filters.command("post") & filters.chat(allowed_chats))
async def postl_command(client, message):
    await post(client, message)

@app.on_callback_query(filters.regex("^postl_"))
async def postl_confirmation_callback(client, callback_query):
    await post_callback(client, callback_query)

@app.on_message(filters.command("bgen") & filters.chat(allowed_chats))
async def handle_bgen(client, message):
    await bgen(client, message)

@app.on_message(filters.command("genl") & filters.chat(allowed_chats))
async def handle_genl(client, message):
    await genl(client, message)

@app.on_message(filters.command("ping") & filters.chat(allowed_chats))
async def handle_ping(client, message):
    await ping(client, message)

@app.on_message(filters.command("ub") & filters.chat(allowed_chats))
async def handle_ub(client, message):
    await ub(client, message)

if __name__ == "__main__":
    app.run()
