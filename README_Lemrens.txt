Lemrens — Termux installation
=============================

1) Keep lemrens.py and install_lemrens.sh in the same folder in Termux.
2) Open that folder and run:
     bash install_lemrens.sh
3) Start the tool from any directory by typing:
     Lemrens

What changed:
- Tool name shown in the terminal and bot welcome text is Lemrens.
- The terminal banner remains animated in place, with colored text below it.
- The bot token is not echoed while typing.
- Routine polling/connection chatter and the generic "Bot started" line are hidden.
- In Telegram you can type image / صورة or video / فيديو, without a slash command.
- You can also send a photo or video directly. Type cancel / إلغاء to cancel.
- Existing inline controls for mode, width, and video frame rate remain available.

Dependencies used by the script must already be installed in Termux, including
python-telegram-bot (v20+), Wand/ImageMagick, and ffmpeg/ffprobe.

Optional: avoid entering the token on every launch by setting it in your shell
configuration (keep it private):
  export LEMRENS_BOT_TOKEN='YOUR_BOT_TOKEN'
Then reload the shell configuration. Do not share this token with anyone.
