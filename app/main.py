# FastAPI uygulamasını oluşturmak için FastAPI ve Request sınıflarını içe aktarıyoruz.
# Dosya yükleme işlemleri için UploadFile ve File sınıflarını da dahil ediyoruz.
from fastapi import FastAPI, Request, UploadFile, File

# HTML ve Yönlendirme yanıtları döndürmek için kullanıyoruz.
from fastapi.responses import HTMLResponse, RedirectResponse
import os
from datetime import date

# HTML şablonlarını kullanabilmek için Jinja2Templates'i içe aktarıyoruz.
from fastapi.templating import Jinja2Templates

# Excel dosyalarını okumak ve bellek üzerinde işlemek için pandas kütüphanesini içe aktarıyoruz.
import pandas as pd


# models.py dosyasını içe aktarıyoruz.
# Bu işlem yapılınca Order modeli uygulama tarafından tanınır.
from app import models

# Veritabanı tablolarını oluşturmak ve veritabanı işlemlerini yönetmek için
# Base, engine ve SessionLocal nesnelerini içe aktarıyoruz.
from app.database import Base, engine, SessionLocal
# Veritabanı tablolarını oluşturmak için
# Base ve engine nesnelerini içe aktarıyoruz.
from app.database import Base, engine, SessionLocal
# Otomatik sipariş verisi ekleme fonksiyonunu içe aktarıyoruz.
from app.seed_data import seed_orders
from sqlalchemy import func


# models.py içerisinde tanımlanan tabloları kontrol eder.
# Tablo yoksa SQLite içerisinde otomatik olarak oluşturur.
# Tablo zaten varsa yeniden oluşturmaz ve verileri silmez.
Base.metadata.create_all(bind=engine)

# Uygulama ayağa kalktığında otomatik olarak örnek sipariş verilerini ekliyoruz.
seed_orders()


# FastAPI uygulamasını oluşturuyoruz.
# title bilgisi otomatik API dokümantasyonunda gösterilir.
app = FastAPI(
    title="Üretim Asistanım",
)


# HTML dosyalarımızın bulunduğu klasörü FastAPI'ye tanıtıyoruz.
templates = Jinja2Templates(
    directory="app/templates",
)


# Kullanıcı ana adrese geldiğinde çalışacak fonksiyonu tanımlıyoruz.
# "/" projenin ana sayfasını ifade eder.
@app.get(
    "/",

    # Bu adresin HTML içerik döndüreceğini belirtiyoruz.
    response_class=HTMLResponse,
)
@app.get("/", response_class=HTMLResponse)
# Ana Sayfa / Dashboard (Yönetici Paneli) Rotası.
@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    start_date: str | None = None,  # Tarayıcıdan gelecek başlangıç tarihi (Örn: '2026-07-01')
    end_date: str | None = None,    # Tarayıcıdan gelecek bitiş tarihi
    date_type: str | None = "estimated_delivery_date" # Hangi tarihe göre filtreleneceği
):
    # Veritabanına bağlanmak için oturum açıyoruz.
    db = SessionLocal()
    
    # Tarih filtrelerini tutacak değişkenler
    parsed_start = None
    parsed_end = None
    
    # Eğer tarayıcıdan tarih gönderildiyse bunları Python tarih formatına çeviriyoruz
    try:
        if start_date:
            parsed_start = date.fromisoformat(start_date)
        if end_date:
            parsed_end = date.fromisoformat(end_date)
    except Exception as e:
        print(f"Tarih formatı dönüştürme hatası: {e}")
        # Hata durumunda filtreleri sıfırlıyoruz
        parsed_start = None
        parsed_end = None

    try:
        # 1. Dashboard Kartı: Toplam Sipariş Sayısı
        total_orders = db.query(models.Order).count()
        
        # 2. Dashboard Kartı: Devam eden siparişlerin sayısı (Yeni, Planlandı, Üretimde)
        active_orders = db.query(models.Order).filter(
            models.Order.status.in_(["Yeni", "Planlandı", "Üretimde"])
        ).count()
        
        # 3. Dashboard Kartı: Tamamlanan siparişlerin sayısı
        completed_orders = db.query(models.Order).filter(
            models.Order.status == "Tamamlandı"
        ).count()
        
        # 4. Yeni Dashboard Kartı: Bugün ilk kez tamamlanan siparişler
        # completion_date alanı bugünün tarihine eşit olanları sayıyoruz.
        completed_today = db.query(models.Order).filter(
            models.Order.completion_date == date.today()
        ).count()
                # --- RİSK VE GECİKME ANALİZİ BAŞLANGICI ---
        # Tamamlanmamış (Yeni, Planlandı, Üretimde) ve tahmini teslim tarihi olan siparişleri çekiyoruz
        active_orders_list = db.query(models.Order).filter(
            models.Order.status.in_(["Yeni", "Planlandı", "Üretimde"]),
            models.Order.estimated_delivery_date != None
        ).all()
        
        delayed_orders = []   # Gecikmiş siparişler listesi
        critical_orders = []  # Kritik (0-2 gün kalmış) siparişler listesi
        upcoming_orders = []  # Yaklaşan (3-7 gün kalmış) siparişler listesi
        ontime_orders = []    # Zamanında (7 günden fazla kalmış) siparişler listesi
        
        today = date.today()
        
        for order in active_orders_list:
            # Kalan gün sayısını hesaplıyoruz (Termin Tarihi - Bugün)
            delta = (order.estimated_delivery_date - today).days
            
            # Sipariş nesnesine geçici olarak remaining_days değerini atıyoruz
            order.remaining_days = delta
            
            if delta < 0:
                delayed_orders.append(order)
            elif 0 <= delta <= 2:
                critical_orders.append(order)
            elif 3 <= delta <= 7:
                upcoming_orders.append(order)
            else:
                ontime_orders.append(order)
        # --- RİSK VE GECİKME ANALİZİ BİTİŞİ ---
        
        # Pasta Grafiği İçin: Siparişlerin durumlarına göre dağılım sayılarını buluyoruz.
        status_counts = {
            "Yeni": 0,
            "Planlandı": 0,
            "Üretimde": 0,
            "Tamamlandı": 0
        }
        
        # Grafik sorgusunu hazırlıyoruz
        query = db.query(models.Order.status, func.count(models.Order.status))
        
        # EĞER TARİH FİLTRESİ VERİLDİYSE sorguya filtre ekliyoruz (Örn: between start and end)
        if parsed_start and parsed_end:
            # Seçilen tarih türüne göre ilgili kolonu filtreye bağlıyoruz
            if date_type == "estimated_delivery_date":
                query = query.filter(models.Order.estimated_delivery_date.between(parsed_start, parsed_end))
            elif date_type == "actual_delivery_date":
                query = query.filter(models.Order.actual_delivery_date.between(parsed_start, parsed_end))
            elif date_type == "completion_date":
                query = query.filter(models.Order.completion_date.between(parsed_start, parsed_end))
        
        # Gruplayıp sonuçları alıyoruz
        results = query.group_by(models.Order.status).all()
        
        for status, count in results:
            if status in status_counts:
                status_counts[status] = count
                
        # Tablo: Eklenen en son 5 sipariş
        last_orders = db.query(models.Order).order_by(models.Order.id.desc()).limit(5).all()
        
    finally:
        # Oturumu kapatıyoruz
        db.close()

    # Tüm verileri arayüze gönderiyoruz
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "Dashboard - Üretim Asistanım",
            "total_orders": total_orders,
            "active_orders": active_orders,
            "completed_orders": completed_orders,
            "completed_today": completed_today, # Bugün tamamlananları gönderdik
            "status_counts": status_counts,
            "last_orders": last_orders,
            # Seçilen filtreleri arayüzde tekrar gösterebilmek için geri gönderiyoruz
            "start_date": start_date,
            "end_date": end_date,
            "date_type": date_type,
                        # Risk analiz listeleri ve sayıları
            "delayed_orders": delayed_orders,
            "critical_orders": critical_orders,
            "upcoming_orders": upcoming_orders,
            "ontime_orders": ontime_orders,
            "delayed_count": len(delayed_orders),
            "critical_count": len(critical_orders),
            "upcoming_count": len(upcoming_orders),
            "ontime_count": len(ontime_orders)
        },
    )

# Tüm siparişlerin listeleneceği /orders sayfasının GET rotası.
@app.get("/orders", response_class=HTMLResponse)
def get_orders(request: Request):
    # Veritabanı işlemleri için SessionLocal kullanarak yeni bir oturum (session) oluşturuyoruz.
    db = SessionLocal()
    try:
        # Veritabanındaki tüm sipariş (Order) kayıtlarını sorgulayıp getiriyoruz.
        orders = db.query(models.Order).all()
    finally:
        # İşlem tamamlandığında veritabanı oturumunu kapatıyoruz.
        db.close()

    # orders.html şablonunu veritabanından aldığımız siparişler ile doldurup döndürüyoruz.
    return templates.TemplateResponse(
        request=request,
        name="orders.html",
        context={
            "title": "Siparişler - Üretim Asistanım",
            "orders": orders,
        },
    )


# Excel dosyasının yükleneceği arayüzü gösteren GET rotası.
@app.get(
    "/imports/upload",
    response_class=HTMLResponse,
)
def get_upload_page(request: Request):
    # Kullanıcıya upload.html dosyasını herhangi bir hata olmadan yüklüyoruz.
    return templates.TemplateResponse(
        request=request,
        name="upload.html",
        context={
            "title": "Excel Yükle - Üretim Asistanım",
            "error": None,
        },
    )


# Yüklenen Excel dosyasını geçici kaydeden ve ilk 20 satırı ön izleyen POST rotası.
@app.post(
    "/imports/preview",
    response_class=HTMLResponse,
)
def post_excel_preview(request: Request, file: UploadFile = File(...)):
    # Dosya seçilip seçilmediğini kontrol ediyoruz.
    if not file or file.filename == "":
        return templates.TemplateResponse(
            request=request,
            name="upload.html",
            context={
                "title": "Excel Yükle - Üretim Asistanım",
                "error": "Lütfen bir Excel dosyası seçin.",
            },
        )

    # Dosya uzantısını kontrol ediyoruz.
    filename = file.filename
    if not (filename.endswith(".xlsx") or filename.endswith(".xls")):
        return templates.TemplateResponse(
            request=request,
            name="upload.html",
            context={
                "title": "Excel Yükle - Üretim Asistanım",
                "error": "Yalnızca .xlsx veya .xls uzantılı Excel dosyaları desteklenmektedir.",
            },
        )

    try:
        # DOSYAYI SUNUCUYA GEÇİCİ OLARAK KAYDEDİYORUZ.
        temp_file_path = "temp_orders.xlsx"
        with open(temp_file_path, "wb") as f:
            f.write(file.file.read())

        # Excel dosyasını geçici dosyadan okuyoruz.
        df = pd.read_excel(temp_file_path)
    except Exception as e:
        return templates.TemplateResponse(
            request=request,
            name="upload.html",
            context={
                "title": "Excel Yükle - Üretim Asistanım",
                "error": f"Excel dosyası okunamadı. Hata: {str(e)}",
            },
        )

    # Pandas'taki boş/NaN (Not a Number) veya NaT (Not a Time) alanları Jinja2 şablonuna göndermeden önce None yapıyoruz.
    df = df.where(pd.notnull(df), None)

    # Excel'in sütun başlıklarını alıyoruz.
    columns = list(df.columns)

    # Excel dosyasındaki toplam satır sayısını alıyoruz.
    total_rows = len(df)

    # Excel dosyasındaki toplam sütun sayısını alıyoruz.
    total_columns = len(columns)

    # İlk 20 satırı ön izleme için alıyoruz ve bunu sözlük listesine (dict list) çeviriyoruz.
    preview_data = df.head(20).to_dict(orient="records")

    # preview.html şablonunu gerekli değişkenlerle birlikte döndürüyoruz.
    return templates.TemplateResponse(
        request=request,
        name="preview.html",
        context={
            "title": "Excel Ön İzleme - Üretim Asistanım",
            "filename": filename,
            "total_rows": total_rows,
            "total_columns": total_columns,
            "columns": columns,
            "preview_data": preview_data,
        },
    )

# Üretim hatlarının listeleneceği /lines sayfasının GET rotası.
@app.get(
    "/lines",
    response_class=HTMLResponse,
)
def get_production_lines(request: Request):
    # Veritabanı bağlantısını açıyoruz.
    db = SessionLocal()

    try:
        # production_lines tablosundaki bütün üretim hatlarını getiriyoruz.
        lines = db.query(models.ProductionLine).all()

        # Her üretim hattını tek tek inceliyoruz.
        for line in lines:

            # Bu hatta atanmış aktif siparişlerin toplam miktarını hesaplıyoruz.
            active_load = (
                db.query(func.sum(models.Order.quantity))
                .filter(
                    models.Order.production_line == line.line_name,
                    models.Order.status.in_(
                        ["Yeni", "Planlandı", "Üretimde"]
                    )
                )
                .scalar()
            )

            # Hatta aktif sipariş yoksa SUM sonucu None gelir.
            # Matematik işleminde hata yaşamamak için None değerini 0 yapıyoruz.
            active_load = active_load or 0

                        # Kapasite tanımlıysa ve 0'dan büyükse doluluk oranını hesaplıyoruz.
            if line.capacity and line.capacity > 0:
                occupancy_rate = (
                    active_load / line.capacity
                ) * 100
            else:
                # Kapasite 0 ise sıfıra bölme hatasını önlüyoruz.
                occupancy_rate = 0

            # Hesaplanan değerleri geçici olarak üretim hattı nesnesine ekliyoruz.
            # Bunlar veritabanına kaydedilmez; yalnızca HTML'e gönderilir.
            line.active_load = active_load
            line.occupancy_rate = round(occupancy_rate, 1)

    finally:
        # İşlem tamamlanınca veritabanı bağlantısını kapatıyoruz.
        db.close()

    # Hesaplanan değerlerle birlikte üretim hatlarını HTML'e gönderiyoruz.
    return templates.TemplateResponse(
        request=request,
        name="lines.html",
        context={
            "title": "Üretim Hatları - Üretim Asistanım",
            "lines": lines,
        },
    )

# Excel verilerini okuyup veritabanını güncelleyen (Upsert) POST rotası.
@app.post("/imports/save")
def post_excel_save():
    temp_file_path = "temp_orders.xlsx"
    
    # Eğer geçici dosya yoksa ana sayfaya yönlendiriyoruz.
    if not os.path.exists(temp_file_path):
        return RedirectResponse(url="/", status_code=303)
        
    db = SessionLocal()
    try:
        # Geçici Excel dosyasını Pandas ile okuyoruz.
        df = pd.read_excel(temp_file_path)
        df = df.where(pd.notnull(df), None)
        
        # Excel sütun isimlerini eşleştirmek için başlık kombinasyonlarını tanımlıyoruz
        order_no_keys = ["Sipariş No", "Sipariş Numarası", "Sipariş No.", "order_no", "Order No"]
        item_no_keys = ["Kalem No", "Kalem Numarası", "Kalem No.", "item_no", "Item No"]
        customer_name_keys = ["Müşteri", "Müşteri Adı", "customer_name", "Customer Name", "Customer"]
        product_name_keys = ["Ürün", "Ürün Adı", "product_name", "Product Name", "Product"]
        quantity_keys = ["Miktar", "quantity", "Quantity"]
        production_line_keys = ["Üretim Hattı", "production_line", "Production Line", "Hat"]
        status_keys = ["Durum", "status", "Status"]
        estimated_delivery_keys = ["Tahmini Teslim Tarihi", "Termin", "Teslim Tarihi", "estimated_delivery_date"]
        actual_delivery_keys = ["Gerçek Teslim Tarihi", "actual_delivery_date", "Actual Delivery Date"]

        # Satırdaki verileri esnek başlık eşleşmesine göre okuyan yardımcı fonksiyon.
        def get_val(row, keys, default=None):
            for k in keys:
                if k in row and row[k] is not None:
                    return row[k]
            return default

        # Tarih verisini python date nesnesine çeviren yardımcı fonksiyon (NaT Korumalı).
        def parse_date(val):
            # Eğer veri None, boş veya Pandas NaT ise doğrudan None dönüyoruz
            if val is None or pd.isna(val):
                return None
            if isinstance(val, date):
                return val
            try:
                res = pd.to_datetime(val).date()
                if pd.isna(res):
                    return None
                return res
            except:
                return None

        # Excel'deki her bir satırı döngüyle okuyoruz.
        for index, row in df.iterrows():
            order_no_raw = get_val(row, order_no_keys)
            item_no_raw = get_val(row, item_no_keys)
            
            if order_no_raw is None or item_no_raw is None:
                continue # Boş satırları atlıyoruz.
                
            order_no = str(order_no_raw).strip()
            item_no = str(item_no_raw).strip()

            # Eşleşen kayıt var mı kontrol ediyoruz.
            existing_order = db.query(models.Order).filter(
                models.Order.order_no == order_no,
                models.Order.item_no == item_no
            ).first()

            new_status = get_val(row, status_keys, "Yeni")

            if existing_order:
                # 1. Kural: Durum ilk kez "Tamamlandı" oluyorsa tamamlanma tarihini bugünün tarihi yapıyoruz.
                if new_status == "Tamamlandı":
                    if existing_order.status != "Tamamlandı" and not existing_order.completion_date:
                        existing_order.completion_date = date.today()
                
                # Mevcut kaydı güncelliyoruz.
                existing_order.status = new_status
                existing_order.customer_name = get_val(row, customer_name_keys, existing_order.customer_name)
                existing_order.product_name = get_val(row, product_name_keys, existing_order.product_name)
                existing_order.quantity = get_val(row, quantity_keys, existing_order.quantity)
                existing_order.production_line = get_val(row, production_line_keys, existing_order.production_line)
                existing_order.estimated_delivery_date = parse_date(get_val(row, estimated_delivery_keys, existing_order.estimated_delivery_date))
                existing_order.actual_delivery_date = parse_date(get_val(row, actual_delivery_keys, existing_order.actual_delivery_date))
                
            else:
                # EĞER YOKSA: Yeni kayıt oluşturuyoruz.
                completion_date_val = None
                if new_status == "Tamamlandı":
                    completion_date_val = date.today()

                new_order = models.Order(
                    order_no=order_no,
                    item_no=item_no,
                    customer_name=get_val(row, customer_name_keys),
                    product_name=get_val(row, product_name_keys),
                    quantity=get_val(row, quantity_keys),
                    production_line=get_val(row, production_line_keys),
                    status=new_status,
                    estimated_delivery_date=parse_date(get_val(row, estimated_delivery_keys)),
                    actual_delivery_date=parse_date(get_val(row, actual_delivery_keys)),
                    completion_date=completion_date_val
                )
                db.add(new_order)

        db.commit()
        
    except Exception as e:
        db.rollback()
        print(f"Excel kaydetme hatası: {e}")
        
    finally:
        db.close()
        # İŞLEM BİTİNCE geçici dosyamızı sunucudan siliyoruz.
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    # Başarıyla kaydedildikten sonra kullanıcıyı Sipariş Takip Paneline (/orders) yönlendiriyoruz.
    return RedirectResponse(url="/orders", status_code=303)