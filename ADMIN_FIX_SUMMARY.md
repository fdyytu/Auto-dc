# Perbaikan Admin ID Detection dan Command Restart

## Masalah yang Diperbaiki

### 1. Bug Deteksi Admin ID
**Masalah:** Bot tidak mendeteksi admin ID dari config.json karena bug dalam logika pengecekan admin role.

**Lokasi:** `src/cogs/admin.py` - method `cog_check()`

**Perbaikan:**
- Mengubah variabel `admin_roles` menjadi `admin_role_id` untuk clarity
- Memperbaiki logika pengecekan: `if admin_roles in user_roles:` → `if admin_role_id in user_role_ids:`
- Sebelumnya membandingkan integer dengan list, sekarang membandingkan integer dengan integer

### 2. Penambahan Command !restart
**Fitur Baru:** Command `!restart` untuk me-restart bot server

**Implementasi:**
- Command dengan konfirmasi keamanan (user harus ketik 'ya' atau 'yes')
- Timeout 30 detik untuk konfirmasi
- Logging aktivitas restart
- Cleanup yang proper sebelum restart
- Menggunakan `os.execv()` untuk restart yang aman

## Konfigurasi Admin

### Admin ID di config.json
```json
{
    "admin_id": "1035189920488235120",
    "roles": {
        "admin": "1346120330254483527"
    }
}
```

### Cara Kerja Deteksi Admin
Bot akan mengenali user sebagai admin jika:
1. **User ID** sama dengan `admin_id` di config.json, ATAU
2. **User memiliki role** dengan ID yang sama dengan `roles.admin` di config.json

## Penggunaan Command !restart

```
!restart
```

Bot akan menampilkan konfirmasi:
- Ketik `ya` atau `yes` untuk melanjutkan restart
- Ketik `tidak` atau `no` untuk membatalkan
- Timeout 30 detik jika tidak ada respon

## Testing

Untuk menguji perbaikan:

1. **Test Admin Detection:**
   - Gunakan akun dengan ID `1035189920488235120`
   - Atau akun dengan role admin ID `1346120330254483527`
   - Coba command admin seperti `!addproduct`

2. **Test Restart Command:**
   - Gunakan `!restart` sebagai admin
   - Konfirmasi dengan `ya`
   - Bot akan restart otomatis

## File yang Diubah

- `src/cogs/admin.py`: Perbaikan admin detection + command restart
- Import `asyncio` ditambahkan untuk restart functionality

## Commit Info

Branch: `fix-admin-detection-and-restart`
Commit: `b79b67a`
