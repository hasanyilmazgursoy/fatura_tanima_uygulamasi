# 🧾 Akıllı Fatura Tanıma Sistemi (Regex + AI)

Bu proje, fatura görsellerinden ve PDF dosyalarından yapılandırılmış veri çıkarmak için **Kural Tabanlı (Regex)** ve **Yapay Zeka (LayoutLM Modeli)** yaklaşımlarını birleştiren hibrit bir sistemdir.

## ✨ Temel Özellikler

- **Hibrit Analiz Motoru:** Yüksek doğruluk için hem Regex'in güvenilirliğini hem de LayoutLM modelinin metin ve sayfa düzeni anlama yeteneğini birleştirir.
- **AI Destekli Veri Çıkarma:** Metnin sadece ne olduğunu değil, aynı zamanda faturanın neresinde olduğunu da anlayan, özel olarak eğitilmiş bir **LayoutLM** modeli kullanır.
- **Güvenilir Kural Tabanlı Sistem:** Onlarca farklı fatura alanını tanımak için geliştirilmiş Regex desenleri içerir ve AI modelinin sonuçlarının güvencesi olarak çalışır.
- **Geniş Format Desteği:** `.pdf`, `.png`, `.jpg` gibi yaygın fatura formatlarını doğrudan işleyebilir.
- **İnteraktif Web Arayüzü:** Tekli faturaları kolayca analiz etmek ve sonuçları anında görmek için `Streamlit` tabanlı bir arayüz sunar.
- **Toplu İşlem Yeteneği:** Komut satırından binlerce faturayı paralel olarak analiz edebilir.
- **Gelişmiş Raporlama:** Analiz sonuçlarını `JSON` ve `CSV` formatlarında sunar, alan bazlı başarı özetleri oluşturur ve `golden set` ile model performansını değerlendirir.
- **Model Eğitimi Altyapısı:** Kendi veri setinizle LayoutLM modelini eğitmek için gerekli tüm script'leri (`layoutlm_dataset_converter.py`, `layoutlm_trainer.py`) içerir.

## 🛠️ Teknoloji Mimarisi

- **Programlama Dili:** Python
- **OCR Motoru:** Tesseract
- **Görüntü İşleme:** OpenCV, PyMuPDF
- **AI/ML:** PyTorch, Hugging Face Transformers (LayoutLM)
- **Web Arayüzü:** Streamlit

## 🚀 Kurulum

#### 1. Gerekli Kütüphaneler

Projeyi çalıştırmadan önce `requirements.txt` dosyasındaki kütüphaneleri yükleyin:

```bash
pip install -r requirements.txt
```

*Not: Henüz bir `requirements.txt` dosyası yoksa, temel kütüphaneler şunlardır: `opencv-python`, `pytesseract`, `numpy`, `PyMuPDF`, `pdf2image`, `streamlit`, `torch`, `transformers`, `datasets`, `seqeval`.*

#### 2. Tesseract OCR Kurulumu

1.  **İndirme:** [Tesseract'ın Windows kurulum sayfasından](https://github.com/UB-Mannheim/tesseract/wiki) güncel sürümü indirin.
2.  **Kurulum:** Kurulum sırasında, "Additional language data" (Ek dil verileri) seçeneğini işaretleyerek **Turkish** (`tur`) dil paketini eklediğinizden emin olun.
3.  **Sistem Yolu (PATH):** Tesseract'ı kurduğunuz dizini (genellikle `C:\Program Files\Tesseract-OCR`) sisteminizin `PATH` ortam değişkenine ekleyin.

## 📖 Nasıl Kullanılır?

Projenin üç temel kullanım senaryosu vardır:

### 1. İnteraktif Analiz (Tek Dosya İçin Web Arayüzü)

Kullanımı en kolay yöntemdir. Aşağıdaki komutu çalıştırın ve tarayıcıda açılan arayüzden faturalarınızı yükleyin.

```bash
streamlit run app.py
```

### 2. Toplu Analiz (Komut Satırından)

Binlerce faturayı tek seferde analiz etmek için kullanılır.

1.  **Faturaları Hazırlama:** Analiz edilecek tüm fatura dosyalarını (`.pdf`, `.png` vb.) ana dizindeki `fatura` klasörüne kopyalayın.
2.  **Analizi Başlatma:**
    - **Sadece Regex ile analiz için:**
      ```bash
      python main.py regex
      ```
    - **AI Destekli Hibrit Analiz için (Önerilen):**
      ```bash
      python main.py hibrit
      ```

Tüm raporlar, `test_reports/` altında zaman damgalı yeni bir klasör içinde oluşturulur.

### 3. AI Modelini Eğitme (İleri Seviye)

1.  **Veri Seti Hazırlama:** Etiketlenmiş verilerinizi `layoutlm_dataset_converter.py` script'i ile modelin anlayacağı formata dönüştürün.
2.  **Model Eğitimi:** `layoutlm_trainer.py` script'ini çalıştırarak `layoutlm_quick_model` klasörüne yeni modelinizi eğitin.

## 📂 Proje Yapısı

```
.
├── fatura/                  # Analiz edilecek faturalar
├── test_reports/            # Analiz raporları ve loglar
├── layoutlm_dataset/        # Model eğitimi için hazırlanan veri seti
├── layoutlm_quick_model/    # Eğitilmiş AI modeli dosyaları
├── profiles/                # Satıcı bazlı özel kurallar
├── config.json              # Ana yapılandırma dosyası
├── app.py                   # Streamlit web arayüzü
├── main.py                  # Toplu analiz için ana giriş noktası
├── fatura_regex_analiz_yeni.py # Kural tabanlı analiz motoru
├── fatura_hibrit_analiz.py  # AI ve Regex'i birleştiren hibrit motor
├── layoutlm_trainer.py      # AI modelini eğiten script
└── README.md                # Bu dosya
```