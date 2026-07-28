# SQLAlchemy'nin veritabanı bağlantısı oluşturma aracını içe aktarıyoruz.
from sqlalchemy import create_engine

# Veritabanı modelleri ve oturumları için gerekli sınıfları içe aktarıyoruz.
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# Kullanacağımız veritabanının adresi.
# sqlite:/// ifadesi SQLite kullanacağımızı belirtir.
# ./uretim_asistanim.db ise veritabanı dosyasının
# projenin ana klasöründe oluşturulacağını belirtir.
DATABASE_URL = "sqlite:///./uretim_asistanim.db"


# Python uygulaması ile SQLite veritabanı arasındaki bağlantıyı oluşturuyoruz.
engine = create_engine(
    DATABASE_URL,

    # SQLite aynı bağlantının farklı işlemlerde kullanılmasını
    # varsayılan olarak sınırlar. FastAPI ile çalışabilmesi için
    # bu kontrolü kapatıyoruz.
    connect_args={"check_same_thread": False},
)


# Oluşturacağımız bütün veritabanı tabloları
# bu temel sınıftan miras alacak.
class Base(DeclarativeBase):
    pass


# Veritabanında veri eklemek, okumak, güncellemek
# ve silmek için kullanılacak oturum yapısını oluşturuyoruz.
SessionLocal = sessionmaker(
    # Oturumun hangi veritabanı bağlantısını kullanacağını belirtiyoruz.
    bind=engine,

    # Değişiklikleri otomatik olarak kaydetme.
    # Biz db.commit() komutunu kullanarak kaydedeceğiz.
    autocommit=False,

    # Her işlemden önce verileri otomatik gönderme.
    # Kontrolün bizde olması için kapalı tutuyoruz.
    autoflush=False,
)