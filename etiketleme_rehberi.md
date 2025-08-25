# 🎯 Fatura Etiketleme Rehberi

## ⚠️ **ÖNEMLİ: Manuel Etiketleme**

**Label Studio'da OCR özelliği mevcut olmadığı için:**
- Metin kutularını **manuel olarak** oluşturmanız gerekiyor
- Faturayı **yakınlaştırıp** metin alanlarını seçin
- Her metin alanı için **Rectangle** aracı kullanın

## 📋 Etiket Açıklamaları

### 🔴 **Temel Fatura Bilgileri (Kırmızı Tonları)**
- **`fatura_numarasi`** (#FF0000) - Fatura numarası (örn: "2222023000000092")
- **`fatura_tarihi`** (#FF4500) - Fatura tarihi (örn: "05.04.2023")
- **`fatura_tipi`** (#FF6347) - e-Fatura, e-Arşiv, Proforma vb.
- **`ettn`** (#FFD700) - UUID formatında evrensel tekil numara
- **`son_odeme_tarihi`** (#FFA500) - Ödeme son tarihi

### 🔵 **Satıcı Bilgileri (Mavi Tonları)**
- **`satici_firma_unvani`** (#0000FF) - Satıcı firma adı
- **`satici_adres`** (#4169E1) - Satıcının adresi
- **`satici_telefon`** (#1E90FF) - Satıcı telefon numarası
- **`satici_email`** (#00BFFF) - Satıcı e-posta adresi
- **`satici_vergi_dairesi`** (#87CEEB) - Vergi dairesi adı
- **`satici_vergi_numarasi`** (#ADD8E6) - Vergi numarası
- **`satici_web_sitesi`** (#B0E0E6) - Web sitesi URL'i
- **`satici_ticaret_sicil`** (#AFEEEE) - Ticaret sicil numarası
- **`satici_mersis_no`** (#E0FFFF) - Mersis numarası

### 🟢 **Alıcı Bilgileri (Yeşil Tonları)**
- **`alici_firma_unvani`** (#008000) - Alıcı firma/kişi adı
- **`alici_adres`** (#32CD32) - Alıcının adresi
- **`alici_telefon`** (#90EE90) - Alıcı telefon numarası
- **`alici_email`** (#98FB98) - Alıcı e-posta adresi
- **`alici_tckn`** (#00FF00) - TC Kimlik Numarası
- **`alici_musteri_no`** (#7CFC00) - Müşteri numarası

### 🟣 **Ürün/Hizmet Bilgileri (Mor Tonları)**
- **`urun_aciklama`** (#800080) - Ürün/hizmet açıklaması
- **`urun_miktar`** (#8A2BE2) - Miktar (örn: "2 adet")
- **`birim_fiyat`** (#DA70D6) - Birim fiyat (örn: "150,00 TL")
- **`urun_tutar`** (#DDA0DD) - Ürün toplam tutarı
- **`kdv_orani`** (#EE82EE) - KDV oranı (örn: "%18")

### 🌸 **Finansal Toplamlar (Pembe Tonları)**
- **`mal_hizmet_toplam`** (#FF1493) - Ara toplam
- **`toplam_iskonto`** (#DC143C) - Toplam indirim
- **`vergi_haric_tutar`** (#FF69B4) - Vergi hariç toplam
- **`hesaplanan_kdv`** (#FF00FF) - Hesaplanan KDV tutarı
- **`vergiler_dahil_toplam`** (#FFB6C1) - Vergiler dahil toplam
- **`genel_toplam`** (#FFC0CB) - Ödenecek toplam tutar

### 🟤 **Ödeme ve Diğer Bilgiler (Kahverengi Tonları)**
- **`odeme_sekli`** (#8B4513) - Ödeme şekli (Kredi Kartı, Havale vb.)
- **`banka_bilgileri`** (#A0522D) - IBAN ve banka bilgileri
- **`kargo_bilgisi`** (#CD853F) - Kargo firması
- **`siparis_no`** (#D2691E) - Sipariş numarası

---

## 🎪 **Label Studio'da Etiketleme Adımları**

### **1. Proje Oluşturma**
1. http://localhost:8080 adresine gidin
2. "Create Project" butonuna tıklayın
3. Proje adı: "Fatura Veri Etiketleme"
4. "Data Import" bölümünden fatura dosyalarını yükleyin

### **2. Etiketleme Yapılandırması**
1. "Labeling Setup" bölümüne gidin
2. "Browse Templates" → "OCR" şablonu seçin
3. Yukarıdaki XML konfigürasyonunu kopyalayıp "Code" kısmına yapıştırın

### **3. Etiketleme Stratejisi**
- **Metin Seçimi**: OCR'dan çıkan metin kutularını tıklayarak seçin
- **Birleştirme**: Birbiriyle ilişkili metinleri tek etiket altında birleştirin
- **Tutarlılık**: Aynı tür veriyi her faturada aynı etiketle işaretleyin
- **Kalite**: Sadece emin olduğunuz alanları etiketleyin

### **4. Örnek Etiketleme**

**Fatura Başlığı İçin:**
```
[2222023000000092] → fatura_numarasi
[05.04.2023] → fatura_tarihi
[e-Arşiv Fatura] → fatura_tipi
```

**Satıcı Bilgileri İçin:**
```
[ABC GIDA SANAYİ VE TİCARET A.Ş.] → satici_firma_unvani
[İstanbul/Maltepe, Bağlarbaşı Mah.] → satici_adres
[0212 123 45 67] → satici_telefon
```

**Ürün Satırları İçin:**
```
[Elma 1 KG Paket] → urun_aciklama
[5] → urun_miktar
[25,00 TL] → birim_fiyat
[125,00 TL] → urun_tutar
[%8] → kdv_orani
```

---

## 📊 **İlk Etiketleme Seti İçin Öneriler**

### **Öncelik Sırası:**
1. **fatura_numarasi** - En kritik, dosya adından çıkarılabilir
2. **fatura_tarihi** - Genellikle belirgin
3. **genel_toplam** - En büyük tutar
4. **satici_firma_unvani** - Firma adı
5. **alici_firma_unvani** - Alıcı adı

### **Başlangıç Hedefi:**
- **İlk oturum**: 10-15 farklı fatura
- **Minimum alan**: 5-7 temel alan
- **Kalite**: %100 doğru etiketleme

---

## 💾 **Export ve Devam**

Etiketleme tamamlandıktan sonra:
1. Proje ana sayfasından "Export" butonuna tıklayın
2. Format olarak "JSON" seçin
3. Dosyayı `dataset/` klasörüne kaydedin
4. Aşama 2'ye geçelim!
