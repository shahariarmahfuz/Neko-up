import os
import asyncio
import random
import aiohttp
from telethon import TelegramClient, events
from dotenv import load_dotenv

# .env ফাইল থেকে ভেরিয়েবল লোড করুন
load_dotenv()

# টেলিগ্রাম API কনফিগারেশন
API_ID = "20716719"
API_HASH = "c929824683800816ddf0faac845d89c9"
BOT_TOKEN = "7867830008:AAE9ljH11pHuGVRA9XcwGYhoTYVnEP5cvHE"

# ফ্লাস্ক API এন্ডপয়েন্ট
API_ENDPOINT = "https://molecular-angel-itachivai-e6c91c4d.koyeb.app/up"

# ইউজারের তথ্য সংরক্ষণের জন্য ডিকশনারি
user_data = {}

# ক্লায়েন্ট তৈরি করুন
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

async def upload_video_to_api(file_path):
    """ভিডিও ফাইল ফ্লাস্ক API-তে আপলোড করুন"""
    try:
        with open(file_path, 'rb') as f:
            files = {'video': f}
            response = requests.post(API_ENDPOINT, files=files)
        
        if response.status_code == 202:
            return response.json()  # প্রসেসিং ডেটা রিটার্ন করুন
        else:
            return None
    except Exception as e:
        print(f"Error uploading video: {e}")
        return None

async def check_processing_status(process_id):
    """প্রসেসিং স্ট্যাটাস চেক করুন"""
    try:
        check_url = f"{API_ENDPOINT.rsplit('/',1)[0]}/check_status/{process_id}"
        response = requests.get(check_url, headers={'Accept': 'application/json'})
        
        if response.status_code == 200:
            return response.json()  # স্ট্যাটাস ডেটা রিটার্ন করুন
        else:
            return None
    except Exception as e:
        print(f"Error checking status: {e}")
        return None

async def generate_ai_content(anime, episode, random_id):
    """এআই কনটেন্ট জেনারেট করুন"""
    try:
        async with aiohttp.ClientSession() as session:
            # ডেসক্রিপশন জেনারেট
            desc_params = {
                "q": f"Write a description for episode number {episode} of {anime}. 20-25 words. Only description.",
                "id": random_id
            }
            async with session.get("https://new-ai-buxr.onrender.com/ai", params=desc_params) as response:
                desc_response = await response.json()
                description = desc_response.get("response", "ডেসক্রিপশন জেনারেট করতে সমস্যা!")

            # টাইটেল জেনারেট
            title_params = {
                "q": f"Write the title of episode number {episode} of {anime}. Only title and No additional symbols or text may be written. There's no need to bold the text, just give it normally.",
                "id": random_id
            }
            async with session.get("https://new-ai-buxr.onrender.com/ai", params=title_params) as response:
                title_response = await response.json()
                title = title_response.get("response", "টাইটেল জেনারেট করতে সমস্যা!")
        
        return {"title": title, "description": description}
    except Exception as e:
        return {"error": f"এআই কনটেন্ট জেনারেশনে ত্রুটি: {str(e)}"}

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    """/start কমান্ড হ্যান্ডলার"""
    user_id = event.sender_id
    user_data[user_id] = {
        "anime": None,
        "thumbnail_link": None,
        "anime_number": None,
        "season_number": None,
        "episodes": []  # এপিসোডের ডেটা লিস্ট
    }
    await event.reply("অনুগ্রহ করে এনিমের নাম দিন:")

@client.on(events.NewMessage)
async def handle_input(event):
    """ইউজার ইনপুট হ্যান্ডলিং"""
    user_id = event.sender_id
    if user_id not in user_data:
        await event.reply("প্রথমে /start কমান্ড ব্যবহার করুন")
        return

    user_info = user_data[user_id]
    text = event.message.text.strip()

    if user_info["anime"] is None:
        user_info["anime"] = text
        await event.reply("অনুগ্রহ করে এনিমের থাম্বনেইল লিংক দিন:")
    elif user_info["thumbnail_link"] is None:
        user_info["thumbnail_link"] = text
        await event.reply("অনুগ্রহ করে এনিমে নম্বর দিন:")
    elif user_info["anime_number"] is None:
        user_info["anime_number"] = text
        await event.reply("অনুগ্রহ করে এনিমে সিজন নম্বর দিন:")
    elif user_info["season_number"] is None:
        user_info["season_number"] = text
        user_info["episodes"].append({
            "episode": None,
            "hd_link": None,
            "sd_link": None,
            "title": None,
            "description": None
        })
        await event.reply("অনুগ্রহ করে প্রথম এপিসোডের নম্বর দিন:")
    elif not user_info["episodes"]:
        pass
    else:
        current_episode_data = user_info["episodes"][-1]

        if current_episode_data["episode"] is None:
            current_episode_data["episode"] = text
            await event.reply("অনুগ্রহ করে HD ভিডিও লিংক দিন:")
        elif current_episode_data["hd_link"] is None:
            current_episode_data["hd_link"] = text
            await event.reply("অনুগ্রহ করে SD ভিডিও লিংক দিন:")
        elif current_episode_data["sd_link"] is None:
            current_episode_data["sd_link"] = text
            await event.reply("ভিডিও তথ্য যুক্ত হয়েছে। আপনি কি অন্য এপিসোড যোগ করতে চান? হ্যাঁ অথবা না লিখুন")
        elif text.lower() == '/send':
            asyncio.create_task(send_data(event))  # Create a new task for each user's send_data request
        else:
            await event.reply("ইনপুট প্রসেসিং এ সমস্যা। /start দিয়ে আবার শুরু করুন অথবা এপিসোড নম্বর লিখুন।")

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

    # Process episodes sequentially for each user
    for episode_data in user_info["episodes"]:
        await process_episode_data(event, user_info, episode_data)

    del user_data[user_id]  # ইউজার ডেটা ডিলিট করে দিন

async def process_episode_data(event, user_info, episode_data):
    """এপিসোড ডেটা প্রসেস করুন"""
    try:
        await event.reply(f"এপিসোড {episode_data['episode']} প্রসেসিং করা হচ্ছে...")

        random_id = random.randint(1000, 9999)
        ai_content = await generate_ai_content(user_info["anime"], episode_data["episode"], random_id)

        if "error" in ai_content:
            await event.reply(f"এপিসোড {episode_data['episode']} AI জেনারেশন ত্রুটি: {ai_content['error']}")
            return

        episode_data["title"] = ai_content["title"]
        episode_data["description"] = ai_content["description"]

        # HD এবং SD ভিডিও আপলোড করুন
        hd_link = await upload_video_to_api(episode_data["hd_link"])
        sd_link = await upload_video_to_api(episode_data["sd_link"])

        if hd_link is None or sd_link is None:
            await event.reply(f"এপিসোড {episode_data['episode']} ভিডিও আপলোড করতে সমস্যা হয়েছে।")
            return

        api_url = "https://nekofilx.onrender.com/ad"
        params = {
            "a": user_info["anime_number"],
            "s": user_info["season_number"],
            "t": episode_data["title"],
            "720p": hd_link,
            "480p": sd_link,
            "th": user_info["thumbnail_link"],
            "d": episode_data["description"],
            "eps": episode_data["episode"]
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params) as response:
                api_data = await response.json()
                if api_data.get("status") == "success":
                    await event.reply(f"✅ এপিসোড {episode_data['episode']} যুক্ত করা হয়েছে!\n\n"
                                    f"🎬 এনিমে আইডি: {api_data['anime_id']}\n"
                                    f"🔢 সিজন: {api_data['season']}\n"
                                    f"📝 মেসেজ: {api_data['message']}")
                else:
                    await event.reply(f"❌ এপিসোড {episode_data['episode']} যুক্ত করতে সমস্যা হয়েছে: {api_data.get('message', 'No message')}")

    except Exception as e:
        await event.reply(f"এপিসোড {episode_data['episode']} প্রসেসিং এ ত্রুটি: {str(e)}")

# বট চালান
print("বট চালু হয়েছে...")
client.run_until_disconnected()
