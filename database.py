import sqlite3
from typing import Dict, Any
from datetime import datetime
import logging

def create_connection():
    """Veritabanı bağlantısı oluşturur"""
    try:
        conn = sqlite3.connect('soccer_analysis.db')
        conn.execute("PRAGMA foreign_keys = ON")  # Foreign key desteğini aktif et
        return conn
    except Exception as e:
        logging.error(f"Veritabanı bağlantısı oluşturulurken hata: {str(e)}")
        raise

def create_tables(conn):
    """Veritabanı tablolarını oluşturur"""
    cursor = conn.cursor()
    
    try:
        # Maç bilgileri tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY,
            match_id INTEGER UNIQUE,
            match_date TEXT,
            match_time TEXT,
            league TEXT COLLATE NOCASE,  -- Case-insensitive arama için
            home_team TEXT,
            away_team TEXT,
            stadium TEXT,
            weather TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Tahminler tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY,
            match_id INTEGER,
            over_prediction TEXT,
            btts_prediction TEXT,
            match_result_prediction TEXT,
            ht_goal_prediction TEXT,
            corner_prediction TEXT,
            risky_prediction TEXT,
            FOREIGN KEY (match_id) REFERENCES matches (match_id)
        )
        ''')
        
        # Gol istatistikleri tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS goal_stats (
            id INTEGER PRIMARY KEY,
            match_id INTEGER,
            home_goal_exp REAL,
            away_goal_exp REAL,
            home_goal_ht_exp REAL,
            away_goal_ht_exp REAL,
            FOREIGN KEY (match_id) REFERENCES matches (match_id)
        )
        ''')
        
        # Yüzdeler tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS percentages (
            id INTEGER PRIMARY KEY,
            match_id INTEGER,
            home_goal_percent TEXT,
            away_goal_percent TEXT,
            over_percent_1 TEXT,
            over_percent_2 TEXT,
            over_percent_3 TEXT,
            match_result_percents TEXT,
            home_goal_ht_percent TEXT,
            away_goal_ht_percent TEXT,
            over_05_ht_percent TEXT,
            over_15_ht_percent TEXT,
            over_25_ht_percent TEXT,
            ht_result_percents TEXT,
            FOREIGN KEY (match_id) REFERENCES matches (match_id)
        )
        ''')
        
        # Son 10 maç tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS last_10_matches (
            id INTEGER PRIMARY KEY,
            match_id INTEGER,
            home_team_results TEXT,
            away_team_results TEXT,
            FOREIGN KEY (match_id) REFERENCES matches (match_id)
        )
        ''')
        
        # Bahis oranları tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS odds (
            id INTEGER PRIMARY KEY,
            match_id INTEGER,
            bookmaker TEXT,
            ms1_opening REAL,
            msx_opening REAL,
            ms2_opening REAL,
            ms1_closing REAL,
            msx_closing REAL,
            ms2_closing REAL,
            ht1_opening REAL,
            htx_opening REAL,
            ht2_opening REAL,
            ht1_closing REAL,
            htx_closing REAL,
            ht2_closing REAL,
            opening_odds REAL,
            opening_goalline REAL,
            opening_side REAL,
            opening_odds_ht REAL,
            opening_goalline_ht REAL,
            opening_side_ht REAL,
            closing_odds REAL,
            closing_goalline REAL,
            closing_side REAL,
            closing_odds_ht REAL,
            closing_goalline_ht REAL,
            closing_side_ht REAL,
            FOREIGN KEY (match_id) REFERENCES matches (match_id)
        )
        ''')
        
        # Korner oranları tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS corner_odds (
            id INTEGER PRIMARY KEY,
            match_id INTEGER,
            bookmaker TEXT,
            over_value REAL,
            over_line REAL,
            under_value REAL,
            is_live BOOLEAN,
            FOREIGN KEY (match_id) REFERENCES matches (match_id)
        )
        ''')
        
        # Çifte şans oranları tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS double_chance_odds (
            id INTEGER PRIMARY KEY,
            match_id INTEGER,
            bookmaker TEXT,
            home_draw_value REAL,
            home_away_value REAL,
            away_draw_value REAL,
            FOREIGN KEY (match_id) REFERENCES matches (match_id)
        )
        ''')
        
        # Skor oranları tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS score_odds (
            id INTEGER PRIMARY KEY,
            match_id INTEGER,
            bookmaker TEXT,
            score_type TEXT,  -- h1, h2, h3, g1, g2, g3, d1, d2, d3 etc.
            odds_value REAL,
            FOREIGN KEY (match_id) REFERENCES matches (match_id)
        )
        ''')
        
        # Maç istatistikleri tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS match_statistics (
            id INTEGER PRIMARY KEY,
            match_id INTEGER,
            team_type TEXT,  -- 'home' veya 'away'
            over_25_last10 INTEGER,
            btts_last10 INTEGER,
            ht_over_05_last10 INTEGER,
            over_35_last10 INTEGER,
            over_15_last10 INTEGER,
            ht_over_15_last10 INTEGER,
            FOREIGN KEY (match_id) REFERENCES matches (match_id)
        )
        ''')
        
        # H2H maçları tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS h2h_matches (
            id INTEGER PRIMARY KEY,
            match_id INTEGER,
            game_date TEXT,
            league TEXT,
            home_team TEXT,
            away_team TEXT,
            score TEXT,
            ht_score TEXT,
            corners TEXT,
            ht_corners TEXT,
            FOREIGN KEY (match_id) REFERENCES matches (match_id)
        )
        ''')
        
        # H2H istatistikleri tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS h2h_statistics (
            id INTEGER PRIMARY KEY,
            match_id INTEGER,
            total_matches INTEGER,
            over_25_count INTEGER,
            btts_count INTEGER,
            ht_over_05_count INTEGER,
            over_35_count INTEGER,
            over_15_count INTEGER,
            ht_over_15_count INTEGER,
            home_wins INTEGER,
            away_wins INTEGER,
            draws INTEGER,
            FOREIGN KEY (match_id) REFERENCES matches (match_id)
        )
        ''')
        
        # Poisson dağılımı tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS poisson_distribution (
            id INTEGER PRIMARY KEY,
            match_id INTEGER,
            distribution_type TEXT,  -- 'total', 'home', 'away', 'total_ht', 'home_ht', 'away_ht'
            goals_0 REAL,
            goals_1 REAL,
            goals_2 REAL,
            goals_3 REAL,
            goals_4 REAL,
            goals_5 REAL,
            FOREIGN KEY (match_id) REFERENCES matches (match_id)
        )
        ''')
        
        # Maç skoru tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS match_scores (
            id INTEGER PRIMARY KEY,
            match_id INTEGER,
            home_score INTEGER,
            away_score INTEGER,
            ht_home_score INTEGER,
            ht_away_score INTEGER,
            FOREIGN KEY (match_id) REFERENCES matches (match_id)
        )
        ''')
        
        conn.commit()
        logging.info("Veritabanı tabloları başarıyla oluşturuldu/güncellendi")
        
    except Exception as e:
        logging.error(f"Tablolar oluşturulurken hata: {str(e)}")
        conn.rollback()
        raise

def format_date(date_str: str) -> str:
    """Tarih formatını standardize eder"""
    try:
        # Gelen tarih formatını kontrol et ve standardize et
        date_formats = [
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y/%m/%d"
        ]
        
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime("%Y-%m-%d")  # ISO format
            except ValueError:
                continue
                
        raise ValueError(f"Geçersiz tarih formatı: {date_str}")
        
    except Exception as e:
        logging.error(f"Tarih formatlanırken hata: {str(e)}")
        raise

def insert_match_info(conn, match_data: Dict[str, Any]):
    """Maç bilgilerini veritabanına ekler veya günceller"""
    cursor = conn.cursor()
    
    try:
        # Tarih formatını standardize et
        match_date = format_date(match_data['info']['mac_tarihi'])
        
        # Önce maçın var olup olmadığını kontrol et
        cursor.execute("""
            SELECT match_id FROM matches 
            WHERE match_id = ?
        """, (match_data['info']['id'],))
        
        existing_match = cursor.fetchone()
        
        if existing_match:
            # Maç varsa güncelle
            cursor.execute("""
                UPDATE matches 
                SET match_date = ?,
                    match_time = ?,
                    league = ?,
                    home_team = ?,
                    away_team = ?,
                    stadium = ?,
                    weather = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE match_id = ?
            """, (
                match_date,
                match_data['info']['mac_saati'],
                match_data['info']['lig'],  # Lig ismi olduğu gibi kullanılıyor
                match_data['info']['mac'].split(' - ')[0],
                match_data['info']['mac'].split(' - ')[1],
                match_data['info']['stadium'],
                match_data['info']['weather'],
                match_data['info']['id']
            ))
            
            logging.info(f"Maç bilgileri güncellendi (ID: {match_data['info']['id']})")
            
        else:
            # Maç yoksa ekle
            cursor.execute("""
                INSERT INTO matches 
                (match_id, match_date, match_time, league, home_team, away_team, stadium, weather)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                match_data['info']['id'],
                match_date,
                match_data['info']['mac_saati'],
                match_data['info']['lig'],  # Lig ismi olduğu gibi kullanılıyor
                match_data['info']['mac'].split(' - ')[0],
                match_data['info']['mac'].split(' - ')[1],
                match_data['info']['stadium'],
                match_data['info']['weather']
            ))
            
            logging.info(f"Yeni maç eklendi (ID: {match_data['info']['id']})")
        
        # Tahminleri güncelle/ekle
        cursor.execute("""
            INSERT OR REPLACE INTO predictions
            (match_id, over_prediction, btts_prediction, match_result_prediction, 
            ht_goal_prediction, corner_prediction, risky_prediction)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            match_data['info']['id'],
            match_data['tahminler'].get('ust_tahmini', ''),
            match_data['tahminler'].get('kg_tahmini', ''),
            match_data['tahminler'].get('ms_tahmini', ''),
            match_data['tahminler'].get('iy_gol_tahmini', ''),
            match_data['tahminler'].get('korner_tahmini', ''),
            match_data['tahminler'].get('riskli_tahmin', '')
        ))
        
        # Gol istatistiklerini ekle
        cursor.execute('''
        INSERT OR REPLACE INTO goal_stats
        (match_id, home_goal_exp, away_goal_exp, home_goal_ht_exp, away_goal_ht_exp)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            match_data['info']['id'],
            match_data['home_away_goal']['home_goal'],
            match_data['home_away_goal']['away_goal'],
            match_data['home_away_goal']['home_goal_ht'],
            match_data['home_away_goal']['away_goal_ht']
        ))
        
        # Yüzdeleri ekle
        cursor.execute('''
        INSERT OR REPLACE INTO percentages
        (match_id, home_goal_percent, away_goal_percent, over_percent_1, over_percent_2,
        over_percent_3, match_result_percents, home_goal_ht_percent, away_goal_ht_percent,
        over_05_ht_percent, over_15_ht_percent, over_25_ht_percent, ht_result_percents)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            match_data['info']['id'],
            match_data['yuzdeler']['ev_gol_yuzdesi'],
            match_data['yuzdeler']['dep_gol_yuzdesi'],
            match_data['yuzdeler']['ust_yuzdesi_1'],
            match_data['yuzdeler']['ust_yuzdesi2'],
            match_data['yuzdeler']['ust_yuzdesi3'],
            match_data['yuzdeler']['ms_yuzdeleri'],
            match_data['yuzdeler']['ev_gol_yuzdesi_ht'],
            match_data['yuzdeler']['dep_gol_yuzdesi_ht'],
            match_data['yuzdeler']['ust_yuzdesi_05_ht'],
            match_data['yuzdeler']['ust_yuzdesi_15_ht'],
            match_data['yuzdeler']['ust_yuzdesi_25_ht'],
            match_data['yuzdeler']['iy_yuzdeleri_']
        ))
        
        # Son 10 maç sonuçlarını ekle
        cursor.execute('''
        INSERT OR REPLACE INTO last_10_matches
        (match_id, home_team_results, away_team_results)
        VALUES (?, ?, ?)
        ''', (
            match_data['info']['id'],
            match_data['son_10_mac']['ev_sahibi'],
            match_data['son_10_mac']['deplasman']
        ))
        
        # Bahis oranlarını ekle (tüm bahis şirketleri için)
        if 'bahis_oranlari' in match_data:
            for bookmaker, odds_data in match_data['bahis_oranlari'].items():
                try:
                    # Acilis ve kapanis verilerinin varlığını kontrol et
                    if 'acilis' not in odds_data or 'kapanis' not in odds_data:
                        logging.warning(f"Bahis oranları için acilis veya kapanis verisi eksik: {bookmaker}")
                        continue
                        
                    cursor.execute('''
                    INSERT OR REPLACE INTO odds
                    (match_id, bookmaker, ms1_opening, msx_opening, ms2_opening,
                    ms1_closing, msx_closing, ms2_closing, ht1_opening, htx_opening,
                    ht2_opening, ht1_closing, htx_closing, ht2_closing, opening_odds,
                    opening_goalline, opening_side, opening_odds_ht, opening_goalline_ht,
                    opening_side_ht, closing_odds, closing_goalline, closing_side,
                    closing_odds_ht, closing_goalline_ht, closing_side_ht)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        match_data['info']['id'],
                        bookmaker,
                        odds_data['acilis'].get('acilis_ms1', ''),
                        odds_data['acilis'].get('acilis_msx', ''),
                        odds_data['acilis'].get('acilis_ms2', ''),
                        odds_data['kapanis'].get('kapanis_ms1', ''),
                        odds_data['kapanis'].get('kapanis_msx', ''),
                        odds_data['kapanis'].get('kapanis_ms2', ''),
                        odds_data['acilis'].get('acilis_iy1', ''),
                        odds_data['acilis'].get('acilis_iyx', ''),
                        odds_data['acilis'].get('acilis_iy2', ''),
                        odds_data['kapanis'].get('kapanis_iy1', ''),
                        odds_data['kapanis'].get('kapanis_iyx', ''),
                        odds_data['kapanis'].get('kapanis_iy2', ''),
                        odds_data['acilis'].get('acilis_oran', ''),
                        odds_data['acilis'].get('acilis_goalline', ''),
                        odds_data['acilis'].get('acilis_taraf', ''),
                        odds_data['acilis'].get('acilis_oran_ht', ''),
                        odds_data['acilis'].get('acilis_goalline_ht', ''),
                        odds_data['acilis'].get('acilis_taraf_ht', ''),
                        odds_data['kapanis'].get('kapanis_oran', ''),
                        odds_data['kapanis'].get('kapanis_goalline', ''),
                        odds_data['kapanis'].get('kapanis_taraf', ''),
                        odds_data['kapanis'].get('kapanis_oran_ht', ''),
                        odds_data['kapanis'].get('kapanis_goalline_ht', ''),
                        odds_data['kapanis'].get('kapanis_taraf_ht', '')
                    ))
                    logging.info(f"Bahis oranları eklendi: {bookmaker}")
                except Exception as e:
                    logging.error(f"Bahis oranları eklenirken hata oluştu ({bookmaker}): {str(e)}")
        
        # Korner oranlarını ekle
        if 'korner_oranlari' in match_data and 'Data' in match_data['korner_oranlari']:
            for odds in match_data['korner_oranlari']['Data'].get('oddsList', []):
                if 'odds' in odds:
                    cursor.execute('''
                    INSERT OR REPLACE INTO corner_odds
                    (match_id, bookmaker, over_value, over_line, under_value, is_live)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        match_data['info']['id'],
                        odds.get('cn', ''),
                        odds['odds']['f'].get('u', 0),
                        odds['odds']['f'].get('g', 0),
                        odds['odds']['f'].get('d', 0),
                        odds.get('hr', False)
                    ))
        
        # Çifte şans oranlarını ekle
        if 'cifte_sans_oranlari' in match_data and 'Data' in match_data['cifte_sans_oranlari']:
            for odds in match_data['cifte_sans_oranlari']['Data'].get('oddsList', []):
                if 'fodds' in odds:
                    cursor.execute('''
                    INSERT OR REPLACE INTO double_chance_odds
                    (match_id, bookmaker, home_draw_value, home_away_value, away_draw_value)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (
                        match_data['info']['id'],
                        odds.get('cid', ''),
                        odds['fodds'].get('u', 0),
                        odds['fodds'].get('g', 0),
                        odds['fodds'].get('d', 0)
                    ))
        
        # Skor oranlarını ekle
        if 'skor_oranlari' in match_data and 'Data' in match_data['skor_oranlari']:
            for odds in match_data['skor_oranlari']['Data'].get('oddsList', []):
                if 'odds' in odds:
                    for score_type, value in odds['odds'].items():
                        if value and value != '':
                            cursor.execute('''
                            INSERT OR REPLACE INTO score_odds
                            (match_id, bookmaker, score_type, odds_value)
                            VALUES (?, ?, ?, ?)
                            ''', (
                                match_data['info']['id'],
                                odds.get('cid', ''),
                                score_type,
                                float(value)
                            ))
        
        # Maç istatistiklerini ekle
        if 'match_statistics' in match_data:
            for team_type in ['home', 'away']:
                stats = match_data['match_statistics'][team_type]['last_10']
                cursor.execute('''
                INSERT OR REPLACE INTO match_statistics
                (match_id, team_type, over_25_last10, btts_last10, ht_over_05_last10,
                over_35_last10, over_15_last10, ht_over_15_last10)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    match_data['info']['id'],
                    team_type,
                    stats['over_25'],
                    stats['btts'],
                    stats['ht_over_05'],
                    stats['over_35'],
                    stats['over_15'],
                    stats['ht_over_15']
                ))
        
        # H2H maçlarını ekle
        if 'h2h_matches' in match_data:
            for match in match_data['h2h_matches'].get('matches', []):
                cursor.execute('''
                INSERT OR REPLACE INTO h2h_matches
                (match_id, game_date, league, home_team, away_team, score, ht_score, corners, ht_corners)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    match_data['info']['id'],
                    match['date'],
                    match['league'],
                    match['home_team'],
                    match['away_team'],
                    match['score'],
                    match['ht_score'],
                    match['corners'],
                    match['ht_corners']
                ))
        
        # H2H istatistiklerini ekle
        if 'h2h_matches' in match_data and 'statistics' in match_data['h2h_matches']:
            stats = match_data['h2h_matches']['statistics']
            cursor.execute('''
            INSERT OR REPLACE INTO h2h_statistics
            (match_id, total_matches, over_25_count, btts_count, ht_over_05_count,
            over_35_count, over_15_count, ht_over_15_count, home_wins, away_wins, draws)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                match_data['info']['id'],
                stats['total_matches'],
                stats['over_25'],
                stats['btts'],
                stats['ht_over_05'],
                stats['over_35'],
                stats['over_15'],
                stats['ht_over_15'],
                stats['home_wins'],
                stats['away_wins'],
                stats['draws']
            ))
        
        # Poisson dağılımını ekle
        if 'poisson' in match_data and 'poisson' in match_data['poisson']:
            for dist_type, values in match_data['poisson']['poisson'].items():
                cursor.execute('''
                INSERT OR REPLACE INTO poisson_distribution
                (match_id, distribution_type, goals_0, goals_1, goals_2, goals_3, goals_4, goals_5)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    match_data['info']['id'],
                    dist_type,
                    values.get('0', 0),
                    values.get('1', 0),
                    values.get('2', 0),
                    values.get('3', 0),
                    values.get('4', 0),
                    values.get('5', 0)
                ))
        
        # Maç skorunu ekle
        if 'score' in match_data:
            home_score = 0
            away_score = 0
            ht_home_score = 0
            ht_away_score = 0
            
            # Tam maç skoru
            if match_data['score'].get('home_score') is not None and match_data['score'].get('away_score') is not None:
                try:
                    home_score = int(match_data['score']['home_score'])
                    away_score = int(match_data['score']['away_score'])
                except (ValueError, TypeError):
                    home_score = 0
                    away_score = 0
            
            # İlk yarı skoru
            if match_data['score'].get('ht_score'):
                try:
                    ht_scores = match_data['score']['ht_score'].split('-')
                    ht_home_score = int(ht_scores[0])
                    ht_away_score = int(ht_scores[1])
                except (ValueError, TypeError, IndexError):
                    ht_home_score = 0
                    ht_away_score = 0
            
            cursor.execute('''
            INSERT OR REPLACE INTO match_scores
            (match_id, home_score, away_score, ht_home_score, ht_away_score)
            VALUES (?, ?, ?, ?, ?)
            ''', (
                match_data['info']['id'],
                home_score,
                away_score,
                ht_home_score,
                ht_away_score
            ))
        
        conn.commit()
        logging.info(f"Maç bilgileri başarıyla kaydedildi (ID: {match_data['info']['id']})")
        
    except Exception as e:
        error_msg = f"Maç bilgileri kaydedilirken hata: {type(e).__name__}: {str(e)}"
        logging.error(error_msg)
        conn.rollback()
        raise

def update_database_schema(conn):
    """Veritabanı şemasını günceller, yeni sütunlar ekler"""
    cursor = conn.cursor()
    
    try:
        # Odds tablosunda yeni sütunların varlığını kontrol et
        cursor.execute("PRAGMA table_info(odds)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Yeni sütunları ekle
        new_columns = {
            "opening_odds": "REAL",
            "opening_goalline": "REAL",
            "opening_side": "REAL",
            "opening_odds_ht": "REAL",
            "opening_goalline_ht": "REAL",
            "opening_side_ht": "REAL",
            "closing_odds": "REAL",
            "closing_goalline": "REAL",
            "closing_side": "REAL",
            "closing_odds_ht": "REAL",
            "closing_goalline_ht": "REAL",
            "closing_side_ht": "REAL"
        }
        
        for column_name, column_type in new_columns.items():
            if column_name not in columns:
                cursor.execute(f"ALTER TABLE odds ADD COLUMN {column_name} {column_type}")
                logging.info(f"Yeni sütun eklendi: {column_name}")
        
        conn.commit()
        logging.info("Veritabanı şeması güncellendi")
        
    except Exception as e:
        error_msg = f"Veritabanı şeması güncellenirken hata: {type(e).__name__}: {str(e)}"
        logging.error(error_msg)
        conn.rollback()
        raise