"""
Messages dan Button IDs constants
Author: fdyytu
Created at: 2025-03-07 18:04:56 UTC
Last Modified: 2025-03-10 10:09:16 UTC
"""

# Messages untuk berbagai situasi
class MESSAGES:
    """Message templates untuk bot responses"""
    
    # Success Messages
    SUCCESS = {
        'PURCHASE_COMPLETE': "✅ **Pembelian Berhasil!**\n\n**Produk:** {product_name}\n**Jumlah:** {quantity}\n**Total:** {total_price}\n**Sisa Balance:** {remaining_balance}\n\n**Item yang dibeli:**\n```\n{items}\n```",
        'BALANCE_UPDATED': "✅ Balance berhasil diperbarui!\n**Balance Baru:** {balance}",
        'STOCK_ADDED': "✅ Stock berhasil ditambahkan!\n**Produk:** {product_code}\n**Jumlah ditambah:** {quantity}\n**Total stock:** {total_stock}",
        'PRODUCT_CREATED': "✅ Produk berhasil dibuat!\n**Kode:** {product_code}\n**Nama:** {product_name}\n**Harga:** {price}",
        'REGISTRATION_SUCCESS': "✅ **Registrasi Berhasil!**\n\nSelamat datang di toko kami! Anda sekarang dapat melakukan pembelian.",
        'DONATION_SUCCESS': "✅ **Donasi Berhasil!**\n\n**Jumlah:** {amount}\n**Dari:** {donor}\n\nTerima kasih atas dukungan Anda!",
        'PURCHASE': "✅ **Pembelian Berhasil!**\n\nTerima kasih atas pembelian Anda!",
        'BALANCE_UPDATE': "✅ **Balance Berhasil Diperbarui!**\n\nBalance Anda telah diperbarui."
    }
    
    # Error Messages
    ERROR = {
        'INSUFFICIENT_BALANCE': "❌ **Balance Tidak Mencukupi!**\n\n**Dibutuhkan:** {required}\n**Balance Anda:** {current}\n**Kekurangan:** {shortage}",
        'OUT_OF_STOCK': "❌ **Stock Habis!**\n\nProduk **{product_name}** sedang tidak tersedia.\nSilakan coba lagi nanti atau hubungi admin.",
        'PRODUCT_NOT_FOUND': "❌ **Produk Tidak Ditemukan!**\n\nKode produk **{product_code}** tidak valid atau tidak tersedia.",
        'INVALID_QUANTITY': "❌ **Jumlah Tidak Valid!**\n\nJumlah harus antara 1 dan {max_quantity}.",
        'INVALID_AMOUNT': "❌ **Jumlah tidak valid!** Masukkan angka yang benar.",
        'USER_NOT_REGISTERED': "❌ **Belum Terdaftar!**\n\nAnda belum terdaftar di sistem kami.\nSilakan daftar terlebih dahulu dengan menekan tombol **Register**.",
        'TRANSACTION_FAILED': "❌ **Transaksi Gagal!**\n\n{reason}\n\nSilakan coba lagi atau hubungi admin jika masalah berlanjut.",
        'MAINTENANCE_MODE': "🔧 **Mode Maintenance**\n\nSistem sedang dalam pemeliharaan.\nSilakan coba lagi nanti.",
        'PERMISSION_DENIED': "❌ **Akses Ditolak!**\n\nAnda tidak memiliki izin untuk melakukan tindakan ini.",
        'RATE_LIMITED': "⏰ **Terlalu Cepat!**\n\nSilakan tunggu {cooldown} detik sebelum mencoba lagi.",
        'LOCK_ACQUISITION_FAILED': "❌ **Sistem Sibuk!**\n\nSistem sedang memproses transaksi lain. Silakan coba lagi dalam beberapa detik.",
        'DATABASE_ERROR': "❌ **Error Database!**\n\nTerjadi kesalahan pada database. Silakan coba lagi atau hubungi admin.",
        'NO_HISTORY': "❌ **Tidak Ada Riwayat!**\n\nBelum ada riwayat transaksi untuk ditampilkan."
    }
    
    # Info Messages
    INFO = {
        'PROCESSING': "⏳ **Memproses...**\n\nSilakan tunggu sebentar.",
        'LOADING': "🔄 **Memuat data...**",
        'UPDATING': "🔄 **Memperbarui...**",
        'SYNCING': "🔄 **Sinkronisasi data...**",
        'WELCOME': "👋 **Selamat Datang!**\n\nGunakan tombol di bawah untuk berinteraksi dengan toko kami.",
        'HELP': "ℹ️ **Bantuan**\n\nGunakan tombol-tombol yang tersedia untuk navigasi.\nJika mengalami masalah, hubungi admin.",
        'MAINTENANCE_SCHEDULED': "🔧 **Pemeliharaan Terjadwal**\n\nSistem akan memasuki mode pemeliharaan dalam {time}."
    }
    
    # Warning Messages
    WARNING = {
        'LOW_STOCK': "⚠️ **Stock Menipis!**\n\n**Produk:** {product_name}\n**Sisa:** {remaining} item\n\nSegera lakukan restock!",
        'HIGH_DEMAND': "⚠️ **Permintaan Tinggi!**\n\nProduk ini sedang banyak diminati. Stock mungkin cepat habis.",
        'PRICE_CHANGE': "⚠️ **Perubahan Harga!**\n\n**Produk:** {product_name}\n**Harga Lama:** {old_price}\n**Harga Baru:** {new_price}",
        'SYSTEM_OVERLOAD': "⚠️ **Sistem Sibuk!**\n\nSistem sedang mengalami beban tinggi. Respons mungkin lebih lambat."
    }

# Button IDs
class BUTTON_IDS:
    # Basic Buttons
    CONFIRM = "confirm_{}"
    CANCEL = "cancel_{}"
    BUY = "buy"
    DONATE = "donate"
    REFRESH = "refresh"
    
    # Shop Buttons
    REGISTER = "register"
    BALANCE = "balance"
    WORLD_INFO = "world_info"
    CONFIRM_PURCHASE = "confirm_purchase"
    CANCEL_PURCHASE = "cancel_purchase"
    HISTORY = "history"
    
    @classmethod
    def get_purchase_confirmation_id(cls, product_code: str) -> str:
        """Generate ID untuk konfirmasi pembelian"""
        return f"{cls.CONFIRM_PURCHASE}_{product_code}"
        
    @classmethod
    def get_confirm_id(cls, action_id: str) -> str:
        """Generate ID untuk konfirmasi umum"""
        return cls.CONFIRM.format(action_id)
        
    @classmethod
    def get_cancel_id(cls, action_id: str) -> str:
        """Generate ID untuk pembatalan umum"""
        return cls.CANCEL.format(action_id)

# Event Types untuk logging
class EVENT_TYPES:
    """Event types untuk logging system"""
    
    TRANSACTION = {
        'PURCHASE': 'purchase_completed',
        'DEPOSIT': 'balance_deposited',
        'WITHDRAWAL': 'balance_withdrawn',
        'REFUND': 'transaction_refunded'
    }
    
    PRODUCT = {
        'CREATED': 'product_created',
        'UPDATED': 'product_updated',
        'DELETED': 'product_deleted',
        'STOCK_ADDED': 'stock_added',
        'STOCK_REMOVED': 'stock_removed'
    }
    
    USER = {
        'REGISTERED': 'user_registered',
        'BALANCE_UPDATED': 'user_balance_updated',
        'PROFILE_UPDATED': 'user_profile_updated'
    }
    
    STOCK = {
        'ADDED': 'stock_added',
        'REMOVED': 'stock_removed',
        'LOW': 'stock_low'
    }
    
    WORLD = {
        'UPDATED': 'world_updated',
        'ACCESSED': 'world_accessed'
    }
    
    SYSTEM = {
        'ERROR': 'error',
        'WARNING': 'warning',
        'INFO': 'info',
        'DEBUG': 'debug'
    }
