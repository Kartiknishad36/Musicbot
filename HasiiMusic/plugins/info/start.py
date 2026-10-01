# ============================================================================== 
# start.py - Basics (Premium Edition)
# ============================================================================== 

from pyrogram import enums, filters, types

from HasiiMusic import app, config, db, lang
from HasiiMusic.helpers import buttons, utils


@app.on_message(filters.command(["help"]) & filters.private & ~app.bl_users)
@lang.language()
async def _help(_, m: types.Message):
    try:
        await m.delete()
    except Exception:
        pass

    help_text = (
        f"❖ ✨ <b>ᴛʜɪꜱ ɪꜱ ✨ 🎀 ᴛᴀɴᴜ ᴍᴜꜱɪᴄ</b> 🎀 ✨ 🎵 !\n\n"
        f"❖ 🎧 ᴍᴜꜱɪᴄ ᴘʟᴀʏᴇʀ ᴡɪᴛʜ ᴘʀᴇᴍɪᴜᴍ ᴄᴏɴᴛʀᴏʟꜱ\n"
        f"❖ 🤖 ᴄʀᴇᴀᴛᴇ ʏᴏᴜʀ ᴏᴡɴ ʙᴏᴛ ɪɴꜱᴛᴀɴᴛʟʏ\n"
        f"❖ ⚡ 24x7 ᴀᴄᴛɪᴠᴇ | 💎 ᴘʀᴇᴍɪᴜᴍ ᴄᴜᴀʟɪᴛʏ\n\n"
        f"❖ ❓ ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʜᴇʟᴘ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ɪɴᴀᴏ\n"
        f"ᴀʙᴏᴜᴛ ᴍʏ ᴍᴏᴅᴜʟᴇꜱ ᴀɴᴅ ᴄᴏᴍᴍᴀɴᴅꜱ...!"
    )
    try:
        await m.reply_photo(
            photo=config.START_IMG,
            caption=help_text,
            reply_markup=buttons.help_markup(m.lang),
        )
    except Exception:
        await m.reply_text(
            text=help_text,
            reply_markup=buttons.help_markup(m.lang),
        )


@app.on_message(filters.command(["start"]))
@lang.language()
async def start(_, message: types.Message):
    if message.chat.type != enums.ChatType.PRIVATE:
        try:
            await message.delete()
        except Exception:
            pass

    if not message.from_user:
        return

    if message.from_user.id in app.bl_users and message.from_user.id not in db.notified:
        return await message.reply_text(message.lang["bl_user_notify"])

    if len(message.command) > 1 and message.command[1] == "help":
        return await _help(_, message)

    private = message.chat.type == enums.ChatType.PRIVATE

    if private:
        _text = (
            f"❖ ✨ <b>ᴛʜɪꜱ ɪꜱ ✨ 🎀 ᴛᴀɴᴜ ᴍᴜꜱɪᴄ</b> 🎀 ✨ 🎵 !\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"❖ 🎧 ᴍᴜꜱɪᴄ ᴘʟᴀʏᴇʀ ᴡɪᴛʜ ᴘʀᴇᴍɪᴜᴍ ᴄᴏɴᴛʀᴏʟꜱ\n"
            f"❖ 🤖 ᴄʀᴇᴀᴛᴇ ʏᴏᴜʀ ᴏᴡɴ ʙᴏᴛ ɪɴꜱᴛᴀɴᴛʟʏ\n"
            f"❖ ⚡ 24x7 ᴀᴄᴛɪᴠᴇ | 💎 ᴘʀᴇᴍɪᴜᴍ ᴄᴜᴀʟɪᴛʏ\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"❖ ❓ ᴄʟɪᴄᴋ ᴏɴ ᴛʜᴇ ʜᴇʟᴘ ʙᴜᴛᴛᴏɴ ᴛᴏ ɢᴇᴛ ɪɴᴀᴏ\n"
            f"ᴀʙᴏᴜᴛ ᴍʏ ᴍᴏᴅᴜʟᴇꜱ ᴀɴᴅ ᴄᴏᴍᴍᴀɴᴅꜱ...!"
        )
    else:
        _text = (
            f"❖ ✨ <b>ᴛᴀɴᴜ ᴍᴜꜱɪᴄ ɪꜱ ᴀᴄᴛɪᴠᴇ</b> ✨\n\n"
            f"ᴜꜱᴇ <b>/play</b> ᴛᴏ ꜱᴛᴀʀᴛ ᴍᴜꜱɪᴄ.\n"
            f"ᴜꜱᴇ <b>/help</b> ᴛᴏ ꜱᴇᴇ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅꜱ."
        )

    key = buttons.start_key(message.lang, private)
    try:
        await message.reply_photo(
            photo=config.START_IMG,
            caption=_text,
            reply_markup=key,
        )
    except Exception:
        await message.reply_text(
            text=_text,
            reply_markup=key,
        )

    if private:
        if await db.is_user(message.from_user.id):
            return
        await utils.send_log(message)
        return await db.add_user(message.from_user.id)


@app.on_message(filters.command(["playmode", "settings"]) & filters.group & ~app.bl_users)
@lang.language()
async def settings(_, message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass

    admin_only = await db.get_play_mode(message.chat.id)
    _language = "en"
    settings_text = (
        f"🎯 <b>✨ ᴛᴀɴᴜ ᴍᴜꜱɪᴄ ꜱᴇᴛᴛɪɴɢꜱ ✨</b>\n\n"
        f"🌹 Group: <b>{message.chat.title}</b>\n"
        f"🔑 Play Mode: <b>{'Admins Only' if admin_only else 'Everyone'}</b>\n\n"
        f"Tap the buttons below to change settings."
    )
    await utils.safe_text(
        message,
        settings_text,
        reply_markup=buttons.settings_markup(
            message.lang, admin_only, _language, message.chat.id
        ),
        quote=True,
    )


@app.on_message(filters.new_chat_members, group=7)
@lang.language()
async def _new_member(_, message: types.Message):
    if message.chat.type != enums.ChatType.SUPERGROUP:
        return await message.chat.leave()

    for member in message.new_chat_members:
        if member.id == app.id:
            if await db.is_chat(message.chat.id):
                return
            await db.add_chat(message.chat.id)
