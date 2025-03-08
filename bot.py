import aiohttp
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import json  # Ensure json library is imported

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
            "api_link": None, # Changed from facebook_link to api_link
            "title": None,
            "description": None,
            "hd_link": None,
            "sd_link": None
        })
        await update.message.reply_text("অনুগ্রহ করে প্রথম এপিসোডের নম্বর দিন:")
    elif not user_info["episodes"]:
        pass
    else:
        current_episode_data = user_info["episodes"][-1]

        if current_episode_data["episode"] is None:
            current_episode_data["episode"] = text
            await update.message.reply_text("অনুগ্রহ করে API লিংক দিন:") # Changed prompt
        elif current_episode_data["api_link"] is None: # Changed from facebook_link to api_link
            current_episode_data["api_link"] = text # Changed from facebook_link to api_link
            await update.message.reply_text("ভিডিও তথ্য যুক্ত হয়েছে। আপনি কি অন্য এপিসোড যোগ করতে চান? হ্যাঁ অথবা না লিখুন অথবা /send লিখুন") #Just collect info, AI content will be generated on /send
        else:
            if text.isdigit():
                user_info["episodes"].append({
                    "episode": text,
                    "api_link": None, # Changed from facebook_link to api_link
                    "title": None,
                    "description": None,
                    "hd_link": None,
                    "sd_link": None
                })
                await update.message.reply_text("অনুগ্রহ করে API লিংক দিন:") # Changed prompt
            elif text.lower() == '/send':
                asyncio.create_task(send_data(update, context)) # Create a new task for each user's send_data request
            else:
                await update.message.reply_text("ইনপুট প্রসেসিং এ সমস্যা। /start দিয়ে আবার শুরু করুন অথবা এপিসোড নম্বর লিখুন।")



async def generate_ai_content_for_send(anime, episode, random_id): # Modified AI content generation function for /send
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
            f"🎬 টাইটেল: জেনারেট হবে সেন্ড করার পর\n" # টাইটেল এখন জেনারেট হবে না
            f"📝 ডেসক্রিপশন: জেনারেট হবে সেন্ড করার পর\n" # ডেসক্রিপশন এখন জেনারেট হবে না
            f"🖼️ থামনাইল লিংক: {user_info['thumbnail_link']}\n"
            f"🔗 API লিংক: {episode_data['api_link']}\n" # Changed from ফেসবুক ভিডিও লিংক to API link
            f"🔢 এনিমে নম্বর: {user_info['anime_number']}\n"
            f"🔢 সিজন নম্বর: {user_info['season_number']}\n"
            f"🔗 HD লিংক: প্রসেসিং করার পর পাওয়া যাবে\n" # HD link will be processed later
            f"🔗 SD লিংক: প্রসেসিং করার পর পাওয়া যাবে\n\n" # SD link will be processed later
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
        ai_content = await generate_ai_content_for_send(user_info["anime"], episode_data["episode"], random_id) # Generate AI content here

        if "error" in ai_content:
            error_messages.append(f"এপিসোড {episode_data['episode']} AI জেনারেশন ত্রুটি: {ai_content['error']}")
            return None, error_messages # Skip API call if AI content generation failed

        episode_data["title"] = ai_content["title"]
        episode_data["description"] = ai_content["description"]

        # Process API link to get HD and SD links
        api_link = episode_data["api_link"]
        episode_data["hd_link"] = "লিংক পাওয়া যায়নি" # Default value if HD link is not found
        episode_data["sd_link"] = "লিংক পাওয়া যায়নি" # Default value if SD link is not found

        try:
            async with aiohttp.ClientSession() as session_api_link:
                async with session_api_link.get(api_link) as response_api_link:
                    if response_api_link.status == 200:
                        api_video_data = await response_api_link.json() # Parse JSON response
                        episode_data["hd_link"] = api_video_data.get("hd", episode_data["hd_link"]) # Extract HD link
                        episode_data["sd_link"] = api_video_data.get("sd", episode_data["sd_link"]) # Extract SD link
                    else:
                        error_messages.append(f"API request failed for episode {episode_data['episode']} with status code: {response_api_link.status}")
                        return None, error_messages # Skip API call if API link request failed
        except aiohttp.ClientError as e:
            error_messages.append(f"API request error for episode {episode_data['episode']}: {str(e)}")
            return None, error_messages # Skip API call if API link request error


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

        async with aiohttp.ClientSession() as session_api: # separate session for api call
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
                    await update.message.reply_text(response_message) # Send success message immediately
                else:
                    error_message = f"❌ এপিসোড {episode_data['episode']} যুক্ত করতে সমস্যা হয়েছে: {api_data.get('message', 'No message')}"
                    error_messages.append(error_message)
                    await update.message.reply_text(error_message) # Send error message immediately

                await asyncio.sleep(5) # ৫ সেকেন্ড বিরতি

    except Exception as e:
        error_message = f"এপিসোড {episode_data['episode']} API request error: {str(e)}"
        error_messages.append(error_message)
        await update.message.reply_text(error_message) # Send error message immediately
    return success_messages, error_messages


# ডেটা সেন্ড করার হ্যান্ডলার
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

    # Process episodes sequentially for each user
    all_success_messages = []
    all_error_messages = []
    for episode_data in user_info["episodes"]:
        success_messages, error_messages = await process_episode_data(update, context, user_info, episode_data)
        if success_messages:
            all_success_messages.extend(success_messages)
        if error_messages:
            all_error_messages.extend(error_messages)

    if all_error_messages and not all_success_messages: # if only errors, send summary of errors
        final_response_message = "⚠️ কিছু এপিসোড যুক্ত করতে সমস্যা হয়েছে:\n" + "\n".join(all_error_messages)
        await update.message.reply_text(final_response_message)
    elif all_error_messages and all_success_messages: # if both success and error, send success and then error summary
        final_response_message = "⚠️ কিছু এপিসোড যুক্ত করতে সমস্যা হয়েছে:\n" + "\n".join(all_error_messages)
        await update.message.reply_text(final_response_message)
    elif all_success_messages and not all_error_messages: # if only success, no need for extra message, success messages are already sent episode by episode
        pass # Success messages are already sent episode by episode
    elif not all_success_messages and not all_error_messages: # no episodes processed
        await update.message.reply_text("কোন এপিসোড প্রসেসিং করা হয়নি।")

    del user_data[user_id] # ইউজার ডেটা ডিলিট করে দিন
    await show_preview_all(update, context) # Show preview after processing all episodes


async def handle_send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    if user_id not in user_data:
        await update.message.reply_text("প্রথমে /start কমান্ড ব্যবহার করুন")
        return

    if not user_data[user_id]["episodes"]: # Check if episodes data is available before showing preview
         await update.message.reply_text("কোন এপিসোড তথ্য নেই।")
         return

    await show_preview_all(update, context) # Show preview before processing
    # এরপর ইউজার যদি সেন্ড করতে চায় তাহলে আলাদা বাটন অথবা কমান্ড এর মাধ্যমে সেন্ড করবে। currently /send করবে preview দেখে

def main():
    TOKEN = "7867830008:AAF1hgq5liyBgGn3ATOXQ-vMyo5KFVi4MnE"  # আপনার বটের টোকেন
    app = Application.builder().token(TOKEN).build()

    # হ্যান্ডলার রেজিস্টার করুন
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", handle_send_command)) # Use handle_send_command to create task
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input))

    # বট চালু করুন
    print("বট চালু হয়েছে...")
    app.run_polling()


if __name__ == "__main__":
    main()
