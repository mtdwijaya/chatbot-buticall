# Setup Google Sheet + Email (Apps Script)

Sheet contoh:
https://docs.google.com/spreadsheets/d/19Xbe0GHQ0Czu3nmSdp9IxpIDf40x9rOUcqq_WYpWm2E/edit

## 1. Header baris 1 (wajib urutan ini)

Tempel di **A1** (satu baris, dipisah Tab):

```
Waktu	Nama	Email	WA	Tanggal sewa	Jenis	Ukuran	Durasi (hari)	Harga/hari	Total	Catatan	Telegram ID	Username	Nama Telegram	Status
```

Atau impor [`headers.csv`](headers.csv).

Jika sheet lama masih pakai kolom lama: **ganti seluruh baris 1** dengan header di atas (kolom baru: Email, Durasi, Harga/hari, Total).

## 2. Pasang script
1. Sheet → **Extensi → Apps Script**
2. Tempel isi [`Code.gs`](Code.gs)
3. Samakan `BOOKING_SECRET` dengan `.env`
4. Jalankan `setupStatusValidation` sekali (dropdown Status = Proses | Selesai di kolom O)
5. **Deploy → Manage deployments → Edit → New version → Deploy**

## 3. Isi `.env` bot
```env
BOOKING_WEBHOOK_URL=https://script.google.com/macros/s/XXXX/exec
BOOKING_SECRET=buticall-booking-1234
ADMIN_EMAIL=email.admin@gmail.com
ADMIN_WA=08xxxxxxxxxx
```

## 4. Restart bot
```powershell
python bot.py
```

## Alur booking (Telegram)
Nama → Email → WA → Tanggal → Jenis → Durasi (1/2/3/Lainnya) → Ukuran → Catatan → YA

Setelah YA:
- Baris baru di Sheet (Status: **Proses**)
- Email ke **admin** (notifikasi + link sheet)
- Email ke **pemesan** (konfirmasi + total estimasi)
