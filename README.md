# 🧾 Akıllı Fatura Tanıma Uygulaması

## 📋 Proje Hakkında

Bu proje, **OCR (Optik Karakter Tanıma)** teknolojisi kullanarak faturalardan otomatik olarak bilgi çıkarmaya yönelik bir Python uygulamasıdır. Hafta boyunca geliştirilen tüm özellikler, 5. günde temiz ve anlaşılır fonksiyonlar halinde birleştirilmiştir.

## 🎯 Haftalık Gelişim Süreci

### 1. Gün: `görüntüyüKodlaOkumak.py`
- Temel görüntü işleme
- Resim yükleme ve gri tonlamaya çevirme
- Median blur ile gürültü azaltma

### 2. Gün: `OCR_kullanimi.py`
- Tesseract OCR entegrasyonu
- Gelişmiş görüntü ön işleme
- Türkçe dil desteği

### 3. Gün: `kelimleri bulma.py`
- Akıllı metin analizi
- Anahtar kelime arama
- Tutar bulma algoritması

### 4. Gün: `OCR_ile_box_2.py`
- Görsel geri bildirim
- Çoklu anahtar kelime desteği
- Hata yönetimi

### 5. Gün: `fatura_ocr_sistemi.py` ⭐
- **Haftalık değerlendirme ve kod toparlama**
- Tüm özellikleri birleştiren ana sistem
- Temiz ve anlaşılır fonksiyonlar

## 🚀 Kurulum

### Gereksinimler
```bash
pip install opencv-python
pip install pytesseract
pip install numpy
```

### Tesseract Kurulumu
1. [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) indirin
2. Windows için: `C:\Program Files\Tesseract-OCR\` klasörüne kurun
3. Sistem PATH'ine ekleyin

## 📖 Kullanım

### Basit Kullanım
```python
from fatura_ocr_sistemi import FaturaOCR

# Sistemi başlat
ocr_sistemi = FaturaOCR()

# Faturayı analiz et
sonuclar = ocr_sistemi.fatura_analiz_et("fatura.png")
```

### Gelişmiş Kullanım
```python
# Özel Tesseract yolu ile başlat
ocr_sistemi = FaturaOCR(tesseract_path="C:/custom/path/tesseract.exe")

# Sadece metin çıkarma (görsel gösterme)
sonuclar = ocr_sistemi.fatura_analiz_et("fatura.png", sonuc_goster=False)

# Manuel işlemler
img = ocr_sistemi.resmi_yukle("fatura.png")
processed = ocr_sistemi.resmi_on_isle(img)
ocr_data = ocr_sistemi.metni_cikar(processed)
```

## 🔧 Ana Fonksiyonlar

### `resmi_yukle(dosya_yolu)`
- Belirtilen dosya yolundan fatura resmini yükler
- Dosya varlığını ve formatını kontrol eder
- Hata durumunda None döndürür

### `resmi_on_isle(img, gurultu_azaltma=True)`
- OCR için resmi ön işlemden geçirir
- Gri tonlama, blur, eşikleme işlemleri
- Gürültü azaltma seçeneği

### `metni_cikar(img, dil='tur')`
- OCR ile metin ve koordinat bilgilerini çıkarır
- Türkçe dil desteği
- Güven skorları ile filtreleme

### `anahtar_kelimeleri_bul(ocr_data)`
- OCR verilerinde anahtar kelimeleri arar
- "ödenecek", "toplam", "tutar" gibi terimleri bulur
- Koordinat ve güven bilgilerini döndürür

### `tutar_bul(ocr_data, anahtar_kelime_bilgisi)`
- Anahtar kelime ile aynı satırdaki tutarı arar
- Regex ile tutar formatını doğrular
- Konumsal analiz yapar

### `fatura_analiz_et(dosya_yolu, sonuc_goster=True)`
- **Ana fonksiyon**: Tüm işlemleri sırayla yapar
- Sonuçları görsel olarak gösterir
- Detaylı analiz raporu döndürür

## 🎨 Görsel Çıktı

Sistem, analiz sonuçlarını renkli kutularla işaretler:
- 🔴 **Kırmızı**: Tüm tanınan kelimeler
- 🟢 **Yeşil**: Anahtar kelimeler
- 🔵 **Mavi**: Bulunan tutarlar

## 📊 Çıktı Formatı

```python
{
    "dosya": "fatura.png",
    "anahtar_kelimeler_bulundu": 3,
    "tutarlar_bulundu": 2,
    "anahtar_kelimeler": [...],
    "bulunan_tutarlar": [
        {
            "anahtar_kelime": "Ödenecek Tutar",
            "tutar": "150,50",
            "koordinatlar": (x, y, w, h)
        }
    ],
    "toplam_metin_sayisi": 45,
    "ortalama_guven_skoru": 78.5
}
```

## ⚙️ Yapılandırma

### Anahtar Kelimeler
```python
ocr_sistemi.anahtar_kelimeler = [
    "ödenecek", "toplam", "tutar", "genel toplam", 
    "ödenecek tutar", "vergiler dahil", "net tutar"
]
```

### OCR Ayarları
```python
ocr_sistemi.ocr_config = '--psm 6'      # Tek blok metin
ocr_sistemi.min_confidence = 40         # Minimum güven skoru
```

## 🐛 Hata Ayıklama

Sistem detaylı log mesajları verir:
- 📁 Resim yükleme durumu
- 🔧 İşlem adımları
- ✅ Başarılı işlemler
- ❌ Hata mesajları
- 📊 İstatistikler

## 🔍 Desteklenen Dosya Formatları

- **Resim**: PNG, JPG, JPEG, BMP, TIFF
- **Diller**: Türkçe (varsayılan), İngilizce
- **Çözünürlük**: Herhangi bir boyut

## 💡 İpuçları

1. **Yüksek kaliteli resimler** kullanın
2. **İyi aydınlatma** ile çekin
3. **Düz açı** ile fotoğraf çekin
4. **Tesseract yolunu** doğru ayarlayın

## 📝 Lisans

Bu proje eğitim amaçlı geliştirilmiştir.

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun
3. Commit yapın
4. Pull request gönderin

---

**🎯 Haftanın Hedefi: ✅ TAMAMLANDI!**

Bir fatura resmi verildiğinde, içindeki tüm metinleri ve koordinatlarını başarıyla çıkaran Python script'i hazır! 🎉
