# Futbol Tahmin Botu

Bu bot, belirli liglerdeki futbol maçlarını analiz eder ve tahminleri Telegram kanalına gönderir.

## Kurulum

1. Python 3.8 veya daha yüksek bir sürüm yükleyin
2. Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```

3. `.env` dosyasını düzenleyin:
```
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHANNEL_ID=your_channel_id
```

## Çalıştırma

```bash
python bot.py
```

Bot, yarınki maçları analiz edecek ve sonuçları Telegram kanalına gönderecektir.

## Özellikler

- Belirli liglerdeki maçları filtreleme
- Maç analizleri ve tahminler
- Detaylı istatistikler
- Otomatik Telegram kanal paylaşımı

## Desteklenen Ligler

- Spanish La Liga
- English Premier League
- German Bundesliga
- France Ligue 1
- Italian Serie A
- Turkey Super Lig
- Uefa Champions League
- Uefa Europa League
- Uefa Conference League 