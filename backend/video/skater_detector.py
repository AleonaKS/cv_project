# ./backend/video/skater_detector.py
import numpy as np
from ultralytics import YOLO
import torch 

class SkaterDetector:
    def __init__(self, model_path='yolov8n.pt'):
        self.model = YOLO(model_path)
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model.to(self.device)
        
    def detect_skater(self, frame):
        """Детектирует фигуриста и возвращает маску без него"""
        results = self.model(frame, verbose=False)[0]
        person_boxes = []
        
        for box in results.boxes:
            if int(box.cls) == 0:   
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                person_boxes.append((x1, y1, x2, y2))
        
        if not person_boxes:
            return frame, None, None
            
        # Берем самого крупного (предполагаем, что это фигурист)
        largest_box = max(person_boxes, key=lambda b: (b[2]-b[0])*(b[3]-b[1]))
        x1, y1, x2, y2 = largest_box
         
        padding = 15
        x1 = max(0, x1 - padding)
        y1 = max(0, y1 - padding)
        x2 = min(frame.shape[1], x2 + padding)
        y2 = min(frame.shape[0], y2 + padding)
        
        # Создаем маску без фигуриста
        mask = np.ones(frame.shape[:2], dtype=np.uint8) * 255
        mask[y1:y2, x1:x2] = 0
        frame_without_skater = frame.copy()
        frame_without_skater[mask == 0] = 0
        
        return frame_without_skater, (x1, y1, x2, y2), largest_box

    def track_skater_body(self, frames, fps=25):
        """
        Возвращает массив данных по телу фигуриста в каждом кадре
        Каждый элемент: {
            "bbox": [x1, y1, x2, y2],
            "center": (cx, cy),
            "height": h,
            "width": w,
            "aspect_ratio": w/h,
            "area": area,
            "velocity": (vx, vy),
            "acceleration": (ax, ay),
            "angle": angle_degrees,
            "hands_open": bool,
            "legs_apart": bool
        }
        """
        if len(frames) < 2:
            return []

        body_data = []
        prev_center = None
        prev_height = None
        prev_angle = None

        for i, frame in enumerate(frames):
            _, bbox, full_bbox = self.detect_skater(frame)
            if not bbox:
                body_data.append(None)
                continue

            x1, y1, x2, y2 = full_bbox
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            h = y2 - y1
            w = x2 - x1
            area = w * h
            aspect_ratio = w / h if h > 0 else 0

            # Угол наклона корпуса (по центру и верхней точке головы) 
            head_top = y1
            center_y = cy
            angle = 0
            if h > 0: 
                head_offset = (center_y - head_top) / h
                angle = (0.5 - head_offset) * 180  
 
            hands_open = aspect_ratio > 1.2
            legs_apart = h < 0.7 * np.sqrt(area)  

            # Скорость и ускорение
            velocity = (0, 0)
            acceleration = (0, 0)
            if prev_center:
                vx = cx - prev_center[0]
                vy = cy - prev_center[1]
                velocity = (vx, vy)
                if prev_height is not None:
                    ax = vx - (prev_center[0] - prev_center[0])   
                    ay = vy - (prev_center[1] - prev_center[1])
                    acceleration = (ax, ay)

            body_data.append({
                "bbox": [x1, y1, x2, y2],
                "center": (cx, cy),
                "height": h,
                "width": w,
                "aspect_ratio": aspect_ratio,
                "area": area,
                "velocity": velocity,
                "acceleration": acceleration,
                "angle": angle,
                "hands_open": hands_open,
                "legs_apart": legs_apart,
                "time": i / fps
            })

            prev_center = (cx, cy)
            prev_height = h
            prev_angle = angle

        return body_data

    def get_body_features(self, frames, fps=25):
        """Агрегирует признаки тела в статистику для сравнения"""
        body_data = self.track_skater_body(frames, fps)
        
        # Фильтруем только валидные кадры
        valid_data = [d for d in body_data if d is not None]
        if not valid_data:
            return {}

        heights = [d["height"] for d in valid_data]
        angles = [d["angle"] for d in valid_data]
        velocities = [d["velocity"][1] for d in valid_data]   
        accelerations = [d["acceleration"][1] for d in valid_data]  
        aspect_ratios = [d["aspect_ratio"] for d in valid_data]
        hands_open = [d["hands_open"] for d in valid_data]
        legs_apart = [d["legs_apart"] for d in valid_data]

        return {
            "height_mean": float(np.mean(heights)),
            "height_std": float(np.std(heights)),
            "height_max": float(np.max(heights)),
            "height_min": float(np.min(heights)),
            "angle_mean": float(np.mean(angles)),
            "angle_std": float(np.std(angles)),
            "vertical_velocity_mean": float(np.mean(velocities)),
            "vertical_velocity_max": float(np.max(velocities)),
            "vertical_acceleration_mean": float(np.mean(accelerations)),
            "vertical_acceleration_max": float(np.max(accelerations)),
            "aspect_ratio_mean": float(np.mean(aspect_ratios)),
            "hands_open_ratio": float(np.mean(hands_open)),
            "legs_apart_ratio": float(np.mean(legs_apart)),
            "frames_count": len(valid_data)
        }
