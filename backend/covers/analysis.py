# backend/covers/analysis.py
import cv2
import numpy as np
from sklearn.cluster import KMeans
from backend.covers.placeholder import is_placeholder as check_placeholder  # ИЗМЕНИЛ ИМЯ
from backend.covers.colors import color_contrast, warm_cold_ratio
from backend.covers.face import detect_faces
from backend.covers.composition import face_position
from backend.covers.placeholder_ocr import detect_placeholder_text


def dominant_colors(image, n_colors=3):
    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    img = img.reshape((-1, 3))
    kmeans = KMeans(n_clusters=n_colors, random_state=42).fit(img)
    return kmeans.cluster_centers_.astype(int)

def text_density(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    area = image.shape[0] * image.shape[1]
    return sum(cv2.contourArea(c) for c in contours) / area

def edge_density(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    return np.sum(edges > 0) / edges.size

def negative_space_ratio(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    return 1 - (np.sum(edges > 0) / edges.size)


def analyze_cover(image):
    # ИСПРАВЛЕНИЕ: используем новое имя функции
    placeholder_visual = check_placeholder(image) 
    placeholder_ocr = detect_placeholder_text(image)

    # ИСПРАВЛЕНИЕ: используем новое имя переменной
    is_placeholder_result = (
        placeholder_visual["is_placeholder"] or
        placeholder_ocr["is_placeholder_text"]
    )

    # --- ВСЁ СЧИТАЕМ В ЛЮБОМ СЛУЧАЕ ---
    colors = dominant_colors(image)
    text = text_density(image)
    edge = edge_density(image)
    negative = negative_space_ratio(image)

    complexity = 0.4 * edge + 0.3 * text + 0.3 * (1 - negative)
    contrast = color_contrast(colors)
    warmth = warm_cold_ratio(colors)

    try:
        faces = detect_faces(image)
        face_pos = face_position(image, faces)
    except Exception:
        faces = []
        face_pos = "no_face"

    has_face = len(faces) > 0

    if complexity < 0.2:
        label = "минималистичная"
    elif complexity < 0.4:
        label = "сбалансированная"
    else:
        label = "перегруженная"

    result = {
        "type": "placeholder" if is_placeholder_result else "normal",  # ИСПРАВЛЕНИЕ

        "placeholder": {
            "visual": placeholder_visual,
            "ocr": placeholder_ocr
        },

        "colors": colors.tolist(),
        "text_density": round(text, 3),
        "edge_density": round(edge, 3),
        "negative_space": round(negative, 3),
        "complexity": round(complexity, 3),
        "color_contrast": round(contrast, 2),
        "warm_cold_balance": round(warmth, 2),
        "face": has_face,
        "face_position": face_pos,
        "design": label,
    }

    if is_placeholder_result:  
        result["message"] = "Обложка скоро появится"

    return result
