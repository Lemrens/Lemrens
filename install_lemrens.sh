#!/data/data/com.termux/files/usr/bin/bash
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
SOURCE="$SCRIPT_DIR/lemrens.py"

if [ ! -f "$SOURCE" ]; then
  echo "Missing lemrens.py. Keep this installer beside lemrens.py and try again."
  exit 1
fi

if [ -z "${PREFIX:-}" ]; then
  PREFIX="/data/data/com.termux/files/usr"
fi

APP_DIR="$HOME/.local/share/lemrens"
mkdir -p "$APP_DIR" "$PREFIX/bin"
cp "$SOURCE" "$APP_DIR/lemrens.py"
chmod 600 "$APP_DIR/lemrens.py"

cat > "$PREFIX/bin/Lemrens" <<'LAUNCHER'
#!/data/data/com.termux/files/usr/bin/sh
exec python "$HOME/.local/share/lemrens/lemrens.py" "$@"
LAUNCHER
chmod 755 "$PREFIX/bin/Lemrens"
ln -sf "$PREFIX/bin/Lemrens" "$PREFIX/bin/lemrens"

echo "Lemrens installed. Run it by typing: Lemrens"
echo "The token prompt is hidden. To avoid entering it each time, set LEMRENS_BOT_TOKEN in your shell environment."
