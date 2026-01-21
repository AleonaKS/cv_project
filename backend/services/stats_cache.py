# backend/services/stats_cache.py
import json
import os
import sys
import pandas as pd
from datetime import datetime

# Получаем абсолютный путь к корневой директории проекта
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CACHE_FILE = os.path.join(PROJECT_ROOT, "backend", "data", "stats_cache.json")
CACHE_DURATION = 360000000  # 1 час в секундах

def is_cache_valid():
    """Проверяет, актуален ли кеш"""
    if not os.path.exists(CACHE_FILE):
        return False
    
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # Проверяем время создания кеша
        cache_time = datetime.fromisoformat(cache_data['timestamp'])
        current_time = datetime.now()
        time_diff = (current_time - cache_time).total_seconds()
        
        return time_diff < CACHE_DURATION
    except Exception as e:
        print(f"Ошибка проверки кеша: {e}")
        return False

def load_cached_stats():
    """Загружает статистику из кеша"""
    if not os.path.exists(CACHE_FILE):
        return None
    
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)['stats']
    except Exception as e:
        print(f"Ошибка загрузки кеша: {e}")
        return None

def save_stats_to_cache(stats_data):
    """Сохраняет статистику в кеш"""
    cache_data = {
        'timestamp': datetime.now().isoformat(),
        'stats': stats_data
    }
    
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)

def get_cached_stats(csv_path=None, force_refresh=False):
    """
    Основная функция: возвращает статистику из кеша или вычисляет заново
    """
    # Используем абсолютный путь к CSV файлу
    if csv_path is None:
        csv_path = os.path.join(PROJECT_ROOT, "backend", "data", "books_local.csv")
    else:
        csv_path = os.path.join(PROJECT_ROOT, csv_path)
    
    # Если принудительное обновление или кеш невалиден - пересчитываем
    if force_refresh or not is_cache_valid():
        print("Вычисление новой статистики...")
        
        # Импортируем здесь, чтобы избежать циклических импортов
        from backend.services.analysis_service import dataset_stats
        
        fresh_stats = dataset_stats(csv_path, limit=None)
        
        # Сохраняем в кеш
        save_stats_to_cache(fresh_stats)
        return fresh_stats
    else:
        print("📊 Загрузка статистики из кеша...")
        cached_stats = load_cached_stats()
        if cached_stats:
            return cached_stats
        else:
            # Если кеш поврежден, вычисляем заново
            from backend.services.analysis_service import dataset_stats
            fresh_stats = dataset_stats(csv_path, limit=None)
            save_stats_to_cache(fresh_stats)
            return fresh_stats
