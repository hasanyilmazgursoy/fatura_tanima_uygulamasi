import streamlit as st
import os
from fatura_regex_analiz_yeni import FaturaRegexAnaliz
from PIL import Image
from datetime import datetime

# --- Sayfa Konfigürasyonu ---
st.set_page_config(layout="wide")

# --- Başlık ---
st.title("📄 Akıllı Fatura Tanıma Sistemi")
st.markdown("Bu arayüz, yüklediğiniz fatura görsellerini veya PDF'lerini analiz ederek içindeki verileri yapılandırılmış formatta çıkarır.")

# --- Analiz Motorunu Yükleme ---
@st.cache_resource
def motoru_yukle():
    print("🚀 Analiz motoru ilk kez yükleniyor...")
    return FaturaRegexAnaliz()

analiz_sistemi = motoru_yukle()

# --- Çıktı klasörü (her oturum için zaman damgalı) ---
if 'output_dir' not in st.session_state:
    base_dir = 'test_reports'
    os.makedirs(base_dir, exist_ok=True)
    run_dir = os.path.join(base_dir, datetime.now().strftime('%Y%m%d_%H%M%S_streamlit'))
    os.makedirs(run_dir, exist_ok=True)
    st.session_state['output_dir'] = run_dir

try:
    analiz_sistemi.output_dir = st.session_state['output_dir']
except Exception:
    pass

st.sidebar.markdown(f"Çıktı klasörü: `{st.session_state['output_dir']}`")

# --- Performans Seçenekleri ---
fast_mode = st.sidebar.checkbox("Hızlı mod (ön işleme ve ek OCR denemeleri azalt)", value=True)
pdf_dpi = st.sidebar.slider("PDF DPI (kalite hızı etkiler)", min_value=150, max_value=300, value=220, step=10)
save_debug = st.sidebar.checkbox("Debug görsel kaydet", value=not fast_mode)

# Analiz motoru ayarları
setattr(analiz_sistemi, 'fast_mode', fast_mode)
setattr(analiz_sistemi, 'pdf_dpi', pdf_dpi)
setattr(analiz_sistemi, 'save_debug', save_debug)

# --- YENİ: Detaylı Sonuç Gösterme Fonksiyonu ---
def goster_detayli_sonuclar(data):
    """
    Analizden gelen yapılandırılmış veriyi, istenen formatta,
    hem bulunan hem de bulunamayan alanları gösterecek şekilde yazdırır.
    """
    
    # Teknik isimleri kullanıcı dostu etiketlere çeviren harita
    alan_map = {
        "📌 Satıcı Bilgileri": {
            "Firma": "satici_firma_unvani", "Adres": "satici_adres", "Tel": "satici_telefon",
            "E-Posta": "satici_email", "Vergi Dairesi": "satici_vergi_dairesi",
            "Vergi No": "satici_vergi_numarasi", "Web": "satici_web_sitesi",
            "Ticaret Sicil No": "satici_ticaret_sicil", "Mersis No": "satici_mersis_no"
        },
        "📌 Alıcı Bilgileri": {
            "Ad Soyad/Firma": "alici_firma_unvani", "Adres": "alici_adres", "E-Posta": "alici_email",
            "Tel": "alici_telefon", "TCKN": "alici_tckn", "Müşteri No": "alici_musteri_no"
        },
        "📌 Fatura Bilgileri": {
            "ETTN": "ettn", "Fatura Tipi": "fatura_tipi", "Fatura No": "fatura_numarasi",
            "Fatura Tarihi": "fatura_tarihi", "Son Ödeme Tarihi": "son_odeme_tarihi"
        },
        "📌 Toplamlar": {
            "Mal/Hizmet Toplam Tutarı": "mal_hizmet_toplam", "Toplam İskonto": "toplam_iskonto",
            "Vergi Hariç Tutar": "vergi_haric_tutar", "Hesaplanan KDV": "hesaplanan_kdv",
            "Vergiler Dahil Toplam Tutar": "vergiler_dahil_toplam",
            "Ödenecek Tutar": "genel_toplam"
        },
        "📌 Banka Bilgileri": {
            "IBAN": "banka_bilgileri"
        }
    }

    # Her bir kategoriyi ve alanı döngüye al
    for kategori, alanlar in alan_map.items():
        st.subheader(kategori)
        for etiket, teknik_ad in alanlar.items():
            deger = data.get(teknik_ad)
            if deger and str(deger).strip():
                st.markdown(f"**{etiket}:** `{deger}`")
            else:
                st.markdown(f"**{etiket}:** <span style='color: #FF4B4B;'>Bulunamadı</span>", unsafe_allow_html=True)
        st.markdown("---") # Kategoriler arasına ayraç koy

    # Ürün/Hizmet Bilgileri (Kalemler) için özel bölüm
    st.subheader("📌 Ürün/Hizmet Bilgileri")
    kalemler = data.get("kalemler", [])
    if not kalemler:
        st.info("Fatura kalemi bulunamadı.")
    else:
        for i, kalem in enumerate(kalemler):
            st.markdown(f"**Ürün {i+1}**")
            # Kalem içindeki her alanı etiketleyerek göster
            kalem_etiket_map = {
                "Açıklama": "aciklama", "Miktar": "miktar", "Birim Fiyat": "birim_fiyat",
                "İskonto": "iskonto", "Mal/Hizmet Tutarı": "tutar",
                "KDV Oranı (%)": "kdv_orani", "KDV Tutarı": "kdv_tutari"
            }
            for etiket, teknik_ad in kalem_etiket_map.items():
                deger = kalem.get(teknik_ad)
                if deger and str(deger).strip():
                     st.markdown(f"- **{etiket}:** `{deger}`")
                else:
                     st.markdown(f"- **{etiket}:** <span style='color: #FF4B4B;'>Bulunamadı</span>", unsafe_allow_html=True)
            if i < len(kalemler) - 1:
                st.markdown("---")

# --- Arayüz Sütunları ---
col1, col2 = st.columns(2)

with col1:
    st.header("1. Fatura Dosyasını Yükleyin")
    uploaded_file = st.file_uploader("Bir PNG, JPG veya PDF dosyası seçin", type=["png", "jpg", "jpeg", "pdf"])

    if uploaded_file is not None:
        gecici_klasor = "fatura_uploads"
        os.makedirs(gecici_klasor, exist_ok=True)
        dosya_yolu = os.path.join(gecici_klasor, uploaded_file.name)
        with open(dosya_yolu, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"'{uploaded_file.name}' başarıyla yüklendi.")

        if uploaded_file.type.startswith('image/'):
            st.image(Image.open(uploaded_file), caption="Yüklenen Fatura", use_column_width=True)
        else:
            st.info("PDF önizlemesi. Analiz, PDF'in ilk sayfasını resme çevirerek yapılır.")
            try:
                pdf_image = analiz_sistemi.resmi_yukle(dosya_yolu)
                if pdf_image is not None:
                    st.image(pdf_image[:, :, ::-1], caption="PDF'in İlk Sayfası", use_column_width=True)
            except Exception as e:
                st.warning(f"PDF önizlemesi oluşturulamadı: {e}")

with col2:
    st.header("2. Analiz Sonuçları")

    if uploaded_file is not None:
        if st.button("Faturayı Analiz Et", type="primary"):
            with st.spinner("🧠 Fatura analiz ediliyor... Lütfen bekleyin."):
                try:
                    sonuclar = analiz_sistemi.fatura_analiz_et(dosya_yolu, gorsellestir=False)
                    if "hata" in sonuclar:
                        st.error(f"Analiz Başarısız: {sonuclar['hata']}")
                    else:
                        structured_data = sonuclar.get("structured", {})
                        
                        # --- YENİ: Formatlı Gösterim ---
                        goster_detayli_sonuclar(structured_data)

                        # --- ESKİ GÖRÜNÜMLERİ AÇILIR-KAPANIR BÖLÜMLERE TAŞIYALIM ---
                        with st.expander("🔍 Diğer Detayları Gör"):
                            st.subheader("📈 OCR İstatistikleri")
                            stats = sonuclar.get("ocr_istatistikleri", {})
                            st.markdown(f"- **Ortalama Güven Skoru:** `{stats.get('ortalama_guven_skoru', 'N/A')}`")
                            st.markdown(f"- **Okunan Kelime Sayısı:** `{stats.get('gecerli_kelime', 'N/A')}`")

                            st.subheader("📝 Ham Metin")
                            st.text_area("OCR'dan Çıkarılan Ham Metin", stats.get('ham_metin', 'Metin çıkarılamadı.'), height=150)

                            st.subheader("⚙️ Ham JSON Çıktısı")
                            st.json(structured_data)

                        # Debug işlenmiş görseli göster (varsa)
                        debug_name = f"debug_processed_{os.path.splitext(os.path.basename(dosya_yolu))[0]}.png"
                        debug_path = os.path.join(st.session_state['output_dir'], debug_name)
                        if os.path.exists(debug_path):
                            st.image(debug_path, caption="İşlenmiş Görsel (Debug)", use_column_width=True)

                except Exception as e:
                    st.error(f"Analiz sırasında beklenmedik bir hata oluştu: {e}")
            os.remove(dosya_yolu)
    else:
        st.info("Analiz sonuçlarını görmek için lütfen bir fatura dosyası yükleyin.")
