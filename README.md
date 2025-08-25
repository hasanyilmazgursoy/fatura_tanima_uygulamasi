# 🧾 Akıllı Fatura Tanıma ve Veri Çıkarma Sistemi

Bu proje, fatura görsellerinden ve PDF dosyalarından otomatik olarak yapılandırılmış veri çıkaran gelişmiş bir sistemdir. Sistem, **kural tabanlı (Regex)** ve **yapay zeka tabanlı (LayoutLMv3)** yaklaşımları birleştiren **hibrit** bir model kullanarak yüksek doğruluk ve esneklik sunar.

Proje, hem toplu fatura işleme için bir **komut satırı arayüzü (CLI)** hem de tekil faturaları analiz etmek için interaktif bir **web arayüzü (Streamlit)** içerir.

## ✨ Ana Özellikler

- **Hibrit Analiz Motoru**: Güvenilir ve hızlı sonuçlar için kural tabanlı **Regex** ile esnek ve öğrenen **LayoutLMv3** modelini birleştirir. AI tahminleri belirli bir güven eşiğinin altındaysa Regex sonucunu yedek olarak kullanır.
- **Geniş Format Desteği**: `.pdf`, `.png`, `.jpg`, `.jpeg` gibi yaygın fatura formatlarını sorunsuzca işler.
- **Paralel İşleme**: Çok sayıda faturayı aynı anda işleyerek analiz sürecini önemli ölçüde hızlandırır.
- **İnteraktif Web Arayüzü**: Kullanıcıların faturaları kolayca yükleyip sonuçları anında görebileceği `Streamlit` tabanlı bir arayüz sunar.
- **Satıcıya Özel Profiller**: A101, FLO, Trendyol gibi farklı satıcıların fatura formatlarına özel kurallar uygulayarak veri çıkarma doğruluğunu artırır.
- **Kapsamlı Raporlama**: Analiz sonuçlarını detaylı `JSON`, özet `CSV` ve okunabilir `HTML` formatlarında raporlar. Ayrıca "Golden Set"e karşı otomatik doğruluk değerlendirmesi yapar.
- **Model Eğitimi ve Entegrasyonu**: Kendi fatura verilerinizle LayoutLMv3 modelini eğitmek ve sisteme entegre etmek için gerekli tüm betikleri içerir.
- **Gelişmiş Görüntü İşleme**: OCR (Tesseract) performansını artırmak için eğiklik düzeltme, gürültü azaltma ve kontrast iyileştirme gibi OpenCV tabanlı ön işleme adımları uygular.

## 🏗️ Proje Mimarisi

Proje, faturaları ham veriden yapılandırılmış bilgiye dönüştüren modüler bir boru hattı (pipeline) üzerine kurulmuştur:

1.  **Veri Girişi**: `fatura/` klasöründeki PDF veya resim dosyaları.
2.  **Veri Ön İşleme**:
    - `pdf_to_png_converter.py`: PDF'leri analiz için PNG formatına dönüştürür.
    - `convert_labelstudio_to_golden.py`: Label Studio'dan gelen etiketlenmiş verileri test için "golden set" formatına çevirir.
    - `layoutlm_dataset_converter.py`: Label Studio verilerini LayoutLM modeli eğitimi için `arrow` formatına dönüştürür.
3.  **Analiz Motorları**:
    - **Regex Motoru (`fatura_regex_analiz_yeni.py`)**: Görüntü işleme, Tesseract ile OCR ve kural tabanlı veri çıkarma işlemlerini yürütür.
    - **AI Motoru (`fatura_hibrit_analiz.py` içindeki `LayoutLMPredictor`)**: Önceden eğitilmiş LayoutLMv3 modelini kullanarak metin ve konum bilgisinden etiketleri tahmin eder.
4.  **Hibrit Birleştirme (`fatura_hibrit_analiz.py`)**: Her iki motordan gelen sonuçları birleştirerek en güvenilir çıktıyı oluşturur.
5.  **Çıktı ve Raporlama**:
    - Analiz sonuçları `test_reports/` klasörüne zaman damgalı alt klasörler halinde kaydedilir.
    - Raporlar JSON, CSV ve HTML formatlarında oluşturulur.

## 🚀 Kurulum

#### 1. Gerekli Kütüphaneler

Projeyi çalıştırmadan önce `requirements.txt` dosyasındaki bağımlılıkları yükleyin:

```bash
pip install -r requirements.txt
```

#### 2. Tesseract OCR Kurulumu

Bu uygulama, metin tanıma için Tesseract OCR motorunu kullanır.

1.  **İndirme:** [Tesseract'ın Windows kurulum sayfasından](https://github.com/UB-Mannheim/tesseract/wiki) en güncel sürümü indirin.
2.  **Kurulum:** Kurulum sırasında, "Additional language data" (Ek dil verileri) seçeneğini işaretleyerek **Turkish** (`tur`) dil paketini de eklediğinizden emin olun.
3.  **Sistem Yolu (PATH):** Tesseract'ı kurduğunuz dizini (genellikle `C:\Program Files\Tesseract-OCR`) sisteminizin `PATH` ortam değişkenine ekleyin.

### Veri ve Model Dosyaları

**Önemli Not:** Bu depoya, kullanıcıya özel ve büyük boyutlu oldukları için aşağıdaki dosyalar ve klasörler dahil **edilmemiştir**:

-   **`fatura/`, `fatura_png/`, `fatura_uploads/`**: Kendi fatura dosyalarınızı bu klasörlere yerleştirerek analiz yapabilirsiniz.
-   **`dataset/`**: Kendi etiketlenmiş verilerinizi (Label Studio çıktısı) bu klasöre koymalısınız.
-   **`layoutlm_quick_model/`**: Eğitilmiş yapay zeka modeli. Hibrit analizi kullanmak için `layoutlm_trainer.py` betiğini çalıştırarak kendi modelinizi eğitmeniz gerekmektedir.

Projenin klasör yapısı, bu klasörlerin yerini göstermek amacıyla boş `.gitkeep` dosyaları ile korunmaktadır.

## 📖 Nasıl Kullanılır?

Projenin iki ana kullanım modu bulunmaktadır: Komut Satırı Arayüzü (Toplu Analiz) ve Web Arayüzü (Tekil Analiz).

### 1. Web Arayüzü (Önerilen Başlangıç)

Kullanıcı dostu arayüz ile tekil faturaları hızlıca analiz etmek için:

```bash
streamlit run app.py
```

Bu komut, tarayıcınızda fatura yükleyip sonuçları anında görebileceğiniz bir web sayfası açacaktır.

### 2. Komut Satırı Arayüzü (Toplu Analiz)

`fatura/` klasöründeki tüm faturaları toplu olarak analiz etmek için `main.py` betiğini kullanın.

#### Adım 1: Faturaları Hazırlama

Analiz etmek istediğiniz tüm fatura dosyalarını (`.png`, `.jpg`, `.pdf` vb.) proje ana dizinindeki `fatura` klasörünün içine koyun.

#### Adım 2: Analizi Başlatma

- **Hibrit Mod (Regex + AI - Varsayılan)**:
  ```bash
  python main.py hibrit
  ```
- **Sadece Regex Modu**:
  ```bash
  python main.py regex
  ```

Program, `fatura` klasöründeki tüm dosyaları tarayacak ve sonuçları `test_reports/` altında zaman damgalı yeni bir klasöre kaydedecektir.

## 🧠 Makine Öğrenmesi Modeli Eğitimi

Kendi veri setinizle LayoutLMv3 modelini eğitmek için aşağıdaki adımları izleyin:

1.  **Veri Etiketleme**: Faturalarınızı `fatura_png/` klasörüne PNG olarak ekleyin ve Label Studio gibi bir etiketleme aracıyla etiketleyin. `label_studio_config.xml` dosyasını Label Studio projenize import ederek başlayabilirsiniz.
2.  **Label Studio Export**: Etiketlediğiniz verileri Label Studio'dan `JSON` formatında dışa aktırın ve `dataset/` klasörüne kaydedin.
3.  **Veri Setini Dönüştürme**: Label Studio formatındaki verileri LayoutLM formatına dönüştürün:
    ```bash
    python layoutlm_dataset_converter.py
    ```
    Bu betik, `layoutlm_dataset/` klasörünü oluşturacaktır.
4.  **Modeli Eğitme**: Dönüştürülmüş veri seti ile modeli eğitin:
    ```bash
    python layoutlm_trainer.py
    ```
    Eğitim tamamlandığında, en iyi model `layoutlm_quick_model/` dizinine kaydedilecektir. Hibrit analiz sistemi bu modeli otomatik olarak kullanacaktır.

## 📂 Proje Yapısı

```
.
├── app.py                     # Streamlit web arayüzü
├── main.py                    # Komut satırı giriş noktası (toplu analiz)
├── fatura/                    # Analiz edilecek faturaların bulunduğu klasör
├── fatura_png/                # PDF'den dönüştürülen PNG dosyaları
├── fatura_hibrit_analiz.py    # Regex ve AI motorlarını birleştiren hibrit sistem
├── fatura_regex_analiz_yeni.py# Sadece kural tabanlı (Regex) analiz motoru
├── layoutlm_trainer.py        # LayoutLMv3 modelini eğitmek için kullanılan betik
├── layoutlm_quick_model/      # Eğitilmiş ve kullanıma hazır LayoutLMv3 modeli
├── layoutlm_dataset/          # Model eğitimi için hazırlanmış veri seti
├── layoutlm_dataset_converter.py # Label Studio verilerini LayoutLM formatına dönüştürür
├── profiles/                  # Satıcıya özel analiz kuralları
├── dataset/                   # Label Studio'dan dışa aktarılan ham etiket verileri
├── golden/                    # Test için kullanılan "doğru" etiketlenmiş veri setleri
├── config.json                # Genel uygulama ayarları
├── config/patterns.json       # Regex desenleri
├── test_reports/              # Analiz raporlarının ve çıktılarının kaydedildiği klasör
├── requirements.txt           # Gerekli Python kütüphaneleri
└── README.md                  # Bu dosya
```