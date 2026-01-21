# backend/app.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image
import os 
import logging
import json
import time
import requests

from backend.covers.analysis import analyze_cover
from backend.covers.face import detect_faces
from backend.covers.filters import apply_filter
from backend.services.color_picker import ColorPicker
from backend.services.dataset_loader import load_books
from backend.services.stats_cache import get_cached_stats
from backend.services.similarity_service import orb_features, compare_orb

app = FastAPI()
 
logging.basicConfig(level=logging.INFO)
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

color_picker = ColorPicker()
 
def read_image_from_bytes(data):
    img = Image.open(BytesIO(data)).convert("RGB") 
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)  

def img_to_base64(img):
    _, buf = cv2.imencode(".png", img)
    return base64.b64encode(buf).decode("utf-8")

def load_image_from_local(path):
    if not os.path.exists(path):
        return None
    return cv2.imread(path)  

def load_image_from_url(url: str):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return read_image_from_bytes(r.content)
    except Exception as e:
        logging.error(f"Ошибка загрузки изображения по URL: {e}")
        return None


@app.get("/")
async def read_root():
    with open("frontend/index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

# @app.get("/")
# async def serve_frontend():
#     frontend_path = "frontend/index.html"
#     if os.path.exists(frontend_path):
#         return FileResponse(frontend_path)
#     else:
#         return JSONResponse(
#             {"error": "Frontend not found. Check file path."},
#             status_code=404
#         )


# ---- API маршруты для анализа обложек ----

@app.post("/api/analyze")
async def analyze(
    file: UploadFile = File(None),
    image_url: str = Form(None),
    image_path: str = Form(None)
):
    if file:
        data = await file.read()
        img = read_image_from_bytes(data)
    elif image_url:
        img = load_image_from_url(image_url)
        if img is None:
            return JSONResponse({"error": "Не удалось загрузить изображение по ссылке"}, status_code=400)
    elif image_path:
        img = load_image_from_local(image_path)
        if img is None:
            return JSONResponse({"error": f"Файл не найден: {image_path}"}, status_code=400)
    else:
        return JSONResponse({"error": "Нет изображения"}, status_code=400)
    analysis = analyze_cover(img)
    faces = detect_faces(img)
    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x+w, y+h), (0,255,0), 2)
    analysis["image_base64"] = img_to_base64(img)
    return analysis


@app.post("/api/filter")
async def filter_image(
    file: UploadFile = File(None),
    image_url: str = Form(None),
    mode: str = Form(...)
):
    if file:
        data = await file.read()
        img = read_image_from_bytes(data)
    elif image_url:
        img = load_image_from_url(image_url)
        if img is None:
            raise HTTPException(400, "Не удалось загрузить изображение по URL")
    else:
        raise HTTPException(400, "Нет изображения")

    filtered = apply_filter(img, mode)
    return {"image_base64": img_to_base64(filtered)}




# ---- API маршруты для работы с цветом ----

@app.post("/api/pick_color")
async def pick_color(file: UploadFile = File(...), x: int = Form(...), y: int = Form(...)):
    """Возвращает цвет пикселя и информацию о нем"""
    data = await file.read()
    img = read_image_from_bytes(data)
    if x >= img.shape[1] or y >= img.shape[0]:
        return {"error": "Координаты вне изображения"}
    b, g, r = img[y, x].tolist()
    return {
        "rgb": [r, g, b],
        "hex": f"#{r:02x}{g:02x}{b:02x}",
        "position": {"x": x, "y": y}
    }

@app.post("/api/replace_color_advanced")
async def replace_color_advanced(
    file: UploadFile = File(...),
    target_hex: str = Form(...),
    new_hex: str = Form(...),
    tolerance: int = Form(30)
):
    """Замена цвета с выбором из палитры для обоих цветов"""
    data = await file.read()
    img = read_image_from_bytes(data)
    
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    target_rgb = hex_to_rgb(target_hex)
    new_rgb = hex_to_rgb(new_hex)
    
    target_bgr = (target_rgb[2], target_rgb[1], target_rgb[0])
    new_bgr = (new_rgb[2], new_rgb[1], new_rgb[0])
    
    diff = np.abs(img.astype(int) - np.array(target_bgr))
    mask = np.all(diff <= tolerance, axis=-1)
    
    result_img = img.copy()
    result_img[mask] = new_bgr
    
    return {"image_base64": img_to_base64(result_img)}

@app.post("/api/get_color")
async def get_color(file: UploadFile = File(...), x: int = Form(...), y: int = Form(...)):
    data = await file.read()
    img = read_image_from_bytes(data)
    if x >= img.shape[1] or y >= img.shape[0]:
        return {"error": "Координаты вне изображения"}
    color = tuple(int(c) for c in img[y, x])
    return {"color": color}

@app.post("/api/replace_color")
async def replace_color(file: UploadFile = File(...), x: int = Form(...), y: int = Form(...), new_color: str = Form(...)):
    data = await file.read()
    img = read_image_from_bytes(data)
    target = tuple(map(int, new_color.split(",")))
    src_color = tuple(int(c) for c in img[y, x])
    mask = np.all(np.abs(img - src_color) <= 30, axis=-1)
    img[mask] = target
    return {"image_base64": img_to_base64(img)}


# ---- API маршруты для поиска похожих обложек ----

@app.post("/api/similarity")
async def similarity(
    file: UploadFile = File(None),
    image_url: str = Form(None),
    top_n: int = Form(5)
):
    if file:
        data = await file.read()
        query_img = read_image_from_bytes(data)
    elif image_url:
        query_img = load_image_from_url(image_url)
        if query_img is None:
            return JSONResponse({"error": "Не удалось загрузить изображение"}, status_code=400)
    else:
        return JSONResponse({"error": "Нет изображения"}, status_code=400) 
    query_des = orb_features(query_img)
    df = load_books("backend/data/books_local.csv", limit=None)
    results = []
    for _, row in df.iterrows():
        img_path = row.get("image_path")
        if not img_path or not os.path.exists(img_path):
            continue
        img = load_image_from_local(img_path)
        des = orb_features(img)
        score = compare_orb(query_des, des)
        results.append({
            "title": row.get("title", "Unknown"),
            "score": score,
            "image_base64": img_to_base64(img)
        })

    results = sorted(results, key=lambda x: x["score"], reverse=True)[:top_n]
    return results


# ---- API маршруты для статистики ----

@app.get("/api/genre-stats")
async def genre_stats(force_refresh: bool = False):
    """Возвращает статистику из кеша или вычисляет заново"""
    try:
        stats = get_cached_stats("backend/data/books_local.csv", force_refresh=force_refresh)
        
        plot_path = stats.get("plot_path", "")
        if plot_path and os.path.exists(plot_path):
            try:
                with open(plot_path, "rb") as img_file:
                    stats["plot_base64"] = base64.b64encode(img_file.read()).decode('utf-8')
            except Exception as e:
                logging.error(f"Ошибка загрузки графика: {e}")
                stats["plot_base64"] = None
        else:
            stats["plot_base64"] = None
        
        stats["source"] = "cache" if not force_refresh else "fresh"
        stats["cache_info"] = "" if not force_refresh else "Пересчитанная статистика"
        
        return stats
        
    except Exception as e:
        return JSONResponse(
            {"error": f"Ошибка получения статистики: {str(e)}"}, 
            status_code=500
        )

@app.post("/api/refresh-stats")
async def refresh_stats():
    """Обновление статистики"""
    try:
        stats = get_cached_stats("backend/data/books_local.csv", force_refresh=True)
        return {"message": "Статистика обновлена", "stats": stats}
    except Exception as e:
        return JSONResponse(
            {"error": f"Ошибка обновления статистики: {str(e)}"}, 
            status_code=500
        )


# ---- API маршруты для анализа видео фигурного катания ----
from backend.video.utils import extract_frames_interval

@app.post("/api/analyze-skating")
async def analyze_skating_video(
    file: UploadFile = File(None),
    youtube_url: str = Form(None),
    jump_intervals: str = Form(None)
): 
    try:
        video_path = None
        parsed_intervals = None

        # 1. получение интервалов
        if not jump_intervals:
            return JSONResponse(
                {"success": False, "error": "Не указаны интервалы прыжков. Пример: [[75,78],[94,96]]"},
                status_code=400
            )

        try:
            parsed_intervals = json.loads(jump_intervals)
            if not isinstance(parsed_intervals, list) or len(parsed_intervals) == 0:
                raise ValueError("Интервалы должны быть непустым списком [[start,end], ...]")
            for interval in parsed_intervals:
                if not isinstance(interval, list) or len(interval) != 2:
                    raise ValueError("Каждый интервал должен быть списком [start, end]")
                if interval[0] >= interval[1]:
                    raise ValueError("Начало интервала должно быть меньше конца")
        except json.JSONDecodeError:
            return JSONResponse(
                {"success": False, "error": "Неверный формат JSON для jump_intervals"},
                status_code=400
            )

        # 2. загрузка видео
        if youtube_url:
            from backend.video.loader import download_youtube_video
            video_path = download_youtube_video(youtube_url)
        elif file and file.filename:
            upload_dir = "uploads"
            os.makedirs(upload_dir, exist_ok=True)
            timestamp = int(time.time())
            safe_filename = f"{timestamp}_{file.filename}"
            video_path = os.path.join(upload_dir, safe_filename)
            with open(video_path, "wb") as buffer:
                buffer.write(await file.read())
        else:
            return JSONResponse(
                {"success": False, "error": "Необходимо загрузить файл или указать YouTube ссылку"},
                status_code=400
            )

        # 3. инициализация 
        from backend.video.analyze_skating_improved import SkatingAnalyzer
        analyzer = SkatingAnalyzer()   
        result = analyzer.analyze_skating(video_path, jump_intervals=parsed_intervals)
 
        result["analysis_method"] = "manual_only"
        result["shots_analysis"] = []
        result["all_jumps"] = []
        result["shots_timeline"] = []
        result["total_jumps"] = 0
        result["shots_detected"] = 0

        # 4. очистка временного файла
        if video_path and os.path.exists(video_path):
            try:
                os.unlink(video_path)
            except:
                pass
        return result

    except Exception as e:
        logging.error(f"Ошибка анализа видео фигурного катания: {str(e)}")
        return JSONResponse(
            {"success": False, "error": f"Ошибка анализа: {str(e)}"},
            status_code=500
        )


# ---- Статические файлы фронтенда ----
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
 