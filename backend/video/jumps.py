# backend/video/jumps.py 
import cv2
import numpy as np

def detect_jumps(frames, fps, motion_threshold=1.2, min_jump_duration=0.3): 
    if len(frames) < 10:  
        return []

    jumps = []
    jump_candidates = []
     
    processed_frames = []
    for frame in frames: 
        small_frame = cv2.resize(frame, (480, 270))  
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY) 
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        processed_frames.append(gray)
 
    for i in range(1, len(processed_frames)):
        prev_gray = processed_frames[i-1]
        curr_gray = processed_frames[i]
        
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, curr_gray,
            None, 
            pyr_scale=0.5, 
            levels=3, 
            winsize=15, 
            iterations=3, 
            poly_n=5, 
            poly_sigma=1.2, 
            flags=0
        )
         
        mean_horizontal = np.mean(flow[..., 0])
        mean_vertical = np.mean(flow[..., 1])
         
        is_upward_motion = mean_vertical < -motion_threshold
        is_significant_motion = abs(mean_vertical) > motion_threshold * 0.7
        
        if is_upward_motion and is_significant_motion:
            jump_time = float(i / fps)
            intensity = float(abs(mean_vertical))
 
            if not jump_candidates or (jump_time - jump_candidates[-1]["time"]) > 0.1:
                jump_candidates.append({
                    "time": jump_time,
                    "intensity": intensity,
                    "frame_index": i
                })
     
    if jump_candidates:
        current_jump = jump_candidates[0]
        for candidate in jump_candidates[1:]:
            if candidate["time"] - current_jump["time"] < min_jump_duration:
                current_jump["intensity"] = max(current_jump["intensity"], candidate["intensity"])
                current_jump["end_time"] = candidate["time"]
            else: 
                if "end_time" not in current_jump:
                    current_jump["end_time"] = current_jump["time"] + 0.1
                jumps.append(current_jump.copy())
                current_jump = candidate
         
        if "end_time" not in current_jump:
            current_jump["end_time"] = current_jump["time"] + 0.1
        jumps.append(current_jump)
    
    return jumps
