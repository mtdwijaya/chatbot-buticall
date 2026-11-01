/**
 * BUTICALL — Web App penerima booking dari Telegram bot.
 *
 * Header baris 1 (urutan wajib):
 * Waktu | Nama | Email | WA | Tanggal sewa | Jenis | Ukuran |
 * Durasi (hari) | Harga/hari | Total | Catatan |
 * Telegram ID | Username | Nama Telegram | Status
 *
 * Status enum: Proses | Selesai (kolom O = 15)
 * Jalankan setupStatusValidation() sekali, lalu Deploy New version.
 */

var BOOKING_SECRET = "buticall-booking-1234";
var DEFAULT_ADMIN_EMAIL = "mtiasdw44@gmail.com";

var STATUS_PROSES = "Proses";
var STATUS_SELESAI = "Selesai";
var STATUS_COL = 15; // Kolom O

function setupStatusValidation() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  ensureStatusValidation_(sheet);
}

function ensureStatusValidation_(sheet) {
  var rule = SpreadsheetApp.newDataValidation()
    .requireValueInList([STATUS_PROSES, STATUS_SELESAI], true)
    .setAllowInvalid(false)
    .setHelpText("Pilih: Proses atau Selesai")
    .build();
  sheet.getRange(2, STATUS_COL, 2000, 1).setDataValidation(rule);
}

function formatRp_(n) {
  var num = Number(n);
  if (isNaN(num)) return String(n || "-");
  return (
    "Rp " +
    Math.round(num)
      .toString()
      .replace(/\B(?=(\d{3})+(?!\d))/g, ".")
  );
}

function doPost(e) {
  try {
    var raw = e && e.postData && e.postData.contents ? e.postData.contents : "";
    var data = JSON.parse(raw || "{}");

    if (!data.secret || data.secret !== BOOKING_SECRET) {
      return jsonResponse({ ok: false, error: "Secret tidak valid" });
    }

    var ss = SpreadsheetApp.getActiveSpreadsheet();
    var sheet = ss.getActiveSheet();
    var sheetUrl = ss.getUrl();
    ensureStatusValidation_(sheet);

    var nama = data.nama || "-";
    var email = data.email || "-";
    var wa = data.wa || "-";
    var tanggal = data.tanggal || "-";
    var jenis = data.jenis || "-";
    var ukuran = data.ukuran || "-";
    var durasi = data.durasi || "-";
    var harga = data.harga_per_hari || "";
    var total = data.total || "";
    var catatan = data.catatan || "-";
    var waktu = data.waktu || "-";
    var tgUser = data.telegram_username ? "@" + data.telegram_username : "-";
    var tgName = data.telegram_name || "-";
    var tgId = data.telegram_id || "-";
    var adminWa = data.admin_wa || "-";

    sheet.appendRow([
      data.waktu || "",
      data.nama || "",
      data.email || "",
      data.wa || "",
      data.tanggal || "",
      data.jenis || "",
      data.ukuran || "",
      data.durasi || "",
      data.harga_per_hari || "",
      data.total || "",
      data.catatan || "-",
      data.telegram_id || "",
      data.telegram_username || "",
      data.telegram_name || "",
      STATUS_PROSES,
    ]);

    var toAdmin = (data.admin_email || DEFAULT_ADMIN_EMAIL || "").trim();
    if (toAdmin) {
      sendAdminEmail_({
        to: toAdmin,
        sheetUrl: sheetUrl,
        nama: nama,
        email: email,
        wa: wa,
        tanggal: tanggal,
        jenis: jenis,
        ukuran: ukuran,
        durasi: durasi,
        harga: harga,
        total: total,
        catatan: catatan,
        waktu: waktu,
        tgUser: tgUser,
        tgName: tgName,
        tgId: tgId,
      });
    }

    var toCustomer = (data.email || "").trim();
    if (toCustomer && toCustomer.indexOf("@") !== -1) {
      sendCustomerEmail_({
        to: toCustomer,
        nama: nama,
        tanggal: tanggal,
        jenis: jenis,
        ukuran: ukuran,
        durasi: durasi,
        harga: harga,
        total: total,
        catatan: catatan,
        adminWa: adminWa,
      });
    }

    return jsonResponse({ ok: true });
  } catch (err) {
    return jsonResponse({ ok: false, error: String(err) });
  }
}

function sendAdminEmail_(p) {
  var subject = "[BUTICALL] Booking baru — " + p.nama + " · " + p.tanggal;
  var body = [
    "BUTICALL — Notifikasi Booking",
    "================================",
    "",
    "Ada booking baru dari chatbot.",
    "Status awal: " + STATUS_PROSES,
    "",
    "--- Data pelanggan ---",
    "Nama          : " + p.nama,
    "Email         : " + p.email,
    "WhatsApp      : " + p.wa,
    "Tanggal sewa  : " + p.tanggal,
    "Jenis busana  : " + p.jenis,
    "Ukuran        : " + p.ukuran,
    "Durasi        : " + p.durasi + " hari",
    "Harga/hari    : " + formatRp_(p.harga),
    "Total estimasi: " + formatRp_(p.total),
    "Catatan       : " + p.catatan,
    "",
    "--- Data Telegram ---",
    "Nama Telegram : " + p.tgName,
    "Username      : " + p.tgUser,
    "Telegram ID   : " + p.tgId,
    "Waktu kirim   : " + p.waktu,
    "",
    "--- Tindak lanjut ---",
    "1. Hubungi pelanggan via WhatsApp / email.",
    "2. Konfirmasi ketersediaan & jadwal.",
    "3. Ubah Status di sheet menjadi \"" + STATUS_SELESAI + "\" jika selesai.",
    "",
    "Buka spreadsheet booking:",
    p.sheetUrl,
    "",
    "— Bot BUTICALL",
  ].join("\n");

  var htmlBody = [
    "<div style=\"font-family:Arial,sans-serif;font-size:14px;color:#222;line-height:1.5\">",
    "<h2 style=\"margin:0 0 8px 0\">BUTICALL — Booking Baru</h2>",
    "<p style=\"margin:0 0 16px 0\">Status awal: <strong>" +
      STATUS_PROSES +
      "</strong></p>",
    "<table style=\"border-collapse:collapse;width:100%;max-width:520px\">",
    rowHtml_("Nama", p.nama),
    rowHtml_("Email", p.email),
    rowHtml_("WhatsApp", p.wa),
    rowHtml_("Tanggal sewa", p.tanggal),
    rowHtml_("Jenis busana", p.jenis),
    rowHtml_("Ukuran", p.ukuran),
    rowHtml_("Durasi", String(p.durasi) + " hari"),
    rowHtml_("Harga/hari", formatRp_(p.harga)),
    rowHtml_("Total estimasi", formatRp_(p.total)),
    rowHtml_("Catatan", p.catatan),
    rowHtml_("Nama Telegram", p.tgName),
    rowHtml_("Username", p.tgUser),
    rowHtml_("Telegram ID", String(p.tgId)),
    rowHtml_("Waktu kirim", p.waktu),
    "</table>",
    "<p style=\"margin:16px 0 8px 0\"><strong>Tindak lanjut</strong></p>",
    "<ol style=\"margin:0 0 16px 20px;padding:0\">",
    "<li>Hubungi pelanggan via WhatsApp / email.</li>",
    "<li>Konfirmasi ketersediaan &amp; jadwal.</li>",
    "<li>Ubah Status menjadi <em>" + STATUS_SELESAI + "</em> jika selesai.</li>",
    "</ol>",
    "<p style=\"margin:0 0 4px 0\"><a href=\"" +
      p.sheetUrl +
      "\">Buka spreadsheet booking</a></p>",
    "<p style=\"margin:16px 0 0 0;color:#666;font-size:12px\">— Bot BUTICALL</p>",
    "</div>",
  ].join("");

  MailApp.sendEmail({
    to: p.to,
    subject: subject,
    body: body,
    htmlBody: htmlBody,
  });
}

function sendCustomerEmail_(p) {
  var subject = "Konfirmasi booking BUTICALL — " + p.tanggal;
  var body = [
    "Halo " + p.nama + ",",
    "",
    "Terima kasih! Booking kamu sudah kami terima.",
    "Admin BUTICALL akan menghubungi kamu via WhatsApp untuk konfirmasi.",
    "",
    "--- Ringkasan pesanan ---",
    "Tanggal sewa  : " + p.tanggal,
    "Jenis         : " + p.jenis,
    "Ukuran        : " + p.ukuran,
    "Durasi        : " + p.durasi + " hari",
    "Harga/hari    : " + formatRp_(p.harga),
    "Total estimasi: " + formatRp_(p.total),
    "Catatan       : " + p.catatan,
    "",
    "*Total di atas bersifat estimasi dan belum termasuk DP/biaya tambahan jika ada.",
    "",
    "WhatsApp admin: " + p.adminWa,
    "",
    "Salam,",
    "BUTICALL",
  ].join("\n");

  var htmlBody = [
    "<div style=\"font-family:Arial,sans-serif;font-size:14px;color:#222;line-height:1.5\">",
    "<h2 style=\"margin:0 0 8px 0\">Konfirmasi Booking BUTICALL</h2>",
    "<p>Halo <strong>" + escapeHtml_(p.nama) + "</strong>,</p>",
    "<p>Terima kasih! Booking kamu sudah kami terima. Admin akan menghubungi via WhatsApp untuk konfirmasi.</p>",
    "<table style=\"border-collapse:collapse;width:100%;max-width:520px;margin:16px 0\">",
    rowHtml_("Tanggal sewa", p.tanggal),
    rowHtml_("Jenis", p.jenis),
    rowHtml_("Ukuran", p.ukuran),
    rowHtml_("Durasi", String(p.durasi) + " hari"),
    rowHtml_("Harga/hari", formatRp_(p.harga)),
    rowHtml_("Total estimasi", formatRp_(p.total)),
    rowHtml_("Catatan", p.catatan),
    "</table>",
    "<p style=\"color:#555;font-size:13px\">*Total bersifat estimasi dan belum termasuk DP/biaya tambahan jika ada.</p>",
    "<p>WhatsApp admin: <strong>" + escapeHtml_(p.adminWa) + "</strong></p>",
    "<p style=\"margin:16px 0 0 0;color:#666;font-size:12px\">Salam,<br>BUTICALL</p>",
    "</div>",
  ].join("");

  MailApp.sendEmail({
    to: p.to,
    subject: subject,
    body: body,
    htmlBody: htmlBody,
  });
}

function escapeHtml_(value) {
  return String(value || "-")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function rowHtml_(label, value) {
  return (
    "<tr>" +
    "<td style=\"padding:6px 10px 6px 0;color:#555;vertical-align:top;width:140px\">" +
    label +
    "</td>" +
    "<td style=\"padding:6px 0;vertical-align:top\"><strong>" +
    escapeHtml_(value) +
    "</strong></td>" +
    "</tr>"
  );
}

function doGet() {
  return ContentService.createTextOutput(
    "BUTICALL booking webhook aktif. Gunakan POST."
  ).setMimeType(ContentService.MimeType.TEXT);
}

function jsonResponse(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(
    ContentService.MimeType.JSON
  );
}
