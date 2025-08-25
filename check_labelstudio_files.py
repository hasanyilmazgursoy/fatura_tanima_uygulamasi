import json
import os

def check_labelstudio_files():
    """Label Studio dosyasındaki dosya adlarını kontrol eder"""

    labelstudio_file = "dataset/project-7-at-2025-08-22-15-55-bf61c2ef.json"

    print("🔍 Label Studio dosyalarındaki dosya adlarını kontrol ediyorum...")

    with open(labelstudio_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"📊 Toplam {len(data)} dosya bulundu")

    # Mevcut PNG dosyaları
    png_files = [f.replace('.png', '') for f in os.listdir('fatura_png') if f.endswith('.png')]
    print(f"🖼️ PNG klasöründe {len(png_files)} dosya var")

    # Label Studio'daki dosya adlarını çıkar
    for i, item in enumerate(data):
        file_upload = item.get('file_upload', '')
        data_id = item.get('data', {}).get('id', '')

        print(f"{i+1}. Label Studio ID: {data_id}")
        print(f"   Dosya upload: {file_upload}")

        # Hash'lenmiş dosya adı varsa
        if file_upload:
            hash_name = file_upload.split('/')[-1].split('\\')[-1].replace('.png', '')
            print(f"   Hash adı: {hash_name}")

            # Eşleşen PNG dosyasını bul
            matching_png = None
            for png in png_files:
                if hash_name in png or png in hash_name:
                    matching_png = png
                    break

            if matching_png:
                print(f"   ✅ Eşleşme: {matching_png}.png")
            else:
                print(f"   ❌ Eşleşme bulunamadı")

        print()

if __name__ == "__main__":
    check_labelstudio_files()

