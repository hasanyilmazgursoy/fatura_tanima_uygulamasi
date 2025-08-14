# 🧾 Akıllı Fatura Tanıma Uygulaması

Bu proje, **OCR (Optik Karakter Tanıma)** ve **Düzenli İfadeler (Regex)** teknolojilerini kullanarak fatura görsellerinden ve PDF dosyalarından otomatik olarak yapılandırılmış veri çıkaran bir Python uygulamasıdır.

## ✨ Ana Özellikler

- **Geniş Format Desteği:** Hem resim dosyalarını (`.png`, `.jpg` vb.) hem de `.pdf` formatındaki faturaları doğrudan işleyebilir.
- **Esnek Yapılandırma:** Tüm ayarlar (dosya yolları, formatlar) `config.json` dosyası üzerinden kolayca yönetilebilir.
- **Kapsamlı Veri Çıkarma:** Fatura No, Tarih, Tutar, VKN, TCKN, Adres gibi onlarca farklı alanı tanımak için gelişmiş Regex desenleri kullanır.
- **Çift Raporlama Sistemi:** Analiz sonuçlarını hem makine tarafından okunabilir `JSON` hem de Excel gibi programlarla uyumlu `CSV` formatında sunar.
- **Gelişmiş Hata Yönetimi:** Analiz sırasında oluşan hataları `analiz_hatalari.log` dosyasına kaydederek sorun takibini kolaylaştırır.
- **Yüksek Başarılı OCR:** Tesseract motoru, Türkçe ve İngilizce dilleri için optimize edilmiştir.

## 🚀 Kurulum

#### 1. Gerekli Kütüphaneler

Projeyi çalıştırmak için aşağıdaki Python kütüphanelerini yükleyin:

```bash
pip install opencv-python pytesseract numpy PyMuPDF pdf2image
```

#### 2. Tesseract OCR Kurulumu

Bu uygulama, metin tanıma için Tesseract OCR motorunu kullanır.

1.  **İndirme:** [Tesseract'ın Windows kurulum sayfasından](https://github.com/UB-Mannheim/tesseract/wiki) en güncel sürümü indirin.
2.  **Kurulum:** Kurulum sırasında, "Additional language data" (Ek dil verileri) seçeneğini işaretleyerek **Turkish** (`tur`) dil paketini de eklediğinizden emin olun.
3.  **Sistem Yolu (PATH):** Tesseract'ı kurduğunuz dizini (genellikle `C:\Program Files\Tesseract-OCR`) sisteminizin `PATH` ortam değişkenine ekleyin. Bu, programın Tesseract'ı komut satırından bulabilmesi için gereklidir.

## 📖 Nasıl Kullanılır?

Projenin kullanımı oldukça basittir.

#### 1. Faturaları Hazırlama

Analiz etmek istediğiniz tüm fatura dosyalarını (`.png`, `.jpg`, `.pdf` vb.) proje ana dizinindeki `fatura` klasörünün içine veya bu klasörün altındaki herhangi bir klasöre koyun.

#### 2. Ayarları Gözden Geçirme (İsteğe Bağlı)

`config.json` dosyasını açarak faturaların bulunduğu veya raporların kaydedileceği klasör isimlerini değiştirebilirsiniz.

```json
{
    "klasor_yollari": {
        "fatura_klasoru": "fatura",
        "rapor_klasoru": "test_reports"
    },
    "desteklenen_formatlar": [
        ".png", ".jpg", ".jpeg", ".pdf"
    ]
}
```

#### 3. Analizi Başlatma

Aşağıdaki komutu terminalde çalıştırarak tüm analiz sürecini başlatın:

```bash
python main.py
```

Program, `fatura` klasöründeki tüm dosyaları tarayacak, analiz edecek ve sonuçları `test_reports` klasörüne `toplu_fatura_raporu_....json` ve `toplu_fatura_raporu_....csv` olarak kaydedecektir. Oluşan hatalar ise aynı klasördeki `analiz_hatalari.log` dosyasına yazılacaktır.

## 📂 Proje Yapısı

```
.
├── fatura/                  # Analiz edilecek faturaların bulunduğu klasör
│   └── test/                # Alt klasörler de taranır
├── test_reports/            # Analiz sonrası raporların kaydedildiği klasör
│   ├── analiz_hatalari.log
│   ├── toplu_fatura_raporu_....csv
│   └── toplu_fatura_raporu_....json
├── config.json              # Uygulama ayarları
├── fatura_regex_analiz_yeni.py  # Ana OCR ve Regex analiz mantığı
├── main.py                  # Projenin ana giriş noktası
└── README.md                # Bu dosya
```

## 🎯 İyileştirme ve Gelecek Adımlar

Bu projenin mevcut durumu sağlam bir temel oluşturmaktadır. Gelecekte yapılabilecek potansiyel iyileştirmeler şunlardır:

- **Regex Desenlerini Genişletme:** Daha fazla fatura formatını tanımak için `fatura_regex_analiz_yeni.py` dosyasındaki desenleri zenginleştirmek.
- **Konumsal Analiz:** Sadece metne değil, metnin faturadaki konumuna göre daha akıllı veri çıkarma (örneğin, "en alttaki en büyük tutar genel toplamdır" gibi).
- **Web Arayüzü:** Flask veya Django kullanarak kullanıcıların faturaları tarayıcı üzerinden yükleyebileceği bir arayüz oluşturmak.
- **Makine Öğrenmesi Modelleri:** Veri çıkarma doğruluğunu en üst seviyeye taşımak için Named Entity Recognition (NER) veya Layout-Aware (örn: LayoutLM) modelleri eğitmek.
