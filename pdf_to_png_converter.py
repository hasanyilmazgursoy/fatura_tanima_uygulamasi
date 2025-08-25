import os
import fitz  # PyMuPDF
from PIL import Image
import glob

def pdf_to_png(pdf_path, output_path, dpi=150):
    """
    PDF dosyasını PNG'ye çevirir
    """
    try:
        # PDF'i aç
        pdf_doc = fitz.open(pdf_path)

        # İlk sayfayı al
        page = pdf_doc.load_page(0)

        # PNG olarak kaydet
        pix = page.get_pixmap(dpi=dpi)
        pix.save(output_path)

        pdf_doc.close()
        print(f"✅ {os.path.basename(pdf_path)} → {os.path.basename(output_path)}")
        return True

    except Exception as e:
        print(f"❌ Hata: {pdf_path} - {e}")
        return False

def convert_fatura_pdfs():
    """
    fatura klasöründeki PDF'leri PNG'ye çevirir
    """
    fatura_klasoru = "fatura"
    png_klasoru = "fatura_png"

    # PNG klasörü oluştur
    os.makedirs(png_klasoru, exist_ok=True)

    # PDF dosyalarını bul
    pdf_files = glob.glob(os.path.join(fatura_klasoru, "*.pdf"))

    if not pdf_files:
        print("❌ Fatura klasöründe PDF dosyası bulunamadı!")
        return

    print(f"📄 {len(pdf_files)} PDF dosyası bulundu")
    print("=" * 50)

    converted = 0
    for pdf_file in pdf_files[:10]:  # İlk 10 dosyayı çevir
        base_name = os.path.splitext(os.path.basename(pdf_file))[0]
        png_file = os.path.join(png_klasoru, f"{base_name}.png")

        if pdf_to_png(pdf_file, png_file):
            converted += 1

    print("=" * 50)
    print(f"✅ {converted} PDF dosyası PNG'ye çevrildi")
    print(f"📂 PNG dosyaları: {png_klasoru} klasöründe")

if __name__ == "__main__":
    convert_fatura_pdfs()

