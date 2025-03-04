import sqlite3
import logging
from datetime import datetime, timedelta
import pytz
from typing import List, Dict, Any, Tuple
import requests
import os
from dotenv import load_dotenv
import concurrent.futures
from itertools import islice

# .env dosyasını yükle
load_dotenv()

# Türkiye saat dilimi
TR_TIMEZONE = pytz.timezone('Europe/Istanbul')

# API URL'sini al
API_URL = os.getenv('API_URL')

# Batch size for parallel processing
BATCH_SIZE = 10

def get_match_result(match_id: int) -> Dict[str, Any]:
    """API'den maç sonucunu alır"""
    logging.info(f"🔄 Maç sonucu alınıyor (ID: {match_id})")
    try:
        url = f"{API_URL}/analyze-match"
        
        # İstek verisi
        payload = {
            "match_id": match_id
        }
        
        logging.debug(f"API isteği gönderiliyor: {url}")
        logging.debug(f"Payload: {payload}")
        
        # POST isteği gönder
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        logging.debug(f"API yanıtı alındı: {data}")
        
        if not data or 'data' not in data:
            raise ValueError(f"Maç sonucu bulunamadı (ID: {match_id})")
            
        # API'den gelen veriyi kontrol et
        if 'score' not in data['data']:
            raise ValueError(f"Maç skoru verisi eksik (ID: {match_id})")
            
        score_data = data['data']['score']
        logging.debug(f"Skor verisi: {score_data}")
        
        # Skor verilerini ayıkla
        try:
            # Boş string kontrolü ekle
            home_score_str = score_data.get('home_score', '')
            away_score_str = score_data.get('away_score', '')
            ht_score_str = score_data.get('ht_score', '')
            
            # Eğer skorlar boş string ise None olarak ayarla
            home_score = int(home_score_str) if home_score_str.strip() else None
            away_score = int(away_score_str) if away_score_str.strip() else None
            
            # İlk yarı skorunu kontrol et
            ht_home_score = None
            ht_away_score = None
            if ht_score_str.strip() and '-' in ht_score_str:
                ht_scores = ht_score_str.split('-')
                if ht_scores[0].strip() and ht_scores[1].strip():
                    ht_home_score = int(ht_scores[0])
                    ht_away_score = int(ht_scores[1])
            
            result = {
                'home_score': home_score,
                'away_score': away_score,
                'ht_home_score': ht_home_score,
                'ht_away_score': ht_away_score
            }
            
            # Log mesajını güncelle
            score_msg = "Skor bulunamadı" if all(v is None for v in result.values()) else \
                       f"MS {home_score}-{away_score}, İY {ht_home_score}-{ht_away_score}"
            logging.info(f"✅ Maç sonucu başarıyla alındı (ID: {match_id}): {score_msg}")
            
            return result
            
        except (ValueError, TypeError, AttributeError) as e:
            raise ValueError(f"Skor verisi işlenirken hata: {str(e)}")
        
    except Exception as e:
        logging.error(f"❌ Maç sonucu alınırken hata (ID: {match_id}): {str(e)}")
        raise

def get_db_connection():
    """Veritabanı bağlantısı oluşturur"""
    logging.debug("Veritabanı bağlantısı oluşturuluyor...")
    return sqlite3.connect('soccer_analysis.db')

def get_completed_matches() -> List[Dict[str, Any]]:
    """0-0 skorlu maçları veritabanından alır"""
    logging.info("🔍 0-0 skorlu maçlar aranıyor...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # En az 2 saat önce başlamış ve skoru 0-0 olan maçları al
        two_hours_ago = datetime.now(TR_TIMEZONE) - timedelta(hours=2)
        current_date = two_hours_ago.strftime("%Y-%m-%d")
        current_time = two_hours_ago.strftime("%H:%M")
        
        query = """
        SELECT m.match_id, m.match_date, m.match_time, m.league, 
               m.home_team, m.away_team, 
               ms.home_score, ms.away_score, 
               ms.ht_home_score, ms.ht_away_score
        FROM matches m
        INNER JOIN match_scores ms ON m.match_id = ms.match_id
        WHERE (m.match_date < ? OR (m.match_date = ? AND m.match_time <= ?))
        AND ms.home_score = 0 AND ms.away_score = 0
        AND ms.ht_home_score = 0 AND ms.ht_away_score = 0
        ORDER BY m.match_date DESC, m.match_time ASC
        """
        
        cursor.execute(query, (current_date, current_date, current_time))
        matches = cursor.fetchall()
        
        result = []
        for match in matches:
            match_data = {
                'match_id': match[0],
                'match_date': match[1],
                'match_time': match[2],
                'league': match[3],
                'home_team': match[4],
                'away_team': match[5],
                'home_score': match[6],
                'away_score': match[7],
                'ht_home_score': match[8],
                'ht_away_score': match[9]
            }
            result.append(match_data)
            logging.debug(f"0-0 skorlu maç bulundu: {match_data['league']} - {match_data['home_team']} vs {match_data['away_team']}")
        
        logging.info(f"✅ Toplam {len(result)} adet 0-0 skorlu maç bulundu")
        return result
        
    except Exception as e:
        logging.error(f"❌ 0-0 skorlu maçlar alınırken hata: {str(e)}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

def update_match_scores(match_id: int, scores: Dict[str, Any]) -> bool:
    """Maç skorlarını günceller"""
    logging.info(f"📝 Maç skoru güncelleniyor (ID: {match_id})")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Önce mevcut skorları kontrol et
        cursor.execute("""
            SELECT home_score, away_score, ht_home_score, ht_away_score 
            FROM match_scores 
            WHERE match_id = ?
        """, (match_id,))
        
        existing_scores = cursor.fetchone()
        
        if existing_scores:
            logging.debug(f"Mevcut skorlar: MS {existing_scores[0]}-{existing_scores[1]}, İY {existing_scores[2]}-{existing_scores[3]}")
            # Skorlar değişmişse güncelle
            if (existing_scores[0] != scores['home_score'] or 
                existing_scores[1] != scores['away_score'] or
                existing_scores[2] != scores['ht_home_score'] or
                existing_scores[3] != scores['ht_away_score']):
                
                cursor.execute("""
                    UPDATE match_scores 
                    SET home_score = ?,
                        away_score = ?,
                        ht_home_score = ?,
                        ht_away_score = ?
                    WHERE match_id = ?
                """, (
                    scores['home_score'],
                    scores['away_score'],
                    scores['ht_home_score'],
                    scores['ht_away_score'],
                    match_id
                ))
                
                conn.commit()
                logging.info(
                    f"✅ Maç skorları güncellendi (ID: {match_id})\n"
                    f"Eski skor: MS {existing_scores[0]}-{existing_scores[1]}, İY {existing_scores[2]}-{existing_scores[3]}\n"
                    f"Yeni skor: MS {scores['home_score']}-{scores['away_score']}, İY {scores['ht_home_score']}-{scores['ht_away_score']}"
                )
                return True
            else:
                logging.info(f"ℹ️ Skor değişmediği için güncelleme yapılmadı (ID: {match_id})")
                
        else:
            # Skor kaydı yoksa yeni kayıt ekle
            cursor.execute("""
                INSERT INTO match_scores 
                (match_id, home_score, away_score, ht_home_score, ht_away_score)
                VALUES (?, ?, ?, ?, ?)
            """, (
                match_id,
                scores['home_score'],
                scores['away_score'],
                scores['ht_home_score'],
                scores['ht_away_score']
            ))
            
            conn.commit()
            logging.info(
                f"✅ Yeni maç skoru eklendi (ID: {match_id})\n"
                f"Skor: MS {scores['home_score']}-{scores['away_score']}, İY {scores['ht_home_score']}-{scores['ht_away_score']}"
            )
            return True
            
        return False
        
    except Exception as e:
        logging.error(f"❌ Maç skoru güncellenirken hata: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def process_match(match: Dict[str, Any]) -> Tuple[bool, bool, Dict[str, Any]]:
    """Tek bir maçı işler ve sonucu döndürür"""
    try:
        logging.info(f"\n📌 Maç analiz ediliyor:\n"
                    f"Lig: {match['league']}\n"
                    f"Tarih: {match['match_date']} {match['match_time']}\n"
                    f"Maç: {match['home_team']} vs {match['away_team']}")
        
        # API'den maç sonucunu al
        scores = get_match_result(match['match_id'])
        
        # Skoru güncelle
        is_updated = update_match_scores(match['match_id'], scores)
        
        return True, is_updated, match
        
    except Exception as e:
        logging.error(f"❌ Maç analizi sırasında hata (ID: {match['match_id']}): {str(e)}")
        return False, False, match

def process_batch(matches: List[Dict[str, Any]]) -> Tuple[int, int]:
    """Maç grubunu paralel olarak işler"""
    success_count = 0
    update_count = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
        # Tüm maçları paralel olarak işle
        future_to_match = {executor.submit(process_match, match): match for match in matches}
        
        # Sonuçları topla
        for future in concurrent.futures.as_completed(future_to_match):
            match = future_to_match[future]
            try:
                success, updated, _ = future.result()
                if success:
                    success_count += 1
                if updated:
                    update_count += 1
            except Exception as e:
                logging.error(f"❌ Batch işleme hatası (Match ID: {match['match_id']}): {str(e)}")
    
    return success_count, update_count

def analyze_results():
    """0-0 skorlu maçların sonuçlarını analiz eder"""
    logging.info("🚀 0-0 skorlu maçların analizi başlatılıyor...")
    
    try:
        # 0-0 skorlu maçları al
        completed_matches = get_completed_matches()
        total_matches = len(completed_matches)
        logging.info(f"📊 Toplam {total_matches} adet 0-0 skorlu maç bulundu")
        
        if not completed_matches:
            logging.info("ℹ️ İşlenecek 0-0 skorlu maç bulunamadı")
            return True
        
        # İstatistikler
        total_success = 0
        total_updates = 0
        batch_count = 0
        
        # Maçları BATCH_SIZE'lık gruplara böl ve işle
        for i in range(0, total_matches, BATCH_SIZE):
            batch_count += 1
            batch = completed_matches[i:i + BATCH_SIZE]
            
            logging.info(f"\n🔄 Batch #{batch_count} işleniyor ({len(batch)} maç)")
            
            # Batch'i işle ve sonuçları al
            success_count, update_count = process_batch(batch)
            
            # İstatistikleri güncelle
            total_success += success_count
            total_updates += update_count
            
            # Batch özeti
            logging.info(f"✅ Batch #{batch_count} tamamlandı:")
            logging.info(f"📊 Başarılı: {success_count}/{len(batch)}")
            logging.info(f"🔄 Güncellenen: {update_count}")
        
        # Genel özet
        logging.info(f"\n📋 0-0 Skorlu Maç Analiz Özeti:")
        logging.info(f"✅ Toplam başarılı işlenen: {total_success}/{total_matches}")
        logging.info(f"🔄 Toplam güncellenen: {total_updates}")
        logging.info(f"📦 Toplam batch sayısı: {batch_count}")
        logging.info(f"❌ Hata sayısı: {total_matches - total_success}")
        
        return True
        
    except Exception as e:
        logging.error(f"❌ 0-0 skorlu maç analizi sırasında hata: {str(e)}")
        return False

if __name__ == "__main__":
    # Loglama ayarları
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('results.log'),
            logging.StreamHandler()
        ]
    )
    
    logging.info("\n" + "="*50)
    logging.info("🔄 Sonuç analizi başlatılıyor...")
    logging.info("="*50 + "\n")
    
    # Sonuçları analiz et
    analyze_results() 