#!/data/data/com.termux/files/usr/bin/bash
set -Eeuo pipefail

APP_NAME="Lemrens"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
SOURCE="$SCRIPT_DIR/lemrens.py"
REQ_SOURCE="$SCRIPT_DIR/requirements.txt"
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
APP_DIR="$HOME/.local/share/lemrens"
BIN_DIR="$PREFIX/bin"

if [ -t 1 ]; then
  RESET='\033[0m'; BOLD='\033[1m'; CYAN='\033[36m'; GREEN='\033[32m'; YELLOW='\033[33m'; RED='\033[31m'
else
  RESET=''; BOLD=''; CYAN=''; GREEN=''; YELLOW=''; RED=''
fi
say() { printf "%b\n" "$*"; }
fail() { say "${RED}✖ $* ${RESET}"; exit 1; }

say "${CYAN}${BOLD}"
say "╭────────────────────────────────────────╮"
say "│           L E M R E N S                │"
say "│     Terminal tools • Smart setup       │"
say "╰────────────────────────────────────────╯"
say "${RESET}"

[ -f "$SOURCE" ] || fail "لم أجد lemrens.py. شغّل المثبّت من مجلد المشروع."
[ -f "$REQ_SOURCE" ] || fail "لم أجد requirements.txt في مجلد المشروع."
command -v pkg >/dev/null 2>&1 || fail "هذا المثبّت مخصص لـ Termux."

say "${YELLOW}◆ التحقق من متطلبات النظام وتثبيت الناقص منها... ${RESET}"
pkg update -y
pkg install -y python imagemagick ffmpeg

mkdir -p "$APP_DIR" "$BIN_DIR"
cp "$SOURCE" "$APP_DIR/lemrens.py"
cp "$REQ_SOURCE" "$APP_DIR/requirements.txt"
chmod 600 "$APP_DIR/lemrens.py" "$APP_DIR/requirements.txt"

say "${YELLOW}◆ التحقق من مكتبات Python وتثبيت الناقص منها... ${RESET}"
python -m pip install -r "$APP_DIR/requirements.txt"

python - <<'PY' || fail "فشل التحقق من مكتبات Python بعد التثبيت."
import telegram
import wand
print("Python packages: OK")
PY
command -v ffmpeg >/dev/null 2>&1 || fail "لم يتم العثور على ffmpeg."
command -v ffprobe >/dev/null 2>&1 || fail "لم يتم العثور على ffprobe."

cat > "$BIN_DIR/Lemrens" <<'LAUNCHER'
#!/data/data/com.termux/files/usr/bin/bash
set -eu
APP_DIR="$HOME/.local/share/lemrens"

if [ ! -f "$APP_DIR/lemrens.py" ] || [ ! -f "$APP_DIR/requirements.txt" ]; then
  printf '\033[31mLemrens is not installed correctly. Run the installer again.\033[0m\n' >&2
  exit 1
fi

# Restore Python dependencies if they were removed after installation.
if ! python -c 'import telegram, wand' >/dev/null 2>&1; then
  printf '\033[33mLemrens: installing missing Python libraries...\033[0m\n'
  python -m pip install -r "$APP_DIR/requirements.txt"
fi

# Restore system dependencies if missing.
if ! command -v ffmpeg >/dev/null 2>&1 || ! command -v ffprobe >/dev/null 2>&1; then
  if command -v pkg >/dev/null 2>&1; then
    pkg install -y ffmpeg
  else
    printf 'Lemrens requires ffmpeg/ffprobe. Install with: pkg install ffmpeg\n' >&2
    exit 1
  fi
fi
if ! command -v magick >/dev/null 2>&1 && ! command -v convert >/dev/null 2>&1; then
  if command -v pkg >/dev/null 2>&1; then
    pkg install -y imagemagick
  else
    printf 'Lemrens requires ImageMagick. Install with: pkg install imagemagick\n' >&2
    exit 1
  fi
fi

exec python "$APP_DIR/lemrens.py" "$@"
LAUNCHER
chmod 755 "$BIN_DIR/Lemrens"
ln -sf "$BIN_DIR/Lemrens" "$BIN_DIR/lemrens"

say "${GREEN}${BOLD}✓ تم تثبيت Lemrens بنجاح.${RESET}"
say "شغّل الأداة من أي مجلد بكتابة: ${CYAN}Lemrens${RESET}"
say "سيتم فحص المكتبات تلقائيًا، وتثبيت الناقص منها عند الحاجة."
say "لن يظهر توكن البوت أثناء كتابته. لا تحفظ التوكن داخل المستودع."
