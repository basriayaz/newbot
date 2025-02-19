from aiogram import Bot
from aiogram.types import FSInputFile
import os
from dotenv import load_dotenv
import logging
import asyncio
from typing import Optional

# .env dosyasını yükle
load_dotenv()

# Telegram bot token'ı
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')

# Bot oluştur
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Global event loop
loop = None

def get_event_loop():
    """Event loop'u alır veya oluşturur"""
    global loop
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

async def _send_message(message: str):
    """Telegram kanalına mesaj gönderir (async versiyon)"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        error_msg = "Telegram token veya kanal ID bulunamadı"
        logging.error(error_msg)
        raise ValueError(error_msg)
        
    try:
        logging.info(f"Telegram mesajı gönderiliyor... (Uzunluk: {len(message)} karakter)")
        result = await bot.send_message(
            chat_id=TELEGRAM_CHANNEL_ID,
            text=message,
            parse_mode="HTML"
        )
        logging.info(f"Mesaj başarıyla gönderildi (Message ID: {result.message_id})")
        return result
    except Exception as e:
        error_msg = f"Telegram mesajı gönderilirken hata oluştu: {type(e).__name__}: {str(e)}"
        logging.error(error_msg)
        raise

async def _send_photo(photo_path: str, caption: Optional[str] = None):
    """Telegram kanalına fotoğraf gönderir (async versiyon)"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
        error_msg = "Telegram token veya kanal ID bulunamadı"
        logging.error(error_msg)
        raise ValueError(error_msg)
        
    if not os.path.exists(photo_path):
        error_msg = f"Fotoğraf dosyası bulunamadı: {photo_path}"
        logging.error(error_msg)
        raise FileNotFoundError(error_msg)
        
    try:
        logging.info(f"Telegram fotoğrafı gönderiliyor... (Dosya: {photo_path})")
        photo = FSInputFile(photo_path)
        result = await bot.send_photo(
            chat_id=TELEGRAM_CHANNEL_ID,
            photo=photo,
            caption=caption
        )
        logging.info(f"Fotoğraf başarıyla gönderildi (Message ID: {result.message_id})")
        return result
    except Exception as e:
        error_msg = f"Telegram fotoğrafı gönderilirken hata oluştu: {type(e).__name__}: {str(e)}"
        logging.error(error_msg)
        raise

def send_message(message: str):
    """send_message fonksiyonunun senkron versiyonu"""
    if not message:
        error_msg = "Gönderilecek mesaj boş olamaz"
        logging.error(error_msg)
        raise ValueError(error_msg)
        
    try:
        logging.info("Event loop alınıyor...")
        loop = get_event_loop()
        
        logging.info("Mesaj gönderme işlemi başlatılıyor...")
        result = loop.run_until_complete(_send_message(message))
        
        return result
    except Exception as e:
        error_msg = f"Telegram mesajı gönderilirken hata oluştu: {type(e).__name__}: {str(e)}"
        logging.error(error_msg)
        raise
    finally:
        if loop and not loop.is_closed():
            logging.info("Bot oturumu kapatılıyor...")
            loop.run_until_complete(bot.session.close())

def send_photo(photo_path: str, caption: Optional[str] = None):
    """send_photo fonksiyonunun senkron versiyonu"""
    if not photo_path:
        error_msg = "Fotoğraf yolu boş olamaz"
        logging.error(error_msg)
        raise ValueError(error_msg)
        
    try:
        logging.info("Event loop alınıyor...")
        loop = get_event_loop()
        
        logging.info("Fotoğraf gönderme işlemi başlatılıyor...")
        result = loop.run_until_complete(_send_photo(photo_path, caption))
        
        return result
    except Exception as e:
        error_msg = f"Telegram fotoğrafı gönderilirken hata oluştu: {type(e).__name__}: {str(e)}"
        logging.error(error_msg)
        raise
    finally:
        if loop and not loop.is_closed():
            logging.info("Bot oturumu kapatılıyor...")
            loop.run_until_complete(bot.session.close())

def cleanup():
    """Bot ve event loop'u temizler"""
    global loop
    if loop and not loop.is_closed():
        logging.info("Cleanup işlemi başlatılıyor...")
        try:
            loop.run_until_complete(bot.session.close())
            loop.close()
            logging.info("Cleanup başarıyla tamamlandı")
        except Exception as e:
            logging.error(f"Cleanup sırasında hata oluştu: {type(e).__name__}: {str(e)}")
            raise 