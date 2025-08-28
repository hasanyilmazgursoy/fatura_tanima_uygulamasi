import os
import json
import csv
import logging
import glob
from datetime import datetime
from fatura_analiz_motoru import FaturaAnalizMotoru
from typing import Dict
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
from tqdm import tqdm

# Logging'i en başta ve temel seviyede yapılandır
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log_ayarlarini_yap(rapor_klasoru: str):
    """
    Loglama ayarlarını yapılandırır. Hataları bir dosyaya kaydeder.
    """
    log_dosyasi = os.path.join(rapor_klasoru, "analiz_hatalari.log")
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename=log_dosyasi,
        filemode='w',
        encoding='utf-8'
    )
    logging.info(f"📝 Hata kayıtları (log) şu dosyaya yazılacak: {log_dosyasi}")

def analyze_file_for_pool(path: str, output_dir: str) -> Dict:
    """ProcessPoolExecutor ile kullanılabilir, üst seviye fonksiyon."""
    try:
        local = FaturaAnalizMotoru()
        try:
            local.output_dir = output_dir
        except Exception:
            pass
        return local.analiz_et(path)
    except Exception as e:
        return {"hata": str(e), "dosya": path}

def ayarları_yukle() -> dict:
    """
    config.json dosyasından ayarları yükler.
    """
    config_dosyasi = "config.json"
    try:
        with open(config_dosyasi, 'r', encoding='utf-8') as f:
            ayarlar = json.load(f)
        logging.info("✅ Konfigürasyon dosyası başarıyla yüklendi.")
        return ayarlar
    except FileNotFoundError:
        logging.error(f"❌ Hata: Konfigürasyon dosyası bulunamadı: '{config_dosyasi}'")
        logging.error("Lütfen proje ana dizininde bu dosyanın olduğundan emin olun.")
        return None
    except json.JSONDecodeError:
        logging.error(f"❌ Hata: '{config_dosyasi}' dosyası geçerli bir JSON formatında değil.")
        return None

def sonuclari_csv_kaydet(rapor_klasoru: str, tum_sonuclar: list):
    """
    Analiz sonuçlarını bir CSV dosyasına kaydeder.
    """
    if not tum_sonuclar:
        return

    csv_dosyasi = os.path.join(rapor_klasoru, f"toplu_fatura_raporu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    
    # Yapılandırılmış verileri ve OCR skorunu al
    yazilacak_veriler = []
    for sonuc in tum_sonuclar:
        veri = sonuc.get('structured', {})
        # OCR istatistiklerinden güven skorunu ekle
        ocr_stats = sonuc.get('ocr_istatistikleri', {})
        veri['ortalama_guven_skoru'] = ocr_stats.get('ortalama_guven_skoru')
        yazilacak_veriler.append(veri)
    
    # CSV başlıklarını (sütun isimlerini) dinamik olarak belirle
    # Tüm faturalardaki bütün olası alanları topla
    basliklar = set()
    for veri in yazilacak_veriler:
        basliklar.update(veri.keys())
    
    # Başlık sırasını belirle (güven skorunu başa alabiliriz)
    sirali_basliklar = sorted(list(basliklar))
    if 'ortalama_guven_skoru' in sirali_basliklar:
        sirali_basliklar.insert(0, sirali_basliklar.pop(sirali_basliklar.index('ortalama_guven_skoru')))

    try:
        with open(csv_dosyasi, 'w', newline='', encoding='utf-8-sig') as f:
            # `DictWriter` nesnesi, sözlükleri CSV satırlarına yazmayı kolaylaştırır
            writer = csv.DictWriter(f, fieldnames=sirali_basliklar)
            
            # Başlık satırını yaz
            writer.writeheader()
            
            # Her bir faturanın verisini bir satır olarak yaz
            writer.writerows(yazilacak_veriler)
        
        logging.info(f"📄 CSV raporu da başarıyla oluşturuldu: {csv_dosyasi}")
    except Exception as e:
        logging.error(f"❌ CSV dosyası yazılırken bir hata oluştu: {e}")
        logging.error(f"CSV dosyası yazılırken bir hata oluştu: {e}")


def sonuclari_turkce_formatla(analiz_sonucu: Dict) -> Dict:
    """
    Analiz motorundan gelen teknik sonuçları, son kullanıcı için
    okunaklı Türkçe alan adlarına dönüştürür.
    """
    alan_eslestirme_map = {
        # Teknik Alan Adı: Okunaklı Türkçe Alan Adı
        "satici_firma_unvani": "Satıcı Firma",
        "satici_adres": "Satıcı Adres",
        "satici_telefon": "Satıcı Telefon",
        "satici_email": "Satıcı E-Posta",
        "satici_vergi_dairesi": "Satıcı Vergi Dairesi",
        "satici_vergi_numarasi": "Satıcı Vergi No",
        "satici_mersis_no": "Satıcı Mersis No",
        "satici_ticaret_sicil": "Ticaret Sicil No",
        "alici_firma_unvani": "Alıcı Firma/Ad Soyad",
        "alici_adres": "Alıcı Adres",
        "alici_email": "Alıcı E-Posta",
        "alici_telefon": "Alıcı Telefon",
        "alici_tckn": "Alıcı TCKN",
        "fatura_numarasi": "Fatura No",
        "fatura_tarihi": "Fatura Tarihi",
        "son_odeme_tarihi": "Son Ödeme Tarihi",
        "ettn": "ETTN",
        "para_birimi": "Para Birimi",
        "toplam_iskonto": "Toplam İskonto",
        "vergi_haric_tutar": "Vergi Hariç Tutar",
        "hesaplanan_kdv": "Hesaplanan KDV",
        "genel_toplam": "Genel Toplam / Ödenecek Tutar",
    }
    
    kalem_eslestirme_map = {
        "aciklama": "Açıklama",
        "miktar": "Miktar",
        "birim_fiyat": "Birim Fiyat",
        "iskonto": "İskonto",
        "tutar": "Mal/Hizmet Tutarı",
        "kdv_orani": "KDV Oranı",
        "kdv_tutari": "KDV Tutarı"
    }

    formatlanmis_sonuc = {}
    structured_data = analiz_sonucu.get("structured", {})

    for teknik_ad, turkce_ad in alan_eslestirme_map.items():
        if structured_data.get(teknik_ad):
            formatlanmis_sonuc[turkce_ad] = structured_data[teknik_ad]

    # Kalemleri formatla
    if structured_data.get("kalemler"):
        formatlanmis_sonuc["Kalemler"] = []
        for kalem in structured_data["kalemler"]:
            formatli_kalem = {}
            for tek_ad, tur_ad in kalem_eslestirme_map.items():
                if kalem.get(tek_ad):
                    formatli_kalem[tur_ad] = kalem[tek_ad]
            if formatli_kalem:
                formatlanmis_sonuc["Kalemler"].append(formatli_kalem)

    return formatlanmis_sonuc


def ocr_metnini_disa_aktar(dosya_yolu: str, cikti_dosyasi: str):
    """Tek bir dosyanın ham OCR metnini dışa aktarır."""
    # BU FONKSİYON GEÇİCİ OLARAK DEVRE DIŞI BIRAKILDI
    logging.warning("ocr_metnini_disa_aktar fonksiyonu geçici olarak devre dışı.")
    return
    # try:
    #     with open('config.json', 'r', encoding='utf-8') as f:
    #         config = json.load(f)
    #     tesseract_path = config.get('tesseract_cmd_path')
    #     analiz_motoru = FaturaAnalizMotoru(tesseract_cmd_path=tesseract_path)
        
    #     sonuclar = analiz_motoru.analiz_et(dosya_yolu)
    #     ham_metin = sonuclar.get("ham_metin", "Metin çıkarılamadı.")
        
    #     with open(cikti_dosyasi, 'w', encoding='utf-8') as f:
    #         f.write(ham_metin)
        
    #     print(f"✅ Ham metin başarıyla kaydedildi: {cikti_dosyasi}")
    # except Exception as e:
    #     print(f"❌ Ham metin dışa aktarılırken bir hata oluştu: {e}")
    #     logging.error(f"Ham metin dışa aktarılırken bir hata oluştu: {e}")


def hizli_test_calistir(ham_metin_dosyasi: str):
    """Kaydedilmiş ham metin üzerinden sadece Regex analizini çalıştırır."""
    # BU FONKSİYON GEÇİCİ OLARAK DEVRE DIŞI BIRAKILDI
    logging.warning("hizli_test_calistir fonksiyonu geçici olarak devre dışı.")
    return
    # try:
    #     with open('config.json', 'r', encoding='utf-8') as f:
    #         config = json.load(f)
    #     tesseract_path = config.get('tesseract_cmd_path')
    #     analiz_motoru = FaturaAnalizMotoru(tesseract_cmd_path=tesseract_path)
        
    #     with open(ham_metin_dosyasi, 'r', encoding='utf-8') as f:
    #         ham_metin = f.read()
            
    #     yapilandirilmis_veri = analiz_motoru.yapilandirilmis_veri_cikar(ham_metin)
        
    #     print("\n--- HIZLI TEST SONUÇLARI ---")
    #     print(json.dumps(yapilandirilmis_veri, indent=2, ensure_ascii=False))
    # except Exception as e:
    #     print(f"❌ Hızlı test başlatılırken bir hata oluştu: {e}")
    #     logging.error(f"Hızlı test başlatılırken bir hata oluştu: {e}")


def ana_analiz_süreci():
    """
    Tüm faturaları işleyen ve raporlayan ana iş akışı.
    Bu fonksiyonu projenin ana giriş noktası olarak kullanın.
    """
    # Tek bir dosyayı test etmek için bu bölümü kullan
    tek_dosya_yolu = r"27.08.2025_Gelen Fatura (1)/05.07.2025-NYS2025000000188.pdf"
    
    # Tesseract yolunu config'den al
    tesseract_path = None
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        tesseract_path = config.get('tesseract_cmd_path')
    except FileNotFoundError:
        logging.warning("config.json bulunamadı.")

    analiz_motoru = FaturaAnalizMotoru(tesseract_cmd_path=tesseract_path)
    
    logging.info(f"Tek dosya analizi başlatılıyor: {tek_dosya_yolu}")
    sonuclar = analiz_motoru.analiz_et(tek_dosya_yolu)
    
    logging.info("--- ANALİZ SONUÇLARI ---")
    logging.info(json.dumps(sonuclar.get('yapilandirilmis_veri'), indent=2, ensure_ascii=False))
    logging.info("Debug görseli 'test_reports/debug_images' klasörüne kaydedildi.")


def akilli_test_analizi_yap(tum_sonuclar: list, rapor_klasoru: str):
    """
    🧠 Test sonuçlarını akıllıca analiz eder ve iyileştirme önerileri sunar
    """
    logging.info("🧠 AKILLI TEST ANALİZİ BAŞLATILIYOR...")
    
    # Analiz verilerini topla
    analiz_verileri = {
        'toplam_fatura': len(tum_sonuclar),
        'basarili_alanlar': {},
        'basarisiz_alanlar': {},
        'ocr_kalite_analizi': {},
        'regex_basari_oranlari': {},
        'hata_turleri': {},
        'iyilestirme_onerileri': [],
        'pattern_matching_basari': []
    }
    
    # Kritik alanları tanımla
    kritik_alanlar = {
        'fatura_numarasi': 'Fatura Numarası',
        'fatura_tarihi': 'Fatura Tarihi', 
        'genel_toplam': 'Genel Toplam',
        'satici_firma_unvani': 'Satıcı Firma',
        'alici_tckn': 'Alıcı TCKN',
        'ettn': 'ETTN'
    }
    
    # Her fatura için analiz yap
    for sonuc in tum_sonuclar:
        structured_data = sonuc.get('structured', {})
        ocr_stats = sonuc.get('ocr_istatistikleri', {})
        regex_sonuclari = sonuc.get('regex', {})
        
        # OCR kalitesi analizi
        guven_skoru = ocr_stats.get('ortalama_guven_skoru', '0%')
        if isinstance(guven_skoru, str):
            guven_skoru = float(guven_skoru.replace('%', ''))
        
        if guven_skoru >= 80:
            kalite_grubu = 'Yüksek'
        elif guven_skoru >= 60:
            kalite_grubu = 'Orta'
        else:
            kalite_grubu = 'Düşük'
        
        if kalite_grubu not in analiz_verileri['ocr_kalite_analizi']:
            analiz_verileri['ocr_kalite_analizi'][kalite_grubu] = 0
        analiz_verileri['ocr_kalite_analizi'][kalite_grubu] += 1
        
        # Alan başarı analizi
        for alan, aciklama in kritik_alanlar.items():
            if alan not in analiz_verileri['basarili_alanlar']:
                analiz_verileri['basarili_alanlar'][alan] = 0
                analiz_verileri['basarisiz_alanlar'][alan] = 0
            
            if structured_data.get(alan):
                analiz_verileri['basarili_alanlar'][alan] += 1
            else:
                analiz_verileri['basarisiz_alanlar'][alan] += 1
        
        # Regex başarı analizi
        for regex_alan, sonuclar in regex_sonuclari.items():
            if regex_alan not in analiz_verileri['regex_basari_oranlari']:
                analiz_verileri['regex_basari_oranlari'][regex_alan] = {'bulundu': 0, 'bulunamadi': 0}
            
            if sonuclar and len(sonuclar) > 0:
                analiz_verileri['regex_basari_oranlari'][regex_alan]['bulundu'] += 1
            else:
                analiz_verileri['regex_basari_oranlari'][regex_alan]['bulunamadi'] += 1
        
        # Pattern Matching Başarı Analizi
        pattern_basari = pattern_matching_basari_analizi(sonuc)
        if 'pattern_matching_basari' not in analiz_verileri:
            analiz_verileri['pattern_matching_basari'] = []
        analiz_verileri['pattern_matching_basari'].append(pattern_basari)
    
    # Başarı oranlarını hesapla
    basari_oranlari = {}
    for alan in kritik_alanlar:
        toplam = analiz_verileri['basarili_alanlar'][alan] + analiz_verileri['basarisiz_alanlar'][alan]
        if toplam > 0:
            oran = (analiz_verileri['basarili_alanlar'][alan] / toplam) * 100
            basari_oranlari[alan] = f"{oran:.1f}%"
    
    # Hata türlerini analiz et
    hata_analizi = hata_turlerini_analiz_et(tum_sonuclar)
    analiz_verileri['hata_turleri'] = hata_analizi
    
    # İyileştirme önerileri oluştur
    iyilestirme_onerileri = iyilestirme_onerileri_olustur(basari_oranlari, hata_analizi, analiz_verileri)
    analiz_verileri['iyilestirme_onerileri'] = iyilestirme_onerileri
    
    # Analiz raporunu yazdır
    akilli_analiz_raporu_yazdir(analiz_verileri, basari_oranlari)
    
    # Detaylı analiz raporunu kaydet
    akilli_analiz_raporu_kaydet(analiz_verileri, rapor_klasoru)
    
    return analiz_verileri

def hata_turlerini_analiz_et(tum_sonuclar: list) -> dict:
    """
    🔍 Hata türlerini kategorize eder ve analiz eder
    """
    hata_turleri = {
        'ocr_kalitesi_dusuk': 0,
        'regex_pattern_uyumsuz': 0,
        'format_farkliligi': 0,
        'karakter_tanima_hatasi': 0,
        'yapisal_bozulma': 0
    }
    
    for sonuc in tum_sonuclar:
        structured_data = sonuc.get('structured', {})
        ocr_stats = sonuc.get('ocr_istatistikleri', {})
        regex_sonuclari = sonuc.get('regex', {})
        
        # OCR kalitesi düşük
        guven_skoru = ocr_stats.get('ortalama_guven_skoru', '0%')
        if isinstance(guven_skoru, str):
            guven_skoru = float(guven_skoru.replace('%', ''))
        
        if guven_skoru < 60:
            hata_turleri['ocr_kalitesi_dusuk'] += 1
        
        # Regex pattern uyumsuzluğu
        eksik_alanlar = []
        for alan in ['fatura_numarasi', 'fatura_tarihi', 'genel_toplam']:
            if not structured_data.get(alan):
                eksik_alanlar.append(alan)
        
        if len(eksik_alanlar) >= 2:
            hata_turleri['regex_pattern_uyumsuz'] += 1
        
        # Format farklılığı
        ham_metin = ocr_stats.get('ham_metin', '')
        if ' - ' in ham_metin or ' | ' in ham_metin:
            hata_turleri['format_farkliligi'] += 1
        
        # Karakter tanıma hatası
        if '©' in ham_metin or '®' in ham_metin or '™' in ham_metin:
            hata_turleri['karakter_tanima_hatasi'] += 1
        
        # Yapısal bozulma
        if len(ham_metin.split()) > 500:  # Çok uzun metin
            hata_turleri['yapisal_bozulma'] += 1
    
    return hata_turleri

def iyilestirme_onerileri_olustur(basari_oranlari: dict, hata_analizi: dict, analiz_verileri: dict) -> list:
    """
    💡 İyileştirme önerileri oluşturur
    """
    oneriler = []
    
    # Başarı oranına göre öneriler
    for alan, oran in basari_oranlari.items():
        oran_deger = float(oran.replace('%', ''))
        if oran_deger < 50:
            oneriler.append(f"🚨 {alan.replace('_', ' ').title()}: %{oran_deger:.1f} başarı - Acil iyileştirme gerekli")
        elif oran_deger < 80:
            oneriler.append(f"⚠️ {alan.replace('_', ' ').title()}: %{oran_deger:.1f} başarı - İyileştirme önerilir")
    
    # Hata türlerine göre öneriler
    if hata_analizi['ocr_kalitesi_dusuk'] > 0:
        oneriler.append(f"🔧 OCR Kalitesi: {hata_analizi['ocr_kalitesi_dusuk']} fatura düşük kalite - PSM ayarları optimize edilmeli")
    
    if hata_analizi['regex_pattern_uyumsuz'] > 0:
        oneriler.append(f"🔧 Regex Desenleri: {hata_analizi['regex_pattern_uyumsuz']} fatura için uyumsuz - Yeni desenler eklenmeli")
    
    if hata_analizi['format_farkliligi'] > 0:
        oneriler.append(f"🔧 Format Desteği: {hata_analizi['format_farkliligi']} fatura farklı format - Format parser geliştirilmeli")
    
    # Genel öneriler
    if len(oneriler) == 0:
        oneriler.append("🎉 Tüm alanlar %80+ başarı oranında - Sistem mükemmel çalışıyor!")
    elif len(oneriler) <= 3:
        oneriler.append("✅ Sistem genel olarak iyi çalışıyor, küçük iyileştirmeler yeterli")
    else:
        oneriler.append("🚨 Sistem önemli iyileştirmeler gerektiriyor - Öncelikli alanlar belirlenmeli")
    
    return oneriler

def akilli_analiz_raporu_yazdir(analiz_verileri: dict, basari_oranlari: dict):
    """
    📊 Akıllı analiz raporunu ekrana yazdırır
    """
    logging.info("📊 AKILLI TEST ANALİZ RAPORU")
    logging.info(f"📈 TOPLAM FATURA SAYISI: {analiz_verileri['toplam_fatura']}")
    logging.info("🎯 ALAN BAŞARI ORANLARI:")
    for alan, oran in basari_oranlari.items():
        logging.info(f"   {alan.replace('_', ' ').title()}: {oran}")
    logging.info("🔍 HATA TÜRÜ ANALİZİ:")
    for hata_turu, sayi in analiz_verileri['hata_turleri'].items():
        if sayi > 0:
            logging.info(f"   {hata_turu.replace('_', ' ').title()}: {sayi} fatura")
    logging.info("💡 İYİLEŞTİRME ÖNERİLERİ:")
    for oneri in analiz_verileri['iyilestirme_onerileri']:
        logging.info(f"   {oneri}")
    logging.info("📊 OCR KALİTE DAĞILIMI:")
    for kalite, sayi in analiz_verileri['ocr_kalite_analizi'].items():
        yuzde = (sayi / analiz_verileri['toplam_fatura']) * 100
        logging.info(f"   {kalite}: {sayi} fatura (%{yuzde:.1f})")
    logging.info("🎯 PATTERN MATCHING BAŞARI ORANI:")
    if 'pattern_matching_basari' in analiz_verileri and analiz_verileri['pattern_matching_basari']:
        toplam_basari = sum(p['basari_orani'] for p in analiz_verileri['pattern_matching_basari'])
        ortalama_basari = toplam_basari / len(analiz_verileri['pattern_matching_basari'])
        logging.info(f"   Ortalama Pattern Matching Başarı Oranı: %{ortalama_basari:.1f}")
        
        # En başarılı ve en başarısız faturalar
        basarili_faturalar = [p for p in analiz_verileri['pattern_matching_basari'] if p['basari_orani'] >= 80]
        basarisiz_faturalar = [p for p in analiz_verileri['pattern_matching_basari'] if p['basari_orani'] < 50]
        
        logging.info(f"   Yüksek Başarılı (≥80%): {len(basarili_faturalar)} fatura")
        logging.info(f"   Düşük Başarılı (<50%): {len(basarisiz_faturalar)} fatura")
        
        if basarisiz_faturalar:
            logging.info("   En Düşük Başarılı Faturalar:")
            for fatura in sorted(basarisiz_faturalar, key=lambda x: x['basari_orani'])[:3]:
                dosya_adi = os.path.basename(fatura['dosya'])
                logging.info(f"     {dosya_adi}: %{fatura['basari_orani']:.1f}")

def akilli_analiz_raporu_kaydet(analiz_verileri: dict, rapor_klasoru: str):
    """
    💾 Akıllı analiz raporunu dosyaya kaydeder
    """
    rapor_dosyasi = os.path.join(rapor_klasoru, f"akilli_analiz_raporu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    with open(rapor_dosyasi, 'w', encoding='utf-8') as f:
        json.dump(analiz_verileri, f, ensure_ascii=False, indent=4)
    
    logging.info(f"💾 Akıllı analiz raporu kaydedildi: {rapor_dosyasi}")

def akilli_analiz_html_kaydet(analiz_verileri: dict, rapor_klasoru: str):
    """
    Akıllı analiz özetini basit bir HTML olarak kaydeder.
    """
    html_yolu = os.path.join(rapor_klasoru, f"akilli_analiz_ozet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")

    # Başarı oranlarını hesapla
    basarili = analiz_verileri.get('basarili_alanlar', {})
    basarisiz = analiz_verileri.get('basarisiz_alanlar', {})
    alanlar = sorted(set(list(basarili.keys()) + list(basarisiz.keys())))
    satirlar = []
    for alan in alanlar:
        toplam = basarili.get(alan, 0) + basarisiz.get(alan, 0)
        oran = (basarili.get(alan, 0) / toplam * 100) if toplam else 0.0
        satirlar.append(f"<tr><td>{alan}</td><td>{basarili.get(alan,0)}</td><td>{basarisiz.get(alan,0)}</td><td>{oran:.1f}%</td></tr>")

    ocr_kalite = analiz_verileri.get('ocr_kalite_analizi', {})
    hata_turleri = analiz_verileri.get('hata_turleri', {})
    oneriler = analiz_verileri.get('iyilestirme_onerileri', [])

    html = f"""
    <html><head><meta charset='utf-8'><title>Akıllı Analiz Özeti</title>
    <style>body{{font-family:Arial,sans-serif}} table,td,th{{border:1px solid #ddd;border-collapse:collapse;padding:6px}} th{{background:#f5f5f5}}</style>
    </head><body>
    <h2>Akıllı Analiz Özeti</h2>
    <h3>Alan Bazlı Başarı</h3>
    <table><tr><th>Alan</th><th>Başarılı</th><th>Başarısız</th><th>Başarı Oranı</th></tr>
    {''.join(satirlar)}
    </table>
    <h3>OCR Kalite Dağılımı</h3>
    <ul>
    {''.join(f"<li>{k}: {v}</li>" for k,v in ocr_kalite.items())}
    </ul>
    <h3>Hata Türleri</h3>
    <ul>
    {''.join(f"<li>{k}: {v}</li>" for k,v in hata_turleri.items())}
    </ul>
    <h3>İyileştirme Önerileri</h3>
    <ul>
    {''.join(f"<li>{o}</li>" for o in oneriler)}
    </ul>
    </body></html>
    """

    with open(html_yolu, 'w', encoding='utf-8') as f:
        f.write(html)

    logging.info(f"📄 HTML özet oluşturuldu: {html_yolu}")

from utils import norm_amount as _norm_amount, norm_date as _norm_date


def golden_degerlendirme_yap(run_klasoru: str, tum_sonuclar: list):
    """golden/golden.json dosyası varsa, çıkardığımız alanları beklenenlerle karşılaştırır."""
    import os, json, csv
    golden_path = os.path.join('golden', 'golden.json')
    if not os.path.exists(golden_path):
        logging.info("ℹ️ Golden set bulunamadı (golden/golden.json). Değerlendirme atlandı.")
        return
    try:
        golden = json.load(open(golden_path, encoding='utf-8'))
    except Exception as e:
        logging.error(f"❌ Golden set yüklenemedi: {e}")
        return

    # Golden formatı: [{"dosya": "filename.pdf", "expected": {"fatura_numarasi": "...", ...}}]
    exp_map = { os.path.basename(item.get('dosya','')): item.get('expected',{}) for item in golden }
    fields = sorted({ k for item in exp_map.values() for k in item.keys() }) or ['fatura_numarasi','fatura_tarihi','ettn','genel_toplam']

    results = []
    field_hits = {f: 0 for f in fields}
    field_total = {f: 0 for f in fields}

    for s in tum_sonuclar:
        base = os.path.basename(s.get('dosya',''))
        exp = exp_map.get(base)
        if not exp:
            continue
        got = s.get('structured', {})
        row = { 'dosya': base }
        for f in fields:
            expected = exp.get(f)
            actual = got.get(f)
            # normalize for certain fields
            if f in ('genel_toplam','mal_hizmet_toplam','hesaplanan_kdv'):
                expected_n = _norm_amount(expected)
                actual_n = _norm_amount(actual)
            elif f in ('fatura_tarihi','son_odeme_tarihi'):
                expected_n = _norm_date(expected)
                actual_n = _norm_date(actual)
            else:
                expected_n = str(expected or '').strip()
                actual_n = str(actual or '').strip()
            ok = bool(expected_n) and (expected_n == actual_n)
            row[f] = 'OK' if ok else f"EXP:{expected_n}|GOT:{actual_n}"
            if expected is not None:
                field_total[f] += 1
                if ok:
                    field_hits[f] += 1
        results.append(row)

    # Yaz
    out_json = os.path.join(run_klasoru, 'golden_evaluation.json')
    out_csv = os.path.join(run_klasoru, 'golden_evaluation.csv')
    json.dump({'results': results, 'fields': fields}, open(out_json,'w',encoding='utf-8'), ensure_ascii=False, indent=2)
    with open(out_csv, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=['dosya']+fields)
        w.writeheader(); w.writerows(results)

    # Özet
    logging.info('📐 Golden değerlendirme (alan başarı oranları):')
    for f in fields:
        tot = field_total.get(f,0) or 0
        hit = field_hits.get(f,0)
        oran = (hit/tot*100) if tot else 0.0
        logging.info(f"  - {f}: {hit}/{tot} (%{oran:.1f})")
    logging.info(f"📄 Golden raporları: {out_json}, {out_csv}")

def hata_turu_tespit_et(eksik_alanlar: list, ocr_stats: dict, regex_sonuclari: dict) -> str:
    """
    🔍 Tek bir fatura için hata türünü tespit eder
    """
    guven_skoru = ocr_stats.get('ortalama_guven_skoru', '0%')
    if isinstance(guven_skoru, str):
        guven_skoru = float(guven_skoru.replace('%', ''))
    
    ham_metin = ocr_stats.get('ham_metin', '')
    
    # OCR kalitesi düşük
    if guven_skoru < 60:
        return "OCR Kalitesi Düşük"
    
    # Regex pattern uyumsuzluğu
    if len(eksik_alanlar) >= 2:
        return "Regex Pattern Uyumsuzluğu"
    
    # Format farklılığı
    if ' - ' in ham_metin or ' | ' in ham_metin:
        return "Format Farklılığı"
    
    # Karakter tanıma hatası
    if '©' in ham_metin or '®' in ham_metin or '™' in ham_metin:
        return "Karakter Tanıma Hatası"
    
    # Yapısal bozulma
    if len(ham_metin.split()) > 500:
        return "Yapısal Bozulma"
    
    return "Bilinmeyen Hata"

def iyilestirme_onerisi_olustur_tek_fatura(eksik_alanlar: list, hata_turu: str, guven_skoru: str) -> str:
    """
    💡 Tek bir fatura için iyileştirme önerisi oluşturur
    """
    oneriler = []
    
    # OCR kalitesi düşükse
    if isinstance(guven_skoru, str):
        guven_skoru = float(guven_skoru.replace('%', ''))
    
    if guven_skoru < 60:
        oneriler.append("PSM ayarları optimize edilmeli")
    
    # Eksik alanlara göre öneriler
    if 'fatura_numarasi' in eksik_alanlar:
        oneriler.append("Fatura numarası regex deseni genişletilmeli")
    
    if 'fatura_tarihi' in eksik_alanlar:
        oneriler.append("Tarih formatı regex deseni güçlendirilmeli")
    
    if 'genel_toplam' in eksik_alanlar:
        oneriler.append("Para formatı regex deseni iyileştirilmeli")
    
    # Hata türüne göre öneriler
    if hata_turu == "Format Farklılığı":
        oneriler.append("Farklı formatlar için parser geliştirilmeli")
    
    if hata_turu == "Karakter Tanıma Hatası":
        oneriler.append("OCR karakter seti genişletilmeli")
    
    if not oneriler:
        return "Genel regex optimizasyonu önerilir"
    
    return "; ".join(oneriler)

def pattern_matching_basari_analizi(sonuc: dict) -> dict:
    """
    🎯 Pattern matching başarı oranını analiz eder
    """
    structured_data = sonuc.get('structured', {})
    regex_sonuclari = sonuc.get('regex', {})
    
    # Kritik alanlar için pattern matching başarısı
    kritik_alanlar = ['fatura_numarasi', 'fatura_tarihi', 'genel_toplam']
    pattern_basari = {
        'dosya': sonuc.get('dosya', ''),
        'toplam_alan': len(kritik_alanlar),
        'basarili_alan': 0,
        'basarisiz_alan': 0,
        'basari_orani': 0.0,
        'detayli_analiz': {}
    }
    
    for alan in kritik_alanlar:
        # Structured data'da var mı?
        structured_var = bool(structured_data.get(alan))
        
        # Regex'de bulundu mu?
        regex_alan = alan.replace('fatura_numarasi', 'fatura_no').replace('genel_toplam', 'para')
        regex_bulundu = bool(regex_sonuclari.get(regex_alan, []))
        
        if structured_var or regex_bulundu:
            pattern_basari['basarili_alan'] += 1
            durum = 'BAŞARILI'
        else:
            pattern_basari['basarisiz_alan'] += 1
            durum = 'BAŞARISIZ'
        
        pattern_basari['detayli_analiz'][alan] = {
            'structured_var': structured_var,
            'regex_bulundu': regex_bulundu,
            'durum': durum
        }
    
    if pattern_basari['toplam_alan'] > 0:
        pattern_basari['basari_orani'] = (pattern_basari['basarili_alan'] / pattern_basari['toplam_alan']) * 100
    
    return pattern_basari

if __name__ == "__main__":
    multiprocessing.freeze_support() # Windows için
    # Tek bir dosyayı test etmek için bu bölümü kullan
    tek_dosya_yolu = r"27.08.2025_Gelen Fatura (1)/05.07.2025-NYS2025000000188.pdf"

    # Proje ana dizinini bu dosyanın konumuna göre al
    PROJE_DIZINI = os.path.dirname(os.path.abspath(__file__))
    config_dosya_yolu = os.path.join(PROJE_DIZINI, 'config.json')
    
    # Tesseract yolunu config'den al
    tesseract_path = None
    try:
        with open(config_dosya_yolu, 'r', encoding='utf-8') as f:
            config = json.load(f)
        tesseract_path = config.get('tesseract_cmd_path')
    except FileNotFoundError:
        logging.warning(f"config.json bulunamadı: {config_dosya_yolu}")

    analiz_motoru = FaturaAnalizMotoru(tesseract_cmd_path=tesseract_path)
    
    logging.info(f"Tek dosya analizi başlatılıyor: {tek_dosya_yolu}")
    sonuclar = analiz_motoru.analiz_et(tek_dosya_yolu)
    
    logging.info("--- ANALİZ SONUÇLARI ---")
    logging.info(json.dumps(sonuclar.get('yapilandirilmis_veri'), indent=2, ensure_ascii=False))
    logging.info("Debug görseli 'test_reports/debug_images' klasörüne kaydedildi.")
