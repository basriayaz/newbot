import os
import json
import logging
import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import RetryAfter, TelegramError
import asyncio
import random
import sys
import schedule
import time
from typing import Optional, List, Dict, Any, Tuple

# Configure logging with more detail
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Configuration related errors"""
    pass

class APIError(Exception):
    """API related errors"""
    pass

class TelegramError(Exception):
    """Telegram related errors"""
    pass

class BotConfig:
    """Bot configuration handler"""
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Validate required environment variables
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.channel_id = os.getenv('TELEGRAM_CHANNEL_ID')
        
        if not self.token:
            raise ConfigError("TELEGRAM_TOKEN not found in environment variables")
        if not self.channel_id:
            raise ConfigError("TELEGRAM_CHANNEL_ID not found in environment variables")
            
        # Constants
        self.api_base_url = "https://soccer-api-yeni-503570030595.us-central1.run.app"
        self.filtered_leagues = [
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
        
        # Emojis
        self.league_emojis = {
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
        self.confidence_emojis = ["🎯", "💫", "✨", "🌟", "⚡️", "🔥"]

class MatchAnalyzer:
    """Handle match analysis and API calls"""
    def __init__(self, config: BotConfig):
        self.config = config
        self.session = requests.Session()
        # Set timeouts
        self.fetch_timeout = 30  # 30 seconds for fetching match list
        self.analyze_timeout = 20  # 20 seconds for analyzing single match
        
    async def fetch_matches(self, date_str: str) -> List[Dict[str, Any]]:
        """Fetch matches for given date with error handling"""
        try:
            response = self.session.post(
                f"{self.config.api_base_url}/fetch-matches",
                json={"date": date_str},
                timeout=self.fetch_timeout
            )
            response.raise_for_status()
            data = response.json()
            
            if not isinstance(data, dict) or 'status' not in data or 'data' not in data:
                raise APIError("Invalid response format from fetch-matches API")
                
            if data['status'] != 'success' or not isinstance(data['data'], list):
                raise APIError(f"API error: {data.get('message', 'Unknown error')}")
                
            return data['data']
            
        except requests.RequestException as e:
            logger.error(f"Network error while fetching matches: {str(e)}")
            raise APIError(f"Failed to fetch matches: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response while fetching matches: {str(e)}")
            raise APIError("Invalid response format from API")
            
    async def analyze_match(self, match_id: int) -> Optional[Dict[str, Any]]:
        """Analyze a specific match with error handling and timeout"""
        try:
            # Create a future for the request
            loop = asyncio.get_event_loop()
            future = loop.run_in_executor(
                None,
                lambda: self.session.post(
                    f"{self.config.api_base_url}/analyze-match",
                    json={"match_id": match_id},
                    timeout=self.analyze_timeout
                )
            )
            
            # Wait for the response with timeout
            try:
                response = await asyncio.wait_for(future, timeout=self.analyze_timeout)
            except asyncio.TimeoutError:
                logger.warning(f"Analysis timeout for match {match_id} after {self.analyze_timeout} seconds")
                return None
                
            response.raise_for_status()
            data = response.json()
            
            if not isinstance(data, dict) or 'status' not in data:
                raise APIError("Invalid response format from analyze-match API")
                
            if data['status'] != 'success':
                logger.warning(f"Analysis failed for match {match_id}: {data.get('message', 'Unknown error')}")
                return None
                
            return data
            
        except requests.RequestException as e:
            logger.error(f"Network error while analyzing match {match_id}: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response while analyzing match {match_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error analyzing match {match_id}: {str(e)}")
            return None

class MessageFormatter:
    """Handle message formatting"""
    def __init__(self, config: BotConfig):
        self.config = config
        
    def get_league_emoji(self, league_name: str) -> str:
        """Get emoji for league with fallback"""
        for key, emoji in self.config.league_emojis.items():
            if key.lower() in league_name.lower():
                return emoji
        return "⚽️"
        
    def format_analysis_message(self, match_data: Tuple, analysis_data: Dict[str, Any]) -> Optional[str]:
        """Format match analysis into a readable message with error handling"""
        try:
            if not analysis_data or 'data' not in analysis_data:
                return None
            
            data = analysis_data['data']
            info = data.get('info', {})
            tahminler = data.get('tahminler', {})
            
            # Validate required fields
            required_fields = ['lig', 'mac', 'mac_tarihi', 'mac_saati']
            if not all(field in info for field in required_fields):
                logger.error(f"Missing required fields in match info: {info}")
                return None
            
            # Skip if there's a risky prediction
            if tahminler.get('riskli_tahmin'):
                return None
                
            # Get league emoji
            league_emoji = self.get_league_emoji(info['lig'])
            confidence_emoji = random.choice(self.config.confidence_emojis)
            
            # Format message
            message_parts = []
            message_parts.append(f"{league_emoji} <b>{info['lig'].upper()}</b> {league_emoji}")
            message_parts.append("━━━━━━━━━━━━━━━━━━━━━")
            message_parts.append(f"🏟 <b>{info['mac']}</b>")
            message_parts.append(f"📅 {info['mac_tarihi']} | ⏰ {info['mac_saati']}\n")
            
            message_parts.append(f"{confidence_emoji} <b>GÜNÜN TAHMİNLERİ</b> {confidence_emoji}")
            message_parts.append("━━━━━━━━━━━━━━━━━━━━━")
            
            # Add predictions
            predictions = []
            if tahminler.get('ms_tahmini'):
                predictions.append(f"📊 Maç Sonucu: {tahminler['ms_tahmini']}")
            if tahminler.get('ust_tahmini'):
                predictions.append(f"📈 Gol Tahmini: {tahminler['ust_tahmini']}")
            if tahminler.get('kg_tahmini'):
                predictions.append(f"🥅 Karşılıklı Gol: {tahminler['kg_tahmini']}")
            if tahminler.get('iy_gol_tahmini'):
                predictions.append(f"⏱ İlk Yarı: {tahminler['iy_gol_tahmini']}")
            if tahminler.get('korner_tahmini'):
                predictions.append(f"🚩 Korner: {tahminler['korner_tahmini']}")
            
            if not predictions:
                logger.warning(f"No valid predictions for match {info['mac']}")
                return None
                
            message_parts.append("\n".join(predictions))
            message_parts.append("")
            
            # Add optional info
            if info.get('stadium'):
                message_parts.append(f"🏟 Stadyum: {info['stadium']}")
            if info.get('weather'):
                message_parts.append(f"🌤 Hava Durumu: {info['weather']}")
            
            message_parts.append("━━━━━━━━━━━━━━━━━━━━━")
            message_parts.append(f"#Tahmin #{info['lig'].replace(' ', '')}")
            
            return "\n".join(message_parts)
            
        except Exception as e:
            logger.error(f"Error formatting message: {str(e)}")
            return None

class TelegramBot:
    """Main bot class"""
    def __init__(self):
        try:
            self.config = BotConfig()
            self.analyzer = MatchAnalyzer(self.config)
            self.formatter = MessageFormatter(self.config)
            self.bot = Bot(token=self.config.token)
            self.retry_count = 3
            self.retry_delay = 5
            self.is_running = False
        except Exception as e:
            logger.critical(f"Failed to initialize bot: {str(e)}")
            raise

    async def send_message(self, message: str) -> bool:
        """Send message to Telegram channel"""
        for attempt in range(self.retry_count):
            try:
                async with self.bot:
                    await self.bot.send_message(
                        chat_id=self.config.channel_id,
                        text=message,
                        parse_mode='HTML'
                    )
                return True
            except RetryAfter as e:
                retry_after = e.retry_after
                logger.warning(f"Rate limited, waiting {retry_after} seconds")
                await asyncio.sleep(retry_after)
            except TelegramError as e:
                if attempt == self.retry_count - 1:
                    logger.error(f"Failed to send message after {self.retry_count} attempts: {str(e)}")
                    return False
                logger.warning(f"Telegram error (attempt {attempt + 1}/{self.retry_count}): {str(e)}")
                await asyncio.sleep(self.retry_delay)
        return False

    async def send_header_message(self, date_str: str) -> bool:
        """Send header message for daily predictions"""
        message = [
            "🎯 <b>GÜNÜN MAÇ TAHMİNLERİ</b> 🎯",
            f"📅 {date_str}",
            "━━━━━━━━━━━━━━━━━━━━━\n",
            "⚡️ Sadece güvenilir tahminler paylaşılmaktadır",
            "🎯 Riskli tahminler filtrelenmiştir",
            "📊 Veriler yapay zeka ile analiz edilmiştir\n",
            "━━━━━━━━━━━━━━━━━━━━━"
        ]
        return await self.send_message("\n".join(message))

    async def process_matches(self) -> None:
        """Process matches and send to Telegram"""
        try:
            # Get today's date instead of tomorrow
            istanbul_tz = pytz.timezone('Europe/Istanbul')
            today = datetime.now(istanbul_tz)
            date_str = today.strftime("%d.%m.%Y")
            api_date = today.strftime("%Y-%m-%d")
            
            # Send header
            if not await self.send_header_message(date_str):
                logger.error("Failed to send header message")
                return
                
            # Fetch and process matches
            try:
                matches = await self.analyzer.fetch_matches(api_date)
            except APIError as e:
                logger.error(f"Failed to fetch matches: {str(e)}")
                await self.send_message("⚠️ Maç verileri alınırken bir hata oluştu. Lütfen daha sonra tekrar deneyin.")
                return
                
            analyzed_count = 0
            error_count = 0
            
            for match in matches:
                try:
                    if not isinstance(match, (list, tuple)) or len(match) < 5:
                        logger.error(f"Invalid match data format: {match}")
                        continue
                        
                    match_id, team1, team2, league, _ = match
                    
                    # Check if league is in filtered leagues
                    if not any(filtered_league.lower() in league.lower() for filtered_league in self.config.filtered_leagues):
                        continue
                        
                    # Analyze match
                    analysis = await self.analyzer.analyze_match(match_id)
                    if not analysis:
                        error_count += 1
                        continue
                        
                    # Format and send message
                    message = self.formatter.format_analysis_message(match, analysis)
                    if message and await self.send_message(message):
                        analyzed_count += 1
                        await asyncio.sleep(1)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"Error processing match {match_id if 'match_id' in locals() else 'Unknown'}: {str(e)}")
                    error_count += 1
                    
            # Send summary
            if analyzed_count > 0:
                footer = [
                    "\n🏆 <b>GÜNÜN TAHMİNLERİ TAMAMLANDI</b> 🏆",
                    f"📊 Toplam {analyzed_count} güvenilir tahmin paylaşıldı",
                    "━━━━━━━━━━━━━━━━━━━━━"
                ]
                await self.send_message("\n".join(footer))
            else:
                await self.send_message("⚠️ Bugün için güvenilir tahmin bulunamadı.")
                
            if error_count > 0:
                logger.warning(f"Completed with {error_count} errors")
                
        except Exception as e:
            logger.error(f"Critical error in process_matches: {str(e)}")
            await self.send_message("⚠️ Sistem hatası oluştu. Yöneticiye bildirildi.")

    async def run_daily_job(self):
        """Run the daily job"""
        try:
            await self.process_matches()
            logger.info("Daily job completed successfully")
        except Exception as e:
            logger.error(f"Error in daily job: {str(e)}")

    async def start(self):
        """Start the bot"""
        self.is_running = True
        
        # Run immediately when started
        logger.info("Running initial job...")
        await self.run_daily_job()
        
        # Schedule next run at 11:00
        while self.is_running:
            try:
                now = datetime.now(pytz.timezone('Europe/Istanbul'))
                next_run = now.replace(hour=11, minute=0, second=0, microsecond=0)
                
                if now >= next_run:
                    next_run = next_run + timedelta(days=1)
                
                # Calculate seconds until next run
                delay = (next_run - now).total_seconds()
                
                logger.info(f"Next run scheduled at {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                await asyncio.sleep(delay)
                
                if self.is_running:
                    await self.run_daily_job()
                
            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    def stop(self):
        """Stop the bot"""
        self.is_running = False
        logger.info("Bot stopped.")

async def run_bot():
    """Run the bot"""
    try:
        # Set timezone to Turkey
        os.environ['TZ'] = 'Europe/Istanbul'
        time.tzset()
        
        # Initialize and start the bot
        bot = TelegramBot()
        
        logger.info("Starting bot...")
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        bot.stop()
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(run_bot()) 