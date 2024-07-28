import os
from PIL import Image
from template import generate

async def bgen(client, message):
    try:
        message_text = ' '.join(message.command[1:])
        if not message_text:
            await message.reply_text("Please provide a message for the banner in the format /bgen (codename) (maintainer)")
            return
        
        try:
            codename, maintainer = message_text.split(maxsplit=1)
        except ValueError:
            await message.reply_text("Invalid message format. Please use /bgen (codename) (maintainer)")
            return
        
        if not codename or not maintainer:
            await message.reply_text("Both codename and maintainer are required.")
            return
        
        if not codename.isalnum() or not maintainer.isalnum():
            await message.reply_text("Codename and maintainer must only contain alphanumeric characters.")
            return
        
        banner_buffer = generate(codename, maintainer)
        output_filename = f'{codename}.png'
        
        with open(output_filename, 'wb') as file:
            file.write(banner_buffer.getbuffer())
        
        await message.reply_document(document=open(output_filename, 'rb'), caption=f"Banner for device {codename} & for {maintainer}.")
    except Exception as e:
        await message.reply_text(f"An error occurred: {str(e)}")
    finally:
        try:
            os.remove(output_filename)
        except Exception:
            pass
