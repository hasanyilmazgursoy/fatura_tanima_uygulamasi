from typing import Dict
from .profile_base import ProfileRule


class FLOProfile(ProfileRule):
    name = 'FLO'

    def applies(self, text_lower: str) -> bool:
        return ('flo' in text_lower) or ('kinetix' in text_lower) or ('polaris' in text_lower)

    def apply_rules(self, data: Dict, text: str) -> Dict:
        # FLO kalem başlıkları farklı varyantlarda; fatura tipi ve alan temizliği
        if data.get('fatura_tipi'):
            data['fatura_tipi'] = data['fatura_tipi'].replace('TCKN', '').strip()
        return data


