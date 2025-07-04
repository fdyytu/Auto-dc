# Struktur Folder Tenant

Folder ini berisi struktur terpisah untuk setiap tenant agar tidak tercampur dengan bot utama.

## Struktur Folder

```
tenants/
├── template/                 # Template konfigurasi untuk tenant baru
│   ├── config/
│   │   └── tenant_config.json
│   ├── data/                # Data tenant (database, cache, dll)
│   ├── logs/                # Log khusus tenant
│   ├── backups/             # Backup data tenant
│   ├── cogs/                # Cogs khusus tenant (jika ada)
│   └── services/            # Services khusus tenant (jika ada)
├── active/                  # Folder untuk tenant yang aktif
│   └── {tenant_id}/         # Folder per tenant
│       ├── config/
│       ├── data/
│       ├── logs/
│       ├── backups/
│       ├── cogs/
│       └── services/
└── README.md
```

## Cara Kerja

1. **Template**: Folder `template/` berisi konfigurasi dasar yang akan disalin untuk setiap tenant baru
2. **Active**: Folder `active/` berisi folder untuk setiap tenant yang aktif
3. **Isolasi**: Setiap tenant memiliki folder terpisah untuk menghindari konflik data
4. **Konfigurasi**: Setiap tenant memiliki file konfigurasi sendiri di `config/tenant_config.json`

## Fitur

- ✅ Isolasi data per tenant
- ✅ Konfigurasi terpisah per tenant
- ✅ Log terpisah per tenant
- ✅ Backup terpisah per tenant
- ✅ Cogs dan services khusus per tenant (opsional)

## Penggunaan

Tenant baru akan dibuat dengan menyalin struktur dari `template/` ke `active/{tenant_id}/`
