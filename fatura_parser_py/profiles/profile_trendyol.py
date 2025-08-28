from typing import Dict
from .profile_base import ProfileRule
import re


class TrendyolProfile(ProfileRule):
    name = 'TRENDYOL'

    def applies(self, text_lower: str) -> bool:
        return ('trendyol' in text_lower) or ('trendyolmail' in text_lower)

    def apply_rules(self, data: Dict, text: str) -> Dict:
        # Sipariş no ve ETTN güçlendirme
        if not data.get('siparis_no'):
            m = re.search(r'(?:SİPARİŞ|SIPARIS|ORDER)\s*(?:NO|NUMARASI)?\s*[:\-]?\s*([A-Z0-9\-]{6,25})', text, re.IGNORECASE)
            if m:
                data['siparis_no'] = m.group(1)
        return data


