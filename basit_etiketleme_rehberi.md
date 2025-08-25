# 🎯 Basit Etiketleme Rehberi

## 📋 Etiket Açıklamaları

- **`fatura_numarasi`** (kırmızı) - Fatura numarası
- **`fatura_tarihi`** (turuncu) - Fatura tarihi
- **`genel_toplam`** (yeşil) - Ödenecek toplam tutar
- **`satici_firma_unvani`** (mavi) - Satıcı firma adı
- **`alici_firma_unvani`** (mor) - Alıcı firma/kişi adı

## 🎪 Etiketleme Adımları

### **1. Rectangle Aracı ile Metin Kutusu Oluşturma:**
1. **Faturayı yakınlaştırın** (zoom butonları)
2. **Sol panelden Rectangle aracını seçin**
3. **İlgili metni bulup üzerine kare çizin**
4. **Renk kodlu kutu görünecek**

### **2. Etiket Atama:**
1. **Kutuya tıklayın** (seçili hale gelsin)
2. **Sağ panelden etiketi seçin**
3. **"Submit" butonuna tıklayın**

### **3. Örnek Etiketleme:**

**Fatura Numarası:**
- Dosya: `05.04.2023-2222023000000092.pdf`
- Faturada "2222023000000092" yazan yeri bulun
- Rectangle ile kutu çizin
- `fatura_numarasi` etiketini seçin

**Fatura Tarihi:**
- Faturada "05.04.2023" yazan yeri bulun
- Rectangle ile kutu çizin
- `fatura_tarihi` etiketini seçin

**Genel Toplam:**
- Faturada en büyük tutarı bulun
- Rectangle ile kutu çizin
- `genel_toplam` etiketini seçin

## 🚀 Başlama

1. **Label Studio'ya gidin:** http://localhost:8080
2. **Proje ana sayfasında "Import" butonuna tıklayın**
3. **5 farklı fatura yükleyin**
4. **İlk faturaya tıklayıp etiketlemeye başlayın**

