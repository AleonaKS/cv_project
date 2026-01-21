# # backend/video/jumps_improved.py
# import cv2
# import numpy as np
# from .skater_detector import SkaterDetector
 

# class ImprovedJumpDetector:
#     def __init__(self):
#         self.skater_detector = SkaterDetector()
        
#     def detect_jumps_by_height(self, frames, fps, height_threshold=0.15):
#         """Исправленная детекция прыжков по изменению высоты фигуриста"""
#         if len(frames) < 10:
#             return []
        
#         heights = self.skater_detector.track_skater_height(frames)
        
#         if len(heights) < 10:
#             return []
        
#         heights = np.array(heights, dtype=np.float32)
#         valid_heights = heights[heights > 0]
        
#         if len(valid_heights) == 0:
#             return []
        
#         base_height = np.median(valid_heights)
#         jumps = []
#         in_jump = False
#         jump_start = 0
#         min_height_ratio = 1.0  # Отслеживаем минимальную высоту (сжатие)
#         max_height_ratio = 1.0  # Отслеживаем максимальную высоту (прыжок)
        
#         for i in range(len(heights)):
#             if heights[i] > 0:
#                 height_ratio = heights[i] / base_height
                
#                 # Детекция подготовки к прыжку (сжатие)
#                 if not in_jump and height_ratio < 0.85:
#                     in_jump = True
#                     jump_start = i
#                     min_height_ratio = height_ratio
#                     max_height_ratio = height_ratio
                
#                 # Во время прыжка
#                 elif in_jump:
#                     min_height_ratio = min(min_height_ratio, height_ratio)
#                     max_height_ratio = max(max_height_ratio, height_ratio)
                    
#                     # Конец прыжка - возврат к нормальной высоте
#                     if height_ratio < 1.1 and i - jump_start > fps * 0.1:
#                         # Проверяем, был ли это реальный прыжок
#                         if max_height_ratio > 1.15:  # Фигурист действительно подпрыгнул
#                             jump_time = jump_start / fps
#                             jump_duration = (i - jump_start) / fps
                            
#                             intensity = max_height_ratio - 1.0  # Интенсивность пропорциональна высоте
                            
#                             jumps.append({
#                                 "time": round(jump_time, 3),
#                                 "duration": round(jump_duration, 3),
#                                 "intensity": round(intensity, 3),
#                                 "height_ratio": round(max_height_ratio, 3),
#                                 "compression_ratio": round(min_height_ratio, 3)
#                             })
                        
#                         in_jump = False
        
#         return jumps

    
#     def detect_jumps_combined(self, frames, fps):
#         """
#         Комбинированный подход: движение + высота
#         """
#         # 1. Детекция по оптическому потоку (старый метод)
#         from .jumps import detect_jumps as detect_by_motion
#         motion_jumps = detect_by_motion(frames, fps)
        
#         # 2. Детекция по высоте (новый метод)
#         height_jumps = self.detect_jumps_by_height(frames, fps)
        
#         # 3. Объединение результатов
#         all_jumps = []
#         jump_times = set()
        
#         # Добавляем прыжки по движению
#         for jump in motion_jumps:
#             all_jumps.append({
#                 **jump,
#                 "detection_method": "motion"
#             })
#             jump_times.add(round(jump["time"], 1))
        
#         # Добавляем прыжки по высоте, если они не дублируются
#         for jump in height_jumps:
#             if round(jump["time"], 1) not in jump_times:
#                 all_jumps.append({
#                     **jump,
#                     "detection_method": "height"
#                 })
        
#         # Сортируем по времени
#         all_jumps.sort(key=lambda x: x["time"])
        
#         return all_jumps
