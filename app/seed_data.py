# app/seed_data.py
from datetime import date
from app.database import SessionLocal
# Yeni modellerimizin hepsini içe aktarıyoruz
from app.models import Order, ProductionLine, Product, RawMaterial, Recipe, WarehouseStock

def seed_orders():
    """
    Veritabanını sıfırdan kurduğumuzda, tüm ilişkisel tabloları
    (Üretim Hatları, Ürünler, Hammaddeler, Stoklar, Reçeteler ve Siparişler)
    gerçekçi test verileriyle dolduran yardımcı fonksiyon.
    """
    db = SessionLocal()
    try:
        # Eğer veritabanında zaten ürün varsa mükerrer eklemeyi önlemek için atlıyoruz.
        if db.query(Product).first() is not None:
            print("Veritabanında ürün verisi zaten mevcut, seed işlemi atlandı.")
            return

        print("Veritabanı seed işlemi başlatılıyor...")

        # 1. ADIM: Üretim Hatlarını (Makineleri) Ekle
        sample_lines = [
            ProductionLine(line_name="SPL-01", capacity=5000, operator_name="Ahmet Yılmaz"),
            ProductionLine(line_name="SPL-02", capacity=7500, operator_name="Elif Kaya"),
            ProductionLine(line_name="SPL-03", capacity=4000, operator_name="Murat Demir"),
        ]
        db.add_all(sample_lines)
        db.flush() # ID'lerin oluşması için geçici olarak veritabanına gönderiyoruz
        print("- Üretim hatları eklendi.")

        # 2. ADIM: Ürün Kataloğunu Ekle
        p1 = Product(product_code="URN-SPN01", product_name="Spunbond Kumaş", product_group="Spunbond", standard_width=160.0, grammage=50.0, unit="Metre", eligible_lines="SPL-01,SPL-02")
        p2 = Product(product_code="URN-MEL02", product_name="Meltblown Filtre", product_group="Meltblown", standard_width=160.0, grammage=25.0, unit="Metre", eligible_lines="SPL-03")
        p3 = Product(product_code="URN-SMS03", product_name="SMS Maske Kumaşı", product_group="SMS", standard_width=160.0, grammage=40.0, unit="Metre", eligible_lines="SPL-01,SPL-02")
        db.add_all([p1, p2, p3])
        db.flush()
        print("- Ürün kataloğu oluşturuldu.")

        # 3. ADIM: Hammaddeleri Ekle
        rm1 = RawMaterial(material_code="RAW-PP01", material_name="Polipropilen Granül", material_type="Polimer", unit="Kg", min_stock=1000.0, safety_stock=500.0, min_order_qty=1000.0, lead_time=5)
        rm2 = RawMaterial(material_code="RAW-COL02", material_name="Mavi Masterbatch Boya", material_type="Katkı Maddesi", unit="Kg", min_stock=200.0, safety_stock=100.0, min_order_qty=100.0, lead_time=3)
        db.add_all([rm1, rm2])
        db.flush()
        print("- Hammadde tanımları oluşturuldu.")

        # 4. ADIM: Depo ve Lot Bazlı Hammadde Stoklarını Ekle
        # Merkez Depoda 5000 kg Polipropilen Granül var.
        stock1 = WarehouseStock(raw_material_id=rm1.id, warehouse_name="Merkez Depo", lot_number="LOT-PP2026-01", physical_stock=5000.0, reserved_stock=0.0, usable_stock=5000.0)
        # Boya Deposunda 150 kg Mavi Boya var (Minimum stok olan 200'ün altında - Satın alma uyarısı için)
        stock2 = WarehouseStock(raw_material_id=rm2.id, warehouse_name="Boya Deposu", lot_number="LOT-COL2026-02", physical_stock=150.0, reserved_stock=0.0, usable_stock=150.0)
        db.add_all([stock1, stock2])
        db.flush()
        print("- Depo hammadde stokları girildi.")

        # 5. ADIM: Ürün Reçetelerini (BOM) Eşleştir
        # Spunbond Kumaş (p1) reçetesi: 1 metre üretim için 0.95 kg Polipropilen, 0.05 kg Boya gerekir.
        bom_p1_1 = Recipe(product_id=p1.id, raw_material_id=rm1.id, quantity_needed=0.95, scrap_rate=3.0, version="v1.0")
        bom_p1_2 = Recipe(product_id=p1.id, raw_material_id=rm2.id, quantity_needed=0.05, scrap_rate=3.0, version="v1.0")
        
        # Meltblown Filtre (p2) reçetesi: 1 metre üretim için 1.00 kg Polipropilen gerekir. Boya istemez.
        bom_p2 = Recipe(product_id=p2.id, raw_material_id=rm1.id, quantity_needed=1.00, scrap_rate=5.0, version="v1.0")
        
        db.add_all([bom_p1_1, bom_p1_2, bom_p2])
        db.flush()
        print("- Ürün reçeteleri (BOM) tanımlandı.")

        # 6. ADIM: Örnek Siparişleri Ekle (Ürünlere ve Hatlara Bağlı)
        sample_orders = [
            Order(
                order_no="SIP-1001", item_no="10", customer_name="Atlas Tekstil",
                product_id=p1.id, quantity=1500.0, width=160.0, grammage=50.0,
                market_type="Yurtiçi", sales_rep="Ahmet Mert", unit_price=1.20, currency="USD",
                production_line="SPL-01", priority="Yüksek", status="Yeni",
                estimated_delivery_date=date(2026, 7, 30), actual_delivery_date=None
            ),
            Order(
                order_no="SIP-1002", item_no="10", customer_name="Ege Ambalaj",
                product_id=p2.id, quantity=2300.0, width=160.0, grammage=25.0,
                market_type="Yurtdışı", sales_rep="Elif Şen", unit_price=2.10, currency="EUR",
                production_line="SPL-03", priority="Orta", status="Planlandı",
                estimated_delivery_date=date(2026, 7, 28), actual_delivery_date=None
            ),
            Order(
                order_no="SIP-1003", item_no="10", customer_name="Zirve Medikal",
                product_id=p3.id, quantity=4000.0, width=160.0, grammage=40.0,
                market_type="Yurtiçi", sales_rep="Ahmet Mert", unit_price=1.50, currency="USD",
                production_line="SPL-02", priority="Düşük", status="Üretimde",
                estimated_delivery_date=date(2026, 7, 25), actual_delivery_date=None
            ),
            Order(
                order_no="SIP-1004", item_no="10", customer_name="Beta Lojistik",
                product_id=p1.id, quantity=800.0, width=160.0, grammage=50.0,
                market_type="Yurtdışı", sales_rep="Can Yılmaz", unit_price=1.15, currency="USD",
                production_line="SPL-01", priority="Orta", status="Tamamlandı",
                estimated_delivery_date=date(2026, 7, 20), actual_delivery_date=date(2026, 7, 20),
                completion_date=date(2026, 7, 20)
            )
        ]
        db.add_all(sample_orders)
        db.commit()
        print("✔ Tüm ilişkisel veriler başarıyla kaydedildi.")

    except Exception as e:
        db.rollback()
        print(f"Seed işlemi sırasında bir hata oluştu: {e}")
    finally:
        db.close()