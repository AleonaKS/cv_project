# backend/video/shots.py
import cv2
import numpy as np


def detect_shots(video_path, threshold=0.6, min_shot_duration=2.0, max_shots=50):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    
    if fps <= 0:
        fps = 25

    prev_hist = None
    shots = [0.0]
    frame_idx = 0
    last_shot_time = 0.0
    shot_count = 0

    while True:
        ret, frame = cap.read()
        if not ret or shot_count >= max_shots:
            break

        # Используем цветные гистограммы для большей точности
        small_frame = cv2.resize(frame, (320, 180))
        
        # Гистограммы для каждого канала
        hist_b = cv2.calcHist([small_frame], [0], None, [32], [0, 256])
        hist_g = cv2.calcHist([small_frame], [1], None, [32], [0, 256])
        hist_r = cv2.calcHist([small_frame], [2], None, [32], [0, 256])
        
        hist_b = cv2.normalize(hist_b, hist_b).flatten()
        hist_g = cv2.normalize(hist_g, hist_g).flatten()
        hist_r = cv2.normalize(hist_r, hist_r).flatten()
        
        # Объединяем гистограммы
        current_hist = np.concatenate([hist_b, hist_g, hist_r])

        if prev_hist is not None:
            # Сравниваем с использованием нескольких метрик
            correlation = cv2.compareHist(prev_hist, current_hist, cv2.HISTCMP_CORREL)
            chi_square = cv2.compareHist(prev_hist, current_hist, cv2.HISTCMP_CHISQR)
            
            current_time = frame_idx / fps
            
            # Комбинированная логика детекции
            significant_change = (
                correlation < threshold or 
                chi_square > (1 - threshold) * 100
            )
            
            sufficient_time_passed = (current_time - last_shot_time) >= min_shot_duration
            
            if significant_change and sufficient_time_passed:
                shots.append(round(current_time, 2))
                last_shot_time = current_time
                shot_count += 1

        prev_hist = current_hist
        frame_idx += 1

    cap.release()
    return shots
