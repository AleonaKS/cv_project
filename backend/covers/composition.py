# backend/covers/composition.py

def face_position(image, faces):
    # ✅ правильная проверка
    if faces is None or len(faces) == 0:
        return "no_face"

    h, w = image.shape[:2]

    x, y, fw, fh = faces[0]
    cx = x + fw / 2
    cy = y + fh / 2

    horizontal = "center"
    vertical = "center"

    if cx < w / 3:
        horizontal = "left"
    elif cx > 2 * w / 3:
        horizontal = "right"

    if cy < h / 3:
        vertical = "top"
    elif cy > 2 * h / 3:
        vertical = "bottom"

    return f"{vertical}-{horizontal}"
