import schedule
import time
from datetime import datetime, timedelta
import pytz
from bot import process_matches
from telegram_bot import send_message, cleanup, send_photo
from message_handler import (
    get_major_league_predictions, get_ht_goals_predictions,
    format_prediction_message, create_ht_goals_table_image,
    get_random_ad, create_daily_coupon, generate_prediction_comment,
    get_good_morning_message, get_ready_message
)
import logging
import sys
import atexit
import os

# Türkiye saat dilimi
TR_TIMEZONE = pytz.timezone('Europe/Istanbul')

# Haftanın günleri için günaydın mesajları
GOOD_MORNING_MESSAGES = {
    0: "Herkese mutlu haftalar! ☀️ Yeni bir hafta, yeni fırsatlarla başlıyor. Günün maçları için hazır mısınız? ⚽",
    1: "Günaydın! 🌅 Salı gününe enerjik bir başlangıç yapalım. Bugün de heyecan dolu maçlar bizi bekliyor! ⚽",
    2: "Günaydın! 🌞 Haftanın ortasında futbol heyecanı devam ediyor. Bugünün maçlarını kaçırmayın! ⚽",
    3: "Güzel bir Perşembe gününden herkese merhaba! 🌄 Bugün de birbirinden önemli maçlar var. ⚽",
    4: "Haftanın son iş gününden herkese günaydın! 🌅 Cuma günü futbol şöleni başlıyor! ⚽",
    5: "Günaydın! 🌞 Hafta sonu futbol heyecanına hazır mısınız? Bugün harika maçlar bizi bekliyor! ⚽",
    6: "Pazar gününden herkese günaydın! 🌅 Haftanın son gününde futbol şöleni devam ediyor! ⚽"
}

def is_turkish_time(hour: int, minute: int = 0) -> bool:
    """Verilen saatin Türkiye saati olup olmadığını kontrol eder"""
    now = datetime.now(TR_TIMEZONE)
    return now.hour == hour and now.minute == minute

def daily_match_analysis():
    """Günlük maç analizlerini yapar"""
    logging.info("Günlük maç analizi başlatılıyor...")
    try:
        process_matches()
        send_message("✅ Günün maçları analiz edildi ve veritabanına kaydedildi.")
    except Exception as e:
        error_msg = f"❌ Maç analizi sırasında hata oluştu: {str(e)}"
        logging.error(error_msg)
        send_message(error_msg)

def send_good_morning():
    """Günaydın mesajı gönderir"""
    try:
        weekday = datetime.now(TR_TIMEZONE).weekday()
        message = GOOD_MORNING_MESSAGES.get(weekday, "Günaydın! ⚽")
        send_message(message)
    except Exception as e:
        logging.error(f"Günaydın mesajı gönderilirken hata oluştu: {e}")

def send_daily_matches_ready():
    """Günün maçları hazır mesajı gönderir"""
    try:
        message = "🎯 Günün maçları hazır!\n\n" \
                 "📊 Analizler tamamlandı ve sistem hazır.\n" \
                 "👥 Bekleyenler burada mı?"
        send_message(message)
    except Exception as e:
        logging.error(f"Maç hazır mesajı gönderilirken hata oluştu: {e}")

def send_first_prediction():
    """Günün ilk tahminini gönderir"""
    logging.info("İlk tahmin gönderme işlemi başlatılıyor...")
    try:
        predictions = get_major_league_predictions()
        logging.info(f"Veritabanından {len(predictions) if predictions else 0} tahmin alındı")
        
        if not predictions:
            error_msg = "❌ Veritabanında tahmin bulunamadı"
            logging.warning(error_msg)
            send_message(error_msg)
            return
        
        try:
            prediction = predictions[0]
            message = format_prediction_message(prediction)
            logging.info("Tahmin mesajı formatlandı")
            
            if message:
                send_message(message)
                logging.info("İlk tahmin başarıyla gönderildi")
            else:
                error_msg = "❌ Tahmin mesajı oluşturulamadı"
                logging.error(error_msg)
                send_message(error_msg)
                
        except IndexError:
            error_msg = "❌ Tahmin listesi boş"
            logging.error(error_msg)
            send_message(error_msg)
            
        except Exception as e:
            error_msg = f"❌ Tahmin mesajı oluşturulurken hata: {type(e).__name__}: {str(e)}"
            logging.error(error_msg)
            send_message(error_msg)
            
    except Exception as e:
        error_msg = f"❌ İlk tahmin gönderilirken hata: {type(e).__name__}: {str(e)}"
        logging.error(error_msg)
        send_message(error_msg)

def send_second_prediction():
    """Günün ikinci tahminini gönderir"""
    try:
        predictions = get_major_league_predictions()
        if len(predictions) > 1:
            prediction = predictions[1]
            message = format_prediction_message(prediction)
            send_message(message)
    except Exception as e:
        logging.error(f"İkinci tahmin gönderilirken hata oluştu: {e}")

def send_advertisement():
    """Reklam gönderisi paylaşır"""
    try:
        ad = get_random_ad()
        if os.path.exists(ad['image']):
            send_photo(ad['image'], ad['text'])
        else:
            send_message(ad['text'])
    except Exception as e:
        logging.error(f"Reklam gönderilirken hata oluştu: {e}")

def send_third_prediction():
    """Günün üçüncü tahminini gönderir"""
    try:
        predictions = get_major_league_predictions()
        if len(predictions) > 2:
            prediction = predictions[2]
            message = format_prediction_message(prediction)
            send_message(message)
    except Exception as e:
        logging.error(f"Üçüncü tahmin gönderilirken hata oluştu: {e}")

def send_fourth_prediction():
    """Günün dördüncü tahminini gönderir"""
    try:
        predictions = get_major_league_predictions()
        if len(predictions) > 3:
            prediction = predictions[3]
            message = format_prediction_message(prediction)
            send_message(message)
    except Exception as e:
        logging.error(f"Dördüncü tahmin gönderilirken hata oluştu: {e}")

def send_coupon_announcement():
    """Günün kuponu hazır mesajını gönderir"""
    try:
        message = "🎯 Günün kuponu hazırlanıyor...\n\n" \
                 "📊 Major liglerden özel seçimler\n" \
                 "👥 Bekleyenleri görelim!"
        send_message(message)
    except Exception as e:
        logging.error(f"Kupon duyurusu gönderilirken hata oluştu: {e}")

def send_daily_coupon():
    """Günün kuponunu gönderir"""
    logging.info("Günün kuponu oluşturma işlemi başlatılıyor...")
    try:
        predictions = get_major_league_predictions()
        logging.info(f"Veritabanından {len(predictions) if predictions else 0} tahmin alındı")
        
        if not predictions:
            error_msg = "❌ Veritabanında tahmin bulunamadı"
            logging.warning(error_msg)
            send_message(error_msg)
            return
        
        try:
            message = create_daily_coupon(predictions)
            logging.info("Kupon mesajı oluşturuldu")
            
            if message.startswith("❌"):
                logging.warning(message)
            
            send_message(message)
            logging.info("Günün kuponu başarıyla gönderildi")
            
        except Exception as e:
            error_msg = f"❌ Kupon mesajı oluşturulurken hata: {type(e).__name__}: {str(e)}"
            logging.error(error_msg)
            send_message(error_msg)
            
    except Exception as e:
        error_msg = f"❌ Günün kuponu gönderilirken hata: {type(e).__name__}: {str(e)}"
        logging.error(error_msg)
        send_message(error_msg)

def send_ht_goals_announcement():
    """İlk yarı gol listesi duyurusunu gönderir"""
    try:
        message = "⚽ İlk Yarı Gol Listesi hazırlanıyor...\n\n" \
                 "📊 Özel algoritma ile seçilmiş maçlar\n" \
                 "👥 Bekleyenleri görelim!"
        send_message(message)
    except Exception as e:
        logging.error(f"İY gol duyurusu gönderilirken hata oluştu: {e}")

def send_ht_goals_list():
    """İlk yarı gol listesini görsel olarak gönderir"""
    logging.info("İlk yarı gol listesi oluşturma işlemi başlatılıyor...")
    try:
        predictions = get_ht_goals_predictions()
        logging.info(f"Veritabanından {len(predictions) if predictions else 0} ilk yarı gol tahmini alındı")
        
        if not predictions:
            error_msg = "❌ Veritabanında ilk yarı gol tahmini bulunamadı"
            logging.warning(error_msg)
            send_message(error_msg)
            return
        
        try:
            # Tablo görsellerini oluştur
            image_paths = create_ht_goals_table_image(predictions)
            logging.info(f"{len(image_paths)} adet ilk yarı gol listesi görseli oluşturuldu")
            
            # Görselleri gönder
            for i, image_path in enumerate(image_paths, 1):
                caption = f"📊 GÜNÜN İLK YARI GOL LİSTESİ"
                if len(image_paths) > 1:
                    caption += f" ({i}/{len(image_paths)})"
                photo_message = send_photo(image_path, caption)
                logging.info(f"İlk yarı gol listesi görseli {i} başarıyla gönderildi")
                
                # Görseli sil
                try:
                    os.remove(image_path)
                except Exception as e:
                    logging.warning(f"Görsel silinirken hata: {str(e)}")
                
        except Exception as e:
            error_msg = f"❌ İlk yarı gol listesi görseli oluşturulurken hata: {type(e).__name__}: {str(e)}"
            logging.error(error_msg)
            send_message(error_msg)
            
    except Exception as e:
        error_msg = f"❌ İlk yarı gol listesi gönderilirken hata: {type(e).__name__}: {str(e)}"
        logging.error(error_msg)
        send_message(error_msg)

def send_major_league_predictions():
    """Major lig tahminlerini gönderir"""
    logging.info("Major lig tahminleri gönderme işlemi başlatılıyor...")
    try:
        predictions = get_major_league_predictions()
        logging.info(f"Veritabanından {len(predictions) if predictions else 0} major lig tahmini alındı")
        
        if not predictions:
            error_msg = "❌ Veritabanında major lig tahmini bulunamadı"
            logging.warning(error_msg)
            send_message(error_msg)
            return
            
        for prediction in predictions:
            try:
                # Tahmin mesajını oluştur ve gönder
                message = format_prediction_message(prediction)
                prediction_message = send_message(message)
                logging.info(f"Tahmin mesajı başarıyla gönderildi ({prediction['home_team']} vs {prediction['away_team']})")
                
            except Exception as e:
                error_msg = f"❌ Tahmin gönderilirken hata: {type(e).__name__}: {str(e)}"
                logging.error(error_msg)
                continue
                
    except Exception as e:
        error_msg = f"❌ Major lig tahminleri gönderilirken hata: {type(e).__name__}: {str(e)}"
        logging.error(error_msg)
        send_message(error_msg)

def test_all_functions():
    """Tüm fonksiyonları test eder"""
    print("🔄 Test başlatılıyor...")
    
    functions_to_test = [
        ("Maç analizi", daily_match_analysis),
        ("Günaydın mesajı", send_good_morning),
        ("Maçlar hazır mesajı", send_daily_matches_ready),
        ("İlk tahmin", send_first_prediction),
        ("İkinci tahmin", send_second_prediction),
        ("Reklam", send_advertisement),
        ("Üçüncü tahmin", send_third_prediction),
        ("Dördüncü tahmin", send_fourth_prediction),
        ("Kupon duyurusu", send_coupon_announcement),
        ("Günün kuponu", send_daily_coupon),
        ("İY gol duyurusu", send_ht_goals_announcement),
        ("İY gol listesi", send_ht_goals_list),
    ]
    
    for name, func in functions_to_test:
        try:
            print(f"\n📋 {name} testi...")
            func()
            print(f"✅ {name} başarılı")
        except Exception as e:
            print(f"❌ {name} hatası: {e}")
    
    print("\n🏁 Test tamamlandı!")
    cleanup()

def run_scheduler():
    """Zamanlanmış görevleri çalıştırır"""
    # Mevcut görevler
    schedule.every().day.at("07:00").do(daily_match_analysis)
    schedule.every().day.at("10:50").do(send_good_morning)
    schedule.every().day.at("11:30").do(send_daily_matches_ready)
    
    # Yeni görevler
    schedule.every().day.at("12:00").do(send_first_prediction)
    schedule.every().day.at("12:03").do(send_second_prediction)
    schedule.every().day.at("13:00").do(send_advertisement)
    schedule.every().day.at("13:30").do(send_third_prediction)
    schedule.every().day.at("13:33").do(send_fourth_prediction)
    schedule.every().day.at("13:50").do(send_coupon_announcement)
    schedule.every().day.at("14:20").do(send_daily_coupon)
    schedule.every().day.at("15:00").do(send_ht_goals_announcement)
    schedule.every().day.at("15:30").do(send_ht_goals_list)
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(30)
        except Exception as e:
            logging.error(f"Scheduler çalışırken hata oluştu: {e}")
            time.sleep(300)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('scheduler.log'),
            logging.StreamHandler()
        ]
    )
    
    # Program sonlandığında temizlik yap
    atexit.register(cleanup)
    
    # Komut satırı argümanlarını kontrol et
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_all_functions()
    else:
        print("🤖 Bot başlatılıyor... (Test için 'python scheduler.py test' komutunu kullanın)")
        run_scheduler() 