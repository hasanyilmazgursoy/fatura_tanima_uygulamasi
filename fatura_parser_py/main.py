import os
import json
import csv
import logging
import glob
from datetime import datetime
from fatura_regex_analiz_yeni import FaturaRegexAnaliz
from typing import Dict
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

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
    print(f"📝 Hata kayıtları (log) şu dosyaya yazılacak: {log_dosyasi}")

def analyze_file_for_pool(path: str, output_dir: str) -> Dict:
    """ProcessPoolExecutor ile kullanılabilir, üst seviye fonksiyon."""
    try:
        local = FaturaRegexAnaliz()
        try:
            local.output_dir = output_dir
        except Exception:
            pass
        return local.fatura_analiz_et(path, gorsellestir=False)
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
        print("✅ Konfigürasyon dosyası başarıyla yüklendi.")
        return ayarlar
    except FileNotFoundError:
        print(f"❌ Hata: Konfigürasyon dosyası bulunamadı: '{config_dosyasi}'")
        print("Lütfen proje ana dizininde bu dosyanın olduğundan emin olun.")
        return None
    except json.JSONDecodeError:
        print(f"❌ Hata: '{config_dosyasi}' dosyası geçerli bir JSON formatında değil.")
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
        
        print(f"📄 CSV raporu da başarıyla oluşturuldu: {csv_dosyasi}")
    except Exception as e:
        print(f"❌ CSV dosyası yazılırken bir hata oluştu: {e}")
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


def ocr_metnini_disa_aktar(analiz_sistemi: FaturaRegexAnaliz, dosya_yolu: str, rapor_klasoru: str):
    """
    Belirli bir faturayı analiz eder ve OCR'dan çıkan ham metni bir .txt dosyasına kaydeder.
    Bu, Regex ve veri çıkarma mantığını test etmek için kullanılır.
    """
    print(f"\n📄 OCR Ham Metin Dışa Aktarma: {os.path.basename(dosya_yolu)}")
    img = analiz_sistemi.resmi_yukle(dosya_yolu)
    if img is None:
        return
    
    processed_img = analiz_sistemi.resmi_on_isle(img)
    ocr_data, _ = analiz_sistemi.metni_cikar(processed_img)
    
    valid_texts = [
        text.strip()
        for conf, text in zip(ocr_data['conf'], ocr_data['text'])
        if int(conf) >= analiz_sistemi.min_confidence and text and text.strip()
    ]
    ham_metin = ' '.join(valid_texts)
    
    # Çıktı dosyasının adını oluştur
    base_name = os.path.splitext(os.path.basename(dosya_yolu))[0]
    txt_dosyasi = os.path.join(rapor_klasoru, f"hizli_test_{base_name}.txt")
    
    with open(txt_dosyasi, 'w', encoding='utf-8') as f:
        f.write(ham_metin)
        
    print(f"✅ Ham metin başarıyla kaydedildi: {txt_dosyasi}")


def hizli_test_calistir(analiz_sistemi: FaturaRegexAnaliz, txt_dosya_yolu: str):
    """
    Kaydedilmiş bir .txt dosyasındaki ham metni kullanarak sadece veri çıkarma adımını test eder.
    """
    print(f"\n⚡ Hızlı Test Başlatılıyor: {os.path.basename(txt_dosya_yolu)}")
    if not os.path.exists(txt_dosya_yolu):
        print(f"❌ Hata: Test metin dosyası bulunamadı: {txt_dosya_yolu}")
        return

    with open(txt_dosya_yolu, 'r', encoding='utf-8') as f:
        ham_metin = f.read()

    # Sadece Regex ve yapılandırılmış veri çıkarma adımlarını çalıştır
    print("   🔍 Regex ile veri çıkarma...")
    regex_sonuclari = analiz_sistemi.regex_ile_veri_cikar(ham_metin)
    
    print("   🏗️ Yapılandırılmış veri çıkarma...")
    # Hızlı testte OCR verisi olmadığı için boş bir dict gönderiyoruz.
    # Bu, `yapilandirilmis_veri_cikar` fonksiyonunun bu duruma göre
    # ayarlanmasını gerektirebilir (örn. bloklara ayırmayı atlamak).
    # Şimdilik, sadece ham metne dayalı kısımlar çalışacaktır.
    # Daha gelişmiş bir versiyon için ocr_data'yı da JSON olarak saklayabiliriz.
    dummy_ocr_data = {'text': [], 'conf': [], 'left': [], 'top': [], 'width': [], 'height': []}
    structured_data = analiz_sistemi.yapilandirilmis_veri_cikar(dummy_ocr_data, ham_metin)

    print("\n📊 HIZLI TEST SONUÇLARI:")
    sonuclar = {"regex": regex_sonuclari, "structured": structured_data}
    analiz_sistemi.sonuclari_yazdir(sonuclar)


def ana_analiz_süreci():
    """
    Ana fatura analiz sürecini yönetir. Belirtilen klasördeki tüm faturaları
    işler ve sonuçları tek bir JSON raporunda birleştirir.
    """
    print("🚀 Akıllı Fatura Tanıma Uygulaması Başlatılıyor...")
    print("="*50)

    # Ayarları yükle
    ayarlar = ayarları_yukle()
    if not ayarlar:
        return

    # Rapor klasörünü oluştur ve bu koşu için zaman damgalı alt klasör aç
    rapor_klasoru = ayarlar['klasor_yollari']['rapor_klasoru']
    os.makedirs(rapor_klasoru, exist_ok=True)
    run_klasoru = os.path.join(rapor_klasoru, datetime.now().strftime('%Y%m%d_%H%M%S'))
    os.makedirs(run_klasoru, exist_ok=True)
    log_ayarlarini_yap(run_klasoru)

    # Paralel iş parçası sayısı (0 veya yoksa otomatik)
    parallel_workers = 0
    try:
        parallel_workers = int(ayarlar.get('parallel_workers', 0))
    except Exception:
        parallel_workers = 0

    # Fatura ve rapor klasör yolları (config'den)
    fatura_klasoru = ayarlar['klasor_yollari']['fatura_klasoru']
    
    if not os.path.exists(fatura_klasoru):
        hata_mesaji = f"Fatura klasörü bulunamadı: '{fatura_klasoru}'. Lütfen faturalarınızı bu klasöre koyun veya config.json dosyasını güncelleyin."
        print(f"❌ Hata: {hata_mesaji}")
        logging.error(hata_mesaji)
        return

    # Desteklenen resim ve PDF formatları (config'den)
    desteklenen_formatlar = ayarlar['desteklenen_formatlar']
    
    # --- TEK DOSYA TEST MODU DEVRE DIŞI BIRAKILDI ---
    # islenicek_faturalar = [os.path.join(fatura_klasoru, '3.png')]
    # --- TEK DOSYA TEST MODU SONU ---

    # İşlenecek faturaları bul (glob ile alt klasörler dahil) - (YENİDEN AKTİF EDİLDİ)
    print(f"📂 '{fatura_klasoru}' klasöründeki tüm faturalar aranıyor...")
    islenicek_faturalar = []
    for format in desteklenen_formatlar:
        # `**` operatörü, tüm alt dizinlerde aramayı sağlar (recursive=True)
        desen = os.path.join(fatura_klasoru, '**', f'*{format}')
        islenicek_faturalar.extend(glob.glob(desen, recursive=True))

    if not islenicek_faturalar:
        print(f"❌ '{fatura_klasoru}' klasöründe desteklenen formatta fatura bulunamadı.")
        return

    print(f"🎯 Toplam {len(islenicek_faturalar)} adet fatura analiz edilecek...")

    # Tüm sonuçları ve hatalı dosyaları topla (paralel/seri)
    tum_sonuclar = []
    hatali_dosyalar = []

    worker_count = parallel_workers if parallel_workers and parallel_workers > 0 else max(1, (os.cpu_count() or 2) - 1)
    if worker_count > 1:
        print(f"⚙️ Paralel analiz: {worker_count} işçi")
        with ProcessPoolExecutor(max_workers=worker_count) as ex:
            future_map = {ex.submit(analyze_file_for_pool, p, run_klasoru): p for p in islenicek_faturalar}
            for fut in as_completed(future_map):
                dosya_yolu = future_map[fut]
                try:
                    sonuclar = fut.result()
                except Exception as e:
                    hata_mesaji = f"{os.path.basename(dosya_yolu)} analiz edilemedi. Hata: {e}"
                    print(f"⚠️  Uyarı: {hata_mesaji}")
                    logging.error(hata_mesaji)
                    hatali_dosyalar.append(dosya_yolu)
                    continue
                if "hata" not in sonuclar:
                    tum_sonuclar.append(sonuclar)
                else:
                    hatali_dosyalar.append(dosya_yolu)
    else:
        # Seri analiz
        analiz_sistemi = FaturaRegexAnaliz()
        try:
            analiz_sistemi.output_dir = run_klasoru
        except Exception:
            pass
        for dosya_yolu in islenicek_faturalar:
            try:
                print(f"\n{'─'*20} Analiz ediliyor: {os.path.basename(dosya_yolu)} {'─'*20}")
                sonuclar = analiz_sistemi.fatura_analiz_et(dosya_yolu, gorsellestir=False)
                if "hata" not in sonuclar:
                    tum_sonuclar.append(sonuclar)
                else:
                    hatali_dosyalar.append(dosya_yolu)
            except Exception as e:
                hata_mesaji = f"{os.path.basename(dosya_yolu)} analiz edilirken beklenmedik bir hata oluştu: {e}"
                print(f"❌ Beklenmedik Hata: {hata_mesaji}")
                logging.exception(hata_mesaji)
                hatali_dosyalar.append(dosya_yolu)

    # Toplu raporu kaydet
    if tum_sonuclar:
        rapor_dosyasi = os.path.join(run_klasoru, f"toplu_fatura_raporu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(rapor_dosyasi, 'w', encoding='utf-8') as f:
            json.dump(tum_sonuclar, f, ensure_ascii=False, indent=4)
        
        # Sonuçları CSV olarak da kaydet (koşu klasörüne)
        sonuclari_csv_kaydet(run_klasoru, tum_sonuclar)

        print("\n" + "="*50)
        print("📊 ANALİZ TAMAMLANDI")
        
        basarili_sayisi = len(tum_sonuclar)
        hatali_sayisi = len(hatali_dosyalar)
        
        print(f"✅ Başarıyla analiz edilen fatura sayısı: {basarili_sayisi}")
        if hatali_sayisi > 0:
            print(f"❌ Hatalı veya işlenemeyen fatura sayısı: {hatali_sayisi}")
            print(f"📄 Detaylar için 'analiz_hatalari.log' dosyasına bakın.")
        
        # JSON raporunu yeni formatla kaydet
        formatli_json_raporu = [sonuclari_turkce_formatla(sonuc) for sonuc in tum_sonuclar]
        rapor_dosyasi_formatli = os.path.join(run_klasoru, f"toplu_fatura_raporu_formatli_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(rapor_dosyasi_formatli, 'w', encoding='utf-8') as f:
            json.dump(formatli_json_raporu, f, ensure_ascii=False, indent=4)

        print(f"📄 Detaylı (orijinal) JSON rapor dosyası oluşturuldu: {rapor_dosyasi}")
        print(f"📄 Formaplanmış Türkçe JSON rapor dosyası oluşturuldu: {rapor_dosyasi_formatli}")
        
        # 🧠 AKILLI TEST ANALİZİ BAŞLAT
        print("\n" + "="*50)
        print("🧠 AKILLI TEST ANALİZİ BAŞLATILIYOR...")
        print("="*50)
        
        akilli_analiz_sonucu = akilli_test_analizi_yap(tum_sonuclar, run_klasoru)
        akilli_analiz_html_kaydet(akilli_analiz_sonucu, run_klasoru)
        golden_degerlendirme_yap(run_klasoru, tum_sonuclar)

        print("="*50)

def akilli_test_analizi_yap(tum_sonuclar: list, rapor_klasoru: str):
    """
    🧠 Test sonuçlarını akıllıca analiz eder ve iyileştirme önerileri sunar
    """
    print("\n🧠 AKILLI TEST ANALİZİ BAŞLATILIYOR...")
    print("="*60)
    
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
    print("\n📊 AKILLI TEST ANALİZ RAPORU")
    print("="*60)
    
    print(f"📈 TOPLAM FATURA SAYISI: {analiz_verileri['toplam_fatura']}")
    print()
    
    print("🎯 ALAN BAŞARI ORANLARI:")
    for alan, oran in basari_oranlari.items():
        print(f"   {alan.replace('_', ' ').title()}: {oran}")
    print()
    
    print("🔍 HATA TÜRÜ ANALİZİ:")
    for hata_turu, sayi in analiz_verileri['hata_turleri'].items():
        if sayi > 0:
            print(f"   {hata_turu.replace('_', ' ').title()}: {sayi} fatura")
    print()
    
    print("💡 İYİLEŞTİRME ÖNERİLERİ:")
    for oneri in analiz_verileri['iyilestirme_onerileri']:
        print(f"   {oneri}")
    print()
    
    print("📊 OCR KALİTE DAĞILIMI:")
    for kalite, sayi in analiz_verileri['ocr_kalite_analizi'].items():
        yuzde = (sayi / analiz_verileri['toplam_fatura']) * 100
        print(f"   {kalite}: {sayi} fatura (%{yuzde:.1f})")
    
    print()
    print("🎯 PATTERN MATCHING BAŞARI ORANI:")
    if 'pattern_matching_basari' in analiz_verileri and analiz_verileri['pattern_matching_basari']:
        toplam_basari = sum(p['basari_orani'] for p in analiz_verileri['pattern_matching_basari'])
        ortalama_basari = toplam_basari / len(analiz_verileri['pattern_matching_basari'])
        print(f"   Ortalama Pattern Matching Başarı Oranı: %{ortalama_basari:.1f}")
        
        # En başarılı ve en başarısız faturalar
        basarili_faturalar = [p for p in analiz_verileri['pattern_matching_basari'] if p['basari_orani'] >= 80]
        basarisiz_faturalar = [p for p in analiz_verileri['pattern_matching_basari'] if p['basari_orani'] < 50]
        
        print(f"   Yüksek Başarılı (≥80%): {len(basarili_faturalar)} fatura")
        print(f"   Düşük Başarılı (<50%): {len(basarisiz_faturalar)} fatura")
        
        if basarisiz_faturalar:
            print("   En Düşük Başarılı Faturalar:")
            for fatura in sorted(basarisiz_faturalar, key=lambda x: x['basari_orani'])[:3]:
                dosya_adi = os.path.basename(fatura['dosya'])
                print(f"     {dosya_adi}: %{fatura['basari_orani']:.1f}")

def akilli_analiz_raporu_kaydet(analiz_verileri: dict, rapor_klasoru: str):
    """
    💾 Akıllı analiz raporunu dosyaya kaydeder
    """
    rapor_dosyasi = os.path.join(rapor_klasoru, f"akilli_analiz_raporu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    with open(rapor_dosyasi, 'w', encoding='utf-8') as f:
        json.dump(analiz_verileri, f, ensure_ascii=False, indent=4)
    
    print(f"💾 Akıllı analiz raporu kaydedildi: {rapor_dosyasi}")

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

    print(f"📄 HTML özet oluşturuldu: {html_yolu}")

def _norm_amount(s: str) -> str:
    if not s:
        return ''
    t = str(s).upper().replace('TL','').replace('TRY','').replace('₺','').strip()
    import re
    t = re.sub(r'[^0-9.,]', '', t)
    t = t.replace('.', '').replace(',', '.')
    try:
        val = float(t)
        return f"{val:.2f}"
    except Exception:
        return ''

def _norm_date(s: str) -> str:
    if not s:
        return ''
    import re
    t = re.sub(r'[^0-9./\-]', '', str(s))
    t = re.sub(r"\s*[/\-.]\s*", '-', t)
    return t

def golden_degerlendirme_yap(run_klasoru: str, tum_sonuclar: list):
    """golden/golden.json dosyası varsa, çıkardığımız alanları beklenenlerle karşılaştırır."""
    import os, json, csv
    golden_path = os.path.join('golden', 'golden.json')
    if not os.path.exists(golden_path):
        print("ℹ️ Golden set bulunamadı (golden/golden.json). Değerlendirme atlandı.")
        return
    try:
        golden = json.load(open(golden_path, encoding='utf-8'))
    except Exception as e:
        print(f"❌ Golden set yüklenemedi: {e}")
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
    print('📐 Golden değerlendirme (alan başarı oranları):')
    for f in fields:
        tot = field_total.get(f,0) or 0
        hit = field_hits.get(f,0)
        oran = (hit/tot*100) if tot else 0.0
        print(f"  - {f}: {hit}/{tot} (%{oran:.1f})")
    print(f"📄 Golden raporları: {out_json}, {out_csv}")

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
    # --- KULLANIM MODLARI ---
    # 1. Normal Analiz (Tüm faturaları işler)
    ana_analiz_süreci()

    # 2. Ham Metin Dışa Aktarma (Sadece bir fatura için OCR metnini .txt olarak kaydeder)
    # Yorum satırını kaldırıp, dosya yolunu güncelleyerek kullanabilirsiniz.
    # sistem = FaturaRegexAnaliz()
    # ocr_metnini_disa_aktar(sistem, r"fatura/5c565ea6-b2f6-4e4a-b004-75cface23500.pdf", "test_reports")

    # 3. Hızlı Test (Kaydedilmiş .txt üzerinden sadece veri çıkarma testi yapar)
    # Yorum satırını kaldırıp, .txt dosyasının yolunu vererek kullanabilirsiniz.
    # sistem = FaturaRegexAnaliz()
    # hizli_test_calistir(sistem, r"test_reports/hizli_test_5c565ea6-b2f6-4e4a-b004-75cface23500.txt")
