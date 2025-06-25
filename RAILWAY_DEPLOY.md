# Panduan Deploy Discord Bot ke Railway

## Persiapan

1. **Pastikan Anda memiliki akun Railway**
   - Daftar di [railway.app](https://railway.app)
   - Connect dengan GitHub account

2. **Environment Variables yang diperlukan**
   Setelah deploy, set environment variables berikut di Railway dashboard:
   ```
   DISCORD_TOKEN=your_bot_token_here
   GUILD_ID=your_guild_id_here
   ADMIN_ID=your_admin_id_here
   DATABASE_URL=sqlite:///bot.db
   DEBUG=False
   LOG_LEVEL=INFO
   ```

## Cara Deploy

### Method 1: Deploy dari GitHub (Recommended)

1. Push repository ini ke GitHub
2. Di Railway dashboard, klik "New Project"
3. Pilih "Deploy from GitHub repo"
4. Pilih repository ini
5. Railway akan otomatis detect Dockerfile dan build

### Method 2: Deploy via Railway CLI

1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   ```

2. Login ke Railway:
   ```bash
   railway login
   ```

3. Deploy project:
   ```bash
   railway deploy
   ```

## Konfigurasi Environment Variables

Setelah deploy, tambahkan environment variables di Railway dashboard:

1. Buka project di Railway dashboard
2. Klik tab "Variables"
3. Tambahkan semua environment variables yang diperlukan

## Monitoring

- Logs dapat dilihat di Railway dashboard tab "Deployments"
- Bot akan restart otomatis jika crash
- Railway menyediakan metrics untuk monitoring resource usage

## Troubleshooting

### Bot tidak connect ke Discord
- Pastikan DISCORD_TOKEN sudah benar
- Check logs untuk error messages

### Database issues
- Untuk production, pertimbangkan menggunakan PostgreSQL
- Railway menyediakan PostgreSQL addon

### Memory/CPU limits
- Railway free tier memiliki limits
- Upgrade ke Pro plan jika diperlukan

## File yang dibuat untuk Railway

- `Dockerfile`: Container configuration
- `.dockerignore`: Exclude unnecessary files dari build
- `RAILWAY_DEPLOY.md`: Dokumentasi ini

## Tips Optimasi

1. **Database**: Gunakan PostgreSQL untuk production
2. **Logging**: Set LOG_LEVEL=WARNING untuk mengurangi logs
3. **Caching**: Implementasi Redis untuk caching jika diperlukan
4. **Monitoring**: Setup alerts untuk downtime

## Support

Jika ada masalah dengan deployment:
1. Check Railway logs
2. Verify environment variables
3. Test bot locally dengan Docker
