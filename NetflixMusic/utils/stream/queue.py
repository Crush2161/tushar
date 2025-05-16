import asyncio
from typing import Union

from NetflixMusic.misc import db
from NetflixMusic.utils.formatters import check_duration, seconds_to_min
from config import autoclean, time_to_seconds


async def put_queue(
    chat_id,
    original_chat_id,
    file,
    title,
    duration,
    user,
    vidid,
    user_id,
    stream,
    forceplay: Union[bool, str] = None,
):
    duration_in_seconds = 0
    try:
        title = str(title).title()
        if duration and isinstance(duration, str):
            try:
                duration_in_seconds = time_to_seconds(duration) - 3
            except:
                duration_in_seconds = 0
    except:
        title = str(title)
        duration_in_seconds = 0

    put = {
        "title": title,
        "dur": duration,
        "streamtype": stream,
        "by": user,
        "user_id": user_id,
        "chat_id": original_chat_id,
        "file": file,
        "vidid": vidid,
        "seconds": duration_in_seconds,
        "played": 0,
    }
    
    try:
        if forceplay:
            check = db.get(chat_id, [])
            if check:
                check.insert(0, put)
            else:
                db[chat_id] = []
                db[chat_id].append(put)
        else:
            if chat_id not in db:
                db[chat_id] = []
            db[chat_id].append(put)
    except (TypeError, KeyError):
        db[chat_id] = []
        db[chat_id].append(put)
    autoclean.append(file)


async def put_queue_index(
    chat_id,
    original_chat_id,
    file,
    title,
    duration,
    user,
    vidid,
    stream,
    forceplay: Union[bool, str] = None,
):
    dur = 0
    try:
        if isinstance(vidid, str) and (vidid.startswith("http://") or vidid.startswith("https://")):
            dur = await asyncio.get_event_loop().run_in_executor(
                None, check_duration, vidid
            )
            if dur != "Unknown":
                duration = seconds_to_min(dur)
            else:
                duration = "ᴜʀʟ sᴛʀᴇᴀᴍ"
    except:
        duration = "ᴜʀʟ sᴛʀᴇᴀᴍ"
    put = {
        "title": title,
        "dur": duration,
        "streamtype": stream,
        "by": user,
        "chat_id": original_chat_id,
        "file": file,
        "vidid": vidid,
        "seconds": dur,
        "played": 0,
    }
    try:
        if forceplay:
            check = db.get(chat_id, [])
            if check:
                check.insert(0, put)
            else:
                db[chat_id] = []
                db[chat_id].append(put)
        else:
            if chat_id not in db:
                db[chat_id] = []
            db[chat_id].append(put)
    except (TypeError, KeyError):
        db[chat_id] = []
        db[chat_id].append(put)
