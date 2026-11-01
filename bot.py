import asyncio
import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WA_ADMIN = os.getenv("ADMIN_WA", "082281550251")
JAM_OPS = "09.00–21.00 WIB"

def kb(*rows: list[str]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton(label) for label in row] for row in rows],
        resize_keyboard=True,
    )


MENU_KEYBOARD = kb(["1", "2", "3"], ["4", "5", "6"], ["MENU"])
KOLEKSI_KEYBOARD = kb(["A", "B", "C", "D"], ["MENU"])
HARGA_KEYBOARD = kb(["A", "B", "C"], ["D", "E"], ["4", "6", "MENU"])
BUNDLING_KEYBOARD = kb(["A", "B", "C"], ["6", "MENU"])
DETAIL_KEYBOARD = kb(["2", "3", "6"], ["MENU"])
STOK_KEYBOARD = kb(["6", "MENU"])
BOOKING_KEYBOARD = kb(["3", "6"], ["MENU"])
ADMIN_KEYBOARD = kb(["MENU"])

TEXT_MENU = f"""Halo! Selamat datang di BUTICALL
Sewa busana desain sendiri untuk wisuda, pesta, dan acara formal.

Pilih menu:
1 Info koleksi
2 Cek harga sewa
3 Cek ketersediaan
4 Cara booking
5 Paket bundling
6 Hubungi admin

Tekan tombol di bawah, atau ketik angka 1-6.
Tekan MENU untuk kembali."""

TEXT_KOLEKSI = """Koleksi BUTICALL:
A Kebaya modern
B Gaun pesta
C Gaun wisuda
D Pakaian formal

Tekan A/B/C/D di bawah, atau MENU untuk kembali."""

TEXT_HARGA = """Harga sewa BUTICALL (per 1–2 hari):
A Kebaya modern : Rp 150.000
B Gaun pesta    : Rp 175.000
C Gaun wisuda   : Rp 200.000
D Formal        : Rp 150.000
E Bundling      : mulai Rp 225.000

*Ganti angka ini sesuai harga asli toko.

Tekan A–E untuk detail, atau 4 / 6 / MENU."""

TEXT_STOK = """Cek ketersediaan — balas dengan format:

NAMA / TANGGAL / UKURAN / JENIS

Contoh:
Sinta / 15 Juni 2026 / M / Gaun wisuda

Admin akan konfirmasi stok.
Tekan 6 untuk hubungi admin sekarang."""

TEXT_BOOKING = """Cara booking BUTICALL:
1. Pilih model & size
2. Cek tanggal ketersediaan
3. Bayar DP
4. Fitting (jika perlu)
5. Ambil/kirim sesuai jadwal
6. Kembalikan sesuai durasi sewa

Tekan 3 cek stok | 6 Hubungi Admin | MENU"""

TEXT_BUNDLING = """Paket bundling:
A Paket Wisuda (gaun + aksesoris)
B Paket Pesta (dress + aksesoris)
C Paket Kebaya (kebaya + aksesoris)

Tekan A/B/C untuk detail, atau 6 untuk admin."""

TEXT_ADMIN = f"""Admin BUTICALL
WhatsApp: {WA_ADMIN}
Jam: {JAM_OPS}

Siapkan: nama, tanggal sewa, acara, size, model.
Tekan MENU untuk kembali."""

DETAIL = {
    "A": """Kebaya modern BUTICALL
• Size: S, M, L, XL
• Cocok: wisuda, kondangan, formal
• Harga: Rp 150.000 / 1–2 hari

Tekan 2 harga | 3 stok | 6 Hubungi Admin | MENU""",
    "B": """Gaun pesta BUTICALL
• Size: S, M, L, XL
• Cocok: pesta, dinner, pemotretan
• Harga: Rp 175.000 / 1–2 hari

Tekan 2 harga | 3 stok | 6 Hubungi Admin | MENU""",
    "C": """Gaun wisuda BUTICALL
• Size: S, M, L, XL
• Cocok: wisuda & foto studio
• Harga: Rp 200.000 / 1–2 hari

Tekan 2 harga | 3 stok | 6 Hubungi Admin | MENU""",
    "D": """Pakaian formal BUTICALL
• Size: S, M, L, XL
• Cocok: acara formal / meeting
• Harga: Rp 150.000 / 1–2 hari

Tekan 2 harga | 3 stok | 6 Hubungi Admin | MENU""",
}

BUNDLING_DETAIL = {
    "A": "Paket Wisuda: gaun + aksesoris. Mulai Rp 225.000\nTekan 6 Hubungi Admin | MENU",
    "B": "Paket Pesta: dress + aksesoris. Mulai Rp 250.000\nTekan 6 Hubungi Admin | MENU",
    "C": "Paket Kebaya: kebaya + aksesoris. Mulai Rp 225.000\nTekan 6 Hubungi Admin | MENU",
}

TEXT_UNKNOWN = """Maaf, aku belum paham.
Aku chatbot menu BUTICALL.

Tekan MENU
1 Koleksi | 2 Harga | 3 Ketersediaan
4 Booking | 5 Bundling | 6 Hubungi Admin"""

MENU_ROUTES = {
    "1": ("koleksi", TEXT_KOLEKSI, KOLEKSI_KEYBOARD),
    "2": ("harga", TEXT_HARGA, HARGA_KEYBOARD),
    "3": ("stok", TEXT_STOK, STOK_KEYBOARD),
    "4": ("booking", TEXT_BOOKING, BOOKING_KEYBOARD),
    "5": ("bundling", TEXT_BUNDLING, BUNDLING_KEYBOARD),
    "6": ("admin", TEXT_ADMIN, ADMIN_KEYBOARD),
}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["mode"] = "menu"
    await update.message.reply_text(TEXT_MENU, reply_markup=MENU_KEYBOARD)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    key = text.upper()
    mode = context.user_data.get("mode", "menu")

    # Deteksi format cek stok: NAMA / TANGGAL / UKURAN / JENIS
    if "/" in text and text.count("/") >= 3:
        context.user_data["mode"] = "menu"
        await update.message.reply_text(
            "Terima kasih! Data sudah diterima.\n"
            f"Admin akan cek stok lalu menghubungi via WA: {WA_ADMIN}\n\n"
            "Tekan MENU untuk kembali.",
            reply_markup=MENU_KEYBOARD,
        )
        return

    if key in {"MENU", "0", "HALO", "HI", "START"}:
        context.user_data["mode"] = "menu"
        await update.message.reply_text(TEXT_MENU, reply_markup=MENU_KEYBOARD)
        return

    if key in MENU_ROUTES:
        new_mode, body, keyboard = MENU_ROUTES[key]
        context.user_data["mode"] = new_mode
        await update.message.reply_text(body, reply_markup=keyboard)
        return

    # Tombol E dari menu harga → paket bundling
    if key == "E" and mode == "harga":
        context.user_data["mode"] = "bundling"
        await update.message.reply_text(TEXT_BUNDLING, reply_markup=BUNDLING_KEYBOARD)
        return

    # Di mode bundling, A/B/C = detail paket
    if mode == "bundling" and key in BUNDLING_DETAIL:
        await update.message.reply_text(
            BUNDLING_DETAIL[key], reply_markup=DETAIL_KEYBOARD
        )
        return

    if key in DETAIL:
        await update.message.reply_text(DETAIL[key], reply_markup=DETAIL_KEYBOARD)
        return

    if key in {"PAKET A", "PAKET B", "PAKET C"}:
        kode = key[-1]
        context.user_data["mode"] = "bundling"
        await update.message.reply_text(
            BUNDLING_DETAIL[kode], reply_markup=DETAIL_KEYBOARD
        )
        return

    await update.message.reply_text(TEXT_UNKNOWN, reply_markup=MENU_KEYBOARD)


def main():
    if not BOT_TOKEN:
        raise SystemExit(
            "BOT_TOKEN kosong. Isi token BotFather di file .env (BOT_TOKEN=...)"
        )
    # Python 3.14+: pastikan MainThread punya event loop
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("BUTICALL bot jalan... Tekan Ctrl+C untuk stop")
    app.run_polling()


if __name__ == "__main__":
    main()