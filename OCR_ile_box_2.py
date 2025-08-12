import cv2
import pytesseract
from pytesseract import Output
import re

# --- Tesseract ayarı ---
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# --- Görsel yolu ---
image_path = r"C:\Users\hasan\OneDrive\Desktop\5.png"

try:
    # Görseli oku
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Hata: '{image_path}' dosyası okunamadı.")

    # Gri tonlama
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    print(f"'{image_path}' için OCR işlemi başlatılıyor...\n")

    # OCR parametreleri
    config_params = r'--psm 6'
    data = pytesseract.image_to_data(gray_img, lang='tur', config=config_params, output_type=Output.DICT)

    # Anahtar kelimeler
    anahtar_kelimeler = ["ödenecek", "toplam", "tutar", "genel toplam", "ödenecek tutar", "vergiler dahil"]
    bulunan_tutar = None
    n_boxes = len(data['text'])

    # --- Kelimeleri çiz ---
    for i in range(n_boxes):
        if int(data['conf'][i]) >= 50:
            (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)  # kırmızı kutu

    # --- Anahtar kelime arama ---
    for i in range(n_boxes):
        if int(data['conf'][i]) > 40:
            aranan_metin = data['text'][i].lower()

            if any(kelime in aranan_metin for kelime in anahtar_kelimeler):
                print(f"✅ Anahtar kelime bulundu: '{data['text'][i]}'")
                (x, y, w, h) = (data['left'][i], data['top'][i], data['width'][i], data['height'][i])
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)  # yeşil kutu (anahtar kelime)

                # Aynı satırda sağdaki değeri ara
                for j in range(i + 1, n_boxes):
                    is_on_same_line = abs(data['top'][j] - y) < 20
                    is_to_the_right = data['left'][j] > x

                    if is_on_same_line and is_to_the_right:
                        potential_text = data['text'][j]
                        cleaned_text = re.sub(r'[^\d,.]', '', potential_text)

                        if re.search(r'[\d]', cleaned_text) and re.search(r'[,.]', cleaned_text):
                            print(f"-> Potansiyel tutar bulundu: '{cleaned_text}'")
                            bulunan_tutar = cleaned_text

                            # Tutar kutusunu yeşil yap
                            (tx, ty, tw, th) = (data['left'][j], data['top'][j], data['width'][j], data['height'][j])
                            cv2.rectangle(img, (tx, ty), (tx + tw, ty + th), (0, 255, 0), 2)
                            break
                if bulunan_tutar:
                    break

    print("\n" + "-" * 30)
    if bulunan_tutar:
        print(f"✅ Başarılı: Tespit Edilen Ödenecek Tutar: {bulunan_tutar}")
    else:
        print("❌ Başarısız: Bu faturada tutar bulunamadı.")
    print("-" * 30)

    # --- Görseli göster ---
    cv2.imshow("Fatura OCR Sonucu", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

except FileNotFoundError as e:
    print(e)
except Exception as e:
    print(f"Beklenmedik bir hata oluştu: {e}")
