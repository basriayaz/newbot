import sqlite3
from datetime import datetime
import random
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
import logging
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai
import pytz

# .env dosyasını yükle
load_dotenv()

# Türkiye saat dilimi
TR_TIMEZONE = pytz.timezone('Europe/Istanbul')

# Major ligler listesi
MAJOR_LEAGUES = [
    'Spanish La Liga',
    'English Premier League',
    'German Bundesliga',
    'German Bundesliga 2',
    'Italian Serie A',
    'Italian Serie B',
    'French Ligue 1',
    'Turkey Super Lig',
    'Uefa Champions League',
    'Uefa Europa League',
    'Uefa Europa Conference League',
    'England Championship',
    'Uefa Nations League'
    'Spanish La Liga 2',
    'Liga Portugal 1',
    'Holland Eredivisie',
    'Belgium Pro League',
    'Switzerland Super League',
    'Austrian Bundesliga',
]

# Reklam şablonları
AD_TEMPLATES = [
    {
        "image": "images/ramen.jpg",
        "text": "Global Yeni Güvenilir Bahis&Casino Sitesi Ramenbet artık Türkiye'de!\n\n"
                "60.000 TL'ye kadar İlk Para Yatırma Bonusu!\n"
                "300 TL FREEBET!\n\n"
                "Ramenbet'e üye ol 👉\n\n"
                "Not: 💯💯Güven Onayı ✅\n\n"
                "Kayıt: https://bit.ly/40JD3GU"
    },
    {
        "image": None,  # henüz görsel yok
        "text": "İskoçyalı & Simyacı'nın ortak VIP kanalında bol bol kazanç fırsatı seni bekliyor! 🍀\n\n"
                "✅ Günün Türkiye İdeal ve Riskli kuponları 🏆\n"
                "✅ Sürpriz kuponlar📊\n"
                "✅ Süper Lig tahminleri ⚽️\n"
                "✅ Özel oyuncu istatistik tahminleri 🎯\n"
                "✅ Maçlar hakkında genel ön bilgiler 🔍\n"
                "✅ Günün tahmin listeleri (2.5 üst/iy 0.5 üst) 📋\n"
                "➡️ Ve bol bol canlı tahminler olacak! ✨\n\n"
                "💬 Katılmak için @alchemiist1 veya @iskocyalii ile iletişime geçin!\n\n"
                "Kazançlı bir haftasonu için doğru yerdesiniz! 💸✅"
    },
    {
        "image": "images/meta.jpg",
        "text": "1️⃣0️⃣🔤 YAP 2️⃣0️⃣🔤 ÇEK\n\n"
                "⭐️100₺ yatır / 1000₺ yap /2000₺ çek\n"
                "⭐️250₺ yatır / 2500₺ yap / 5000₺ çek\n"
                "⭐️500₺ yatır / 5000₺ yap / 10000₺ çek\n\n"
                "🧡Bu promosyon 100₺ ile 500₺ arası yapacağınız yatırıma özeldir.\n\n"
                "🧡Spor alanında kombine kuponda her maç oranı minimum 1.65 olacak şekilde bahis alınmalıdır.\n\n"
                "🧡 Casino alanında 4 katı çevirim şartı mevcuttur.\n\n"
                "🧡Yatırım miktarınızın 10 katı bakiyeye ulaştıktan sonra 20 katı çekim yapabilirsiniz.\n\n"
                "🧡Yatırım sağladıktan sonra bakiyenizin kullanmadan canlı destek hattına bağlanarak bonusunuzu talep etmeyi unutmayınız!!!\n\n"
                "✅ https://www.metabetaff.com/go/343434"
    },
    {
        "image": "images/mega.jpg",
        "text": "🎁KAMPANYA 🎁\n\n"
                "Verdiğimiz Mega Linkinden kayıt olup yatırım yapan herkesin kazanacağı ayrıcalıklar 💪\n\n"
                "➡️1 Aylık tipstergpt.com üyeliği 🤖\n"
                "➡️1 Aylık Canlı ve Günün Listelerinin bulunduğu VIP grup 😀\n\n"
                "Yatırım sonrası @iskocyalii adresinden iletişime geçmeniz yeterli olacaktır💎\n"
                "(Min yatırım 500₺)\n\n"
                "➡️KAYIT OL: bit.ly/megapari_iskocyali"
    }
]

# Günlük mesaj şablonları
GOOD_MORNING_MESSAGES = {
    0: "🌅 Günaydın! Yeni bir haftaya başlıyoruz. Herkese Bol kazançlı bir gün diliyorum ⚽",  # Pazartesi
    1: "🌞 Günaydın! Salı günü güzel maçlar var. Analizlerimiz hazır! Herkese bol kazançlı bir gün diliyorum 📊",  # Salı
    2: "🌄 Günaydın! Herkese bol kazançlı bir gün diliyorum Kazandırmaya devam edeceğiz💪",  # Çarşamba
    3: "🌅 Günaydın! Yeni bir günden herkese merhaba! Kazanmaya Hazır mısınız? ⚽",  # Perşembe
    4: "🌞 Günaydın! Bugün harika maçlar var. Sizin için özel analizlerimiz hazır! 📈",  # Cuma
    5: "🌄 Günaydın! Hafta sonu geldi, kazanmanın zamanıdır! Analizlerimiz hazır! ⚽Herkese bol kazançlı bir gün diliyorum",  # Cumartesi
    6: "🌅 Günaydın! Pazar günü futbol şöleni ile birlikteyiz! 🎯Herkese bol kazançlı bir gün diliyorum"  # Pazar
}

# İyi geceler mesajları
GOOD_NIGHT_MESSAGES = {
    0: "🌙 İyi geceler! Haftanın ilk gününü geride bıraktık. Yarın yeni tahminlerle buluşmak üzere! 💤",  # Pazartesi
    1: "🌃 İyi geceler! Bugünkü analizlerimizle kazananlar olduğunu umuyoruz. Yarın görüşmek üzere! 🌠",  # Salı
    2: "🌉 İyi geceler! Haftanın ortasındayız, yarın yeni tahminlerle devam edeceğiz. Tatlı rüyalar! 💫",  # Çarşamba
    3: "🌌 İyi geceler! Bugünkü maçlar umarız istediğiniz gibi geçmiştir. Yarın yeni analizlerle buradayız! 🌟",  # Perşembe
    4: "🌆 İyi geceler! Hafta sonu maçları için hazırlıklarımız tamam. Yarın görüşmek üzere! 🏆",  # Cuma
    5: "🌃 İyi geceler! Cumartesi maçlarını geride bıraktık. Yarın futbol şöleni devam ediyor! 💤",  # Cumartesi
    6: "🌙 İyi geceler! Bir haftalık futbol maratonunu tamamladık. Yarın yeni bir haftaya başlıyoruz! 🌠"  # Pazar
}

READY_MESSAGES = {
    "matches": [
        "📢 Günün maçları hazır! Bekleyenler burada mı? 🤔\n\n⚽ Özel analizlerimiz birazdan sizlerle! 🎯",
        "🔔 Günün maç analizleri hazırlandı! Kazanmaya hazır mısınız? 📊\n\n⚽ Birazdan paylaşıyoruz! 🎯",
        "📣 Dikkat! Günün maçları için analizlerimiz hazır! 🔍\n\n⚽ Tahminlerimiz birazdan yayında! 🎯",
        "🚨 Günün maçları için özel analizlerimiz tamamlandı! 📈\n\n⚽ Birazdan sizlerle paylaşacağız! 🎯",
        "📌 Günün maç tahminleri için hazırlıklarımız tamam! 🎮\n\n⚽ Analizlerimiz birazdan sizlerle! 🎯"
    ],
    "coupon": [
        "🎯 Günün kuponu hazırlanıyor!\n\n⚽ Bekleyenler varsa biraz sonra kuponu paylaşacağız! 📈",
        "🎫 Günün özel kuponu için son kontroller yapılıyor!\n\n⚽ Birazdan sizlerle paylaşacağız! 💰",
        "🎲 Günün kazandıran kuponu hazır olmak üzere!\n\n⚽ Takipte kalın, birazdan yayınlıyoruz! 📊",
        "🏆 Günün yüksek oranlı kuponu hazırlanıyor!\n\n⚽ Kazanmak isteyenler için birazdan paylaşımda olacağız! 💸",
        "📝 Günün kuponu için son dokunuşlar yapılıyor!\n\n⚽ Birazdan sizlerle buluşacak! 🔥"
    ],
    "ht_goals": [
        "⏱ Günün İlk Yarı Gol Listesi hazırlanıyor!\n\n⚽ Özel analizlerimiz birazdan sizlerle! 🎯",
        "⌛ İlk Yarı Gol Listesi için son kontroller yapılıyor!\n\n⚽ Birazdan paylaşıyoruz! 📊",
        "🕒 Günün İlk Yarı Gol tahminleri hazır olmak üzere!\n\n⚽ Takipte kalın, birazdan yayında! 🎯",
        "⏰ İlk Yarı Gol Listesi için analizlerimiz tamamlandı!\n\n⚽ Birazdan sizlerle paylaşacağız! 📈",
        "⌚ Günün İlk Yarı Gol tahminleri için hazırlıklarımız tamam!\n\n⚽ Birazdan sizlerle! 🎮"
    ],
    "risky": [
        "⚠️ Günün Riskli Kuponları hazırlanıyor!\n\n⚽ Cesur olanlar için birazdan paylaşımda olacağız! 🔥",
        "🎲 Riskli ama yüksek oranlı tahminlerimiz hazır olmak üzere!\n\n⚽ Birazdan sizlerle! 💰",
        "🚨 Günün Riskli Kuponları için son kontroller yapılıyor!\n\n⚽ Takipte kalın, birazdan yayında! 📊",
        "⚡ Yüksek oranlı riskli tahminlerimiz hazırlanıyor!\n\n⚽ Birazdan paylaşıyoruz! 💸",
        "🔥 Günün Riskli Kuponları için analizlerimiz tamamlandı!\n\n⚽ Cesur olanlar için birazdan yayında! 🎯"
    ],
    "special": [
        "🌟 Günün Özel Tahminleri hazırlanıyor!\n\n⚽ VIP analizlerimiz birazdan sizlerle! 💎",
        "💎 Özel tahmin listesi için son kontroller yapılıyor!\n\n⚽ Birazdan paylaşıyoruz! 🏆",
        "🏅 Günün Özel Tahminleri hazır olmak üzere!\n\n⚽ Takipte kalın, birazdan yayında! 📊",
        "👑 VIP tahminlerimiz için analizlerimiz tamamlandı!\n\n⚽ Birazdan sizlerle paylaşacağız! 💰",
        "🔮 Günün Özel Tahminleri için hazırlıklarımız tamam!\n\n⚽ Birazdan sizlerle! 🎮"
    ]
}

# Varsayılan yorumlar listesi
DEFAULT_COMMENTS = [
    "⚽ Analizlerimiz ve istatistikler bu tahmini destekliyor. Sizce de öyle mi? 🎯",
    "📊 Veriler bu maç için olumlu sinyaller veriyor. Katılıyor musunuz? ⚽",
    "🎯 İstatistiksel veriler tahminimizi güçlü bir şekilde destekliyor. Ne düşünüyorsunuz? ⚽",
    "⚽ Uzman ekibimiz bu tahmine güveniyor. Siz bu konuda ne düşünüyorsunuz? 🎯",
    "🎯 Bu tahmin için analizlerimiz oldukça pozitif. Siz ne düşünüyorsunuz? ⚽",
    "⚽ İstatistikler ve analizler bu seçimi destekliyor. Katılıyor musunuz? 🎯",
    "📈 Tahmin modelimiz bu maç için oldukça iddialı. Siz ne düşünüyorsunuz? ⚽",
    "⚽ Veriler ve analizler bu tahmini işaret ediyor. Katılıyor musunuz? 🎯",
    "🎯 Uzman ekibimiz bu tahmine güveniyor. Sizin görüşünüz nedir? ⚽",
    "⚽ İstatistikler bu maç için net konuşuyor. Siz ne dersiniz? 🎯"
]

# Global variable to keep track of current ad index
_current_ad_index = 0

def get_db_connection():
    """Veritabanı bağlantısı oluşturur"""
    return sqlite3.connect('soccer_analysis.db')

def get_major_league_predictions() -> List[Dict[str, Any]]:
    """Major liglerden tahminleri alır"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Bugünün tarihini Türkiye saatine göre al
        today = datetime.now(TR_TIMEZONE).strftime("%Y-%m-%d")
        logging.info(f"Aranan tarih: {today}")
        
        # Major ligler için placeholder oluştur
        placeholders = ','.join(['?' for _ in MAJOR_LEAGUES])
        
        query = f"""
        SELECT m.match_id, m.league, m.home_team, m.away_team, m.match_time,
               p.over_prediction, p.btts_prediction, p.match_result_prediction,
               p.ht_goal_prediction, p.risky_prediction
        FROM matches m
        LEFT JOIN predictions p ON m.match_id = p.match_id
        WHERE m.match_date = ?
        AND m.league IN ({placeholders})
        AND (
            p.over_prediction IS NOT NULL OR 
            p.btts_prediction IS NOT NULL OR 
            p.match_result_prediction IS NOT NULL OR
            p.risky_prediction IS NOT NULL OR
            p.ht_goal_prediction IS NOT NULL
        )
        AND (
            LENGTH(TRIM(COALESCE(p.over_prediction, ''))) > 0 OR
            LENGTH(TRIM(COALESCE(p.btts_prediction, ''))) > 0 OR
            LENGTH(TRIM(COALESCE(p.match_result_prediction, ''))) > 0 OR
            LENGTH(TRIM(COALESCE(p.risky_prediction, ''))) > 0 OR
            LENGTH(TRIM(COALESCE(p.ht_goal_prediction, ''))) > 0
        )
        ORDER BY m.match_time ASC
        """
        
        # Parametreleri hazırla: önce tarih, sonra major ligler
        params = [today] + MAJOR_LEAGUES
        cursor.execute(query, params)
        predictions = cursor.fetchall()
        
        if not predictions:
            logging.warning(f"Bugün için hiç tahmin bulunamadı.")
            return []
        
        logging.info(f"Toplam {len(predictions)} tahmin bulundu")
        
        result = []
        for pred in predictions:
            try:
                prediction = {
                    'match_id': pred[0],
                    'league': pred[1],
                    'home_team': pred[2],
                    'away_team': pred[3],
                    'match_time': pred[4],
                    'over_prediction': pred[5],
                    'btts_prediction': pred[6],
                    'match_result_prediction': pred[7],
                    'ht_goal_prediction': pred[8],
                    'risky_prediction': pred[9]
                }
                result.append(prediction)
                
            except Exception as e:
                logging.error(f"Tahmin verisi işlenirken hata: {type(e).__name__}: {str(e)}")
                continue
        
        return result
        
    except Exception as e:
        logging.error(f"Major lig tahminleri alınırken hata: {type(e).__name__}: {str(e)}")
        return []
        
    finally:
        if 'conn' in locals():
            conn.close()

def get_ht_goals_predictions() -> List[Dict[str, Any]]:
    """İlk yarı gol tahminlerini alır"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Bugünün tarihini Türkiye saatine göre al
        today = datetime.now(TR_TIMEZONE).strftime("%Y-%m-%d")
        
        query = """
        SELECT DISTINCT m.match_id, m.league, m.home_team, m.away_team, m.match_time,
               p.ht_goal_prediction, 
               COALESCE(pc.over_05_ht_percent, '0%') as over_05_ht_percent,
               COALESCE(pc.over_15_ht_percent, '0%') as over_15_ht_percent,
               o.opening_goalline, o.closing_goalline,
               o.opening_goalline_ht, o.closing_goalline_ht
        FROM matches m
        LEFT JOIN predictions p ON m.match_id = p.match_id
        LEFT JOIN percentages pc ON m.match_id = pc.match_id
        LEFT JOIN odds o ON m.match_id = o.match_id AND o.bookmaker = 'Bet365'
        WHERE m.match_date = ?
        AND p.ht_goal_prediction IS NOT NULL
        AND LENGTH(TRIM(p.ht_goal_prediction)) > 0
        ORDER BY m.match_time ASC
        """
        
        cursor.execute(query, (today,))
        predictions = cursor.fetchall()
        
        # Benzersiz maçları tutmak için set kullanıyoruz
        seen_match_ids = set()
        result = []
        
        for pred in predictions:
            try:
                match_id = pred[0]
                
                # Eğer bu maç daha önce eklenmediyse
                if match_id not in seen_match_ids:
                    # Yüzde işaretini kaldır ve integer'a çevir
                    over_05_percent = pred[6].replace('%', '') if pred[6] else '0'
                    over_15_percent = pred[7].replace('%', '') if pred[7] else '0'
                    
                    # İlk yarı kapanış goalline değeri 1'den küçük olan maçları filtrele
                    closing_goalline_ht = pred[11]
                    if closing_goalline_ht is not None and float(closing_goalline_ht) < 1:
                        continue
                    
                    prediction = {
                        'match_id': match_id,
                        'league': pred[1],
                        'home_team': pred[2],
                        'away_team': pred[3],
                        'match_time': pred[4],
                        'ht_goal_prediction': pred[5],
                        'over_05_ht_percent': int(over_05_percent),
                        'over_15_ht_percent': int(over_15_percent),
                        'opening_goalline': pred[8],
                        'closing_goalline': pred[9],
                        'opening_goalline_ht': pred[10],
                        'closing_goalline_ht': pred[11]
                    }
                    result.append(prediction)
                    seen_match_ids.add(match_id)
            except Exception as e:
                logging.error(f"Tahmin verisi işlenirken hata: {str(e)}")
                continue
        
        return result
        
    except Exception as e:
        logging.error(f"İY gol tahminleri alınırken hata: {str(e)}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

def create_ht_goals_table_image(predictions: List[Dict[str, Any]]) -> List[str]:
    """İlk yarı gol tahminlerini görsel tablo olarak oluşturur"""
    
    # Font paths - Local fonts directory
    FONT_PATHS = [
        "fonts/Helvetica.ttf",         # Primary font
        "fonts/Arial.ttf",             # Fallback font 1
        "fonts/DejaVuSans.ttf"         # Fallback font 2
    ]
    
    def get_available_font(size: int) -> ImageFont.FreeTypeFont:
        """Kullanılabilir bir font döndürür"""
        # Önce fonts klasörünün varlığını kontrol et
        if not os.path.exists('fonts'):
            os.makedirs('fonts')
            logging.info("fonts klasörü oluşturuldu")
        
        # Font dosyalarının varlığını kontrol et
        missing_fonts = [font for font in FONT_PATHS if not os.path.exists(font)]
        if missing_fonts:
            logging.warning(f"Eksik font dosyaları: {missing_fonts}")
            logging.warning("Lütfen font dosyalarını fonts/ klasörüne ekleyin")
        
        # Mevcut fontları dene
        for font_path in FONT_PATHS:
            try:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)
            except Exception as e:
                logging.warning(f"Font yüklenemedi ({font_path}): {e}")
                continue
        
        # Sistem fontlarını dene
        system_fonts = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "/System/Library/Fonts/Helvetica.ttc",              # macOS
            "C:\\Windows\\Fonts\\arial.ttf"                     # Windows
        ]
        
        for font_path in system_fonts:
            try:
                if os.path.exists(font_path):
                    return ImageFont.truetype(font_path, size)
            except Exception as e:
                logging.warning(f"Sistem fontu yüklenemedi ({font_path}): {e}")
                continue
        
        logging.error("Hiçbir font yüklenemedi, varsayılan font kullanılıyor")
        return ImageFont.load_default()
    
    # Font boyutları
    title_font_size = 48
    header_font_size = 32  # Başlık font boyutunu küçülttük
    content_font_size = 28
    
    # Renk tanımları
    background_color = (240, 242, 245)  # Arka plan rengi
    header_bg_color = (46, 204, 113)    # Yeşil başlık (önceden mavi idi)
    text_color = (44, 62, 80)           # Koyu mavi-gri metin
    header_text_color = (255, 255, 255)  # Beyaz başlık metni
    border_color = (189, 195, 199)      # Şık gri kenarlık
    alt_row_color = (236, 240, 241)     # Alternatif satır rengi
    increase_color = (46, 204, 113)     # Yeşil (artış için)
    decrease_color = (231, 76, 60)      # Kırmızı (azalış için)
    
    # Sütun genişlikleri
    time_width = 100      # Saat sütunu genişliği
    league_width = 300    # Lig sütunu genişliği (250'den 300'e arttırıldı)
    match_width = 550     # Maç sütunu genişliği
    prediction_width = 150 # Tahmin sütunu genişliği
    percent_width = 150   # Yüzde sütunları genişliği
    goalline_width = 150  # Goalline sütunları genişliği
    
    # Satır yüksekliği ve kenar boşlukları
    row_height = 55
    header_height = 80
    title_height = 100
    margin = 40
    padding = 20
    
    # Maksimum karakter uzunlukları
    max_league_chars = 20
    max_match_chars = 40
    
    def truncate_text(text: str, max_chars: int) -> str:
        """Metni belirli bir uzunlukta kısaltır"""
        if not text:
            return ""
        text = text.strip()
        if len(text) <= max_chars:
            return text
        return text[:max_chars-3] + "..."
    
    def get_centered_text_position(text: str, font, available_width: int, x_start: int) -> int:
        """Metni yatayda ortalamak için x pozisyonunu hesaplar"""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        return x_start + (available_width - text_width) // 2
    
    # Tahminleri gruplara ayır
    max_predictions_per_image = 40
    prediction_groups = [predictions[i:i + max_predictions_per_image] 
                        for i in range(0, len(predictions), max_predictions_per_image)]
    
    image_paths = []
    
    for group_index, group in enumerate(prediction_groups, 1):
        # Görsel boyutları
        total_width = time_width + league_width + match_width + prediction_width + (percent_width * 2) + (goalline_width * 4) + (margin * 2)
        total_height = (title_height + header_height + 
                       (row_height * len(group)) + (margin * 2))
        
        # Yeni görsel oluştur
        img = Image.new('RGB', (total_width, total_height), background_color)
        draw = ImageDraw.Draw(img)
        
        # Fontları yükle
        title_font = get_available_font(title_font_size)
        header_font = get_available_font(header_font_size)
        content_font = get_available_font(content_font_size)
        
        # Başlık
        title_text = f"İlk Yarı Gol Listesi {group_index}/{len(prediction_groups)}"
        title_x = get_centered_text_position(title_text, title_font, total_width, 0)
        draw.text(
            (title_x, margin),
            title_text,
            font=title_font,
            fill=header_bg_color
        )
        
        # Başlık altı çizgisi
        y_pos = margin + title_height - 10
        draw.line([(margin, y_pos), (total_width - margin, y_pos)], 
                 fill=header_bg_color, width=3)
        
        # Başlık alanı
        header_y = margin + title_height
        draw.rectangle(
            [(margin, header_y),
             (total_width - margin, header_y + header_height)],
            fill=header_bg_color,
            width=0
        )
        
        # Başlık metinleri - Kısaltılmış başlıklar
        x_pos = margin
        headers = ["Saat", "Lig", "Maç", "Tahmin", "0.5 Üst", "1.5 Üst", 
                  "Açılış", "Kapanış", "İY Açılış", "İY Kapanış"]
        widths = [time_width, league_width, match_width, prediction_width, percent_width, percent_width, 
                 goalline_width, goalline_width, goalline_width, goalline_width]
        
        for header, width in zip(headers, widths):
            text_x = get_centered_text_position(header, header_font, width, x_pos)
            draw.text(
                (text_x, header_y + (header_height - header_font_size) // 2),
                header,
                font=header_font,
                fill=header_text_color
            )
            x_pos += width
        
        # İçerik
        y_pos = margin + title_height + header_height
        for i, pred in enumerate(group):
            # Her satır için dikdörtgen çiz (kenarlık için)
            draw.rectangle(
                [(margin, y_pos),
                 (total_width - margin, y_pos + row_height)],
                fill=alt_row_color if i % 2 == 0 else background_color,
                outline=border_color,
                width=1
            )
            
            x_pos = margin
            
            # Saat
            time_text = pred['match_time']
            text_x = get_centered_text_position(time_text, content_font, time_width, x_pos)
            draw.text(
                (text_x, y_pos + (row_height - content_font_size) // 2),
                time_text,
                font=content_font,
                fill=text_color
            )
            
            # Lig
            x_pos += time_width
            league = truncate_text(pred['league'], max_league_chars)
            league_x = x_pos + padding
            draw.text(
                (league_x, y_pos + (row_height - content_font_size) // 2),
                league,
                font=content_font,
                fill=text_color
            )
            
            # Maç
            x_pos += league_width
            match = truncate_text(f"{pred['home_team']} - {pred['away_team']}", max_match_chars)
            match_x = x_pos + padding
            draw.text(
                (match_x, y_pos + (row_height - content_font_size) // 2),
                match,
                font=content_font,
                fill=text_color
            )
            
            # Tahmin
            x_pos += match_width
            prediction = pred['ht_goal_prediction']
            text_x = get_centered_text_position(prediction, content_font, prediction_width, x_pos)
            draw.text(
                (text_x, y_pos + (row_height - content_font_size) // 2),
                prediction,
                font=content_font,
                fill=text_color
            )
            
            # İY 0.5 Üst Yüzdesi
            x_pos += prediction_width
            over_05_text = f"%{pred['over_05_ht_percent']}"
            text_x = get_centered_text_position(over_05_text, content_font, percent_width, x_pos)
            draw.text(
                (text_x, y_pos + (row_height - content_font_size) // 2),
                over_05_text,
                font=content_font,
                fill=text_color
            )
            
            # İY 1.5 Üst Yüzdesi
            x_pos += percent_width
            over_15_text = f"%{pred['over_15_ht_percent']}"
            text_x = get_centered_text_position(over_15_text, content_font, percent_width, x_pos)
            draw.text(
                (text_x, y_pos + (row_height - content_font_size) // 2),
                over_15_text,
                font=content_font,
                fill=text_color
            )
            
            # Açılış Goalline
            x_pos += percent_width
            opening_gl = str(pred.get('opening_goalline', '-')) if pred.get('opening_goalline') is not None else '-'
            text_x = get_centered_text_position(opening_gl, content_font, goalline_width, x_pos)
            draw.text(
                (text_x, y_pos + (row_height - content_font_size) // 2),
                opening_gl,
                font=content_font,
                fill=text_color
            )
            
            # Kapanış Goalline - Renk kodlaması
            x_pos += goalline_width
            closing_gl = str(pred.get('closing_goalline', '-')) if pred.get('closing_goalline') is not None else '-'
            text_x = get_centered_text_position(closing_gl, content_font, goalline_width, x_pos)
            
            # Renk kodlaması için değerleri karşılaştır
            cell_color = text_color
            cell_bg_color = None
            
            try:
                if (pred.get('opening_goalline') is not None and 
                    pred.get('closing_goalline') is not None):
                    opening_val = float(pred['opening_goalline'])
                    closing_val = float(pred['closing_goalline'])
                    
                    if closing_val > opening_val:
                        cell_bg_color = increase_color
                    elif closing_val < opening_val:
                        cell_bg_color = decrease_color
            except (ValueError, TypeError):
                pass
                
            # Arka plan rengi varsa, önce onu çiz
            if cell_bg_color:
                draw.rectangle(
                    [(x_pos, y_pos), (x_pos + goalline_width, y_pos + row_height)],
                    fill=cell_bg_color
                )
                
            draw.text(
                (text_x, y_pos + (row_height - content_font_size) // 2),
                closing_gl,
                font=content_font,
                fill=header_text_color if cell_bg_color else text_color
            )
            
            # Açılış Goalline İY
            x_pos += goalline_width
            opening_gl_ht = str(pred.get('opening_goalline_ht', '-')) if pred.get('opening_goalline_ht') is not None else '-'
            text_x = get_centered_text_position(opening_gl_ht, content_font, goalline_width, x_pos)
            draw.text(
                (text_x, y_pos + (row_height - content_font_size) // 2),
                opening_gl_ht,
                font=content_font,
                fill=text_color
            )
            
            # Kapanış Goalline İY - Renk kodlaması
            x_pos += goalline_width
            closing_gl_ht = str(pred.get('closing_goalline_ht', '-')) if pred.get('closing_goalline_ht') is not None else '-'
            text_x = get_centered_text_position(closing_gl_ht, content_font, goalline_width, x_pos)
            
            # Renk kodlaması için değerleri karşılaştır
            cell_color = text_color
            cell_bg_color = None
            
            try:
                if (pred.get('opening_goalline_ht') is not None and 
                    pred.get('closing_goalline_ht') is not None):
                    opening_val = float(pred['opening_goalline_ht'])
                    closing_val = float(pred['closing_goalline_ht'])
                    
                    if closing_val > opening_val:
                        cell_bg_color = increase_color
                    elif closing_val < opening_val:
                        cell_bg_color = decrease_color
            except (ValueError, TypeError):
                pass
                
            # Arka plan rengi varsa, önce onu çiz
            if cell_bg_color:
                draw.rectangle(
                    [(x_pos, y_pos), (x_pos + goalline_width, y_pos + row_height)],
                    fill=cell_bg_color
                )
                
            draw.text(
                (text_x, y_pos + (row_height - content_font_size) // 2),
                closing_gl_ht,
                font=content_font,
                fill=header_text_color if cell_bg_color else text_color
            )
            
            y_pos += row_height
        
        # Dış kenarlık
        draw.rectangle(
            [(margin, margin + title_height),
             (total_width - margin, total_height - margin)],
            outline=header_bg_color,
            width=2
        )
        
        # Dikey çizgiler
        x_pos = margin
        for width in widths[:-1]:  # Son sütun hariç her sütun arasına çizgi
            x_pos += width
            draw.line(
                [(x_pos, margin + title_height),
                 (x_pos, total_height - margin)],
                fill=border_color,
                width=2
            )
        
        # Başlık altı çizgisi (kalın)
        y_pos = margin + title_height + header_height
        draw.line(
            [(margin, y_pos),
             (total_width - margin, y_pos)],
            fill=header_bg_color,
            width=2
        )
        
        # Görüntüyü kaydet
        image_path = f'ht_goals_table_{group_index}.png'
        img.save(image_path)
        image_paths.append(image_path)
    
    return image_paths

def generate_prediction_comment(prediction: Dict[str, Any]) -> str:
    """Tahmin için yorum oluşturur"""
    try:
        # Eğer tahmin verisi eksikse veya geçersizse
        if not prediction or not isinstance(prediction, dict):
            return random.choice(DEFAULT_COMMENTS)
            
        # Rastgele bir yorum seç
        return random.choice(DEFAULT_COMMENTS)
            
    except Exception as e:
        logging.error(f"Yorum oluşturulurken hata: {str(e)}")
        return random.choice(DEFAULT_COMMENTS)

def get_ai_comment(prediction: Dict[str, Any]) -> str:
    """Gemini AI'dan tahmin için yorum alır"""
    try:
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Tahmin bilgilerini metin haline getir
        match_info = f"Lig: {prediction['league']}\n"
        match_info += f"Maç: {prediction['home_team']} vs {prediction['away_team']}\n"
        
        if prediction.get('match_result_prediction'):
            match_info += f"Maç Sonucu Tahmini: {prediction['match_result_prediction']}\n"
        if prediction.get('over_prediction'):
            match_info += f"Gol Tahmini: {prediction['over_prediction']}\n"
        if prediction.get('ht_goal_prediction'):
            match_info += f"İlk Yarı Gol Tahmini: {prediction['ht_goal_prediction']}\n"
        if prediction.get('risky_prediction'):
            match_info += f"Riskli Tahmin: {prediction['risky_prediction']}\n"
            
        prompt = f"""Aşağıdaki futbol maç tahminini analiz et ve 2 cümlelik profesyonel bir yorum yaz.
        Yorumun ilk cümlesi tahminle ilgili olumlu bir analiz, ikinci cümlesi ise dikkat edilmesi gereken bir nokta olsun.
        Yanıt maksimum 2 cümle olmalı.
        
        {match_info}"""
        
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        logging.error(f"AI yorum alınırken hata: {str(e)}")
        return "AI yorumu alınamadı."

def format_prediction_message(prediction: Dict[str, Any]) -> str:
    """Tahmin mesajını formatlar"""
    try:
        if not prediction:
            raise ValueError("Tahmin verisi boş")
            
        # Temel kontroller
        required_fields = ['league', 'home_team', 'away_team', 'match_time']
        missing_fields = [field for field in required_fields if not prediction.get(field)]
        if missing_fields:
            raise ValueError(f"Eksik alanlar: {', '.join(missing_fields)}")
        
        # Bugünün tarihini Türkiye saatine göre al
        today = datetime.now(TR_TIMEZONE).strftime("%Y-%m-%d")
        display_date = datetime.strptime(today, "%Y-%m-%d").strftime("%d/%m/%Y")
            
        message = f"🏆 {prediction['league']}\n"
        message += f"⚽ {prediction['home_team']} - {prediction['away_team']}\n"
        message += f"📅 {display_date} | ⏰ {prediction['match_time']}\n\n"
        
        # Tahminleri kontrol et ve ekle
        predictions_found = False
        
        if prediction.get('match_result_prediction') and prediction['match_result_prediction'].strip():
            message += f"📊 Maç Sonucu: {prediction['match_result_prediction']}\n"
            predictions_found = True
            
        if prediction.get('over_prediction') and prediction['over_prediction'].strip():
            message += f"📈 Gol Tahmini: {prediction['over_prediction']}\n"
            predictions_found = True
            
        if prediction.get('ht_goal_prediction') and prediction['ht_goal_prediction'].strip():
            message += f"⏱ İY: {prediction['ht_goal_prediction']}\n"
            predictions_found = True
            
        if prediction.get('risky_prediction') and prediction['risky_prediction'].strip():
            message += f"⚠️ Riskli Tahmin: {prediction['risky_prediction']}\n"
            predictions_found = True
            
        if not predictions_found:
            logging.error(f"Maç tahminleri (ID: {prediction.get('match_id')}):")
            logging.error(f"MS: {prediction.get('match_result_prediction')}")
            logging.error(f"Gol: {prediction.get('over_prediction')}")
            logging.error(f"İY: {prediction.get('ht_goal_prediction')}")
            logging.error(f"Riskli: {prediction.get('risky_prediction')}")
            raise ValueError(f"Geçerli tahmin bulunamadı (Maç ID: {prediction.get('match_id', '?')})")
        
        # AI yorumunu al ve ekle
        ai_comment = get_ai_comment(prediction)
        message += f"\n🤖 AI Yorumu:\n{ai_comment}\n"
        
        # Site linkini ekle
        message += "\n🌐 tipstergpt.com"
        
        return message
        
    except Exception as e:
        error_msg = f"Tahmin mesajı formatlanırken hata: {type(e).__name__}: {str(e)}"
        logging.error(error_msg)
        raise ValueError(error_msg)

def create_daily_coupon(predictions: List[Dict[str, Any]], match_count: int = 3) -> str:
    """Günlük kupon oluşturur"""
    try:
        if not predictions:
            return "❌ Tahmin bulunamadı"
            
        # Geçerli tahminleri filtrele
        valid_predictions = []
        for pred in predictions:
            if (pred.get('match_result_prediction') or 
                pred.get('over_prediction') or 
                pred.get('btts_prediction')):
                valid_predictions.append(pred)
                
        if len(valid_predictions) < match_count:
            return f"❌ Yeterli tahmin bulunamadı (Mevcut: {len(valid_predictions)}, Gerekli: {match_count})"
        
        selected_matches = random.sample(valid_predictions, match_count)
        
        message = "🔥 🎯 GÜNÜN KUPONU 🔥\n\n"
        
        for i, match in enumerate(selected_matches, 1):
            try:
                message += f"{i}. {match['league']}\n"
                message += f"   {match['home_team']} vs {match['away_team']}\n"
                message += f"   🕒 {match['match_time']}\n"
                
                # En iyi tahmini seç
                prediction = None
                
                if match.get('match_result_prediction'):
                    prediction = f"Maç Sonucu: {match['match_result_prediction']}"
                elif match.get('over_prediction'):
                    prediction = f"Gol Beklentisi: {match['over_prediction']}"
                elif match.get('btts_prediction'):
                    prediction = f"KG: {match['btts_prediction']}"
                
                if not prediction:
                    logging.warning(f"Maç için tahmin bulunamadı: {match['home_team']} vs {match['away_team']}")
                    continue
                    
                message += f"   📊 {prediction}\n\n"
                
            except Exception as e:
                logging.error(f"Kupon maçı formatlanırken hata: {type(e).__name__}: {str(e)}")
                continue
        
        return message
        
    except Exception as e:
        error_msg = f"Kupon oluşturulurken hata: {type(e).__name__}: {str(e)}"
        logging.error(error_msg)
        return f"❌ {error_msg}"

def get_next_ad() -> Dict[str, Any]:
    """Sıradaki reklamı döndürür"""
    global _current_ad_index
    ad = AD_TEMPLATES[_current_ad_index]
    _current_ad_index = (_current_ad_index + 1) % len(AD_TEMPLATES)  # Cycle through ads
    return ad

def get_random_ad() -> Dict[str, Any]:
    """Rastgele bir reklam şablonu seçer (legacy support)"""
    return random.choice(AD_TEMPLATES)

def get_daily_predictions(count: int = 1) -> List[Dict[str, Any]]:
    """Günlük tahminleri alır"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Bugünün tarihini Türkiye saatine göre al
        today = datetime.now(TR_TIMEZONE).strftime("%Y-%m-%d")
        
        # Major ligler için placeholder oluştur
        placeholders = ','.join(['?' for _ in MAJOR_LEAGUES])
        
        query = f"""
        SELECT m.match_id, m.league, m.home_team, m.away_team, m.match_time,
               p.over_prediction, p.btts_prediction, p.match_result_prediction,
               p.ht_goal_prediction, p.risky_prediction
        FROM matches m
        LEFT JOIN predictions p ON m.match_id = p.match_id
        WHERE m.match_date = ?
        AND m.league IN ({placeholders})
        AND (
            p.over_prediction IS NOT NULL OR 
            p.btts_prediction IS NOT NULL OR 
            p.match_result_prediction IS NOT NULL OR
            p.risky_prediction IS NOT NULL
        )
        AND (
            LENGTH(TRIM(COALESCE(p.over_prediction, ''))) > 0 OR
            LENGTH(TRIM(COALESCE(p.btts_prediction, ''))) > 0 OR
            LENGTH(TRIM(COALESCE(p.match_result_prediction, ''))) > 0 OR
            LENGTH(TRIM(COALESCE(p.risky_prediction, ''))) > 0
        )
        ORDER BY RANDOM()
        LIMIT ?
        """
        
        # Parametreleri hazırla: önce tarih, sonra major ligler, en son limit
        params = [today] + MAJOR_LEAGUES + [count]
        cursor.execute(query, params)
        predictions = cursor.fetchall()
        
        result = []
        for pred in predictions:
            prediction = {
                'match_id': pred[0],
                'league': pred[1],
                'home_team': pred[2],
                'away_team': pred[3],
                'match_time': pred[4],
                'over_prediction': pred[5],
                'btts_prediction': pred[6],
                'match_result_prediction': pred[7],
                'ht_goal_prediction': pred[8],
                'risky_prediction': pred[9]
            }
            result.append(prediction)
        
        return result
        
    except Exception as e:
        logging.error(f"Günlük tahminler alınırken hata: {str(e)}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

def get_good_morning_message() -> str:
    """Günün günaydın mesajını döndürür"""
    # Türkiye saatine göre haftanın gününü al
    weekday = datetime.now(TR_TIMEZONE).weekday()
    return GOOD_MORNING_MESSAGES.get(weekday, GOOD_MORNING_MESSAGES[0])

def get_ready_message(message_type: str) -> str:
    """Hazırlık mesajını döndürür"""
    messages = READY_MESSAGES.get(message_type, [])
    if not messages:
        return ""
    return random.choice(messages)

def get_good_night_message() -> str:
    """Günün iyi geceler mesajını döndürür"""
    # Türkiye saatine göre haftanın gününü al
    weekday = datetime.now(TR_TIMEZONE).weekday()
    return GOOD_NIGHT_MESSAGES.get(weekday, GOOD_NIGHT_MESSAGES[0]) 