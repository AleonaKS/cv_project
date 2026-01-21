# # backend/video/shots_improved.py
# import cv2
# import numpy as np
# from .skater_detector import SkaterDetector

# class ImprovedShotDetector:
#     def __init__(self):
#         self.skater_detector = SkaterDetector()
        
#     def detect_shots_by_background(self, video_path, threshold=0.7, motion_threshold=0.1):
#         """Улучшенная детекция смены планов с фильтрацией движения фигуриста"""
#         cap = cv2.VideoCapture(video_path)
#         fps = cap.get(cv2.CAP_PROP_FPS) or 25
        
#         shots = [0.0]
#         prev_background_hist = None
#         frame_idx = 0
#         last_shot_time = 0.0
        
#         sample_interval = max(1, int(fps / 5))
#         prev_frame = None
        
#         while True:
#             ret, frame = cap.read()
#             if not ret:
#                 break
                
#             if frame_idx % sample_interval != 0:
#                 frame_idx += 1
#                 continue
            
#             # Детекция фигуриста и удаление его из кадра
#             frame_without_skater, bbox = self.skater_detector.detect_skater(frame)
            
#             if frame_without_skater is None:
#                 continue
            
#             # Фильтрация по движению камеры (если предыдущий кадр есть)
#             if prev_frame is not None:
#                 # Сравниваем только фон (без фигуриста)
#                 prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
#                 curr_gray = cv2.cvtColor(frame_without_skater, cv2.COLOR_BGR2GRAY)
                
#                 flow = cv2.calcOpticalFlowFarneback(prev_gray, curr_gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
#                 motion_magnitude = np.sqrt(flow[...,0]**2 + flow[...,1]**2)
#                 avg_motion = np.mean(motion_magnitude)
                
#                 # Пропускаем кадры с сильным движением камеры
#                 if avg_motion > motion_threshold:
#                     prev_frame = frame_without_skater
#                     frame_idx += 1
#                     continue
            
#             # Анализ фона
#             background_frame = cv2.resize(frame_without_skater, (320, 180))
            
#             hist_b = cv2.calcHist([background_frame], [0], None, [32], [0, 256])
#             hist_g = cv2.calcHist([background_frame], [1], None, [32], [0, 256])
#             hist_r = cv2.calcHist([background_frame], [2], None, [32], [0, 256])
            
#             hist_b = cv2.normalize(hist_b, hist_b).flatten()
#             hist_g = cv2.normalize(hist_g, hist_g).flatten()
#             hist_r = cv2.normalize(hist_r, hist_r).flatten()
            
#             current_hist = np.concatenate([hist_b, hist_g, hist_r])
            
#             if prev_background_hist is not None:
#                 correlation = cv2.compareHist(prev_background_hist, current_hist, cv2.HISTCMP_CORREL)
#                 current_time = frame_idx / fps
                
#                 if correlation < threshold and (current_time - last_shot_time) > 2.0:
#                     shots.append(round(current_time, 2))
#                     last_shot_time = current_time
            
#             prev_background_hist = current_hist
#             prev_frame = frame_without_skater
#             frame_idx += 1
        
#         cap.release()
#         return shots
