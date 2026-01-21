import cv2
import numpy as np

def apply_filter(image, mode):
    img = image.copy()

    if mode == "grayscale":
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


    if mode == "warm":
        img[:,:,2] = np.clip(img[:,:,2] + 30, 0, 255)

    if mode == "cold":
        img[:,:,0] = np.clip(img[:,:,0] + 30, 0, 255)

    return img
