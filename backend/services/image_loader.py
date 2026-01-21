import requests
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
import time
import random

def load_image_from_url(url: str, timeout=30, max_retries=2):
    """Загружает изображение с URL с обходом блокировок"""
    
    # Случайные User-Agent для обхода блокировок
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
    ]
    
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'image',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'cross-site'
    }
    
    for attempt in range(max_retries):
        try:
            print(f"[attempt {attempt+1}] Loading {url[:60]}...")
            
            # Добавляем случайную задержку между запросами
            time.sleep(random.uniform(1, 3))
            
            resp = requests.get(url, timeout=timeout, headers=headers, stream=True)
            resp.raise_for_status()
            
            # Проверяем что это действительно изображение
            content_type = resp.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                print(f"[image skipped] Not an image: {content_type}")
                return None
                
            if len(resp.content) == 0:
                print(f"[image skipped] Empty content")
                return None
                
            # Загружаем через PIL
            try:
                img = Image.open(BytesIO(resp.content)).convert("RGB")
                img_array = np.array(img)
                
                # Конвертируем в BGR для OpenCV
                image = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                
                # Ресайз если слишком большое
                h, w = image.shape[:2]
                if h > 800 or w > 800:
                    scale = min(800/h, 800/w)
                    new_w, new_h = int(w * scale), int(h * scale)
                    image = cv2.resize(image, (new_w, new_h))
                    
                print(f"✓ Image loaded: {image.shape}")
                return image
                
            except Exception as pil_error:
                print(f"[PIL error] {pil_error}")
                # Пробуем напрямую через OpenCV
                try:
                    img_array = np.frombuffer(resp.content, np.uint8)
                    image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                    if image is not None:
                        print(f"✓ Image loaded via OpenCV: {image.shape}")
                        return image
                except Exception as cv_error:
                    print(f"[OpenCV error] {cv_error}")
                    return None
                    
        except requests.exceptions.Timeout:
            print(f"[timeout] Attempt {attempt+1} failed")
            if attempt < max_retries - 1:
                wait_time = random.uniform(3, 7)
                print(f"Waiting {wait_time:.1f}s before retry...")
                time.sleep(wait_time)
                continue
                
        except requests.exceptions.RequestException as e:
            print(f"[request error] {type(e).__name__}: {e}")
            if attempt < max_retries - 1:
                time.sleep(random.uniform(2, 5))
                continue
                
        except Exception as e:
            print(f"[unexpected error] {type(e).__name__}: {e}")
            return None
    
    print(f"❌ Failed to load image after {max_retries} attempts")
    return None
 