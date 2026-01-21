# ./backend/video/jump_contrastive.py

import cv2
import numpy as np
from .utils import extract_frames_interval
from .skater_detector import SkaterDetector
import logging
import base64
from scipy.stats import entropy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JumpContrastiveAnalyzer:
    def __init__(self):
        self.skater_detector = SkaterDetector()

    def extract_scene_features(self, frames): 
        if len(frames) == 0:
            return {"brightness": [], "edges": [], "color_entropy": []}

        brightness = []
        edges = []
        color_entropy = []

        for frame in frames: 
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness.append(float(np.mean(gray)))
 
            sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            edge_mag = np.sqrt(sobel_x**2 + sobel_y**2)
            edges.append(float(np.mean(edge_mag)))
 
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            h_hist = cv2.calcHist([hsv], [0], None, [256], [0, 256])
            h_hist = h_hist / h_hist.sum() if h_hist.sum() > 0 else h_hist
            ent = entropy(h_hist.flatten() + 1e-10)   
            color_entropy.append(float(ent))

        return {
            "brightness": np.array(brightness),
            "edges": np.array(edges),
            "color_entropy": np.array(color_entropy)
        }

    def analyze(self, video_path, jump_intervals, context_window=3.0):
        """Версия с тремя кадрами: начало, середина, конец прыжка"""
        results = []

        for idx, (start, end) in enumerate(jump_intervals):
            try: 
                cap = cv2.VideoCapture(video_path)
                fps = cap.get(cv2.CAP_PROP_FPS) or 25
                cap.release()
 
                jump_frames, _ = extract_frames_interval(video_path, start, end)
                if len(jump_frames) < 3:
                    logger.warning(f"Прыжок {idx+1}: слишком мало кадров - пропускаем")
                    continue
 
                pre_start = max(0, start - context_window)
                pre_frames, _ = extract_frames_interval(video_path, pre_start, start)
 
                post_end = end + context_window
                post_frames, _ = extract_frames_interval(video_path, end, post_end)
 
                sample_frames = []
                if len(jump_frames) >= 3: 
                    indices = [0, len(jump_frames)//2, len(jump_frames)-1]
                    
                    for frame_idx in indices:
                        frame = jump_frames[frame_idx].copy()
                        _, bbox, _ = self.skater_detector.detect_skater(frame)
                        if bbox:
                            x1, y1, x2, y2 = bbox
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
                            cv2.putText(frame, f"Прыжок {idx+1}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
                        
                        _, buffer = cv2.imencode('.png', frame)
                        sample_frames.append(base64.b64encode(buffer).decode('utf-8'))
                elif len(jump_frames) > 0: 
                    for i in range(len(jump_frames)):
                        frame = jump_frames[i].copy()
                        _, bbox, _ = self.skater_detector.detect_skater(frame)
                        if bbox:
                            x1, y1, x2, y2 = bbox
                            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
                            cv2.putText(frame, f"Прыжок {idx+1}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
                        
                        _, buffer = cv2.imencode('.png', frame)
                        sample_frames.append(base64.b64encode(buffer).decode('utf-8'))
 
                jump_scene = self.extract_scene_features(jump_frames)
                pre_scene = self.extract_scene_features(pre_frames)
                post_scene = self.extract_scene_features(post_frames)

                jump_body = self.skater_detector.get_body_features(jump_frames, fps)
                pre_body = self.skater_detector.get_body_features(pre_frames, fps)
                post_body = self.skater_detector.get_body_features(post_frames, fps)

                comparison = {}

                def safe_mean(arr):
                    return float(np.mean(arr)) if len(arr) > 0 else 0.0

                def safe_get(data, key, default=0):
                    return data.get(key, default) if data else default
 
                scene_keys = ["brightness", "edges", "color_entropy"]
                scene_names = {
                    "brightness": "Яркость",
                    "edges": "Контраст",
                    "color_entropy": "Цветовая энтропия"
                }

                for key in scene_keys:
                    jump_val = safe_mean(jump_scene[key]) if key in jump_scene else 0
                    pre_val = safe_mean(pre_scene[key]) if key in pre_scene else 0
                    post_val = safe_mean(post_scene[key]) if key in post_scene else 0

                    diff = jump_val - pre_val
                    pct_change = (diff / pre_val * 100) if pre_val != 0 else (jump_val * 100)

                    comparison[key] = {
                        "name": scene_names.get(key, key),
                        "category": "Сцена",
                        "jump": round(jump_val, 4),
                        "pre": round(pre_val, 4),
                        "post": round(post_val, 4),
                        "difference": round(diff, 4),
                        "percent_change": round(pct_change, 2),
                        "jump_vs_pre": round(jump_val - pre_val, 4),
                        "jump_vs_post": round(jump_val - post_val, 4),
                        "jump_vs_pre_pct": round(pct_change, 2)
                    }
 
                body_keys = [
                    "height_max", "vertical_velocity_max", "vertical_acceleration_max",
                    "aspect_ratio_mean", "angle_mean", "hands_open_ratio", "legs_apart_ratio"
                ]
                body_names = {
                    "height_max": "Макс. высота",
                    "vertical_velocity_max": "Макс. скорость вверх",
                    "vertical_acceleration_max": "Макс. ускорение",
                    "aspect_ratio_mean": "Ширина/высота",
                    "angle_mean": "Наклон корпуса (°)",
                    "hands_open_ratio": "Руки открыты (%)",
                    "legs_apart_ratio": "Ноги разведены (%)"
                }

                for key in body_keys:
                    jump_val = safe_get(jump_body, key)
                    pre_val = safe_get(pre_body, key)
                    post_val = safe_get(post_body, key)

                    diff = jump_val - pre_val
                    pct_change = (diff / pre_val * 100) if pre_val != 0 else (jump_val * 100)

                    comparison[key] = {
                        "name": body_names.get(key, key),
                        "category": "Тело",
                        "jump": round(jump_val, 4),
                        "pre": round(pre_val, 4),
                        "post": round(post_val, 4),
                        "difference": round(diff, 4),
                        "percent_change": round(pct_change, 2),
                        "jump_vs_pre": round(jump_val - pre_val, 4),
                        "jump_vs_post": round(jump_val - post_val, 4),
                        "jump_vs_pre_pct": round(pct_change, 2)
                    }
 
                post_height_std = safe_get(post_body, "height_std", 0)
                post_height_mean = safe_get(post_body, "height_mean", 1)
                landing_stability = 1.0 - (post_height_std / post_height_mean) if post_height_mean > 0 else 0.0

                pre_height_std = safe_get(pre_body, "height_std", 0)
                pre_height_mean = safe_get(pre_body, "height_mean", 1)
                pre_stability = 1.0 - (pre_height_std / pre_height_mean) if pre_height_mean > 0 else 0.0

                jump_height_std = safe_get(jump_body, "height_std", 0)
                jump_height_mean = safe_get(jump_body, "height_mean", 1)
                jump_stability = 1.0 - (jump_height_std / jump_height_mean) if jump_height_mean > 0 else 0.0

                diff = jump_stability - pre_stability
                pct_change = (diff / pre_stability * 100) if pre_stability != 0 else (jump_stability * 100)

                comparison["landing_stability"] = {
                    "name": "Стабильность приземления",
                    "category": "Стабильность",
                    "jump": round(jump_stability, 4),
                    "pre": round(pre_stability, 4),
                    "post": round(landing_stability, 4),
                    "difference": round(diff, 4),
                    "percent_change": round(pct_change, 2),
                    "jump_vs_pre": round(jump_stability - pre_stability, 4),
                    "jump_vs_post": round(jump_stability - landing_stability, 4),
                    "jump_vs_pre_pct": round(pct_change, 2)
                }
 
                results.append({
                    "jump_index": idx + 1,
                    "time_interval": [round(start, 2), round(end, 2)],
                    "jump_duration": round(end - start, 2),
                    "comparison": comparison,
                    "sample_frames": sample_frames,
                    "frame_counts": {
                        "pre": len(pre_frames),
                        "jump": len(jump_frames),
                        "post": len(post_frames)
                    }
                })

            except Exception as e:
                logger.error(f"Ошибка при анализе прыжка {idx+1}: {str(e)}")
                results.append({
                    "jump_index": idx + 1,
                    "time_interval": [start, end],
                    "error": str(e)
                })

        return results
