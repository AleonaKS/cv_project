# ./backend/video/analyze_skating_improved.py
import cv2
import logging
from .jump_contrastive import JumpContrastiveAnalyzer 

cv2.setNumThreads(0)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SkatingAnalyzer:
    def __init__(self):
        self.contrastive = JumpContrastiveAnalyzer()

    def analyze_skating(self, video_path, jump_intervals=None): 
        try:
            if not jump_intervals or len(jump_intervals) == 0:
                raise ValueError("Не указаны интервалы прыжков. Пример: [[75, 78], [94, 96]]")
 
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError("Не удалось открыть видео")

            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            cap.release()
 
            contrastive_results = self.contrastive.analyze(video_path, jump_intervals, context_window=3.0)

            return {
                "success": True,
                "video_info": {
                    "fps": round(fps, 2),
                    "duration": round(duration, 2),
                    "total_frames": frame_count
                },
                "manual_jump_intervals": jump_intervals,
                "jump_analysis": contrastive_results,   
                "analysis_method": "contextual_body_only"
            }

        except Exception as e:
            logger.error(f"Ошибка в analyze_skating: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "analysis_method": "contextual_body_only"
            }
