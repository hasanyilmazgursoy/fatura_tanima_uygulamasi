import os
import re
import cv2
import json
import fitz
import torch
import logging
import numpy as np
import pytesseract
from PIL import Image
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from scipy.ndimage import interpolation as inter
from transformers import LayoutLMv3ForTokenClassification, LayoutLMv3TokenizerFast

# Logging ayarları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- GÖRÜNTÜ İŞLEME YARDIMCI FONKSİYONLARI ---
def deskew(image, angle):
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated

def determine_skew(image_gray):
    try:
        thresh = cv2.bitwise_not(image_gray)
        coords = np.column_stack(np.where(thresh > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45: angle = -(90 + angle)
        else: angle = -angle
        return angle
    except Exception: return None

# --- LAYOUTLM TAHMİN SINIFI ---
class LayoutLMPredictor:
    """LayoutLM model ile tahmin yapan sınıf"""

    def __init__(self, model_path="./layoutlm_quick_model"):
        self.model_path = model_path
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Label mapping (layoutlm_trainer.py ile aynı olmalı)
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

        self.model = None
        self.tokenizer = None
        self.load_model(model_path)

    def load_model(self, model_path):
        """Model ve tokenizer'ı yükle"""
        try:
            if os.path.exists(model_path):
                logger.info(f"🤖 LayoutLM model yükleniyor: {model_path}")

                self.tokenizer = LayoutLMv3TokenizerFast.from_pretrained(model_path)
                self.model = LayoutLMv3ForTokenClassification.from_pretrained(
                    model_path,
                    num_labels=self.num_labels,
                    id2label=self.id2label,
                    label2id=self.label2id
                )
                self.model.to(self.device)
                self.model.eval()

                logger.info("✅ LayoutLM model başarıyla yüklendi")
                return True
            else:
                logger.warning(f"⚠️ LayoutLM model bulunamadı: {model_path}")
                return False

        except Exception as e:
            logger.error(f"❌ LayoutLM model yüklenemedi: {str(e)}")
            return False

    def predict(self, image_path: str, ocr_data: Dict) -> Dict:
        """LayoutLM ile tahmin yap"""
        if not self.model:
            logger.warning("⚠️ Model yüklenmemiş, tahmin yapılamıyor")
            return {}

        try:
            # Gelen OCR verisini kullan
            words = [item['text'] for item in ocr_data['ocr_results']]
            boxes = [item['box'] for item in ocr_data['ocr_results']]
            
            # Kutuları normalize et (LayoutLMv3 [0, 1000] formatını bekler)
            image = Image.open(image_path).convert("RGB")
            width, height = image.size
            normalized_boxes = []
            for box in boxes:
                x1, y1, x2, y2 = box
                normalized_box = [
                    int(1000 * x1 / width),
                    int(1000 * y1 / height),
                    int(1000 * x2 / width),
                    int(1000 * y2 / height)
                ]
                normalized_boxes.append(normalized_box)

            # Tokenization
            encoding = self.tokenizer(
                words,
                boxes=normalized_boxes,
                truncation=True,
                padding="max_length",
                max_length=512,
                return_tensors="pt"
            )

            # Model tahmini
            with torch.no_grad():
                outputs = self.model(**{k: v.to(self.device) for k, v in encoding.items()})
            
            # Güven skorlarını ve tahminleri al
            logits = outputs.logits
            probabilities = torch.nn.functional.softmax(logits, dim=-1)
            predictions = logits.argmax(-1)
            
            # Her token için en yüksek olasılığı al
            max_probabilities = probabilities.max(dim=-1).values

            # Sonuçları CPU'ya taşı ve listeye çevir
            predictions = predictions.squeeze().tolist()
            max_probabilities = max_probabilities.squeeze().tolist()
            input_ids = encoding["input_ids"].squeeze().tolist()

            # Entity çıkarımı
            entities = self.extract_entities(input_ids, predictions, max_probabilities)

            return entities

        except Exception as e:
            import traceback
            logger.error(f"❌ LayoutLM tahmin hatası: {str(e)}\n{traceback.format_exc()}")
            return {}

    def extract_entities(self, input_ids: List[int], predictions: List[int], probabilities: List[float]) -> Dict:
        """
        Token ID'leri, tahminler ve olasılıkları kullanarak anlamlı varlıkları
        (entity) ve güven skorlarını çıkaran fonksiyon. 
        Bu versiyon, alt kelimeleri (subwords) doğru bir şekilde birleştirmek
        için tokenizer.decode() kullanır.
        """
        entities = {}
        current_entity = None
        current_ids = []
        current_scores = []

        # input_ids, predictions ve probabilities listelerini dolaş
        for token_id, prediction, prob in zip(input_ids, predictions, probabilities):
            # Özel token'ları (PAD, CLS, SEP) atla
            if token_id in [self.tokenizer.pad_token_id, self.tokenizer.cls_token_id, self.tokenizer.sep_token_id]:
                continue

            # Tahmin edilen ID'yi etikete çevir (örn: 'B-fatura_tarihi')
            label = self.id2label[prediction]

            # Eğer etiket 'B-' (Beginning) ile başlıyorsa
            if label.startswith("B-"):
                # Bir önceki varlığı (eğer varsa) kaydet
                if current_entity and current_ids:
                    # Token ID'lerini kullanarak metni oluştur
                    decoded_text = self.tokenizer.decode(current_ids, skip_special_tokens=True).strip()
                    # Ortalama güven skorunu hesapla
                    avg_score = sum(current_scores) / len(current_scores) if current_scores else 0
                    if decoded_text: # Sadece boş olmayan metinleri ekle
                        entities[current_entity] = {"text": decoded_text, "confidence": avg_score}

                # Yeni bir varlık başlat
                current_entity = label[2:]  # 'B-' önekini kaldır
                current_ids = [token_id]    # Mevcut token ID'sini listeye ekle
                current_scores = [prob]     # Mevcut güven skorunu listeye ekle

            # Eğer etiket 'I-' (Inside) ile başlıyorsa
            elif label.startswith("I-"):
                # Eğer bu, mevcut varlığın devamıysa (örn: 'I-fatura_tarihi' 'B-fatura_tarihi'nin devamıysa)
                if current_entity and label[2:] == current_entity:
                    current_ids.append(token_id)
                    current_scores.append(prob)
                # Eğer değilse, bu 'I-' etiketini görmezden gel ve önceki varlığı bitir
                else:
                    if current_entity and current_ids:
                        decoded_text = self.tokenizer.decode(current_ids, skip_special_tokens=True).strip()
                        avg_score = sum(current_scores) / len(current_scores) if current_scores else 0
                        if decoded_text:
                            entities[current_entity] = {"text": decoded_text, "confidence": avg_score}
                    # Her şeyi sıfırla
                    current_entity, current_ids, current_scores = None, [], []
            
            # Eğer etiket 'O' (Outside) ise
            else:
                # Bir önceki varlığı (eğer varsa) kaydet
                if current_entity and current_ids:
                    decoded_text = self.tokenizer.decode(current_ids, skip_special_tokens=True).strip()
                    avg_score = sum(current_scores) / len(current_scores) if current_scores else 0
                    if decoded_text:
                        entities[current_entity] = {"text": decoded_text, "confidence": avg_score}
                # Her şeyi sıfırla
                current_entity, current_ids, current_scores = None, [], []

        # Döngü bittikten sonra son kalan varlığı da kaydet
        if current_entity and current_ids:
            decoded_text = self.tokenizer.decode(current_ids, skip_special_tokens=True).strip()
            avg_score = sum(current_scores) / len(current_scores) if current_scores else 0
            if decoded_text:
                entities[current_entity] = {"text": decoded_text, "confidence": avg_score}

        return entities

# --- BİRLEŞTİRİLMİŞ HİBRİT ANALİZ SINIFI ---
class HibritFaturaAnalizor:
    """Regex ve LayoutLM analiz yeteneklerini birleştiren tek sınıf."""

    def __init__(self, model_path="./layoutlm_quick_model", config_path: str = os.path.join('config', 'config.json'), patterns_path: str = os.path.join('config', 'patterns.json')):
        # Regex bölümü için başlatma
        self.config = self._load_json(config_path, "Yapılandırma")
        self.patterns = self._load_json(patterns_path, "Desen")
        self.png_output_dir = self.config.get('klasor_yollari', {}).get('png_klasoru', 'fatura_png')
        os.makedirs(self.png_output_dir, exist_ok=True)
        ocr_config_defaults = {"lang": "tur", "PAGE_SEG_MODE": "3", "OEM_MODE": "3"}
        ocr_config = self.config.get('ocr_ayarlari', ocr_config_defaults)
        self.ocr_config = f'--oem {ocr_config.get("OEM_MODE", "3")} --psm {ocr_config.get("PAGE_SEG_MODE", "3")} -l {ocr_config.get("lang", "tur")}'

        # LayoutLM bölümü için başlatma
        self.layoutlm = LayoutLMPredictor(model_path)
        self.ai_confidence_threshold = self.config.get('ai_guven_esigi', 0.80)

    # --- REGEX BÖLÜMÜNDEN GELEN METOTLAR ---
    def _load_json(self, path: str, name: str) -> Dict:
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f: return json.load(f)
            else: return {}
        except Exception: return {}

    def _get_image_from_path(self, dosya_yolu: str) -> Tuple[Optional[np.ndarray], str]:
        image_path_for_ai = dosya_yolu
        try:
            if dosya_yolu.lower().endswith('.pdf'):
                png_filename = os.path.splitext(os.path.basename(dosya_yolu))[0] + '.png'
                png_path = os.path.join(self.png_output_dir, png_filename)
                image_path_for_ai = png_path
                if not os.path.exists(png_path):
                    doc = fitz.open(dosya_yolu)
                    page = doc.load_page(0)
                    pix = page.get_pixmap(dpi=self.config.get('pdf_dpi', 300))
                    pix.save(png_path)
                    doc.close()
                image = cv2.imread(png_path)
                return image, image_path_for_ai
            else:
                image = cv2.imread(dosya_yolu)
                return image, image_path_for_ai
        except Exception: return None, ""

    def _gelismis_on_isleme(self, image: np.ndarray) -> np.ndarray:
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            if self.config.get('egiklik_duzeltme_aktif', True):
                angle = determine_skew(gray)
                if angle is not None and -45 < angle < 45:
                    image = deskew(image, angle)
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            if self.config.get('gurultu_azaltma_aktif', True):
                gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
            clahe = cv2.createCLAHE(clipLimit=self.config.get('clahe_clip_limit', 2.0), tileGridSize=(self.config.get('clahe_grid_size', 8), self.config.get('clahe_grid_size', 8)))
            return clahe.apply(gray)
        except Exception: return image

    def _on_isle_ve_ocr_yap(self, image: np.ndarray) -> Tuple[np.ndarray, str, float, List[Dict]]:
        best_text, best_ocr_results = "", []
        best_confidence, best_psm = -1.0, -1
        processed_image = self._gelismis_on_isleme(image.copy())
        psm_modes = self.config.get('denenecek_psm_modlari', [3, 6, 4, 11])
        for psm in psm_modes:
            try:
                ocr_config_psm = self.ocr_config.replace(f"--psm {self.ocr_config.split('--psm ')[1].split(' ')[0]}", f"--psm {psm}")
                ocr_data = pytesseract.image_to_data(processed_image, config=ocr_config_psm, output_type=pytesseract.Output.DICT)
                confidences, text_parts, current_ocr_results = [], [], []
                for i, text in enumerate(ocr_data['text']):
                    conf = int(ocr_data['conf'][i])
                    if text.strip() and conf > self.config.get('ocr_guven_esigi', 20):
                        text_parts.append(text)
                        confidences.append(conf)
                        current_ocr_results.append({'text': ocr_data['text'][i], 'box': (ocr_data['left'][i], ocr_data['top'][i], ocr_data['left'][i] + ocr_data['width'][i], ocr_data['top'][i] + ocr_data['height'][i])})
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                if avg_confidence > best_confidence:
                    best_confidence, best_text, best_ocr_results, best_psm = avg_confidence, " ".join(text_parts), current_ocr_results, psm
            except Exception: continue
        return processed_image, best_text, best_confidence, best_ocr_results

    def _regex_ile_veri_cikar(self, metin: str) -> Dict:
        """Verilen metinden regex desenlerini kullanarak veri çıkarır."""
        sonuclar = defaultdict(list)
        # print("🔎 Regex ile veri çıkarma başlatılıyor...") # GEREKSIZ DETAY
        for anahtar, desen_listesi in self.patterns.items():
            for desen in desen_listesi:
                try:
                    eslesmeler = re.findall(desen, metin, re.IGNORECASE | re.MULTILINE)
                    if eslesmeler:
                        temizlenmis_eslesmeler = [str(item).strip() for item in eslesmeler if str(item).strip()]
                        if temizlenmis_eslesmeler:
                            sonuclar[anahtar].extend(temizlenmis_eslesmeler)
                except Exception as e:
                    # Bu hatayı loglamak daha iyi olabilir, ama şimdilik sessiz kalabilir.
                    pass # print(f"   ⚠️ '{anahtar}' için Regex hatası: {e} (Desen: {desen})")
        
        for anahtar in sonuclar:
            sonuclar[anahtar] = list(dict.fromkeys(sonuclar[anahtar]))
        # print("✅ Regex analizi tamamlandı!") # GEREKSIZ DETAY
        return dict(sonuclar)

    # --- HİBRİT BİRLEŞTİRME VE ANALİZ METOTLARI ---
    def analiz_et(self, dosya_yolu: str) -> Dict:
        image, image_path_for_ai = self._get_image_from_path(dosya_yolu)
        if image is None: return {"hata": "Dosya yüklenemedi"}
        
        _, ocr_text, confidence, ocr_results_list = self._on_isle_ve_ocr_yap(image)
        if not ocr_text: return {"hata": "Metin çıkarılamadı"}

        regex_sonuclari = self._regex_ile_veri_cikar(ocr_text)
        
        regex_sonuc_ve_ocr = {
            "ortalama_guven": f"{confidence:.2f}%",
            "regex": regex_sonuclari,
            "ocr_results": ocr_results_list,
            "debug_image_path": image_path_for_ai
        }

        layoutlm_sonuc = {}
        if image_path_for_ai and os.path.exists(image_path_for_ai):
            layoutlm_sonuc = self.layoutlm.predict(image_path_for_ai, regex_sonuc_ve_ocr)

        hibrit_sonuc = self._birlesik_sonuc(regex_sonuc_ve_ocr, layoutlm_sonuc)
        
        # self._sonuclari_goster(regex_sonuc_ve_ocr, layoutlm_sonuc, hibrit_sonuc) # Detaylı çıktı için açılabilir

        final_result = {
            "dosya_adi": os.path.basename(dosya_yolu),
            "analiz_tarihi": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "sonuclar": {
                "regex": regex_sonuclari,
                "layoutlm": layoutlm_sonuc,
                "hibrit": hibrit_sonuc
            },
            "istatistikler": self._istatistikler_hesapla(regex_sonuc_ve_ocr, layoutlm_sonuc, hibrit_sonuc),
            "ocr_guven_skoru": f"{confidence:.2f}%"
        }
        
        return final_result

    def _birlesik_sonuc(self, regex_sonuc: Dict, layoutlm_sonuc: Dict) -> Dict:
        hibrit_sonuc = {}
        regex_data = regex_sonuc.get("regex", {})
        tum_alanlar = set(regex_data.keys()) | set(layoutlm_sonuc.keys())
        for alan in tum_alanlar:
            regex_deger_raw = regex_data.get(alan, "")
            regex_deger = str(regex_deger_raw[0]).strip() if isinstance(regex_deger_raw, list) and regex_deger_raw else str(regex_deger_raw).strip()
            layoutlm_item = layoutlm_sonuc.get(alan, {})
            layoutlm_deger = layoutlm_item.get("text", "").strip()
            layoutlm_guven = layoutlm_item.get("confidence", 0.0)
            if layoutlm_guven >= self.ai_confidence_threshold:
                hibrit_sonuc[alan] = layoutlm_deger
            elif regex_deger:
                hibrit_sonuc[alan] = regex_deger
            else:
                hibrit_sonuc[alan] = layoutlm_deger
        return hibrit_sonuc

    def _sonuclari_goster(self, regex_sonuc: Dict, layoutlm_sonuc: Dict, hibrit_sonuc: Dict):
        """(ARTIK KULLANILMIYOR) Üç sistemin sonuçlarını karşılaştırarak gösterir."""
        pass 

    def _istatistikler_hesapla(self, regex_sonuc: Dict, layoutlm_sonuc: Dict, hibrit_sonuc: Dict) -> Dict:
        """Üç sistem için istatistikler hesaplar."""
        regex_data = regex_sonuc.get("regex", {})
        regex_bulunan = len([v for v in regex_data.values() if v and str(v).strip()])
        # DÜZELTME: Hatalı parantez ve mantık düzeltildi.
        layoutlm_bulunan = len([v for v in layoutlm_sonuc.values() if isinstance(v, dict) and v.get('text', '').strip()])
        hibrit_bulunan = len([v for v in hibrit_sonuc.values() if v and str(v).strip()])
        tum_alanlar = len(set(regex_data.keys()) | set(layoutlm_sonuc.keys()))

        return {
            "toplam_alan": tum_alanlar,
            "regex_bulunan": regex_bulunan,
            "layoutlm_bulunan": layoutlm_bulunan,
            "hibrit_bulunan": hibrit_bulunan
        }

def test_hibrit_sistem():
    """Hibrit sistemi test et"""
    print("🧪 HİBRİT SİSTEM TESTİ")
    print("=" * 40)

    # Test dosyası
    test_dosya = "fatura/01.11.2023-21F2023000000007.png"

    if os.path.exists(test_dosya):
        analizor = HibritFaturaAnalizor()
        sonuc = analizor.analiz_et(test_dosya)

        print("\n📈 İSTATİSTİKLER")
        print(f"   📋 Regex alanları:     {sonuc['istatistikler']['regex_bulunan']}")
        print(f"   🤖 LayoutLM alanları:  {sonuc['istatistikler']['layoutlm_bulunan']}")
        print(f"   🔄 Hibrit alanları:    {sonuc['istatistikler']['hibrit_bulunan']}")
        print(f"   📊 Toplam alan sayısı: {sonuc['istatistikler']['toplam_alan']}")

        print("\n✅ Test tamamlandı!")
        print(f"📄 Analiz edilen dosya: {os.path.basename(test_dosya)}")
        print(f"🔍 Bulunan alan sayısı: {sonuc['istatistikler']['hibrit_bulunan']}")

        return sonuc
    else:
        print(f"❌ Test dosyası bulunamadı: {test_dosya}")
        return None

if __name__ == "__main__":
    test_hibrit_sistem()
