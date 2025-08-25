import json
import os
from pathlib import Path
import numpy as np
from PIL import Image
from transformers import LayoutLMv3Processor, AutoTokenizer
from datasets import Dataset
import torch

class LayoutLMDatasetConverter:
    """
    Label Studio formatını LayoutLM eğitim formatına dönüştüren sınıf
    """

    def __init__(self):
        self.processor = LayoutLMv3Processor.from_pretrained("microsoft/layoutlmv3-base")
        self.tokenizer = AutoTokenizer.from_pretrained("microsoft/layoutlmv3-base")

        # Etiket ID'lerini tanımla
        self.label2id = {
            'O': 0,  # Outside
            'B-fatura_numarasi': 1,
            'I-fatura_numarasi': 2,
            'B-fatura_tarihi': 3,
            'I-fatura_tarihi': 4,
            'B-genel_toplam': 5,
            'I-genel_toplam': 6,
            'B-satici_firma_unvani': 7,
            'I-satici_firma_unvani': 8,
            'B-alici_firma_unvani': 9,
            'I-alici_firma_unvani': 10,
        }
        self.id2label = {v: k for k, v in self.label2id.items()}

    def load_labelstudio_data(self, file_path):
        """Label Studio export dosyasını yükler"""
        print(f"📄 Label Studio dosyasını yüklüyorum: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"📊 {len(data)} adet etiketlenmiş dosya bulundu")
        return data

    def convert_to_layoutlm_format(self, labelstudio_data):
        """Label Studio formatını LayoutLM formatına dönüştürür"""
        layoutlm_data = []

        for i, item in enumerate(labelstudio_data):
            try:
                print(f"\n🔍 Dosya {i+1}/10 işleniyor...")

                # Tüm dosyaları işle

                # Dosya bilgilerini al
                file_info = item.get('file_upload', '')
                print(f"   Dosya upload: {file_info}")

                if not file_info:
                    print("   ❌ Dosya upload bilgisi yok")
                    continue

                # Dosya adını temizle
                file_name = file_info.split('/')[-1].split('\\')[-1]
                file_name = file_name.replace('.png', '.pdf')  # PNG'yi PDF'e çevir
                print(f"   Temiz dosya adı: {file_name}")

                # Görüntü dosyasının yolunu bul
                # Label Studio hash'lenmiş dosya adından orijinal adı çıkar
                hash_name = file_name.replace('.pdf', '').split('-')[0]
                original_name = file_name.replace(f"{hash_name}-", "").replace('.pdf', '')
                image_path = f"fatura_png/{original_name}.png"
                print(f"   Hash adı: {hash_name}")
                print(f"   Orijinal ad: {original_name}")
                print(f"   Aranan path: {image_path}")

                if not os.path.exists(image_path):
                    print(f"   ❌ Görüntü dosyası bulunamadı: {image_path}")
                    continue

                print("   ✅ Görüntü dosyası bulundu!")

                # Etiketleme bilgilerini al
                annotations = item.get('annotations', [])
                print(f"   Annotations sayısı: {len(annotations)}")

                if not annotations:
                    print("   ❌ Annotation yok")
                    continue

                # İlk annotation'ı al
                annotation = annotations[0]
                result = annotation.get('result', [])
                print(f"   Result sayısı: {len(result)}")

                if not result:
                    print("   ❌ Result yok")
                    continue

                # Bounding box ve etiket bilgilerini çıkar
                words = []
                boxes = []
                labels = []

                print(f"   Result'ları işliyorum...")
                processed_results = 0

                # Rectangle ve labels result'larını eşleştir
                rectangles = []
                label_results = []

                for res in result:
                    res_type = res.get('type', '')
                    res_id = res.get('id', '')

                    if res_type == 'rectangle':
                        rectangles.append(res)
                    elif res_type == 'labels':
                        label_results.append(res)

                print(f"   Rectangle sayısı: {len(rectangles)}")
                print(f"   Labels sayısı: {len(label_results)}")

                # Rectangle ve labels'ları eşleştir (aynı id'ye göre)
                for rect in rectangles:
                    rect_id = rect.get('id', '')
                    rect_value = rect.get('value', {})

                    # Eşleşen label'ı bul
                    matching_label = None
                    for label_res in label_results:
                        if label_res.get('id', '') == rect_id:
                            matching_label = label_res
                            break

                    if matching_label:
                        processed_results += 1

                        # Bounding box bilgilerini al
                        x = rect_value.get('x', 0)
                        y = rect_value.get('y', 0)
                        width = rect_value.get('width', 0)
                        height = rect_value.get('height', 0)

                        # Etiket bilgilerini al
                        label_value = matching_label.get('value', {})
                        labels_list = label_value.get('labels', [])
                        print(f"       Rectangle ID: {rect_id}, Labels: {labels_list}")

                        if labels_list:
                            label = labels_list[0]

                            # Metin bilgisini al (eğer varsa)
                            text = rect_value.get('text', f"[{label}]")  # Default text

                            words.append(text)
                            boxes.append([x, y, x + width, y + height])
                            labels.append(label)
                            print(f"       ✅ Etiket eklendi: {label} -> {text}")

                print(f"   İşlenen result sayısı: {processed_results}")
                print(f"   Toplam etiket sayısı: {len(labels)}")

                if words and boxes and labels:
                    layoutlm_item = {
                        'id': file_name,
                        'image_path': image_path,
                        'tokens': words,
                        'bboxes': boxes,
                        'labels': labels
                    }
                    layoutlm_data.append(layoutlm_item)

                    print(f"✅ {file_name}: {len(words)} kelime, {len(set(labels))} benzersiz etiket")

            except Exception as e:
                print(f"❌ Hata: {file_name} - {e}")
                continue

        return layoutlm_data

    def create_huggingface_dataset(self, layoutlm_data):
        """LayoutLM formatındaki verileri Hugging Face Dataset formatına dönüştürür"""
        print(f"🔄 Hugging Face Dataset oluşturuyorum...")

        # Veri setini kontrol et
        if not layoutlm_data:
            print("❌ LayoutLM verisi bulunamadı!")
            return None

        # Hugging Face Dataset formatına dönüştür
        dataset_dict = {
            'id': [],
            'image_path': [],
            'tokens': [],
            'bboxes': [],
            'labels': []
        }

        for item in layoutlm_data:
            dataset_dict['id'].append(item['id'])
            dataset_dict['image_path'].append(item['image_path'])
            dataset_dict['tokens'].append(item['tokens'])
            dataset_dict['bboxes'].append(item['bboxes'])
            dataset_dict['labels'].append(item['labels'])

        # Dataset oluştur
        dataset = Dataset.from_dict(dataset_dict)

        print(f"✅ Hugging Face Dataset oluşturuldu: {len(dataset)} örnek")
        return dataset

    def preprocess_function(self, examples):
        """LayoutLM preprocessing fonksiyonu"""
        images = []
        words = []
        boxes = []
        word_labels = []

        for image_path, word_list, bbox_list, label_list in zip(
            examples['image_path'], examples['tokens'], examples['bboxes'], examples['labels']
        ):
            try:
                # Görüntüyü yükle
                image = Image.open(image_path).convert("RGB")
                images.append(image)

                # Kelime ve bbox bilgilerini işle
                words.append(word_list)
                boxes.append(bbox_list)

                # Etiketleri sayısal değerlere çevir
                label_ids = []
                for label in label_list:
                    # B- ve I- prefix'lerini ekle
                    b_label = f"B-{label}"
                    if b_label in self.label2id:
                        label_ids.append(self.label2id[b_label])
                    else:
                        label_ids.append(self.label2id['O'])  # Default to 'O'

                word_labels.append(label_ids)

            except Exception as e:
                print(f"❌ Preprocessing hatası: {e}")
                continue

        # LayoutLM v3 processor ile encode et
        encoded_inputs = self.processor(
            images=images,
            text=words,
            boxes=boxes,
            word_labels=word_labels,
            padding="max_length",
            truncation=True,
            max_length=512,
            return_tensors="pt"
        )

        return encoded_inputs

    def save_dataset(self, dataset, output_path):
        """Dataset'i dosyaya kaydeder"""
        print(f"💾 Dataset kaydediliyor: {output_path}")
        dataset.save_to_disk(output_path)
        print(f"✅ Dataset kaydedildi: {output_path}")

def main():
    """Ana fonksiyon"""
    print("🚀 LayoutLM Dataset Dönüştürücü Başlatıldı")
    print("=" * 50)

    # LayoutLM dönüştürücüyü başlat
    converter = LayoutLMDatasetConverter()

    # Label Studio verisini yükle
    labelstudio_file = "dataset/project-7-at-2025-08-22-15-55-bf61c2ef.json"
    if not os.path.exists(labelstudio_file):
        print(f"❌ Label Studio dosyası bulunamadı: {labelstudio_file}")
        return

    labelstudio_data = converter.load_labelstudio_data(labelstudio_file)

    # LayoutLM formatına dönüştür
    layoutlm_data = converter.convert_to_layoutlm_format(labelstudio_data)

    if not layoutlm_data:
        print("❌ LayoutLM verisi oluşturulamadı!")
        return

    print(f"✅ {len(layoutlm_data)} adet LayoutLM verisi oluşturuldu")

    # Hugging Face Dataset oluştur
    dataset = converter.create_huggingface_dataset(layoutlm_data)

    if dataset:
        # Dataset'i kaydet
        output_path = "layoutlm_dataset"
        converter.save_dataset(dataset, output_path)

        print("\n🎉 Dataset dönüştürme tamamlandı!")
        print(f"📁 Dataset kaydedildi: {output_path}")
        print(f"📊 Toplam örnek sayısı: {len(dataset)}")

        # İlk örneği göster
        print("\n📋 İlk örnek:")
        first_example = dataset[0]
        print(f"ID: {first_example['id']}")
        print(f"Kelime sayısı: {len(first_example['tokens'])}")
        print(f"Benzersiz etiket sayısı: {len(set(first_example['labels']))}")

if __name__ == "__main__":
    main()
