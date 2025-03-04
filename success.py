import sqlite3
import pandas as pd
import logging
from datetime import datetime
import pytz
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Türkiye saat dilimi
TR_TIMEZONE = pytz.timezone('Europe/Istanbul')

def get_db_connection():
    """Veritabanı bağlantısı oluşturur"""
    logging.debug("Veritabanı bağlantısı oluşturuluyor...")
    return sqlite3.connect('soccer_analysis.db')

def get_match_data(start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
    """Veritabanından maç verilerini alır"""
    logging.info("🔍 Maç verileri alınıyor...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
        SELECT 
            m.match_date,
            m.league,
            m.home_team,
            m.away_team,
            p.over_prediction,
            p.btts_prediction,
            p.match_result_prediction,
            p.ht_goal_prediction,
            p.risky_prediction,
            ms.ht_home_score,
            ms.ht_away_score,
            ms.home_score,
            ms.away_score
        FROM matches m
        LEFT JOIN predictions p ON m.match_id = p.match_id
        LEFT JOIN match_scores ms ON m.match_id = ms.match_id
        WHERE ms.home_score IS NOT NULL
        """
        
        params = []
        if start_date:
            query += " AND m.match_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND m.match_date <= ?"
            params.append(end_date)
            
        query += " ORDER BY m.match_date DESC, m.match_time ASC"
        
        cursor.execute(query, params)
        matches = cursor.fetchall()
        
        result = []
        for match in matches:
            match_data = {
                'Tarih': match[0],
                'Lig': match[1],
                'Maç': f"{match[2]} - {match[3]}",
                'Üst Tahmini': match[4] if match[4] else '-',
                'KG Tahmini': match[5] if match[5] else '-',
                'MS Tahmini': match[6] if match[6] else '-',
                'İY Gol Tahmini': match[7] if match[7] else '-',
                'Riskli Tahmin': match[8] if match[8] else '-',
                'İY Skor': f"{match[9]}-{match[10]}" if match[9] is not None and match[10] is not None else '-',
                'MS Skor': f"{match[11]}-{match[12]}" if match[11] is not None and match[12] is not None else '-'
            }
            result.append(match_data)
            logging.debug(f"Maç verisi alındı: {match_data['Maç']}")
        
        logging.info(f"✅ Toplam {len(result)} maç verisi alındı")
        return result
        
    except Exception as e:
        logging.error(f"❌ Maç verileri alınırken hata: {str(e)}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

def export_to_excel(matches: List[Dict[str, Any]], filename: str = None) -> bool:
    """Maç verilerini Excel dosyasına aktarır"""
    try:
        if not matches:
            logging.warning("⚠️ Aktarılacak veri bulunamadı")
            return False
            
        # Varsayılan dosya adı
        if not filename:
            current_date = datetime.now(TR_TIMEZONE).strftime("%Y%m%d")
            filename = f"mac_analiz_{current_date}.xlsx"
        
        # DataFrame oluştur
        df = pd.DataFrame(matches)
        
        # Sütun sıralaması
        columns = [
            'Tarih',
            'Lig',
            'Maç',
            'Üst Tahmini',
            'KG Tahmini',
            'MS Tahmini',
            'İY Gol Tahmini',
            'Riskli Tahmin',
            'İY Skor',
            'MS Skor'
        ]
        
        # Excel yazıcı
        writer = pd.ExcelWriter(filename, engine='xlsxwriter')
        
        # DataFrame'i Excel'e yaz
        df[columns].to_excel(writer, sheet_name='Maç Analizi', index=False)
        
        # Excel çalışma kitabı ve sayfası
        workbook = writer.book
        worksheet = writer.sheets['Maç Analizi']
        
        # Format tanımlamaları
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#0066cc',
            'font_color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        
        cell_format = workbook.add_format({
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        
        # Sütun genişliklerini ayarla
        worksheet.set_column('A:A', 12)  # Tarih
        worksheet.set_column('B:B', 20)  # Lig
        worksheet.set_column('C:C', 35)  # Maç
        worksheet.set_column('D:H', 15)  # Tahminler
        worksheet.set_column('I:J', 10)  # Skorlar
        
        # Başlık formatını uygula
        for col_num, value in enumerate(columns):
            worksheet.write(0, col_num, value, header_format)
        
        # Hücre formatını uygula
        for row in range(1, len(matches) + 1):
            for col in range(len(columns)):
                worksheet.write(row, col, df.iloc[row-1][columns[col]], cell_format)
        
        # Excel dosyasını kaydet
        writer.close()
        
        logging.info(f"✅ Veriler başarıyla '{filename}' dosyasına kaydedildi")
        return True
        
    except Exception as e:
        logging.error(f"❌ Excel dosyası oluşturulurken hata: {str(e)}")
        return False

def analyze_success(start_date: str = None, end_date: str = None, filename: str = None):
    """Maç verilerini analiz eder ve Excel'e aktarır"""
    logging.info("🚀 Başarı analizi başlatılıyor...")
    
    try:
        # Maç verilerini al
        matches = get_match_data(start_date, end_date)
        
        if not matches:
            logging.warning("⚠️ Analiz edilecek maç bulunamadı")
            return False
        
        # Excel'e aktar
        if export_to_excel(matches, filename):
            return True
        
        return False
        
    except Exception as e:
        logging.error(f"❌ Analiz sırasında hata: {str(e)}")
        return False

if __name__ == "__main__":
    # Loglama ayarları
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('success.log'),
            logging.StreamHandler()
        ]
    )
    
    logging.info("\n" + "="*50)
    logging.info("🔄 Başarı analizi başlatılıyor...")
    logging.info("="*50 + "\n")
    
    # Örnek kullanım:
    # Belirli tarih aralığı için analiz
    # analyze_success(start_date="2024-03-01", end_date="2024-03-20")
    
    # Tüm zamanlar için analiz
    analyze_success() 