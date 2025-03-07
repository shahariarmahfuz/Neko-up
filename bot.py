import os
import asyncio
import requests
from telethon import TelegramClient, events
from dotenv import load_dotenv
import random
import aiohttp

# .env ফাইল থেকে ভেরিয়েবল লোড করুন
load_dotenv()

# টেলিগ্রাম API কনফিগারেশন
API_ID = "20716719"
API_HASH = "c929824683800816ddf0faac845d89c9"
BOT_TOKEN = "7867830008:AAE9ljH11pHuGVRA9XcwGYhoTYVnEP5cvHE"

# ফ্লাস্ক API এন্ডপয়েন্ট
# ফ্লাস্ক API এন্ডপয়েন্ট (removed as per request, using /up endpoint now)
# API_ENDPOINT = os.getenv("FLASK_API_ENDPOINT")

# Nekosfast API endpoint for video upload
VIDEO_UPLOAD_ENDPOINT = "https://molecular-angel-itachivai-e6c91c4d.koyeb.app/up"
AI_CONTENT_ENDPOINT = "https://new-ai-buxr.onrender.com/ai"
ADD_EPISODE_API_URL = "https://nekofilx.onrender.com/ad"


# ইউজার তথ্য সংরক্ষণের জন্য ডিকশনারি (Telethon context is different, using a simple dict for now)
user_data = {}

# ক্লায়েন্ট তৈরি করুন
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

async def generate_ai_content(anime, episode, random_id):
    """এআই কনটেন্ট জেনারেশন ফাংশন"""
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
            async with session.get(AI_CONTENT_ENDPOINT, params=desc_params) as response:
                desc_response = await response.json()
                episode_data["description"] = desc_response.get("response", "ডেসক্রিপশন জেনারেট করতে সমস্যা!")

            # টাইটেল জেনারেট
            title_params = {
                "q": f"Write the title of episode number {episode} of {anime}. Only title and No additional symbols or text may be written. There's no need to bold the text, just give it normally.",
                "id": random_id
            }
            async with session.get(AI_CONTENT_ENDPOINT, params=title_params) as response:
                title_response = await response.json()
                episode_data["title"] = title_response.get("response", "টাইটেল জেনারেট করতে সমস্যা!")
        return episode_data
    except Exception as e:
        return {"error": f"এআই কনটেন্ট জেনারেশনে ত্রুটি: {str(e)}"}

async def upload_video_to_nekosfast(file_path):
    """ভিডিও ফাইল Nekosfast API-তে আপলোড করুন"""
    try:
        video_params = {"up": ""} # file path will be handled by aiohttp
        async with aiohttp.ClientSession() as session_video_upload:
            with open(file_path, 'rb') as f:
                files = {'video': f}
                async with session_video_upload.post(VIDEO_UPLOAD_ENDPOINT, data=files) as response_video_upload: # Changed to data=files for file upload
                    if response_video_upload.status == 200:
                        video_data = await response_video_upload.json()
                        if video_data.get("success"):
                            hd_link = video_data["links"].get("hd", "লিংক পাওয়া যায়নি")
                            sd_link = video_data["links"].get("sd", "লিংক পাওয়া যায়নি")
                            return {"hd_link": hd_link, "sd_link": sd_link}
                        else:
                            return None
                    else:
                        return None
    except Exception as e:
        print(f"Error uploading video: {e}")
        return None


@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    """/start কমান্ড হ্যান্ডলার"""
    user_id = event.sender_id
    user_data[user_id] = {
        "anime": None,
        "thumbnail_link": None,
        "anime_number": None,
        "season_number": None,
        "episodes": [],
        "awaiting_hd_video": False,
        "awaiting_sd_video": False,
        "current_episode_index": -1 # Track current episode being processed
    }
    await event.reply("অনুগ্রহ করে এনিমের নাম দিন:")

@client.on(events.NewMessage(pattern='/preview'))
async def show_preview_all(event):
    """সকল এপিসোডের প্রিভিউ দেখানো"""
    user_id = event.sender_id
    if user_id not in user_data:
        await event.reply("প্রথমে /start কমান্ড ব্যবহার করুন")
        return

    user_info = user_data[user_id]

    preview_message_all = "🎬 সকল এপিসোডের প্রিভিউ:\n\n"
    for episode_data in user_info["episodes"]:
        preview_message_all += (
            f"📺 এনিমে: {user_info['anime']}\n"
            f"🔢 এপিসোড: {episode_data['episode']}\n"
            f"🎬 টাইটেল: {episode_data['title'] or 'জেনারেট হবে সেন্ড করার পর'}\n"
            f"📝 ডেসক্রিপশন: {episode_data['description'] or 'জেনারেট হবে সেন্ড করার পর'}\n"
            f"🖼️ থামনাইল লিংক: {user_info['thumbnail_link']}\n"
            f"🔗 HD লিংক: {episode_data['hd_link'] or 'প্রসেসিং করার পর পাওয়া যাবে'}\n"
            f"🔗 SD লিংক: {episode_data['sd_link'] or 'প্রসেসিং করার পর পাওয়া যাবে'}\n\n"
            "------------------------\n"
        )
    preview_message_all += "যদি সব তথ্য সঠিক থাকে, /send লিখে ভিডিওগুলো যুক্ত করুন।"
    await event.reply(preview_message_all)


@client.on(events.NewMessage(pattern='/send'))
async def send_data_command(event):
    """ডেটা সেন্ড করার কমান্ড হ্যান্ডলার"""
    await send_data(event)


async def send_data(event):
    """ডেটা সেন্ড করার হ্যান্ডলার"""
    user_id = event.sender_id
    if user_id not in user_data:
        await event.reply("প্রথমে /start কমান্ড ব্যবহার করুন")
        return

    user_info = user_data[user_id]
    episodes_data = user_info["episodes"]

    if not episodes_data:
        await event.reply("কোন এপিসোড তথ্য নেই।")
        return

    await event.reply(f"মোট {len(episodes_data)} এপিসোড প্রসেসিং করা হচ্ছে...")

    all_success_messages = []
    all_error_messages = []

    for index, episode_data in enumerate(user_info["episodes"]):
        success_messages, error_messages = await process_episode_data(event, user_info, episode_data, index) # Pass index
        if success_messages:
            all_success_messages.extend(success_messages)
        if error_messages:
            all_error_messages.extend(error_messages)

    if all_error_messages and not all_success_messages:
        final_response_message = "⚠️ কিছু এপিসোড যুক্ত করতে সমস্যা হয়েছে:\n" + "\n".join(all_error_messages)
        await event.reply(final_response_message)
    elif all_error_messages and all_success_messages:
        final_response_message = "⚠️ কিছু এপিসোড যুক্ত করতে সমস্যা হয়েছে:\n" + "\n".join(all_error_messages)
        await event.reply(final_response_message)
    elif all_success_messages and not all_error_messages:
        pass # Success messages are already sent episode by episode
    elif not all_success_messages and not all_error_messages:
        await event.reply("কোন এপিসোড প্রসেসিং করা হয়নি।")

    del user_data[user_id]


async def process_episode_data(event, user_info, episode_data, episode_index): # Added episode_index
    success_messages = []
    error_messages = []
    try:
        await event.reply(f"এপিসোড {episode_data['episode']} প্রসেসিং করা হচ্ছে...")

        random_id = random.randint(1000, 9999)
        ai_content = await generate_ai_content(user_info["anime"], episode_data["episode"], random_id)

        if "error" in ai_content:
            error_messages.append(f"এপিসোড {episode_data['episode']} AI জেনারেশন ত্রুটি: {ai_content['error']}")
            return None, error_messages

        episode_data["title"] = ai_content["title"]
        episode_data["description"] = ai_content["description"]

        hd_video_path = episode_data.get("hd_video_path")
        sd_video_path = episode_data.get("sd_video_path")

        if hd_video_path and sd_video_path: # Proceed only if both video paths are available
            await event.reply(f"এপিসোড {episode_data['episode']} - এইচডি ভিডিও আপলোড হচ্ছে...")
            hd_video_links = await upload_video_to_nekosfast(hd_video_path)
            await event.reply(f"এপিসোড {episode_data['episode']} - এসডি ভিডিও আপলোড হচ্ছে...")
            sd_video_links = await upload_video_to_nekosfast(sd_video_path)

            if hd_video_links and sd_video_links:
                episode_data["hd_link"] = hd_video_links.get("hd_link")
                episode_data["sd_link"] = sd_video_links.get("sd_link")

                api_url = ADD_EPISODE_API_URL
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
                            await event.reply(response_message)
                        else:
                            error_message = f"❌ এপিসোড {episode_data['episode']} যুক্ত করতে সমস্যা হয়েছে: {api_data.get('message', 'No message')}"
                            error_messages.append(error_message)
                            await event.reply(error_message)
            else:
                error_message = f"❌ এপিসোড {episode_data['episode']} ভিডিও আপলোড করতে সমস্যা হয়েছে।"
                error_messages.append(error_message)
                await event.reply(error_message)
        else:
             error_message = f"❌ এপিসোড {episode_data['episode']} এইচডি ও এসডি ভিডিও পাওয়া যায়নি।";
             error_messages.append(error_message)
             await event.reply(error_message)


        await asyncio.sleep(5)

    except Exception as e:
        error_message = f"এপিসোড {episode_data['episode']} API request error: {str(e)}"
        error_messages.append(error_message)
        await event.reply(error_message)
    finally:
        if episode_data.get("hd_video_path") and os.path.exists(episode_data["hd_video_path"]):
            os.remove(episode_data["hd_video_path"]) # Delete temp HD file
        if episode_data.get("sd_video_path") and os.path.exists(episode_data["sd_video_path"]):
            os.remove(episode_data["sd_video_path"]) # Delete temp SD file
    return success_messages, error_messages


@client.on(events.NewMessage)
async def handle_input(event):
    """ইউজার ইনপুট হ্যান্ডলিং"""
    user_id = event.sender_id
    if user_id not in user_data:
        return # Ignore if user not started

    user_info = user_data[user_id]
    message_text = event.message.text.strip()

    if user_info["anime"] is None:
        user_info["anime"] = message_text
        await event.reply("অনুগ্রহ করে এনিমের থাম্বনেইল লিংক দিন:")
    elif user_info["thumbnail_link"] is None:
        user_info["thumbnail_link"] = message_text
        await event.reply("অনুগ্রহ করে এনিমে নম্বর দিন:")
    elif user_info["anime_number"] is None:
        user_info["anime_number"] = message_text
        await event.reply("অনুগ্রহ করে এনিমে সিজন নম্বর দিন:")
    elif user_info["season_number"] is None:
        user_info["season_number"] = message_text
        user_info["current_episode_index"] += 1 # Increment episode index
        user_info["episodes"].append({
            "episode": None,
            "hd_video_path": None,
            "sd_video_path": None,
            "title": None,
            "description": None,
            "hd_link": None,
            "sd_link": None
        })
        await event.reply("অনুগ্রহ করে প্রথম এপিসোডের নম্বর দিন:")
    elif user_info["episodes"] and user_info["episodes"][user_info["current_episode_index"]]["episode"] is None:
        current_episode_data = user_info["episodes"][user_info["current_episode_index"]]
        current_episode_data["episode"] = message_text
        user_info["awaiting_hd_video"] = True # Awaiting HD video next
        await event.reply("অনুগ্রহ করে এইচডি ভিডিও ফাইল আপলোড করুন:")

@client.on(events.NewMessage(func=lambda e: e.message.media and hasattr(e.message.media, 'document')))
async def handle_video_upload(event):
    """ভিডিও ফাইল আপলোড হ্যান্ডলার"""
    user_id = event.sender_id
    if user_id not in user_data:
        return

    user_info = user_data[user_id]
    current_episode_data = None
    if user_info["episodes"]:
        current_episode_data = user_info["episodes"][user_info["current_episode_index"]]

    if user_info["awaiting_hd_video"] and current_episode_data:
        if event.message.video:
            try:
                hd_temp_file = f"temp_hd_{event.message.id}_{user_id}.mp4"
                await event.download_media(file=hd_temp_file)
                current_episode_data["hd_video_path"] = hd_temp_file
                user_info["awaiting_hd_video"] = False
                user_info["awaiting_sd_video"] = True # Now awaiting SD video
                await event.reply("এইচডি ভিডিও যুক্ত হয়েছে। অনুগ্রহ করে এসডি ভিডিও ফাইল আপলোড করুন:")
            except Exception as e:
                await event.reply(f"এইচডি ভিডিও সেভ করতে সমস্যা: {str(e)}")
                user_info["awaiting_hd_video"] = False # Reset state on error
                user_info["awaiting_sd_video"] = False
        else:
            await event.reply("অনুগ্রহ করে এইচডি ভিডিও ফাইল আপলোড করুন।") # Remind to upload video if not video
    elif user_info["awaiting_sd_video"] and current_episode_data:
        if event.message.video:
            try:
                sd_temp_file = f"temp_sd_{event.message.id}_{user_id}.mp4"
                await event.download_media(file=sd_temp_file)
                current_episode_data["sd_video_path"] = sd_temp_file
                user_info["awaiting_sd_video"] = False
                await event.reply("ভিডিও তথ্য যুক্ত হয়েছে। আপনি কি অন্য এপিসোড যোগ করতে চান? হ্যাঁ অথবা না লিখুন অথবা /preview অথবা /send লিখুন")
            except Exception as e:
                await event.reply(f"এসডি ভিডিও সেভ করতে সমস্যা: {str(e)}")
                user_info["awaiting_sd_video"] = False # Reset state on error
        else:
            await event.reply("অনুগ্রহ করে এসডি ভিডিও ফাইল আপলোড করুন।") # Remind to upload video if not video
    elif event.message.text and user_info["episodes"]:
        current_episode_data = user_info["episodes"][user_info["current_episode_index"]]
        text = event.message.text.strip()
        if text.isdigit():
            user_info["current_episode_index"] += 1 # Increment episode index for new episode
            user_info["episodes"].append({
                "episode": text,
                "hd_video_path": None,
                "sd_video_path": None,
                "title": None,
                "description": None,
                "hd_link": None,
                "sd_link": None
            })
            user_info["awaiting_hd_video"] = True # Awaiting HD video for new episode
            await event.reply("অনুগ্রহ করে এইচডি ভিডিও ফাইল আপলোড করুন:")

        elif text.lower() == '/send':
             await send_data_command(event) # call send data when user types /send
        elif text.lower() == '/preview':
            await show_preview_all(event)
        else:
            await event.reply("ইনপুট প্রসেসিং এ সমস্যা। /start দিয়ে আবার শুরু করুন অথবা এপিসোড নম্বর লিখুন।")


# বট চালান
print("Bot is running...")
client.run_until_disconnected()
