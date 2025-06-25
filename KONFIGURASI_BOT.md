# Konfigurasi Bot Discord

## Sistem Konfigurasi Hybrid

Bot ini menggunakan sistem konfigurasi hybrid yang menggabungkan:
- **config.json** untuk konfigurasi non-sensitif
- **Environment Variables** untuk data sensitif (token)

## Cara Kerja

### 1. Token Bot (Sensitif)
- **HARUS** disimpan di environment variable `DISCORD_TOKEN`
- **TIDAK** disimpan di config.json untuk keamanan
- Bot akan otomatis membaca dari environment variable

### 2. Konfigurasi Lainnya (Non-sensitif)
- Disimpan di `config.json`
- Meliputi: guild_id, channel_id, role_id, cooldowns, permissions

## Setup Environment Variables

### Untuk Development:
1. Copy `.env.example` ke `.env`
2. Isi `DISCORD_TOKEN=your_actual_bot_token`
3. Jalankan bot dengan `python main.py`

### Untuk Production:
Set environment variable di hosting platform:
```bash
export DISCORD_TOKEN=your_actual_bot_token
```

## Struktur config.json

```json
{
    "_comment": "Token bot dimuat dari environment variable DISCORD_TOKEN",
    "token": "",
    "guild_id": "your_guild_id",
    "admin_id": "your_admin_id",
    "channels": {
        "welcome": "channel_id",
        "logs": "channel_id"
    },
    "roles": {
        "admin": "role_id",
        "moderator": "role_id"
    }
}
```

## Validasi Konfigurasi

Bot akan:
1. ✅ Memuat config.json
2. ✅ Mengecek DISCORD_TOKEN di environment
3. ✅ Validasi semua konfigurasi yang diperlukan
4. ❌ Gagal start jika token tidak ditemukan

## Troubleshooting

### Error: "Token bot tidak ditemukan!"
- Pastikan DISCORD_TOKEN sudah di-set di environment variables
- Cek file .env sudah ada dan berisi token yang benar

### Error: "Kunci konfigurasi yang hilang"
- Pastikan semua field wajib ada di config.json
- Cek format JSON valid (tidak ada trailing comma, dll)
