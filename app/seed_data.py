# app/seed_data.py
# Python'ın standart datetime kütüphanesinden tarih sınıfını içe aktarıyoruz.
from datetime import date

# SQLAlchemy oturumunu ve veritabanı tablomuzu temsil eden Order modelini içe aktarıyoruz.
from app.database import SessionLocal
from app.models import Order

def seed_orders():
    """
    Veritabanında eğer hiç sipariş yoksa, test amaçlı 10 adet yapay sipariş
    ekleyen yardımcı fonksiyon. Teslimat tarihlerini de kapsar.
    """
    # Veritabanında işlem yapabilmek için SessionLocal kullanarak bir oturum başlatıyoruz.
    db = SessionLocal()
    try:
        # Tabloda önceden eklenmiş herhangi bir sipariş var mı diye kontrol ediyoruz.
        # .first() metodu tablodaki ilk kaydı getirir. Kayıt varsa None dönmez.
        if db.query(Order).first() is not None:
            print("Veritabanında sipariş verisi zaten mevcut, seed işlemi atlandı.")
            return

        # 10 adet yapay sipariş nesnesinden oluşan bir liste tanımlıyoruz.
        # Yeni, Planlandı ve Üretimde durumundaki siparişlerin tahmini teslim tarihleri dolu, gerçek teslim tarihleri boştur.
        # Teslim Edildi durumundaki siparişlerin hem tahmini hem de gerçek teslim tarihleri doludur.
        sample_orders = [
            Order(
                order_no="SIP-1001",
                customer_name="Atlas Tekstil",
                product_name="Spunbond Kumaş",
                quantity=1500.0,
                production_line="SPL1",
                status="Yeni",
                estimated_delivery_date=date(2026, 7, 30),
                actual_delivery_date=None,
                item_no="10"
            ),
            Order(
                order_no="SIP-1002",
                customer_name="Ege Ambalaj",
                product_name="Meltblown Filtre",
                quantity=2300.5,
                production_line="SPL3",
                status="Planlandı",
                estimated_delivery_date=date(2026, 7, 28),
                actual_delivery_date=None,
                item_no="10"
            ),
            Order(
                order_no="SIP-1003",
                customer_name="Zirve Medikal",
                product_name="SMS Maske Kumaşı",
                quantity=4000.0,
                production_line="SPL2",
                status="Üretimde",
                estimated_delivery_date=date(2026, 7, 25),
                actual_delivery_date=None,
                item_no="10"
            ),
            Order(
                order_no="SIP-1004",
                customer_name="Beta Lojistik",
                product_name="Lamine Önlük Kumaşı",
                quantity=800.0,
                production_line="SPL5",
                status="Teslim Edildi",
                estimated_delivery_date=date(2026, 7, 20),
                actual_delivery_date=date(2026, 7, 20),  # Gününde teslimat örneği
            item_no="10"
            ),
            Order(
                order_no="SIP-1005",
                customer_name="Ova Tarım",
                product_name="Agrotekstil Örtü",
                quantity=5000.0,
                production_line="SPL4",
                status="Yeni",
                estimated_delivery_date=date(2026, 8, 5),
                actual_delivery_date=None,
                item_no="10"
    
            ),
            Order(
                order_no="SIP-1006",
                customer_name="Deniz Giyim",
                product_name="Tela Astar",
                quantity=1200.0,
                production_line="SPL1",
                status="Planlandı",
                estimated_delivery_date=date(2026, 8, 2),
                actual_delivery_date=None,
                item_no="10"
            ),
            Order(
                order_no="SIP-1007",
                customer_name="Asya Hijyen",
                product_name="Nonwoven Şerit",
                quantity=3500.75,
                production_line="SPL3",
                status="Üretimde",
                estimated_delivery_date=date(2026, 7, 24),
                actual_delivery_date=None,
                item_no="10"
            
            ),
            Order(
                order_no="SIP-1008",
                customer_name="Lider Mobilya",
                product_name="Spunbond Astar",
                quantity=950.0,
                production_line="SPL2",
                status="Teslim Edildi",
                estimated_delivery_date=date(2026, 7, 18),
                actual_delivery_date=date(2026, 7, 21),  # Gecikmeli teslimat örneği (3 gün gecikmiş)
                item_no="10"
            ),
            Order(
                order_no="SIP-1009",
                customer_name="Yıldız Filtre",
                product_name="Meltblown Maske Katmanı",
                quantity=2800.0,
                production_line="SPL4",
                status="Yeni",
                estimated_delivery_date=date(2026, 8, 1),
                actual_delivery_date=None, 
                item_no="10"
            ),
            Order(
                order_no="SIP-1010",
                customer_name="Kuzey Paketleme",
                product_name="Lamine Ambalaj",
                quantity=1750.5,
                production_line="SPL5",
                status="Planlandı",
                estimated_delivery_date=date(2026, 7, 29),
                actual_delivery_date=None,
                item_no="10"
            )
        ]

        # Hazırladığımız tüm sipariş nesnelerini topluca veritabanı oturumuna ekliyoruz.
        db.add_all(sample_orders)
        
        # Yapılan tüm ekleme işlemlerini commit ederek veritabanına kalıcı olarak kaydediyoruz.
        db.commit()
        print("10 adet örnek sipariş (teslim tarihleriyle birlikte) başarıyla veritabanına eklendi.")
    except Exception as e:
        # Herhangi bir hata oluşursa veritabanı bütünlüğünü korumak adına yapılan işlemleri geri alıyoruz.
        db.rollback()
        print(f"Seed işlemi sırasında bir hata oluştu: {e}")
    finally:
        # Açılan oturumu kapatıp veritabanı bağlantı kaynaklarını serbest bırakıyoruz.
        db.close()
