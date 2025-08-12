#2.gün
import cv2
import pytesseract
import numpy as np

# Tesseract programının yüklü olduğu yol
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Görüntüyü yükle
img = cv2.imread(r"C:\Users\hasan\OneDrive\Desktop\denemeddd.png")
if img is None:
    print("Görüntü yüklenemedi, dosya yolunu kontrol et.")
    exit()

# Gri tonlama
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Gaussian Blur ile gürültü azaltma
blur = cv2.GaussianBlur(gray, (5,5), 0)

# Adaptif eşikleme ile siyah-beyaz yapma
thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY, 11, 2)

# Median blur ile ekstra parazit azaltma
clean = cv2.medianBlur(thresh, 3)

# İşlenmiş görüntüyü göster (isteğe bağlı)
cv2.imshow("OCR için Hazır Görüntü", clean)
cv2.waitKey(0)
cv2.destroyAllWindows()

# OCR ile metni çıkar, --psm 6 = Tek blok metin
text = pytesseract.image_to_string(clean, lang='tur', config='--psm 6')

print("---- OCR Sonucu ----")
print(text)
