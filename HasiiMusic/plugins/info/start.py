# ============================================================================== 
# start.py - Basics (Premium Edition)
# ============================================================================== 
# Essential user-facing commands: /start, /help, /settings, etc.
# Full premium design with colorful emojis, flowers and detailed captions.
# ============================================================================== 

from pyrogram import enums, filters, types

from HasiiMusic import app, config, db, lang
from HasiiMusic.helpers import buttons, utils


@app.on_message(filters.command(["help"]) & filters.private & ~app.bl_users)
@lang.language()
async def _help(_, m: types.Message):
    # Auto-delete command message
    try:
        await m.delete()
    except Exception:
        pass
    
    help_text = (
        f"🌹 <b>✨ ᴛᴀɴᴜ ᴍᴜꜱɪᴄ ᴘʀᴇᴍɪᴜᴍ ᴇᴅɪᴛɪᴏɴ ✨</b> 🌹\n\n"
        f"🌺 Choose a category below to explore commands:\n"
        f"• 🔴 <b>Admins</b> — Manage your group\n"
        f"• 🟢 <b>Auth</b> — Authorized users\n"
        f"• 🟡 <b>Broadcast</b> — Message all chats\n"
        f"• 🔵 <b>Loop / Play / Queue</b> — Playback control\n"
        f"• 🟠 <b>Blacklist</b> — Block chats or users\n"
        f"• 🟣 <b>Stats / Sudo / Ping</b> — Bot info\n"
        f"• 🌺 <b>Tag</b> — Tag all members, spam, bomb & more\n\n"
        f"🌸 Tap any button to see detailed help."
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
    # Auto-delete command message in group chats
    if message.chat.type != enums.ChatType.PRIVATE:
        try:
            await message.delete()
        except Exception:
            pass
    
    # Skip if message from channel or anonymous admin
    if not message.from_user:
        return

    # Check if user is blacklisted
    if message.from_user.id in app.bl_users and message.from_user.id not in db.notified:
        return await message.reply_text(message.lang["bl_user_notify"])

    # If /start help, show help menu
    if len(message.command) > 1 and message.command[1] == "help":
        return await _help(_, message)

    # Determine if chat is private or group
    private = message.chat.type == enums.ChatType.PRIVATE

    if private:
        _text = (
            f"🌹 <b>✨ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛᴀɴᴜ ᴍᴜꜱɪᴄ ✨</b> 🌹\n\n"
            f"🌸 Hey <b>{message.from_user.first_name}</b>!\n"
            f"I’m <b>{app.name}</b> — your premium high-quality music bot.\n\n"
            f"🎵 Play songs from YouTube, Spotify, Telegram & more\n"
            f"🎯 Crystal clear audio + video streaming\n"
            f"🌺 Powerful tag, admin & utility tools\n"
            f"💎 Beautiful colorful controls & design\n\n"
            f"👉 Add me to your group and start the party!"
        )
    else:
        _text = (
            f"🌹 <b>✨ ᴛᴀɴᴜ ᴍᴜꜱɪᴄ ɪꜱ ᴀᴄᴛɪᴠᴇ ✨</b> 🌹\n\n"
            f"🌸 Thanks for adding me here!\n"
            f"Use <b>/play</b> to start music instantly.\n"
            f"Type <b>/help</b> to see all premium features."
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

    # For private chats, add user to database if new
    if private:
        if await db.is_user(message.from_user.id):
            return  # User already exists, no need to add
        # Log new user to logger group
        await utils.send_log(message)
        # Add user to database
        return await db.add_user(message.from_user.id)


@app.on_message(filters.command(["playmode", "settings"]) & filters.group & ~app.bl_users)
@lang.language()
async def settings(_, message: types.Message):
    # Auto-delete command message
    try:
        await message.delete()
    except Exception:
        pass
    
    admin_only = await db.get_play_mode(message.chat.id)  # Get play mode setting
    _language = "en"
    settings_text = (
        f"🎯 <b>✨ ᴛᴀɴᴜ ᴍᴜꜱɪᴄ ᴛᴇᴛᴛɪɴɢꜱ ✨</b>\n\n"
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
    # Only work in supergroups (not basic groups)
    if message.chat.type != enums.ChatType.SUPERGROUP:
        return await message.chat.leave()

    # Check each new member
    for member in message.new_chat_members:
        if member.id == app.id:  # Bot itself was added
            if await db.is_chat(message.chat.id):
                return  # Chat already in database
            # Add chat to database (log is sent from new_chat.py with photo)
            await db.add_chat(message.chat.id)
