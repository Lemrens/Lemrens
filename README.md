# Lemrens

**Lemrens** is a terminal-first Telegram tool for converting images and videos into ASCII art. It includes a live terminal banner, colored status text, image/video conversion controls, and a Termux installer.

## Features

- Animated terminal banner with a fixed, colored interface.
- Convert photos and videos into ASCII art through Telegram.
- Choose rendering style and output width using inline controls.
- Video frame-rate options and progress updates.
- Hidden token prompt: your bot token is not echoed while typing.
- One-word launcher: type `Lemrens` from any Termux directory.
- Dependency checks during installation; the launcher restores missing Python dependencies when needed.
- Uses Termux packages for FFmpeg and ImageMagick.

## Install on Termux

```bash
pkg update
pkg install -y git
git clone https://github.com/Lemrens/Lemrens.git
cd Lemrens
bash install_lemrens.sh
```

After installation, start the app from anywhere:

```bash
Lemrens
```

The installer checks and installs Python, ImageMagick, FFmpeg/ffprobe, and the Python packages listed in `requirements.txt`. The launcher also checks dependencies at startup and attempts to restore missing packages.

## Use the Telegram bot

1. Start Lemrens in Termux.
2. Enter your Telegram bot token when prompted. The token is hidden while typing.
3. Open your bot in Telegram and send `/start`.
4. Send an image or video directly, or type `image` / `صورة` or `video` / `فيديو`.
5. Choose style, width, and frame rate using the buttons.

Type `cancel` / `إلغاء` to cancel a pending action.

## Keep your token private

Do not commit your bot token to GitHub or paste it into public issues. To avoid entering it every time, set it in your private Termux shell configuration:

```bash
echo 'export LEMRENS_BOT_TOKEN="YOUR_BOT_TOKEN"' >> ~/.bashrc
source ~/.bashrc
```

Replace the placeholder locally with your token. Never publish that value. If a token was exposed publicly, revoke it through BotFather and create a new one.

## Dependencies

- Python 3
- `python-telegram-bot` (v20+)
- Wand
- ImageMagick
- FFmpeg and ffprobe

## Troubleshooting

- If `Lemrens: command not found`, close and reopen Termux, or run `hash -r`.
- If installation fails, retry `pkg update && pkg upgrade`, then run `bash install_lemrens.sh` again from the repository directory.
- Keep the terminal open while the bot is running.

## License

No license is specified yet. Add a license file if you want to define how others may reuse or distribute the project.
