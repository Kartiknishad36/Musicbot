# ============================================================================== 
# _inline.py - Premium Keyboard Buttons
# ============================================================================== 
# Helper methods to generate all the inline keyboards (play controls, help menus, etc).
# Premium multi-color emoji style for bright, colorful button look.
# ============================================================================== 

from pyrogram import types

from HasiiMusic import app, config, lang


class Inline:
    def __init__(self):
        self.ikm = types.InlineKeyboardMarkup
        self.ikb = types.InlineKeyboardButton

    def cancel_dl(self, text) -> types.InlineKeyboardMarkup:
        return self.ikm([[self.ikb(text=f"❌ {text}", callback_data=f"cancel_dl")]])

    def controls(
        self,
        chat_id: int,
        status: str = None,
        timer: str = None,
        remove: bool = False,
        is_playing: bool = True,
    ) -> types.InlineKeyboardMarkup:
        keyboard = []
        if status:
            keyboard.append(
                [self.ikb(
                    text=f"🌟 {status}", callback_data=f"controls status {chat_id}")]
            )
        elif timer:
            keyboard.append(
                [self.ikb(
                    text=f"⏱️ {timer}", callback_data=f"controls status {chat_id}")]
            )

        if not remove:
            # Seek buttons row - different colors
            keyboard.append(
                [
                    self.ikb(
                        text="🔴 « 30", callback_data=f"controls seek_back_30 {chat_id}"),
                    self.ikb(
                        text="🟡 « 10", callback_data=f"controls seek_back_10 {chat_id}"),
                    self.ikb(
                        text="🟢 10 »", callback_data=f"controls seek_forward_10 {chat_id}"),
                    self.ikb(
                        text="🔵 30 »", callback_data=f"controls seek_forward_30 {chat_id}"),
                ]
            )
            # Main control buttons row - premium colorful
            keyboard.append(
                [
                    self.ikb(
                        text="🟣 ⏸️" if is_playing else "🟢 ▶️", 
                        callback_data=f"controls {'pause' if is_playing else 'resume'} {chat_id}"
                    ),
                    self.ikb(
                        text="🟠 ⏮️", callback_data=f"controls previous {chat_id}"),
                    self.ikb(
                        text="🔵 🔄", callback_data=f"controls replay {chat_id}"),
                    self.ikb(
                        text="🟢 ⏭️", callback_data=f"controls skip {chat_id}"),
                    self.ikb(
                        text="🔴 ⏹️", callback_data=f"controls stop {chat_id}"),
                ]
            )
            # Delete button as full-width button at bottom
            keyboard.append(
                [
                    self.ikb(
                        text="🗑️ ᴅᴇʟᴇᴛᴇ", callback_data=f"controls close {chat_id}"),
                ]
            )
        return self.ikm(keyboard)

    def help_markup(
        self, _lang: dict, back: bool = False
    ) -> types.InlineKeyboardMarkup:
        if back:
            rows = [
                [
                    self.ikb(text="🔙 ʙᴀᴄᴋ", callback_data="help_main"),
                ]
            ]
        else:
            # Help menu with categorized buttons (3 per row) - colorful premium
            rows = [
                [
                    self.ikb(text="🔴 ᴀᴅᴍɪɴꜱ", callback_data="help_admins"),
                    self.ikb(text="🟢 ᴀᴜᴛʜ", callback_data="help_auth"),
                    self.ikb(text="🟡 ʙʀᴏᴀᴅᴄᴀꜱᴛ", callback_data="help_broadcast"),
                ],
                [
                    self.ikb(text="🔵 ʟᴏᴏᴘ", callback_data="help_loop"),
                    self.ikb(text="🟠 ᴘʟᴀʏ", callback_data="help_play"),
                    self.ikb(text="🟣 ᴄᴜᴇᴜᴇ", callback_data="help_queue"),
                ],
                [
                    self.ikb(text="🔴 ʙʟ-ᴄʜᴀᴛ", callback_data="help_blchat"),
                    self.ikb(text="🟡 ʙʟ-ᴜꜱᴇʀ", callback_data="help_bluser"),
                    self.ikb(text="🟢 ꜱᴇᴇᴋ", callback_data="help_seek"),
                ],
                [
                    self.ikb(text="🔵 ᴘɪɴɢ", callback_data="help_ping"),
                    self.ikb(text="🟠 ꜱᴛᴀᴛꜱ", callback_data="help_stats"),
                    self.ikb(text="🟣 ꜱᴜᴅᴏ", callback_data="help_sudo"),
                ],
                [
                    self.ikb(text="🌺 ᴛᴀɢ", callback_data="help_tag"),
                ],
                [
                    self.ikb(text="🔙 ʙᴀᴄᴋ", callback_data="start"),
                ]
            ]
        return self.ikm(rows)


    def ping_markup(self, text: str) -> types.InlineKeyboardMarkup:
        return self.ikm([
            [
                self.ikb(text="📢 Channel", url=config.SUPPORT_CHANNEL),
                self.ikb(text="🆘 Support", url=config.SUPPORT_CHAT),
            ],
            [
                self.ikb(text="➕ Add Me to Your Group", url=f"https://t.me/{app.username}?startgroup=true"),
            ]
        ])

    def play_queued(
        self, chat_id: int, item_id: str, _text: str
    ) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(
                        text="🟢 ▶️", callback_data=f"controls resume {chat_id}"),
                    self.ikb(
                        text="🟣 ⏸️", callback_data=f"controls pause {chat_id}"),
                    self.ikb(
                        text="🔵 ⏭️", callback_data=f"controls skip {chat_id}"),
                    self.ikb(
                        text="🔴 ⏹️", callback_data=f"controls stop {chat_id}"),
                ],
                [
                    self.ikb(
                        text="🗑️ ᴅᴇʟᴇᴛᴇ", callback_data=f"controls close {chat_id}"),
                ]
            ]
        )

    def queue_markup(
        self, chat_id: int, _text: str, playing: bool
    ) -> types.InlineKeyboardMarkup:
        _action = "pause" if playing else "resume"
        emoji = "🟣 ⏸️" if playing else "🟢 ▶️"
        return self.ikm(
            [[self.ikb(
                text=f"{emoji} {_text}", callback_data=f"controls {_action} {chat_id} q")]]
        )

    def settings_markup(
        self, lang: dict, admin_only: bool, language: str, chat_id: int
    ) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(
                        text=f"🎯 {lang['play_mode']} ➜",
                        callback_data=f"controls status {chat_id}",
                    ),
                    self.ikb(text=f"🔑 {admin_only}", callback_data="playmode"),
                ],
            ]
        )

    def start_key(
        self, lang: dict, private: bool = False
    ) -> types.InlineKeyboardMarkup:
        rows = [
            [
                self.ikb(
                    text=f"🌹 {lang['add_me']}",
                    url=f"https://t.me/{app.username}?startgroup=true",
                )
            ],
            [
                self.ikb(text=f"📚 {lang['help']}", callback_data="help"),
                self.ikb(text="🌺 ᴛᴀɢ", callback_data="help_tag"),
            ],
            [
                self.ikb(text=f"🆘 {lang['support']}", url=config.SUPPORT_CHAT),
                self.ikb(text=f"📢 {lang['channel']}", url=config.SUPPORT_CHANNEL),
            ],
        ]
        if private:
            rows += [
                [
                    self.ikb(
                        text=f"💻 {lang.get('source', 'Source')}",
                        url="https://github.com/Kartiknishad36/Musicbot",
                    )
                ]
            ]
        return self.ikm(rows)

    def yt_key(self, link: str) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(text="📋 ᴄᴏᴘʏ ʟɪɴᴋ", copy_text=link),
                    self.ikb(text="🎥 ᴏᴘᴇɴ ɪɴ ʏᴏᴜᴛᴜʙᴇ", url=link),
                ],
            ]
        )

    def tag_markup(self, chat_id: int) -> types.InlineKeyboardMarkup:
        """Premium colored buttons for tag controls."""
        return self.ikm([
            [
                self.ikb(text="🔴 Stop", callback_data=f"tag_stop {chat_id}"),
                self.ikb(text="🟡 Cancel", callback_data=f"tag_cancel {chat_id}"),
            ],
            [
                self.ikb(text="🟢 Resume", callback_data=f"tag_resume {chat_id}"),
            ]
        ])
