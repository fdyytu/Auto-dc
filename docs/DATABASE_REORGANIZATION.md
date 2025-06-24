# Reorganisasi Database dan File Structure

## Perubahan yang Dilakukan

### 1. Database Models
Dibuat models lengkap di `database/models/`:
- `user.py` - Model untuk User dan UserGrowID
- `product.py` - Model untuk Product dan Stock
- `transaction.py` - Model untuk Transaction
- `level.py` - Model untuk Level, LevelReward, dan LevelSettings
- `balance.py` - Model Balance yang sudah ada (dipindahkan dari data/models/)

### 2. Database Repositories
Dibuat repositories lengkap di `database/repositories/`:
- `user_repository.py` - Repository untuk operasi user
- `product_repository.py` - Repository untuk operasi produk dan stok
- `transaction_repository.py` - Repository untuk operasi transaksi
- `leveling_repository.py` - Repository untuk sistem leveling (sudah ada)
- `reputation_repository.py` - Repository untuk sistem reputasi (sudah ada)

### 3. Database Manager
- `database/manager.py` - Database manager utama yang menggabungkan fungsi dari `database.py` root dan `database/connection.py`
- Menyediakan fungsi backward compatibility untuk kode yang sudah ada
- Singleton pattern untuk memastikan satu instance database manager

### 4. File Reorganization
File-file dipindahkan ke folder yang sesuai:

#### Dari `ext/` ke `services/`:
- `balance_manager.py` → `services/balance_service.py`
- `admin_service.py` → `services/admin_service.py`
- `product_manager.py` → `services/product_service_old.py`
- `cache_manager.py` → `services/cache_service.py`
- `donate.py` → `services/donation_service.py`
- `trx.py` → `services/transaction_service.py`

#### Dari `ext/` ke `utils/`:
- `base_handler.py` → `utils/base_handler.py`

#### Dari `ext/` ke `config/constants/`:
- `constants.py` → `config/constants/bot_constants.py`

#### Dari `ext/` ke `ui/`:
- `live_buttons.py` → `ui/buttons/live_buttons.py`
- `live_stock.py` → `ui/views/live_stock_view.py`

### 5. Folder `ext/` Dihapus
Folder `ext/` telah dihapus karena semua file sudah dipindahkan ke lokasi yang sesuai.

## Struktur Database Baru

```
database/
├── __init__.py          # Export semua komponen database
├── manager.py           # Database manager utama
├── connection.py        # Connection manager (existing)
├── migrations.py        # Database migrations (existing)
├── models/
│   ├── __init__.py      # Export semua models
│   ├── user.py          # User dan UserGrowID models
│   ├── product.py       # Product dan Stock models
│   ├── transaction.py   # Transaction model
│   ├── level.py         # Level system models
│   └── balance.py       # Balance model (moved from data/models/)
└── repositories/
    ├── __init__.py              # Export semua repositories
    ├── user_repository.py       # User operations
    ├── product_repository.py    # Product dan Stock operations
    ├── transaction_repository.py # Transaction operations
    ├── leveling_repository.py   # Leveling operations (existing)
    └── reputation_repository.py # Reputation operations (existing)
```

## Cara Penggunaan

### Database Manager
```python
from database import db_manager, DatabaseManager

# Inisialisasi database
await db_manager.initialize()

# Atau buat instance baru
db = DatabaseManager()
await db.initialize()
```

### Models
```python
from database.models import User, Product, Transaction, Level

# Buat user baru
user = User(growid="testuser", balance_wl=1000)

# Buat produk baru
product = Product(code="TEST", name="Test Product", price=100)
```

### Repositories
```python
from database.repositories import UserRepository, ProductRepository

# Gunakan repository
user_repo = UserRepository(db_manager)
user = await user_repo.get_user_by_growid("testuser")

product_repo = ProductRepository(db_manager)
products = await product_repo.get_all_products()
```

### Backward Compatibility
Kode lama masih bisa berfungsi:
```python
from database import get_connection, setup_database, verify_database

# Fungsi lama masih tersedia
conn = get_connection()
setup_database()
verify_database()
```

## Keuntungan Reorganisasi

1. **Struktur yang Lebih Jelas**: File-file sekarang berada di folder yang sesuai dengan fungsinya
2. **Separation of Concerns**: Models, repositories, dan database manager terpisah dengan jelas
3. **Reusability**: Models dan repositories bisa digunakan kembali di berbagai bagian aplikasi
4. **Maintainability**: Kode lebih mudah dipelihara dan dikembangkan
5. **Type Safety**: Models menggunakan dataclass dan type hints untuk keamanan tipe
6. **Async Support**: Repositories mendukung operasi asynchronous
7. **Backward Compatibility**: Kode lama masih bisa berfungsi tanpa perubahan

## File yang Perlu Diupdate

Setelah reorganisasi ini, file-file berikut mungkin perlu diupdate import statement-nya:
- File yang mengimport dari `ext/`
- File yang menggunakan database connection langsung
- File yang menggunakan models dari `data/models/`

## Testing

Setelah reorganisasi, disarankan untuk:
1. Test semua fungsi database
2. Test import statements di semua file
3. Test backward compatibility
4. Test repository operations
5. Test model serialization/deserialization
