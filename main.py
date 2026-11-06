#!/usr/bin/env python3
import asyncio
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.align import Align
from rich.text import Text

from config_manager import load_config, save_config, config_exists
from promo_sender import run_promo, get_all_groups
from telethon import TelegramClient

console = Console()

BANNER = r"""
[bold cyan]
 ████████╗ ██████╗     ██████╗ ██████╗  ██████╗ ███╗   ███╗ ██████╗ 
 ╚══██╔══╝ ██╔════╝    ██╔══██╗██╔══██╗██╔═══██╗████╗ ████║██╔═══██╗
    ██║    ██║  ███╗   ██████╔╝██████╔╝██║   ██║██╔████╔██║██║   ██║
    ██║    ██║   ██║   ██╔═══╝ ██╔══██╗██║   ██║██║╚██╔╝██║██║   ██║
    ██║    ╚██████╔╝   ██║     ██║  ██║╚██████╔╝██║ ╚═╝ ██║╚██████╔╝
    ╚═╝     ╚═════╝    ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝     ╚═╝ ╚═════╝ 
[/bold cyan]
[bold yellow]     Telegram Group Promo Bot • Termux Edition v1.0[/bold yellow]
"""


def show_banner():
    console.clear()
    console.print(Align.center(BANNER))


def show_menu():
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("[bold green]1[/]", "Konfigurasi Akun & Pesan")
    table.add_row("[bold green]2[/]", "Lihat Konfigurasi Sekarang")
    table.add_row("[bold green]3[/]", "Ambil Daftar Grup dari Akun")
    table.add_row("[bold green]4[/]", "🚀  Jalankan Promosi")
    table.add_row("[bold green]5[/]", "Reset Konfigurasi")
    table.add_row("[bold green]0[/]", "Keluar")
    console.print(Panel(table, title="[bold cyan]MENU UTAMA[/]", border_style="cyan"))


def ask_multiline(prompt_text, default=""):
    console.print(f"[bold yellow]{prompt_text}[/]")
    console.print("[dim]Ketik pesan. Akhiri dengan baris berisi titik (.) saja.[/]")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == ".":
            break
        lines.append(line)
    result = "\n".join(lines).strip()
    return result if result else default


def cmd_config():
    cfg = load_config()

    console.print(Panel("[bold]Isi data konfigurasi. Kosongkan untuk pakai nilai default.[/]",
                        border_style="green"))

    api_id = Prompt.ask("API ID", default=str(cfg.get("api_id") or ""))
    if api_id.strip():
        try:
            cfg["api_id"] = int(api_id)
        except ValueError:
            console.print("[red]API ID harus angka![/]")

    api_hash = Prompt.ask("API HASH", default=cfg.get("api_hash") or "")
    if api_hash.strip():
        cfg["api_hash"] = api_hash.strip()

    phone = Prompt.ask("Nomor HP (contoh +628xxxx)", default=cfg.get("phone") or "")
    if phone.strip():
        cfg["phone"] = phone.strip()

    # Target grup
    console.print("[bold yellow]Target grup[/] (pisahkan dengan koma, contoh: -1001234567890,@namagrup)")
    current = ", ".join(str(g) for g in cfg.get("target_groups", []))
    raw = Prompt.ask("Daftar grup", default=current)
    groups = []
    for g in raw.split(","):
        g = g.strip()
        if not g:
            continue
        try:
            groups.append(int(g))
        except ValueError:
            groups.append(g)
    cfg["target_groups"] = groups

    # Pesan promo
    console.print("[bold yellow]Pesan promosi[/]")
    msg = ask_multiline("Isi pesan promosi:", default=cfg.get("promo_message", ""))
    cfg["promo_message"] = msg

    # Interval & delay
    cfg["interval_seconds"] = IntPrompt.ask(
        "Interval antar grup (detik)", default=int(cfg.get("interval_seconds", 60)))
    cfg["random_delay_seconds"] = IntPrompt.ask(
        "Random delay tambahan (0 = mati)", default=int(cfg.get("random_delay_seconds", 0)))
    cfg["max_send_per_run"] = IntPrompt.ask(
        "Maksimal grup per run (0 = semua)", default=int(cfg.get("max_send_per_run", 0)))
    cfg["shuffle_groups"] = Confirm.ask(
        "Acak urutan grup?", default=bool(cfg.get("shuffle_groups", True)))
    cfg["session_name"] = Prompt.ask(
        "Nama session file", default=cfg.get("session_name", "promo_session"))

    save_config(cfg)
    console.print("[bold green]✅ Konfigurasi disimpan.[/]")


def cmd_show():
    cfg = load_config()
    table = Table(title="📋 Konfigurasi Saat Ini", border_style="cyan", show_lines=True)
    table.add_column("Field", style="bold yellow")
    table.add_column("Value", style="white")

    safe = cfg.copy()
    if safe.get("api_hash"):
        safe["api_hash"] = safe["api_hash"][:6] + "***"
    if safe.get("phone"):
        p = safe["phone"]
        safe["phone"] = p[:4] + "***" + p[-3:] if len(p) > 8 else "***"

    for k, v in safe.items():
        if isinstance(v, list):
            v = "\n".join(str(x) for x in v) if v else "(kosong)"
        if isinstance(v, str) and "\n" in v:
            v = v.replace("\n", "\n  ")
        table.add_row(str(k), str(v))
    console.print(table)


async def _fetch_groups(cfg):
    client = TelegramClient(cfg["session_name"], int(cfg["api_id"]), cfg["api_hash"])
    await client.start(phone=cfg["phone"])
    groups = await get_all_groups(client)
    await client.disconnect()
    return groups


def cmd_fetch_groups():
    cfg = load_config()
    if not cfg.get("api_id") or not cfg.get("api_hash"):
        console.print("[red]Isi API ID & HASH dulu di menu 1.[/]")
        return
    console.print("[cyan]Mengambil daftar grup...[/]")
    try:
        groups = asyncio.run(_fetch_groups(cfg))
    except Exception as e:
        console.print(f"[red]Gagal: {e}[/]")
        return
    table = Table(title=f"📂 {len(groups)} grup ditemukan", border_style="magenta")
    table.add_column("#", style="dim")
    table.add_column("ID", style="cyan")
    table.add_column("Nama")
    table.add_column("Tipe")
    for i, g in enumerate(groups, 1):
        table.add_row(str(i), str(g["id"]), g["name"], g["type"])
    console.print(table)

    if groups and Confirm.ask("Tambahkan semua ke target grup?", default=False):
        cfg["target_groups"] = [g["id"] for g in groups]
        save_config(cfg)
        console.print("[bold green]✅ Target grup diperbarui.[/]")


def cmd_run():
    cfg = load_config()
    if not cfg.get("api_id") or not cfg.get("api_hash") or not cfg.get("target_groups"):
        console.print("[red]Konfigurasi belum lengkap! Isi dulu di menu 1.[/]")
        return

    total = len(cfg["target_groups"])
    console.print(Panel(
        f"[bold]Target :[/] {total} grup\n"
        f"[bold]Interval:[/] {cfg['interval_seconds']}s + random {cfg['random_delay_seconds']}s\n"
        f"[bold]Max    :[/] {cfg['max_send_per_run'] or 'semua'} grup",
        title="🚀 Siap Jalankan", border_style="yellow"))

    if not Confirm.ask("Mulai sekarang?", default=True):
        return

    with Progress(
        SpinnerColumn(),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("• {task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Mengirim...", total=min(total, cfg['max_send_per_run'] or total))

        def cb(i, t, status, target, msg):
            progress.update(task, completed=i, description=f"{status} → {target}")

        try:
            s, f = asyncio.run(run_promo(cfg, progress_callback=cb))
            console.print(f"\n[bold green]✅ Sukses: {s}[/]  [bold red]❌ Gagal: {f}[/]")
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/]")


def cmd_reset():
    if Confirm.ask("[red]Yakin reset konfigurasi?[/]", default=False):
        save_config({})
        console.print("[green]✅ Konfigurasi direset.[/]")


def main():
    while True:
        show_banner()
        show_menu()
        choice = Prompt.ask("[bold cyan]Pilih menu[/]", choices=["0","1","2","3","4","5"], default="0")

        if choice == "0":
            console.print("[bold yellow]👋 Bye![/]")
            sys.exit(0)
        elif choice == "1":
            cmd_config()
        elif choice == "2":
            cmd_show()
        elif choice == "3":
            cmd_fetch_groups()
        elif choice == "4":
            cmd_run()
        elif choice == "5":
            cmd_reset()

        console.print()
        Prompt.ask("[dim]Tekan ENTER untuk kembali ke menu[/]", default="")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Dibatalkan.[/]")
        sys.exit(0)
