# 🧾 Akıllı Fatura Tanıma ve Veri Çıkarma Sistemi

Bu proje, fatura görsellerinden ve PDF dosyalarından yapılandırılmış verileri (JSON, CSV) otomatik olarak çıkaran, gelişmiş bir Python uygulamasıdır. Özellikle, tek tip fatura düzenleri için optimize edilmiş, geometrik bölge tespiti ve akıllı veri çıkarma algoritmalarıyla yüksek doğruluk hedefler.

## ✨ Ana Özellikler

- **Çoklu Format Desteği:** PNG, JPG ve PDF formatındaki fatura dosyalarını işleyebilir.
- **Hassas Geometrik Bölge Tespiti:** Kullanıcı tarafından belirlenmiş, özel koordinatlara dayalı geometrik bölgeler (Satıcı Bilgileri, Fatura Detayları, Alıcı Bilgileri, Toplamlar) kullanarak faturanın farklı alanlarını ayrıştırır.
- **Kapsamlı Veri Çıkarma:** `config/patterns.json` dosyasında tanımlanan Regex desenleri ile fatura numarası, tarih, tutarlar, VKN, adres gibi ana bilgileri; `pdfplumber` ve `pandas` entegrasyonu ile ise ürün/hizmet kalemlerini tablolar halinde çıkarır.
- **Esnek Yapılandırma:** Tesseract OCR motorunun yolu, fatura ve rapor klasörleri gibi tüm uygulama ayarları `config.json` üzerinden kolayca yönetilir.
- **Yüksek Başarılı OCR:** Tesseract OCR motoru, Türkçe (tur) ve İngilizce (eng) dilleri için optimize edilmiş, güvenilir metin tanıma sağlar.
- **Görsel Hata Ayıklama (Debug):** Tespit edilen geometrik bölgeleri ve çıkarılan verileri doğrudan fatura görseli üzerine çizerek görsel doğrulama ve hata ayıklama imkanı sunar.
- **Detaylı Raporlama:** Analiz sonuçlarını hem makine tarafından okunabilir JSON hem de kolay işlenebilir CSV formatında sunar.
- **Hata Yönetimi:** Analiz sırasında oluşan hataları `analiz_hatalari.log` dosyasına kaydederek sorun takibini kolaylaştırır.

## 🚀 Kurulum ve Çalıştırma

### 1. Gerekli Kütüphaneler

Projeyi çalıştırmak için aşağıdaki Python kütüphanelerini yükleyin:

```bash
pip install opencv-python pytesseract numpy PyMuPDF pdfplumber pandas
```

### 2. Tesseract OCR Kurulumu

Bu uygulama, metin tanıma için Tesseract OCR motorunu kullanır.

1.  **İndirme:** [Tesseract'ın Windows kurulum sayfasından](https://github.com/UB-Mannheim/tesseract/wiki) en güncel sürümü indirin.
2.  **Kurulum:** Kurulum sırasında, "Additional language data" (Ek dil verileri) seçeneğini işaretleyerek **Turkish** (`tur`) dil paketini de eklediğinizden emin olun.
3.  **Yol Belirtme:** `config.json` dosyanızda `tesseract_cmd_path` anahtarına Tesseract'ın `tesseract.exe` dosyasının tam yolunu belirtin. Örneğin:
    `"tesseract_cmd_path": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"`

### 3. Proje Ayarları (`config.json`)

`config.json` dosyasını açarak faturaların bulunduğu (`fatura_klasoru`) ve raporların kaydedileceği (`rapor_klasoru`) klasör isimlerini değiştirebilirsiniz. Ayrıca, **Tesseract yolunu mutlaka belirtin**.

```json
{
    "tesseract_cmd_path": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
    "klasor_yollari": {
        "fatura_klasoru": "fatura",
        "rapor_klasoru": "test_reports"
    },
    "desteklenen_formatlar": [
        ".png", ".jpg", ".jpeg", ".pdf"
    ]
}
```

### 4. Analizi Başlatma

Analiz etmek istediğiniz tüm fatura dosyalarını (`.png`, `.jpg`, `.pdf` vb.) `config.json`'da belirtilen `fatura_klasoru` içine yerleştirin (alt klasörler de taranır).

Daha sonra, aşağıdaki komutu terminalde çalıştırarak tüm analiz sürecini başlatın:

```bash
python main.py
```

Program, her çalıştırmada zaman damgalı bir koşu klasörü oluşturur. Bu klasörde detaylı raporları ve görsel hata ayıklama çıktılarını bulacaksınız:

```
test_reports/
  └── YYYYMMDD_HHMMSS/
      ├── toplu_fatura_raporu_*.json
      ├── toplu_fatura_raporu_*.csv
      ├── akilli_analiz_raporu_*.json
      ├── debug_processed_*.png
      └── analiz_hatalari.log
```

**Not:** Windows’ta konsol kodlaması hatası görürseniz `python -X utf8 main.py` komutunu kullanın.

## 📂 Proje Yapısı

```
.
├── fatura/                  # Analiz edilecek faturaların bulunduğu klasör (config.json'dan ayarlanır)
│   └── <alt_klasorler>/     # Alt klasörler de taranır
├── test_reports/            # Analiz raporlarının ve debug görsellerinin kaydedildiği klasör
│   └── YYYYMMDD_HHMMSS/     # Her koşu için oluşturulan zaman damgalı alt klasör
│       ├── ... (rapor dosyaları ve debug görselleri)
├── config/
│   ├── config.json          # Genel uygulama ayarları (Tesseract yolu, klasörler vb.)
│   └── patterns.json        # Regex desenleri ve blok atamaları
├── golden/
│   └── golden_dataset.json  # Modelin performansını değerlendirmek için kullanılan "gerçek" veri seti (isteğe bağlı)
├── fatura_analiz_motoru.py  # OCR, kelime ve blok gruplama, geometrik bölge tespiti ve veri çıkarma mantığını içeren ana motor
├── main.py                  # Projenin ana giriş noktası ve analiz akışını yönetir
└── README.md                # Bu proje hakkında genel bilgi
```

## 💡 Gelecek Vizyonu: Makine Öğrenmesi Entegrasyonu

Mevcut kural tabanlı sistem, hassas veri etiketleme kapasitesiyle, projenin bir sonraki seviyesi için sağlam bir temel oluşturmaktadır: Makine Öğrenmesi (ML) ile daha esnek ve akıllı bir yapıya geçiş.

### Aşama 1: Veri Seti Oluşturma ve Zenginleştirme

-   **Mevcut Sistemin Kullanımı:** Geliştirdiğimiz `FaturaAnalizMotoru` sistemi, yüzlerce veya binlerce faturayı işleyerek otomatik olarak etiketlenmiş bir veri seti oluşturmak için kullanılacaktır. Her fatura için çıkarılan yapılandırılmış JSON çıktısı, ML model eğitimi için temel veri kaynağımız olacaktır.
-   **Doğrulama ve Düzeltme Arayüzü (Opsiyonel):** Kullanıcıların, sistem tarafından yanlış etiketlenen verileri düzeltebileceği basit bir web arayüzü geliştirilebilir. Bu "insan-döngüde" (human-in-the-loop) yaklaşım, veri setinin kalitesini ve modelin doğruluğunu sürekli artıracaktır.
-   **Veri Formatı:** Oluşturulan veri setleri, NER (Named Entity Recognition - İsimlendirilmiş Varlık Tanıma) modellerinin eğitimi için uygun bir formata (örn. IOB2 formatı: B-SATICI, I-SATICI, B-TARIH, O) dönüştürülecektir.

### Aşama 2: Model Seçimi ve Eğitimi

-   **Model Mimarisi:** Fatura anlama görevleri için en son teknoloji sonuçlar veren LayoutLM, LiLT veya Donut gibi Transformer tabanlı, metin ve düzen (layout) bilgisini bir arada kullanan modeller seçilecektir. Bu modeller, sadece metni değil, metnin faturadaki konumunu da anladıkları için çok daha isabetli sonuçlar verirler.
-   **Eğitim Süreci:** Etiketli veri seti kullanılarak seçilen ML modeli, belirli varlıkları (fatura numarası, tarih, toplam tutar, satıcı adı vb.) tanımak üzere eğitilecektir.
-   **Fine-Tuning:** Önceden eğitilmiş (pre-trained) bir modelin, kendi veri setimizle yeniden eğitilmesi (fine-tuning), daha az veri ile daha yüksek başarı elde etmemizi sağlayacaktır.

### Aşama 3: Entegrasyon ve Hibrit Yaklaşım

-   **ML Modelinin Entegrasyonu:** Eğitilen ML modeli, mevcut kural tabanlı sisteme yeni bir "analiz motoru" olarak entegre edilecektir.
-   **Hibrit Yaklaşım:** Başlangıçta, hem kural tabanlı sistemin hem de ML modelinin sonuçları karşılaştırılabilir. Eğer ML modeli bir alanda düşük bir güven skoru verirse, kural tabanlı sistemin sonucu yedek olarak kullanılabilir. Bu hibrit yaklaşım, sistemin genel güvenilirliğini artırır ve geçiş sürecini daha pürüzsüz hale getirir.
-   **Sürekli İyileştirme:** Yeni gelen ve doğrulanan faturalar, modelin periyodik olarak yeniden eğitilmesi için kullanılarak sistemin zamanla daha da akıllı hale gelmesi sağlanacaktır.

Bu yol haritası, projenin sadece mevcut sorunları çözmekle kalmayıp, aynı zamanda endüstri standardı teknolojileri kullanarak geleceğe dönük, ölçeklenebilir ve çok daha güçlü bir yapıya kavuşmasını sağlayacaktır.