import os
import torch
from torch.utils.data import DataLoader
from transformers import (
    LayoutLMv3ForTokenClassification,
    LayoutLMv3TokenizerFast,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback
)
from datasets import load_from_disk, Dataset
import numpy as np
from seqeval.metrics import classification_report, f1_score, precision_score, recall_score
import json
import logging
from datetime import datetime
from tqdm import tqdm

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LayoutLMTrainer:
    def __init__(self, model_path="./layoutlm_quick_model"):
        self.model_path = model_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"🖥️ Cihaz: {self.device}")

        # Label mapping
        self.label_list = [
            "O",  # Outside
            "B-fatura_numarasi", "I-fatura_numarasi",
            "B-fatura_tarihi", "I-fatura_tarihi",
            "B-fatura_tipi", "I-fatura_tipi",
            "B-ettn", "I-ettn",
            "B-son_odeme_tarihi", "I-son_odeme_tarihi",
            "B-satici_firma_unvani", "I-satici_firma_unvani",
            "B-satici_adres", "I-satici_adres",
            "B-satici_telefon", "I-satici_telefon",
            "B-satici_email", "I-satici_email",
            "B-satici_vergi_dairesi", "I-satici_vergi_dairesi",
            "B-satici_vergi_numarasi", "I-satici_vergi_numarasi",
            "B-satici_web_sitesi", "I-satici_web_sitesi",
            "B-satici_ticaret_sicil", "I-satici_ticaret_sicil",
            "B-satici_mersis_no", "I-satici_mersis_no",
            "B-alici_firma_unvani", "I-alici_firma_unvani",
            "B-alici_adres", "I-alici_adres",
            "B-alici_telefon", "I-alici_telefon",
            "B-alici_email", "I-alici_email",
            "B-alici_tckn", "I-alici_tckn",
            "B-alici_musteri_no", "I-alici_musteri_no",
            "B-urun_aciklama", "I-urun_aciklama",
            "B-urun_miktar", "I-urun_miktar",
            "B-birim_fiyat", "I-birim_fiyat",
            "B-urun_tutar", "I-urun_tutar",
            "B-kdv_orani", "I-kdv_orani",
            "B-mal_hizmet_toplam", "I-mal_hizmet_toplam",
            "B-toplam_iskonto", "I-toplam_iskonto",
            "B-vergi_haric_tutar", "I-vergi_haric_tutar",
            "B-hesaplanan_kdv", "I-hesaplanan_kdv",
            "B-vergiler_dahil_toplam", "I-vergiler_dahil_toplam",
            "B-genel_toplam", "I-genel_toplam",
            "B-odeme_sekli", "I-odeme_sekli",
            "B-banka_bilgileri", "I-banka_bilgileri",
            "B-kargo_bilgisi", "I-kargo_bilgisi",
            "B-siparis_no", "I-siparis_no"
        ]

        self.label2id = {label: i for i, label in enumerate(self.label_list)}
        self.id2label = {i: label for i, label in enumerate(self.label_list)}
        self.num_labels = len(self.label_list)

    def load_dataset(self, dataset_path="./layoutlm_dataset"):
        """Dataset'i yükle"""
        if os.path.exists(dataset_path):
            logger.info(f"📂 Dataset yükleniyor: {dataset_path}")
            dataset = load_from_disk(dataset_path)
            return dataset
        else:
            raise FileNotFoundError(f"Dataset bulunamadı: {dataset_path}")

    def load_model_and_tokenizer(self):
        """Model ve tokenizer'ı yükle"""
        logger.info("🤖 Model ve tokenizer yükleniyor...")

        # Tokenizer
        self.tokenizer = LayoutLMv3TokenizerFast.from_pretrained("microsoft/layoutlmv3-base")

        # Model
        self.model = LayoutLMv3ForTokenClassification.from_pretrained(
            "microsoft/layoutlmv3-base",
            num_labels=self.num_labels,
            id2label=self.id2label,
            label2id=self.label2id
        )

        self.model.to(self.device)

    def preprocess_function(self, example):
        """Veri ön işleme (tek bir örnek için)"""
        
        # Gelen basit etiketleri IOB formatına ve ID'lere dönüştür
        tokens = example["tokens"]
        bboxes = example["bboxes"]
        doc_labels = example["labels"]
        
        iob_labels = []
        last_label = "O"
        for label in doc_labels:
            label = label.strip()
            if not label or label == "O":
                iob_labels.append(self.label2id["O"])
                last_label = "O"
            else:
                iob_format_label = f"B-{label}" if label != last_label else f"I-{label}"
                iob_labels.append(self.label2id.get(iob_format_label, self.label2id["O"]))
                last_label = label

        # Tokenization
        encoding = self.tokenizer(
            tokens,
            boxes=bboxes,
            word_labels=iob_labels,
            truncation=True,
            padding="max_length",
            max_length=512,
            return_tensors="pt"
        )
        
        # Boyutları düzelt (squeeze)
        encoding = {key: val.squeeze() for key, val in encoding.items()}
        return encoding

    def compute_metrics(self, p):
        """Performans metrikleri hesaplama"""
        predictions, labels = p
        predictions = np.argmax(predictions, axis=2)

        # Remove ignored index (special tokens)
        true_predictions = [
            [self.label_list[p] for (p, l) in zip(prediction, label) if l != -100]
            for prediction, label in zip(predictions, labels)
        ]
        true_labels = [
            [self.label_list[l] for (p, l) in zip(prediction, label) if l != -100]
            for prediction, label in zip(predictions, labels)
        ]

        results = classification_report(true_labels, true_predictions, output_dict=True)

        return {
            "precision": results["macro avg"]["precision"],
            "recall": results["macro avg"]["recall"],
            "f1": results["macro avg"]["f1-score"],
            "accuracy": results["macro avg"]["f1-score"]  # Approximation
        }

    def train(self, dataset_path="./layoutlm_dataset", epochs=10, batch_size=4):
        """Model eğitimi"""
        print("🎯 LAYOUTLM MODEL EĞİTİMİ BAŞLATIYOR")
        print("=" * 60)

        try:
            # Dataset yükleme
            dataset = self.load_dataset(dataset_path)
            logger.info(f"📊 Dataset boyutu: {len(dataset)}")

            # Model ve tokenizer yükleme
            self.load_model_and_tokenizer()

            # Veri ön işleme
            logger.info("🔄 Veri ön işleme başlatılıyor...")

            # Manuel Veri İşleme Döngüsü
            # dataset.map() yerine manuel bir for döngüsü kullanıyoruz.
            # Bu, büyük veri setlerinde RecursionError gibi hataları önlemek için pratik bir çözümdür.
            all_input_ids, all_attention_masks, all_bboxes, all_labels = [], [], [], []
            for example in tqdm(dataset, desc="Veri ön işleniyor"):
                encoding = self.preprocess_function(example)
                all_input_ids.append(encoding['input_ids'].long().tolist())
                all_attention_masks.append(encoding['attention_mask'].long().tolist())
                all_bboxes.append(encoding['bbox'].long().tolist())
                all_labels.append(encoding['labels'].long().tolist())

            processed_dataset = Dataset.from_dict({
                'input_ids': all_input_ids,
                'attention_mask': all_attention_masks,
                'bbox': all_bboxes,
                'labels': all_labels
            })
            
            # Veri setini %80 train, %20 test (eval) olarak ayır
            split_dataset = processed_dataset.train_test_split(test_size=0.2)
            train_ds = split_dataset["train"]
            eval_ds = split_dataset["test"]

            logging.info(f"Eğitim seti boyutu: {len(train_ds)}")
            logging.info(f"Değerlendirme seti boyutu: {len(eval_ds)}")


            # Eğitim argümanları
            training_args = TrainingArguments(
                output_dir=self.model_path,
                num_train_epochs=epochs,
                per_device_train_batch_size=batch_size,
                per_device_eval_batch_size=batch_size,
                learning_rate=5e-5,
                evaluation_strategy="epoch",
                save_strategy="epoch",
                load_best_model_at_end=True,
                metric_for_best_model="f1",
                greater_is_better=True,
                save_total_limit=2,
                fp16=True,
                dataloader_num_workers=0,  # Windows için
                remove_unused_columns=False,
                report_to="none",  # wandb entegrasyonunu kapat
            )

            # Trainer'ı oluştur
            trainer = Trainer(
                model=self.model,
                args=training_args,
                train_dataset=train_ds,
                eval_dataset=eval_ds,
                tokenizer=self.tokenizer,
                compute_metrics=self.compute_metrics,
                callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
            )

            # Eğitim başlatma
            logger.info("🏃 Eğitim başlatılıyor...")
            trainer.train()

            # Model kaydetme
            trainer.save_model(self.model_path)
            logger.info(f"💾 Model kaydedildi: {self.model_path}")

            # Sonuçları yazdırma
            print("\n🎉 Model eğitimi tamamlandı!")
            print(f"📁 Model kaydedildi: {self.model_path}")

            # Eğitim loglarını kaydet
            self.save_training_log(trainer, epochs, batch_size)

            return True

        except Exception as e:
            import traceback
            logger.error(f"❌ Eğitim hatası: {str(e)}")
            logger.error(traceback.format_exc()) # Hatanın tüm detaylarını logla
            print(f"❌ Hata: {str(e)}")
            print(f"Detaylar: {traceback.format_exc()}") # Hatanın tüm detaylarını terminale yazdır
            return False

    def save_training_log(self, trainer, epochs, batch_size):
        """Eğitim loglarını kaydet"""
        log_data = {
            "training_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model_path": self.model_path,
            "epochs": epochs,
            "batch_size": batch_size,
            "device": str(self.device),
            "final_metrics": trainer.evaluate() if hasattr(trainer, 'evaluate') else {}
        }

        log_file = f"{self.model_path}_training_log.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        logger.info(f"📝 Eğitim logu kaydedildi: {log_file}")

def main():
    """Ana eğitim fonksiyonu"""
    trainer = LayoutLMTrainer()

    # Eğitim parametreleri
    dataset_path = "./layoutlm_dataset"
    epochs = 15  # Daha fazla epoch için
    batch_size = 2  # Küçük batch size

    print(f"""
🧪 LAYOUTLM MODEL EĞİTİMİ
===============================
📂 Dataset: {dataset_path}
📊 Epoch sayısı: {epochs}
📦 Batch size: {batch_size}
🖥️ Cihaz: {trainer.device}
    """)

    # Eğitim başlat
    success = trainer.train(dataset_path, epochs, batch_size)

    if success:
        print("\n✅ Eğitim başarıyla tamamlandı!")
        print("💡 Sonraki adımlar:")
        print("1. Model performansını test et")
        print("2. Hibrit analiz sistemine entegre et")
        print("3. Ana sisteme bağla")
    else:
        print("\n❌ Eğitim başarısız oldu!")
        print("🔍 Hata loglarını kontrol edin")

if __name__ == "__main__":
    main()
