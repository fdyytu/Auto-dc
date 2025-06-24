# Auto-DC Discord Bot

Discord bot untuk mengelola store dan berbagai fitur komunitas Discord.

## 📁 Struktur Project

```
Auto-dc/
├── src/                    # Source code utama
│   ├── bot/               # Core bot functionality
│   │   ├── bot.py         # Main bot class
│   │   ├── startup.py     # Startup manager
│   │   └── ...
│   ├── cogs/              # Discord cogs (commands & events)
│   ├── services/          # Business logic services
│   ├── database/          # Database models & repositories
│   │   ├── models/        # Data models
│   │   ├── repositories/  # Data access layer
│   │   ├── connection.py  # Database connection
│   │   └── migrations.py  # Database migrations
│   ├── business/          # Business logic modules
│   │   ├── leveling/      # Leveling system
│   │   ├── reputation/    # Reputation system
│   │   ├── shop/          # Shop system
│   │   └── tickets/       # Ticket system
│   ├── ui/                # User interface components
│   │   ├── buttons/       # Discord buttons
│   │   ├── modals/        # Discord modals
│   │   ├── selects/       # Discord select menus
│   │   └── views/         # Discord views
│   ├── utils/             # Utility functions
│   ├── config/            # Configuration files
│   ├── handlers/          # Event handlers
│   ├── logs/              # Log files
│   └── ext/               # Extensions
├── docs/                  # Dokumentasi
├── scripts/               # Utility scripts
├── tests/                 # Unit tests
├── assets/                # Static files
├── .github/               # GitHub workflows
├── .backups/              # Backup files (hidden)
├── .temp/                 # Temporary files (hidden)
├── main.py                # Entry point
├── requirements.txt       # Dependencies
└── .env                   # Environment variables
```

## 🚀 Quick Start

1. **Clone repository:**
   ```bash
   git clone <repository-url>
   cd Auto-dc
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup environment:**
   ```bash
   cp .env.example .env
   # Edit .env dengan konfigurasi Anda
   ```

4. **Run bot:**
   ```bash
   python main.py
   ```

## 📋 Features

- 🛒 **Store System** - Manajemen produk dan transaksi
- 📊 **Leveling System** - Sistem level dan XP
- ⭐ **Reputation System** - Sistem reputasi user
- 🎫 **Ticket System** - Sistem tiket support
- 🛡️ **Auto Moderation** - Moderasi otomatis
- 📈 **Statistics** - Statistik server dan user
- 🎵 **Music** - Bot musik (opsional)
- 🎁 **Giveaway** - Sistem giveaway

## 🔧 Configuration

Konfigurasi utama berada di `src/config/config.json`. File ini berisi:

- Token bot dan ID server
- Channel dan role IDs
- Cooldowns dan rate limits
- Automod settings
- Hot reload settings

## 📚 Documentation

Dokumentasi lengkap tersedia di folder `docs/`:

- `docs/README_RESTRUCTURE.md` - Detail restructuring
- `docs/HOT_RELOAD_GUIDE.md` - Panduan hot reload
- `docs/DATABASE_REORGANIZATION.md` - Reorganisasi database
- `docs/HELP_COMMAND_FIX.md` - Perbaikan help command

## 🧪 Testing

```bash
# Run tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_services.py
```

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

[Specify your license here]

## 👥 Authors

- fdyyuk - Initial work and restructuring
