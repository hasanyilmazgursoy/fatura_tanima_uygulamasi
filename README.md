# 🧾 Akıllı Fatura Tanıma ve Veri Çıkarma Sistemi

Bu proje, Türk e-faturalarından yapılandırılmış verileri (JSON, CSV) otomatik olarak çıkaran gelişmiş bir Python uygulamasıdır. Hibrit OCR yaklaşımı, dinamik bölgeleme ve akıllı veri temizleme özellikleriyle yüksek doğruluk oranı hedefler.

## ✨ Özellikler

- **Hibrit Metin Çıkarımı**: pdfplumber + Tesseract OCR fallback ile maksimum veri yakalama
- **Dinamik Bölgeleme**: Anahtar kelime tabanlı akıllı alan tespiti (sabit koordinat yerine)
- **Görüntü Ön İşleme**: Otomatik temizlik, gürültü azaltma ve eğrilik düzeltme
- **Çoklu Format Desteği**: PDF, PNG, JPG, TIFF, BMP
- **Streamlit Arayüzü**: Dosya yükleme, debug görseli, düzenlenebilir sonuçlar
- **Kapsamlı Raporlama**: JSON/CSV çıktı, debug görselleri, akıllı analiz raporları
- **Esnek Yapılandırma**: patterns.json ile regex desenleri, config.json ile ayarlar

## 🚀 Hızlı Başlangıç

### Gereksinimler
- Python 3.8+
- Tesseract OCR (Türkçe dil paketi ile)
- Windows/Linux/macOS

### Kurulum

1. **Depoyu klonlayın:**
```bash
git clone https://github.com/hasanyilmazgursoy/fatura_tanima_uygulamasi.git
cd fatura_tanima_uygulamasi
```

2. **Bağımlılıkları yükleyin:**
```bash
pip install -r requirements.txt
```

3. **Tesseract OCR kurun:**
   - **Windows**: [Tesseract İndirme](https://github.com/UB-Mannheim/tesseract/wiki)
   - **Linux**: `sudo apt-get install tesseract-ocr tesseract-ocr-tur`
   - **macOS**: `brew install tesseract tesseract-lang`

4. **Yapılandırma:**
```json
{
    "tesseract_cmd_path": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
    "klasor_yollari": {
        "fatura_klasoru": "ornek_faturalar",
        "rapor_klasoru": "test_reports"
    }
}
```
`config.json` dosyasını `config/config.sample.json` içeriğini temel alarak oluşturup kendi ortamınıza göre düzenleyin.

## 📖 Kullanım

### Streamlit Arayüzü (Önerilen)
```bash
streamlit run app.py
```
- Tarayıcıda dosya yükleyin
- "Faturayı Analiz Et" butonuna tıklayın
- Debug görselini inceleyin
- Sonuçları düzenleyip JSON/CSV indirin

### Komut Satırı
```bash
# Tek dosya analizi
python main.py

# Toplu değerlendirme
python degerlendir.py
```
Windows PowerShell'de UTF-8 gerekirse: `python -X utf8 main.py`

## 🖼️ Ekran Görüntüleri

### Streamlit Arayüzü
![Streamlit Arayüzü](docs/streamlit_interface.png)

### Debug Görseli
![Debug Görseli](docs/debug_visualization.png)

### Analiz Sonuçları
![Analiz Sonuçları](docs/analysis_results.png)

Not: Bu görseller placeholder'dır. Kendi ekran görüntülerinizi `docs/` klasörüne ekleyip bağlantıları güncelleyebilirsiniz.

## 🛠️ Teknolojiler

- **OCR & Metin İşleme**: Tesseract, pdfplumber, PyMuPDF
- **Görüntü İşleme**: OpenCV, NumPy
- **Web Arayüzü**: Streamlit
- **Veri İşleme**: Pandas, JSON, CSV
- **Regex & Pattern Matching**: Python re, custom patterns
- **Loglama & Hata Yönetimi**: Python logging

## 📁 Proje Yapısı

```
fatura_tanima_uygulamasi/
├── 📄 app.py                 # Streamlit web arayüzü
├── 📄 main.py                # CLI ana giriş noktası
├── 📄 fatura_analiz_motoru.py # Ana analiz motoru
├── 📄 degerlendir.py         # Toplu değerlendirme
├── 📄 utils.py               # Yardımcı fonksiyonlar
├── 📁 config/
│   ├── patterns.json         # Regex desenleri
│   └── golden_dataset.json   # Test veri seti
├── 📁 test_reports/          # Analiz çıktıları (gitignore)
├── 📄 requirements.txt       # Python bağımlılıkları
└── 📄 README.md              # Bu dosya
```

## 🔧 Yapılandırma

### patterns.json
Regex desenlerini ve alan eşleştirmelerini içerir:
```json
{
    "fatura_no": {
        "desen": "(?:Fatura No|FATURA NO)\\s*([A-Z0-9]+)",
        "blok": "fatura_bilgileri"
    }
}
```

### Görüntü Ön İşleme Presetleri
- **auto**: Otomatik heuristik seçim
- **scan**: Tarama optimizasyonu (gürültü azaltma)
- **skew**: Eğrilik düzeltme
- **clean**: Temiz PDF optimizasyonu

## 📊 Çıktı Formatları

### JSON Çıktısı
```json
{
    "fatura_no": "SND2024000000004",
    "fatura_tarihi": "15-03-2024",
    "ettn": "27d06435-9c77-4a8f-8148-828bb7b63e84",
    "satici_unvan": "NETCOM",
    "alici_unvan": "KOÇAK PIRLANTA",
    "odenecek_tutar": "109999.99",
    "urun_kalemleri": [...]
}
```

## 🧪 Test ve Değerlendirme

### Golden Dataset
```bash
# config/golden_dataset.json ile doğruluk testi
python degerlendir.py
```

### Akıllı Analiz
- Alan bazlı başarı oranları
- OCR kalite analizi
- Pattern matching performansı
- İyileştirme önerileri

Not: Birim test altyapısı eklenecektir. Test dosyaları eklendikçe `pytest` ile çalıştırma talimatları güncellenecektir.

## 🐛 Sorun Giderme

| Sorun | Çözüm |
|-------|-------|
| Tesseract bulunamadı | `config.json`'da yol kontrolü |
| Düşük OCR kalitesi | Görüntü ön işleme presetini değiştirin |
| Yanlış bölgeleme | patterns.json'da anchor kelimeleri güncelleyin |
| Boş alanlar | Regex desenlerini kontrol edin |

## 🔐 Gizlilik ve Veri

- Gerçek faturalar kişisel/kurumsal veriler içerir; repoya yüklemeyin.
- Örnek verileri anonimleştirerek paylaşın.
- `test_reports/`, `temp_uploads/`, örnek veri klasörleri `.gitignore` ile hariç tutulmuştur.

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın

Ayrıntılı rehber için bkz. [CONTRIBUTING.md](CONTRIBUTING.md).

### Geliştirme Kurulumu
```bash
pip install -r requirements-dev.txt  # Geliştirme bağımlılıkları
pytest tests/                        # Testleri çalıştır
```

## 📄 Lisans

Bu proje MIT Lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 👤 İletişim

- **Geliştirici**: Hasan Yılmaz Gürsoy
- **GitHub**: [@hasanyilmazgursoy](https://github.com/hasanyilmazgursoy)
- **LinkedIn**: [Hasan Yılmaz Gürsoy](https://www.linkedin.com/in/hasan-y%C4%B1lmaz-g%C3%BCrsoy-a900b9229/)
- **Proje Linki**: [fatura_tanima_uygulamasi](https://github.com/hasanyilmazgursoy/fatura_tanima_uygulamasi)

---

⭐ Bu projeyi beğendiyseniz yıldız vermeyi unutmayın!