import os
import json
import csv
import logging
import glob
from datetime import datetime
from fatura_regex_analiz_yeni import FaturaRegexAnaliz
from typing import Dict

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

    # Rapor klasörünü oluştur ve loglamayı ayarla
    rapor_klasoru = ayarlar['klasor_yollari']['rapor_klasoru']
    os.makedirs(rapor_klasoru, exist_ok=True)
    log_ayarlarini_yap(rapor_klasoru)

    # Sistem başlat
    analiz_sistemi = FaturaRegexAnaliz()

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

    # Tüm sonuçları ve hatalı dosyaları topla
    tum_sonuclar = []
    hatali_dosyalar = []
    for dosya_yolu in islenicek_faturalar:
        try:
            print(f"\n{'─'*20} Analiz ediliyor: {os.path.basename(dosya_yolu)} {'─'*20}")
            
            # Görselleştirmeyi KAPATARAK toplu analiz yap
            sonuclar = analiz_sistemi.fatura_analiz_et(dosya_yolu, gorsellestir=False)
            
            # Sonuçları ekle ve kritik alanları kontrol et
            if "hata" not in sonuclar:
                tum_sonuclar.append(sonuclar)
                analiz_sistemi.sonuclari_yazdir(sonuclar)
                
                # Başarısızlık analizi için loglama
                structured_data = sonuclar.get('structured', {})
                kritik_alanlar = ['fatura_numarasi', 'fatura_tarihi', 'genel_toplam']
                eksik_alanlar = [alan for alan in kritik_alanlar if not structured_data.get(alan)]
                
                if eksik_alanlar:
                    basarisizlik_log_yolu = os.path.join(rapor_klasoru, "basarisiz_faturalar.log")
                    with open(basarisizlik_log_yolu, 'a', encoding='utf-8') as log_f:
                        log_f.write(f"--- BASARISIZ VAKA: {os.path.basename(dosya_yolu)} ---\n")
                        log_f.write(f"Eksik Kritik Alanlar: {', '.join(eksik_alanlar)}\n")
                        # OCR'dan çıkan ham metni de log'a ekleyelim
                        ham_metin = sonuclar.get('ocr_istatistikleri', {}).get('ham_metin', 'METIN_CIKARILAMADI')
                        log_f.write(f"Ham Metin: {ham_metin}\n\n") # Metnin bir kısmını al
            else:
                hata_mesaji = f"{os.path.basename(dosya_yolu)} analiz edilemedi. Hata: {sonuclar['hata']}"
                print(f"⚠️  Uyarı: {hata_mesaji}")
                logging.error(hata_mesaji)
                hatali_dosyalar.append(dosya_yolu)

        except Exception as e:
            hata_mesaji = f"{os.path.basename(dosya_yolu)} analiz edilirken beklenmedik bir hata oluştu: {e}"
            print(f"❌ Beklenmedik Hata: {hata_mesaji}")
            logging.exception(hata_mesaji) # `exception` metodu, traceback'i de loglar
            hatali_dosyalar.append(dosya_yolu)

    # Toplu raporu kaydet
    if tum_sonuclar:
        rapor_dosyasi = os.path.join(rapor_klasoru, f"toplu_fatura_raporu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(rapor_dosyasi, 'w', encoding='utf-8') as f:
            json.dump(tum_sonuclar, f, ensure_ascii=False, indent=4)
        
        # Sonuçları CSV olarak da kaydet
        sonuclari_csv_kaydet(rapor_klasoru, tum_sonuclar)

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
        rapor_dosyasi_formatli = os.path.join(rapor_klasoru, f"toplu_fatura_raporu_formatli_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(rapor_dosyasi_formatli, 'w', encoding='utf-8') as f:
            json.dump(formatli_json_raporu, f, ensure_ascii=False, indent=4)

        print(f"📄 Detaylı (orijinal) JSON rapor dosyası oluşturuldu: {rapor_dosyasi}")
        print(f"📄 Formaplanmış Türkçe JSON rapor dosyası oluşturuldu: {rapor_dosyasi_formatli}")
        print("="*50)

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
