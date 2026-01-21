# ./backend/video/utils.py

import cv2 

def extract_frames_interval(video_path, start_sec, end_sec, max_frames=120):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 25

    cap.set(cv2.CAP_PROP_POS_MSEC, start_sec * 1000)

    frames = []
    while cap.get(cv2.CAP_PROP_POS_MSEC) < end_sec * 1000:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
        if len(frames) >= max_frames:
            break

    cap.release()
    return frames, fps
