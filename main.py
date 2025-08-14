import os
import json
import csv
import logging
import glob
from datetime import datetime
from fatura_regex_analiz_yeni import FaturaRegexAnaliz

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
    
    # Sadece yapılandırılmış verileri al
    yazilacak_veriler = [sonuc.get('structured', {}) for sonuc in tum_sonuclar]
    
    # CSV başlıklarını (sütun isimlerini) dinamik olarak belirle
    # Tüm faturalardaki bütün olası alanları topla
    basliklar = set()
    for veri in yazilacak_veriler:
        basliklar.update(veri.keys())
    
    # Başlık sırasını belirle (isteğe bağlı olarak sıralanabilir)
    sirali_basliklar = sorted(list(basliklar))

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
    
    # --- GEÇİCİ TEST KODU ---
    # Sadece belirli bir faturayı test etmek için aşağıdaki satırı etkinleştirin.
    islenicek_faturalar = [os.path.join(fatura_klasoru, 'test', '5c565ea6-b2f6-4e4a-b004-75cface23500.pdf')]
    # --- GEÇİCİ TEST KODU SONU ---

    # İşlenecek faturaları bul (glob ile alt klasörler dahil) - GEÇİCİ OLARAK DEVRE DIŞI
    # print(f"📂 '{fatura_klasoru}' klasöründeki faturalar aranıyor...")
    # islenicek_faturalar = []
    # for format in desteklenen_formatlar:
    #     # `**` operatörü, tüm alt dizinlerde aramayı sağlar (recursive=True)
    #     desen = os.path.join(fatura_klasoru, '**', f'*{format}')
    #     islenicek_faturalar.extend(glob.glob(desen, recursive=True))

    if not islenicek_faturalar or not os.path.exists(islenicek_faturalar[0]):
        print(f"❌ Test edilecek fatura bulunamadı veya yolu yanlış: {islenicek_faturalar}")
        return

    print(f"🎯 Sadece 1 adet test faturası analiz edilecek...")

    # Tüm sonuçları ve hatalı dosyaları topla
    tum_sonuclar = []
    hatali_dosyalar = []
    for dosya_yolu in islenicek_faturalar:
        try:
            print(f"\n{'─'*20} Analiz ediliyor: {os.path.basename(dosya_yolu)} {'─'*20}")
            
            # Gorsellestirmeyi kapatarak analiz et
            sonuclar = analiz_sistemi.fatura_analiz_et(dosya_yolu, gorsellestir=False)
            
            # Sonuçları ekle
            if "hata" not in sonuclar:
                tum_sonuclar.append(sonuclar)
                analiz_sistemi.sonuclari_yazdir(sonuclar)
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
        
        print(f"📄 Detaylı JSON rapor dosyası oluşturuldu: {rapor_dosyasi}")
        print("="*50)

if __name__ == "__main__":
    ana_analiz_süreci()
