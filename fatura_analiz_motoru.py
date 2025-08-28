import re
import os
import json
import logging
from typing import List, Dict, Optional, Any, Tuple
from collections import defaultdict
import numpy as np
import cv2
import pytesseract
import fitz  # PyMuPDF
import pdfplumber
import pandas as pd
from utils import validate_patterns_structure, preprocess_image, guardian_postprocess

class FaturaAnalizMotoru:
    """
    Akıllı Fatura Tanıma Sistemi (Blok & Koordinat Tabanlı).
    """

    def __init__(self, tesseract_cmd_path: Optional[str] = None):
        if tesseract_cmd_path and os.path.exists(tesseract_cmd_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_path
        self.logger = logging.getLogger(__name__)
        self.patterns = self._load_patterns_from_config('config/patterns.json')
        validate_patterns_structure(self.patterns, self.logger)

    def _load_patterns_from_config(self, config_path: str) -> Dict:
        try:
            project_root = os.path.dirname(os.path.abspath(__file__))
            absolute_path = os.path.join(project_root, config_path)
            with open(absolute_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Patterns dosyası bulunamadı: {config_path}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Patterns JSON format hatası: satır/sütun bilinmiyor, detay: {e}")
            return {}
        except Exception:
            self.logger.exception(f"Patterns yüklenirken beklenmeyen hata: {config_path}")
            return {}

    def _pdf_sayfasini_goruntuye_cevir(self, pdf_path: str, page_num: int = 0, dpi: int = 300) -> Optional[np.ndarray]:
        try:
            doc = fitz.open(pdf_path)
            if page_num >= len(doc): return None
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=dpi)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            if pix.n == 3: # RGB
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            elif pix.n == 4: # RGBA
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            return img
        except Exception as e:
            self.logger.error(f"PDF sayfası görüntüye dönüştürülürken hata: {e}")
            return None

    def _get_words_with_coords(self, file_path: str) -> Tuple[List[Dict], Tuple[float, float]]:
        words = []
        page_size = (0.0, 0.0)
        if file_path.lower().endswith('.pdf'):
            try:
                with pdfplumber.open(file_path) as pdf:
                    if pdf.pages:
                        page = pdf.pages[0]
                        words = [{'text': w['text'], 'x0': w['x0'], 'top': w['top'], 'x1': w['x1'], 'bottom': w['bottom']} for w in page.extract_words(x_tolerance=2)]
                        page_size = (page.width, page.height)
            except Exception as e:
                self.logger.warning(f"Pdfplumber kelime çıkaramadı: {e}.")
        return words, page_size

    def _ocr_fulltext_fallback(self, file_path: str) -> str:
        try:
            image = self._pdf_sayfasini_goruntuye_cevir(file_path, dpi=300)
            if image is None:
                return ''
            processed = preprocess_image(image, 'auto')
            config = '--oem 3 --psm 6'
            text = pytesseract.image_to_string(processed, lang='tur', config=config)
            return text or ''
        except Exception:
            self.logger.exception("OCR fallback sırasında hata")
            return ''

    def _group_words_into_blocks(self, words: List[Dict], line_tolerance: int = 10, block_tolerance_multiplier: float = 2.5) -> List[Dict]:
        if not words: return []
        words.sort(key=lambda w: (w['top'], w['x0']))
        lines = []
        if words:
            current_line = [words[0]]
            for word in words[1:]:
                if abs(word['top'] - current_line[-1]['top']) < line_tolerance:
                    current_line.append(word)
                else:
                    lines.append(current_line)
                    current_line = [word]
            lines.append(current_line)
        blocks = []
        if not lines: return []
        current_block_words = lines[0]
        avg_heights = [w['bottom'] - w['top'] for w in words if w['bottom'] > w['top']]
        avg_height = sum(avg_heights) / len(avg_heights) if avg_heights else 10
        block_tolerance = avg_height * block_tolerance_multiplier
        for line in lines[1:]:
            if (line[0]['top'] - current_block_words[-1]['bottom']) < block_tolerance:
                current_block_words.extend(line)
            else:
                blocks.append(current_block_words)
                current_block_words = line
        blocks.append(current_block_words)
        formatted_blocks = []
        for block_words in blocks:
            text = " ".join(w['text'] for w in block_words)
            x0 = min(w['x0'] for w in block_words)
            top = min(w['top'] for w in block_words)
            x1 = max(w['x1'] for w in block_words)
            bottom = max(w['bottom'] for w in block_words)
            formatted_blocks.append({'text': text, 'coords': (x0, top, x1, bottom)})
        return formatted_blocks

    def _compute_boundaries(self, blocks: List[Dict], page_size: Tuple[float, float]) -> Dict[str, float]:
        page_width, page_height = page_size
        # Varsayılan eşikler
        x_divider = page_width * 0.52
        y_seller_end = page_height * 0.18
        y_buyer_info_end = page_height * 0.38
        y_totals_start = page_height * 0.48

        try:
            # Dinamik ayarlama: toplamlar için çapa kelimeler
            total_anchors = [
                'ödenecek', 'vergiler dahil', 'mal hizmet toplam', 'toplam iskonto',
                'hesaplanan kdv', 'genel toplam', 'ödenecek tutar'
            ]
            y_candidates = []
            for b in blocks:
                t = b['text'].lower()
                if any(a in t for a in total_anchors):
                    # Toplamlar genelde bu bloğun merkezinin biraz üstünden başlar
                    _, y0, _, y1 = b['coords']
                    y_candidates.append((y0 + y1) / 2)
            if y_candidates:
                est = min(y_candidates)  # en yukarıdaki toplam-ilişkili blok
                # Bir miktar yukarı tolerans (satır başlarına denk getirmek için)
                y_totals_start = max(page_height * 0.35, est - page_height * 0.03)

            # Fatura bilgileri (sağ üst) için çapa: Fatura No, ETTN, Fatura Tarihi
            info_anchors = ['fatura no', 'ettn', 'fatura tarihi', 'düzenleme']
            info_y = []
            info_x = []
            for b in blocks:
                t = b['text'].lower()
                if any(a in t for a in info_anchors):
                    x0, y0, x1, y1 = b['coords']
                    info_y.append((y0 + y1) / 2)
                    info_x.append((x0 + x1) / 2)
            if info_y:
                y_buyer_info_end = max(y_buyer_info_end, max(info_y) + page_height * 0.02)
            if info_x:
                # Sağ ağırlıklı ise x_divider biraz sağa alınır
                median_x = sorted(info_x)[len(info_x)//2]
                x_divider = max(x_divider, median_x - page_width * 0.02)
        except Exception:
            self.logger.warning('Dinamik sınır tahmini başarısız, varsayılanlar kullanılacak')

        return {
            'x_divider': x_divider,
            'y_seller_end': y_seller_end,
            'y_buyer_info_end': y_buyer_info_end,
            'y_totals_start': y_totals_start,
        }

    def _identify_blocks(self, blocks: List[Dict], page_size: Tuple[float, float], boundaries: Optional[Dict[str, float]] = None) -> Dict[str, str]:
        page_width, page_height = page_size
        identified_block_texts = {'satici': [], 'alici': [], 'fatura_bilgileri': [], 'toplamlar': []}

        if boundaries is None:
            boundaries = self._compute_boundaries(blocks, page_size)
        x_divider = boundaries['x_divider']
        y_seller_end = boundaries['y_seller_end']
        y_buyer_info_end = boundaries['y_buyer_info_end']
        y_totals_start = boundaries['y_totals_start']

        for block in blocks:
            x0, y0, x1, y1 = block['coords']
            block_center_x = (x0 + x1) / 2
            block_center_y = (y0 + y1) / 2
            if block_center_y < y_seller_end and block_center_x < x_divider:
                identified_block_texts['satici'].append(block['text'])
            elif y_seller_end <= block_center_y < y_buyer_info_end and block_center_x < x_divider:
                identified_block_texts['alici'].append(block['text'])
            elif block_center_y < y_buyer_info_end and block_center_x >= x_divider:
                identified_block_texts['fatura_bilgileri'].append(block['text'])
            elif block_center_y > y_totals_start:
                identified_block_texts['toplamlar'].append(block['text'])
        return {key: "\n".join(texts) for key, texts in identified_block_texts.items()}

    def _extract_data_from_blocks(self, blocks: Dict[str, str], full_text: str) -> Dict[str, Any]:
        data = {}
        if not self.patterns:
             self.logger.warning("Desenler (patterns) yüklenemediği için Regex ile veri çıkarılamıyor.")
             return data
        for key, pattern_info in self.patterns.items():
            if not isinstance(pattern_info, dict): continue
            desen = pattern_info.get('desen')
            target_text = blocks.get(pattern_info.get('blok'), full_text)
            if desen and target_text:
                match = re.search(desen, target_text, re.IGNORECASE | re.DOTALL)
                if match:
                    value = next((g for g in match.groups() if g is not None), match.group(0))
                    data[key] = " ".join(value.strip().split())
        return data
    
    def _gorsel_hata_ayiklama_ciz(self, file_path: str, page_size: Tuple[float, float], boundaries: Optional[Dict[str, float]] = None):
        try:
            image = self._pdf_sayfasini_goruntuye_cevir(file_path, dpi=150)
            if image is None: return
            page_height, page_width, _ = image.shape
            
            if boundaries is None:
                # Görüntü boyutundan tahmin (sayfa_size ile yakın)
                x_divider = int(page_width * 0.52)
                y_seller_end = int(page_height * 0.18)
                y_buyer_info_end = int(page_height * 0.38)
                y_totals_start = int(page_height * 0.48)
            else:
                x_divider = int(boundaries['x_divider'] / page_size[0] * page_width)
                y_seller_end = int(boundaries['y_seller_end'] / page_size[1] * page_height)
                y_buyer_info_end = int(boundaries['y_buyer_info_end'] / page_size[1] * page_height)
                y_totals_start = int(boundaries['y_totals_start'] / page_size[1] * page_height)

            areas = {
                "satici (mavi)": (0, 0, x_divider, y_seller_end),
                "alici (yesil)": (0, y_seller_end, x_divider, y_buyer_info_end),
                "fatura_bilgileri (sari)": (x_divider, 0, page_width, y_buyer_info_end),
                "toplamlar (kirmizi)": (0, y_totals_start, page_width, page_height)
            }
            colors = {"satici (mavi)": (255, 0, 0),"alici (yesil)": (0, 255, 0),"fatura_bilgileri (sari)": (0, 255, 255),"toplamlar (kirmizi)": (0, 0, 255)}
            for name, (x0, y0, x1, y1) in areas.items():
                cv2.rectangle(image, (x0, y0), (x1, y1), colors[name], 3)
                cv2.putText(image, name.split(' ')[0], (x0 + 10, y0 + 30), cv2.FONT_HERSHEY_SIMPLEX, 1.2, colors[name], 4)
            output_folder = "test_reports/debug_images"
            os.makedirs(output_folder, exist_ok=True)
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_path = os.path.join(output_folder, f"debug_{base_name}.png")
            cv2.imwrite(output_path, image)
        except Exception as e:
            self.logger.error(f"Görsel hata ayıklama çıktısı oluşturulurken hata: {e}")

    def analiz_et(self, dosya_yolu: str) -> Dict[str, Any]:
        words, page_size = self._get_words_with_coords(dosya_yolu)
        full_text = ''
        if words:
            blocks_with_coords = self._group_words_into_blocks(words)
            boundaries = self._compute_boundaries(blocks_with_coords, page_size)
            identified_blocks = self._identify_blocks(blocks_with_coords, page_size, boundaries)
            full_text = "\n".join([block['text'] for block in blocks_with_coords])
        else:
            # pdfplumber başarısızsa OCR fallback
            self.logger.warning("pdfplumber kelime çıkaramadı, OCR fallback devrede")
            ocr_text = self._ocr_fulltext_fallback(dosya_yolu)
            full_text = ocr_text
            identified_blocks = {k: '' for k in ['satici', 'alici', 'fatura_bilgileri', 'toplamlar']}
            boundaries = None

        # Debug görseli çiz (mümkünse)
        try:
            self._gorsel_hata_ayiklama_ciz(dosya_yolu, page_size, boundaries)
        except Exception:
            self.logger.warning("Debug görseli oluşturulamadı")

        data = self._extract_data_from_blocks(identified_blocks, full_text)
        data = guardian_postprocess(data)
        data['urun_kalemleri'] = self._urun_kalemlerini_cikar_pdfplumber(dosya_yolu) or []
        return {"yapilandirilmis_veri": data, "ham_metin": full_text}

    def _urun_kalemlerini_cikar_pdfplumber(self, dosya_yolu: str) -> Optional[List[Dict]]:
        if not dosya_yolu.lower().endswith('.pdf'): return None
        try:
            with pdfplumber.open(dosya_yolu) as pdf:
                all_items = []
                for page in pdf.pages:
                    tables = page.extract_tables()
                    if not tables: continue
                    for table in tables:
                        if not table or len(table) < 2: continue
                        header = [str(cell).lower().replace('\n', ' ').strip() for cell in table[0] if cell]
                        if 'mal hizmet' in header and 'miktar' in header:
                            df = pd.DataFrame(table[1:], columns=header)
                            all_items.extend(df.to_dict('records'))
                return all_items
        except Exception as e:
            self.logger.error(f"pdfplumber ile tablo çıkarılırken hata: {e}")
            return None