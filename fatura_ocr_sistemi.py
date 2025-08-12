# 5. GÜN: Haftalık Değerlendirme ve Kod Toparlama
# Akıllı Fatura Tanıma Uygulaması - Ana Sistem
# 
# Bu dosya, hafta boyunca geliştirilen tüm OCR özelliklerini
# temiz ve anlaşılır fonksiyonlar halinde birleştirir.

import cv2
import numpy as np
import pytesseract
from pytesseract import Output
import re
import os
from typing import Dict, List, Tuple, Optional

class FaturaOCR:
    """
    Fatura OCR işlemlerini yöneten ana sınıf.
    Bu sınıf, hafta boyunca geliştirilen tüm özellikleri içerir.
    """
    
    def __init__(self, tesseract_path: str = None):
        """
        FaturaOCR sınıfını başlatır.
        
        Args:
            tesseract_path (str): Tesseract programının yolu. 
                                None ise varsayılan yol kullanılır.
        """
        # Tesseract yolunu ayarla
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        else:
            # Varsayılan Windows yolu
            default_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            if os.path.exists(default_path):
                pytesseract.pytesseract.tesseract_cmd = default_path
            else:
                print("⚠️  Uyarı: Tesseract yolu bulunamadı. Lütfen manuel olarak ayarlayın.")
        
        # Anahtar kelimeler - faturada aranacak önemli terimler
        self.anahtar_kelimeler = [
            "ödenecek", "toplam", "tutar", "genel toplam", 
            "ödenecek tutar", "vergiler dahil", "net tutar"
        ]
        
        # OCR ayarları
        self.ocr_config = '--psm 6'  # Tek blok metin
        self.min_confidence = 40     # Minimum güven skoru
        
        # Ekran boyutu ayarları
        self.max_pencere_genislik = 1200  # Maksimum pencere genişliği
        self.max_pencere_yukseklik = 800  # Maksimum pencere yüksekliği
        
        print("✅ FaturaOCR sistemi başlatıldı!")
        print(f"   📐 Ekran boyutu: {self.max_pencere_genislik}x{self.max_pencere_yukseklik} piksel")
    
    def resmi_yukle(self, dosya_yolu: str) -> Optional[np.ndarray]:
        """
        Belirtilen dosya yolundan fatura resmini yükler.
        
        Args:
            dosya_yolu (str): Resim dosyasının tam yolu
            
        Returns:
            np.ndarray: Yüklenen resim (BGR formatında) veya None (hata durumunda)
        """
        try:
            print(f"📁 Resim yükleniyor: {dosya_yolu}")
            
            # Resmi yükle
            img = cv2.imread(dosya_yolu)
            
            if img is None:
                print(f"❌ Hata: '{dosya_yolu}' dosyası yüklenemedi!")
                return None
            
            # Resim boyutlarını kontrol et
            height, width = img.shape[:2]
            print(f"✅ Resim başarıyla yüklendi: {width}x{height} piksel")
            
            return img
            
        except Exception as e:
            print(f"❌ Resim yükleme hatası: {e}")
            return None
    
    def resmi_on_isle(self, img: np.ndarray, gurultu_azaltma: bool = True) -> np.ndarray:
        """
        OCR için resmi ön işlemden geçirir.
        
        Args:
            img (np.ndarray): İşlenecek resim (BGR formatında)
            gurultu_azaltma (bool): Gürültü azaltma işlemi yapılsın mı?
            
        Returns:
            np.ndarray: İşlenmiş resim (gri tonlamada)
        """
        print("🔧 Resim ön işleme başlatılıyor...")
        
        try:
            # 1. BGR'den gri tonlamaya çevir
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            print("   ✅ Gri tonlamaya çevrildi")
            
            if gurultu_azaltma:
                # 2. Gaussian blur ile gürültü azaltma
                blur = cv2.GaussianBlur(gray, (5, 5), 0)
                print("   ✅ Gaussian blur uygulandı")
                
                # 3. Adaptif eşikleme ile siyah-beyaz yapma
                thresh = cv2.adaptiveThreshold(
                    blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY, 11, 2
                )
                print("   ✅ Adaptif eşikleme uygulandı")
                
                # 4. Median blur ile ekstra parazit azaltma
                clean = cv2.medianBlur(thresh, 3)
                print("   ✅ Median blur uygulandı")
                
                return clean
            else:
                return gray
                
        except Exception as e:
            print(f"❌ Resim ön işleme hatası: {e}")
            return img
    
    def metni_cikar(self, img: np.ndarray, dil: str = 'tur') -> Dict:
        """
        Resimden OCR kullanarak metin ve koordinat bilgilerini çıkarır.
        
        Args:
            img (np.ndarray): İşlenecek resim
            dil (str): OCR dili ('tur' = Türkçe)
            
        Returns:
            Dict: OCR sonuçları (metin, koordinatlar, güven skorları)
        """
        print(f"🔍 OCR işlemi başlatılıyor (Dil: {dil})...")
        
        try:
            # OCR işlemi
            data = pytesseract.image_to_data(
                img, 
                lang=dil, 
                config=self.ocr_config, 
                output_type=Output.DICT
            )
            
            # Sonuçları analiz et
            n_boxes = len(data['text'])
            gecerli_metinler = 0
            
            for i in range(n_boxes):
                if int(data['conf'][i]) >= self.min_confidence:
                    gecerli_metinler += 1
            
            print(f"✅ OCR tamamlandı: {gecerli_metinler}/{n_boxes} geçerli metin bulundu")
            
            return data
            
        except Exception as e:
            print(f"❌ OCR hatası: {e}")
            return {}
    
    def anahtar_kelimeleri_bul(self, ocr_data: Dict) -> List[Dict]:
        """
        OCR verilerinde anahtar kelimeleri arar ve bulur.
        
        Args:
            ocr_data (Dict): OCR sonuçları
            
        Returns:
            List[Dict]: Bulunan anahtar kelimeler ve bilgileri
        """
        print("🔍 Anahtar kelimeler aranıyor...")
        
        bulunan_kelimeler = []
        n_boxes = len(ocr_data.get('text', []))
        
        for i in range(n_boxes):
            if int(ocr_data['conf'][i]) >= self.min_confidence:
                metin = ocr_data['text'][i].lower()
                
                # Anahtar kelime kontrolü
                for anahtar in self.anahtar_kelimeler:
                    if anahtar in metin:
                        kelime_bilgisi = {
                            'index': i,
                            'metin': ocr_data['text'][i],
                            'anahtar_kelime': anahtar,
                            'x': ocr_data['left'][i],
                            'y': ocr_data['top'][i],
                            'genislik': ocr_data['width'][i],
                            'yukseklik': ocr_data['height'][i],
                            'guven': ocr_data['conf'][i]
                        }
                        bulunan_kelimeler.append(kelime_bilgisi)
                        print(f"   ✅ Anahtar kelime bulundu: '{ocr_data['text'][i]}' ({anahtar})")
                        break
        
        print(f"✅ Toplam {len(bulunan_kelimeler)} anahtar kelime bulundu")
        return bulunan_kelimeler
    
    def tutar_bul(self, ocr_data: Dict, anahtar_kelime_bilgisi: Dict) -> Optional[str]:
        """
        Anahtar kelime ile aynı satırda bulunan tutarı arar.
        
        Args:
            ocr_data (Dict): OCR sonuçları
            anahtar_kelime_bilgisi (Dict): Bulunan anahtar kelime bilgisi
            
        Returns:
            str: Bulunan tutar veya None
        """
        print(f"💰 Tutar aranıyor: '{anahtar_kelime_bilgisi['metin']}' için...")
        
        try:
            anahtar_y = anahtar_kelime_bilgisi['y']
            anahtar_x = anahtar_kelime_bilgisi['x']
            n_boxes = len(ocr_data['text'])
            
            for j in range(n_boxes):
                if int(ocr_data['conf'][j]) >= self.min_confidence:
                    # Aynı satırda mı kontrol et
                    is_on_same_line = abs(ocr_data['top'][j] - anahtar_y) < 20
                    # Sağda mı kontrol et
                    is_to_the_right = ocr_data['left'][j] > anahtar_x
                    
                    if is_on_same_line and is_to_the_right:
                        potential_text = ocr_data['text'][j]
                        # Sadece rakam, virgül ve nokta içeren metinleri al
                        cleaned_text = re.sub(r'[^\d,.]', '', potential_text)
                        
                        # Tutar formatı kontrolü (rakam + virgül/nokta)
                        if re.search(r'[\d]', cleaned_text) and re.search(r'[,.]', cleaned_text):
                            print(f"   ✅ Potansiyel tutar bulundu: '{cleaned_text}'")
                            return cleaned_text
            
            print("   ❌ Bu anahtar kelime için tutar bulunamadı")
            return None
            
        except Exception as e:
            print(f"❌ Tutar arama hatası: {e}")
            return None
    
    def sonuclari_gorselle(self, img: np.ndarray, ocr_data: Dict, 
                          anahtar_kelimeler: List[Dict], bulunan_tutarlar: List[Dict]) -> np.ndarray:
        """
        OCR sonuçlarını görsel olarak işaretler.
        
        Args:
            img (np.ndarray): Orijinal resim
            ocr_data (Dict): OCR sonuçları
            anahtar_kelimeler (List[Dict]): Bulunan anahtar kelimeler
            bulunan_tutarlar (List[Dict]): Bulunan tutarlar
            
        Returns:
            np.ndarray: İşaretlenmiş resim
        """
        print("🎨 Görsel sonuçlar hazırlanıyor...")
        
        # Resmin kopyasını al
        result_img = img.copy()
        
        # Tüm tanınan kelimeleri kırmızı kutularla işaretle
        n_boxes = len(ocr_data.get('text', []))
        for i in range(n_boxes):
            if int(ocr_data['conf'][i]) >= self.min_confidence:
                (x, y, w, h) = (ocr_data['left'][i], ocr_data['top'][i], 
                               ocr_data['width'][i], ocr_data['height'][i])
                cv2.rectangle(result_img, (x, y), (x + w, y + h), (0, 0, 255), 1)  # Kırmızı
        
        # Anahtar kelimeleri yeşil kutularla işaretle
        for kelime in anahtar_kelimeler:
            (x, y, w, h) = (kelime['x'], kelime['y'], kelime['genislik'], kelime['yukseklik'])
            cv2.rectangle(result_img, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Yeşil
        
        # Bulunan tutarları mavi kutularla işaretle
        for tutar in bulunan_tutarlar:
            if tutar['koordinatlar']:
                (x, y, w, h) = tutar['koordinatlar']
                cv2.rectangle(result_img, (x, y), (x + w, y + h), (255, 0, 0), 2)  # Mavi
        
        print("✅ Görsel sonuçlar hazırlandı")
        return result_img
    
    def resmi_olcekli_goster(self, img: np.ndarray, pencere_adi: str, max_genislik: int = None, max_yukseklik: int = None):
        """
        Resmi uygun ölçekte gösterir.
        
        Args:
            img (np.ndarray): Gösterilecek resim
            pencere_adi (str): Pencere adı
            max_genislik (int): Maksimum pencere genişliği (None ise varsayılan kullanılır)
            max_yukseklik (int): Maksimum pencere yüksekliği (None ise varsayılan kullanılır)
        """
        # Varsayılan boyutları kullan
        if max_genislik is None:
            max_genislik = self.max_pencere_genislik
        if max_yukseklik is None:
            max_yukseklik = self.max_pencere_yukseklik
        
        # Resim boyutlarını al
        height, width = img.shape[:2]
        
        # Ölçek faktörünü hesapla
        scale_x = max_genislik / width
        scale_y = max_yukseklik / height
        scale = min(scale_x, scale_y, 1.0)  # 1.0'dan büyük olmasın
        
        # Yeni boyutları hesapla
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        # Resmi yeniden boyutlandır
        resized_img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # Pencereyi oluştur ve boyutlandır
        cv2.namedWindow(pencere_adi, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(pencere_adi, new_width, new_height)
        
        # Resmi göster
        cv2.imshow(pencere_adi, resized_img)
        
        print(f"   📏 Resim ölçeklendi: {width}x{height} → {new_width}x{new_height} (ölçek: {scale:.2f})")
    
    def fatura_analiz_et(self, dosya_yolu: str, sonuc_goster: bool = True) -> Dict:
        """
        Ana fonksiyon: Faturayı analiz eder ve sonuçları döndürür.
        
        Args:
            dosya_yolu (str): Fatura resim dosyasının yolu
            sonuc_goster (bool): Sonuçları görsel olarak göster
            
        Returns:
            Dict: Analiz sonuçları
        """
        print("=" * 60)
        print("🚀 FATURA ANALİZİ BAŞLATILIYOR")
        print("=" * 60)
        
        # 1. Resmi yükle
        img = self.resmi_yukle(dosya_yolu)
        if img is None:
            return {"hata": "Resim yüklenemedi"}
        
        # 2. Resmi ön işle
        processed_img = self.resmi_on_isle(img)
        
        # 3. OCR ile metni çıkar
        ocr_data = self.metni_cikar(processed_img)
        if not ocr_data:
            return {"hata": "OCR işlemi başarısız"}
        
        # 4. Anahtar kelimeleri bul
        anahtar_kelimeler = self.anahtar_kelimeleri_bul(ocr_data)
        
        # 5. Her anahtar kelime için tutar ara
        bulunan_tutarlar = []
        for kelime in anahtar_kelimeler:
            tutar = self.tutar_bul(ocr_data, kelime)
            if tutar:
                tutar_bilgisi = {
                    'anahtar_kelime': kelime['metin'],
                    'tutar': tutar,
                    'koordinatlar': (kelime['x'], kelime['y'], kelime['genislik'], kelime['yukseklik'])
                }
                bulunan_tutarlar.append(tutar_bilgisi)
        
        # 6. Sonuçları görselleştir
        if sonuc_goster:
            result_img = self.sonuclari_gorselle(img, ocr_data, anahtar_kelimeler, bulunan_tutarlar)
            # Resmi uygun ölçekte göster
            self.resmi_olcekli_goster(result_img, "Fatura OCR Analiz Sonucu")
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        
        # 7. Sonuçları döndür
        sonuclar = {
            "dosya": dosya_yolu,
            "anahtar_kelimeler_bulundu": len(anahtar_kelimeler),
            "tutarlar_bulundu": len(bulunan_tutarlar),
            "anahtar_kelimeler": anahtar_kelimeler,
            "bulunan_tutarlar": bulunan_tutarlar,
            "toplam_metin_sayisi": len(ocr_data.get('text', [])),
            "ortalama_guven_skoru": np.mean([float(x) for x in ocr_data.get('conf', []) if x != -1])
        }
        
        # Sonuçları yazdır
        self.sonuclari_yazdir(sonuclar)
        
        return sonuclar
    
    def sonuclari_yazdir(self, sonuclar: Dict):
        """
        Analiz sonuçlarını güzel bir şekilde yazdırır.
        
        Args:
            sonuclar (Dict): Analiz sonuçları
        """
        print("\n" + "=" * 60)
        print("📊 ANALİZ SONUÇLARI")
        print("=" * 60)
        
        if "hata" in sonuclar:
            print(f"❌ HATA: {sonuclar['hata']}")
            return
        
        print(f"📁 Dosya: {sonuclar['dosya']}")
        print(f"🔍 Bulunan Anahtar Kelimeler: {sonuclar['anahtar_kelimeler_bulundu']}")
        print(f"💰 Bulunan Tutarlar: {sonuclar['tutarlar_bulundu']}")
        print(f"📝 Toplam Metin Sayısı: {sonuclar['toplam_metin_sayisi']}")
        print(f"📊 Ortalama Güven Skoru: {sonuclar['ortalama_guven_skoru']:.1f}%")
        
        if sonuclar['bulunan_tutarlar']:
            print("\n💰 BULUNAN TUTARLAR:")
            for i, tutar in enumerate(sonuclar['bulunan_tutarlar'], 1):
                print(f"   {i}. {tutar['anahtar_kelime']} → {tutar['tutar']}")
        else:
            print("\n❌ Hiç tutar bulunamadı!")
        
        print("=" * 60)


def main():
    """
    Ana program fonksiyonu - test ve örnek kullanım için.
    """
    print("🎯 Akıllı Fatura Tanıma Sistemi - 5. Gün")
    print("📚 Haftalık Değerlendirme ve Kod Toparlama")
    print()
    
    # FaturaOCR sistemini başlat
    ocr_sistemi = FaturaOCR()
    
    # Test dosyası yolu (kullanıcı buraya kendi dosya yolunu yazabilir)
    test_dosya = r"C:\Users\hasan\OneDrive\Desktop\1.png"
    
    # Dosya var mı kontrol et
    if os.path.exists(test_dosya):
        print(f"✅ Test dosyası bulundu: {test_dosya}")
        
        # Faturayı analiz et
        sonuclar = ocr_sistemi.fatura_analiz_et(test_dosya, sonuc_goster=True)
        
    else:
        print(f"⚠️  Test dosyası bulunamadı: {test_dosya}")
        print("💡 Lütfen kendi fatura resminizin yolunu 'test_dosya' değişkenine yazın.")
        print("   Örnek: test_dosya = r'C:\\Users\\hasan\\Desktop\\fatura.png'")
        
        # Örnek resim oluştur (test için)
        print("\n🎨 Test için örnek resim oluşturuluyor...")
        test_img = np.ones((600, 800, 3), dtype=np.uint8) * 255  # Beyaz arka plan
        
        # Test metni ekle
        cv2.putText(test_img, "ORNEK FATURA", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
        cv2.putText(test_img, "Odenecek Tutar: 150,50 TL", (50, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(test_img, "Toplam: 180,00 TL", (50, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(test_img, "Test amacli olusturulmustur", (50, 500), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (128, 128, 128), 2)
        
        # Örnek resmi göster
        ocr_sistemi.resmi_olcekli_goster(test_img, "Test Ornek Fatura")
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
