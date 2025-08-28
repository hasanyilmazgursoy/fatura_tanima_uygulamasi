from typing import Dict
from .profile_base import ProfileRule
import re


class A101Profile(ProfileRule):
    name = 'A101'

    def applies(self, text_lower: str) -> bool:
        return ('a101' in text_lower) or ('yeni mağazacılık' in text_lower) or ('a101.com.tr' in text_lower)

    def apply_rules(self, data: Dict, text: str) -> Dict:
        # Fatura no fallback: A + 15 hane
        if not data.get('fatura_numarasi'):
            m = re.search(r'\bA\d{15}\b', text)
            if m:
                data['fatura_numarasi'] = m.group(0)

        # Genel toplam varyantları
        if not data.get('genel_toplam'):
            m = re.search(r'(?:Ödenecek\s*Tutar|Genel\s*Toplam|Vergiler\s*Dahil\s*Toplam)\s*[:\-]?\s*(\d{1,3}(?:\.\d{3})*,\d{2})', text, re.IGNORECASE)
            if m:
                data['genel_toplam'] = m.group(1)

        return data


