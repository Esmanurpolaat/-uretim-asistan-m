# Üretim Asistanım - Dijital Üretim ve Planlama Yönetim Sistemi (MES/ERP)

Bu proje, küçük ve orta ölçekli üretim tesislerinde sipariş süreçlerinin yönetilmesi, üretim planlaması, hammadde ihtiyaç analizi (MRP), makine kapasite takibi ve üretim onaylarının (MES) dijitalleştirilmesi amacıyla geliştirilmiş **modern, yüksek performanslı bir web uygulamasıdır.**

---

##  Temel Özellikler (Modüller)

### 1.  Operasyonel Kontrol Merkezi (Dashboard)
*   **Canlı Durum Şeridi:** Termin durumu, günlük tamamlanacak siparişler ve aktif hat sayılarını gösteren dinamik durum paneli.
*   **4 Operasyonel KPI Kartı:** Aktif Sipariş Hacmi, Geciken Sipariş Hacmi, 7 Günlük Termin Yakınlaşımı ve Bugünkü Teslimat Yükümlülüğü kg ve adet bazında anlık izlenebilir.
*   **Aylık Performans ve Verimlilik Özeti:** Tamamlanan iş hacmi, zamanında teslimat oranı (%) ve ortalama gecikme sürelerini hesaplar.
*   **Dinamik JS Filtreleme:** Sayfa yenilenmeden, KPI kartlarına tıklayarak tüm sipariş listesini anlık süzme yeteneği.
*   **Öncelikli Operasyonel Faaliyetler:** Stok seviyesi kritik olan hammaddeler ve teslimatı gecikmiş siparişler için otomatik uyarılar üretir.

### 2.  Sipariş Yönetimi (CRUD)
*   Siparişlerin listelenmesi, detaylı incelenmesi, güncellenmesi ve yeni sipariş kaydı oluşturulması.
*   **Hibrit Arama Motoru:** Müşteri adı, sipariş no veya durum kriterlerine göre sayfa yenilenmeden anlık arama desteği.

### 3.  Kapasite ve Hat İzleme (CRUD)
*   Üretim hatlarının (SPL-01, SPL-02, SPL-03 vb.) günlük kapasiteleri, aktif yük birikimleri ve anlık doluluk oranları (%) görsel barlarla takip edilir.
*   Hatlarda atanmış olan aktif işlerin detaylı dökümü listelenir.
*   **Dinamik Yönetim:** Arayüz üzerinden yeni hat tanımlama, kapasite/operatör güncelleme ve hatta iş yükü yoksa güvenli silme imkanı.

### 4.  Üretim Planlama ve Çizelgeleme
*   Planlanmamış siparişlerin kapasitesi uygun olan üretim hatlarına atanması ve planlanan bitiş sürelerinin otomatik hesaplanması.
*   Çizelgeleme işleminden önce reçete uygunluğu kontrolü.

### 5.  Üretim Onay Sistemi (MES)
*   Saha üretim onaylarının (üretilen miktar ve fire miktarları) girilerek siparişlerin tamamlanması.
*   **FIFO (İlk Giren İlk Çıkar) Tüketim Algoritması:** Üretim onaylandığında, ilgili ürünün reçetesine göre tüketilecek hammaddeler, depodaki lot numaralarına göre en eski tarihliden başlanarak otomatik olarak düşülür.

### 6.  Malzeme İhtiyaç Planlama (MRP)
*   Planlanmış siparişlerin toplam hammadde ihtiyaçları ile depo kullanılabilir stok miktarları karşılaştırılır. Eksik veya emniyet stoğu altına düşen hammaddeler için otomatik satın alma uyarısı üretilir.

### 7.  Performans Raporlama
*   Aylık hedeflenen vs gerçekleşen üretim miktarlarını karşılaştıran Someka tarzı KPI tablosu.
*   Bar ve çizgi grafiklerin bir arada sunulduğu hibrit trend analiz grafiklerin (Chart.js).

### 8.  Excel Veri Entegrasyonu
*   Excel dosyalarındaki (`.xlsx`) toplu sipariş verilerinin okunması, ön izlenmesi ve veritabanına otomatik toplu yazılması/güncellenmesi (Upsert).

---

##  Teknoloji Yığını (Stack)

*   **Backend:** FastAPI (Python 3.10+)
*   **Database & ORM:** SQLite & SQLAlchemy 2.0 (Modern Declarative Mapped Yapısı)
*   **Excel Engine:** Pandas & Openpyxl
*   **Frontend:** Vanilla HTML5, Vanilla CSS3 (Slate & Anthracite Premium Tema, 6px border-radius standardı), Vanilla JavaScript
*   **Grafikler:** Chart.js

---

##  Klasör  Yapısı

```
üretim-asistanım/
├── app/                        # Uygulama Kod Dizini
│   ├── templates/              # HTML Arayüz Şablonları (Jinja2)
│   │   ├── index.html          # Ana Dashboard
│   │   ├── orders.html         # Sipariş Yönetimi
│   │   ├── planning.html       # Üretim Planlama
│   │   ├── production.html     # MES Üretim Onay
│   │   ├── mrp.html            # Malzeme Planlama (MRP)
│   │   ├── reports.html        # Performans Raporları
│   │   ├── line_form.html      # Hat Giriş/Düzenleme Formu
│   │   └── ... (diğer formlar)
│   ├── database.py             # Veritabanı ve Session Yapılandırması
│   ├── main.py                 # FastAPI Rotaları (Endpoints) ve İş Mantığı
│   ├── models.py               # SQLAlchemy Veritabanı Modelleri
│   └── seed_data.py            # Başlangıç Test Verileri (Seed)
├── scratch/                    # Veri ve İndeks Güncelleme Scriptleri
├── uretim_asistanim.db         # SQLite Veritabanı Dosyası
├── requirements.txt            # Python Paket Bağımlılıkları
└── README.md                   # Proje Dokümantasyonu
```

---

##  Veritabanı Performans Optimizasyonları

Uygulamanın büyük veri setleri altında yüksek hızda çalışması amacıyla SQLite veritabanı üzerinde aşağıdaki indeksler (`INDEX`) tanımlanmıştır:
*   `idx_orders_status` (Sipariş durumu sorguları için)
*   `idx_orders_production_line` (Hattaki iş yükü hesaplamaları için)
*   `idx_orders_estimated_delivery_date` (Termin ve gecikme analizleri için)
*   `idx_warehouse_stocks_raw_material_id` (FIFO stok arama hızlandırması için)

---

##  Kurulum ve Çalıştırma Adımları

### 1. Sanal Ortam Oluşturma ve Bağımlılıkların Yüklenmesi
Proje dizininde bir terminal açın ve aşağıdaki komutları sırasıyla çalıştırın:

```powershell
# Sanal ortam oluşturun
python -m venv .venv

# Sanal ortamı aktif edin
.venv\Scripts\Activate.ps1

# Gerekli kütüphaneleri yükleyin
pip install -r requirements.txt
```

### 2. Uygulamayı Başlatma
Sunucuyu başlatmak için uvicorn komutunu çalıştırın:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Uygulama başarıyla başlatıldıktan sonra tarayıcınızdan **`http://127.0.0.1:8000/`** adresine giderek kontrol panelini kullanmaya başlayabilirsiniz.
