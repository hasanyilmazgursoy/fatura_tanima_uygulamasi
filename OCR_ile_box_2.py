import cv2
import pytesseract
from pytesseract import Output
import re

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
image_path = r"C:\Users\hasan\OneDrive\Desktop\5.png"  # Test edeceğiniz faturanın adını buraya yazın

try:
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Hata: '{image_path}' dosyası okunamadı.")

    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    print(f"'{image_path}' için işlem başlatılıyor...")

    config_params = r'--psm 6'
    data = pytesseract.image_to_data(gray_img, lang='tur', config=config_params, output_type=Output.DICT)

    # --- İYİLEŞTİRME: Birden fazla anahtar kelime kullanıyoruz ---
    anahtar_kelimeler = ["ödenecek", "toplam", "tutar", "genel toplam", "ödenecek tutar", "vergiler dahil"]
    bulunan_tutar = None

    n_boxes = len(data['text'])
    for i in range(n_boxes):
        if int(data['conf'][i]) > 40:

            aranan_metin = data['text'][i].lower()
            # Herhangi bir anahtar kelime eşleşiyor mu?
            if any(kelime in aranan_metin for kelime in anahtar_kelimeler):
                print(f"✅ Anahtar kelime bulundu: '{data['text'][i]}'")
                (x, y) = (data['left'][i], data['top'][i])

                for j in range(i + 1, n_boxes):
                    is_on_same_line = abs(data['top'][j] - y) < 20
                    is_to_the_right = data['left'][j] > x

                    if is_on_same_line and is_to_the_right:
                        potential_text = data['text'][j]

                        # --- İYİLEŞTİRME: Para birimi gibi ekleri temizliyoruz ---
                        cleaned_text = re.sub(r'[^\d,.]', '', potential_text)

                        # En az bir virgül veya nokta ve en az bir rakam içermeli
                        if re.search(r'[\d]', cleaned_text) and re.search(r'[,.]', cleaned_text):
                            print(f"-> Potansiyel tutar bulundu ve temizlendi: '{cleaned_text}'")
                            bulunan_tutar = cleaned_text
                            break
                if bulunan_tutar:
                    break

    print("-" * 30)
    if bulunan_tutar:
        print(f"✅ Başarılı: Tespit Edilen Ödenecek Tutar: {bulunan_tutar}")
    else:
        print("❌ Başarısız: Bu faturada tutar bulunamadı.")
    print("-" * 30)

except FileNotFoundError as e:
    print(e)
except Exception as e:
    print(f"Beklenmedik bir hata oluştu: {e}")