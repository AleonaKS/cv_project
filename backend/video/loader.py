# backend/video/loader.py
import cv2 
from pytube import YouTube
import tempfile
import os 
import re


def load_video_source(source): 
    if isinstance(source, str) and os.path.exists(source):
        return source
    else:
        raise ValueError("Неподдерживаемый источник видео")

def extract_frames_simple(video_path, max_frames=60): 
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []
    
    frames = []
    for _ in range(max_frames):
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    
    cap.release()
    return frames

def extract_frames_interval(video_path, start_time, end_time, max_frames=120):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25

    cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)

    frames = []
    while cap.get(cv2.CAP_PROP_POS_MSEC) < end_time * 1000:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
        if len(frames) >= max_frames:
            break

    cap.release()
    return frames, fps
