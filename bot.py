import os
import requests
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# টোকেন এবং API এন্ডপয়েন্ট
TELEGRAM_TOKEN = "7479613855:AAFoEk8FOTOADo5hcewJPdEFOaIvgKLGyFg"
API_ENDPOINT = "https://molecular-angel-itachivai-e6c91c4d.koyeb.app/up"

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # ভিডিও ফাইল ডাউনলোড করুন
        file = await update.message.video.get_file()
        temp_file = f"temp_{update.update_id}.mp4"
        await file.download_to_drive(temp_file)
        
        # ফ্লাস্ক API-তে ভিডিও আপলোড করুন
        with open(temp_file, 'rb') as f:
            files = {'video': f}
            response = requests.post(API_ENDPOINT, files=files)
            
        # টেম্প ফাইল ডিলিট করুন
        os.remove(temp_file)
        
        # যদি API রেসপন্স সফল না হয়
        if response.status_code != 202:
            await update.message.reply_text("⚠️ Processing failed to start")
            return
            
        # প্রসেসিং স্ট্যাটাস চেক করার জন্য ডেটা নিন
        data = response.json()
        process_id = data['process_id']
        check_url = f"{API_ENDPOINT.rsplit('/',1)[0]}/check_status/{process_id}"
        
        # ইউজারকে প্রসেসিং শুরু হয়েছে জানান
        msg = await update.message.reply_text("🔄 Processing started...")
        
        # প্রসেসিং স্ট্যাটাস চেক করুন
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
    # টেলিগ্রাম বট অ্যাপ্লিকেশন তৈরি করুন
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # ভিডিও মেসেজ হ্যান্ডলার যোগ করুন
    app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    
    # বট চালান
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
