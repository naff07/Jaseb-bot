import asyncio
import random
import logging
from datetime import datetime
from telethon import TelegramClient

logger = logging.getLogger("promo")


def setup_logger(log_file):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )


async def get_all_groups(client):
    """Ambil semua grup dari dialog akun."""
    groups = []
    async for dialog in client.iter_dialogs():
        if dialog.is_group or dialog.is_channel:
            groups.append({
                "id": dialog.id,
                "name": dialog.name or "Tanpa Nama",
                "type": "channel" if dialog.is_channel else "group"
            })
    return groups


async def run_promo(cfg, progress_callback=None):
    """
    Jalankan pengiriman promo.
    progress_callback(index, total, status, target, message) untuk update UI.
    """
    setup_logger(cfg.get("log_file", "promo.log"))

    client = TelegramClient(
        cfg["session_name"],
        int(cfg["api_id"]),
        cfg["api_hash"]
    )

    await client.start(phone=cfg["phone"])
    logger.info("Login berhasil.")

    targets = list(cfg["target_groups"])
    if cfg.get("shuffle_groups"):
        random.shuffle(targets)

    max_send = int(cfg.get("max_send_per_run", 0)) or len(targets)
    targets = targets[:max_send]

    base_interval = int(cfg.get("interval_seconds", 60))
    rand_delay = int(cfg.get("random_delay_seconds", 0))
    message = cfg["promo_message"]

    success, failed = 0, 0
    total = len(targets)

    for i, target in enumerate(targets, start=1):
        try:
            await client.send_message(target, message)
            success += 1
            logger.info(f"✅ [{i}/{total}] Terkirim → {target}")
            if progress_callback:
                progress_callback(i, total, "✅ Terkirim", str(target), message)
        except Exception as e:
            failed += 1
            logger.error(f"❌ [{i}/{total}] Gagal → {target} | {e}")
            if progress_callback:
                progress_callback(i, total, f"❌ Gagal: {e}", str(target), message)

        if i < total:
            delay = base_interval + (random.randint(0, rand_delay) if rand_delay else 0)
            logger.info(f"⏳ Menunggu {delay} detik sebelum lanjut...")
            await asyncio.sleep(delay)

    await client.disconnect()
    logger.info(f"🏁 Selesai. Sukses: {success}, Gagal: {failed}")
    return success, failed
