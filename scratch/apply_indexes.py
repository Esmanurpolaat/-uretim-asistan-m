import sqlite3

def apply_indexes():
    conn = sqlite3.connect("uretim_asistanim.db")
    cursor = conn.cursor()
    
    print("Oluşturulacak indeksler listeleniyor...")
    index_queries = [
        "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)",
        "CREATE INDEX IF NOT EXISTS idx_orders_production_line ON orders(production_line)",
        "CREATE INDEX IF NOT EXISTS idx_orders_estimated_delivery_date ON orders(estimated_delivery_date)",
        "CREATE INDEX IF NOT EXISTS idx_warehouse_stocks_raw_material_id ON warehouse_stocks(raw_material_id)"
    ]
    
    for query in index_queries:
        print(f"Çalıştırılıyor: {query}")
        cursor.execute(query)
        
    conn.commit()
    print("İndeksler başarıyla veritabanına uygulandı (Commited).")
    
    # Doğrulama: Tüm indeksleri listele
    print("\n--- MEVCUT VERİTABANI İNDEKSLERİ ---")
    cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type = 'index'")
    for name, tbl_name in cursor.fetchall():
        print(f"İndeks Adı: {name} | Ait Olduğu Tablo: {tbl_name}")
        
    conn.close()

if __name__ == "__main__":
    apply_indexes()
