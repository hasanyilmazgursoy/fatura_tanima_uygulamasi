import streamlit as st
import os
import json
import pandas as pd
import io
from fatura_analiz_motoru import FaturaAnalizMotoru

# Geçici dosyaların kaydedileceği klasör
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

st.set_page_config(layout="wide", page_title="Akıllı Fatura Tanıma Sistemi")

def display_results(results: dict, source_path: str | None = None):
    """Analiz sonuçlarını Streamlit arayüzünde gösterir."""
    
    st.subheader("Çıkarılan Yapılandırılmış Veri")
    
    yapilandirilmis_veri = results.get("yapilandirilmis_veri", {})
    
    if not yapilandirilmis_veri:
        st.warning("Bu dosyadan yapılandırılmış veri çıkarılamadı.")
        return

    # Önemli alanları ve diğerlerini ayır
    onemli_alanlar = [
        'fatura_no', 'fatura_tarihi', 'satici_unvan', 'alici_unvan', 
        'odenecek_tutar', 'mal_hizmet_toplam_tutari', 'ettn'
    ]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("🔹 Temel Fatura Bilgileri")
        for alan in onemli_alanlar:
            deger = yapilandirilmis_veri.get(alan)
            if deger:
                st.metric(label=alan.replace('_', ' ').title(), value=str(deger))

    with col2:
        st.info("🔸 Diğer Detaylar")
        diger_veriler = {k: v for k, v in yapilandirilmis_veri.items() if k not in onemli_alanlar and k != 'urun_kalemleri'}
        if diger_veriler:
            st.json(diger_veriler)
        else:
            st.write("Diğer detaylar bulunamadı.")

    st.divider()

    # Ürün kalemlerini göster
    st.subheader("Ürün/Hizmet Kalemleri")
    urun_kalemleri = yapilandirilmis_veri.get("urun_kalemleri", [])
    if urun_kalemleri:
        try:
            df = pd.DataFrame(urun_kalemleri)
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Ürün kalemleri tablo olarak gösterilirken bir hata oluştu: {e}")
            st.json(urun_kalemleri)
    else:
        st.warning("Dosyadan ürün/hizmet kalemi çıkarılamadı.")

    # Debug görselini (varsa) göster
    with st.expander("Debug Görselini Göster (Bölge İşaretleri)"):
        debug_img_path = None
        try:
            if source_path:
                base = os.path.splitext(os.path.basename(source_path))[0]
                candidate = os.path.join("test_reports", "debug_images", f"debug_{base}.png")
                if os.path.exists(candidate):
                    debug_img_path = candidate
        except Exception:
            debug_img_path = None
        if debug_img_path:
            st.image(debug_img_path, caption=os.path.basename(debug_img_path), use_column_width=True)
        else:
            st.write("Debug görseli bulunamadı.")

    # Ham metni genişletilebilir bir alanda göster
    with st.expander("OCR'dan Çıkarılan Ham Metni Gör"):
        st.text_area("Ham Metin", results.get("ham_metin", "Ham metin bulunamadı."), height=300)

    st.divider()

    # Verileri düzenleme ve indirme
    st.subheader("Verileri Düzelt ve İndir")
    duzenlenmis = {}
    if yapilandirilmis_veri:
        editable_fields = {k: v for k, v in yapilandirilmis_veri.items() if k != 'urun_kalemleri'}
        cols = st.columns(2)
        items = list(editable_fields.items())
        for idx, (k, v) in enumerate(items):
            with cols[idx % 2]:
                duzenlenmis[k] = st.text_input(k.replace('_', ' ').title(), value=str(v))
        # Kalemleri aynen taşı
        if 'urun_kalemleri' in yapilandirilmis_veri:
            duzenlenmis['urun_kalemleri'] = yapilandirilmis_veri['urun_kalemleri']
    else:
        st.info("Düzenlenecek veri bulunamadı.")

    if duzenlenmis:
        json_bytes = json.dumps(duzenlenmis, ensure_ascii=False, indent=2).encode('utf-8')
        st.download_button("Düzeltilmiş JSON'u İndir", data=json_bytes, file_name="duzeltilmis_sonuc.json", mime="application/json")

        try:
            flat = {k: v for k, v in duzenlenmis.items() if k != 'urun_kalemleri'}
            buf = io.StringIO()
            pd.DataFrame([flat]).to_csv(buf, index=False)
            st.download_button("Düzeltilmiş CSV'yi İndir", data=buf.getvalue(), file_name="duzeltilmis_sonuc.csv", mime="text/csv")
        except Exception as e:
            st.warning(f"CSV çıktısı oluşturulurken hata: {e}")

def main():
    """Streamlit uygulamasının ana fonksiyonu."""
    st.title("📄 Akıllı Fatura Tanıma Uygulaması")
    st.markdown("""
        Bu uygulama, yüklediğiniz fatura görsellerini veya PDF'lerini analiz ederek
        içerisindeki yapılandırılmış verileri (Fatura No, Tarih, Tutar, Satıcı, Alıcı vb.)
        otomatik olarak çıkarır.
    """)

    uploaded_file = st.file_uploader(
        "Analiz etmek için bir fatura dosyası seçin (PDF, PNG, JPG)",
        type=["pdf", "png", "jpg", "jpeg"]
    )

    if uploaded_file is not None:
        # Dosyayı geçici olarak kaydet
        temp_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"'{uploaded_file.name}' dosyası başarıyla yüklendi.")
        
        if st.button("Faturayı Analiz Et", type="primary"):
            with st.spinner("Fatura analiz ediliyor... Bu işlem biraz zaman alabilir."):
                try:
                    # Tesseract yolunu config'den oku
                    tesseract_path = None
                    try:
                        with open('config.json', 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        tesseract_path = config.get('tesseract_cmd_path')
                    except FileNotFoundError:
                        st.warning("config.json bulunamadı, varsayılan Tesseract yolu kullanılacak.")

                    # Analiz motorunu başlat ve çalıştır
                    analiz_motoru = FaturaAnalizMotoru(tesseract_cmd_path=tesseract_path)
                    results = analiz_motoru.analiz_et(temp_path)
                    
                    st.divider()
                    display_results(results, source_path=temp_path)

                except Exception as e:
                    st.error(f"Analiz sırasında beklenmedik bir hata oluştu: {e}")
                finally:
                    # Geçici dosyayı sil
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

if __name__ == "__main__":
    main()
