import json
import os
from collections import defaultdict

def convert_labelstudio_to_golden(labelstudio_file, output_file):
    """
    Label Studio export dosyasını golden dataset formatına dönüştürür
    """
    print(f"📄 Label Studio dosyasını okuyorum: {labelstudio_file}")

    with open(labelstudio_file, 'r', encoding='utf-8') as f:
        labelstudio_data = json.load(f)

    print(f"📊 {len(labelstudio_data)} adet etiketlenmiş dosya bulundu")

    golden_data = []
    processed_files = 0

    for item in labelstudio_data:
        try:
            # Dosya adını al
            file_path = item.get('file_upload', '')
            if not file_path:
                continue

            # Dosya adını temizle (sadece dosya adını al)
            file_name = file_path.split('/')[-1].split('\\')[-1]
            file_name = file_name.replace('.png', '.pdf')  # PNG'yi PDF'e çevir

            # Etiketlenmiş verileri topla
            expected_data = {}
            annotations = item.get('annotations', [])

            if not annotations:
                continue

            # İlk annotation'ı al (genellikle sadece bir tane var)
            annotation = annotations[0]
            results = annotation.get('result', [])

            # Etiketleri işle
            for result in results:
                if result.get('type') == 'labels':
                    labels = result.get('value', {}).get('labels', [])
                    if labels:
                        label = labels[0]  # İlk etiket
                        # Bu basit versiyon için sadece varlığını işaretle
                        expected_data[label] = "ETIKETLENMIS"

            # Sadece en az 3 etiket içeren dosyaları al
            if len(expected_data) >= 3:
                golden_item = {
                    "dosya": file_name,
                    "expected": expected_data
                }
                golden_data.append(golden_item)
                processed_files += 1

        except Exception as e:
            print(f"⚠️ Hata: {file_path} - {e}")
            continue

    # Golden dataset'i kaydet
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(golden_data, f, ensure_ascii=False, indent=2)

    print(f"✅ {processed_files} dosya golden dataset'e dönüştürüldü")
    print(f"💾 Kaydedildi: {output_file}")

    return golden_data

def analyze_golden_dataset(golden_data):
    """
    Golden dataset'i analiz eder
    """
    print("\n📊 GOLDEN DATASET ANALİZİ")
    print("=" * 50)

    total_files = len(golden_data)
    all_labels = set()

    # Tüm etiketleri topla
    for item in golden_data:
        all_labels.update(item['expected'].keys())

    print(f"📁 Toplam dosya sayısı: {total_files}")
    print(f"🏷️ Benzersiz etiket sayısı: {len(all_labels)}")
    print(f"📋 Tüm etiketler: {sorted(all_labels)}")

    # En çok kullanılan etiketleri göster
    label_counts = defaultdict(int)
    for item in golden_data:
        for label in item['expected'].keys():
            label_counts[label] += 1

    print("\n📈 Etiket Dağılımı:")
    for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_files) * 100
        print(".1f")

if __name__ == "__main__":
    # Dosya yolları
    labelstudio_file = "dataset/project-7-at-2025-08-22-15-55-bf61c2ef.json"
    golden_output = "golden/golden_from_labelstudio.json"

    # Klasörü oluştur
    os.makedirs("golden", exist_ok=True)

    # Dönüştür
    golden_data = convert_labelstudio_to_golden(labelstudio_file, golden_output)

    # Analiz et
    if golden_data:
        analyze_golden_dataset(golden_data)

        print("""
🎯 AŞAMA 2'YE HAZIRLIK:
✅ Golden dataset oluşturuldu
✅ Mevcut sistem test edilmeye hazır
✅ main.py ile test analizi başlatılabilir
        """)
