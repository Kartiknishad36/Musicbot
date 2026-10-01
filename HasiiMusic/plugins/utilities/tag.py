# ============================================================================== 
# tag.py - Premium Tag System (Full Detail)
# ============================================================================== 
# Complete tagging toolkit for groups:
#   /tagall  or /all     - Tag every member one-by-one with optional custom text
#   /tag <text>          - Same as tagall with custom message
#   /tagspam             - Rapid spam-style tagging (short delay)
#   /tagbomb             - Bomb mode (very fast, short messages)
#   /taggaali            - Random mild roast / gaali style tags
#   /tagstop  /tagcancel - Stop any running tag process instantly
#   /tagresume           - Resume if paused (future-ready)
#
# Features:
#   - Admin / Sudo only
#   - Progress percentage + ETA style status messages
#   - Automatic skip of bots & deleted accounts
#   - FloodWait safe with exponential backoff
#   - Colorful premium buttons to stop / cancel mid-process
#   - Per-chat running task tracking (no overlap)
#   - Detailed logging of every step
# ============================================================================== 

import asyncio
import random
import time
from typing import Dict, List, Optional, Set

from pyrogram import enums, filters, types
from pyrogram.errors import (
    ChatWriteForbidden,
    FloodWait,
    PeerIdInvalid,
    UserBannedInChannel,
    UserDeactivated,
    UserIsBlocked,
    UserNotParticipant,
)

from HasiiMusic import app, config, db
from HasiiMusic.helpers import buttons
from HasiiMusic.helpers._admins import admin_check

# Global tracker: chat_id -> asyncio.Task
_running_tags: Dict[int, asyncio.Task] = {}
# Cancel flags: chat_id -> bool
_cancel_flags: Dict[int, bool] = {}
# Pause flags (for future resume)
_pause_flags: Dict[int, bool] = {}

# Mild gaali / roast list (Hindi + English mix, keep it fun not toxic)
GAALI_LIST = [
    "👊 अबे क्या बात कर रहा है", 
    "😂 और भाई क्या कर रहा है तुझे", 
    "🤣 चुप रहा तू थोड़ा सा चिल्ल हो", 
    "💀 झूठ मत क्यों ब्रो", 
    "👎 बेकार हो गया", 
    "🤪 पागल है क्या हालत", 
    "🐸 मच्छर कुछ भी नहीं", 
    "🤡 और बहुत मजाक है", 
    "🐝 भीड़ बना रहा है क्या", 
    "🤯 दिमाग हो गया तुम", 
    "🙄 कुछ नहीं बनता क्या", 
    "🥴 थोड़ा सा काम कर", 
    "😅 बस तेरा कर रहा", 
    "🤦‍♂️ अब क्या करेगा", 
    "👊👊 जलदी से बाहर निकल", 
]

# Decorative prefixes for normal tags
PREFIXES = [
    "🌹", "🌺", "🌸", "✨", "💕", "💖", 
    "🌟", "💫", "🎀", "🎁", "🎉", "🎊",
]


def _is_cancelled(chat_id: int) -> bool:
    return _cancel_flags.get(chat_id, False)


def _is_paused(chat_id: int) -> bool:
    return _pause_flags.get(chat_id, False)


async def _safe_sleep(seconds: float, chat_id: int):
    """Sleep but wake early if cancelled."""
    end = time.time() + seconds
    while time.time() < end:
        if _is_cancelled(chat_id):
            return
        await asyncio.sleep(0.25)


async def _get_members(chat_id: int) -> List[types.User]:
    """Collect all non-bot, non-deleted members. Detailed logging."""
    members: List[types.User] = []
    try:
        async for member in app.get_chat_members(chat_id):
            user = member.user
            if user is None:
                continue
            if user.is_bot:
                continue
            if user.is_deleted:
                continue
            members.append(user)
    except Exception as e:
        app.logger.warning(f"[TAG] Failed to fetch members in {chat_id}: {e}")
    return members


async def _send_tag(
    chat_id: int,
    user: types.User,
    text: str,
    mode: str = "normal",
) -> bool:
    """Send one tag message. Returns True on success."""
    mention = user.mention if user.username is None else f"@{user.username}"
    if not mention or mention == "":
        mention = f"<a href='tg://user?id={user.id}'>{user.first_name or 'User'}</a>"

    if mode == "gaali":
        body = random.choice(GAALI_LIST)
        final = f"{random.choice(PREFIXES)} {mention} {body}"
    elif mode == "bomb":
        final = f"💣 {mention}"
    elif mode == "spam":
        final = f"{random.choice(PREFIXES)} {mention} {text}"
    else:
        final = f"{random.choice(PREFIXES)} {mention} {text}"

    try:
        await app.send_message(chat_id, final)
        return True
    except FloodWait as e:
        app.logger.info(f"[TAG] FloodWait {e.value}s in {chat_id}")
        await asyncio.sleep(e.value + 1)
        try:
            await app.send_message(chat_id, final)
            return True
        except Exception:
            return False
    except (UserIsBlocked, UserDeactivated, PeerIdInvalid, UserNotParticipant, UserBannedInChannel):
        return False
    except ChatWriteForbidden:
        return False
    except Exception as e:
        app.logger.debug(f"[TAG] send error: {e}")
        return False


async def _run_tag_process(
    chat_id: int,
    initiator_id: int,
    custom_text: str,
    mode: str = "normal",
    delay: float = 1.8,
):
    """Core tagging loop with full progress, cancel support and detailed status."""
    start_ts = time.time()
    members = await _get_members(chat_id)
    total = len(members)

    if total == 0:
        await app.send_message(chat_id, "❌ कोई मेम्बर नहीं मिला।")
        return

    status_msg = await app.send_message(
        chat_id,
        f"🌹 <b>ᴛᴀɴᴜ ᴍᴜꜱɪᴄ ᴛᴀɢ ᴛᴀꜱᴋ ꜱᴛᴀʀᴛᴇᴅ</b> 🌹\n\n"
        f"📊 Total members: <b>{total}</b>\n"
        f"🎯 Mode: <b>{mode.upper()}</b>\n"
        f"⏳ Delay: <b>{delay}s</b>\n\n"
        f"🚀 Starting now... Use buttons below to stop anytime.",
        reply_markup=buttons.tag_markup(chat_id),
    )

    success = 0
    failed = 0
    skipped = 0

    for idx, user in enumerate(members, 1):
        if _is_cancelled(chat_id):
            break

        # Pause support
        while _is_paused(chat_id) and not _is_cancelled(chat_id):
            await asyncio.sleep(0.5)

        if _is_cancelled(chat_id):
            break

        ok = await _send_tag(chat_id, user, custom_text, mode)
        if ok:
            success += 1
        else:
            failed += 1

        # Update status every 8 tags or at the end
        if idx % 8 == 0 or idx == total:
            percent = round((idx / total) * 100, 1)
            elapsed = time.time() - start_ts
            eta = ((elapsed / idx) * (total - idx)) if idx else 0
            try:
                await status_msg.edit_text(
                    f"🌹 <b>ᴛᴀɴᴜ ᴍᴜꜱɪᴄ ᴛᴀɢ ᴘʀᴏɢʀᴇꜱꜱ</b> 🌹\n\n"
                    f"📈 Progress: <b>{idx}/{total}</b> ({percent}%)\n"
                    f"✅ Success: <b>{success}</b>\n"
                    f"❌ Failed: <b>{failed}</b>\n"
                    f"⏱️ Elapsed: <b>{int(elapsed)}s</b> | ETA: <b>{int(eta)}s</b>\n\n"
                    f"Mode: <code>{mode}</code>",
                    reply_markup=buttons.tag_markup(chat_id),
                )
            except Exception:
                pass

        await _safe_sleep(delay, chat_id)

    # Final summary
    elapsed = time.time() - start_ts
    cancelled = _is_cancelled(chat_id)
    summary = (
        f"🌹 <b>ᴛᴀɴᴜ ᴍᴜꜱɪᴄ ᴛᴀɢ ᴄᴏᴍᴘʟᴇᴛᴇᴅ</b> 🌹\n\n"
        f"{'⛔ Cancelled by admin' if cancelled else '✅ Finished successfully'}\n\n"
        f"📊 Total processed: <b>{success + failed}</b> / {total}\n"
        f"✅ Tagged: <b>{success}</b>\n"
        f"❌ Failed/Skipped: <b>{failed}</b>\n"
        f"⏱️ Time taken: <b>{int(elapsed)}s</b>\n"
        f"🎯 Mode: <code>{mode.upper()}</code>"
    )
    try:
        await status_msg.edit_text(summary)
    except Exception:
        await app.send_message(chat_id, summary)

    # Cleanup
    _running_tags.pop(chat_id, None)
    _cancel_flags.pop(chat_id, None)
    _pause_flags.pop(chat_id, None)


def _start_tag_task(chat_id: int, initiator_id: int, text: str, mode: str, delay: float):
    """Create and store the background task."""
    if chat_id in _running_tags and not _running_tags[chat_id].done():
        return False  # already running

    _cancel_flags[chat_id] = False
    _pause_flags[chat_id] = False
    task = asyncio.create_task(
        _run_tag_process(chat_id, initiator_id, text, mode, delay)
    )
    _running_tags[chat_id] = task
    return True


# --------------------------------------------------------------------------
# COMMANDS
# --------------------------------------------------------------------------

@app.on_message(filters.command(["tagall", "all", "tag"]) & filters.group & ~app.bl_users)
@admin_check
@lang.language()
async def tagall_cmd(_, message: types.Message):
    """ /tagall | /all | /tag [optional text] """
    try:
        await message.delete()
    except Exception:
        pass

    chat_id = message.chat.id
    if chat_id in _running_tags and not _running_tags[chat_id].done():
        return await message.reply_text(
            "⚠️ एक ᴛᴀɢ प्रोसेस पहले से चल रहा है।\n"
            "रुको /tagstop या /tagcancel से बंद करो।",
            reply_markup=buttons.tag_markup(chat_id),
        )

    # Extract custom text
    text = message.text.split(None, 1)[1] if len(message.command) > 1 else "🌹 ᴛᴀɴᴜ ᴍᴜꜱɪᴄ की ओर से टैग!"

    started = _start_tag_task(chat_id, message.from_user.id, text, "normal", 1.8)
    if not started:
        await message.reply_text("⚠️ पहले से चल रहा है। /tagstop करो।")


@app.on_message(filters.command(["tagspam"]) & filters.group & ~app.bl_users)
@admin_check
@lang.language()
async def tagspam_cmd(_, message: types.Message):
    """Fast spam-style tagging."""
    try:
        await message.delete()
    except Exception:
        pass

    chat_id = message.chat.id
    if chat_id in _running_tags and not _running_tags[chat_id].done():
        return await message.reply_text("⚠️ Already running. /tagstop first.")

    text = message.text.split(None, 1)[1] if len(message.command) > 1 else "💥 SPAM TAG!"
    _start_tag_task(chat_id, message.from_user.id, text, "spam", 0.9)


@app.on_message(filters.command(["tagbomb", "bomb"]) & filters.group & ~app.bl_users)
@admin_check
@lang.language()
async def tagbomb_cmd(_, message: types.Message):
    """Ultra-fast bomb tagging (short messages)."""
    try:
        await message.delete()
    except Exception:
        pass

    chat_id = message.chat.id
    if chat_id in _running_tags and not _running_tags[chat_id].done():
        return await message.reply_text("⚠️ Already running. /tagstop first.")

    _start_tag_task(chat_id, message.from_user.id, "", "bomb", 0.45)


@app.on_message(filters.command(["taggaali", "gaali"]) & filters.group & ~app.bl_users)
@admin_check
@lang.language()
async def taggaali_cmd(_, message: types.Message):
    """Random mild roast / gaali style tagging."""
    try:
        await message.delete()
    except Exception:
        pass

    chat_id = message.chat.id
    if chat_id in _running_tags and not _running_tags[chat_id].done():
        return await message.reply_text("⚠️ Already running. /tagstop first.")

    _start_tag_task(chat_id, message.from_user.id, "", "gaali", 1.5)


@app.on_message(filters.command(["tagstop", "tagcancel", "stoptag", "canceltag"]) & filters.group & ~app.bl_users)
@admin_check
@lang.language()
async def tagstop_cmd(_, message: types.Message):
    """Immediately cancel any running tag process."""
    try:
        await message.delete()
    except Exception:
        pass

    chat_id = message.chat.id
    if chat_id not in _running_tags or _running_tags[chat_id].done():
        return await message.reply_text("ℹ️ कोई ᴛᴀɢ प्रोसेस चल नहीं रहा।")

    _cancel_flags[chat_id] = True
    await message.reply_text(
        "⏹️ <b>ᴛᴀɢ प्रोसेस रोक दिया गया!</b>\n"
        "थोड़ी देर से रुक जाएगा..."
    )


# Callback handlers for the stop / cancel buttons
@app.on_callback_query(filters.regex(r"^tag_stop "))
@admin_check
async def tag_stop_cb(_, query: types.CallbackQuery):
    chat_id = int(query.data.split()[1])
    if chat_id in _running_tags and not _running_tags[chat_id].done():
        _cancel_flags[chat_id] = True
        await query.answer("⏹️ Tag process stopped!", show_alert=True)
        try:
            await query.message.edit_text("⏹️ <b>Tag process stopped by admin.</b>")
        except Exception:
            pass
    else:
        await query.answer("No active tag process.", show_alert=True)


@app.on_callback_query(filters.regex(r"^tag_cancel "))
@admin_check
async def tag_cancel_cb(_, query: types.CallbackQuery):
    chat_id = int(query.data.split()[1])
    if chat_id in _running_tags and not _running_tags[chat_id].done():
        _cancel_flags[chat_id] = True
        await query.answer("❌ Tag cancelled!", show_alert=True)
        try:
            await query.message.edit_text("❌ <b>Tag process cancelled.</b>")
        except Exception:
            pass
    else:
        await query.answer("No active tag process.", show_alert=True)


@app.on_callback_query(filters.regex(r"^tag_resume "))
@admin_check
async def tag_resume_cb(_, query: types.CallbackQuery):
    chat_id = int(query.data.split()[1])
    if chat_id in _pause_flags:
        _pause_flags[chat_id] = False
        await query.answer("▶️ Resumed!", show_alert=True)
    else:
        await query.answer("Nothing to resume.", show_alert=True)


# Help callback for tag section (linked from help menu)
@app.on_callback_query(filters.regex(r"^help_tag$"))
@lang.language()
async def help_tag_cb(_, query: types.CallbackQuery):
    text = (
        f"🌺 <b>✨ ᴛᴀɴᴜ ᴍᴜꜱɪᴄ ᴛᴀɢ ᴘᴏᴡᴇʀ ᴇᴅɪᴛɪᴏɴ ✨</b> 🌺\n\n"
        f"🔴 <b>/tagall</b> वा <b>/all</b> वा <b>/tag [text]</b>\n"
        f"   • सभी मेम्बर्स को एक-एक करके टैग करता है\n"
        f"   • ऑप्शनल टेक्सट दे सकते हो\n\n"
        f"🟡 <b>/tagspam [text]</b>\n"
        f"   • तेज़ स्पैम मोड (कम डिले)\n\n"
        f"💣 <b>/tagbomb</b> वा <b>/bomb</b>\n"
        f"   • बहुत तेज़ बॉम्ब मोड (short tags)\n\n"
        f"👊 <b>/taggaali</b> वा <b>/gaali</b>\n"
        f"   • रैंडम मिल्ड रोस्ट / गाली स्टाइल टैग\n\n"
        f"⏹️ <b>/tagstop</b> वा <b>/tagcancel</b>\n"
        f"   • चल रहे टैग को तुरंत रोको\n\n"
        f"💡 <b>Note:</b> सिरीज (series) टैग के लिए फ़ाइल भेजो — मैं फ़ाइल भेजूँगा तो अड कर दूँगा।\n\n"
        f"🔐 सिर्फ़ अडमिन / सुडो के लिए ही काम करता है।"
    )
    await query.message.edit_text(
        text,
        reply_markup=buttons.help_markup(query.message.lang if hasattr(query.message, "lang") else {}, back=True),
    )
    await query.answer()
