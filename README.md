## 🧾 Akıllı Fatura Tanıma ve Veri Çıkarma Sistemi

Bu proje, fatura görselleri ve PDF dosyalarından yapılandırılmış verileri (JSON, CSV) otomatik olarak çıkaran bir Python uygulamasıdır. Mevcut sürüm; Tesseract OCR, kural tabanlı alan çıkarımı ve basit tablo yaklaşımlarıyla çalışır.

### Özellikler
- Çoklu format: PDF, PNG, JPG
- Alan çıkarımı: Fatura No, Tarih, ETTN, tutarlar, satıcı/alıcı vb.
- Tablo/kalem çıkarımı: `pdfplumber` ve `pandas` ile ürün/hizmet kalemleri
- Raporlama: JSON ve CSV çıktı, debug görselleri
- Esnek yapılandırma: `config.json` ile klasör ve Tesseract yolu

---

## Kurulum

1) Python 3.11 önerilir. Bağımlılıkları kurun:
```bash
pip install -r requirements.txt
```

2) Tesseract OCR’ı kurun (Windows): `C:\\Program Files\\Tesseract-OCR\\tesseract.exe`
- İndirme: https://github.com/UB-Mannheim/tesseract/wiki
- Kurulumda Turkish (tur) dil paketini seçin.

3) `config.json` yapılandırması (örnek):
```json
{
    "tesseract_cmd_path": "C\\\\Program Files\\\\Tesseract-OCR\\\\tesseract.exe",
    "klasor_yollari": {
        "fatura_klasoru": "27.08.2025_Gelen Fatura (1)",
        "rapor_klasoru": "test_reports"
    },
    "parallel_workers": 0,
    "desteklenen_formatlar": [".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".pdf"]
}
```

---

## Çalıştırma

### Komut satırı (tek dosya örnek akış)
```bash
python main.py
```
Çıktılar `test_reports/` altındaki zaman damgalı klasöre ve `test_reports/debug_images` dizinine kaydedilir.

### Streamlit arayüzü
```bash
streamlit run app.py
```
Tarayıcıda dosya yükleyip “Faturayı Analiz Et” ile sonuçları görüntüleyin.

Not (Windows): UTF-8 konsol gerekirse `python -X utf8 main.py`.

---

## Çıktılar
- `toplu_fatura_raporu_*.csv`/`*.json`: Alan bazlı yapılandırılmış veriler
- `akilli_analiz_raporu_*.json` ve `akilli_analiz_ozet_*.html`: Toplu test analizi (varsa)
- `debug_processed_*.png`: İşlenen faturalarda tespit edilen alanlar
- `analiz_hatalari.log`: Hataların özet kaydı

---

## Proje Yapısı (özet)
```
.
├── config/
│   ├── config.json
│   └── patterns.json
├── golden/
│   └── golden.json (opsiyonel)
├── main.py
├── app.py
├── fatura_analiz_motoru.py
├── test_reports/ (çıktı)
├── requirements.txt
└── README.md
```

---

## Sorun Giderme
- Tesseract yolu bulunamadı: `config.json` içindeki `tesseract_cmd_path`’i kontrol edin.
- OCR kalitesi düşük: Kaynağın çözünürlüğünü artırın; görüntü PDF’den direkt çıkarıldıysa DPI yükseltin.
- CSV/JSON alanları boş: İlgili fatura formatı için `patterns.json` desenlerini gözden geçirin.

---

## Lisans
Lisans dosyası (LICENSE) eklenecektir. Tercihiniz belirtmediyseniz MIT lisansı önerilir.