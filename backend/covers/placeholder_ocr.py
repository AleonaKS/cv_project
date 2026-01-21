# backend/covers/placeholder_ocr.py
import cv2
import pytesseract
import re
import numpy as np

PLACEHOLDER_PATTERNS = [
    r"обложка\s+скоро",
    r"скоро\s+появ",
    r"coming\s+soon", 
    r"cover\s+coming",
    r"no\s+cover",
    r"image\s+not\s+available",
    r"cover\s+not\s+available"
]

def preprocess_for_ocr(image):
    """Улучшает изображение для OCR"""
    # Конвертируем в grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Увеличиваем контраст
    gray = cv2.equalizeHist(gray)
    
    # Бинаризация Оцу
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Убираем шум
    kernel = np.ones((2,2), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    return thresh

def detect_placeholder_text(image, min_confidence=30):
    """Улучшенный OCR для определения текста заглушек"""
    
    processed = preprocess_for_ocr(image)
    
    # Пробуем разные конфигурации OCR
    configs = [
        '--psm 6',      # Единый блок текста
        '--psm 7',      # Одна строка текста
        '--psm 8',      # Одно слово
        '--psm 13'      # Сырой текст
    ]
    
    all_found_phrases = []
    
    for config in configs:
        try:
            data = pytesseract.image_to_data(
                processed,
                lang='rus+eng',
                config=config,
                output_type=pytesseract.Output.DICT
            )
            
            for i, text in enumerate(data['text']):
                if not text.strip():
                    continue
                    
                conf = int(data['conf'][i])
                if conf < min_confidence:
                    continue
                
                text_lower = text.lower()
                for pattern in PLACEHOLDER_PATTERNS:
                    if re.search(pattern, text_lower):
                        all_found_phrases.append(text.strip())
                        
        except Exception as e:
            print(f"OCR error with config {config}: {e}")
            continue
    
    # Также пробуем простой текст без конфигурации
    try:
        simple_text = pytesseract.image_to_string(processed, lang='rus+eng')
        if simple_text:
            simple_text_lower = simple_text.lower()
            for pattern in PLACEHOLDER_PATTERNS:
                if re.search(pattern, simple_text_lower):
                    all_found_phrases.extend([t.strip() for t in simple_text.split('\n') if t.strip()])
    except Exception as e:
        print(f"Simple OCR error: {e}")
    
    return {
        "is_placeholder_text": len(all_found_phrases) > 0,
        "found_phrases": list(set(all_found_phrases)),
        "confidence": "high" if len(all_found_phrases) > 0 else "low"
    }
