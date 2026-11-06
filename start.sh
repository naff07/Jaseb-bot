#!/data/data/com.termux/files/usr/bin/bash
# Launcher otomatis untuk Termux

set -e
cd "$(dirname "$0")"

if ! command -v python &> /dev/null; then
    echo "❌ Python belum ada. Install: pkg install python"
    exit 1
fi

if [ ! -d ".venv" ]; then
    echo "📦 Membuat virtualenv..."
    python -m venv .venv
fi

source .venv/bin/activate

if ! python -c "import telethon" &> /dev/null; then
    echo "📦 Install dependencies..."
    pip install -r requirements.txt
fi

python main.py
