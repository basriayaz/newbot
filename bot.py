import os
import json
import logging
import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from telegram import Bot
import asyncio
import sys

# Logging ayarları
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Çevre değişkenlerini yükle
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
API_URL = "https://soccer-api-yeni-503570030595.us-central1.run.app"

# Takip edilecek ligler
LEAGUES = [
    "Spanish La Liga",
    "English Premier League", 
    "German Bundesliga",
    "France Ligue 1",
    "Italian Serie A",
    "Turkey Super Lig",
    "Uefa Champions League",
    "Uefa Europa League",
    "Uefa Conference League"
]

# Lig emojileri
LEAGUE_EMOJIS = {
    "spanish la liga": "🇪🇸",
    "english premier league": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "german bundesliga": "🇩🇪",
    "france ligue 1": "🇫🇷",
    "italian serie a": "🇮🇹",
    "turkey super lig": "🇹🇷",
    "uefa champions league": "🏆",
    "uefa europa league": "🌟",
    "uefa conference league": "⭐"
}

class SoccerBot:
    def __init__(self):
        self.bot = Bot(token=TELEGRAM_TOKEN)
        self.session = requests.Session()
        self.is_running = True
        
    def get_league_emoji(self, league_name: str) -> str:
        """Get emoji for league"""
        for key, emoji in LEAGUE_EMOJIS.items():
            if key.lower() in league_name.lower():
                return emoji
        return "⚽️"

    async def send_telegram_message(self, message: str) -> None:
        """Send message to Telegram channel"""
        try:
            async with self.bot:
                await self.bot.send_message(
                    chat_id=TELEGRAM_CHANNEL_ID,
                    text=message,
                    parse_mode='HTML'
                )
                await asyncio.sleep(1)  # Rate limiting
        except Exception as e:
            logger.error(f"Telegram error: {e}")

    def fetch_daily_matches(self) -> list:
        """Fetch today's matches"""
        try:
            today = datetime.now(pytz.timezone('Europe/Istanbul')).strftime("%Y-%m-%d")
            response = self.session.post(
                f"{API_URL}/fetch-matches",
                json={"date": today},
                timeout=30
            )
            data = response.json()
            if data.get('status') == 'success':
                return data.get('data', [])
            return []
        except Exception as e:
            logger.error(f"Error fetching matches: {e}")
            return []

    def analyze_match(self, match_id: int) -> dict:
        """Analyze a single match"""
        try:
            response = self.session.post(
                f"{API_URL}/analyze-match",
                json={"match_id": match_id},
                timeout=20
            )
            data = response.json()
            if data.get('status') == 'success':
                return data
            return None
        except Exception as e:
            logger.error(f"Error analyzing match {match_id}: {e}")
            return None

    def format_prediction_message(self, match: tuple, analysis: dict) -> str:
        """Format prediction message"""
        try:
            info = analysis['data']['info']
            tahminler = analysis['data']['tahminler']
            
            # Herhangi bir tahmin var mı kontrol et
            has_predictions = any([
                tahminler.get('ms_tahmini'),
                tahminler.get('ust_tahmini'),
                tahminler.get('kg_tahmini'),
                tahminler.get('iy_gol_tahmini'),
                tahminler.get('korner_tahmini'),
                tahminler.get('riskli_tahmin')
            ])
            
            if not has_predictions:
                return None
            
            league_emoji = self.get_league_emoji(info['lig'])
            message = [
                f"{league_emoji} <b>{info['mac']}</b>",
                f"📅 {info['mac_tarihi']} | ⏰ {info['mac_saati']}\n"
            ]
            
            # Tüm tahminleri ekle
            if tahminler.get('ms_tahmini'): message.append(f"📊 Maç Sonucu: {tahminler['ms_tahmini']}")
            if tahminler.get('ust_tahmini'): message.append(f"📈 Gol Tahmini: {tahminler['ust_tahmini']}")
            if tahminler.get('kg_tahmini'): message.append(f"🥅 KG: {tahminler['kg_tahmini']}")
            if tahminler.get('iy_gol_tahmini'): message.append(f"⏱ İY: {tahminler['iy_gol_tahmini']}")
            if tahminler.get('korner_tahmini'): message.append(f"🚩 Korner: {tahminler['korner_tahmini']}")
            if tahminler.get('riskli_tahmin'): message.append(f"⚠️ Riskli Tahmin: {tahminler['riskli_tahmin']}")
            
            return "\n".join(message)
            
        except Exception as e:
            logger.error(f"Error formatting message: {e}")
            return None

    async def process_matches(self):
        """Main process to fetch, analyze and send predictions"""
        try:
            # Header mesajı
            await self.send_telegram_message(
                "📢 <b>TAHMİN BİLDİRİMİ</b> 📢\n"
                "━━━━━━━━━━━━━━━━━━━━━\n"
                "🔍 Günün maç tahminleri analiz ediliyor...\n"
                "⏳ Tahminler birazdan paylaşılacak\n"
                "📊 Tüm ligler ve maçlar kontrol ediliyor\n"
                "━━━━━━━━━━━━━━━━━━━━━"
            )

            # Günün maçlarını çek
            matches = self.fetch_daily_matches()
            if not matches:
                await self.send_telegram_message("⚠️ Bugün için maç bulunamadı.")
                return

            # Liglere göre filtrele
            filtered_matches = []
            for match in matches:
                if match and len(match) >= 5:
                    _, _, _, league, _ = match
                    if any(filtered_league.lower() in league.lower() for filtered_league in LEAGUES):
                        filtered_matches.append(match)

            if not filtered_matches:
                await self.send_telegram_message("⚠️ Takip edilen liglerde maç bulunamadı.")
                return

            # Maçları analiz et ve tahminleri gönder
            prediction_count = 0
            for match in filtered_matches:
                match_id = match[0]
                analysis = self.analyze_match(match_id)
                
                if analysis:
                    message = self.format_prediction_message(match, analysis)
                    if message:
                        await self.send_telegram_message(message)
                        prediction_count += 1

            # Özet mesajı
            if prediction_count > 0:
                await self.send_telegram_message(
                    f"\n✅ Toplam {prediction_count} maç için tahmin paylaşıldı\n"
                    "━━━━━━━━━━━━━━━━━━━━━"
                )
            else:
                await self.send_telegram_message(
                    "⚠️ Tahmin bulunamadı.\n"
                    "• Uygun maç bulunamadı\n"
                    "━━━━━━━━━━━━━━━━━━━━━"
                )

        except Exception as e:
            logger.error(f"Error in process_matches: {e}")
            await self.send_telegram_message("⚠️ Sistem hatası oluştu.")

    async def run_daily(self):
        """Run daily at 11:00 Turkish time"""
        while self.is_running:
            try:
                # Türkiye saati ile şu anki zaman
                now = datetime.now(pytz.timezone('Europe/Istanbul'))
                
                # Bir sonraki çalışma zamanını hesapla (saat 11:00)
                next_run = now.replace(hour=11, minute=0, second=0, microsecond=0)
                if now >= next_run:
                    next_run += timedelta(days=1)
                
                # Bir sonraki çalışmaya kadar bekle
                wait_seconds = (next_run - now).total_seconds()
                logger.info(f"Next run scheduled at {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                
                await asyncio.sleep(wait_seconds)
                
                if self.is_running:
                    await self.process_matches()
                
            except Exception as e:
                logger.error(f"Error in daily schedule: {e}")
                await asyncio.sleep(300)  # Hata durumunda 5 dakika bekle

    def stop(self):
        """Stop the bot"""
        self.is_running = False
        logger.info("Bot stopped")

async def main():
    """Run the bot"""
    try:
        bot = SoccerBot()
        
        # İlk çalıştırmada hemen başlat
        await bot.process_matches()
        
        # Günlük zamanlamayı başlat
        await bot.run_daily()
        
    except Exception as e:
        logger.error(f"Bot error: {e}")
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        bot.stop()

if __name__ == "__main__":
    asyncio.run(main()) 