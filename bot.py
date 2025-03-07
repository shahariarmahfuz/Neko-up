import os
import requests
import asyncio
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, CallbackContext

TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
API_ENDPOINT = "http://your-flask-app-domain:8000/up"

async def handle_video(update: Update, context: CallbackContext):
    try:
        file = await update.message.video.get_file()
        temp_file = f"temp_{update.update_id}.mp4"
        await file.download_to_drive(temp_file)
        
        with open(temp_file, 'rb') as f:
            files = {'video': f}
            response = requests.post(API_ENDPOINT, files=files)
            
        os.remove(temp_file)
        
        if response.status_code != 202:
            await update.message.reply_text("⚠️ Processing failed to start")
            return
            
        data = response.json()
        process_id = data['process_id']
        check_url = f"{API_ENDPOINT.rsplit('/',1)[0]}/check_status/{process_id}"
        
        msg = await update.message.reply_text("🔄 Processing started...")
        
        while True:
            status_response = requests.get(check_url, headers={'Accept': 'application/json'})
            if status_response.status_code == 200:
                result = status_response.json()
                if result['status'] == 'success':
                    await msg.edit_text(f"✅ Processed!\nURL: {result['url']}")
                    break
                elif result['status'] == 'error':
                    await msg.edit_text(f"❌ Error: {result['message']}")
                    break
            await asyncio.sleep(5)
            
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.run_polling()

if __name__ == "__main__":
    main()
