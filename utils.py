import re
import logging


def norm_amount(value: str) -> str:
    if not value:
        return ''
    text = str(value).upper().replace('TL', '').replace('TRY', '').replace('₺', '').strip()
    text = re.sub(r'[^0-9.,]', '', text)
    text = text.replace('.', '').replace(',', '.')
    try:
        val = float(text)
        return f"{val:.2f}"
    except Exception:
        return ''


def norm_date(value: str) -> str:
    if not value:
        return ''
    text = re.sub(r'[^0-9./\-]', '', str(value))
    text = re.sub(r"\s*[/\-.]\s*", '-', text)
    return text


def validate_patterns_structure(patterns: dict, logger: logging.Logger) -> None:
    if not isinstance(patterns, dict):
        logger.error("Patterns yapısı dict değil.")
        return
    for key, item in patterns.items():
        if not isinstance(item, dict):
            logger.warning(f"Pattern '{key}' nesnesi dict değil, atlanacak.")
            continue
        desen = item.get('desen')
        if not isinstance(desen, str) or not desen.strip():
            logger.warning(f"Pattern '{key}' için geçersiz/boş 'desen' alanı.")

