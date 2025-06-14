# 🔥 Hot Reload System - Panduan Penggunaan

## Deskripsi
Fitur Hot Reload memungkinkan bot untuk secara otomatis memuat ulang file dan folder ketika ada perubahan, tanpa perlu me-restart seluruh sistem bot.

## Fitur Utama

### ✨ Auto Detection
- **File Monitoring**: Memantau perubahan pada file `.py` di folder yang ditentukan
- **Real-time Reload**: Reload otomatis ketika file dimodifikasi, dibuat, atau dihapus
- **Smart Filtering**: Mengabaikan file yang tidak perlu (cache, log, dll)

### 📁 Folder yang Dipantau
- `cogs/` - Discord bot cogs/extensions
- `services/` - Business logic services
- `handlers/` - Command dan event handlers
- `utils/` - Utility functions
- `ui/` - User interface components
- `database/` - Database models dan repositories
- `business/` - Business logic modules
- `data/` - Data models

### ⚙️ Konfigurasi
Konfigurasi hot reload dapat diatur di `config.json`:

```json
{
  "hot_reload": {
    "enabled": true,
    "watch_directories": ["cogs", "services", "handlers", "utils", "ui", "database", "business", "data"],
    "watch_extensions": [".py"],
    "ignore_patterns": ["__pycache__", "*.pyc", "*.log", ".git"],
    "reload_delay": 1.0,
    "auto_reload_cogs": true,
    "log_reloads": true
  }
}
```

## Commands Admin

### `!reload` - Menu utama
Menampilkan daftar semua commands hot reload yang tersedia.

### `!reload status` - Cek Status
Menampilkan status hot reload system:
- Status aktif/tidak aktif
- Jumlah direktori yang dipantau
- Jumlah extensions yang dimuat
- Konfigurasi detail

### `!reload toggle` - Toggle On/Off
Mengaktifkan atau menonaktifkan hot reload system.

### `!reload cog <nama>` - Reload Cog Tertentu
Reload cog/extension tertentu secara manual.

Contoh:
```
!reload cog admin
!reload cog cogs.leveling
```

### `!reload all` - Reload Semua Cogs
Reload semua cogs yang dimuat secara bersamaan.

## Cara Kerja

### 1. File Monitoring
- Menggunakan library `watchdog` untuk memantau perubahan file
- Mendeteksi event: create, modify, delete
- Filter berdasarkan ekstensi dan pattern yang diabaikan

### 2. Auto Reload Process
1. **Deteksi Perubahan** → File change terdeteksi
2. **Delay Processing** → Tunggu 1 detik (configurable) untuk menghindari multiple reload
3. **Module Classification** → Tentukan apakah file adalah cog atau module biasa
4. **Reload Execution** → Jalankan reload sesuai tipe module
5. **Logging** → Log hasil reload (sukses/gagal)

### 3. Cog vs Module Handling
- **Cogs** (`cogs.*`): Menggunakan `bot.reload_extension()`
- **Modules** (lainnya): Menggunakan `importlib.reload()`

## Keuntungan

### 🚀 Development Speed
- Tidak perlu restart bot untuk testing perubahan
- Instant feedback saat development
- Workflow yang lebih efisien

### 🛡️ Stability
- Bot tetap online dan connected
- Tidak kehilangan state/session
- User experience tidak terganggu

### 📊 Monitoring
- Log detail untuk setiap reload
- Status monitoring via commands
- Error handling yang robust

## Best Practices

### ✅ Do's
- Test perubahan di development environment dulu
- Monitor log untuk memastikan reload berhasil
- Gunakan `!reload status` untuk cek system health
- Backup file penting sebelum perubahan besar

### ❌ Don'ts
- Jangan edit file core system (bot.py, main.py) saat production
- Hindari perubahan yang membutuhkan restart database
- Jangan disable hot reload di production tanpa alasan kuat

## Troubleshooting

### Hot Reload Tidak Berfungsi
1. Cek status: `!reload status`
2. Pastikan konfigurasi benar di `config.json`
3. Cek log untuk error messages
4. Restart hot reload: `!reload toggle` (off → on)

### Reload Gagal
1. Cek syntax error di file yang diubah
2. Pastikan dependencies tersedia
3. Cek log error untuk detail
4. Manual reload: `!reload cog <nama>`

### Performance Issues
1. Kurangi jumlah direktori yang dipantau
2. Tambah pattern ignore untuk file yang tidak perlu
3. Increase reload delay di config

## Technical Details

### Dependencies
- `watchdog>=3.0.0` - File system monitoring
- `python-dotenv>=1.0.0` - Environment variables

### Files Modified
- `core/hot_reload.py` - Hot reload manager
- `core/bot.py` - Integration dengan bot
- `cogs/admin.py` - Admin commands
- `config.json` - Configuration
- `requirements.txt` - Dependencies

### Architecture
```
HotReloadManager
├── HotReloadHandler (watchdog)
├── File Change Detection
├── Module Classification
├── Reload Execution
└── Status Monitoring
```

## Examples

### Menambah Command Baru
1. Edit file cog (misal: `cogs/admin.py`)
2. Tambah command baru
3. Save file
4. Hot reload otomatis mendeteksi dan reload cog
5. Command baru langsung tersedia

### Mengubah Service Logic
1. Edit file service (misal: `services/user_service.py`)
2. Ubah business logic
3. Save file
4. Hot reload otomatis reload module
5. Logic baru langsung aktif

### Testing Hot Reload
```bash
# Jalankan test script
python3 test_hot_reload.py

# Edit file saat script berjalan untuk melihat hot reload bekerja
```

---

**🎉 Hot Reload System siap digunakan!**

Dengan fitur ini, development bot Discord menjadi lebih efisien dan produktif. Bot dapat terus berjalan normal sambil menerima update code secara real-time.
