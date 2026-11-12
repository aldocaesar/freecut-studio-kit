#!/usr/bin/env bash
# ============================================================================
# FreeCut Universal Studio Bot (v6) — macOS & Linux Installer (`install.sh`)
# ============================================================================
# Usage:
#   chmod +x install.sh && ./install.sh
#   ./install.sh --with-freecut-app   # also clones & installs walterlow/freecut locally
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

WITH_FREECUT=0
SETUP_KEYS=0
for arg in "$@"; do
  if [[ "$arg" == "--with-freecut-app" ]]; then
    WITH_FREECUT=1
  elif [[ "$arg" == "--setup-keys" ]]; then
    SETUP_KEYS=1
  fi
done

echo "======================================================================"
echo " FreeCut Universal Studio Bot v6 — macOS / Linux Automatic Setup"
echo "======================================================================"

install_pkg() {
  local cmd_name="$1"
  local brew_pkg="$2"
  local apt_pkg="$3"
  if command -v "$cmd_name" >/dev/null 2>&1; then
    echo "  [OK] $cmd_name found: $(command -v "$cmd_name")"
    return
  fi
  echo "  [INSTALL] Installing $cmd_name..."
  if command -v brew >/dev/null 2>&1; then
    brew install "$brew_pkg"
  elif command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update -y && sudo apt-get install -y $apt_pkg
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y $apt_pkg
  else
    echo "  [ERROR] Please install '$cmd_name' manually and re-run ./install.sh"
    exit 1
  fi
}

echo ""
echo "[1/5] Checking System Binaries (Python 3, FFmpeg, Node.js, Git)..."
install_pkg python3 python "python3 python3-venv python3-pip"
install_pkg ffmpeg ffmpeg ffmpeg
install_pkg node node nodejs
install_pkg git git git

echo ""
echo "[2/5] Setting up Python Virtual Environment (.venv) & packages..."
if [[ ! -x "$ROOT_DIR/.venv/bin/python" ]]; then
  python3 -m venv "$ROOT_DIR/.venv"
fi
PY_EXE="$ROOT_DIR/.venv/bin/python"
"$PY_EXE" -B -m pip install --upgrade pip
"$PY_EXE" -B -m pip install -r "$ROOT_DIR/requirements.txt"

echo ""
echo "[3/5] Installing Playwright Chromium headless renderer..."
"$PY_EXE" -B -m playwright install chromium

echo ""
echo "[4/5] Syncing skills for all Frontier AIs (.agents/skills <-> .claude/skills)..."
rm -rf "$ROOT_DIR/.claude/skills"
mkdir -p "$ROOT_DIR/.claude/skills"
for sk in doc-art-director doc-lottie-overlays doc-motion-scenes freecut-unified-engine; do
  if [[ -d "$ROOT_DIR/.agents/skills/$sk" ]]; then
    cp -R "$ROOT_DIR/.agents/skills/$sk" "$ROOT_DIR/.claude/skills/$sk"
    rm -f "$ROOT_DIR/.claude/skills/$sk/.openbot-managed.json"
  fi
done

if [[ ! -f "$ROOT_DIR/.env" && -f "$ROOT_DIR/.env.example" ]]; then
  cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
fi

if [[ "$WITH_FREECUT" -eq 1 ]]; then
  echo ""
  echo "[Optional] Cloning & installing local FreeCut Web Editor (walterlow/freecut)..."
  if [[ ! -d "$ROOT_DIR/freecut-app" ]]; then
    git clone --depth 1 https://github.com/walterlow/freecut.git "$ROOT_DIR/freecut-app"
  fi
  (cd "$ROOT_DIR/freecut-app" && npm install)
  cat > "$ROOT_DIR/start-freecut.sh" <<EOF
#!/usr/bin/env bash
cd "$ROOT_DIR/freecut-app" && npm run dev
EOF
  chmod +x "$ROOT_DIR/start-freecut.sh"
  echo "  [OK] Run ./start-freecut.sh anytime to launch FreeCut locally."
fi

echo ""
echo "[5/5] Running Environment Doctor Verification..."
"$PY_EXE" -B "$ROOT_DIR/doctor.py"

if [[ "$SETUP_KEYS" -eq 1 ]]; then
  "$PY_EXE" -B "$ROOT_DIR/.agents/skills/freecut-unified-engine/scripts/bootstrap_env.py" --setup-keys
else
  echo ""
  echo "[TIP] 0 API keys required! To add your FREE Pixabay HD key (pixabay.com/api/docs/) or optional Groq/ElevenLabs keys anytime:"
  echo "      $PY_EXE -B .agents/skills/freecut-unified-engine/scripts/bootstrap_env.py --setup-keys"
fi
