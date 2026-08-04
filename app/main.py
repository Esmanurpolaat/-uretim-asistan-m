# FastAPI uygulamasını oluşturmak için FastAPI ve Request sınıflarını içe aktarıyoruz.
# Dosya yükleme işlemleri için UploadFile ve File sınıflarını da dahil ediyoruz.
from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Form

# HTML ve Yönlendirme yanıtları döndürmek için kullanıyoruz.
from fastapi.responses import HTMLResponse, RedirectResponse
import os
from datetime import date, datetime

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
from sqlalchemy.orm import joinedload


# models.py içerisinde tanımlanan tabloları kontrol eder.
# Tablo yoksa SQLite içerisinde otomatik olarak oluşturur.
# Tablo zaten varsa yeniden oluşturmaz ve verileri silmez.
Base.metadata.create_all(bind=engine)

# Uygulama ayağa kalktığında otomatik olarak örnek sipariş verilerini ekliyoruz.
seed_orders()


# FastAPI uygulamasını oluşturuyoruz.
# title bilgisi otomatik API dokümantasyonunda gösterilir.
app = FastAPI(
    title="Üretim Asistanım", #title yani başlık cnm 
)


# HTML dosyalarımızın bulunduğu klasörü FastAPI'ye tanıtıyoruz.
templates = Jinja2Templates(
    directory="app/templates",# burda da klasör tanımladık cnm html kısmı burası işte  inja da pyhtondaki elemanları htmle aktarmaya yarayan şey 
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
    request: Request, #request, kullanıcı bir sayfayı açtığında tarayıcının sunucuya gönderdiği talebin bütün bilgilerini Python içerisinde tutan değişkendi
    start_date: str | None = None,  # Tarayıcıdan gelecek başlangıç tarihi (Örn: '2026-07-01')  bide boş kalabilir None=none olduğu için 
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
        completed_orders = db.query(models.Order).filter( # veritabanında sorgu yapıyoruz queryi o yüzden kullanıyoruz tamamalanan siparişleri getirmek için.
            models.Order.status == "Tamamlandı"
        ).count()
        
        # 4. Yeni Dashboard Kartı: Bugün ilk kez tamamlanan siparişler
        # completion_date alanı bugünün tarihine eşit olanları sayıyoruz.
        completed_today = db.query(models.Order).filter( # önce değişkenin adını atadık sonra da değişkenin içinde olucak veriyi sorguladık
            models.Order.completion_date == date.today() #bugun tamamlanma koşulu 
        ).count()
                # --- RİSK VE GECİKME ANALİZİ BAŞLANGICI ---
        # Tamamlanmamış (Yeni, Planlandı, Üretimde) ve tahmini teslim tarihi olan siparişleri çekiyoruz
        active_orders_list = db.query(models.Order).options(joinedload(models.Order.product)).filter(
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
        last_orders = db.query(models.Order).options(joinedload(models.Order.product)).order_by(models.Order.id.desc()).limit(5).all()
        
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
        orders = db.query(models.Order).options(joinedload(models.Order.product)).all()
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
# Yeni Sipariş Formu Açma Rotası
@app.get("/orders/new", response_class=HTMLResponse)
def get_new_order_form(request: Request):
    db = SessionLocal()
    try:
        lines = db.query(models.ProductionLine).all()
        products = db.query(models.Product).filter(models.Product.is_active == True).all()
    finally:
        db.close()
    return templates.TemplateResponse(
        request=request,
        name="order_form.html",
        context={
            "request": request,
            "order": None,
            "lines": lines,
            "products": products
        }
    )

# Sipariş Düzenleme Formu Açma Rotası
@app.get("/orders/{id}/edit", response_class=HTMLResponse)
def get_edit_order_form(request: Request, id: int):
    db = SessionLocal()
    try:
        order = db.query(models.Order).filter(models.Order.id == id).first()
        lines = db.query(models.ProductionLine).all()
        products = db.query(models.Product).filter(models.Product.is_active == True).all()
        if not order:
            raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")
    finally:
        db.close()
    return templates.TemplateResponse(
        request=request,
        name="order_form.html",
        context={
            "request": request,
            "order": order,
            "lines": lines,
            "products": products
        }
    )

# Yeni Sipariş Kaydetme Rotası (POST)
@app.post("/orders/new")
def post_new_order(
    request: Request,
    order_no: str = Form(...),
    item_no: str = Form(...),
    customer_name: str = Form(...),
    product_id: int = Form(...),
    quantity: float = Form(...),
    width: float = Form(None),
    grammage: float = Form(None),
    unit_price: float = Form(0.0),
    currency: str = Form("TRY"),
    market_type: str = Form("Yurtiçi"),
    sales_rep: str = Form(None),
    priority: str = Form("Orta"),
    production_line: str = Form(None),
    status: str = Form(...),
    estimated_delivery_date: str = Form(...),
    actual_delivery_date: str = Form(None)
):
    db = SessionLocal()
    try:
        # 1. Sipariş No ve Kalem No benzersizlik kontrolü
        existing_order = db.query(models.Order).filter(
            models.Order.order_no == order_no.strip(),
            models.Order.item_no == item_no.strip()
        ).first()
        
        if existing_order:
            lines = db.query(models.ProductionLine).all()
            products = db.query(models.Product).filter(models.Product.is_active == True).all()
            return templates.TemplateResponse(
                request=request,
                name="order_form.html",
                context={
                    "request": request,
                    "order": None,
                    "lines": lines,
                    "products": products,
                    "error": f"'{order_no}' ve Kalem '{item_no}' numaralı sipariş zaten kayıtlı!"
                }
            )
            
        # 2. Tarih formatlarını python date nesnelerine dönüştürüyoruz
        est_date = datetime.strptime(estimated_delivery_date, "%Y-%m-%d").date()
        act_date = None
        if actual_delivery_date and actual_delivery_date.strip():
            act_date = datetime.strptime(actual_delivery_date, "%Y-%m-%d").date()
            
        # 3. Yeni Sipariş modelini oluşturuyoruz ve veritabanına ekliyoruz
        new_order = models.Order(
            order_no=order_no.strip(),
            item_no=item_no.strip(),
            customer_name=customer_name.strip(),
            product_id=product_id,
            quantity=quantity,
            width=width,
            grammage=grammage,
            unit_price=unit_price,
            currency=currency.strip(),
            market_type=market_type.strip(),
            sales_rep=sales_rep.strip() if sales_rep else None,
            priority=priority.strip(),
            production_line=production_line.strip() if production_line else None,
            status=status.strip(),
            estimated_delivery_date=est_date,
            actual_delivery_date=act_date
        )
        db.add(new_order)
        db.commit()
    except Exception as e:
        db.rollback()
        lines = db.query(models.ProductionLine).all()
        products = db.query(models.Product).filter(models.Product.is_active == True).all()
        return templates.TemplateResponse(
            request=request,
            name="order_form.html",
            context={
                "request": request,
                "order": None,
                "lines": lines,
                "products": products,
                "error": f"Sipariş kaydedilirken bir hata oluştu: {str(e)}"
            }
        )
    finally:
        db.close()
        
    return RedirectResponse(url="/orders", status_code=303)

# Sipariş Güncelleme Rotası (POST)
@app.post("/orders/{id}/edit")
def post_edit_order(
    request: Request,
    id: int,
    customer_name: str = Form(...),
    product_id: int = Form(...),
    quantity: float = Form(...),
    width: float = Form(None),
    grammage: float = Form(None),
    unit_price: float = Form(0.0),
    currency: str = Form("TRY"),
    market_type: str = Form("Yurtiçi"),
    sales_rep: str = Form(None),
    priority: str = Form("Orta"),
    production_line: str = Form(None),
    status: str = Form(...),
    estimated_delivery_date: str = Form(...),
    actual_delivery_date: str = Form(None)
):
    db = SessionLocal()
    try:
        # 1. Siparişi veritabanından çekiyoruz
        order = db.query(models.Order).filter(models.Order.id == id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Sipariş bulunamadı.")
            
        # 2. İş Akışı (Durum Geçişleri) Kontrolü (Adım 5)
        # Geçerli durum geçiş haritasını tanımlıyoruz
        VALID_TRANSITIONS = {
            "Yeni": ["Yeni", "Planlandı"],
            "Planlandı": ["Yeni", "Planlandı", "Üretimde"],
            "Üretimde": ["Planlandı", "Üretimde", "Tamamlandı"],
            "Tamamlandı": ["Tamamlandı"]
        }
        
        current_status = order.status
        target_status = status.strip()
        
        # Eğer durum değişmişse ve bu değişim geçersizse hata verip durduruyoruz
        if current_status != target_status:
            allowed_next = VALID_TRANSITIONS.get(current_status, [current_status])
            if target_status not in allowed_next:
                lines = db.query(models.ProductionLine).all()
                products = db.query(models.Product).filter(models.Product.is_active == True).all()
                return templates.TemplateResponse(
                    request=request,
                    name="order_form.html",
                    context={
                        "request": request,
                        "order": order,
                        "lines": lines,
                        "products": products,
                        "error": f"Hatalı Durum Geçişi! '{current_status}' durumundaki bir sipariş doğrudan '{target_status}' yapılamaz. Geçilebilecek durumlar: {', '.join(allowed_next)}"
                    }
                )
        
        # 3. Tarih dönüşümlerini yapıyoruz
        est_date = datetime.strptime(estimated_delivery_date, "%Y-%m-%d").date()
        act_date = None
        if actual_delivery_date and actual_delivery_date.strip():
            act_date = datetime.strptime(actual_delivery_date, "%Y-%m-%d").date()
            
        # 4. Sipariş bilgilerini güncelliyoruz
        order.customer_name = customer_name.strip()
        order.product_id = product_id
        order.quantity = quantity
        order.width = width
        order.grammage = grammage
        order.unit_price = unit_price
        order.currency = currency.strip()
        order.market_type = market_type.strip()
        order.sales_rep = sales_rep.strip() if sales_rep else None
        order.priority = priority.strip()
        order.production_line = production_line.strip() if production_line else None
        order.status = target_status
        order.estimated_delivery_date = est_date
        order.actual_delivery_date = act_date
        
        db.commit()
    except Exception as e:
        db.rollback()
        lines = db.query(models.ProductionLine).all()
        products = db.query(models.Product).filter(models.Product.is_active == True).all()
        return templates.TemplateResponse(
            request=request,
            name="order_form.html",
            context={
                "request": request,
                "order": order,
                "lines": lines,
                "products": products,
                "error": f"Güncelleme hatası: {str(e)}"
            }
        )
    finally:
        db.close()
        
    return RedirectResponse(url="/orders", status_code=303)

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
            # Bu hatta atanmış ve henüz tamamlanmamış (aktif) siparişlerin listesini çekiyoruz
            active_orders = db.query(models.Order).filter(
                models.Order.production_line == line.line_name,
                models.Order.status.in_(["Yeni", "Planlandı", "Üretimde"])
            ).all()
            
            # Sipariş listesini arayüze göndermek için makine nesnemize ekliyoruz
            line.active_orders = active_orders
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

        # Yeni Alan Eşlemeleri (En, Gramaj, Fiyat vb.)
        width_keys = ["En", "Genişlik", "width", "Width", "En (cm)"]
        grammage_keys = ["Gramaj", "grammage", "Grammage", "Gramaj (g/m²)"]
        unit_price_keys = ["Birim Fiyat", "Fiyat", "unit_price", "Unit Price", "Price"]
        currency_keys = ["Döviz", "Para Birimi", "currency", "Currency"]
        market_type_keys = ["Pazar", "Pazar Türü", "market_type", "Market Type"]
        sales_rep_keys = ["Satış Temsilcisi", "Satışçı", "sales_rep", "Sales Rep", "Sales Representative"]
        priority_keys = ["Öncelik", "priority", "Priority"]

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

            # ÜRÜN BULMA VEYA OTOMATİK KATALOĞA EKLEME MANTIĞI
            prod_name_val = get_val(row, product_name_keys)
            product_id_val = None
            if prod_name_val:
                prod_name_val = str(prod_name_val).strip()
                # Veritabanında bu isimde ürün var mı?
                product_obj = db.query(models.Product).filter(models.Product.product_name == prod_name_val).first()
                
                # Yoksa otomatik oluşturuyoruz
                if not product_obj:
                    product_count = db.query(models.Product).count()
                    base_code = f"URN-AUTO{product_count + 1:03d}"
                    # Benzersiz kod kontrolü (mükerrer kod olmaması için)
                    while db.query(models.Product).filter(models.Product.product_code == base_code).first():
                        product_count += 1
                        base_code = f"URN-AUTO{product_count + 1:03d}"
                    
                    product_obj = models.Product(
                        product_code=base_code,
                        product_name=prod_name_val,
                        product_group="Otomatik",
                        is_active=True
                    )
                    db.add(product_obj)
                    db.flush() # ID almak için veritabanını tetikliyoruz
                
                product_id_val = product_obj.id

            if existing_order:
                # 1. Kural: Durum ilk kez "Tamamlandı" oluyorsa tamamlanma tarihini bugünün tarihi yapıyoruz.
                if new_status == "Tamamlandı":
                    if existing_order.status != "Tamamlandı" and not existing_order.completion_date:
                        existing_order.completion_date = date.today()
                
                # Mevcut kaydı güncelliyoruz.
                existing_order.status = new_status
                existing_order.customer_name = get_val(row, customer_name_keys, existing_order.customer_name)
                if product_id_val is not None:
                    existing_order.product_id = product_id_val
                existing_order.quantity = get_val(row, quantity_keys, existing_order.quantity)
                existing_order.production_line = get_val(row, production_line_keys, existing_order.production_line)
                existing_order.estimated_delivery_date = parse_date(get_val(row, estimated_delivery_keys, existing_order.estimated_delivery_date))
                existing_order.actual_delivery_date = parse_date(get_val(row, actual_delivery_keys, existing_order.actual_delivery_date))
                
                # Yeni veriler varsa mevcut kaydı güncelliyoruz
                existing_order.width = get_val(row, width_keys, existing_order.width)
                existing_order.grammage = get_val(row, grammage_keys, existing_order.grammage)
                existing_order.unit_price = get_val(row, unit_price_keys, existing_order.unit_price)
                existing_order.currency = get_val(row, currency_keys, existing_order.currency)
                existing_order.market_type = get_val(row, market_type_keys, existing_order.market_type)
                existing_order.sales_rep = get_val(row, sales_rep_keys, existing_order.sales_rep)
                existing_order.priority = get_val(row, priority_keys, existing_order.priority)
                
            else:
                # EĞER YOKSA: Yeni kayıt oluşturuyoruz.
                completion_date_val = None
                if new_status == "Tamamlandı":
                    completion_date_val = date.today()

                new_order = models.Order(
                    order_no=order_no,
                    item_no=item_no,
                    customer_name=get_val(row, customer_name_keys),
                    product_id=product_id_val,
                    quantity=get_val(row, quantity_keys),
                    width=get_val(row, width_keys),
                    grammage=get_val(row, grammage_keys),
                    unit_price=get_val(row, unit_price_keys, 0.0),
                    currency=get_val(row, currency_keys, "TRY"),
                    market_type=get_val(row, market_type_keys, "Yurtiçi"),
                    sales_rep=get_val(row, sales_rep_keys),
                    priority=get_val(row, priority_keys, "Orta"),
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

# crud kısmının get rotasını kelyeceğiz şuan#
@app.get("/products", response_class=HTMLResponse)
def get_products(request:Request):
    db=SessionLocal()
    try:
        products= db.query(models.Product).all()
    finally:
        db.close()
    return templates.TemplateResponse(
        
            request=request,
            name="products.html" ,
            context ={ 
                "title":"Ürün Kataloğu - Üretim Asistanım",
                "products":products,
            }
        )
# burda da düzenleme yeni ürün kısmı için get rotası oluşturuyorum #
@app.get("/products/new", response_class=HTMLResponse) 
def get_new_product_form(request: Request):
    return templates.TemplateResponse(
      request=request,
      name="product_form.html",
      context={
          "title":"Yeni Ürün Ekle - Üretim Asistanım",
          "product":None
      }
    )
#post rotasını ekliyoruz yeni ürün ekleme güncelleme  post veri gödermeye yarar get çekmeye 
@app.post("/products/new")
def post_new_product(#bu fonksiyon html formundan gönderilen bilgileri teslim alır 
    request: Request,#tarayıcıdan gelen isteği belirtiyo
    product_code: str = Form(...), #form(...) formdan gelecek bu alanların zorunlu olduğu anlamına gelir 
    product_name: str = Form(...),
    product_group: str | None = Form(None),# form(none)forma göderilmezse o alanı none yapabilirsin demek 
    standard_width: float | None = Form(None), #| none da direkt boş olabilir anlamında 
    grammage: float | None = Form(None),
    unit: str = Form("Metre"), #boşssa metre ver 
    eligible_lines: str | None = Form(None),
):
    db = SessionLocal()
    try:#hata olursa doğru düzgün çalıştırılsın diye 
        existing = db.query(models.Product).filter( #existing daha önce aynı isimde veri var mıydı nın kontrolunu sağlıyor 
            #filter kısmı da neye göre arama yapacağını verir db.query de zaten sorgulama yapcam models.productta dıyor 
            models.Product.product_code == product_code.strip()#strip metinin balındaki ve sonundaki gereksiz bilgileri siler 
        ).first()

        if existing: # ürün zaten varsa 
            return templates.TemplateResponse(
                request=request,
                name="product_form.html",
                context={
                    "title": "Yeni Ürün Ekle - Üretim Asistanım",
                    "product": None,
                    "error": f"'{product_code}' ürün kodu zaten kayıtlı!"#gönderilen hata kısmı burası 
                }
            )

        # Yeni ürün nesnesi oluşturuyoruz
        new_product = models.Product(
            product_code=product_code.strip(),
            product_name=product_name.strip(),
            product_group=product_group.strip() if product_group else None, #Product group doluysa boşluklarını temizle;boşsa none kaydet 
            standard_width=standard_width,
            grammage=grammage,
            unit=unit,
            eligible_lines=eligible_lines.strip() if eligible_lines else None,
            is_active=True #eklenen ürün başlangıçta aktif oluşturulur 

        )
        db.add(new_product)
        db.commit() #yapılan değişikliği kesin olarak veritabanına kaydet
    except Exception as e: #try içinde herhanhi bir hata olusursa pyhton direkt buraya geçer 
        db.rollback() #hata olursa tamamlanmış verileri geri al 
        print(f"Ürün kaydetme hatası: {e}")
        return templates.TemplateResponse(
            request=request,
            name="product_form.html",
            context={
                "title": "Yeni Ürün Ekle - Üretim Asistanım",
                "product": None,
                "error": "Ürün kaydedilirken sistemsel bir hata oluştu!"
            }
        )
    finally:
        db.close()

    return RedirectResponse(url="/products", status_code=303) #ürün başarıyla kaydedilirse kullanıcı ürünler sayfasına yönlendirilir 

@app.get("/products/{id}/edit", response_class=HTMLResponse)
def get_edit_product_form(id: int, request: Request):
    db = SessionLocal()
    try:
        # first kısmı da şey anlamında sorgudan sonraki ilk sonucu getir
        product = db.query(models.Product).filter(models.Product.id == id).first()
    finally:
        db.close()

    return templates.TemplateResponse(
        request=request,
        name="product_form.html",
        context={
            "title": "Ürün Düzenle - Üretim Asistanım",
            "product": product
        }
    )


# get/products/5/edit 
# idsi 5 olan ürünü düzenlemek için, mevcut bilgileri forma doldurur
# formu kullanıcıya gönderir
# post product 5 edit 5 numaralı üründe yapılan değişiklikleri alır o veriyi bulur
# yeni değerlerle günceller veritabanına kaydeder

# bu kısmın çalışma mantığı sırasıyla
# form bilgileri fonksiyonuna gelir, veritabanı açılır, ürün için başlangıç değerleri verilir
# tryla riskli işlemler başlatılır, idye göre urun aranır, ürün bulunmuş mu kontrol edilir, ürün kodu başkasında var mı kontrol edilir
# aynı kod başka üründe varsa form geri açılır çakışma yoksa ürün alanları değiştirilir,
# değişiklikler kaydedilir, hata çıkarsa except çalışır

# şimdi de get yaptığımız güncellemeyi post yapacağız
@app.post("/products/{id}/edit")
def post_edit_product(
    id: int,
    request: Request,
    product_code: str = Form(...),
    product_name: str = Form(...),
    product_group: str | None = Form(None),  # bu kısımlar aslında html formundaki verileri alıyor 
    standard_width: float | None = Form(None),
    grammage: float | None = Form(None),
    unit: str = Form("Metre"),
    eligible_lines: str | None = Form(None),
    is_active: bool = Form(True)
):
    db = SessionLocal()
    product = None

    try:
        product = db.query(models.Product).filter(models.Product.id == id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Ürün Bulunamadı") 

        existing = db.query(models.Product).filter(
            models.Product.product_code == product_code.strip(),
            models.Product.id != id
        ).first()

        if existing:
            return templates.TemplateResponse(
                request=request,
                name="product_form.html",
                context={
                    "title": "Ürün Düzenle - Üretim Asistanım",
                    "product": product,
                    "error": f"'{product_code}' Ürün kodu başka bir ürüne ait!"
                }
            )

        # alınan veriyi mevcut ürüne aktarır
        product.product_code = product_code.strip()
        product.product_name = product_name.strip()
        product.product_group = product_group.strip() if product_group else None
        product.standard_width = standard_width
        product.grammage = grammage
        product.unit = unit
        product.eligible_lines = eligible_lines.strip() if eligible_lines else None
        product.is_active = is_active
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Ürün düzenleme hatası: {e}")
        return templates.TemplateResponse(
            request=request,
            name="product_form.html",
            context={
                "title": "Ürün Düzenle - Üretim Asistanım",
                "product": product,
                "error": "Ürün güncellenirken bir hata oluştu!"
            }
        )
    finally:
        db.close()
        

    return RedirectResponse(url="/products", status_code=303)

# burda da hammadde katalogu ksımının veritabanından get isteklerini yapıyoruz api bağlantısı ile  
@app.get("/raw-materials", response_class=HTMLResponse)
def get_raw_materials(request: Request):
    db = SessionLocal()
    try: 
        raw_materials = db.query(models.RawMaterial).all()
    finally:
        db.close()
        
    return templates.TemplateResponse(
        request=request,
        name="raw_materials.html",
        context={
            "title": "Hammadde Kataloğu - Üretim Asistanım",
            "raw_materials": raw_materials
        }
    )

@app.get("/raw-materials/new", response_class=HTMLResponse)
def get_raw_material_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="raw_material_form.html",
        context={
            "title": "Yeni Hammadde Ekle - Üretim Asistanım",
            "raw_material": None
        }
    )

@app.post("/raw-materials/new")
def post_raw_material(
    request: Request,
    material_code: str = Form(...),
    material_name: str = Form(...),
    material_type: str | None = Form(None),
    unit: str = Form("Kg"),
    min_stock: float = Form(0.0),
    safety_stock: float = Form(0.0),
    min_order_qty: float = Form(0.0),
    lead_time: int = Form(0)
):
    db = SessionLocal()
    try: 
        existing = db.query(models.RawMaterial).filter(
            models.RawMaterial.material_code == material_code.strip()
        ).first()
        
        if existing:
            return templates.TemplateResponse(
                request=request,
                name="raw_material_form.html",
                context={
                    "title": "Yeni Hammadde Ekle - Üretim Asistanım",
                    "raw_material": None,
                    "error": f"'{material_code}' hammadde kodu zaten kayıtlı!"
                }
            )
            
        new_material = models.RawMaterial(
            material_code=material_code.strip(),
            material_name=material_name.strip(),
            material_type=material_type.strip() if material_type else None,
            unit=unit,
            min_stock=min_stock,
            safety_stock=safety_stock,
            min_order_qty=min_order_qty,
            lead_time=lead_time,
            is_active=True
        )
        db.add(new_material)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Hammadde kaydetme hatası: {e}")
        return templates.TemplateResponse(
            request=request,
            name="raw_material_form.html",
            context={
                "title": "Yeni Hammadde Ekle - Üretim Asistanım",
                "raw_material": None,
                "error": "Hammadde kaydedilirken sistemsel bir hata oluştu!"
            }
        )
    finally:
        db.close()
        
    return RedirectResponse(url="/raw-materials", status_code=303)

#üst kısımda hammadde stok kısmının yeni olusturma get se post rotalarını koymustum sımdı işe düzenleme kısmının get ve post rotalarını eklicem
@app.get("/raw-materials/{id}/edit", response_class=HTMLResponse)
def get_edit_raw_material_form(id: int, request: Request):
    db = SessionLocal()
    try:
        raw_material = db.query(models.RawMaterial).filter(models.RawMaterial.id == id).first()
    finally:
        db.close()

    return templates.TemplateResponse(
        request=request,
        name="raw_material_form.html",
        context={
            "title": "Hammadde Düzenle - Üretim Asistanım",
            "raw_material": raw_material
        }
    )

#hammadde duzenlenme kısmının post isteği
@app.post("/raw-materials/{id}/edit")
def post_edit_raw_material(
    id: int,
    request: Request,
    material_code: str = Form(...),
    material_name: str = Form(...),
    material_type: str | None = Form(None),
    unit: str = Form("Kg"),
    min_stock: float = Form(0.0),
    safety_stock: float = Form(0.0),
    min_order_qty: float = Form(0.0),
    lead_time: int = Form(0),
    is_active: bool = Form(True)
):
    db = SessionLocal()
    raw_material = None
    try:
        raw_material = db.query(models.RawMaterial).filter(models.RawMaterial.id == id).first()
        if not raw_material:
            raise HTTPException(status_code=404, detail="Hammadde bulunamadı")

        existing = db.query(models.RawMaterial).filter(
            models.RawMaterial.material_code == material_code.strip(),
            models.RawMaterial.id != id
        ).first()

        if existing:
            return templates.TemplateResponse(
                request=request,
                name="raw_material_form.html",
                context={
                    "title": "Hammadde Düzenle - Üretim Asistanım",
                    "raw_material": raw_material,
                    "error": f"'{material_code}' hammadde kodu başka bir hammaddeye ait!"
                }
            )

        #kanka burda da yeni bilgileri veriypruz 
        raw_material.material_code = material_code.strip() #strip sadece metinler(string) için geçerli olan bir komuttur 
        raw_material.material_name = material_name.strip()
        raw_material.material_type = material_type.strip() if material_type else None
        raw_material.unit = unit
        raw_material.min_stock = min_stock
        raw_material.safety_stock = safety_stock
        raw_material.min_order_qty = min_order_qty
        raw_material.lead_time = lead_time
        raw_material.is_active = is_active

        db.commit()
    except Exception as e: #herhangi bir hata varsa bu bloğu çalıştır 
        db.rollback()
        print(f"Hammadde düzenleme hatası: {e}")
        return templates.TemplateResponse(
            request=request,
            name="raw_material_form.html",
            context={
                "title": "Hammadde Düzenle - Üretim Asistanım",
                "raw_material": raw_material,
                "error": "Hammadde güncellenirken bir hata oluştu!"
                #kanka burda tekrar form kısmını veriyoruz ki hata olsutugunda bos ekran değil tekrar form gelsin bize 
                #zaten templates html de formu çizdiren kısım bizde o yzüden tekrar templates yazıyoruz 
            }
        )
    finally:
        db.close()
        
    return RedirectResponse(url="/raw-materials", status_code=303)
# Depo stok takip sayfası (GET)
@app.get("/stocks", response_class=HTMLResponse)
def get_warehouse_stocks(request: Request):
    db = SessionLocal()
    try:
        # joinedload kullanarak stoklarla birlikte ilişkili hammadde bilgilerini de tek sorguda çekiyoruz
        stocks = db.query(models.WarehouseStock).options(
            joinedload(models.WarehouseStock.raw_material)
        ).all()
        
        # Stok durumunu kontrol etmek amacıyla hammadde emniyet stoğu kontrolü için tüm aktif hammaddeleri de çekiyoruz
        raw_materials = db.query(models.RawMaterial).filter(models.RawMaterial.is_active == True).all()
    finally:
        db.close()
        
    return templates.TemplateResponse(
        request=request,
        name="stocks.html",
        context={
            "title": "Depo Stok Takibi - Üretim Asistanım",
            "stocks": stocks,
            "raw_materials": raw_materials
        }
    )
# Yeni stok giriş formu (GET)
@app.get("/stocks/new", response_class=HTMLResponse)
def get_new_stock_form(request: Request):
    db = SessionLocal()
    try:
        # Formda hammadde seçebilmek için aktif hammaddeleri çekiyoruz
        raw_materials = db.query(models.RawMaterial).filter(models.RawMaterial.is_active == True).all()
    finally:
        db.close()
        
    return templates.TemplateResponse(
        request=request,
        name="stock_form.html",
        context={
            "title": "Yeni Stok Girişi - Üretim Asistanım",
            "raw_materials": raw_materials
        }
    )

# Yeni stok kaydetme işlemi (POST)
@app.post("/stocks/new")
def post_new_stock(
    request: Request,
    raw_material_id: int = Form(...),
    warehouse_name: str = Form(...),
    lot_number: str = Form(...),
    physical_stock: float = Form(0.0)
):
    db = SessionLocal()
    try:
        # İlk girişte rezerve stok sıfır, kullanılabilir stok ise fiziksel stoğa eşittir
        new_stock = models.WarehouseStock(
            raw_material_id=raw_material_id,
            warehouse_name=warehouse_name.strip(),
            lot_number=lot_number.strip().upper(),  # Lot numaralarını standart olması için büyük harfe çeviriyoruz
            physical_stock=physical_stock,
            reserved_stock=0.0,
            usable_stock=physical_stock
        )
        db.add(new_stock)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Stok kaydetme hatası: {e}")
        # Hata durumunda formu aktif hammaddelerle birlikte tekrar yüklüyoruz
        raw_materials = db.query(models.RawMaterial).filter(models.RawMaterial.is_active == True).all()
        return templates.TemplateResponse(
            request=request,
            name="stock_form.html",
            context={
                "title": "Yeni Stok Girişi - Üretim Asistanım",
                "raw_materials": raw_materials,
                "error": "Stok kaydedilirken sistemsel bir hata oluştu!"
            }
        )
    finally:
        db.close()
        
    return RedirectResponse(url="/stocks", status_code=303)

@app.get("/recipes", response_class=HTMLResponse)
def get_recipes(request: Request):
    db = SessionLocal()
    try:
        #joinedload kullancaz ortak bağlantı için 
        recipes = db.query(models.Recipe).options(
            joinedload(models.Recipe.product),
            joinedload(models.Recipe.raw_material)  
        ).all()
    finally:
        db.close()
        
    return templates.TemplateResponse(
        request=request,
        name="recipes.html",
        context={
            "title": "Ürün Reçeteleri (BOM) - Üretim Asistanım",
            "recipes": recipes
        }   
    )
# Yeni reçete ekleme formu (GET)
@app.get("/recipes/new", response_class=HTMLResponse)
def get_new_recipe_form(request: Request):
    db = SessionLocal()
    try:
        # Formda seçilebilmesi için aktif ürünleri ve aktif hammaddeleri çekiyoruz
        products = db.query(models.Product).filter(models.Product.is_active == True).all()
        raw_materials = db.query(models.RawMaterial).filter(models.RawMaterial.is_active == True).all()
    finally:
        db.close()
        
    return templates.TemplateResponse(
        request=request,
        name="recipe_form.html",
        context={
            "title": "Yeni Ürün Reçetesi (BOM) Ekle - Üretim Asistanım",
            "products": products,
            "raw_materials": raw_materials,
            "recipe": None  # Yeni ekleme olduğu için reçete boş gidiyor
        }
    )

# Yeni reçete kaydetme işlemi (POST)
@app.post("/recipes/new")
def post_new_recipe(
    request: Request,
    product_id: int = Form(...),
    raw_material_id: int = Form(...),
    quantity_needed: float = Form(...),
    scrap_rate: float = Form(0.0),
    version: str = Form("v1.0")
):
    db = SessionLocal()
    try:
        # Seçilen ürün ve hammadde arasında zaten bir reçete tanımı var mı kontrol ediyoruz
        existing = db.query(models.Recipe).filter(
            models.Recipe.product_id == product_id,
            models.Recipe.raw_material_id == raw_material_id
        ).first()
        
        if existing:
            # Hata durumunda dropdown'ları doldurmak için ürün ve hammaddeleri tekrar çekiyoruz
            products = db.query(models.Product).filter(models.Product.is_active == True).all()
            raw_materials = db.query(models.RawMaterial).filter(models.RawMaterial.is_active == True).all()
            return templates.TemplateResponse(
                request=request,
                name="recipe_form.html",
                context={
                    "title": "Yeni Ürün Reçetesi (BOM) Ekle - Üretim Asistanım",
                    "products": products,
                    "raw_materials": raw_materials,
                    "recipe": None,
                    "error": "Bu ürün ve hammadde eşleşmesi için zaten bir reçete satırı tanımlı!"
                }
            )
        
        # Yeni reçete kaydını oluşturuyoruz
        new_recipe = models.Recipe(
            product_id=product_id,
            raw_material_id=raw_material_id,
            quantity_needed=quantity_needed,
            scrap_rate=scrap_rate / 100.0,  # Arayüzden %5 olarak gelen veriyi 0.05 olarak kaydediyoruz
            version=version.strip()
        )
        db.add(new_recipe)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Reçete kaydetme hatası: {e}")
        products = db.query(models.Product).filter(models.Product.is_active == True).all()
        raw_materials = db.query(models.RawMaterial).filter(models.RawMaterial.is_active == True).all()
        return templates.TemplateResponse(
            request=request,
            name="recipe_form.html",
            context={
                "title": "Yeni Ürün Reçetesi (BOM) Ekle - Üretim Asistanım",
                "products": products,
                "raw_materials": raw_materials,
                "recipe": None,
                "error": "Reçete kaydedilirken sistemsel bir hata oluştu!"
            }
        )
    finally:
        db.close()
        
    return RedirectResponse(url="/recipes", status_code=303)

# Reçete düzenleme formu (GET)
@app.get("/recipes/{id}/edit", response_class=HTMLResponse)
def get_edit_recipe_form(id: int, request: Request):
    db = SessionLocal()
    try:
        # Düzenlenecek reçeteyi veritabanından çekiyoruz
        recipe = db.query(models.Recipe).filter(models.Recipe.id == id).first()
        if not recipe:
            raise HTTPException(status_code=404, detail="Reçete bulunamadı")
            
        # Formda gösterilmek üzere aktif ürün ve hammaddeleri çekiyoruz
        products = db.query(models.Product).filter(models.Product.is_active == True).all()
        raw_materials = db.query(models.RawMaterial).filter(models.RawMaterial.is_active == True).all()
    finally:
        db.close()
        
    return templates.TemplateResponse(
        request=request,
        name="recipe_form.html",
        context={
            "title": "Ürün Reçetesi (BOM) Düzenle - Üretim Asistanım",
            "products": products,
            "raw_materials": raw_materials,
            "recipe": recipe
        }
    )

# Reçete düzenleme kaydı (POST)
@app.post("/recipes/{id}/edit")
def post_edit_recipe(
    id: int,
    request: Request,
    product_id: int = Form(...),
    raw_material_id: int = Form(...),
    quantity_needed: float = Form(...),
    scrap_rate: float = Form(0.0),
    version: str = Form("v1.0")
):
    db = SessionLocal()
    recipe = None
    try:
        # Reçeteyi buluyoruz
        recipe = db.query(models.Recipe).filter(models.Recipe.id == id).first()
        if not recipe:
            #raise şey demek hatayı direkt biz göderiyoruz eğer şartlar sağlanmadıysa direkt kodun devamını çalıştırma ve bu hata mesajını gönder 
            raise HTTPException(status_code=404, detail="Reçete bulunamadı")
            
        # Mükerrer Eşleşme Kontrolü: Ürün veya hammadde değiştirildiyse, bu eşleşmenin başka bir reçetede olmaması gerekir
        existing = db.query(models.Recipe).filter(
            models.Recipe.product_id == product_id,
            models.Recipe.raw_material_id == raw_material_id,
            models.Recipe.id != id
        ).first()
        
        if existing:
            products = db.query(models.Product).filter(models.Product.is_active == True).all()
            raw_materials = db.query(models.RawMaterial).filter(models.RawMaterial.is_active == True).all()
            return templates.TemplateResponse(
                request=request,
                name="recipe_form.html",
                context={
                    "title": "Ürün Reçetesi (BOM) Düzenle - Üretim Asistanım",
                    "products": products,
                    "raw_materials": raw_materials,
                    "recipe": recipe,
                    "error": "Bu ürün ve hammadde eşleşmesi için başka bir reçete zaten tanımlı!"
                }
            )
            
        # Bilgileri güncelliyoruz
        recipe.product_id = product_id
        recipe.raw_material_id = raw_material_id
        recipe.quantity_needed = quantity_needed
        recipe.scrap_rate = scrap_rate / 100.0  # Arayüzden %5 olarak gelen veriyi 0.05 olarak güncelliyoruz
        recipe.version = version.strip()
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Reçete düzenleme hatası: {e}")
        products = db.query(models.Product).filter(models.Product.is_active == True).all()
        raw_materials = db.query(models.RawMaterial).filter(models.RawMaterial.is_active == True).all()
        return templates.TemplateResponse(
            request=request,
            name="recipe_form.html",
            context={
                "title": "Ürün Reçetesi (BOM) Düzenle - Üretim Asistanım",
                "products": products,
                "raw_materials": raw_materials,
                "recipe": recipe,
                "error": "Reçete güncellenirken sistemsel bir hata oluştu!"
            }
        )
    finally:
        db.close()
        
    return RedirectResponse(url="/recipes", status_code=303)
    