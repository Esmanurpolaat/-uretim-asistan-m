import sqlite3

def fix_database():
    conn = sqlite3.connect("uretim_asistanim.db")
    cursor = conn.cursor()
    
    # 1. 'Yeni' statüsündeki siparişlerin üretim hattı atamasını temizle (çünkü henüz planlanmadılar)
    cursor.execute("UPDATE orders SET production_line = NULL WHERE status = 'Yeni'")
    
    # 2. Hatların kapasitelerini mantıklı seviyelere çek (SPL-01: 15000, SPL-02: 20000, SPL-03: 12000)
    cursor.execute("UPDATE production_lines SET capacity = 15000 WHERE line_name = 'SPL-01'")
    cursor.execute("UPDATE production_lines SET capacity = 20000 WHERE line_name = 'SPL-02'")
    cursor.execute("UPDATE production_lines SET capacity = 12000 WHERE line_name = 'SPL-03'")
    
    conn.commit()
    print("Database values successfully updated to logical and realistic levels!")
    
    # Kontrol et
    print("\n--- GÜNCEL HAT DURUMLARI ---")
    cursor.execute("SELECT line_name, capacity FROM production_lines")
    for r in cursor.fetchall():
        print(r)
        
    print("\n--- AKTİF YÜK ALTINDAKİ SİPARİŞLER (Planlandı veya Üretimde) ---")
    cursor.execute("SELECT order_no, quantity, production_line, status FROM orders WHERE status IN ('Planlandı', 'Üretimde')")
    for r in cursor.fetchall():
        print(r)
        
    conn.close()

if __name__ == "__main__":
    fix_database()
