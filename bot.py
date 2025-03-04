import requests
import json
from datetime import datetime
import time
import logging
import asyncio
import aiohttp
from database import create_connection, create_tables, insert_match_info, update_database_schema
from typing import List, Dict, Any
from asyncio import Semaphore

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

# API endpoint'leri
FETCH_MATCHES_URL = "https://soccer-api-yeni-503570030595.us-central1.run.app/fetch-matches"
ANALYZE_MATCH_URL = "https://soccer-api-yeni-503570030595.us-central1.run.app/analyze-match"

# Eş zamanlı işlem limiti
MAX_CONCURRENT_TASKS = 5

def fetch_daily_matches(date_str: str) -> list:
    """Günün maç listesini API'den alır"""
    max_retries = 3
    retry_delay = 2  # saniye
    
    for attempt in range(max_retries):
        try:
            logging.info(f"Maç listesi alınıyor... (Tarih: {date_str})")
            response = requests.post(FETCH_MATCHES_URL, json={"date": date_str})
            response.raise_for_status()
            data = response.json()
            
            if not data:
                error_msg = "API boş yanıt döndürdü"
                logging.error(error_msg)
                if attempt < max_retries - 1:
                    logging.info(f"Yeniden deneniyor ({attempt + 2}/{max_retries})...")
                    time.sleep(retry_delay)
                    continue
                return []
            
            if data.get("status") == "success" and "data" in data and data["data"]:
                matches = data["data"]
                logging.info(f"Toplam {len(matches)} maç bulundu")
                return matches
            else:
                error_msg = f"API yanıtı başarısız veya veri yok: {data}"
                logging.error(error_msg)
                if attempt < max_retries - 1:
                    logging.info(f"Yeniden deneniyor ({attempt + 2}/{max_retries})...")
                    time.sleep(retry_delay)
                    continue
                return []
                
        except (requests.exceptions.RequestException, json.JSONDecodeError, TypeError, KeyError) as e:
            error_msg = f"Maç listesi alınırken hata oluştu: {type(e).__name__}: {str(e)}"
            logging.error(error_msg)
            
            if attempt < max_retries - 1:
                logging.info(f"Yeniden deneniyor ({attempt + 2}/{max_retries})...")
                time.sleep(retry_delay)
                continue
            return []
    
    return []

async def analyze_match_async(session: aiohttp.ClientSession, match_id: int, semaphore: Semaphore) -> Dict[str, Any]:
    """Belirli bir maçı eş zamanlı olarak analiz eder"""
    max_retries = 3
    retry_delay = 2
    
    async with semaphore:  # Eş zamanlı işlem sayısını sınırla
        for attempt in range(max_retries):
            try:
                logging.info(f"Maç analizi yapılıyor (ID: {match_id})")
                async with session.post(ANALYZE_MATCH_URL, json={"match_id": match_id}) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    if data.get("status") == "success" and "data" in data:
                        return data["data"]
                    else:
                        error_msg = f"Maç analizi başarısız: {data}"
                        logging.error(error_msg)
                        
                        if attempt < max_retries - 1:
                            logging.info(f"Yeniden deneniyor ({attempt + 2}/{max_retries})...")
                            await asyncio.sleep(retry_delay)
                            continue
                        return None
                        
            except Exception as e:
                error_msg = f"Maç analizi sırasında hata oluştu (ID: {match_id}): {type(e).__name__}: {str(e)}"
                logging.error(error_msg)
                
                if attempt < max_retries - 1:
                    logging.info(f"Yeniden deneniyor ({attempt + 2}/{max_retries})...")
                    await asyncio.sleep(retry_delay)
                    continue
                return None
    
    return None

async def process_matches_async():
    """Günün maçlarını eş zamanlı olarak işler"""
    try:
        # Veritabanı bağlantısını oluştur
        conn = create_connection()
        create_tables(conn)
        update_database_schema(conn)
        
        # Bugünün tarihini al
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Günün maçlarını al
        matches = fetch_daily_matches(today)
        
        if not matches:
            error_msg = f"{today} tarihi için maç bulunamadı"
            logging.warning(error_msg)
            return error_msg
        
        logging.info(f"{today} tarihi için {len(matches)} maç bulundu")
        
        # İstatistikler
        successful_analyses = 0
        failed_analyses = 0
        skipped_analyses = 0
        
        # Semaphore oluştur
        semaphore = Semaphore(MAX_CONCURRENT_TASKS)
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for match in matches:
                try:
                    match_id = match[0]
                except (IndexError, TypeError) as e:
                    logging.error(f"Geçersiz maç verisi: {match}, Hata: {type(e).__name__}: {str(e)}")
                    failed_analyses += 1
                    continue
                
                # Veritabanında kontrol et
                cursor = conn.cursor()
                cursor.execute("SELECT match_id FROM matches WHERE match_id = ?", (match_id,))
                existing_match = cursor.fetchone()
                
                if existing_match:
                    logging.info(f"Maç zaten veritabanında mevcut (ID: {match_id}), atlanıyor...")
                    skipped_analyses += 1
                    continue
                
                # Analiz görevini ekle
                task = asyncio.create_task(analyze_match_async(session, match_id, semaphore))
                tasks.append((match_id, task))
            
            # Tüm görevleri bekle
            for match_id, task in tasks:
                try:
                    match_analysis = await task
                    if match_analysis:
                        insert_match_info(conn, match_analysis)
                        logging.info(f"Maç analizi başarıyla kaydedildi (ID: {match_id})")
                        successful_analyses += 1
                    else:
                        logging.error(f"Maç analizi başarısız (ID: {match_id})")
                        failed_analyses += 1
                except Exception as e:
                    logging.error(f"Maç işlenirken hata oluştu (ID: {match_id}): {type(e).__name__}: {str(e)}")
                    failed_analyses += 1
        
        # İşlem özetini oluştur
        summary = f"""
        📊 Analiz Özeti ({today}):
        ✅ Başarılı: {successful_analyses}
        ❌ Başarısız: {failed_analyses}
        ⏭️ Atlanan: {skipped_analyses}
        📈 Toplam: {len(matches)}
        """
        logging.info(summary)
        
        return summary
        
    except Exception as e:
        error_msg = f"Genel bir hata oluştu: {type(e).__name__}: {str(e)}"
        logging.error(error_msg)
        return error_msg
        
    finally:
        if 'conn' in locals():
            conn.close()
            logging.info("Veritabanı bağlantısı kapatıldı")

def process_matches():
    """Senkron wrapper fonksiyonu"""
    return asyncio.run(process_matches_async())

if __name__ == "__main__":
    process_matches() 