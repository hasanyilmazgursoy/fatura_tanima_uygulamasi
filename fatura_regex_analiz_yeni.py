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
from profiles import A101Profile, FLOProfile, TrendyolProfile

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
                'desen': r'\b\d{1,2}\s*[/\-.]\s*\d{1,2}\s*[/\-.]\s*\d{2,4}\b',
                'aciklama': 'Tarih formatları (24.04.2023, 03 - 06 - 2025, 15/12/2024)',
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
                'desen': r'(?:fatura\s*no|belge\s*no|fatura\s*numarası|invoice\s*no|seri\s*sira)[\s:]*([A-Z0-9/&\-]{8,25})\b|\b[A-Z]{3}\d{13}\b',
                'aciklama': 'Fatura numaraları (FEA2023001157280, GIB2023000000001, özel karakter toleransı)',
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
                # ETTN UUID formatı (büyük/küçük harf toleransı)
                'desen': r'(?:ettn|evrensel\s*tekil)[\s:]*([A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12})',
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
            },
            # 🆕 YENİ EKLENEN REGEX DESENLERİ - FAZE 1
            'alici_ad_soyad': {
                'desen': r'(?:SAYIN|ALICI|MÜŞTERİ|GÖKHAN|MEHMET|FUNDA)[\s:]+([A-ZÇĞİÖŞÜ\s\.]{3,25})\b',
                'aciklama': 'Alıcı ad soyad bilgileri (Gokhan Çağaptay, Mehmet Emir Arslan)',
                'ornek': 'Gokhan Çağaptay'
            },
            'alici_adres': {
                'desen': r'(?:ADRES|ADRESİ|BATTALGAZİ|GAZİPAŞA)[\s:]+([A-ZÇĞİÖŞÜ\s/]+(?:MALATYA|ANTALYA|İSTANBUL|BATTALGAZİ|GAZİPAŞA)[A-ZÇĞİÖŞÜ\s/]*)',
                'aciklama': 'Alıcı adres bilgileri (Malatya / Battalgazi, Antalya / Gazipaşa)',
                'ornek': 'Malatya / Battalgazi'
            },
            'urun_aciklama': {
                'desen': r'(?:ÜRÜN|MAL|HİZMET|AÇIKLAMA|HERBAL|HP\s*PAVILION)[\s:]+([A-ZÇĞİÖŞÜa-zçğıöşü\s\d\-\.]+(?:ML|KG|ADET|LİTRE|Q\s*KLAVYE))',
                'aciklama': 'Ürün açıklama bilgileri (Herbal Science Boom Butter, HP Pavilion 800 Q Klavye)',
                'ornek': 'Herbal Science Boom Butter Saç Bakım Yağı 190 ML'
            },
            'urun_miktar': {
                'desen': r'(\d+)\s*(?:adet|ad|piece|unit|ML|ml|KG|kg)',
                'aciklama': 'Ürün miktar bilgileri (4 adet, 190 ML, 1 adet)',
                'ornek': '4 adet'
            },
            'birim_fiyat': {
                'desen': r'(?:BİRİM\s*FİYAT|BİRİM|UNIT\s*PRICE|FİYAT|PRICE)[\s:]+(\d+[,\.]\d+\s*TL?)|(\d+[,\.]\d+\s*TL?)\s*(?:birim|unit|adet)|\((\d+[,\.]\d+\s*TL?)\)|(\d+[,\.]\d+\s*TL?)(?=\s*\))',
                'aciklama': 'Birim fiyat bilgileri (104,17 TL, 748,50 TL, 160,17 TL) - tüm formatlar dahil',
                'ornek': '104,17 TL'
            },
            'odeme_sekli': {
                'desen': r'(?:ÖDEME|ÖDEME ŞEKLİ|PAYMENT|KREDİ|BANKA)[\s:]+([A-ZÇĞİÖŞÜa-zçğıöşü\s]+(?:KREDİ|BANKA|NAKİT|ELEKTRONİK|E-TİCARET|TRENDYOL\s*TEMLİK))',
                'aciklama': 'Ödeme şekli bilgileri (Kredi Kartı, E-Ticaret, Trendyol Temlik)',
                'ornek': 'Kredi Kartı (Trendyol temlik hesabı)'
            },
            'kargo_bilgisi': {
                'desen': r'(?:KARGO|CARGO|TAŞIYICI|SHIPPING)[\s:]+([A-ZÇĞİÖŞÜa-zçğıöşü\s]+(?:PTT|MNG|TRENDYOL|EXPRESS))',
                'aciklama': 'Kargo bilgileri (PTT Kargo, MNG Kargo, Trendyol Express)',
                'ornek': 'PTT Kargo'
            },
            'siparis_no': {
                'desen': r'(?:SİPARİŞ\s*(?:NO|NUMARASI)|SIPARIS\s*(?:NO|NUMARASI)|ORDER\s*(?:NO)?)\s*[:\-]?\s*(?=(?:[A-Z0-9\-]{6,25})\b)(?=.*\d)([A-Z0-9\-]{6,25})',
                'aciklama': 'Sipariş numarası bilgileri (TY0725295, A101-2023-001); en az bir rakam şartı, NO/NUMARASI zorunlu (Sipariş tek başına değil).',
                'ornek': 'TY0725295'
            }
        }

    def _ocr_text_with_config(self, img: np.ndarray, config_suffix: str) -> str:
        """Alternatif Tesseract ayarı ile hızlı OCR metni döndürür."""
        try:
            cfg = f"--oem 3 {config_suffix} -l tur+eng"
            text = pytesseract.image_to_string(img, config=cfg)
            return text or ""
        except Exception:
            return ""

    def _field_level_ocr_fallback(self, img: np.ndarray, structured: Dict, current_text: str) -> Dict:
        """Kritik alanlar eksikse alternatif PSM/whitelist ile OCR deneyerek alanları tamamlar."""
        missing = [k for k in ['fatura_numarasi', 'fatura_tarihi', 'ettn'] if not structured.get(k)]
        if not missing:
            return structured

        alt_texts = []
        # Genel daha ayrıntılı PSM denemeleri
        for psm in (6, 7, 11, 13):
            alt = self._ocr_text_with_config(img, f"--psm {psm}")
            if alt:
                alt_texts.append(alt)

        # ETTN için whitelist (hex + '-')
        if 'ettn' in missing:
            alt = self._ocr_text_with_config(img, "--psm 6 -c tessedit_char_whitelist=0123456789abcdefABCDEF- ")
            if alt:
                alt_texts.append(alt)

        if not alt_texts:
            return structured

        combined = current_text + "\n" + "\n".join(alt_texts)
        # Sadece eksik alanları yeniden çıkar
        # fatura no
        if 'fatura_numarasi' in missing and not structured.get('fatura_numarasi'):
            m = re.search(r'(?:fatura\s*no|belge\s*no)[\s:]*([A-Z0-9/&\-]{8,25})', combined, re.IGNORECASE)
            if not m:
                m = re.search(r'\bA\d{15}\b', combined)
            if not m:
                m = re.search(r'\b[A-Z]{3}\d{13}\b', combined)
            if m:
                structured['fatura_numarasi'] = m.group(1) if m.lastindex else m.group(0)

        # tarih
        if 'fatura_tarihi' in missing and not structured.get('fatura_tarihi'):
            m = re.search(r'\b\d{1,2}\s*[/\-.]\s*\d{1,2}\s*[/\-.]\s*\d{2,4}\b', combined)
            if m:
                structured['fatura_tarihi'] = re.sub(r'\s*[/\-.]\s*', '-', m.group(0))

        # ettn
        if 'ettn' in missing and not structured.get('ettn'):
            m = re.search(r'([A-Fa-f0-9]{8}-(?:[A-Fa-f0-9]{4}-){3}[A-Fa-f0-9]{12})', combined)
            if m:
                structured['ettn'] = m.group(1)

        return structured
        
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
            'mal_hizmet_toplam','toplam_iskonto','vergi_haric_tutar','hesaplanan_kdv',
            'vergiler_dahil_toplam','genel_toplam','para_birimi',
            # Ödeme ve teslimat
            'odeme_sekli','odeme_vadesi','banka_bilgileri'
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
            'kdv_orani': ['kdv %', 'kdv', 'vat'],
            'iskonto': ['isk', 'indirim', 'discount'],
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
            stop_keywords = ['mal hizmet toplam', 'ara toplam', 'genel toplam', 'ödenecek', 'toplam kdv', 'vergiler dahil toplam', 'toplam tutar']
            if any(kw in line_text for kw in stop_keywords):
                stop_y = y
                break # Toplamlar bölümünü bulduktan sonra aramayı durdur

        # Eğer sütunlar bulunamadıysa, işlemi sonlandır
        if not columns or header_line_y == -1:
            return []

        # 2. Başlık satırından sonraki ve toplamlar bloğundan önceki satırları işle
        kalemler = []
        # Sütun konumları ve mesafe eşiği
        if columns:
            col_positions = list(columns.values())
            col_positions.sort()
            avg_gap = 0
            if len(col_positions) >= 2:
                gaps = [col_positions[i+1]-col_positions[i] for i in range(len(col_positions)-1)]
                avg_gap = sum(gaps)/len(gaps)
            max_col_dist = avg_gap*0.75 if avg_gap else 9999
        else:
            max_col_dist = 9999

        for y, line_words in sorted_lines:
            # Sadece ürün kalemlerinin olduğu bölgeye odaklan
            if y > header_line_y + (avg_line_height * 0.5) and y < stop_y:
                
                # Satırı sütunlara ayır
                item = defaultdict(list)
                for word in line_words:
                    # Kelimeyi en yakın sütuna ata
                    if not columns: continue
                    closest_col_name = min(columns.keys(), key=lambda col: abs(word['left'] - columns.get(col, float('inf'))))
                    if abs(word['left'] - columns[closest_col_name]) <= max_col_dist:
                        item[closest_col_name].append(word['text'])

                # Ayrıştırılmış veriyi yapılandır
                if item:
                    # En azından bir açıklama ve bir sayısal değer (tutar/fiyat) olmalı
                    has_description = 'aciklama' in item and item['aciklama']
                    has_amount = ('tutar' in item and item['tutar']) or ('birim_fiyat' in item and item['birim_fiyat'])
                    
                    if has_description and has_amount:
                        kalem = {cat: ' '.join(texts) for cat, texts in item.items()}
                        kalemler.append(kalem)
        
        # 3. Adım: Çıkarılan kalemleri temizle, normalize et ve eksikleri hesapla
        temizlenmis_kalemler = []
        for kalem in kalemler:
            # Temel temizlik
            temiz_kalem = {}
            for key, value in kalem.items():
                if value and str(value).strip():
                    temiz_kalem[key] = str(value).strip()
            
            # Sayısal normalize
            miktar_num = None
            if 'miktar' in temiz_kalem:
                try:
                    miktar_num = float(self._normalize_amount(temiz_kalem['miktar']).replace(',', '.'))
                except Exception:
                    miktar_num = None
            birim_fiyat_num = self._parse_amount_to_float(temiz_kalem.get('birim_fiyat'))
            tutar_num = self._parse_amount_to_float(temiz_kalem.get('tutar'))

            # Eksik tutarı hesapla
            if tutar_num is None and miktar_num is not None and birim_fiyat_num is not None:
                calc = miktar_num * birim_fiyat_num
                temiz_kalem['tutar_hesap'] = f"{calc:,.2f}".replace(',', 'X').replace('.', ',').replace('X','.')
                tutar_num = calc

            # Normalize alanları ekle (raporlama için)
            if miktar_num is not None:
                temiz_kalem['miktar_num'] = miktar_num
            if birim_fiyat_num is not None:
                temiz_kalem['birim_fiyat_num'] = birim_fiyat_num
            if tutar_num is not None and 'tutar_num' not in temiz_kalem:
                temiz_kalem['tutar_num'] = tutar_num
            
            if temiz_kalem:
                temizlenmis_kalemler.append(temiz_kalem)

        # 🆕 YENİ: Regex tabanlı ürün kalemi parsing'i (yedek strateji)
        if not temizlenmis_kalemler:
            temizlenmis_kalemler = self._regex_ile_urun_kalemleri_cikar(ham_metin)
        
        return temizlenmis_kalemler

    def _regex_ile_urun_kalemleri_cikar(self, ham_metin: str) -> List[Dict]:
        """Regex desenleri kullanarak ürün kalemlerini çıkarır (yedek strateji)"""
        
        kalemler = []
        
        # 🆕 Gelişmiş ürün kalemi regex desenleri
        urun_patterns = [
            # Format: Açıklama + Miktar + Birim Fiyat + Tutar
            r'([A-ZÇĞİÖŞÜa-zçğıöşü\s\d\-\.]+(?:ML|KG|ADET|LİTRE|Q\s*KLAVYE|MOUSE|KARGO))\s+(\d+)\s*(?:adet|ad|piece|unit)?\s+(\d+[,\.]\d+\s*TL?)\s+(\d+[,\.]\d+\s*TL?)',
            
            # Format: Açıklama + Birim Fiyat + Tutar
            r'([A-ZÇĞİÖŞÜa-zçğıöşü\s\d\-\.]+(?:ML|KG|ADET|LİTRE|Q\s*KLAVYE|MOUSE|KARGO))\s+(\d+[,\.]\d+\s*TL?)\s+(\d+[,\.]\d+\s*TL?)',
            
            # Format: Açıklama + Tutar (basit)
            r'([A-ZÇĞİÖŞÜa-zçğıöşü\s\d\-\.]+(?:ML|KG|ADET|LİTRE|Q\s*KLAVYE|MOUSE|KARGO))\s+(\d+[,\.]\d+\s*TL?)',
            
            # Format: Ürün kodu + Açıklama + Tutar
            r'([A-Z0-9\-\.]+)\s+([A-ZÇĞİÖŞÜa-zçğıöşü\s\d\-\.]+(?:ML|KG|ADET|LİTRE))\s+(\d+[,\.]\d+\s*TL?)'
        ]
        
        for pattern in urun_patterns:
            matches = re.finditer(pattern, ham_metin, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                kalem = {}
                
                if len(match.groups()) >= 4:  # 4 grup: açıklama, miktar, birim_fiyat, tutar
                    kalem = {
                        'aciklama': match.group(1).strip(),
                        'miktar': match.group(2).strip(),
                        'birim_fiyat': match.group(3).strip(),
                        'tutar': match.group(4).strip()
                    }
                elif len(match.groups()) >= 3:  # 3 grup: açıklama, birim_fiyat, tutar
                    kalem = {
                        'aciklama': match.group(1).strip(),
                        'birim_fiyat': match.group(2).strip(),
                        'tutar': match.group(3).strip()
                    }
                elif len(match.groups()) >= 2:  # 2 grup: açıklama, tutar
                    kalem = {
                        'aciklama': match.group(1).strip(),
                        'tutar': match.group(2).strip()
                    }
                
                # Kalem geçerli mi kontrol et
                if kalem and self._kalem_gecerli_mi(kalem):
                    kalemler.append(kalem)
        
        return kalemler

    def _kalem_gecerli_mi(self, kalem: Dict) -> bool:
        """Kalem verisinin geçerli olup olmadığını kontrol eder"""
        
        # En azından açıklama olmalı
        if not kalem.get('aciklama'):
            return False
        
        # Açıklama çok kısa olmamalı (en az 3 karakter)
        if len(kalem['aciklama']) < 3:
            return False
        
        # Açıklama sadece sayısal değer olmamalı
        if kalem['aciklama'].replace(',', '').replace('.', '').replace('TL', '').replace(' ', '').isdigit():
            return False
        
        # Gereksiz kelimeleri filtrele
        gereksiz_kelimeler = ['fatura', 'tarih', 'toplam', 'kdv', 'iskonto', 'ödenecek', 'tutar']
        if any(gereksiz in kalem['aciklama'].lower() for gereksiz in gereksiz_kelimeler):
            return False
        
        return True

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
    
    def _parse_amount_to_float(self, amount: Optional[str]) -> Optional[float]:
        """Parasal string'i float'a çevirir (1.234,56 -> 1234.56)."""
        if not amount:
            return None
        s = amount.upper().replace('TL', '').replace('TRY', '').replace('₺', '').strip()
        s = re.sub(r'[^0-9.,]', '', s)
        s = s.replace('.', '').replace(',', '.')
        try:
            return float(s)
        except Exception:
            return None
    
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

    def _preprocess_raw_text(self, text: str) -> str:
        """Ham OCR metnini ön işler: sık OCR hatalarını ve boşluklarını normalize eder"""
        if not text:
            return ""
        # Yaygın OCR düzeltmeleri
        replacements = [
            ("\u2013", "-"), ("\u2014", "-"), ("—", "-"), ("–", "-"),
            ("\u00A0", " "), ("\ufeff", " "),
            (" OETTN", " ETTN"), ("ETTN ", "ETTN: "),
            (" İETTN", " ETTN"), ("E T T N", "ETTN"),
        ]
        for a,b in replacements:
            text = text.replace(a,b)
        # Satır sonu tire birleştirmeleri: "so-\n nuç" -> "sonuç"
        text = re.sub(r"-\s*\n\s*", "", text)
        # Çoklu boşlukları sadeleştir
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _detect_profile(self, text: str) -> str:
        """Metinden marka/profil tespiti (basit anahtar kelime temelli)"""
        low = text.lower()
        if 'flo' in low or 'kinetix' in low or 'polaris' in low:
            return 'FLO'
        if 'trendyol' in low or 'trendyolmail' in low:
            return 'TRENDYOL'
        if 'a101' in low or 'yeni mağazacılık' in low or 'a101.com.tr' in low:
            return 'A101'
        return 'GENEL'

    def _apply_consistency_rules(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Tutar alanlarında tutarlılık kontrolleri ve basit hesaplamalar uygular"""
        gt = data.get('genel_toplam')
        mh = data.get('mal_hizmet_toplam')
        kdv = data.get('hesaplanan_kdv')
        def parse_amount(x: Optional[str]) -> Optional[float]:
            if not x:
                return None
            y = x.upper().replace('TL','').replace('TRY','').replace('₺','').strip()
            y = y.replace('.', '').replace(',', '.')
            try:
                return float(y)
            except Exception:
                return None
        gt_v, mh_v, kdv_v = parse_amount(gt), parse_amount(mh), parse_amount(kdv)
        # Eğer genel_toplam yoksa ve mh+kdv mevcutsa hesapla
        if gt_v is None and mh_v is not None and kdv_v is not None:
            calc = mh_v + kdv_v
            data['genel_toplam'] = f"{calc:,.2f}".replace(',', 'X').replace('.', ',').replace('X','.')
        # Eğer küçük tutarsızlık varsa (≤ 0.02), genel_toplam'ı yuvarla
        elif gt_v is not None and mh_v is not None and kdv_v is not None:
            diff = abs(gt_v - (mh_v + kdv_v))
            if diff <= 0.02:
                calc = mh_v + kdv_v
                data['genel_toplam'] = f"{calc:,.2f}".replace(',', 'X').replace('.', ',').replace('X','.')
        return data

    def yapilandirilmis_veri_cikar(self, ocr_data: Dict, ham_metin: str) -> Dict:
        """
        [SON GÜNCELLEME] Faturadan yapılandırılmış veri çıkarmak için çok adımlı,
        etiket odaklı ve kapsamlı bir yöntem kullanır.
        """
        data: Dict[str, Any] = {}

        # Hızlı test modunda OCR verisi olmayabilir, bu durumu kontrol et
        is_fast_test = not any(ocr_data.values())

        # Adım 1: Faturayı mantıksal bloklara ayır
        satici_blok_text, alici_blok_text, toplamlar_blok_text = "", "", ""
        if not is_fast_test:
            blocks = self._bloklara_ayir(ocr_data)
            for block in blocks:
                label = self._blogu_tanimla(block['text'])
                if label == 'satici' and not satici_blok_text:
                    satici_blok_text = block['text']
                elif label == 'alici' and not alici_blok_text:
                    alici_blok_text = block['text']
                elif label == 'toplamlar' and not toplamlar_blok_text:
                    toplamlar_blok_text = block['text']

        # Aranacak metin kaynaklarını belirle (önce blok, yoksa tüm metin)
        satici_kaynak = satici_blok_text or ham_metin
        alici_kaynak = alici_blok_text or ham_metin
        toplamlar_kaynak = toplamlar_blok_text or ham_metin

        # Yardımcı Fonksiyon: Daha esnek ve bağlamsal arama
        def find_value(text_source: str, patterns: List[str]) -> Optional[str]:
            for pattern in patterns:
                match = re.search(pattern, text_source, re.IGNORECASE | re.DOTALL)
                if match:
                    for group in match.groups():
                        if group and group.strip():
                            return ' '.join(group.strip().split())
            return None

        para_desen = self.regex_desenleri['para']['desen']

        # Adım 2: Etiket odaklı veri çıkarma
        # 📌 SATICI
        data['satici_firma_unvani'] = find_value(satici_kaynak, [r'([A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜa-zçğıöşü\s&\-\.]+(?:A\.Ş\.|LTD\.|TİCARET|PAZARLAMA))'])
        data['satici_vergi_dairesi'] = find_value(satici_kaynak, [r'Vergi\s*Dairesi[\s:]+([A-Z\s]+)'])
        data['satici_vergi_numarasi'] = find_value(satici_kaynak, [r'Vergi\s*No[su]?[\s:]+(\d{10,11})', r'VKN[\s:]+(\d{10,11})'])
        data['satici_telefon'] = find_value(satici_kaynak, [r'Tel[\s:.]*([\d\s\+\(\)]+)'])
        data['satici_email'] = find_value(satici_kaynak, [r'E-?Posta[\s:]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'])
        data['satici_mersis_no'] = find_value(satici_kaynak, [r'Mersis\s*No[\s:]+(\d{16})'])
        data['satici_ticaret_sicil'] = find_value(satici_kaynak, [r'Ticaret\s*Sicil\s*No[\s:]+(\d+)'])
        
        # 📌 ALICI
        data['alici_firma_unvani'] = find_value(alici_kaynak, [r'(?:Sayın|ALICI)[\s:]+([A-ZÇĞİÖŞÜ\s\.]{4,})'])
        data['alici_tckn'] = find_value(alici_kaynak, [r'TCKN[\s:]+(\d{11})'])

        # 🆕 GELİŞMİŞ ALICI BİLGİLERİ - YENİ REGEX DESENLERİ
        if not data.get('alici_firma_unvani'):
            data['alici_firma_unvani'] = find_value(alici_kaynak, [self.regex_desenleri['alici_ad_soyad']['desen']])
        
        data['alici_adres'] = find_value(alici_kaynak, [self.regex_desenleri['alici_adres']['desen']])
        data['alici_email'] = find_value(alici_kaynak, [r'E-?Posta[\s:]+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'])
        data['alici_telefon'] = find_value(alici_kaynak, [r'Tel[\s:.]*([\d\s\+\(\)]+)'])

        # Ham metni ön işle
        ham_metin = self._preprocess_raw_text(ham_metin)
        profil = self._detect_profile(ham_metin)

        # 📌 FATURA
        data['fatura_numarasi'] = find_value(ham_metin, [r'(?:Fatura\s*No|Belge\s*No)[\s:]+([A-Z0-9/&\-]{8,25})', self.regex_desenleri['fatura_no']['desen']])
        data['fatura_tarihi'] = find_value(ham_metin, [r'Fatura\s*Tarihi[\s:]+(\d{1,2}\s*[./-]\s*\d{1,2}\s*[./-]\s*\d{2,4})', self.regex_desenleri['tarih']['desen']])
        data['ettn'] = find_value(ham_metin, [r'ETTN[\s:]+([A-Fa-f0-9]{8}-(?:[A-Fa-f0-9]{4}-){3}[A-Fa-f0-9]{12})', self.regex_desenleri['ettn']['desen']])
        data['fatura_tipi'] = find_value(ham_metin, [r'Fatura\s*Tipi[\s:]+([A-ZÇĞİÖŞÜa-zçğıöşü\s]+)'])

        # Profil bazlı küçük iyileştirmeler
        if profil == 'A101' and not data.get('fatura_numarasi'):
            data['fatura_numarasi'] = find_value(ham_metin, [r'\bA\d{15}\b'])

        # 🆕 YENİ FATURA BİLGİLERİ
        data['siparis_no'] = find_value(ham_metin, [self.regex_desenleri['siparis_no']['desen']])
        data['odeme_sekli'] = find_value(ham_metin, [self.regex_desenleri['odeme_sekli']['desen']])
        data['kargo_bilgisi'] = find_value(ham_metin, [self.regex_desenleri['kargo_bilgisi']['desen']])

        # 📌 TOPLAMLAR (bağlamlı)
        genel_toplam_desenleri = [
            r'(?:Ödenecek\s*Tutar[ı]?)\s*[:\-]?\s*(' + para_desen + ')',
            r'(?:Vergiler\s*Dahil\s*Toplam\s*Tutar[ı]?)\s*[:\-]?\s*(' + para_desen + ')',
            r'(?:Vergiler\s*Dahil\s*Toplam)\s*[:\-]?\s*(' + para_desen + ')',
            r'(?:Genel\s*Toplam(?:\s*Tutar[ı]?)?)\s*[:\-]?\s*(' + para_desen + ')',
            r'(?:Toplam\s*Tutar[ı]?)\s*[:\-]?\s*(' + para_desen + ')'
        ]
        data['genel_toplam'] = find_value(toplamlar_kaynak, genel_toplam_desenleri)
        if not data.get('genel_toplam'):
            data['genel_toplam'] = find_value(ham_metin, genel_toplam_desenleri)

        data['hesaplanan_kdv'] = find_value(toplamlar_kaynak, [r'Hesaplanan\s*KDV[\s:]+(' + para_desen + ')'])
        data['toplam_iskonto'] = find_value(toplamlar_kaynak, [r'Toplam\s*[İI]skonto[\s:]+(' + para_desen + ')'])
        data['mal_hizmet_toplam'] = find_value(toplamlar_kaynak, [r'Mal\s*Hizmet\s*Toplam\s*Tutar[ı]?[\s:]+(' + para_desen + ')'])

        # Fatura tipi normalize (gereksiz kuyrukları kes)
        if data.get('fatura_tipi'):
            ft = data['fatura_tipi']
            for kesici in ['Vergi', 'Dairesi', 'TCKN', 'Mersis', 'Belge', 'No']:
                if kesici in ft:
                    ft = ft.split(kesici)[0].strip()
                    break
            data['fatura_tipi'] = ft or data['fatura_tipi']

        # ETTN fallback: boşluk/noktalama normalize
        if not data.get('ettn'):
            packed = re.sub(r'\s+', '', ham_metin)
            ettn2 = re.findall(r'([A-Fa-f0-9]{8}-(?:[A-Fa-f0-9]{4}-){3}[A-Fa-f0-9]{12})', packed)
            if ettn2:
                data['ettn'] = ettn2[0]

        # Profil kurallarını uygula
        try:
            low = ham_metin.lower()
            for prof in (A101Profile(), FLOProfile(), TrendyolProfile()):
                if prof.applies(low):
                    data = prof.apply_rules(data, ham_metin)
        except Exception:
            pass

        # Tutarlılık kuralları uygula
        data = self._apply_consistency_rules(data)
        
        # Adım 3: Yedek Stratejiler
        if not data.get('fatura_numarasi'):
            data['fatura_numarasi'] = self._extract_first([
                r'\b([A-Z]{3}\d{13})\b',                 # FEA2023001157280
                r'\b([A-Z]{2,4}\d{12,15})\b',            # Genel harf+uzun sayı
                r'\b(A\d{15})\b',                         # A302023001485400 (A101)
                r'\b([A-Z]{1}\d{14,16})\b'               # Tek harf + uzun sayı toleransı
            ], ham_metin)
        if not data.get('genel_toplam'):
            data['genel_toplam'] = self._en_buyuk_tutari_bul(ham_metin)
        if not data.get('alici_tckn'):
            olasi_tckn_list = re.findall(r"(\d{11})", alici_kaynak)
            for olasi_tckn in olasi_tckn_list:
                if self._tckn_dogrula(olasi_tckn): data['alici_tckn'] = olasi_tckn; break
        
        # Adım 4: Kalemler ve Normalizasyon
        data['kalemler'] = self._urun_kalemlerini_cikar(ocr_data, ham_metin)
        
        # Boş değerleri temizle
        cleaned_data = {}
        for key, value in data.items():
            if key == 'kalemler':
                cleaned_data[key] = value
                continue
            if value and str(value).strip():
                cleaned_data[key] = str(value).strip()
        
        # Normalizasyon
        if cleaned_data.get('fatura_tarihi'):
            cleaned_data['fatura_tarihi'] = self._normalize_date(cleaned_data['fatura_tarihi'])
        amount_fields = ['mal_hizmet_toplam', 'toplam_iskonto', 'vergi_haric_tutar', 
                         'hesaplanan_kdv', 'vergiler_dahil_toplam', 'genel_toplam']
        for field in amount_fields:
            if cleaned_data.get(field):
                cleaned_data[field] = self._normalize_amount(cleaned_data[field])

        if not data.get('ettn'):
            # OCR kaynaklı benzer karakter hatalarını normalize edip tekrar dene
            ocr_norm = ham_metin.replace('O', '0').replace('I', '1').replace('l', '1')
            ettn_kandidatlar = re.findall(r'([A-Fa-f0-9]{8}-(?:[A-Fa-f0-9]{4}-){3}[A-Fa-f0-9]{12})', ocr_norm)
            if ettn_kandidatlar:
                data['ettn'] = ettn_kandidatlar[0]

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
                
                # --- YENİ: Bulunan değeri de yazdır ---
                if benzersiz_eslemeler: # Sadece bir şey bulunduysa değerleri yazdır
                    print(f"      ✅ {len(benzersiz_eslemeler)} adet {kategori} bulundu: {benzersiz_eslemeler}")
                else:
                    print(f"      ❌ {kategori} bulunamadı")
                
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
        
        # --- ÖNCEKİ HATA AYIKLAMA KODUNU KALDIRIP YENİDEN EKLEYELİM ---
        # Bu bölüm, önceki adımlardan kalmıştı ve PDF hatasına neden oluyordu.
        # Şimdi bunu da düzelterek sorunu tamamen çözüyoruz.
        processed_img = self.resmi_on_isle(img)
        
        # Hata ayıklama için standart işlenmiş resmi kaydet
        base_name, _ = os.path.splitext(os.path.basename(dosya_yolu))
        debug_dosya_adi = f"debug_processed_{base_name}.png" # PDF yüklenirse hata vermemesi için uzantıyı .png yap
        # Çıktı klasörü main'den set edildiyse onu kullan, yoksa test_reports
        output_dir = getattr(self, 'output_dir', 'test_reports')
        os.makedirs(output_dir, exist_ok=True)
        debug_dosya_yolu = os.path.join(output_dir, debug_dosya_adi)
        cv2.imwrite(debug_dosya_yolu, processed_img)
        print(f"🐛 Standart hata ayıklama resmi kaydedildi: {debug_dosya_yolu}")
        
        # 3. OCR ile metni çıkar (İlk Deneme)
        ocr_data, avg_confidence = self.metni_cikar(processed_img)
        
        # 4. Ham metni oluştur ve kontrol et
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
        # 6b. Alan-bazlı OCR fallback (eksikler için)
        structured_data = self._field_level_ocr_fallback(processed_img, structured_data, ham_metin)
        
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
                "ham_metin_uzunlugu": len(ham_metin),
                "ham_metin": ham_metin
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
            
            # Önemli alanları grupla ve yazdır (korumalı erişim)
            önemli_bulunanlar = {}
            for alan in getattr(self, 'onemli_alanlar', []):
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


def test_yeni_regex_desenleri():
    """🆕 Yeni eklenen regex desenlerini test eder"""
    
    print("🧪 YENİ REGEX DESENLERİ TEST EDİLİYOR...")
    print("="*60)
    
    # Test metinleri (gerçek faturalardan alınan örnekler)
    test_metinleri = [
        {
            'name': 'Trendyol Fatura Örneği',
            'text': '''
            SAYIN Gokhan Çağaptay
            ADRES: Malatya / Battalgazi
            ÜRÜN: Herbal Science Boom Butter Saç Bakım Yağı 190 ML, 4 adet
            BİRİM FİYAT: 104,17 TL
            ÖDEME: Kredi Kartı (Trendyol temlik hesabı)
            KARGO: PTT Kargo
            SİPARİŞ NO: TY0725295
            '''
        },
        {
            'name': 'A101 Fatura Örneği',
            'text': '''
            SAYIN Gökhan Çağaptay
            ADRES: Antalya / Gazipaşa
            ÜRÜN: Kablosuz Mouse Mobile 1850 (1 adet, 160,17 TL)
            KARGO BEDELİ: Kargo Bedeli (1 adet, 12,63 TL)
            ÖDEME: E-Ticaret Kredi Kartı
            KARGO: MNG KARGO YURTİÇİ VE YURTDIŞI
            SİPARİŞ NO: A101-2023-001
            '''
        },
        {
            'name': 'Hacı Şekeroğlu Fatura Örneği',
            'text': '''
            SAYIN MEHMET EMIR ARSLAN
            ADRES: Malatya / Battalgazi
            ÜRÜN: HP Pavilion 800 Q Klavye (1 adet, 748,50 TL)
            ÖDEME: Bilgi yok
            SİPARİŞ NO: HS-2023-169
            '''
        }
    ]
    
    # Sistem başlat
    analiz_sistemi = FaturaRegexAnaliz()
    
    for test_case in test_metinleri:
        print(f"\n📋 TEST: {test_case['name']}")
        print("-" * 40)
        
        # Regex ile veri çıkar
        regex_sonuclari = analiz_sistemi.regex_ile_veri_cikar(test_case['text'])
        
        # Yeni regex desenlerini kontrol et
        yeni_desenler = ['alici_ad_soyad', 'alici_adres', 'urun_aciklama', 'urun_miktar', 
                         'birim_fiyat', 'odeme_sekli', 'kargo_bilgisi', 'siparis_no']
        
        print("🔍 YENİ REGEX DESENLERİ SONUÇLARI:")
        for desen in yeni_desenler:
            if desen in regex_sonuclari and regex_sonuclari[desen]:
                print(f"   ✅ {desen}: {regex_sonuclari[desen]}")
            else:
                print(f"   ❌ {desen}: Bulunamadı")
        
        print()
    
    print("🎯 YENİ REGEX TEST TAMAMLANDI!")
    print("="*60)


if __name__ == "__main__":
    # Ana test fonksiyonu
    main()
    
    # 🆕 Yeni regex desenlerini test et
    test_yeni_regex_desenleri()
