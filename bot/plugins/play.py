import os, asyncio, pafy
import re
import sys
import time
import ffmpeg
import subprocess
from asyncio import sleep
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pytgcalls import GroupCallFactory
from bot import video_link_getter, yt_video_search, match_url
from bot import vcusr
from bot.helpers.decorators import authorized_users_only
from youtube_search import YoutubeSearch
from bot.config import AUDIO_CALL, VIDEO_CALL


LOG_GROUP_ID = -1001576388235


STREAM = {8}
GROUP_CALLS = {}

@vcusr.on_message(filters.command(["pause", f"pause@{USERNAME}"]) & filters.group & ~filters.edited)
@authorized_users_only
async def pause(_, m: Message):
    chat_id = m.chat.id

    if chat_id in AUDIO_CALL:
        await AUDIO_CALL[chat_id].set_audio_pause(True)
        await m.reply_text("⏸ **Paused Audio Streaming !**")

    elif chat_id in VIDEO_CALL:
        await VIDEO_CALL[chat_id].set_video_pause(True)
        await m.reply_text("⏸ **Paused Video Streaming !**")

    else:
        await m.reply_text("❌ **Noting Is Streaming !**")


@vcusr.on_message(filters.command(["resume", f"resume@{USERNAME}"]) & filters.group & ~filters.edited)
@authorized_users_only
async def resume(_, m: Message):
    chat_id = m.chat.id

    if chat_id in AUDIO_CALL:
        await AUDIO_CALL[chat_id].set_audio_pause(False)
        await m.reply_text("▶️ **Resumed Audio Streaming !**")

    elif chat_id in VIDEO_CALL:
        await VIDEO_CALL[chat_id].set_video_pause(False)
        await m.reply_text("▶️ **Resumed Video Streaming !**")

    else:
        await m.reply_text("❌ **Noting Is Streaming !**")


@vcusr.on_message(filters.command(["endstream", f"endstream@{USERNAME}"]) & filters.group & ~filters.edited)
@authorized_users_only
async def endstream(client, m: Message):
    msg = await m.reply_text("🔄 `Processing ...`")
    chat_id = m.chat.id

    if chat_id in AUDIO_CALL:
        await AUDIO_CALL[chat_id].stop()
        AUDIO_CALL.pop(chat_id)
        await msg.edit("⏹️ **Stopped Audio Streaming !**")

    elif chat_id in VIDEO_CALL:
        await VIDEO_CALL[chat_id].stop()
        VIDEO_CALL.pop(chat_id)
        await msg.edit("⏹️ **Stopped Video Streaming !**")

    else:
        await msg.edit("🤖 **Please Start An Stream First !**")


@vcusr.on_message(filters.command("help", "!"))
async def help_vc(client, message):
    text = '''====== **Djxkaykay Help Menu** ======
**Play as Audio**
- !pvc __(reply to audio / youtube url / search query)__
- !radio __(radio stream url)__
**Play as Video**
- !svc __(reply to video / youtube url / search query)__ 💗
- !live __(youtube live stream url)__
**Extra**
- !lvc: Leave from vc
- !video: Download url or search query in video format
- !audio: Download url or search query in audio format
- !skip : Skip streaming file😹'''
    await message.reply(text)

@vcusr.on_message(filters.command("lvc", "!"))
@authorized_users_only
async def leave_vc(client, message):
    CHAT_ID = message.chat.id
    if not str(CHAT_ID).startswith("-100"): return
    group_call = GROUP_CALLS.get(CHAT_ID)
    if group_call:
        await group_call.stop()
        await message.reply_text(f"✅ **Streaming Stopped & Left The Video Chat !**")

@vcusr.on_message(filters.command("live", "!"))
async def live_vc(client, message):
    CHAT_ID = message.chat.id
    if not str(CHAT_ID).startswith("-100"): return
    msg = await message.reply("⏳ __Please wait.__")
    media = message.reply_to_message
    try: INPUT_SOURCE = message.text.split(" ", 1)[1]
    except IndexError: return await msg.edit("🔎 __Give me a URL__")
    if match_url(INPUT_SOURCE, key="yt") is None:
        return await msg.edit("🔎 __Give me a valid URL__")
    #ytlink = await run_cmd(f"youtube-dl -g {INPUT_SOURCE}")
    videof = pafy.new(INPUT_SOURCE)
    ytlink = videof.getbest().url
    if match_url(ytlink) is None:
        return await msg.edit(f"`{ytlink}`")
    try:
        group_call = GROUP_CALLS.get(CHAT_ID)
        if group_call is None:
            group_call = GroupCallFactory(vcusr, outgoing_audio_bitrate_kbit=512).get_group_call()
            GROUP_CALLS[CHAT_ID] = group_call
        if group_call.is_connected:
            await group_call.stop()
            await asyncio.sleep(3)
        await group_call.join(CHAT_ID)
        await msg.delete()
        await msg.reply_photo("https://telegra.ph/file/62e86d8aadde9a8cbf9c2.jpg",
        caption="streaming live from youtube🎬")
        await group_call.start_video(ytlink, repeat=False, enable_experimental_lip_sync=True)
    except Exception as e:
        await message.reply(str(e))
        return await group_call.stop()

@vcusr.on_message(filters.command("radio", "!"))
async def radio_vc(client, message):
    CHAT_ID = message.chat.id
    if not str(CHAT_ID).startswith("-100"): return
    msg = await message.reply("⏳ __Please wait.__")
    media = message.reply_to_message
    try: INPUT_SOURCE = message.text.split(" ", 1)[1]
    except IndexError: return await msg.edit("🔎 __All radio stations listed [here](https://github.com/AnjanaMadu/radio_stations). Please get link from [here](https://github.com/AnjanaMadu/radio_stations)__", disable_web_page_preview=True)
    if match_url(INPUT_SOURCE) is None:
        return await msg.edit("🔎 __Give me a valid URL__")
    
    try:
        
        group_call = GROUP_CALLS.get(CHAT_ID)
        if group_call is None:
            group_call = GroupCallFactory(vcusr, outgoing_audio_bitrate_kbit=512).get_group_call()
            GROUP_CALLS[CHAT_ID] = group_call
        if group_call.is_connected:
            await group_call.stop()
            await asyncio.sleep(3)
        await group_call.join(CHAT_ID)
        await msg.delete()
        await msg.reply_photo("https://telegra.ph/file/62e86d8aadde9a8cbf9c2.jpg",
        caption="streaming radio🎬")
        await group_call.start_audio(INPUT_SOURCE, repeat=False)
    except Exception as e:
        await message.reply(str(e))
        return await group_call.stop()
    
@Client.on_message(filters.command("pvc", "!"))
@authorized_users_only
async def play_vc(client, message):
    global vc_live
    if not message.chat.id == CHAT_ID: return
    msg = await message.reply("⏳ __Please wait.__")
    if vc_live == True:
        return await msg.edit("💬 __Live or Radio Ongoing. Please stop it via `!endvc`.__")
    media = message.reply_to_message
    THUMB_URL, VIDEO_TITLE, VIDEO_DURATION = "https://telegra.ph/file/62e86d8aadde9a8cbf9c2.jpg", "Music", "Not Found"
    if media and media.media:
        await msg.edit("📥 __Downloading...__")
        LOCAL_FILE = await client.download_media(media)
    else:
        try: INPUT_SOURCE = message.text.split(" ", 1)[1]
        except IndexError: return await msg.edit("🔎 __Give me a URL or Search Query. Look__ `!help`")
        if ("youtube.com" in INPUT_SOURCE) or ("youtu.be" in INPUT_SOURCE):
            FINAL_URL = INPUT_SOURCE
        else:
            FINAL_URL = yt_video_search(INPUT_SOURCE)
            if FINAL_URL == 404:
                return await msg.edit("__No videos found__ 🤷‍♂️")
        await msg.edit("📥 __Downloading...__")
        LOCAL_FILE, THUMB_URL, VIDEO_TITLE, VIDEO_DURATION = video_info_extract(FINAL_URL, key="audio")
        if LOCAL_FILE == 500: return await msg.edit("__Download Error.__ 🤷‍♂️ report this to @KayAspirerProject")
         
    try:
        post_data = {'LOCAL_FILE':LOCAL_FILE, 'THUMB_URL':THUMB_URL, 'VIDEO_TITLE':VIDEO_TITLE, 'VIDEO_DURATION':VIDEO_DURATION, 'TYPE':'audio'}
        resp = await play_or_queue("add", post_data)
        if resp['status'] == 'queue':
            await msg.edit(resp['msg'])
        elif resp['status'] == 'play':
            await msg.delete()
            await message.reply_photo(resp['thumb'], caption=resp['msg'])
    except Exception as e:
        await message.reply(str(e))
        return await group_call.stop()
        
    
    
@vcusr.on_message(filters.command("skip", "!"))
async def skip_vc(client, message):
    if len(music_queue) == 0: return
    if group_call.is_video_running:
        await group_call.stop_media()
    elif group_call.is_audio_running:
        await group_call.stop_media()
    elif group_call.is_running:
        await group_call.stop_media()
        
    os.remove(music_queue[0]['source'])
    music_queue.pop(0)
    status = await play_or_queue(None, "check", None)
    os.system(f'echo {status}')

@vcusr.on_callback_query(filters.regex("resume_callback"))
async def resume_callbacc(client, CallbackQuery):
    CHAT_ID = CallbackQuery.message.chat.id
    if CHAT_ID in AUDIO_CALL:
        text = f"▶️ Resumed !"
        await AUDIO_CALL[chat_id].set_audio_pause(False)
    elif CHAT_ID in VIDEO_CALL:
        text = f"▶️ Resumed !"
        await VIDEO_CALL[CHAT_ID].set_video_pause(False)
    else:
        text = f"❌ Nothing is Playing !"
    await Client.answer_callback_query(
        CallbackQuery.id, text, show_alert=True
    )    
   

@vcusr.on_callback_query(filters.regex("pause_callback"))
async def pause_callbacc(client, CallbackQuery):
    chat_id = CallbackQuery.message.chat.id
    if chat_id in AUDIO_CALL:
        text = f"⏸ Paused !"
        await AUDIO_CALL[chat_id].set_audio_pause(True)
    elif chat_id in VIDEO_CALL:
        text = f"⏸ Paused !"
        await VIDEO_CALL[chat_id].set_video_pause(True)
    else:
        text = f"❌ Nothing is Playing !"
    await Client.answer_callback_query(
        CallbackQuery.id, text, show_alert=True
    )


@vcusr.on_callback_query(filters.regex("end_callback"))
async def end_callbacc(client, CallbackQuery):
    CHAT_ID = CallbackQuery.message.chat.id
    if CHAT_ID in AUDIO_CALL:
        text = f"⏹️ Stopped !"
        await AUDIO_CALL[CHAT_ID].stop()
        AUDIO_CALL.pop(CHAT_ID)
    elif CHAT_ID in VIDEO_CALL:
        text = f"⏹️ Stopped !"
        await VIDEO_CALL[CHAT_ID].stop()
        VIDEO_CALL.pop(CHAT_ID)
    else:
        text = f"❌ Nothing is Playing !"
    await Client.answer_callback_query(
        CallbackQuery.id, text, show_alert=True
    )
    await Client.send_message(
        CHAT_ID=CallbackQuery.message.chat.id,
        text=f"✅ **Streaming Stopped & Left The Video Chat !**"
    )
    await CallbackQuery.message.delete()
    
    
    
@vcusr.on_message(filters.command("svc", "!"))
async def stream_vc(client, message):
    CHAT_ID = message.chat.id
    if not str(CHAT_ID).startswith("-100"): return
    msg = await message.reply("⏳ __Please wait.__")
    media = message.reply_to_message
    if media:
        await msg.edit("📥 __Downloading...__")
        LOCAL_FILE = await client.download_media(media)
    else:
        try: INPUT_SOURCE = message.text.split(" ", 1)[1]
        except IndexError: return await msg.edit("🔎 __Give me a URL or Search Query. Look__ ` for !help`")
        if ("youtube.com" in INPUT_SOURCE) or ("youtu.be" in INPUT_SOURCE):
            FINAL_URL = INPUT_SOURCE
        else:
            FINAL_URL = yt_video_search(INPUT_SOURCE)
            if FINAL_URL == 404:
                return await msg.edit("__No videos found__ 🤷‍♂️")
        await msg.edit("📥 __Downloading...__")
        LOCAL_FILE = video_link_getter(FINAL_URL, key="v")
        if LOCAL_FILE == 500: return await msg.edit("__Download Error.__ 🤷‍♂️ report this to @KayAspirerProject")
         
    try:
        group_call = GROUP_CALLS.get(CHAT_ID)
        if group_call is None:
            group_call = GroupCallFactory(vcusr, outgoing_audio_bitrate_kbit=512).get_group_call()
            GROUP_CALLS[CHAT_ID] = group_call
        if group_call.is_connected:
            await group_call.stop()
            await asyncio.sleep(3)
        await group_call.join(CHAT_ID)
        await msg.delete()
        emojilist = [
                "1️⃣",
                "2️⃣",
                "3️⃣",
                "4️⃣",
                "5️⃣",
            ]
        
        results = YoutubeSearch
        
#this is fucking boring          
                
        await msg.reply_photo("https://telegra.ph/file/62e86d8aadde9a8cbf9c2.jpg",
        caption=f"streaming {results} via youtube **djkaykay**",
        reply_markup=InlineKeyboardMarkup(
               [
                   [
                       InlineKeyboardButton(
                          text="⏸",
                          callback_data="pause_callback",
                       ),
                       InlineKeyboardButton(
                          text="▶️",
                          callback_data="resume_callback",
                       ),
                       InlineKeyboardButton(
                          text="⏹️",
                          callback_data="end_callback",
                       ),
                   ],
               ]),
            )                    
                              
        await group_call.start_video(LOCAL_FILE, repeat=False, enable_experimental_lip_sync=True)
    except Exception as e:
        await message.reply(str(e))
        return await group_call.stop()
    
@group_call.on_audio_playout_ended
async def audio_ended_handler(_, __):
    await sleep(3)
    await group_call.stop()
    print(f"[INFO] - AUDIO_CALL ENDED !")

@group_call.on_video_playout_ended
async def video_ended_handler(_, __):
    await sleep(3)
    await group_call.stop()
    print(f"[INFO] - VIDEO_CALL ENDED !")
