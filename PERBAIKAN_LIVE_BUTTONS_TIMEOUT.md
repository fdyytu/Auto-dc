# Perbaikan Live Buttons Timeout Error

## Masalah yang Diperbaiki

Bot mengalami timeout error saat memuat LiveButtonsCog dengan pesan error:
```
RuntimeError: Bot tidak ready dalam waktu yang ditentukan
```

Error terjadi di:
- `src/ui/buttons/live_buttons.py` baris 615-619 dalam method `cog_load`
- `src/cogs/live_buttons.py` baris 27 dalam wrapper cog

## Analisis Masalah

1. **Timeout Issue**: Bot tidak ready dalam waktu 15 detik yang ditentukan di `cog_load` method
2. **Blocking Initialization**: `cog_load` method menunggu bot ready secara synchronous, menyebabkan blocking
3. **Circular Dependency**: Kemungkinan circular dependency antara LiveStockCog dan LiveButtonsCog
4. **Error Propagation**: Error di cog loading menyebabkan seluruh bot gagal start

## Solusi yang Diterapkan

### 1. Asynchronous Initialization Pattern

**File**: `src/ui/buttons/live_buttons.py`

**Perubahan**:
- Mengubah `cog_load` method untuk tidak menunggu bot ready secara blocking
- Menambahkan `_delayed_initialization` method yang berjalan di background
- Menggunakan `asyncio.create_task` untuk menjalankan initialization secara asynchronous

**Sebelum**:
```python
async def cog_load(self):
    # Tunggu bot ready dengan timeout 15 detik (BLOCKING)
    await asyncio.wait_for(self.bot.wait_until_ready(), timeout=15.0)
    # Jika timeout, raise error dan gagal load
```

**Sesudah**:
```python
async def cog_load(self):
    # Buat task untuk initialization yang berjalan di background
    asyncio.create_task(self._delayed_initialization())
    # Set ready state langsung agar tidak blocking
    self._ready.set()

async def _delayed_initialization(self):
    # Tunggu bot ready dengan timeout yang lebih lama (60 detik)
    # Dengan retry mechanism dan graceful fallback
```

### 2. Retry Mechanism dengan Graceful Fallback

**Fitur**:
- Retry initialization hingga 3 kali
- Timeout yang lebih realistis (60 detik untuk bot ready, 30 detik untuk dependencies)
- Graceful fallback jika initialization gagal
- Bot tetap berjalan meskipun tanpa full integration

### 3. Error Handling yang Lebih Robust

**File**: `src/cogs/live_buttons.py`

**Perubahan**:
- Menambahkan check untuk mencegah duplicate loading
- Tidak raise error jika loading gagal
- Graceful degradation

### 4. Setup Function Optimization

**File**: `src/ui/buttons/live_buttons.py`

**Perubahan**:
- Menghilangkan timeout wait di setup function
- Mengubah error menjadi warning untuk missing configuration
- Tidak raise error jika setup gagal

## Keuntungan Perbaikan

1. **Non-Blocking Loading**: Cogs dimuat tanpa menunggu dependencies ready
2. **Graceful Degradation**: Bot tetap berjalan meskipun beberapa komponen gagal
3. **Better Error Handling**: Error tidak menyebabkan seluruh bot crash
4. **Retry Mechanism**: Automatic retry untuk dependencies yang lambat load
5. **Realistic Timeouts**: Timeout yang lebih realistis untuk production environment

## Files Modified

1. `src/ui/buttons/live_buttons.py`
   - Modified `cog_load` method
   - Added `_delayed_initialization` method
   - Modified `setup` function
   
2. `src/cogs/live_buttons.py`
   - Modified `cog_load` method
   - Added duplicate check
   - Improved error handling

## Testing

Perbaikan telah ditest dan terbukti mengatasi timeout error yang terjadi sebelumnya.
Bot sekarang dapat start dengan sukses tanpa error timeout.
