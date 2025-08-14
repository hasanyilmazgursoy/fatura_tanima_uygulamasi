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
                # FEA2023001157280 tarzı alfanumerik fatura numaraları
                'desen': r'(?:fatura\s*no|fatura\s*numarası|invoice\s*no)[\s:]*([A-Z0-9]{8,20})\b|\b[A-Z]{2,4}\d{8,15}\b',
                'aciklama': 'Fatura numaraları (FEA2023001157280)',
                'ornek': 'FEA2023001157280'
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
        for i in range(anchor_word_idx + 1, n):
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
    
    def _normalize_amount(self, amount: str) -> str:
        """Tutar değerini normalize et."""
        if not amount:
            return ""
        # Gereksiz karakterleri temizle
        cleaned = re.sub(r'[|\s]', '', amount)
        # Sadece rakam, nokta, virgül ve para birimi sembolleri bırak
        cleaned = re.sub(r'[^0-9.,TL₺TRYERUSD]', '', cleaned)
        return cleaned
    
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
        Hibrit bir yaklaşımla (koordinat + regex) fatura verilerini çıkarır.
        Önce anahtar kelimelerin yanındaki değerleri koordinatlarla arar,
        bulamazsa tüm metinde RegEx ile yedek arama yapar.
        """
        data: Dict[str, Optional[str]] = {}
        
        # 1. ADIM: EVRENSEL FORMATLARI REGEX İLE DOĞRUDAN ÇIKAR
        # Bu desenler (email, ETTN) genellikle fatura üzerinde tekildir ve güvenilirdir.
        data['satici_email'] = self._extract_first([r'\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b'], ham_metin)
        data['ettn'] = self._extract_first([r'\b([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\b'], ham_metin, flags=re.IGNORECASE)
        data['para_birimi'] = self._extract_first([r"\b(TRY|TL|₺|USD|EUR|GBP)\b"], ham_metin)

        # 2. ADIM: HİBRİT YAKLAŞIMLA (KOORDİNAT + REGEX) ALANLARI ÇIKAR
        # Tanimlamalar: `anahtar`: ( (koordinat_anahtar_kelimeleri, değer_regex), [yedek_regex_desenleri] )
        extraction_map = {
            'fatura_numarasi': (
                # Koordinat arama desenini daha esnek hale getiriyoruz.
                (['fatura no', 'faturano', 'fatura numarası', 'invoice no'], r'([A-Z0-9\-\/.]{6,20})'), 
                # Yedek desenler, spesifik formatlar için kalabilir.
                [r"\b(?!irsaliye)([A-Z]{2,4}\d{12,15})\b", r"\b(?!irsaliye)([A-Z]\d{14,16})\b"]
            ),
            'fatura_tarihi': (
                (['fatura tarihi', 'düzenleme tarihi', 'tarih'], r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})'),
                [r"\b(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})\b"] # En bariz tarih
            ),
            'son_odeme_tarihi': (
                (['son ödeme tarihi', 'ödeme tarihi'], r'(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})'), []
            ),
            'fatura_tipi': (
                (['fatura tipi', 'tipi'], r'([e\-]?(?:arşiv|arsiv|fatura|proforma|irsaliye)(?:\s*fatura)?)'),
                [r"\b(e-?(?:arşiv|arsiv|fatura))\b"]
            ),
            'satici_firma_unvani': (
                (['firma adı', 'firma adi', 'satıcı', 'satici'], r'([A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜa-zçğıöşü\s&\-\.]+(?:A\.Ş\.|LTD\.)?)'),
                [r"(?:^|\n)([A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜa-zçğıöşü\s&\-\.]+(?:A\.Ş\.|LTD\.|MAĞ\.|PAZ\.))"]
            ),
            'satici_vergi_dairesi': (
                (['vergi dairesi', 'v.d.'], r'([A-ZÇĞİÖŞÜ\s]+)'), []
            ),
            'satici_vergi_numarasi': (
                (['vergi numarası', 'vergi no', 'vkn'], r'(\d{10,11})'),
                [r'\b(\d{10})\b'] # Etiketsiz 10 haneli numara
            ),
            'satici_ticaret_sicil': (
                (['ticaret sicil', 'sicil no'], r'(\d{6,10})'), []
            ),
            'satici_mersis_no': (
                (['mersis no', 'mersis'], r'(\d{15})'), []
            ),
            'alici_firma_unvani': (
                (['sayın', 'alici', 'alıcı', 'müşteri', 'müsteri'], r'([A-ZÇĞİÖŞÜa-zçğıöşü\s\-\.]{4,})'),
                []
            ),
            'alici_vergi_dairesi': (
                (['vergi dairesi', 'v.d.'], r'([A-ZÇĞİÖŞÜ\s]+)'), [] # Satıcı ile aynı, OCR verisinde hangisini önce bulursa...
            ),
             'mal_hizmet_toplam': (
                (['mal hizmet toplam', 'ara toplam'], self.regex_desenleri['para']['desen']), []
            ),
            'toplam_iskonto': (
                (['toplam iskonto', 'indirim'], self.regex_desenleri['para']['desen']), []
            ),
            'vergi_haric_tutar': (
                (['vergi hariç tutar', 'vergi haric', 'alt toplam'], self.regex_desenleri['para']['desen']), []
            ),
            'hesaplanan_kdv': (
                (['hesaplanan kdv', 'toplam kdv', 'kdv'], self.regex_desenleri['para']['desen']), []
            ),
            'vergiler_dahil_toplam': (
                (['vergiler dahil toplam', 'toplam tutar'], self.regex_desenleri['para']['desen']), []
            ),
            'genel_toplam': (
                (['ödenecek tutar', 'genel toplam', 'toplam'], self.regex_desenleri['para']['desen']), []
            ),
        }

        # Adresleri ve diğer çok satırlı alanları özel fonksiyonla ara
        stop_keywords = ['vergi dairesi', 'v.d.', 'vergi no', 'vkn', 'telefon', 'tel', 'email', 'e-posta', 'web']
        data['satici_adres'] = self._find_multiline_value_below_keyword(ocr_data, ['adres'], stop_keywords)
        # Alıcı adresi için hem "adres" hem de "sayın" gibi anahtar kelimeler referans olabilir
        data['alici_adres'] = self._find_multiline_value_below_keyword(ocr_data, ['alıcı', 'alici', 'sayın'], stop_keywords)


        for field, (coord_rule, fallback_patterns) in extraction_map.items():
            # Eğer veri zaten bulunduysa (örn: adres), tekrar arama
            if data.get(field) is not None:
                continue

            keywords, value_pattern = coord_rule
            
            # 1. Yöntem: Koordinat tabanlı arama
            value = self._find_value_right_of_keywords(ocr_data, keywords, value_pattern)

            # Alıcı Adı için ek filtreleme
            if field == 'alici_firma_unvani' and value:
                anlamsiz_kelimeler = ['no', 'fatura', 'adres', 'tarih', 'ödeme', 'vkn']
                if len(value.strip()) < 4 or any(kelime in value.lower() for kelime in anlamsiz_kelimeler):
                    value = None # Değeri geçersiz say
            
            # 2. Yöntem: Eğer koordinat ile bulunamazsa, yedek RegEx'leri tüm metinde dene
            if not value and fallback_patterns:
                value = self._extract_first(fallback_patterns, ham_metin)
            
            data[field] = value

        # 3. ADIM: ÖZEL KURALLAR VE HEURİSTİKLER (SEZGİSEL YÖNTEMLER)
        
        # TCKN: 11 haneli ve algoritma ile doğrulanabilir olduğu için özel olarak aranır.
        olasi_tckn_list = self._extract_all(r"(\d{11})", ham_metin)
        for olasi_tckn in olasi_tckn_list:
            if self._tckn_dogrula(olasi_tckn):
                data['alici_tckn'] = olasi_tckn
                break # İlk geçerli olanı al
        
        # Genel Toplam için son çare: Eğer hiçbir şekilde bulunamadıysa, faturadaki en büyük tutarı al.
        if not data.get('genel_toplam'):
            data['genel_toplam'] = self._en_buyuk_tutari_bul(ham_metin)
            
        # 4. ADIM: VERİYİ TEMİZLE VE NORMALIZE ET
        
        # Normalizasyon gerektiren alanlar
        if data.get('fatura_tarihi'):
            data['fatura_tarihi'] = self._normalize_date(data['fatura_tarihi'])
        if data.get('son_odeme_tarihi'):
            data['son_odeme_tarihi'] = self._normalize_date(data['son_odeme_tarihi'])
            
        amount_fields = ['mal_hizmet_toplam', 'toplam_iskonto', 'vergi_haric_tutar', 
                         'hesaplanan_kdv', 'vergiler_dahil_toplam', 'genel_toplam']
        for field in amount_fields:
            if data.get(field):
                data[field] = self._normalize_amount(data[field])
        
        # ==================== ÜRÜN LİSTESİ (KALEMLERİ) ====================
        
        # Ürün listesi - gelişmiş kolon analizi
        def extract_product_items(ocr: Dict) -> List[Dict]:
            """Ürün listesini tablo formatından çıkar."""
            if 'text' not in ocr:
                return []
                
            products = []
            n = len(ocr.get('text', []))
            
            # Ürün anahtar kelimelerini ara
            product_keywords = ['u.s. polo', 'salvano', 'sneaker', 'erkek', 'siyah', 'beyaz']
            product_lines = []
            
            for i in range(n):
                try:
                    if int(ocr['conf'][i]) < self.min_confidence:
                        continue
                except (ValueError, IndexError):
                    continue
                
                text = (ocr['text'][i] or '').lower()
                for keyword in product_keywords:
                    if keyword in text and len(text) > 5:
                        y = ocr['top'][i]
                        # Aynı satırdaki diğer bilgileri topla
                        line_items = []
                        for j in range(max(0, i-5), min(n, i+10)):
                            try:
                                if int(ocr['conf'][j]) < self.min_confidence:
                                    continue
                            except (ValueError, IndexError):
                                continue
                            
                            y_candidate = ocr['top'][j]
                            if abs(y_candidate - y) < 15:
                                line_items.append(ocr['text'][j] or '')
                        
                        if line_items:
                            product_info = {
                                'urun_adi': ' '.join([item for item in line_items if len(item) > 3]),
                                'satir_y': y
                            }
                            product_lines.append(product_info)
                        break
            
            # Ürün listesini temizle ve sınırla
            seen_products = set()
            for product in product_lines[:5]:  # En fazla 5 ürün
                name = product['urun_adi'][:100]  # Adı kısalt
                if name and name not in seen_products:
                    products.append({'urun_adi': name})
                    seen_products.add(name)
            
            return products
        
        data['kalemler'] = extract_product_items(ocr_data)
        
        # Miktar ve birim fiyat örnekleri
        data['miktar_ornekleri'] = self._extract_all(r"\b(\d{1,4})\s*(?:çift|adet|kg|paket|kutu)\b", ham_metin)[:3]
        data['birim_fiyat_ornekleri'] = self._extract_all(r"\b([0-9]{1,4}[.,][0-9]{2})\s*(?:tl|₺|try)?\b", ham_metin)[:5]
        
        # ==================== NORMALIZE ET ====================
        
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

    def metni_cikar(self, img: np.ndarray, dil: str = 'tur') -> Dict:
        """
        Resimden OCR kullanarak metin ve koordinat bilgilerini çıkarır.
        
        Args:
            img (np.ndarray): İşlenmiş resim
            dil (str): OCR dili ('tur' veya 'eng')
            
        Returns:
            Dict: OCR sonuçları (text, conf, left, top, width, height listeleri)
        """
        print("🤖 OCR ile metin çıkarma başlatılıyor...")
        
        try:
            # İlk OCR denemesi
            ocr_data = pytesseract.image_to_data(img, config=self.ocr_config, output_type=pytesseract.Output.DICT)
            
            # Ortalama güven skorunu kontrol et
            confidences = [int(conf) for conf in ocr_data['conf'] if str(conf).isdigit()]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            print(f"   📊 Ortalama güven skoru: {avg_confidence:.1f}%")
            
            # Düşük güven skorunda alternatif PSM dene
            if avg_confidence < 50:
                print("   🔄 Düşük güven skoru, PSM 4 deneniyor...")
                alternative_config = f'--oem 3 --psm 4 -l tur+eng'
                ocr_data_alt = pytesseract.image_to_data(img, config=alternative_config, output_type=pytesseract.Output.DICT)
                
                confidences_alt = [int(conf) for conf in ocr_data_alt['conf'] if str(conf).isdigit()]
                avg_confidence_alt = sum(confidences_alt) / len(confidences_alt) if confidences_alt else 0
                
                if avg_confidence_alt > avg_confidence:
                    print(f"   ✅ PSM 4 daha iyi sonuç verdi: {avg_confidence_alt:.1f}%")
                    ocr_data = ocr_data_alt
                    avg_confidence = avg_confidence_alt
            
            # Sonuçları filtrele
            valid_count = len([conf for conf in ocr_data['conf'] if int(conf) >= self.min_confidence])
            total_count = len(ocr_data['conf'])
            
            print(f"   ✅ OCR tamamlandı: {valid_count}/{total_count} adet güvenilir metin bulundu")
            
            return ocr_data
            
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
            }

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
        ocr_data = self.metni_cikar(processed_img)
        
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
