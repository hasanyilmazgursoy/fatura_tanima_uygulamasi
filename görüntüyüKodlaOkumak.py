#1.gün
import cv2

# Görüntüyü yükle
img = cv2.imread(r"C:\Users\hasan\OneDrive\Desktop\tesst\1.png")

if img is None:
    print("Görüntü yüklenemedi, dosya yolunu kontrol et.")
    exit()

# Gri tonlamaya çevir
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Gürültüyü azaltmak için median blur uygula
clean = cv2.medianBlur(gray, 3)

# İşlenmiş görüntüyü göster
cv2.imshow("Temizlenmiş Fatura", clean)

# Bir tuşa basılınca pencere kapanacak
cv2.waitKey(0)
cv2.destroyAllWindows()
