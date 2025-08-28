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


# --- Görüntü Ön İşleme Preset'leri ---
import cv2
import numpy as np


def _deskew_image(gray_image: np.ndarray) -> np.ndarray:
    # Basit minAreaRect tabanlı eğrilik düzeltme
    coords = np.column_stack(np.where(gray_image < 255))
    if coords.size == 0:
        return gray_image
    rect = cv2.minAreaRect(coords[:, ::-1])
    angle = rect[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = gray_image.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    rotated = cv2.warpAffine(gray_image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated


def preprocess_image(bgr_image: np.ndarray, preset: str = 'auto') -> np.ndarray:
    # Giriş BGR; çıkış ikili/iyileştirilmiş gri olabilir
    gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)

    if preset == 'scan':
        denoised = cv2.medianBlur(gray, 3)
        _, th = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        opened = cv2.morphologyEx(th, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        return opened

    if preset == 'skew':
        denoised = cv2.medianBlur(gray, 3)
        _, th = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        deskewed = _deskew_image(th)
        return deskewed

    if preset == 'clean':
        th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 31, 15)
        return th

    # auto: basit heuristik
    mean_intensity = gray.mean()
    if mean_intensity < 140:
        return preprocess_image(bgr_image, 'scan')
    return preprocess_image(bgr_image, 'clean')


# --- Guardian Post-Process ---
def guardian_postprocess(data: dict) -> dict:
    if not isinstance(data, dict):
        return data
    cleaned = dict(data)
    for key in list(cleaned.keys()):
        val = cleaned.get(key)
        if val is None:
            continue
        k = key.lower()
        if 'tarih' in k:
            cleaned[key] = norm_date(val)
        if any(tok in k for tok in ['tutar', 'toplam', 'kdv']):
            amt = norm_amount(val)
            # 0 veya aşırı uçlara basit filtre
            if amt and (len(amt) <= 12):
                cleaned[key] = amt
    return cleaned

