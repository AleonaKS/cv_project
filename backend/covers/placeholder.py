import cv2
import numpy as np
from backend.covers.placeholder_ocr import detect_placeholder_text


def is_placeholder(
        image,
        white_thresh=240,
        white_ratio_thresh = 0.45,
        edge_thresh = 0.05,
        text_thresh = 0.03
    ):

    """
    Определяет, является ли обложка заглушкой
    """

    h, w, _ = image.shape
    area = h * w

    # --- 1. Доля белого цвета ---
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    white_pixels = np.sum(gray > white_thresh)
    white_ratio = white_pixels / area

    # --- 2. Плотность краёв ---
    edges = cv2.Canny(gray, 100, 200)
    edge_density = np.sum(edges > 0) / edges.size

    # --- 3. Плотность "текста" (контуры) ---
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    text_area = sum(cv2.contourArea(c) for c in contours)
    text_density = text_area / area

    # --- Логика принятия решения ---
    is_blank = (
    white_ratio > white_ratio_thresh and
    edge_density < edge_thresh and
    text_density < text_thresh  
    )


    return {
        "is_placeholder": bool(is_blank),
        "white_ratio": round(white_ratio, 3),
        "edge_density": round(edge_density, 3),
        "text_density": round(text_density, 3)
    }
