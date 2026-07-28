# Python'ın standart datetime kütüphanesinden tarih sınıfını içe aktarıyoruz.
from datetime import date

# Veritabanındaki sütunların veri tiplerini içe aktarıyoruz.
# SQLAlchemy içerisinden Date sınıfını da ekliyoruz.
from sqlalchemy import Float, String, Date

# Modern SQLAlchemy tablo tanımlama araçlarını içe aktarıyoruz.
from sqlalchemy.orm import Mapped, mapped_column

# database.py dosyasındaki temel tablo sınıfını içe aktarıyoruz.
from app.database import Base


# Sipariş bilgilerini saklayacağımız tabloyu tanımlıyoruz.
# Bu Python sınıfı SQLite içerisinde bir tabloya dönüşecek.
class Order(Base):

    # SQLite içerisinde oluşturulacak tablonun adı.
    __tablename__ = "orders"

    # Her sipariş kaydının benzersiz kimlik numarası.
    # primary_key=True olduğu için anahtar alanıdır.
    # Değer otomatik olarak 1, 2, 3 şeklinde artar.
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    # Sipariş numarasını tutar.
    # Örnek: SIP-1001
    order_no: Mapped[str] = mapped_column(
        # En fazla 50 karakter olabilir.
        String(50),

        # Aynı sipariş numarası iki kez kaydedilebilir bu durumlarda ayırtabılmek için kalem no gircez 
        unique=False,

        # Bu alan boş bırakılamaz.
        nullable=False,

        # Sipariş numarasıyla yapılan aramaları hızlandırır.
        index=True,
    )
    # Siparişin kalem numarasını tutar. Boş bırakılamaz.
    item_no: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
   
    # Müşteri adını tutar.
    # Örnek: Atlas Tekstil
    customer_name: Mapped[str] = mapped_column(
        String(150),

        # Müşteri adı zorunludur.
        nullable=False,
    )

    # Ürün veya kumaş adını tutar.
    # Örnek: Spunbond
    product_name: Mapped[str | None] = mapped_column(
        String(150),

        # Bu alan şimdilik boş bırakılabilir.
        nullable=True,
    )

    # Sipariş miktarını tutar.
    # Örnek: 2500.50
    quantity: Mapped[float | None] = mapped_column(
        Float,

        # Bu alan şimdilik boş bırakılabilir.
        nullable=True,
    )

    # Siparişin üretileceği hattı tutar.
    # Örnek: SPL5
    production_line: Mapped[str | None] = mapped_column(
        String(50),

        # Bu alan şimdilik boş bırakılabilir.
        nullable=True,
    )

    # Siparişin mevcut durumunu tutar.
    # Örnek: Yeni, Planlandı, Üretimde, Tamamlandı (Veya Teslim Edildi)
    status: Mapped[str] = mapped_column(
        String(50),

        # Bir durum belirtilmezse otomatik olarak "Yeni" yazılır.
        default="Yeni",

        # Durum alanı boş bırakılamaz.
        nullable=False,
    )

    # Siparişin tahmini/planlanan teslim tarihini tutacak sütun.
    estimated_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        # Bu alan boş bırakılabilir (nullable=True).
        nullable=True,
    )

     # Siparişin gerçekten teslim edildiği tarihi tutacak sütun.
    # Siparişin gerçekten teslim edildiği tarihi tutacak sütun.
    actual_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        # Henüz teslim edilmeyen siparişler için boş bırakılabilir.
        nullable=True,
    )

    # Siparişin ilk kez tamamlandığı tarihi tutar.
    completion_date: Mapped[date | None] = mapped_column(
        Date,
        # Henüz tamamlanmayan siparişler için boş kalabilir.
        nullable=True,
    )

    # Üretim hatlarımızı temsil eden veritabanı tablosunun Python modeli.
class ProductionLine(Base):
    # SQLite'ta oluşturduğumuz tablonun adı ile birebir aynı olmalı.
    __tablename__ = "production_lines"

    # Her makine hattının benzersiz kimlik numarası (Primary Key).
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    # Hattın adı (Örn: SPL-01, SPL-02). Boş bırakılamaz (nullable=False).
    line_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Hattın günlük üretim kapasitesi. Boş bırakılabilir (nullable=True).
    capacity: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    # Hattın başındaki sorumlu çalışanın adı. Boş bırakılabilir.
    operator_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )