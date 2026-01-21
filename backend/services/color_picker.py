import cv2
import numpy as np

class ColorPicker:
    def __init__(self):
        self.selected_color = None
        self.target_color = None
        
    def pick_color_from_image(self, image, x, y):
        """Выбирает цвет из изображения по координатам"""
        if x < 0 or y < 0 or x >= image.shape[1] or y >= image.shape[0]:
            return None
            
        self.selected_color = image[y, x].tolist()
        return self.selected_color
    
    def set_target_color(self, r, g, b):
        """Устанавливает целевой цвет для замены"""
        self.target_color = [b, g, r]  # OpenCV использует BGR
        
    def replace_color(self, image, threshold=30):
        """Заменяет выбранный цвет на целевой"""
        if self.selected_color is None or self.target_color is None:
            return image
            
        img = image.copy()
        src_color = np.array(self.selected_color)
        dst_color = np.array(self.target_color)
        
        # Создаем маску для цветов в пределах порога
        mask = np.all(np.abs(img - src_color) <= threshold, axis=-1)
        img[mask] = dst_color
        
        return img
    
    def get_color_info(self, color):
        """Возвращает информацию о цвете"""
        if color is None:
            return None
            
        b, g, r = color
        return {
            "rgb": (r, g, b),
            "hex": f"#{r:02x}{g:02x}{b:02x}",
            "hsv": cv2.cvtColor(np.uint8([[color]]), cv2.COLOR_BGR2HSV)[0][0].tolist()
        }
