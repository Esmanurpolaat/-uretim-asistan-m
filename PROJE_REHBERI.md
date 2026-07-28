# Üretim Asistanım - Proje El Kitabı ve Handoff Dokümanı

Bu doküman, "Üretim Asistanım" projesinin mimarisini, dosya yapısını, mevcut durumunu ve sonraki adımlarını açıklamaktadır. Bu dokümanı başka bir yapay zekaya (veya geliştiriciye) vererek projeye kaldığınız yerden kolayca devam edebilirsiniz.

---

## 1. Proje Özeti ve Teknoloji Yığını (Stack)

Bu proje, küçük ve orta ölçekli üretim tesislerinde siparişlerin takibini yapmak, teslim tarihlerini yönetmek ve Excel dosyalarından veri yükleyip ön izlemek için geliştirilen hafif bir web uygulamasıdır.

- **Backend (Sunucu):** Python - FastAPI
- **Veritabanı ve ORM:** SQLite - SQLAlchemy 2.0 (Mapped/mapped_column yapısı)
- **Arayüz Şablonları:** Jinja2 (HTML + CSS)
- **Excel İşleme Kütüphaneleri:** Pandas + Openpyxl

---

## 2. Proje Klasör Yapısı

```
üretim-asistanım/
├── .venv/                      # Python Sanal Ortamı
├── app/                        # Uygulama Kodları
│   ├── templates/              # HTML Şablonları (Jinja2)
│   │   ├── index.html          # Ana Sayfa Arayüzü
│   │   ├── orders.html         # Sipariş Takip Tablosu
│   │   ├── upload.html         # Excel Seçme ve Yükleme Formu
│   │   └── preview.html        # Excel Verileri Ön İzleme Sayfası
│   ├── __init__.py
│   ├── database.py             # SQLite ve SQLAlchemy Bağlantı Ayarları
│   ├── main.py                 # FastAPI Rotaları (Endpoints) ve Sunucu Başlangıcı
│   ├── models.py               # Veritabanı Tablo Yapıları (Şemalar)
│   └── seed_data.py            # Otomatik Örnek Veri Doldurma Betiği
├── scratch/                    # Geçici ve Yardımcı Kodlar
│   └── create_lines.py         # SQLite'ta üretim hatları tablosunu oluşturan test kodu
├── gunluk.txt                  # Geliştirme Günlüğü (Öğretici Açıklamalar)
├── requirements.txt            # Proje Bağımlılıkları (fastapi, pandas vb.)
└── uretim_asistanim.db         # SQLite Veritabanı Dosyası (Tüm veriler buradadır)
```

---

## 3. Kritik Dosyaların İçerikleri ve Açıklamaları

### A. Veritabanı Bağlantısı: `app/database.py`
SQLAlchemy kullanarak SQLite ile bağlantı kurar. Veritabanı işlemleri için `SessionLocal` adında oturum yapıcı sunar.
- **Kritik Sınıf:** `Base(DeclarativeBase)` (Bütün tablolar bu sınıftan miras alır).

### B. Modeller (Şemalar): `app/models.py`
Veritabanı tablolarının Python'daki karşılıklarıdır.
- **`Order` Sınıfı:** `orders` tablosunu temsil eder. Kolonları:
  - `id`: Benzersiz anahtar (Primary Key, Otomatik Artan)
  - `order_no`: Sipariş numarası (Benzersiz, String)
  - `customer_name`: Müşteri adı (String)
  - `product_name`: Ürün adı (String, Nullable)
  - `quantity`: Sipariş miktarı (Float, Nullable)
  - `production_line`: Üretim hattı (String, Nullable)
  - `status`: Durum (Yeni, Planlandı, Üretimde, Teslim Edildi)
  - `estimated_delivery_date`: Tahmini teslim tarihi (Date, Nullable)
  - `actual_delivery_date`: Gerçek teslim tarihi (Date, Nullable)

### C. Rotalar (Endpoints): `app/main.py`
Uygulamanın URL adreslerini ve iş mantığını yönetir. Rotalar:
- `GET /`: `index.html` sayfasını döner (Ana Sayfa).
- `GET /orders`: Veritabanındaki tüm siparişleri `SessionLocal` kullanarak sorgular (`db.query(models.Order).all()`) ve `orders.html` şablonuna göndererek listeler.
- `GET /imports/upload`: Excel dosyası yükleme formunun olduğu `upload.html` sayfasını açar.
- `POST /imports/preview`: Tarayıcıdan gönderilen Excel dosyasını alır:
  - Uzantısını kontrol eder (`.xlsx`, `.xls` olmalı).
  - Dosyayı diske kaydetmeden, doğrudan RAM (bellek) üzerinde Pandas `pd.read_excel(file.file)` ile okur.
  - İlk 20 satırı ve sütun başlıklarını ayıklayarak `preview.html` ön izleme ekranına gönderir.

### D. Otomatik Örnek Veriler: `app/seed_data.py`
Veritabanı boşken sunucu ilk kez çalıştırıldığında, veritabanına otomatik olarak 10 adet yapay sipariş ekler. Mükerrer (tekrar eden) kayıtları önlemek için tabloda veri varsa işlemi atlar.

---

## 4. Projenin Şu Anki Durumu (Nerede Kaldık?)

1. **Sipariş Listesi:** `/orders` sayfasında veritabanındaki siparişler tarihleri formatlanmış şekilde listeleniyor.
2. **Excel Ön İzleme:** Kullanıcı Excel dosyası yükleyebiliyor ve ilk 20 satırını başarılı şekilde ön izleyebiliyor (Veritabanına henüz kaydetmiyoruz).
3. **Üretim Hatları Çalışması (Başlanan Kısım):** 
   - Veritabanında (SQLite) `production_lines` adında yeni bir tablo elle oluşturuldu (veya `scratch/create_lines.py` ile hazırlandı) ve içine deneme verileri eklendi.
   - Bu tablonun kolonları: `id`, `line_name`, `capacity`, `operator_name`.
   - **Kaldığımız Nokta:** Bu tablonun modelini (`ProductionLine` sınıfı) `app/models.py` içerisine ekleme, `/lines` rotasını `app/main.py` içerisine yazma ve bunu `lines.html` adında yeni bir şablonla web sitesinde listeleme aşamasındayız.

---

## Geliştiriciye Notlar (Diğer Yapay Zekaya Verilecek Komut)
> *"Merhaba, bu projeyi devralıyorsun. FastAPI + SQLite projesinde teslim tarihli sipariş listeleme ve bellek üzerinden Excel ön izleme yapısı kuruldu. Son olarak veritabanında oluşturulan `production_lines` tablosunu uygulamaya bağlama aşamasındayız. Lütfen `models.py` dosyasına bu tablonun modelini ekleyerek, `/lines` rotasını oluşturarak ve `lines.html` şablonunu tasarlayarak üretim hatlarını listeleyen özelliği tamamla. Kodları doğrudan yazmak yerine bana adım adım ne yazmam gerektiğini söyle ve benim yazmamı sağla."*
