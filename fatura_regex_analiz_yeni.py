"""
6. GÜN: Düzenli İfadeler (Regular Expressions - Regex) ile Fatura Analizi
FLO fatura örneğine göre kapsamlı olarak güncellenmiş versiyonu

Bu modül, fatura resimlerinden OCR ile çıkarılan ham metni regex desenleri kullanarak
yapılandırılmış verilere dönüştürür. FLO fatura formatındaki tüm önemli alanları yakalayabilir.
"""

import cv2
import numpy as np
import pytesseract
import re
from typing import Dict, List, Optional, Any, Tuple
import os
import json
from datetime import datetime
import fitz  # PyMuPDF kütüphanesini ekle
from scipy.ndimage import interpolation as inter

# Yeni eklenen kütüphane
from collections import defaultdict

class FaturaRegexAnaliz:
    """FLO fatura formatına özel geliştirilmiş OCR ve Regex analiz sistemi."""
    
    def __init__(self):
        """Sistem başlatma ve konfigürasyon."""
        
        # OCR ayarları (iyileştirilmiş) - En stabil sonuçlar için PSM 6'ya geri dönüldü
        self.ocr_config = f'--oem 3 --psm 6 -l tur+eng'
        self.min_confidence = 30
        
        # Ekran boyutu ayarları
        self.max_pencere_genislik = 1200
        self.max_pencere_yukseklik = 800
        
        # Regex desenleri - FLO fatura örneğine göre kapsamlı genişletildi
        self.regex_desenleri = {
            'tarih': {
                'desen': r'\b\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}\b',
                'aciklama': 'Tarih formatları (24.04.2023, 15/12/2024)',
                'ornek': '24.04.2023'
            },
            'para': {
                # 1.899,98 TRY formatları
                'desen': r'\b\d{1,3}(?:\.\d{3})*,\d{2}\s*(?:TL|TRY|₺|EUR|USD)?\b|\b\d+,\d{2}\s*(?:TL|TRY|₺|EUR|USD)?\b',
                'aciklama': 'Parasal değerler (1.899,98 TRY, 150,50)',
                'ornek': '1.899,98 TRY'
            },
            'iban': {
                # Türk IBAN formatları - TR9Y TREZ formatını da destekleyen
                'desen': r'\bTR\d{2}\s*(?:[A-Z]{4}\s*)?(?:\d{4}\s*){5}\d{2}\b|TR9Y\s*TREZ\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{4}\s*\d{2}',
                'aciklama': 'IBAN numaraları (TR9Y TREZ 0006 2000 4320 0006 2978 70)',
                'ornek': 'TR9Y TREZ 0006 2000 4320 0006 2978 70'
            },
            'fatura_no': {
                # FEA2023001157280, Belge No, Fatura No:, Seri/Sıra gibi formatlar
                'desen': r'(?:fatura\s*no|belge\s*no|fatura\s*numarası|invoice\s*no|seri\s*sira)[\s:]*([A-Z0-9/]{8,25})\b|\b[A-Z]{3}\d{13}\b',
                'aciklama': 'Fatura numaraları (FEA2023001157280, GIB2023000000001)',
                'ornek': 'Fatura No: FEA2023001157280'
            },
            'vergi_no': {
                # 10-11 haneli vergi numaraları
                'desen': r'(?:vergi\s*numarası|vergi\s*no|vkn)[\s:]*(\d{10,11})\b',
                'aciklama': 'Vergi numaraları (3960622754)',
                'ornek': 'Vergi Numarası: 3960622754'
            },
            'tc_no': {
                # TCKN 11 haneli
                'desen': r'(?:tckn|tc\s*kimlik|tc\s*no|t\.c\.)[\s:]*(\d{11})\b',
                'aciklama': 'TC kimlik numaraları (11111111111)',
                'ornek': 'TCKN: 11111111111'
            },
            'telefon': {
                # Türkiye telefon formatları +90 212 446 22 88, 905377339964
                'desen': r'(?:telefon|tel|phone|gsm)[\s:]*(\+?90?\s*\d{3}\s*\d{3}\s*\d{2}\s*\d{2}|\d{11})',
                'aciklama': 'Telefon numaraları (+90 212 446 22 88, 905377339964)',
                'ornek': '+90 212 446 22 88'
            },
            'email': {
                # E-posta adresleri
                'desen': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'aciklama': 'E-posta adresleri (flo@hs02.kep.tr)',
                'ornek': 'flo@hs02.kep.tr'
            },
            'fatura_tipi': {
                # e-Arşiv, e-Fatura, Proforma vs.
                'desen': r'(?:fatura\s*tipi)[\s:]*([e\-]?(?:arşiv|arsiv|fatura|proforma|irsaliye)(?:\s*fatura)?)\b|\b(e-?(?:arşiv|arsiv|fatura))\b',
                'aciklama': 'Fatura tipi (e-Arşiv Fatura, Proforma)',
                'ornek': 'e-Arşiv Fatura'
            },
            'kdv_orani': {
                # KDV oranları %10.00, %18
                'desen': r'(?:kdv\s*oranı|vat\s*rate)[\s:]*(%?\d{1,2}\.?\d{0,2})%?',
                'aciklama': 'KDV oranları (%10.00, %18)',
                'ornek': '%10.00'
            },
            'ettn': {
                # ETTN UUID formatı
                'desen': r'(?:ettn|evrensel\s*tekil)[\s:]*([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})',
                'aciklama': 'ETTN numaraları (35b720e6-c242-4362-a675-d067b4f41180)',
                'ornek': '35b720e6-c242-4362-a675-d067b4f41180'
            },
            'mersis_no': {
                # Mersis numaraları 15 haneli
                'desen': r'(?:mersis\s*no|mersis)[\s:]*(\d{15})',
                'aciklama': 'Mersis numaraları (039602394900019)',
                'ornek': '039602394900019'
            },
            'ticaret_sicil': {
                # Ticaret sicil numaraları
                'desen': r'(?:ticaret\s*sicil|sicil\s*no)[\s:]*(\d{6,10})',
                'aciklama': 'Ticaret sicil numaraları (823336)',
                'ornek': '823336'
            },
            'musteri_no': {
                # Müşteri numaraları
                'desen': r'(?:müşteri\s*no|customer\s*no)[\s:]*(\d{6,15})',
                'aciklama': 'Müşteri numaraları (0000001011)',
                'ornek': '0000001011'
            },
            'mal_hizmet_kodu': {
                # Ürün/hizmet kodları
                'desen': r'(?:mal\s*hizmet\s*kodu|product\s*code)[\s:]*(\d{8,15})',
                'aciklama': 'Mal/Hizmet kodları (101181464001)',
                'ornek': '101181464001'
            }
        }
        
        print("✅ FaturaRegexAnaliz sistemi başlatıldı! (6. GÜN - FLO Formatı)")
        print(f"   📐 Ekran boyutu: {self.max_pencere_genislik}x{self.max_pencere_yukseklik} piksel")
        print(f"   🔍 Regex desenleri: {len(self.regex_desenleri)} tane tanımlandı")
        
        # Regex desenlerini göster
        self.regex_desenlerini_goster()
        
        # Yapılandırılmış anahtar alan başlıkları (FLO fatura örneğine göre genişletildi)
        self.onemli_alanlar: List[str] = [
            # Temel fatura bilgileri
            'fatura_numarasi','fatura_tarihi','fatura_tipi','ettn','son_odeme_tarihi',
            # Satıcı bilgileri
            'satici_firma_unvani','satici_adres','satici_telefon','satici_email','satici_vergi_dairesi',
            'satici_vergi_numarasi','satici_web_sitesi','satici_ticaret_sicil','satici_mersis_no',
            # Alıcı bilgileri
            'alici_firma_unvani','alici_adres','alici_telefon','alici_email','alici_vergi_dairesi',
            'alici_vergi_numarasi','alici_tckn','alici_musteri_no',
            # Ürün/hizmet bilgileri
            'kalemler','mal_hizmet_aciklamasi','miktar_ornekleri','birim_fiyat_ornekleri',
            # Finansal bilgileri
            'mal_hizmet_toplam','toplam_iskonto','vergi_haric_tutar','hesaplanan_kdv','kdv_orani',
            'vergiler_dahil_toplam','genel_toplam','para_birimi',
            # Ödeme ve teslimat
            'odeme_sekli','odeme_vadesi','tasiyici_unvani','gonderim_tarihi','banka_bilgileri'
        ]
    
    def regex_desenlerini_goster(self):
        """Tanımlanan regex desenlerini gösterir."""
        print("\n🔍 TANIMLI REGEX DESENLERİ:")
        print("=" * 60)
        for kategori, bilgi in self.regex_desenleri.items():
            print(f"📋 {kategori.upper()}:")
            print(f"   Desen: {bilgi['desen']}")
            print(f"   Açıklama: {bilgi['aciklama']}")
            print(f"   Örnek: {bilgi['ornek']}")
            print()
    
    # -------------------- Yardımcı Regex/Heuristik Fonksiyonlar --------------------
    def _extract_first(self, patterns: List[str], text: str, flags=re.IGNORECASE) -> Optional[str]:
        """İlk eşleşen regex sonucunu döndür."""
        for pattern in patterns:
            match = re.search(pattern, text, flags)
            if match:
                return match.group(1) if match.groups() else match.group(0)
        return None
    
    def _extract_all(self, pattern: str, text: str, flags=re.IGNORECASE) -> List[str]:
        """Tüm eşleşen regex sonuçlarını döndür."""
        matches = re.findall(pattern, text, flags)
        return matches if matches else []
    
    def _duzeltme(self, img: np.ndarray) -> np.ndarray:
        """
        Görüntüdeki eğikliği otomatik olarak tespit eder ve düzeltir.
        """
        def find_score(arr, angle):
            data = inter.rotate(arr, angle, reshape=False, order=0)
            hist = np.sum(data, axis=1)
            score = np.sum((hist[1:] - hist[:-1]) ** 2)
            return hist, score

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1] 

        scores = []
        angles = np.arange(-5, 5, 0.1)
        for angle in angles:
            hist, score = find_score(thresh, angle)
            scores.append(score)

        best_angle = angles[np.argmax(scores)]

        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, best_angle, 1.0)
        rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
        return rotated

    def _find_value_right_of_keywords(self, ocr_data: Dict, keywords: List[str], value_pattern: str, y_tolerance: int = 15) -> Optional[str]:
        """
        Bir anahtar kelimeyle aynı hizada (satırda), genellikle sağa hizalanmış olan değeri bulur.
        Ara toplamlar, KDV, banka bilgileri gibi tablo formatındaki veriler için idealdir.
        """
        if 'text' not in ocr_data:
            return None

        n = len(ocr_data['text'])
        anchor_word_idx = -1

        # 1. Anahtar kelimeyi (referans noktasını) bul
        for i in range(n):
            try:
                text = (ocr_data['text'][i] or '').lower().strip('.:')
                if any(kw.lower() in text for kw in keywords):
                    anchor_word_idx = i
                    break
            except (ValueError, IndexError):
                continue
        
        if anchor_word_idx == -1:
            return None
        
        # 2. Referans kelimenin dikey hizasını (Y-koordinatını) al
        y_keyword = ocr_data['top'][anchor_word_idx]

        # 3. Aynı satırda bulunan ve aranan desene uyan tüm adayları bul
        line_candidates = []
        # Not: anchor_word_idx'den başlamıyoruz, tüm satırı taramalıyız
        for i in range(n):
            try:
                word_text = ocr_data['text'][i] or ''
                word_y = ocr_data['top'][i]

                # Kelime aynı satırda mı ve desene uyuyor mu?
                if abs(word_y - y_keyword) < y_tolerance and re.search(value_pattern, word_text, re.IGNORECASE):
                    line_candidates.append({
                        'text': word_text,
                        'left': ocr_data['left'][i]
                    })
            except (ValueError, IndexError):
                continue
        
        # 4. Eğer aday bulunduysa, en sağdakini seç
        if line_candidates:
            # 'left' değeri en büyük olanı (en sağdakini) bul
            best_candidate = max(line_candidates, key=lambda c: c['left'])
            
            # O adayın metnindeki tam eşleşmeyi tekrar RegEx ile çıkar ve döndür
            match = re.search(value_pattern, best_candidate['text'], re.IGNORECASE)
            if match:
                return match.group(1) if match.groups() else match.group(0)

        return None
    
    def _bloklara_ayir(self, ocr_data: Dict, line_height_multiplier: float = 1.5) -> List[Dict]:
        """
        OCR verisindeki kelimeleri, konumlarına göre mantıksal metin bloklarına ayırır.
        """
        if 'text' not in ocr_data:
            return []

        # 1. Geçerli kelimeleri ve ortalama yüksekliklerini bul
        words = []
        heights = []
        for i, conf in enumerate(ocr_data['conf']):
            if int(conf) > self.min_confidence:
                word_info = {
                    'text': ocr_data['text'][i],
                    'left': ocr_data['left'][i],
                    'top': ocr_data['top'][i],
                    'width': ocr_data['width'][i],
                    'height': ocr_data['height'][i]
                }
                words.append(word_info)
                heights.append(word_info['height'])
        
        if not words:
            return []
        
        avg_height = sum(heights) / len(heights)
        vertical_tolerance = avg_height * 0.4

        # 2. Kelimeleri satırlara grupla
        words.sort(key=lambda w: (w['top'], w['left']))
        lines = []
        current_line = []
        if words:
            current_line.append(words[0])
            for word in words[1:]:
                # Eğer kelime bir önceki kelimeyle aynı satırdaysa
                if abs(word['top'] - current_line[-1]['top']) < vertical_tolerance:
                    current_line.append(word)
                else:
                    lines.append(current_line)
                    current_line = [word]
            lines.append(current_line)

        # 3. Satırları bloklara birleştir
        blocks = []
        if lines:
            current_block_words = lines[0]
            last_line_top = lines[0][0]['top']
            
            for line in lines[1:]:
                current_line_top = line[0]['top']
                # Eğer satırlar arası dikey boşluk çok fazlaysa yeni bir blok başlat
                if current_line_top > last_line_top + (avg_height * line_height_multiplier):
                    blocks.append(current_block_words)
                    current_block_words = line
                else:
                    current_block_words.extend(line)
                last_line_top = current_line_top
            blocks.append(current_block_words)

        # 4. Blokları metin ve koordinat bilgisiyle formatla
        formatted_blocks = []
        for block_words in blocks:
            block_words.sort(key=lambda w: (w['top'], w['left']))
            text = ' '.join(w['text'] for w in block_words if w['text'].strip())
            if text:
                formatted_blocks.append({'text': text})

        return formatted_blocks

    def _blogu_tanimla(self, block_text: str) -> str:
        """
        Bir metin bloğunun içeriğine bakarak onu anlamsal olarak etiketler.
        """
        block_text = block_text.lower()
        scores = defaultdict(int)

        # Anahtar kelimeler ve puanları - Daha belirgin ve ayrıştırıcı
        satici_keywords = {
            'vkn': 3, 'vergi no': 3, 'mersis': 3, 'ticaret sicil': 2, 
            'a.ş.': 1, 'ltd.': 1, 'satıcı': 2, 'şirketi': 1, 'vergi dairesi': 2
        }
        alici_keywords = {
            'sayın': 3, 'alıcı': 3, 'tckn': 3, 'müşteri': 2, 
            'ad soyad': 2, 'teslimat adresi': 1, 'fatura adresi': 1
        }
        toplamlar_keywords = {
            'genel toplam': 3, 'ödenecek tutar': 3, 'toplam kdv': 2, 
            'ara toplam': 1, 'iskonto': 1, 'vergiler dahil': 1
        }
        banka_keywords = {'iban': 3, 'hesap no': 2, 'bankası': 1, 'swift': 1}

        keyword_map = {
            'satici': satici_keywords,
            'alici': alici_keywords,
            'toplamlar': toplamlar_keywords,
            'banka': banka_keywords,
        }

        for category, keywords in keyword_map.items():
            for keyword, score in keywords.items():
                if keyword in block_text:
                    scores[category] += score
        
        # Eğer bir blok hem satıcı hem de alıcı anahtar kelimeleri içeriyorsa,
        # hangisinin daha güçlü olduğuna karar ver.
        if 'satici' in scores and 'alici' in scores:
            if scores['satici'] > scores['alici'] * 1.5:
                del scores['alici'] # Satıcı çok daha baskın
            elif scores['alici'] > scores['satici'] * 1.5:
                del scores['satici'] # Alıcı çok daha baskın
            # Aksi halde belirsiz kalabilir, en yüksek skorluya gider.

        if not scores:
            return 'diger'
        
        # En yüksek skoru alan kategoriyi döndür
        return max(scores, key=scores.get)

    def _find_multiline_value_below_keyword(self, ocr_data: Dict, keywords: List[str], stop_keywords: List[str]) -> Optional[str]:
        """
        Bir anahtar kelimenin altındaki birden çok satıra yayılmış metni bulur.
        Adres gibi çok satırlı verileri çıkarmak için idealdir.
        Arama, bir 'stop_keyword' ile karşılaşınca durur.
        """
        if 'text' not in ocr_data:
            return None

        n = len(ocr_data['text'])
        anchor_word_idx = -1

        # 1. Anahtar kelimeyi (referans noktasını) bul
        for i in range(n):
            try:
                text = (ocr_data['text'][i] or '').lower().strip('.:')
                if any(kw.lower() in text for kw in keywords):
                    anchor_word_idx = i
                    break
            except (ValueError, IndexError):
                continue
        
        if anchor_word_idx == -1:
            return None

        # 2. Referans noktasının koordinatlarını al
        anchor = {
            'x': ocr_data['left'][anchor_word_idx],
            'y_bottom': ocr_data['top'][anchor_word_idx] + ocr_data['height'][anchor_word_idx],
            'h': ocr_data['height'][anchor_word_idx]
        }

        # 3. Referans noktasının altındaki kelimeleri topla
        candidate_words = []
        for i in range(anchor_word_idx + 1, n):
            try:
                word_y = ocr_data['top'][i]
                # Sadece anahtar kelimenin altındaki belirli bir dikey aralıktaki kelimelere bak
                if anchor['y_bottom'] - (anchor['h'] * 0.5) < word_y < anchor['y_bottom'] + (anchor['h'] * 7):
                    candidate_words.append({
                        'text': ocr_data['text'][i],
                        'top': ocr_data['top'][i],
                        'left': ocr_data['left'][i]
                    })
            except (ValueError, IndexError):
                continue
        
        if not candidate_words:
            return None

        # 4. Kelimeleri satırlara grupla ve birleştir
        # Satırları dikey konumlarına göre sırala
        candidate_words.sort(key=lambda w: (w['top'], w['left']))
        
        full_text_parts = []
        last_top = -1
        
        for word in candidate_words:
            # Durdurma anahtar kelimesi bulunduysa adresi kes
            if any(stop_kw.lower() in (word['text'] or '').lower() for stop_kw in stop_keywords):
                break
            
            # Yeni bir satıra geçip geçmediğini kontrol et (küçük bir toleransla)
            if last_top != -1 and word['top'] > last_top + (anchor['h'] * 0.5):
                full_text_parts.append('\n') # Satır sonu ekle (isteğe bağlı)

            full_text_parts.append(word['text'])
            last_top = word['top']

        return ' '.join(full_text_parts).replace('\n ', '\n').strip() if full_text_parts else None

    def _urun_kalemlerini_cikar(self, ocr_data: Dict, ham_metin: str) -> List[Dict]:
        """
        OCR verisinden ürün listesini (kalemleri) tablo yapısını analiz ederek çıkarır.
        Bu fonksiyon, başlıkları bulur, sütunları belirler ve satırları ayrıştırır.
        """
        # Güvenilir kelimeleri ve konumlarını al
        words = []
        for i, conf in enumerate(ocr_data['conf']):
            try:
                if int(conf) > self.min_confidence:
                    words.append({
                        'text': ocr_data['text'][i],
                        'left': ocr_data['left'][i],
                        'top': ocr_data['top'][i],
                        'width': ocr_data['width'][i],
                        'height': ocr_data['height'][i]
                    })
            except (ValueError, IndexError):
                continue
        
        if not words:
            return []

        # 1. Başlık anahtar kelimelerini ve sütunlarını bul
        header_keywords = {
            'aciklama': ['açıklama', 'ürün', 'hizmet', 'description', 'cinsi', 'ürün adı'],
            'miktar': ['miktar', 'mik', 'adet', 'qty', 'quantity'],
            'birim_fiyat': ['birim', 'fiyat', 'fiyatı', 'unit price'],
            'tutar': ['tutar', 'toplam', 'amount', 'total', 'net tutar']
        }
        
        # Kelimeleri satırlara grupla
        lines = defaultdict(list)
        words.sort(key=lambda w: (w['top'], w['left']))
        if not words: return []
        
        avg_line_height = sum(w['height'] for w in words) / len(words)
        
        current_line_top = words[0]['top']
        for word in words:
            if abs(word['top'] - current_line_top) > avg_line_height * 0.6:
                current_line_top = word['top']
            lines[current_line_top].append(word)

        # Başlık satırını ve sütun konumlarını bul
        header_line_y = -1
        columns = {}
        stop_y = float('inf')
        
        sorted_lines = sorted(lines.items())

        for y, line_words in sorted_lines:
            line_text = ' '.join(w['text'] for w in line_words).lower()
            
            # Başlıkları ara
            if len(columns) < 2: # Başlıkları bulana kadar devam et
                found_headers = {}
                for cat, kws in header_keywords.items():
                    for word in line_words:
                        if any(kw in word['text'].lower() for kw in kws):
                            found_headers[cat] = word['left']
                            break
                if len(found_headers) >= 2: # En az 2 başlık içeren satırı kabul et
                    header_line_y = y
                    columns = found_headers

            # Durdurma anahtar kelimelerini ara (toplamlar bölümü)
            stop_keywords = ['mal hizmet toplam', 'ara toplam', 'genel toplam', 'ödenecek', 'toplam kdv']
            if any(kw in line_text for kw in stop_keywords):
                stop_y = y
                break # Toplamlar bölümünü bulduktan sonra aramayı durdur

        # Eğer sütunlar bulunamadıysa, işlemi sonlandır
        if not columns or header_line_y == -1:
            return []

        # 2. Başlık satırından sonraki ve toplamlar bloğundan önceki satırları işle
        kalemler = []
        for y, line_words in sorted_lines:
            # Sadece ürün kalemlerinin olduğu bölgeye odaklan
            if y > header_line_y + (avg_line_height * 0.5) and y < stop_y:
                
                # Satırı sütunlara ayır
                item = defaultdict(list)
                for word in line_words:
                    # Kelimeyi en yakın sütuna ata
                    if not columns: continue
                    closest_col_name = min(columns.keys(), key=lambda col: abs(word['left'] - columns.get(col, float('inf'))))
                    item[closest_col_name].append(word['text'])

                # Ayrıştırılmış veriyi yapılandır
                if item:
                    # En azından bir açıklama ve bir sayısal değer (tutar/fiyat) olmalı
                    has_description = 'aciklama' in item and item['aciklama']
                    has_amount = ('tutar' in item and item['tutar']) or ('birim_fiyat' in item and item['birim_fiyat'])
                    
                    if has_description and has_amount:
                        kalem = {cat: ' '.join(texts) for cat, texts in item.items()}
                        kalemler.append(kalem)
        
        # 3. Adım: Çıkarılan kalemleri temizle ve normalize et
        temizlenmis_kalemler = []
        for kalem in kalemler:
            temiz_kalem = {}
            for anahtar, deger in kalem.items():
                # Sayısal alanları temizle (tutar, birim_fiyat, miktar)
                if anahtar in ['tutar', 'birim_fiyat', 'miktar']:
                    # Parasal değeri bulmaya çalış
                    para_eslesmesi = re.search(self.regex_desenleri['para']['desen'], deger)
                    if para_eslesmesi:
                        temiz_deger = self._normalize_amount(para_eslesmesi.group(0))
                    else:
                        # Sadece sayıları ve temel noktalama işaretlerini al
                        temiz_deger = re.sub(r'[^0-9.,]', '', deger)
                # Metinsel alanları temizle (aciklama)
                else:
                    # Gereksiz karakterleri ve kısa anlamsız kelimeleri kaldır
                    temiz_deger = re.sub(r'[|\[\]\'"‘’]', '', deger) # İstenmeyen karakterler
                    temiz_deger = ' '.join(word for word in temiz_deger.split() if len(word) > 1) # 1 harflik kelimeleri at
                
                temiz_kalem[anahtar] = temiz_deger.strip()
            
            # Eğer temizlik sonrası hala anlamlı veri varsa listeye ekle
            if temiz_kalem.get('aciklama') and (temiz_kalem.get('tutar') or temiz_kalem.get('birim_fiyat')):
                temizlenmis_kalemler.append(temiz_kalem)

        return temizlenmis_kalemler

    def _normalize_amount(self, amount: str) -> str:
        """Tutar değerini normalize et."""
        if not amount:
            return ""
        # Para birimi ve diğer metinsel ifadeleri kaldır
        cleaned = re.sub(r'(TL|TRY|₺|EUR|USD)', '', amount, flags=re.IGNORECASE)
        # Sadece rakam, nokta ve virgül bırak, diğer her şeyi temizle
        cleaned = re.sub(r'[^0-9.,]', '', cleaned)
        # Baştaki ve sondaki boşlukları temizle
        return cleaned.strip()
    
    def _normalize_date(self, date: str) -> str:
        """Tarih değerini normalize et."""
        if not date:
            return ""
        # Tarihi standart DD.MM.YYYY formatına dönüştür
        cleaned = re.sub(r'[^\d./\-]', '', date)
        return cleaned
    
    def _normalize_text(self, text: str) -> str:
        """Metin değerini normalize et."""
        if not text:
            return ""
        # Fazla boşlukları ve özel karakterleri temizle
        cleaned = ' '.join(text.split())
        return cleaned

    def _tckn_dogrula(self, tckn: str) -> bool:
        """
        Verilen bir string'in geçerli bir T.C. Kimlik Numarası olup olmadığını kontrol eder.
        """
        if not isinstance(tckn, str) or not tckn.isdigit() or len(tckn) != 11:
            return False
        
        if int(tckn[0]) == 0:
            return False

        h_10 = sum(int(tckn[i]) for i in range(0, 9, 2)) * 7
        h_10 -= sum(int(tckn[i]) for i in range(1, 8, 2))
        
        if h_10 % 10 != int(tckn[9]):
            return False

        h_11 = sum(int(tckn[i]) for i in range(10))
        
        if h_11 % 10 != int(tckn[10]):
            return False
            
        return True

    def _en_buyuk_tutari_bul(self, ham_metin: str) -> Optional[str]:
        """
        Metin içindeki tüm parasal değerleri bulur ve en büyüğünü döndürür.
        """
        para_deseni = self.regex_desenleri['para']['desen']
        bulunan_paralar = re.findall(para_deseni, ham_metin)
        
        en_buyuk_tutar = 0.0
        en_buyuk_tutar_str = None

        for para_str in bulunan_paralar:
            # Para string'ini sayıya çevirmek için temizle (TL, TRY, boşlukları at; virgülü noktaya çevir)
            temiz_deger = para_str.upper().replace('TL', '').replace('TRY', '').replace('₺', '').strip()
            temiz_deger = temiz_deger.replace('.', '').replace(',', '.') # 1.234,56 -> 1234.56
            
            try:
                tutar = float(temiz_deger)
                if tutar > en_buyuk_tutar:
                    en_buyuk_tutar = tutar
                    en_buyuk_tutar_str = para_str
            except ValueError:
                continue
        
        return en_buyuk_tutar_str


    def yapilandirilmis_veri_cikar(self, ocr_data: Dict, ham_metin: str) -> Dict:
        """
        Faturayı mantıksal bloklara ayırır, her bloğu anlamlandırır ve
        hedefli veri çıkarma işlemi yapar.
        """
        data: Dict[str, Optional[str]] = {}
        
        # Hızlı test modunda OCR verisi olmayabilir, bu durumu kontrol et
        is_fast_test = not any(ocr_data.values())

        # 1. Adım: Faturayı mantıksal bloklara ayır (Sadece OCR verisi varsa)
        if not is_fast_test:
            blocks = self._bloklara_ayir(ocr_data)
            
            # 2. Adım: Blokları anlamlandır
            satici_blok_text = ""
            alici_blok_text = ""
            toplamlar_blok_text = ""
            banka_blok_text = ""
            
            for block in blocks:
                label = self._blogu_tanimla(block['text'])
                if label == 'satici' and not satici_blok_text:
                    satici_blok_text = block['text']
                elif label == 'alici' and not alici_blok_text:
                    alici_blok_text = block['text']
                elif label == 'toplamlar' and not toplamlar_blok_text:
                    toplamlar_blok_text = block['text']
                elif label == 'banka' and not banka_blok_text:
                    banka_blok_text = block['text']
        else:
            # Hızlı test modunda blok metinleri boş olur, tüm analiz ham metinden yapılır
            satici_blok_text = alici_blok_text = toplamlar_blok_text = banka_blok_text = ham_metin


        # 3. Adım: Hedeflenmiş Veri Çıkarma
        # Öncelikli olarak tüm metinde aranacak genel bilgiler
        data['fatura_numarasi'] = self._extract_first([
            r'\b([A-Z]{3}\d{13})\b',  # GIB formatı: GIB2023000000001
            r'\b([A-Z]{2,4}\d{12,15})\b', # Genel e-fatura formatı: FEA2023001157280
            r'(?:Fatura\s*No|Belge\s*Numarası)[\s:]*([A-Z0-9/]+)', # Etiketli format: Fatura No: ABC/123
            r'\b([A-Z]\d{14,16})\b'
        ], ham_metin)
        data['fatura_tarihi'] = self._extract_first([r"\b(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\b"], ham_metin)
        data['ettn'] = self._extract_first([r'\b([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\b'], ham_metin, flags=re.IGNORECASE)
        data['para_birimi'] = self._extract_first([r"\b(TRY|TL|₺|USD|EUR|GBP)\b"], ham_metin)

        # Satıcı Bloğu Analizi
        if satici_blok_text:
            data['satici_firma_unvani'] = self._extract_first([r'([A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜa-zçğıöşü\s&\-\.]+(?:A\.Ş\.|LTD\.|MAĞ\.|PAZ\.))'], satici_blok_text)
            data['satici_vergi_numarasi'] = self._extract_first([r'(?:vergi\s*no|vkn)[\s:]*(\d{10,11})', r'\b(\d{10})\b'], satici_blok_text)
            data['satici_mersis_no'] = self._extract_first([r'(?:mersis\s*no)[\s:]*(\d{15})'], satici_blok_text)

        # Alıcı Bloğu Analizi
        if alici_blok_text:
            # Alıcı unvanı/ismi için daha çeşitli desenler
            data['alici_firma_unvani'] = self._extract_first([
                r'(?:Sayın|Alıcı|ALICI|Sayin)[\s:]*([A-ZÇĞİÖŞÜa-zçğıöşü\s\-\.]{4,})',
                r'(?:Ad\s*Soyad|İsim)[\s:]*([A-ZÇĞİÖŞÜa-zçğıöşü\s\-\.]{4,})'
            ], alici_blok_text)
            data['alici_tckn'] = self._extract_first([r'(?:tckn|TCKN)[\s:]*(\d{11})'], alici_blok_text)
            # TCKN için yedek arama (doğrulama ile)
            if not data.get('alici_tckn'):
                olasi_tckn_list = self._extract_all(r"(\d{11})", alici_blok_text)
                for olasi_tckn in olasi_tckn_list:
                    if self._tckn_dogrula(olasi_tckn):
                        data['alici_tckn'] = olasi_tckn
                        break

        # Toplamlar Bloğu Analizi
        if toplamlar_blok_text:
            para_deseni = self.regex_desenleri['para']['desen']
            data['toplam_iskonto'] = self._extract_first([r'(?:toplam\s*iskonto|indirim)[\s:]*(' + para_deseni + ')'], toplamlar_blok_text)
            data['hesaplanan_kdv'] = self._extract_first([r'(?:hesaplanan\s*kdv|toplam\s*kdv)[\s:]*(' + para_deseni + ')'], toplamlar_blok_text)
            data['genel_toplam'] = self._extract_first([r'(?:ödenecek\s*tutar|genel\s*toplam|toplam)[\s:]*(' + para_deseni + ')'], toplamlar_blok_text)

        # Banka Bloğu Analizi
        if banka_blok_text:
            data['banka_bilgileri'] = self._extract_first([self.regex_desenleri['iban']['desen']], banka_blok_text)

        # Yeni Adım: Ürün kalemlerini çıkar (Sadece OCR verisi varsa)
        if not is_fast_test:
            data['kalemler'] = self._urun_kalemlerini_cikar(ocr_data, ham_metin)
        else:
            data['kalemler'] = [] # Hızlı testte bu analiz yapılamaz

        # 4. Adım: Sezgisel Kurallar ve Normalizasyon (Yedekler)
        # Eğer genel toplam bulunamadıysa, en büyük tutarı al.
        if not data.get('genel_toplam'):
            data['genel_toplam'] = self._en_buyuk_tutari_bul(ham_metin)

        # Normalizasyon
        if data.get('fatura_tarihi'):
            data['fatura_tarihi'] = self._normalize_date(data['fatura_tarihi'])
        amount_fields = ['mal_hizmet_toplam', 'toplam_iskonto', 'vergi_haric_tutar', 
                         'hesaplanan_kdv', 'vergiler_dahil_toplam', 'genel_toplam']
        for field in amount_fields:
            if data.get(field):
                data[field] = self._normalize_amount(data[field])
        
        # Boş değerleri temizle
        cleaned_data = {}
        for key, value in data.items():
            if value and str(value).strip():
                cleaned_data[key] = str(value).strip()
            else:
                cleaned_data[key] = None
        
        return cleaned_data

    def regex_ile_veri_cikar(self, ham_metin: str) -> Dict[str, List[str]]:
        """
        Ham metinden regex desenleri kullanarak veri çıkarır.
        
        Args:
            ham_metin (str): OCR'dan gelen ham metin
            
        Returns:
            Dict[str, List[str]]: Her regex kategorisi için bulunan eşleşmeler
        """
        print("🔎 Regex ile veri çıkarma başlatılıyor...")
        
        sonuclar: Dict[str, List[str]] = {}
        
        for kategori, bilgi in self.regex_desenleri.items():
            desen = bilgi['desen']
            print(f"   🔍 {kategori} araniyor...")
            
            try:
                # Regex desenini uygula
                eslemeler = re.findall(desen, ham_metin, re.IGNORECASE | re.MULTILINE)
                
                # Sonuçları düzelt (tuple'lar varsa ilk elemanı al)
                temizlenmis_eslemeler = []
                for esleme in eslemeler:
                    if isinstance(esleme, tuple):
                        # Tuple'dan boş olmayan ilk elemanı al
                        for eleman in esleme:
                            if eleman and str(eleman).strip():
                                temizlenmis_eslemeler.append(str(eleman).strip())
                                break
                    else:
                        temizlenmis_eslemeler.append(str(esleme).strip())
                
                # Tekrarları kaldır ve sınırla
                benzersiz_eslemeler = list(dict.fromkeys(temizlenmis_eslemeler))[:10]
                sonuclar[kategori] = benzersiz_eslemeler
                
                print(f"      ✅ {len(benzersiz_eslemeler)} adet {kategori} bulundu")
                
            except Exception as e:
                print(f"      ❌ {kategori} için regex hatası: {e}")
                sonuclar[kategori] = []
        
        print("✅ Regex analizi tamamlandı!")
        return sonuclar

    def resmi_yukle(self, dosya_yolu: str) -> Optional[np.ndarray]:
        """
        Belirtilen dosya yolundan fatura resmini yükler.
        PDF dosyalarını otomatik olarak resme çevirir.
        
        Args:
            dosya_yolu (str): Resim veya PDF dosyasının tam yolu
            
        Returns:
            np.ndarray: Yüklenen resim (BGR formatında) veya None (hata durumunda)
        """
        print(f"📁 Dosya yükleniyor: {dosya_yolu}")
        try:
            # Dosya uzantısını kontrol et
            dosya_uzantisi = os.path.splitext(dosya_yolu)[1].lower()

            if dosya_uzantisi == '.pdf':
                print("   📄 PDF dosyası algılandı, resme çevriliyor...")
                # PDF'i aç
                pdf_doc = fitz.open(dosya_yolu)
                
                # Sadece ilk sayfayı işle
                if len(pdf_doc) == 0:
                    print("❌ Hata: PDF dosyası boş.")
                    return None
                
                page = pdf_doc.load_page(0)
                
                # Yüksek çözünürlüklü resim oluştur (DPI ayarı)
                pix = page.get_pixmap(dpi=300)
                
                # Pixmap'i Numpy array'e çevir (Daha güvenilir yöntem)
                # pix.samples bir byte dizisidir. Bunu (height, width, 3) şeklinde bir numpy array'e dönüştürürüz.
                img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
                
                # PyMuPDF RGB formatında verir, OpenCV BGR formatını kullanır. Renk kanallarını dönüştür.
                if pix.n == 4: # RGBA ise A kanalını at
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
                elif pix.n == 3: # RGB ise
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                print("   ✅ PDF'in ilk sayfası başarıyla resme çevrildi.")

            else:
                # Geleneksel resim yükleme
                img = cv2.imread(dosya_yolu)
                if img is None:
                    try:
                        # Unicode yol desteği
                        arr = np.fromfile(dosya_yolu, dtype=np.uint8)
                        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                    except Exception:
                        img = None

            if img is None:
                print(f"❌ Hata: '{dosya_yolu}' dosyası yüklenemedi!")
                return None
            
            # Resim boyutlarını kontrol et
            height, width = img.shape[:2]
            print(f"✅ Dosya başarıyla yüklendi ve hazırlandı: {width}x{height} piksel")
            
            return img
            
        except Exception as e:
            print(f"❌ Dosya yükleme hatası: {e}")
            return None

    def resmi_on_isle(self, img: np.ndarray, gurultu_azaltma: bool = True) -> np.ndarray:
        """
        OCR için resmi ön işlemden geçirir.
        Adım 1: Eğiklik Düzeltme (Deskewing)
        Adım 2: CLAHE ile kontrast iyileştirme
        Adım 3: Gürültü Azaltma ve İkilileştirme
        """
        print("🔧 Gelişmiş resim ön işleme başlatılıyor...")
        
        try:
            # Adım 1: Eğiklik Düzeltme
            img = self._duzeltme(img)
            print("   ✅ Eğiklik düzeltildi (Deskewing)")

            # Küçük resimleri büyüt (OCR kalitesi için)
            height, width = img.shape[:2]
            if width < 1000 or height < 1000:
                scale_factor = 1.5
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
                print(f"   ✅ Resim ölçeklendirildi: {new_width}x{new_height}")
            
            # Adım 2: Gri tonlama ve CLAHE
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            print("   ✅ Gri tonlamaya çevrildi")

            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced_gray = clahe.apply(gray)
            print("   ✅ CLAHE ile kontrast iyileştirildi")
            
            if gurultu_azaltma:
                # Adım 3: Gürültü Azaltma ve İkilileştirme
                blur = cv2.GaussianBlur(enhanced_gray, (5, 5), 0)
                print("   ✅ Gaussian blur uygulandı")
                
                thresh = cv2.adaptiveThreshold(
                    blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                    cv2.THRESH_BINARY, 11, 2
                )
                print("   ✅ Adaptif eşikleme uygulandı")
                
                clean = cv2.medianBlur(thresh, 3)
                print("   ✅ Median blur uygulandı")
                
                return clean
            else:
                return enhanced_gray
                
        except Exception as e:
            print(f"❌ Resim ön işleme hatası: {e}")
            return img

    def metni_cikar(self, img: np.ndarray, dil: str = 'tur') -> Tuple[Dict, float]:
        """
        Resimden OCR kullanarak metin ve koordinat bilgilerini çıkarır.
        
        Args:
            img (np.ndarray): İşlenmiş resim
            dil (str): OCR dili ('tur' veya 'eng')
            
        Returns:
            Tuple[Dict, float]: OCR sonuçları ve ortalama güven skoru
        """
        print("🤖 OCR ile metin çıkarma başlatılıyor...")
        
        avg_confidence = 0.0
        try:
            # İlk OCR denemesi
            ocr_data = pytesseract.image_to_data(img, config=self.ocr_config, output_type=pytesseract.Output.DICT)
            
            # Ortalama güven skorunu kontrol et
            confidences = [int(conf) for conf in ocr_data['conf'] if str(conf).isdigit()]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            print(f"   📊 Ortalama güven skoru: {avg_confidence:.1f}%")
            
            # Düşük güven skorunda alternatif PSM dene
            if avg_confidence < 50:
                print("   🔄 Düşük güven skoru, PSM 4 deneniyor...")
                alternative_config = f'--oem 3 --psm 4 -l tur+eng'
                ocr_data_alt = pytesseract.image_to_data(img, config=alternative_config, output_type=pytesseract.Output.DICT)
                
                confidences_alt = [int(conf) for conf in ocr_data_alt['conf'] if str(conf).isdigit()]
                avg_confidence_alt = sum(confidences_alt) / len(confidences_alt) if confidences_alt else 0.0
                
                if avg_confidence_alt > avg_confidence:
                    print(f"   ✅ PSM 4 daha iyi sonuç verdi: {avg_confidence_alt:.1f}%")
                    ocr_data = ocr_data_alt
                    avg_confidence = avg_confidence_alt
            
            # Sonuçları filtrele
            valid_count = len([conf for conf in ocr_data['conf'] if int(conf) >= self.min_confidence])
            total_count = len(ocr_data['conf'])
            
            print(f"   ✅ OCR tamamlandı: {valid_count}/{total_count} adet güvenilir metin bulundu")
            
            return ocr_data, avg_confidence
            
        except Exception as e:
            print(f"❌ OCR hatası: {e}")
            # Boş OCR verisi döndür
            return {
                'text': [],
                'conf': [],
                'left': [],
                'top': [],
                'width': [],
                'height': []
            }, 0.0

    def fatura_analiz_et(self, dosya_yolu: str, gorsellestir: bool = True) -> Dict:
        """
        Fatura resmini analiz eder ve sonuçları döndürür.
        
        Args:
            dosya_yolu (str): Analiz edilecek resim dosyasının yolu
            gorsellestir (bool): Sonuçların görsel olarak gösterilip gösterilmeyeceği
            
        Returns:
            Dict: Analiz sonuçları
        """
        print(f"\n🎯 FATURA ANALİZİ BAŞLATIYOR: {os.path.basename(dosya_yolu)}")
        print("=" * 70)
        
        # 1. Resmi yükle
        img = self.resmi_yukle(dosya_yolu)
        if img is None:
            return {"hata": "Resim yüklenemedi"}
        
        # 2. Resmi ön işlemden geçir
        processed_img = self.resmi_on_isle(img)
        
        # 3. OCR ile metni çıkar
        ocr_data, avg_confidence = self.metni_cikar(processed_img)
        
        # 4. Ham metni oluştur
        valid_texts = []
        for i, (text, conf) in enumerate(zip(ocr_data['text'], ocr_data['conf'])):
            try:
                if int(conf) >= self.min_confidence and text and text.strip():
                    valid_texts.append(text.strip())
            except (ValueError, IndexError):
                continue
        
        ham_metin = ' '.join(valid_texts)
        print(f"📝 Ham metin uzunluğu: {len(ham_metin)} karakter")
        
        # 5. Regex ile veri çıkar
        regex_sonuclari = self.regex_ile_veri_cikar(ham_metin)
        
        # 6. Yapılandırılmış veri çıkar
        print("🏗️ Yapılandırılmış veri çıkarılıyor...")
        structured_data = self.yapilandirilmis_veri_cikar(ocr_data, ham_metin)
        
        # 7. Görselleştir
        if gorsellestir:
            self.sonuclari_gorselle(img, ocr_data, regex_sonuclari)
        
        # 8. Sonuçları birleştir
        sonuclar = {
            "dosya": dosya_yolu,
            "analiz_zamani": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ocr_istatistikleri": {
                "ortalama_guven_skoru": f"{avg_confidence:.2f}%",
                "toplam_kelime": len(ocr_data['text']),
                "gecerli_kelime": len(valid_texts),
                "ham_metin_uzunlugu": len(ham_metin)
            },
            "regex": regex_sonuclari,
            "structured": structured_data
        }
        
        print("✅ Fatura analizi tamamlandı!")
        return sonuclar

    def sonuclari_gorselle(self, img: np.ndarray, ocr_data: Dict, regex_sonuclari: Dict):
        """
        OCR ve regex sonuçlarını görsel olarak gösterir.
        
        Args:
            img: Orijinal resim
            ocr_data: OCR çıktı verisi
            regex_sonuclari: Regex sonuçları
        """
        print("🖼️ Sonuçlar görselleştiriliyor...")
        
        try:
            # Resmi kopyala
            result_img = img.copy()
            
            # OCR kutularını çiz
            for i in range(len(ocr_data['text'])):
                try:
                    conf = int(ocr_data['conf'][i])
                    if conf < self.min_confidence:
                        continue
                except (ValueError, IndexError):
                    continue
                
                x = ocr_data['left'][i]
                y = ocr_data['top'][i]
                w = ocr_data['width'][i]
                h = ocr_data['height'][i]
                
                # Güven skoruna göre renk seç
                if conf > 80:
                    color = (0, 255, 0)  # Yeşil - yüksek güven
                elif conf > 50:
                    color = (0, 165, 255)  # Turuncu - orta güven
                else:
                    color = (0, 0, 255)  # Kırmızı - düşük güven
                
                # Kutu çiz
                cv2.rectangle(result_img, (x, y), (x + w, y + h), color, 2)
            
            # Resmi ekrana sığacak şekilde ölçekle ve göster
            self.resmi_olcekli_goster(result_img, "Fatura OCR Sonuçları")
            
            print("✅ Görselleştirme tamamlandı!")
            
        except Exception as e:
            print(f"❌ Görselleştirme hatası: {e}")

    def resmi_olcekli_goster(self, img: np.ndarray, pencere_adi: str, max_genislik: int = None, max_yukseklik: int = None):
        """
        Resmi ekrana sığacak şekilde ölçeklendirip gösterir.
        
        Args:
            img: Gösterilecek resim
            pencere_adi: Pencere başlığı
            max_genislik: Maksimum genişlik (None ise varsayılan kullanılır)
            max_yukseklik: Maksimum yükseklik (None ise varsayılan kullanılır)
        """
        if max_genislik is None:
            max_genislik = self.max_pencere_genislik
        if max_yukseklik is None:
            max_yukseklik = self.max_pencere_yukseklik
        
        try:
            height, width = img.shape[:2]
            
            # Ölçekleme oranını hesapla
            scale_w = max_genislik / width
            scale_h = max_yukseklik / height
            scale = min(scale_w, scale_h, 1.0)  # 1.0'dan büyük olmasın
            
            if scale < 1.0:
                # Resmi ölçekle
                new_width = int(width * scale)
                new_height = int(height * scale)
                resized_img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
                print(f"   📏 Resim ölçeklendirildi: {width}x{height} -> {new_width}x{new_height}")
            else:
                resized_img = img
            
            # Pencereyi göster
            cv2.imshow(pencere_adi, resized_img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            
        except Exception as e:
            print(f"❌ Resim gösterme hatası: {e}")

    def sonuclari_yazdir(self, sonuclar: Dict):
        """
        Analiz sonuçlarını düzenli olarak yazdırır.
        
        Args:
            sonuclar: Analiz sonuçları dictionary'si
        """
        print("\n" + "="*70)
        print("📊 FATURA ANALİZ SONUÇLARI")
        print("="*70)
        
        # Dosya bilgisi
        print(f"📁 Dosya: {os.path.basename(sonuclar.get('dosya', 'Bilinmiyor'))}")
        print(f"⏰ Analiz Zamanı: {sonuclar.get('analiz_zamani', 'Bilinmiyor')}")
        
        # OCR istatistikleri
        istatistikler = sonuclar.get('ocr_istatistikleri', {})
        print(f"\n📈 OCR İstatistikleri:")
        print(f"   • Ortalama Güven Skoru: {istatistikler.get('ortalama_guven_skoru', 'N/A')}")
        print(f"   • Toplam kelime: {istatistikler.get('toplam_kelime', 0)}")
        print(f"   • Geçerli kelime: {istatistikler.get('gecerli_kelime', 0)}")
        print(f"   • Ham metin uzunluğu: {istatistikler.get('ham_metin_uzunlugu', 0)} karakter")
        
        # Regex sonuçları
        regex_data = sonuclar.get('regex', {})
        print(f"\n🔍 Regex Sonuçları:")
        for kategori, bulunanlar in regex_data.items():
            if bulunanlar:
                print(f"   📋 {kategori.upper()}: {len(bulunanlar)} adet")
                for item in bulunanlar[:3]:  # İlk 3 örneği göster
                    print(f"      • {item}")
                if len(bulunanlar) > 3:
                    print(f"      ... ve {len(bulunanlar) - 3} adet daha")
            else:
                print(f"   📋 {kategori.upper()}: Bulunamadı")
        
        # Yapılandırılmış veriler
        structured = sonuclar.get('structured', {})
        if structured:
            print(f"\n🏗️ Yapılandırılmış Veriler:")
            
            # Önemli alanları grupla ve yazdır
            önemli_bulunanlar = {}
            for alan in self.onemli_alanlar:
                değer = structured.get(alan)
                if değer and str(değer).strip():
                    önemli_bulunanlar[alan] = str(değer).strip()
            
            if önemli_bulunanlar:
                print(f"   ✅ {len(önemli_bulunanlar)} adet önemli alan bulundu:")
                for alan, değer in önemli_bulunanlar.items():
                    # Alan adını güzelleştir
                    güzel_alan = alan.replace('_', ' ').title()
                    # Değeri kısalt
                    kısa_değer = değer[:50] + "..." if len(değer) > 50 else değer
                    print(f"      • {güzel_alan}: {kısa_değer}")
            else:
                print("   ❌ Önemli alan bulunamadı")
        
        print("\n" + "="*70)


def main():
    """Ana test fonksiyonu - FLO fatura formatı için geliştirildi."""
    
    # Sistem başlat
    analiz_sistemi = FaturaRegexAnaliz()
    
    # Test klasörü
    test_klasoru = r"C:\Users\hasan\OneDrive\Desktop\AkilliFaturaTanimaUygulamasi\fatura\test"
    
    if not os.path.exists(test_klasoru):
        print(f"❌ Test klasörü bulunamadı: {test_klasoru}")
        return
    
    # Desteklenen dosya formatları
    desteklenen_formatlar = ['.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp']
    
    # Test dosyalarını bul
    test_dosyalari = []
    for dosya in os.listdir(test_klasoru):
        if any(dosya.lower().endswith(fmt) for fmt in desteklenen_formatlar):
            test_dosyalari.append(os.path.join(test_klasoru, dosya))
    
    if not test_dosyalari:
        print(f"❌ Test klasöründe desteklenen resim dosyası bulunamadı: {test_klasoru}")
        return
    
    print(f"\n🎯 {len(test_dosyalari)} adet test dosyası bulundu")
    
    # Rapor klasörü oluştur
    rapor_klasoru = "test_reports"
    os.makedirs(rapor_klasoru, exist_ok=True)
    
    # Tüm sonuçları topla
    tum_sonuclar = []
    
    for dosya_yolu in test_dosyalari:
        try:
            print(f"\n{'='*20} {os.path.basename(dosya_yolu)} {'='*20}")
            
            # Analiz et
            sonuclar = analiz_sistemi.fatura_analiz_et(dosya_yolu, gorsellestir=False)
            
            # Sonuçları yazdır
            analiz_sistemi.sonuclari_yazdir(sonuclar)
            
            # Sonuçları kaydet
            tum_sonuclar.append(sonuclar)
            
        except Exception as e:
            print(f"❌ {os.path.basename(dosya_yolu)} analiz hatası: {e}")
    
    # Toplu rapor oluştur
    if tum_sonuclar:
        rapor_dosyasi = os.path.join(rapor_klasoru, f"fatura_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(rapor_dosyasi, 'w', encoding='utf-8') as f:
            json.dump(tum_sonuclar, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 Detaylı rapor kaydedildi: {rapor_dosyasi}")
        
        # Özet istatistikler
        print(f"\n📊 GENEL ÖZET:")
        print(f"   • Analiz edilen dosya sayısı: {len(tum_sonuclar)}")
        print(f"   • Ortalama bulunan alan sayısı: {sum(len([v for v in sonuc.get('structured', {}).values() if v]) for sonuc in tum_sonuclar) / len(tum_sonuclar):.1f}")
        print(f"   • Rapor dosyası: {rapor_dosyasi}")
    
    print("\n🎉 Test tamamlandı!")


if __name__ == "__main__":
    main()
