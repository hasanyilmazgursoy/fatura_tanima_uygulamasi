from typing import Dict


class ProfileRule:
    """Profil kuralı arayüzü."""

    name: str = 'GENEL'

    def applies(self, text_lower: str) -> bool:
        return False

    def apply_rules(self, data: Dict, text: str) -> Dict:
        """Çıkarılmış veriye profil bazlı küçük düzeltmeler uygular."""
        return data


