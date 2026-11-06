import json
import os
from pathlib import Path

CONFIG_FILE = Path("config.json")

DEFAULT_CONFIG = {
    "api_id": 0,
    "api_hash": "",
    "phone": "",
    "target_groups": [],
    "promo_message": "🎯 Promosi Produk\n\nIsi pesan promosi Anda di sini...",
    "interval_seconds": 60,
    "random_delay_seconds": 15,
    "max_send_per_run": 10,
    "shuffle_groups": True,
    "session_name": "promo_session",
    "log_file": "promo.log"
}


def load_config():
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        cfg = DEFAULT_CONFIG.copy()
        cfg.update(data)
        return cfg
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def config_exists():
    return CONFIG_FILE.exists() and os.path.getsize(CONFIG_FILE) > 2
