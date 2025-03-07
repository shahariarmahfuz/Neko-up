import aiohttp
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio

# ইউজারের তথ্য সংরক্ষণের জন্য ডিকশনারি
user_data = {}

# /start হ্যান্ডলার
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    user_data[user_id] = {
        "anime": None,
        "thumbnail_link": None,
        "anime_number": None,
        "season_number": None,
        "episodes": [] # এপিসোডের ডেটা লিস্ট
    }
    await update.message.reply_text("অনুগ্রহ করে এনিমের নাম দিন:")

# ইউজার ইনপুট হ্যান্ডলিং
async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    if user_id not in user_data:
        await update.message.reply_text("প্রথমে /start কমান্ড ব্যবহার করুন")
        return

    user_info = user_data[user_id]
    text = update.message.text.strip()

    if user_info["anime"] is None:
        user_info["anime"] = text
        await update.message.reply_text("অনুগ্রহ করে এনিমের থাম্বনেইল লিংক দিন:")
    elif user_info["thumbnail_link"] is None:
        user_info["thumbnail_link"] = text
        await update.message.reply_text("অনুগ্রহ করে এনিমে নম্বর দিন:")
    elif user_info["anime_number"] is None:
        user_info["anime_number"] = text
        await update.message.reply_text("অনুগ্রহ করে এনিমে সিজন নম্বর দিন:")
    elif user_info["season_number"] is None:
        user_info["season_number"] = text
        user_info["episodes"].append({
            "episode": None,
            "hd_link": None,
            "sd_link": None,
            "title": None,
            "description": None,
        })
        await update.message.reply_text("অনুগ্রহ করে প্রথম এপিসোডের নম্বর দিন:")
    elif not user_info["episodes"]:
        pass
    else:
        current_episode_data = user_info["episodes"][-1]

        if current_episode_data["episode"] is None:
            current_episode_data["episode"] = text
            await update.message.reply_text("অনুগ্রহ করে HD ভিডিও লিংক দিন:")
        elif current_episode_data["hd_link"] is None:
            current_episode_data["hd_link"] = text
            await update.message.reply_text("অনুগ্রহ করে SD ভিডিও লিংক দিন:")
        elif current_episode_data["sd_link"] is None:
            current_episode_data["sd_link"] = text
            await update.message.reply_text("ভিডিও তথ্য যুক্ত হয়েছে। আপনি কি অন্য এপিসোড যোগ করতে চান? হ্যাঁ অথবা না লিখুন")
        else:
            if text.isdigit():
                user_info["episodes"].append({
                    "episode": text,
                    "hd_link": None,
                    "sd_link": None,
                    "title": None,
                    "description": None,
                })
                await update.message.reply_text("অনুগ্রহ করে HD ভিডিও লিংক দিন:")
            elif text.lower() == '/send':
                asyncio.create_task(send_data(update, context))
            else:
                await update.message.reply_text("ইনপুট প্রসেসিং এ সমস্যা। /start দিয়ে আবার শুরু করুন অথবা এপিসোড নম্বর লিখুন।")

async def generate_ai_content_for_send(anime, episode, random_id):
    episode_data = {
            "title": None,
            "description": None,
        }
    try:
        async with aiohttp.ClientSession() as session:
            # ডেসক্রিপশন জেনারেট
            desc_params = {
                "q": f"Write a description for episode number {episode} of {anime}. 20-25 words. Only description.",
                "id": random_id
            }
            async with session.get("https://new-ai-buxr.onrender.com/ai", params=desc_params) as response:
                desc_response = await response.json()
                episode_data["description"] = desc_response.get("response", "ডেসক্রিপশন জেনারেট করতে সমস্যা!")

            # টাইটেল জেনারেট
            title_params = {
                "q": f"Write the title of episode number {episode} of {anime}. Only title and No additional symbols or text may be written. There's no need to bold the text, just give it normally.",
                "id": random_id
            }
            async with session.get("https://new-ai-buxr.onrender.com/ai", params=title_params) as response:
                title_response = await response.json()
                episode_data["title"] = title_response.get("response", "টাইটেল জেনারেট করতে সমস্যা!")
        return episode_data
    except Exception as e:
        return {"error": f"এআই কনটেন্ট জেনারেশনে ত্রুটি: {str(e)}"}

# সকল এপিসোডের প্রিভিউ দেখানো
async def show_preview_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    user_info = user_data[user_id]

    preview_message_all = "🎬 সকল এপিসোডের প্রিভিউ:\n\n"
    for episode_data in user_info["episodes"]:
        preview_message_all += (
            f"📺 এনিমে: {user_info['anime']}\n"
            f"🔢 এপিসোড: {episode_data['episode']}\n"
            f"🎬 টাইটেল: জেনারেট হবে সেন্ড করার পর\n"
            f"📝 ডেসক্রিপশন: জেনারেট হবে সেন্ড করার পর\n"
            f"🖼️ থামনাইল লিংক: {user_info['thumbnail_link']}\n"
            f"🔗 HD লিংক: {episode_data['hd_link']}\n"
            f"🔗 SD লিংক: {episode_data['sd_link']}\n"
            f"🔢 এনিমে নম্বর: {user_info['anime_number']}\n"
            f"🔢 সিজন নম্বর: {user_info['season_number']}\n\n"
            "------------------------\n"
        )
    preview_message_all += "যদি সব তথ্য সঠিক থাকে, /send লিখে ভিডিওগুলো যুক্ত করুন।"
    await update.message.reply_text(preview_message_all)

async def process_episode_data(update: Update, context: ContextTypes.DEFAULT_TYPE, user_info, episode_data):
    success_messages = []
    error_messages = []
    try:
        await update.message.reply_text(f"এপিসোড {episode_data['episode']} প্রসেসিং করা হচ্ছে...")

        random_id = random.randint(1000, 9999)
        ai_content = await generate_ai_content_for_send(user_info["anime"], episode_data["episode"], random_id)

        if "error" in ai_content:
            error_messages.append(f"এপিসোড {episode_data['episode']} AI জেনারেশন ত্রুটি: {ai_content['error']}")
            return None, error_messages

        episode_data["title"] = ai_content["title"]
        episode_data["description"] = ai_content["description"]

        api_url = "https://nekofilx.onrender.com/ad"
        params = {
            "a": user_info["anime_number"],
            "s": user_info["season_number"],
            "t": episode_data["title"],
            "720p": episode_data["hd_link"],
            "480p": episode_data["sd_link"],
            "th": user_info["thumbnail_link"],
            "d": episode_data["description"],
            "eps": episode_data["episode"]
        }

        async with aiohttp.ClientSession() as session_api:
            async with session_api.get(api_url, params=params) as response_api:
                api_data = await response_api.json()
                if api_data.get("status") == "success":
                    response_message = (
                        f"✅ এপিসোড {episode_data['episode']} যুক্ত করা হয়েছে!\n\n"
                        f"🎬 এনিমে আইডি: {api_data['anime_id']}\n"
                        f"🔢 সিজন: {api_data['season']}\n"
                        f"📝 মেসেজ: {api_data['message']}\n\n"
                        "ভিডিও তথ্য:\n"
                        f"🆔 আইডি: {api_data['video']['id']}\n"
                        f"🔢 সিরিয়াল: {api_data['video']['serial']}\n"
                        f"🎬 টাইটেল: {api_data['video']['title']}\n"
                        f"📝 ডেসক্রিপশন: {api_data['video']['description']}\n"
                        f"🖼️ থাম্বনাইল: {api_data['video']['thumbnail']}\n"
                        f"🔗 HD: {api_data['video']['links']['720p']}\n"
                        f"🔗 SD: {api_data['video']['links']['480p']}"
                    )
                    success_messages.append(response_message)
                    await update.message.reply_text(response_message)
                else:
                    error_message = f"❌ এপিসোড {episode_data['episode']} যুক্ত করতে সমস্যা হয়েছে: {api_data.get('message', 'No message')}"
                    error_messages.append(error_message)
                    await update.message.reply_text(error_message)

                await asyncio.sleep(5)

    except Exception as e:
        error_message = f"এপিসোড {episode_data['episode']} API request error: {str(e)}"
        error_messages.append(error_message)
        await update.message.reply_text(error_message)
    return success_messages, error_messages

async def send_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    if user_id not in user_data:
        await update.message.reply_text("প্রথমে /start কমান্ড ব্যবহার করুন")
        return

    user_info = user_data[user_id]
    episodes_data = user_info["episodes"]

    if not episodes_data:
        await update.message.reply_text("কোন এপিসোড তথ্য নেই।")
        return

    await update.message.reply_text(f"মোট {len(episodes_data)} এপিসোড প্রসেসিং করা হচ্ছে...")

    all_success_messages = []
    all_error_messages = []
    for episode_data in user_info["episodes"]:
        success_messages, error_messages = await process_episode_data(update, context, user_info, episode_data)
        if success_messages:
            all_success_messages.extend(success_messages)
        if error_messages:
            all_error_messages.extend(error_messages)

    if all_error_messages and not all_success_messages:
        final_response_message = "⚠️ কিছু এপিসোড যুক্ত করতে সমস্যা হয়েছে:\n" + "\n".join(all_error_messages)
        await update.message.reply_text(final_response_message)
    elif all_error_messages and all_success_messages:
        final_response_message = "⚠️ কিছু এপিসোড যুক্ত করতে সমস্যা হয়েছে:\n" + "\n".join(all_error_messages)
        await update.message.reply_text(final_response_message)

    del user_data[user_id]

def main():
    TOKEN = "7059109518:AAHts5ZOlUCqAimWvlO6dtEGnWY723f_gQk"
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", handle_send_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))

    print("বট চালু হয়েছে...")
    app.run_polling()

async def handle_send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    asyncio.create_task(send_data(update, context))

if __name__ == "__main__":
    main()
