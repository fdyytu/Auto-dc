# Perbaikan Urutan Loading Cogs dan Circular Error

## Masalah yang Ditemukan

### 1. Urutan Loading Cogs Tidak Tepat
- **Masalah**: Cogs dimuat secara alfabetis, menyebabkan `live_buttons` dimuat sebelum `live_stock`
- **Dampak**: `LiveButtonsCog` menunggu `LiveStockCog` yang belum dimuat, menyebabkan timeout
- **Log Error**: 
  ```
  LiveButtonsCog - INFO - Still waiting for LiveStockCog... attempt 1/60
  LiveButtonsCog - INFO - Still waiting for LiveStockCog... attempt 11/60
  ```

### 2. Circular Error Loop
- **Masalah**: `LiveStockManager` dan `LiveButtonManager` saling memanggil fungsi status update
- **Dampak**: Error loop tak terbatas yang menghabiskan log dan resources
- **Log Error**:
  ```
  ❌ Livestock error: Button error: Livestock error: Button error: ...
  ```

### 3. Timeout Terlalu Lama
- **Masalah**: Timeout 60+ detik untuk waiting dependencies
- **Dampak**: Bot startup lambat dan hanging

## Solusi yang Diterapkan

### 1. Perbaikan Urutan Loading di ModuleLoader

**File**: `src/bot/module_loader.py`

```python
def _discover_cogs(self, cogs_path: Path) -> List[str]:
    """Auto-discovery dengan urutan prioritas"""
    cog_modules = []
    
    # Urutan prioritas loading cogs
    priority_order = [
        'live_stock.py',    # Harus dimuat pertama
        'live_buttons.py',  # Dimuat setelah live_stock
    ]
    
    # Load priority cogs first
    for priority_file in priority_order:
        py_file = cogs_path / priority_file
        if py_file.exists() and self._validate_cog_file(py_file):
            module_name = f"src.cogs.{py_file.stem}"
            cog_modules.append(module_name)
            logger.info(f"🔍 Priority cog ditemukan: {module_name}")
    
    # Load remaining cogs (non-priority)
    # ... rest of the code
    
    return cog_modules  # Tidak di-sort agar urutan prioritas terjaga
```

**Perubahan**:
- ✅ Menambahkan `priority_order` untuk cogs yang harus dimuat dalam urutan tertentu
- ✅ `live_stock.py` dimuat pertama, baru `live_buttons.py`
- ✅ Menghilangkan `sorted()` agar urutan prioritas terjaga

### 2. Perbaikan Circular Error di LiveButtonManager

**File**: `src/ui/buttons/live_buttons.py`

**Sebelum**:
```python
async def _update_status(self, is_healthy: bool, error: str = None):
    # ... update status
    if self.stock_manager and hasattr(self.stock_manager, 'on_button_status_change'):
        await self.stock_manager.on_button_status_change(is_healthy, error)  # CIRCULAR!
```

**Sesudah**:
```python
async def _update_status(self, is_healthy: bool, error: str = None):
    # ... update status
    # Notify livestock manager (tanpa circular call)
    if self.stock_manager and hasattr(self.stock_manager, 'livestock_status'):
        try:
            # Update status langsung tanpa memanggil function
            self.stock_manager.livestock_status['button_error'] = error
            self.stock_manager.livestock_status['button_healthy'] = is_healthy
            self.logger.debug(f"✅ Status synced to livestock manager")
        except Exception as e:
            self.logger.error(f"Error syncing to livestock manager: {e}")
```

**Perubahan**:
- ✅ Menghilangkan pemanggilan `on_button_status_change()`
- ✅ Update status langsung ke `livestock_status` dictionary
- ✅ Menghapus fungsi `on_livestock_status_change()` yang tidak diperlukan

### 3. Perbaikan Circular Error di LiveStockManager

**File**: `src/ui/views/live_stock_view.py`

**Sebelum**:
```python
async def _update_status(self, is_healthy: bool, error: str = None):
    # ... update status
    if self.button_manager and hasattr(self.button_manager, 'on_livestock_status_change'):
        await self.button_manager.on_livestock_status_change(is_healthy, error)  # CIRCULAR!
```

**Sesudah**:
```python
async def _update_status(self, is_healthy: bool, error: str = None):
    # ... update status
    # Notify button manager (tanpa circular call)
    if self.button_manager and hasattr(self.button_manager, 'button_status'):
        try:
            # Update status langsung tanpa memanggil function
            self.button_manager.button_status['livestock_error'] = error
            self.button_manager.button_status['livestock_healthy'] = is_healthy
            self.logger.debug(f"✅ Status synced to button manager")
        except Exception as e:
            self.logger.error(f"Error syncing to button manager: {e}")
```

**Perubahan**:
- ✅ Menghilangkan pemanggilan `on_livestock_status_change()`
- ✅ Update status langsung ke `button_status` dictionary
- ✅ Menghapus fungsi `on_button_status_change()` yang tidak diperlukan

### 4. Pengurangan Timeout

**File**: `src/ui/buttons/live_buttons.py`

```python
async def initialize_dependencies(self) -> bool:
    max_attempts = 15  # Kurangi dari 60 menjadi 15 detik
    # ...
    
async def cog_load(self):
    success = await asyncio.wait_for(
        self.initialize_dependencies(),
        timeout=20.0  # Kurangi dari 70 menjadi 20 detik
    )

# Di setup function
await asyncio.wait_for(
    cog._ready.wait(),
    timeout=25.0  # Kurangi dari 45 menjadi 25 detik
)
```

**Perubahan**:
- ✅ Timeout dependency initialization: 60s → 15s
- ✅ Timeout cog_load: 70s → 20s  
- ✅ Timeout setup: 45s → 25s

## Hasil Perbaikan

### Log Sebelum Perbaikan
```
LiveButtonsCog - INFO - Still waiting for LiveStockCog... attempt 1/60
LiveButtonsCog - INFO - Still waiting for LiveStockCog... attempt 11/60
...
❌ Livestock error: Button error: Livestock error: Button error: ...
(Circular error loop tak terbatas)
```

### Log Sesudah Perbaikan
```
🔍 Priority cog ditemukan: src.cogs.live_stock
🔍 Priority cog ditemukan: src.cogs.live_buttons
✓ src.cogs.live_stock
LiveStockManager - INFO - LiveStockManager is ready
LiveButtonsCog - INFO - Initializing dependencies...
LiveButtonManager - INFO - Stock manager set successfully
✅ LiveStockCog found and connected: LiveStockCog
✅ Dependencies initialized successfully
✓ src.cogs.live_buttons
```

## Manfaat Perbaikan

1. **Startup Lebih Cepat**: Tidak ada lagi waiting 60+ detik
2. **Tidak Ada Circular Error**: Log bersih tanpa error loop
3. **Loading Sequence Benar**: live_stock → live_buttons
4. **Resource Efficient**: Tidak ada infinite loop yang menghabiskan CPU
5. **Maintainable**: Kode lebih mudah dipahami dan di-debug

## Testing

Bot berhasil dijalankan dengan hasil:
- ✅ Urutan loading cogs benar
- ✅ Tidak ada circular error
- ✅ Startup time normal
- ✅ Dependencies terconnect dengan baik
- ✅ Error handling yang proper

## Dependencies Tambahan

Menambahkan `plotly` ke requirements untuk mengatasi warning:
```bash
pip install plotly
```

## Kesimpulan

Perbaikan ini mengatasi masalah fundamental dalam arsitektur loading cogs dan komunikasi antar komponen. Bot sekarang dapat startup dengan normal tanpa error loop dan dengan urutan loading yang benar.
