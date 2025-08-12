#5.gün

# 5.gün: Kod Toparlama ve Fonksiyonlara Ayırma

import cv2
import pytesseract
from pytesseract import Output
import re

# --- Tesseract Kurulumu ---
# Tesseract'ın bilgisayarınızdaki konumunu belirtin.
# Bu satırı kendi sisteminize göre düzenlemeniz gerekebilir.
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# --- FONKSİYON 1: Görüntü İşleme ---
def goruntuyu_isle(dosya_yolu):
    """
    Verilen yoldaki görüntüyü okur ve ön işleme tabi tutar.

    Args:
        dosya_yolu (str): İşlenecek görüntünün dosya yolu.

    Returns:
        tuple: (orijinal_renkli_goruntu, gri_tonlamali_goruntu)
               Eğer dosya okunamzsa (None, None) döner.
    """
    # Görseli diskten oku
    img = cv2.imread(dosya_yolu)
    if img is None:
        # Görsel okunamadıysa hata yönetimi için None döndür
        return None, None

    # OCR performansını artırmak için görüntüyü gri tonlamaya çevir
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Orijinal ve gri tonlamalı görüntüyü geri döndür
    return img, gray_img

# --- FONKSİYON 2: Veri Çıkarma ve Görselleştirme ---
def tutari_bul_ve_gorsellestir(renkli_goruntu, gri_goruntu):
    """
    Gri tonlamalı görüntü üzerinde OCR uygular, "ödenecek tutar"ı arar
    ve sonucu renkli görüntü üzerinde görselleştirir.

    Args:
        renkli_goruntu: Sonuçların üzerine çizileceği orijinal renkli görüntü.
        gri_goruntu: OCR işleminin yapılacağı gri tonlamalı görüntü.

    Returns:
        tuple: (bulunan_tutar, sonuc_goruntusu)
               'bulunan_tutar' string veya None olabilir.
               'sonuc_goruntusu' kutuların çizildiği renkli görüntüdür.
    """
    # Aranacak anahtar kelimeler listesi (küçük harfle)
    anahtar_kelimeler = ["ödenecek", "toplam", "tutar", "genel toplam", "ödenecek tutar", "vergiler dahil"]
    bulunan_tutar = None # Henüz bir tutar bulunmadı

    # OCR için yapılandırma parametreleri
    # psm 6: Görüntüyü tek tip bir metin bloğu olarak kabul et
    config_params = r'--psm 6'
    # Tesseract'ı kullanarak görüntüden metin verilerini çıkar (detaylı olarak)
    data = pytesseract.image_to_data(gri_goruntu, lang='tur', config=config_params, output_type=Output.DICT)

    n_boxes = len(data['text'])
    # --- Anahtar kelime ve tutar arama döngüsü ---
    for i in range(n_boxes):
        # Eğer kelimenin güven skoru (confidence) %40'tan yüksekse işleme al
        if int(data['conf'][i]) > 40:
            # Okunan metni küçük harfe çevirerek karşılaştırmayı kolaylaştır
            aranan_metin = data['text'][i].lower()

            # Metin, anahtar kelimelerimizden birini içeriyor mu?
            if any(kelime in aranan_metin for kelime in anahtar_kelimeler):
                print(f"✅ Anahtar kelime bulundu: '{data['text'][i]}'")
                # Anahtar kelimenin koordinatlarını al
                (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
                # Anahtar kelimeyi yeşil bir kutu içine al
                cv2.rectangle(renkli_goruntu, (x, y), (x + w, y + h), (0, 255, 0), 2)

                # --- Potansiyel tutarı aynı satırda ara ---
                # Anahtar kelimeden sonraki kelimeleri kontrol et
                for j in range(i + 1, n_boxes):
                    # İki kelimenin dikeyde aynı hizada olup olmadığını kontrol et (20 piksel tolerans)
                    is_on_same_line = abs(data['top'][j] - y) < 20
                    # İkinci kelimenin, anahtar kelimenin sağında olup olmadığını kontrol et
                    is_to_the_right = data['left'][j] > x

                    if is_on_same_line and is_to_the_right:
                        potential_text = data['text'][j]
                        # Metin içindeki rakam, virgül ve nokta dışındaki her şeyi temizle
                        cleaned_text = re.sub(r'[^\d,.]', '', potential_text)

                        # Temizlenmiş metin içinde hem rakam hem de (virgül veya nokta) var mı?
                        # Bu, "1.234,56" veya "12.50" gibi formatları yakalamak için
                        if re.search(r'[\d]', cleaned_text) and re.search(r'[,.]', cleaned_text):
                            print(f"-> Potansiyel tutar bulundu: '{cleaned_text}'")
                            bulunan_tutar = cleaned_text

                            # Tutarın koordinatlarını al ve yeşil kutu içine al
                            (tx, ty, tw, th) = (data['left'][j], data['top'][j], data['width'][j], data['height'][j])
                            cv2.rectangle(renkli_goruntu, (tx, ty), (tx + tw, ty + th), (0, 255, 0), 2)
                            break # Tutar bulundu, iç döngüden çık

                if bulunan_tutar:
                    break # Tutar bulundu, ana döngüden de çık

    return bulunan_tutar, renkli_goruntu


# --- ANA PROGRAM AKIŞI ---
if __name__ == "__main__":
    # İşlenecek faturanın dosya yolu
    image_path = r"C:\Users\hasan\OneDrive\Desktop\5.png"

    try:
        print(f"'{image_path}' için OCR işlemi başlatılıyor...\n")
        # Adım 1: Görüntüyü oku ve ön işle
        renkli_img, gri_img = goruntuyu_isle(image_path)

        # Görüntünün başarıyla okunup okunmadığını kontrol et
        if renkli_img is None:
            raise FileNotFoundError(f"Hata: '{image_path}' dosyası bulunamadı veya okunamadı.")

        # Adım 2: Tutarı bul ve sonucu görselleştir
        tutar, sonuc_img = tutari_bul_ve_gorsellestir(renkli_img, gri_img)

        # Adım 3: Sonucu ekrana yazdır
        print("\n" + "-" * 30)
        if tutar:
            print(f"✅ Başarılı: Tespit Edilen Ödenecek Tutar: {tutar}")
        else:
            print("❌ Başarısız: Bu faturada tutar bulunamadı.")
        print("-" * 30)

        # Adım 4: Sonuç görüntüsünü ekranda göster
        cv2.imshow("Fatura OCR Sonucu", sonuc_img)
        cv2.waitKey(0) # Bir tuşa basılana kadar bekle
        cv2.destroyAllWindows() # Tüm pencereleri kapat

    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        # Beklenmedik diğer tüm hataları yakala
        print(f"Beklenmedik bir hata oluştu: {e}")