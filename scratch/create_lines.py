# scratch/create_lines.py
import sqlite3

def create_and_seed_lines():
    # Proje dizinindeki veritabanı dosyasına doğrudan bağlanıyoruz
    conn = sqlite3.connect("uretim_asistanim.db")
    cursor = conn.cursor()
    
    try:
        # 1. Adım: Eğer tablo önceden varsa siliyoruz (temiz bir başlangıç için)
        cursor.execute("DROP TABLE IF EXISTS production_lines;")
        
        # 2. Adım: Yeni tabloyu oluşturuyoruz (Sorumlunun bahsettiği CREATE TABLE SQL komutu)
        cursor.execute("""
            CREATE TABLE production_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                line_name TEXT NOT NULL,
                capacity INTEGER,
                operator_name TEXT
            );
        """)
        print("1. 'production_lines' tablosu SQL komutuyla başarıyla oluşturuldu.")
        
        # 3. Adım: Tabloya test verileri ekliyoruz (INSERT INTO SQL komutu)
        sample_lines = [
            ("SPL-01", 5000, "Ahmet Yılmaz"),
            ("SPL-02", 7500, "Elif Kaya"),
            ("SPL-03", 4000, "Murat Demir")
        ]
        
        cursor.executemany("""
            INSERT INTO production_lines (line_name, capacity, operator_name)
            VALUES (?, ?, ?);
        """, sample_lines)
        
        # Değişiklikleri veritabanı dosyasına kaydediyoruz (Commit)
        conn.commit()
        print("2. 3 adet örnek üretim hattı verisi tabloya başarıyla yazıldı.")
        
    except Exception as e:
        print(f"Bir hata oluştu: {e}")
        conn.rollback()
    finally:
        # Bağlantıyı kapatıyoruz
        conn.close()

if __name__ == "__main__":
    create_and_seed_lines()
