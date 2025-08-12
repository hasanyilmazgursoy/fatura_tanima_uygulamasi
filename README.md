# 🧾 Akıllı Fatura Tanıma Uygulaması

## 📋 Proje Hakkında

Bu proje, **OCR (Optik Karakter Tanıma)** ve **Düzenli İfadeler (Regex)** teknolojileri kullanarak fatura resimlerinden otomatik olarak yapılandırılmış veri çıkaran gelişmiş bir Python uygulamasıdır. 

### 🎯 Ana Özellikler
- **FLO fatura formatına özel optimize edilmiş** analiz sistemi
- **27 farklı fatura alanı** için yapılandırılmış veri çıkarma
- **15 farklı regex deseni** ile otomatik veri tanıma
- **Çoklu fatura formatı** desteği (e-Arşiv, e-Fatura, Proforma)
- **Adaptif OCR teknolojisi** ile yüksek doğruluk oranı
- **Gerçek zamanlı görsel geri bildirim** sistemi

## 🎯 Sistem Yetenekleri

### 📊 Çıkarılabilen Fatura Bilgileri
**Temel Bilgiler:**
- Fatura numarası (FEA2025001157280 formatı)
- Fatura tarihi ve son ödeme tarihi
- Fatura tipi (e-Arşiv, e-Fatura, Proforma)
- ETTN (Evrensel Tekil Fatura Numarası)

**Satıcı Bilgileri:**
- Firma ünvanı, adres, telefon, email
- Vergi dairesi ve vergi numarası
- Web sitesi, ticaret sicil, mersis numarası

**Alıcı Bilgileri:**
- Müşteri adı/firma, adres, iletişim bilgileri
- TC kimlik numarası, müşteri numarası
- Vergi dairesi ve vergi numarası

**Finansal Bilgiler:**
- Mal/hizmet toplam tutarı
- İskonto oranı ve tutarı
- KDV oranı ve tutarı
- Vergi hariç/dahil tutarlar
- Genel toplam ve ödenecek tutar

**Ürün ve Ödeme:**
- Ürün listesi ve detayları
- Ödeme şekli ve vadesi
- Banka hesap bilgileri (IBAN)
- Taşıyıcı ve gönderim bilgileri

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

### 🎯 Ana Sistem (Önerilen)
```python
from fatura_regex_analiz import FaturaRegexAnaliz

# Sistemi başlat
analiz_sistemi = FaturaRegexAnaliz()

# Tek fatura analizi
sonuclar = analiz_sistemi.fatura_analiz_et("fatura.png")

# Çoklu fatura analizi (otomatik rapor)
python fatura_regex_analiz.py
```

### 🔧 Manuel İşlemler
```python
# Resim yükleme ve ön işleme
img = analiz_sistemi.resmi_yukle("fatura.png")
processed_img = analiz_sistemi.resmi_on_isle(img)

# OCR ile metin çıkarma
ocr_data = analiz_sistemi.metni_cikar(processed_img)

# Yapılandırılmış veri çıkarma
ham_metin = ' '.join([text for text in ocr_data['text'] if text.strip()])
structured_data = analiz_sistemi.yapilandirilmis_veri_cikar(ocr_data, ham_metin)
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

## 📊 Performans ve Başarı Oranları

### 🎯 Test Sonuçları (16 Fatura)
- **FLO Faturalarında**: %85+ başarı oranı
- **Temel Bilgiler**: %75+ yakalama oranı
- **Finansal Tutarlar**: %80+ doğruluk
- **İletişim Bilgileri**: %70+ başarı

### 📋 Regex Performansı
| Kategori | Başarı Oranı | Örnekler |
|----------|---------------|----------|
| Fatura No | %75 | FEA2025001157280 |
| Tarih | %69 | 24-04-2025 |
| Para | %75 | 1.899,98 TRY |
| Telefon | %69 | +90 212 446 22 88 |
| Email | %69 | info@firma.com.tr |
| IBAN | %6 | TR13 0006 4000... |

## 📄 Çıktı Formatı

```json
{
  "dosya": "fatura.png",
  "analiz_zamani": "2025-08-12 13:28:05",
  "regex": {
    "fatura_no": ["FEA2025001157280"],
    "tarih": ["24-04-2025"],
    "para": ["1.899,98 TRY", "400,00 TRY"]
  },
  "structured": {
    "fatura_numarasi": "FEA2025001157280",
    "satici_firma_unvani": "FLO MAĞAZACILIK A.Ş.",
    "genel_toplam": "1.899,98",
    "para_birimi": "TRY"
  }
}
```

## 🚀 Teknik Özellikler

### 🔧 OCR Teknolojisi
- **Tesseract Engine**: OEM 3 + PSM 6/4 adaptif modu
- **Dil Desteği**: Türkçe + İngilizce birlikte
- **Görüntü İyileştirme**: Otomatik ölçekleme (1.5x küçük resimler için)
- **Güven Skoru**: Minimum %30 güvenilirlik filtresi

### 🎯 Regex Desenleri (15 Adet)
- Tarih formatları (DD.MM.YYYY, DD/MM/YYYY)
- Para formatları (1.899,98 TRY, 150,50)
- Türk IBAN formatları (TR9Y TREZ...)
- Fatura numaraları (FEA2025001157280)
- ETTN UUID formatı
- Telefon numaraları (+90 212 446 22 88)
- Email adresleri
- Vergi/TC/Mersis numaraları

### 📊 Veri Çıkarma Algoritması
- **27 yapılandırılmış alan** için özel algoritmalar
- **Heuristik yaklaşım**: Anahtar kelime + konumsal analiz
- **Çoklu doğrulama**: Regex + OCR koordinat bilgisi
- **Normalizasyon**: Otomatik veri temizleme ve standardizasyon

## 🔍 Desteklenen Formatlar

- **Resim Türleri**: PNG, JPG, JPEG, TIF, TIFF, BMP
- **Fatura Türleri**: e-Arşiv, e-Fatura, Proforma, İrsaliye
- **Firma Formatları**: FLO optimized, genel e-fatura desteği
- **Çözünürlük**: 556x632'den 1653x2339'a kadar test edildi

## 💡 En İyi Sonuçlar İçin

1. **300 DPI** veya daha yüksek çözünürlük
2. **Düz açı** ve **iyi aydınlatma**
3. **Kontrast** artırılmış, **net** görüntüler
4. **FLO fatura formatı** için optimize edilmiş

## 🎯 Proje Durumu

✅ **Ana Sistem**: Tamamlandı ve test edildi  
✅ **Regex Motoru**: 15 desen ile optimize edildi  
✅ **FLO Entegrasyonu**: %85+ başarı oranı  
✅ **Çoklu Format**: 16 farklı fatura test edildi  
⚠️ **İyileştirme Alanları**: IBAN (%6) ve ETTN (%6) yakalama  

---

**🚀 Gelişmiş OCR + Regex sistemi ile faturalarınızı otomatik analiz edin!** 🎉
