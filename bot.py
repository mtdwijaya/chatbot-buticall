import asyncio
import os
import re
from datetime import datetime
from dotenv import load_dotenv
import httpx
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WA_ADMIN = os.getenv("ADMIN_WA", "082281550251")
JAM_OPS = "09.00–21.00 WIB"
BOOKING_WEBHOOK_URL = os.getenv("BOOKING_WEBHOOK_URL", "").strip()
BOOKING_SECRET = os.getenv("BOOKING_SECRET", "").strip()
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "").strip()

JENIS_MAP = {
    "A": "Kebaya modern",
    "B": "Gaun pesta",
    "C": "Gaun wisuda",
    "D": "Pakaian formal",
}

HARGA_PER_HARI = {
    "A": 150_000,
    "B": 175_000,
    "C": 200_000,
    "D": 150_000,
}

DURASI_TOMBOL = {
    "1 HARI": 1,
    "2 HARI": 2,
    "3 HARI": 3,
}


def kb(*rows: list[str]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton(label) for label in row] for row in rows],
        resize_keyboard=True,
    )


def format_rp(amount: int) -> str:
    return f"Rp {amount:,}".replace(",", ".")


MENU_KEYBOARD = kb(["1", "2", "3"], ["4", "5"], ["MENU"])
KOLEKSI_KEYBOARD = kb(["A", "B", "C", "D"], ["MENU"])
HARGA_KEYBOARD = kb(["A", "B", "C", "D"], ["1", "5", "MENU"])
DETAIL_KEYBOARD = kb(["3", "4", "5"], ["MENU"])
STOK_KEYBOARD = kb(["5", "MENU"])
ADMIN_KEYBOARD = kb(["MENU"])

BOOKING_CANCEL_KEYBOARD = kb(["BATAL", "MENU"])
BOOKING_JENIS_KEYBOARD = kb(["A", "B", "C", "D"], ["BATAL", "MENU"])
BOOKING_DURASI_KEYBOARD = kb(["1 hari", "2 hari", "3 hari"], ["Lainnya"], ["BATAL", "MENU"])
BOOKING_UKURAN_KEYBOARD = kb(["S", "M", "L"], ["XL", "XXL"], ["BATAL", "MENU"])
UKURAN_OPSI = {"S", "M", "L", "XL", "XXL"}
BOOKING_CATATAN_KEYBOARD = kb(["LEWATI"], ["BATAL", "MENU"])
BOOKING_CONFIRM_KEYBOARD = kb(["YA", "BATAL"], ["MENU"])

TEXT_MENU = f"""Halo! Selamat datang di BUTICALL
Sewa busana desain sendiri untuk wisuda, pesta, dan acara formal.

Pilih menu:
1 Booking
2 Info koleksi
3 Cek harga sewa
4 Cek ketersediaan
5 Hubungi admin

Tekan tombol di bawah, atau ketik angka 1-5.
Tekan MENU untuk kembali."""

TEXT_KOLEKSI = """Koleksi BUTICALL:
A Kebaya modern
B Gaun pesta
C Gaun wisuda
D Pakaian formal

Tekan A/B/C/D di bawah, atau MENU untuk kembali."""

TEXT_HARGA = """Harga sewa BUTICALL (/hari):
A Kebaya modern : Rp 150.000 /hari
B Gaun pesta    : Rp 175.000 /hari
C Gaun wisuda   : Rp 200.000 /hari
D Formal        : Rp 150.000 /hari

Tekan A–D untuk detail, atau 1 / 5 / MENU."""

TEXT_STOK = """Cek ketersediaan — balas dengan format:

NAMA / TANGGAL / UKURAN / JENIS

Contoh:
Sinta / 15 Juni 2026 / M / Gaun wisuda

Admin akan konfirmasi stok.
Tekan 5 untuk hubungi admin sekarang."""

TEXT_ADMIN = f"""Admin BUTICALL
WhatsApp: {WA_ADMIN}
Jam: {JAM_OPS}

Siapkan: nama, tanggal sewa, acara, size, model.
Tekan MENU untuk kembali."""

DETAIL = {
    "A": """Kebaya modern BUTICALL
• Size: S, M, L, XL, XXL
• Cocok: wisuda, kondangan, formal
• Harga: Rp 150.000 /hari

Tekan 3 harga | 4 stok | 5 Hubungi Admin | MENU""",
    "B": """Gaun pesta BUTICALL
• Size: S, M, L, XL, XXL
• Cocok: pesta, dinner, pemotretan
• Harga: Rp 175.000 /hari

Tekan 3 harga | 4 stok | 5 Hubungi Admin | MENU""",
    "C": """Gaun wisuda BUTICALL
• Size: S, M, L, XL, XXL
• Cocok: wisuda & foto studio
• Harga: Rp 200.000 /hari

Tekan 3 harga | 4 stok | 5 Hubungi Admin | MENU""",
    "D": """Pakaian formal BUTICALL
• Size: S, M, L, XL, XXL
• Cocok: acara formal / meeting
• Harga: Rp 150.000 /hari

Tekan 3 harga | 4 stok | 5 Hubungi Admin | MENU""",
}

TEXT_UNKNOWN = """Maaf, aku belum paham.
Aku chatbot menu BUTICALL.

Tekan MENU
1 Booking | 2 Koleksi | 3 Harga
4 Ketersediaan | 5 Hubungi Admin"""

MENU_ROUTES = {
    "2": ("koleksi", TEXT_KOLEKSI, KOLEKSI_KEYBOARD),
    "3": ("harga", TEXT_HARGA, HARGA_KEYBOARD),
    "4": ("stok", TEXT_STOK, STOK_KEYBOARD),
    "5": ("admin", TEXT_ADMIN, ADMIN_KEYBOARD),
}


def clear_booking(context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.pop("booking_step", None)
    context.user_data.pop("booking_data", None)


def is_valid_email(value: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value.strip()))


def apply_durasi(data: dict, hari: int) -> None:
    kode = data.get("jenis_kode", "A")
    harga = HARGA_PER_HARI.get(kode, 150_000)
    data["durasi"] = hari
    data["harga_per_hari"] = harga
    data["total"] = harga * hari


def booking_summary(data: dict) -> str:
    return (
        "Cek data booking kamu:\n\n"
        f"Nama: {data.get('nama', '-')}\n"
        f"Email: {data.get('email', '-')}\n"
        f"WA: {data.get('wa', '-')}\n"
        f"Tanggal sewa: {data.get('tanggal', '-')}\n"
        f"Jenis: {data.get('jenis', '-')}\n"
        f"Durasi: {data.get('durasi', '-')} hari\n"
        f"Harga/hari: {format_rp(int(data.get('harga_per_hari', 0)))}\n"
        f"Total estimasi: {format_rp(int(data.get('total', 0)))}\n"
        f"Ukuran: {data.get('ukuran', '-')}\n"
        f"Catatan: {data.get('catatan', '-')}\n\n"
        "*Total bersifat estimasi (belum termasuk DP/biaya tambahan jika ada).\n\n"
        "Tekan YA untuk kirim, atau BATAL untuk batalkan."
    )


async def after_durasi_set(update: Update, context: ContextTypes.DEFAULT_TYPE, data: dict) -> None:
    context.user_data["booking_step"] = "ukuran"
    await update.message.reply_text(
        "Estimasi biaya:\n"
        f"{format_rp(int(data['harga_per_hari']))} × {data['durasi']} hari "
        f"= {format_rp(int(data['total']))}\n"
        "(Estimasi — belum termasuk DP/biaya tambahan jika ada.)\n\n"
        "Pilih ukuran:\n"
        "S — Small\n"
        "M — Medium\n"
        "L — Large\n"
        "XL — Extra Large\n"
        "XXL — Double Extra Large\n\n"
        "Tekan tombol di bawah.",
        reply_markup=BOOKING_UKURAN_KEYBOARD,
    )


async def submit_booking(payload: dict) -> tuple[bool, str]:
    if not BOOKING_WEBHOOK_URL:
        return False, "Webhook booking belum dikonfigurasi (BOOKING_WEBHOOK_URL)."
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                BOOKING_WEBHOOK_URL, json=payload, follow_redirects=False
            )
            if resp.status_code in {301, 302, 303, 307, 308}:
                loc = resp.headers.get("Location")
                if not loc:
                    return True, "ok"
                resp = await client.get(loc, follow_redirects=True)

        if resp.status_code == 405:
            return True, "ok"

        if resp.status_code >= 400:
            return False, f"Server balas error ({resp.status_code})."

        try:
            data = resp.json()
            if isinstance(data, dict):
                if data.get("ok") is True:
                    return True, "ok"
                if data.get("ok") is False:
                    return False, str(data.get("error") or data)[:200]
        except Exception:
            pass

        body = (resp.text or "").strip()
        if '"ok":true' in body.replace(" ", "").lower():
            return True, "ok"
        if '"ok":false' in body.replace(" ", "").lower() or (
            "error" in body.lower() and "ok" not in body.lower()
        ):
            return False, body[:200]
        return True, "ok"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)[:200]


async def start_booking(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["mode"] = "booking"
    context.user_data["booking_step"] = "nama"
    context.user_data["booking_data"] = {}
    await update.message.reply_text(
        "Form booking BUTICALL\n\n"
        "Ketik nama lengkap kamu.\n"
        "Tekan BATAL atau MENU untuk batal.",
        reply_markup=BOOKING_CANCEL_KEYBOARD,
    )


async def handle_booking(
    update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, key: str
) -> None:
    step = context.user_data.get("booking_step")
    data = context.user_data.setdefault("booking_data", {})

    if key in {"BATAL", "MENU"}:
        clear_booking(context)
        context.user_data["mode"] = "menu"
        await update.message.reply_text(
            "Booking dibatalkan.\n\n" + TEXT_MENU, reply_markup=MENU_KEYBOARD
        )
        return

    if step == "nama":
        data["nama"] = text
        context.user_data["booking_step"] = "email"
        await update.message.reply_text(
            "Ketik email aktif kamu (untuk konfirmasi booking).\n"
            "Contoh: nama@gmail.com",
            reply_markup=BOOKING_CANCEL_KEYBOARD,
        )
        return

    if step == "email":
        email = text.strip()
        if not is_valid_email(email):
            await update.message.reply_text(
                "Format email belum benar. Coba lagi (contoh: nama@gmail.com).",
                reply_markup=BOOKING_CANCEL_KEYBOARD,
            )
            return
        data["email"] = email
        context.user_data["booking_step"] = "wa"
        await update.message.reply_text(
            "Ketik nomor WhatsApp aktif (contoh: 08xxxxxxxxxx).",
            reply_markup=BOOKING_CANCEL_KEYBOARD,
        )
        return

    if step == "wa":
        data["wa"] = text
        context.user_data["booking_step"] = "tanggal"
        await update.message.reply_text(
            "Ketik tanggal sewa (contoh: 15 Juni 2026).",
            reply_markup=BOOKING_CANCEL_KEYBOARD,
        )
        return

    if step == "tanggal":
        data["tanggal"] = text
        context.user_data["booking_step"] = "jenis"
        await update.message.reply_text(
            "Pilih jenis busana:\n"
            "A Kebaya modern — Rp 150.000 /hari\n"
            "B Gaun pesta — Rp 175.000 /hari\n"
            "C Gaun wisuda — Rp 200.000 /hari\n"
            "D Pakaian formal — Rp 150.000 /hari",
            reply_markup=BOOKING_JENIS_KEYBOARD,
        )
        return

    if step == "jenis":
        if key not in JENIS_MAP:
            await update.message.reply_text(
                "Pilih jenis dengan tombol A/B/C/D.",
                reply_markup=BOOKING_JENIS_KEYBOARD,
            )
            return
        data["jenis_kode"] = key
        data["jenis"] = JENIS_MAP[key]
        context.user_data["booking_step"] = "durasi"
        await update.message.reply_text(
            f"Jenis: {data['jenis']}\n"
            f"Harga: {format_rp(HARGA_PER_HARI[key])} /hari\n\n"
            "Sewa berapa lama?\n"
            "Pilih tombol, atau tekan Lainnya untuk ketik jumlah hari.",
            reply_markup=BOOKING_DURASI_KEYBOARD,
        )
        return

    if step == "durasi":
        if key == "LAINNYA":
            context.user_data["booking_step"] = "durasi_custom"
            await update.message.reply_text(
                "Ketik jumlah hari sewa (angka, minimal 1).\nContoh: 5",
                reply_markup=BOOKING_CANCEL_KEYBOARD,
            )
            return
        if key in DURASI_TOMBOL:
            apply_durasi(data, DURASI_TOMBOL[key])
            await after_durasi_set(update, context, data)
            return
        await update.message.reply_text(
            "Pilih lama sewa: 1 hari / 2 hari / 3 hari, atau Lainnya.",
            reply_markup=BOOKING_DURASI_KEYBOARD,
        )
        return

    if step == "durasi_custom":
        if not text.isdigit() or int(text) < 1:
            await update.message.reply_text(
                "Masukkan angka hari yang valid (minimal 1).",
                reply_markup=BOOKING_CANCEL_KEYBOARD,
            )
            return
        apply_durasi(data, int(text))
        await after_durasi_set(update, context, data)
        return

    if step == "ukuran":
        if key not in UKURAN_OPSI:
            await update.message.reply_text(
                "Pilih ukuran dengan tombol S / M / L / XL / XXL.",
                reply_markup=BOOKING_UKURAN_KEYBOARD,
            )
            return
        data["ukuran"] = key
        context.user_data["booking_step"] = "catatan"
        await update.message.reply_text(
            "Ketik catatan (acara, fitting, dll.) atau tekan LEWATI.",
            reply_markup=BOOKING_CATATAN_KEYBOARD,
        )
        return

    if step == "catatan":
        data["catatan"] = "-" if key == "LEWATI" else text
        context.user_data["booking_step"] = "confirm"
        await update.message.reply_text(
            booking_summary(data),
            reply_markup=BOOKING_CONFIRM_KEYBOARD,
        )
        return

    if step == "confirm":
        if key != "YA":
            await update.message.reply_text(
                "Tekan YA untuk kirim, atau BATAL untuk batalkan.",
                reply_markup=BOOKING_CONFIRM_KEYBOARD,
            )
            return

        user = update.effective_user
        payload = {
            "secret": BOOKING_SECRET,
            "admin_email": ADMIN_EMAIL,
            "admin_wa": WA_ADMIN,
            "waktu": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "nama": data.get("nama", ""),
            "email": data.get("email", ""),
            "wa": data.get("wa", ""),
            "tanggal": data.get("tanggal", ""),
            "jenis": data.get("jenis", ""),
            "ukuran": data.get("ukuran", ""),
            "durasi": data.get("durasi", ""),
            "harga_per_hari": data.get("harga_per_hari", ""),
            "total": data.get("total", ""),
            "catatan": data.get("catatan", "-"),
            "telegram_id": user.id if user else "",
            "telegram_username": (user.username or "") if user else "",
            "telegram_name": (user.full_name or "") if user else "",
        }

        await update.message.reply_text("Mengirim booking...")
        ok, err = await submit_booking(payload)
        if not ok:
            await update.message.reply_text(
                "Gagal mengirim booking. Coba tekan YA lagi, atau hubungi admin.\n"
                f"Detail: {err}\n\n"
                f"WA admin: {WA_ADMIN}",
                reply_markup=BOOKING_CONFIRM_KEYBOARD,
            )
            return

        clear_booking(context)
        context.user_data["mode"] = "menu"
        await update.message.reply_text(
            "Booking diterima. Data sudah masuk ke sistem.\n"
            f"Kami juga mengirim konfirmasi ke email: {payload['email']}\n"
            f"Admin akan konfirmasi via WA: {WA_ADMIN}\n\n"
            + TEXT_MENU,
            reply_markup=MENU_KEYBOARD,
        )
        return

    clear_booking(context)
    context.user_data["mode"] = "menu"
    await update.message.reply_text(TEXT_MENU, reply_markup=MENU_KEYBOARD)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clear_booking(context)
    context.user_data["mode"] = "menu"
    await update.message.reply_text(TEXT_MENU, reply_markup=MENU_KEYBOARD)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text:
        return
    key = text.upper()
    mode = context.user_data.get("mode", "menu")

    if mode == "booking":
        await handle_booking(update, context, text, key)
        return

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
        clear_booking(context)
        context.user_data["mode"] = "menu"
        await update.message.reply_text(TEXT_MENU, reply_markup=MENU_KEYBOARD)
        return

    if key == "1":
        await start_booking(update, context)
        return

    if key in MENU_ROUTES:
        new_mode, body, keyboard = MENU_ROUTES[key]
        context.user_data["mode"] = new_mode
        await update.message.reply_text(body, reply_markup=keyboard)
        return

    if key in DETAIL:
        await update.message.reply_text(DETAIL[key], reply_markup=DETAIL_KEYBOARD)
        return

    await update.message.reply_text(TEXT_UNKNOWN, reply_markup=MENU_KEYBOARD)


def main():
    if not BOT_TOKEN:
        raise SystemExit(
            "BOT_TOKEN kosong. Isi token BotFather di file .env (BOT_TOKEN=...)"
        )
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("BUTICALL bot jalan... Tekan Ctrl+C untuk stop")
    if not BOOKING_WEBHOOK_URL:
        print("Peringatan: BOOKING_WEBHOOK_URL belum diisi — booking tidak bisa dikirim.")
    app.run_polling()


if __name__ == "__main__":
    main()
