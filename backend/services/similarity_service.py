import cv2

orb = cv2.ORB_create()

def orb_features(image):
    _, des = orb.detectAndCompute(image, None)
    return des

def compare_orb(des1, des2):
    if des1 is None or des2 is None:
        return 0
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    return len(bf.match(des1, des2))
