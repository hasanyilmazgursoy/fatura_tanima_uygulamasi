import json
import os
from fatura_analiz_motoru import FaturaAnalizMotoru
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
import pandas as pd
from collections import defaultdict
from utils import norm_amount, norm_date
import logging

def degerlendir(analiz_sonuclari: dict, dogruluk_verisi: dict) -> dict:
    """
    Tek bir faturanın analiz sonucunu doğruluk verisiyle karşılaştırır.
    """
    rapor = {"dogru": 0, "yanlis": 0, "eksik": 0, "detaylar": {}}
    
    for anahtar, beklenen_deger in dogruluk_verisi.items():
        bulunan_deger_raw = analiz_sonuclari.get(anahtar)
        
        # Gelen değeri her zaman string'e çevirerek karşılaştırma yap
        bulunan_deger = str(bulunan_deger_raw).strip() if bulunan_deger_raw is not None else None
        beklenen_deger_str = str(beklenen_deger).strip()

        # Ortak normalizasyon: miktar ve tarih alanlarını normalize et
        if bulunan_deger and 'tarih' in anahtar:
            bulunan_deger = norm_date(bulunan_deger)
            beklenen_deger_str = norm_date(beklenen_deger_str)
        elif bulunan_deger and ('tutar' in anahtar or 'toplam' in anahtar or 'kdv' in anahtar):
            bulunan_deger = norm_amount(bulunan_deger)
            beklenen_deger_str = norm_amount(beklenen_deger_str)

        if bulunan_deger is not None and bulunan_deger != "":
            # Karşılaştırma yaparken küçük farklılıkları tolere et (örn: boşluk, büyük/küçük harf, .00 vs)
            if str(bulunan_deger).lower() == str(beklenen_deger_str).lower():
                rapor["dogru"] += 1
                rapor["detaylar"][anahtar] = {"durum": "Doğru", "beklenen": beklenen_deger_str, "bulunan": bulunan_deger_raw}
            else:
                rapor["yanlis"] += 1
                rapor["detaylar"][anahtar] = {"durum": "Yanlış", "beklenen": beklenen_deger_str, "bulunan": bulunan_deger_raw}
        else:
            rapor["eksik"] += 1
            rapor["detaylar"][anahtar] = {"durum": "Eksik", "beklenen": beklenen_deger_str, "bulunan": None}
            
    return rapor

def tek_faturayi_analiz_et(dosya_yolu: str) -> tuple[str, dict]:
    """Bir fatura dosyasını analiz etmek için sarmalayıcı fonksiyon."""
    # Hataları gizlemek için log seviyesini ayarla
    logging.basicConfig(level=logging.CRITICAL)
    analiz_sistemi = FaturaAnalizMotoru()
    sonuc = analiz_sistemi.analiz_et(dosya_yolu)
    return os.path.basename(dosya_yolu), sonuc

def main():
    """
    Ana değerlendirme betiği. Tüm faturaları analiz eder, golden dataset ile karşılaştırır
    ve detaylı bir başarı raporu oluşturur.
    """
    logging.info("🚀 Değerlendirme süreci başlatılıyor...")

    # Golden dataset'i yükle
    try:
        with open('config/golden_dataset.json', 'r', encoding='utf-8') as f:
            golden_dataset = json.load(f)
        logging.info(f"✅ Golden dataset başarıyla yüklendi. {len(golden_dataset)} adet fatura referansı bulundu.")
    except FileNotFoundError:
        logging.error("❌ Hata: 'config/golden_dataset.json' dosyası bulunamadı.")
        return

    # İşlenecek faturaları belirle
    fatura_klasoru = "27.08.2025_Gelen Fatura (1)"
    islenicek_dosyalar = [os.path.join(fatura_klasoru, dosya_adi) for dosya_adi in golden_dataset.keys() if os.path.exists(os.path.join(fatura_klasoru, dosya_adi))]
    
    if not islenicek_dosyalar:
        logging.error(f"❌ '{fatura_klasoru}' içinde değerlendirilecek fatura bulunamadı.")
        return

    logging.info(f"🔍 {len(islenicek_dosyalar)} adet fatura analiz edilecek...")

    # Paralel analiz
    tum_sonuclar = {}
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(tek_faturayi_analiz_et, dosya): dosya for dosya in islenicek_dosyalar}
        for future in tqdm(as_completed(futures), total=len(islenicek_dosyalar), desc="Faturalar Analiz Ediliyor"):
            try:
                dosya_adi, sonuc = future.result()
                tum_sonuclar[dosya_adi] = sonuc['yapilandirilmis_veri']
            except Exception as e:
                dosya = futures[future]
                logging.error(f"❌ {os.path.basename(dosya)} analiz edilirken hata oluştu: {e}")


    logging.info("📊 Değerlendirme sonuçları hesaplanıyor...")
    
    # Değerlendirme
    toplam_rapor = {"dogru": 0, "yanlis": 0, "eksik": 0, "alan_bazli": defaultdict(lambda: {"dogru": 0, "yanlis": 0, "eksik": 0})}
    detayli_sonuclar = {}

    for dosya_adi, analiz_sonucu in tum_sonuclar.items():
        if dosya_adi in golden_dataset:
            dogruluk_verisi = golden_dataset[dosya_adi]
            rapor = degerlendir(analiz_sonucu, dogruluk_verisi)
            detayli_sonuclar[dosya_adi] = rapor['detaylar']
            
            toplam_rapor["dogru"] += rapor["dogru"]
            toplam_rapor["yanlis"] += rapor["yanlis"]
            toplam_rapor["eksik"] += rapor["eksik"]

            for alan, detay in rapor['detaylar'].items():
                if detay['durum'] == 'Doğru':
                    toplam_rapor["alan_bazli"][alan]["dogru"] += 1
                elif detay['durum'] == 'Yanlış':
                    toplam_rapor["alan_bazli"][alan]["yanlis"] += 1
                elif detay['durum'] == 'Eksik':
                    toplam_rapor["alan_bazli"][alan]["eksik"] += 1

    # Raporu yazdır
    logging.info("Değerlendirme Raporu")
    
    toplam_alan = toplam_rapor["dogru"] + toplam_rapor["yanlis"] + toplam_rapor["eksik"]
    basari_orani = (toplam_rapor["dogru"] / toplam_alan) * 100 if toplam_alan > 0 else 0
    
    logging.info(f"Genel Başarı Oranı: {basari_orani:.2f}%")
    logging.info(f"  - Doğru: {toplam_rapor['dogru']}")
    logging.info(f"  - Yanlış: {toplam_rapor['yanlis']}")
    logging.info(f"  - Eksik: {toplam_rapor['eksik']}")
    
    logging.info("Alan Bazlı Başarı Oranları:")
    
    alan_raporlari = []
    # Alanları başarı oranına göre sırala
    sorted_alanlar = sorted(toplam_rapor["alan_bazli"].items(), 
                            key=lambda item: (item[1]["dogru"] / (item[1]["dogru"] + item[1]["yanlis"] + item[1]["eksik"])) if (item[1]["dogru"] + item[1]["yanlis"] + item[1]["eksik"]) > 0 else 0, 
                            reverse=True)

    for alan, skorlar in sorted_alanlar:
        toplam = skorlar["dogru"] + skorlar["yanlis"] + skorlar["eksik"]
        oran = (skorlar["dogru"] / toplam) * 100 if toplam > 0 else 0
        alan_raporlari.append({
            "Alan": alan,
            "Başarı Oranı (%)": f"{oran:.2f}",
            "Doğru": skorlar["dogru"],
            "Yanlış": skorlar["yanlis"],
            "Eksik": skorlar["eksik"],
            "Toplam": toplam
        })
        
    df = pd.DataFrame(alan_raporlari)
    logging.info("\n" + df.to_string(index=False))

    # Sonuçları dosyaya kaydet
    os.makedirs('test_reports', exist_ok=True)
    rapor_dosyasi = os.path.join('test_reports', 'degerlendirme_raporu.json')
    with open(rapor_dosyasi, 'w', encoding='utf-8') as f:
        json.dump({
            "genel_rapor": {
                "basari_orani": basari_orani,
                "dogru": toplam_rapor["dogru"],
                "yanlis": toplam_rapor["yanlis"],
                "eksik": toplam_rapor["eksik"]
            },
            "alan_bazli_rapor": df.to_dict('records'),
            "detayli_sonuclar": detayli_sonuclar
        }, f, ensure_ascii=False, indent=4)
        
    logging.info(f"💾 Detaylı rapor '{rapor_dosyasi}' dosyasına kaydedildi.")
    logging.info("✅ Değerlendirme tamamlandı.")

if __name__ == "__main__":
    # Windows'ta paralel işlem için gerekli
    import multiprocessing
    multiprocessing.freeze_support()
    main()
