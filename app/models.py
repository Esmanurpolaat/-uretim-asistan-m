# Python'ın standart datetime kütüphanesinden tarih sınıfını içe aktarıyoruz.
from datetime import date

# Veritabanındaki sütunların veri tiplerini içe aktarıyoruz.
# SQLAlchemy içerisinden Date, ForeignKey, Integer, Boolean sınıfını da ekliyoruz.
from sqlalchemy import Float, String, Date, ForeignKey, Integer, Boolean

# Modern SQLAlchemy tablo tanımlama araçlarını içe aktarıyoruz.
from sqlalchemy.orm import Mapped, mapped_column, relationship

# database.py dosyasındaki temel tablo sınıfını içe aktarıyoruz.
from app.database import Base


# Sipariş bilgilerini saklayacağımız tabloyu tanımlıyoruz.
# Bu Python sınıfı SQLite içerisinde bir tabloya dönüşecek.
class Order(Base):

    # SQLite içerisinde oluşturulacak tablonun adı.
    __tablename__ = "orders"

    # Her sipariş kaydının benzersiz kimlik numarası.
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    # Sipariş numarasını tutar.
    # Örnek: SIP-1001
    order_no: Mapped[str] = mapped_column(
        String(50),
        unique=False,
        nullable=False,
        index=True,
    )
    # Siparişin kalem numarasını tutar. Boş bırakılamaz.
    item_no: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
   
    # Müşteri adını tutar.
    customer_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    # Ürün Kataloğuyla İlişki (Yabancı Anahtar)
    product_id: Mapped[int | None] = mapped_column(
        ForeignKey("products.id"),
        nullable=True,
    )

    # Sipariş miktarını tutar.
    quantity: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Siparişe Özel Fiziksel Özellikler (En ve Gramaj)
    width: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    grammage: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # Satış ve Finansal Bilgiler
    market_type: Mapped[str] = mapped_column(
        String(50),
        default="Yurtiçi",
        nullable=False,
    )
    sales_rep: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    unit_price: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(20),
        default="TRY",
        nullable=False,
    )

    # Siparişin üretileceği hattı tutar.
    production_line: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Siparişin önceliği (Düşük, Orta, Yüksek)
    priority: Mapped[str] = mapped_column(
        String(50),
        default="Orta",
        nullable=False,
    )

    # Siparişin mevcut durumunu tutar.
    status: Mapped[str] = mapped_column(
        String(50),
        default="Yeni",
        nullable=False,
    )

    # Teslimat tarihleri
    estimated_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    actual_delivery_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )
    completion_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    # İlişkiler
    product = relationship("Product", back_populates="orders")


# Üretim hatlarımızı temsil eden veritabanı tablosunun Python modeli.
class ProductionLine(Base):
    __tablename__ = "production_lines"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    line_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    capacity: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    operator_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )


# 🧱 ÜRÜN KATALOĞU TABLOSU
class Product(Base):
    __tablename__ = "products"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True) # Örn: URN-SPN01
    product_name: Mapped[str] = mapped_column(String(150), nullable=False)
    product_group: Mapped[str | None] = mapped_column(String(100), nullable=True) # Örn: Spunbond, Meltblown
    standard_width: Mapped[float | None] = mapped_column(Float, nullable=True) # Standart en değeri (cm)
    grammage: Mapped[float | None] = mapped_column(Float, nullable=True) # Standart gramajı (g/m2)
    unit: Mapped[str] = mapped_column(String(20), default="Metre", nullable=False) # Ölçü birimi
    eligible_lines: Mapped[str | None] = mapped_column(String(150), nullable=True) # Üretilebildiği makineler (Örn: "SPL-01,SPL-02")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # İlişkiler
    orders = relationship("Order", back_populates="product")
    recipes = relationship("Recipe", back_populates="product")


# 🧱 HAMMADDE TANIMLARI TABLOSU
class RawMaterial(Base):
    __tablename__ = "raw_materials"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    material_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True) # Örn: RAW-PP01
    material_name: Mapped[str] = mapped_column(String(150), nullable=False)
    material_type: Mapped[str | None] = mapped_column(String(100), nullable=True) # Örn: Polimer, Boya
    unit: Mapped[str] = mapped_column(String(20), default="Kg", nullable=False) # Ölçü birimi
    min_stock: Mapped[float] = mapped_column(Float, default=0.0, nullable=False) # Minimum stok
    safety_stock: Mapped[float] = mapped_column(Float, default=0.0, nullable=False) # Emniyet stoğu
    min_order_qty: Mapped[float] = mapped_column(Float, default=0.0, nullable=False) # Minimum sipariş miktarı
    lead_time: Mapped[int] = mapped_column(Integer, default=0, nullable=False) # Tedarik süresi (gün)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # İlişkiler
    recipes = relationship("Recipe", back_populates="raw_material")
    stocks = relationship("WarehouseStock", back_populates="raw_material")


# 🧱 ÜRÜN REÇETELERİ (BOM - BILL OF MATERIALS) TABLOSU
class Recipe(Base):
    __tablename__ = "recipes"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    raw_material_id: Mapped[int] = mapped_column(ForeignKey("raw_materials.id"), nullable=False)
    quantity_needed: Mapped[float] = mapped_column(Float, nullable=False) # 1 birim ürün için gereken hammadde miktarı (örn: 1 mt için 0.15 kg polipropilen)
    scrap_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False) # Fire Oranı (yüzde, örn: 5 = %5)
    version: Mapped[str] = mapped_column(String(20), default="v1.0", nullable=False) # Reçete versiyonu
    
    # İlişkiler
    product = relationship("Product", back_populates="recipes")
    raw_material = relationship("RawMaterial", back_populates="recipes")


# 🧱 DEPO VE LOT BAZLI STOK DETAYI TABLOSU
class WarehouseStock(Base):
    __tablename__ = "warehouse_stocks"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    raw_material_id: Mapped[int] = mapped_column(ForeignKey("raw_materials.id"), nullable=False)
    warehouse_name: Mapped[str] = mapped_column(String(100), nullable=False) # Depo Adı (Örn: Depo-A, Silo-1)
    lot_number: Mapped[str | None] = mapped_column(String(50), nullable=True) # Hammadde Lot / Parti No
    physical_stock: Mapped[float] = mapped_column(Float, default=0.0, nullable=False) # Fiziksel stok
    reserved_stock: Mapped[float] = mapped_column(Float, default=0.0, nullable=False) # Rezerve stok
    usable_stock: Mapped[float] = mapped_column(Float, default=0.0, nullable=False) # Kullanılabilir net stok
    
    # İlişki
    raw_material = relationship("RawMaterial", back_populates="stocks")