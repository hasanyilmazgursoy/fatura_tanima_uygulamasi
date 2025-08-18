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

Program, `fatura` klasöründeki tüm dosyaları tarar ve her çalıştırmada zaman damgalı bir koşu klasörü oluşturur:

```
test_reports/
  └── YYYYMMDD_HHMMSS/
      ├── toplu_fatura_raporu_*.json
      ├── toplu_fatura_raporu_*.csv
      ├── toplu_fatura_raporu_formatli_*.json
      ├── akilli_analiz_raporu_*.json
      ├── akilli_analiz_ozet_*.html     # Alan bazlı başarı ve öneriler
      ├── golden_evaluation.json/csv    # Golden set karşılaştırma (varsa)
      ├── analiz_hatalari.log
      └── debug_processed_*.png
```

Not: Windows’ta konsol kodlaması hatası görürseniz `python -X utf8 main.py` komutunu kullanın.

## 📂 Proje Yapısı

```
.
├── fatura/                  # Analiz edilecek faturaların bulunduğu klasör
│   └── test/                # Alt klasörler de taranır
├── test_reports/            # Her koşu için zaman damgalı alt klasörler
│   └── YYYYMMDD_HHMMSS/
│       ├── toplu_fatura_raporu_*.json/csv
│       ├── toplu_fatura_raporu_formatli_*.json
│       ├── akilli_analiz_raporu_*.json
│       ├── akilli_analiz_ozet_*.html
│       ├── golden_evaluation.json/csv
│       └── debug_processed_*.png
├── config.json              # Uygulama ayarları
├── fatura_regex_analiz_yeni.py  # OCR + Regex + profil kuralları + OCR fallback
├── profiles/                    # Satıcı/profil bazlı küçük kural eklentileri
│   ├── profile_base.py
│   ├── profile_a101.py
│   ├── profile_flo.py
│   └── profile_trendyol.py
├── golden/golden.json           # Golden set (beklenen alanlar) - opsiyonel
├── main.py                  # Projenin ana giriş noktası
└── README.md                # Bu dosya
```

## 🎯 İyileştirme ve Gelecek Adımlar

Bu projenin mevcut durumu sağlam bir temel oluşturmaktadır. Gelecekte yapılabilecek potansiyel iyileştirmeler şunlardır:

- **Regex Desenlerini Genişletme:** Daha fazla fatura formatını tanımak için `config/patterns.json` dosyasına desen ekleyerek sistemi kod değişmeden zenginleştirmek.
- **Konumsal Analiz:** Sadece metne değil, metnin faturadaki konumuna göre daha akıllı veri çıkarma (örneğin, "en alttaki en büyük tutar genel toplamdır" gibi).
- **Web Arayüzü:** Flask veya Django kullanarak kullanıcıların faturaları tarayıcı üzerinden yükleyebileceği bir arayüz oluşturmak.
- **Makine Öğrenmesi Modelleri:** Veri çıkarma doğruluğunu en üst seviyeye taşımak için Named Entity Recognition (NER) veya Layout-Aware (örn: LayoutLM) modelleri eğitmek.

Bu proje, fatura görüntülerinden (PDF, PNG, JPG vb.) metinleri tanımak ve bu metinleri yapılandırılmış (JSON, CSV) verilere dönüştürmek için geliştirilmiş akıllı bir OCR ve veri çıkarma sistemidir.

Sistem, Tesseract OCR motorunu, gelişmiş görüntü işleme tekniklerini (OpenCV) ve karmaşık Regex desenlerini kullanarak faturalardaki bilgileri yüksek doğrulukla çıkarmayı hedefler.

## Gelecek Vizyonu: Makine Öğrenmesi Yol Haritası

Mevcut kural tabanlı sistem, yüksek doğrulukla veri etiketleme kapasitesine sahiptir. Bu, sistemi bir sonraki seviyeye taşımak için mükemmel bir zemin hazırlar: Makine Öğrenmesi (ML) ile daha esnek ve akıllı bir yapıya geçiş.

### Aşama 1: Veri Seti Oluşturma ve Zenginleştirme
- **Mevcut Sistemin Kullanımı:** Geliştirdiğimiz `FaturaRegexAnaliz` sistemi, yüzlerce veya binlerce faturayı işleyerek otomatik olarak etiketlenmiş bir veri seti oluşturmak için kullanılacaktır. Her fatura için çıkarılan yapılandırılmış JSON çıktısı, model eğitimi için temel veri kaynağımız olacaktır.
- **Doğrulama ve Düzeltme Arayüzü:** (Opsiyonel) Kullanıcıların, sistem tarafından yanlış etiketlenen verileri düzeltebileceği basit bir web arayüzü (örn. Flask veya Django ile) geliştirilebilir. Bu, "insan-döngüde" (human-in-the-loop) bir yaklaşım sağlayarak veri setinin kalitesini en üst düzeye çıkaracaktır.
- **Veri Formatı:** Veriler, NER (Named Entity Recognition - İsimlendirilmiş Varlık Tanıma) modellerinin eğitimi için uygun bir formata dönüştürülecektir (örn. IOB2 formatı: B-SATICI, I-SATICI, B-TARIH, O).

### Aşama 2: Model Seçimi ve Eğitimi
- **Model Mimarisi:** Fatura anlama görevleri için state-of-the-art sonuçlar veren LayoutLM, LiLT veya Donut gibi Transformer tabanlı, metin ve düzen (layout) bilgisini bir arada kullanan bir model seçilecektir. Bu modeller, sadece metni değil, metnin faturadaki konumunu da anladıkları için çok daha isabetli sonuçlar verirler.
- **Eğitim Süreci:** Oluşturulan etiketli veri seti kullanılarak seçilen model, belirli varlıkları (fatura numarası, tarih, toplam tutar, satıcı adı vb.) tanımak üzere eğitilecektir.
- **Fine-Tuning:** Önceden eğitilmiş (pre-trained) bir modelin kendi veri setimizle yeniden eğitilmesi (fine-tuning), daha az veri ile daha yüksek başarı elde etmemizi sağlayacaktır.

### Aşama 3: Entegrasyon ve Hibrit Model
- **ML Modelinin Entegrasyonu:** Eğitilen model, mevcut sisteme yeni bir "analiz motoru" olarak entegre edilecektir.
- **Hibrit Yaklaşım:** Başlangıçta, hem Regex tabanlı sistemin hem de ML modelinin sonuçları karşılaştırılabilir.
  - Eğer ML modeli bir alanda düşük bir güven skoru verirse, Regex sisteminin sonucu yedek olarak kullanılabilir.
  - Bu hibrit yaklaşım, sistemin genel güvenilirliğini artırır ve geçiş sürecini daha pürüzsüz hale getirir.
- **Sürekli İyileştirme:** Yeni gelen ve doğrulanan faturalar, modelin periyodik olarak yeniden eğitilmesi için kullanılarak sistemin zamanla daha da akıllı hale gelmesi sağlanacaktır.

Bu yol haritası, projenin sadece mevcut sorunları çözmekle kalmayıp, aynı zamanda endüstri standardı teknolojileri kullanarak geleceğe dönük, ölçeklenebilir ve çok daha güçlü bir yapıya kavuşmasını sağlayacaktır.