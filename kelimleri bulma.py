import cv2
import numpy as np
import pytesseract
from pytesseract import Output
import re

# --- KULLANICI AYARLARI ---
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
image_path = r"C:\Users\hasan\OneDrive\Desktop\1.png"

# --- GÖRÜNTÜ ÖN İŞLEME ---
img = cv2.imread(image_path)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 15)
kernel = np.ones((2,2), np.uint8)
processed_img = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

# --- VERİYİ OKUMA ---
print("Tesseract ile metin ve koordinat verileri okunuyor...")
data = pytesseract.image_to_data(processed_img, lang='tur', output_type=Output.DICT)

# ==============================================================================
# HATA AYIKLAMA (DEBUG) BÖLÜMÜ
# Bu bölüm, Tesseract'in tanıdığı tüm kelimeleri ve bilgilerini yazdırır.
# ==============================================================================
print("\n--- HATA AYIKLAMA MODU AKTİF ---")
print("Tesseract tarafından tanınan tüm kelimeler listeleniyor:")
print("Index | Güven | Dikey Konum (Top) | Metin")
print("---------------------------------------------")
n_boxes = len(data['text'])
for i in range(n_boxes):
    # Boş metinleri atla
    if data['text'][i].strip() != '':
        conf = data['conf'][i]
        top = data['top'][i]
        text = data['text'][i]
        print(f"{i: <5} | {conf: >5}% | {top: >17} | {text}")

print("--- HATA AYIKLAMA MODU SONU ---\n")
# ==============================================================================


# --- METİN ANALİZİ (ÖNCEKİ KODLA AYNI) ---
anahtar_kelime = "ödenecek"
bulunan_tutar = None

for i in range(n_boxes):
    if int(data['conf'][i]) > 50:
        if anahtar_kelime in data['text'][i].lower():
            anahtar_kelime_top = data['top'][i]
            for j in range(n_boxes):
                if int(data['conf'][j]) > 50:
                    is_on_same_line = abs(data['top'][j] - anahtar_kelime_top) < 15
                    if is_on_same_line:
                        potential_text = data['text'][j]
                        if re.match(r'^[\d.,]+$', potential_text) and ',' in potential_text:
                            bulunan_tutar = potential_text
                            break
            if bulunan_tutar:
                break

# --- SONUÇ ---
print("-" * 30)
if bulunan_tutar:
    print(f"✅ Başarılı: Tespit Edilen Ödenecek Tutar: {bulunan_tutar}")
else:
    print("❌ Başarısız: Faturada 'Ödenecek Tutar' bulunamadı veya okunamadı.")
print("-" * 30)