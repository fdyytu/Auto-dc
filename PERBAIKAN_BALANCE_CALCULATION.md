# Perbaikan Sistem Balance Calculation

## Masalah yang Dilaporkan

User melaporkan masalah dengan sistem balance:

1. **Menambah balance 250 WL** → Hasil: `2 DL 50 WL` ✅ (benar)
2. **Mengurangi balance 75 WL** → Hasil: `2 DL` ❌ (salah, seharusnya `1 DL 75 WL`)
3. **Pembelian di live stock** → Error "saldo tidak mencukupi" padahal balance menunjukkan `2 DL` ❌

## Root Cause Analysis

### Masalah Utama
- Command `removebal` hanya mengurangi dari tipe currency yang spesifik (WL/DL/BGL)
- Tidak ada konversi otomatis saat pengurangan balance
- Validasi balance di live stock tidak sinkron dengan display balance

### Contoh Masalah
```
Balance saat ini: 2 DL 50 WL (= 250 WL total)
Command: removebal 75 WL

Metode lama (salah):
- Kurangi 75 dari WL: 50 - 75 = -25 → 0 WL (karena max(0, -25))
- DL tetap: 2 DL
- Hasil: 2 DL 0 WL (= 200 WL total) ❌

Metode baru (benar):
- Total WL saat ini: 250 WL
- Kurangi 75: 250 - 75 = 175 WL
- Konversi kembali: 175 WL = 1 DL 75 WL
- Hasil: 1 DL 75 WL (= 175 WL total) ✅
```

## Perbaikan yang Dilakukan

### 1. File: `src/cogs/admin_balance.py`

**Perbaikan command `removebal`:**
- Ambil balance saat ini terlebih dahulu
- Konversi amount ke WL equivalent
- Validasi apakah balance mencukupi
- Hitung total WL baru setelah pengurangan
- Konversi kembali ke format balance yang tepat
- Update dengan difference yang dihitung

**Kode baru:**
```python
# Get current balance first
current_response = await self.balance_service.get_balance(growid)
current_balance = current_response.data

# Convert amount to WL equivalent for calculation
if balance_type == "WL":
    wl_equivalent = validated_amount
elif balance_type == "DL":
    wl_equivalent = validated_amount * 100  # 1 DL = 100 WL
elif balance_type == "BGL":
    wl_equivalent = validated_amount * 10000  # 1 BGL = 10000 WL

# Calculate new total WL after reduction
new_total_wl = current_balance.total_wl() - wl_equivalent

# Convert back to proper balance format
new_balance = Balance.from_wl(new_total_wl)

# Calculate the difference to apply
wl_diff = new_balance.wl - current_balance.wl
dl_diff = new_balance.dl - current_balance.dl
bgl_diff = new_balance.bgl - current_balance.bgl
```

### 2. File: `src/services/balance_service.py`

**Perbaikan normalisasi balance:**
- Pastikan normalisasi selalu dilakukan setelah update
- Tambahkan normalisasi ganda untuk memastikan konsistensi

**Kode baru:**
```python
# Always normalize the final balance to ensure proper currency conversion
normalized_new_balance = self.normalize_balance(normalized_new_balance)
```

## Testing dan Verifikasi

### Test Scenarios
```
1. Menambah 250 WL:
   Balance awal: 0 WL
   Setelah +250 WL: 2 DL, 50 WL ✅

2. Mengurangi 75 WL dari 2 DL 50 WL:
   Balance saat ini: 2 DL, 50 WL (250 WL total)
   Metode lama (salah): 2 DL (200 WL total) ❌
   Metode baru (benar): 1 DL, 75 WL (175 WL total) ✅

3. Verifikasi pembelian dengan 2 DL:
   Balance: 2 DL (200 WL equivalent)
   Dapat membeli produk seharga 150 WL ✅
   Balance setelah beli: 50 WL ✅
```

## Manfaat Perbaikan

1. **Konsistensi Balance**: Display balance sekarang konsisten dengan perhitungan internal
2. **Pengurangan Balance yang Benar**: Command `removebal` sekarang mengkonversi currency dengan benar
3. **Pembelian Berfungsi**: Live stock tidak lagi error "saldo tidak mencukupi" untuk balance yang valid
4. **Validasi yang Tepat**: Balance validation sekarang menggunakan total WL equivalent

## Cara Penggunaan

### Command `removebal` yang Diperbaiki
```
# Mengurangi 75 WL dari balance user
!removebal username 75 WL

# Mengurangi 1 DL dari balance user  
!removebal username 1 DL

# Mengurangi 1 BGL dari balance user
!removebal username 1 BGL
```

### Output yang Diperbaiki
```
Balance berhasil dikurangi!
User: username
Dikurangi: 75 WL
Balance sebelum: 2 DL, 50 WL
Balance sekarang: 1 DL, 75 WL
```

## Backward Compatibility

- Semua command existing tetap berfungsi
- Format balance display tetap sama
- API balance service tetap kompatibel
- Database schema tidak berubah

## Files yang Dimodifikasi

1. `src/cogs/admin_balance.py` - Perbaikan command removebal
2. `src/services/balance_service.py` - Perbaikan normalisasi balance

## Commit Information

- **Branch**: `fix-balance-calculation-issue`
- **Commit**: `91a7409`
- **Status**: ✅ Tested dan verified
