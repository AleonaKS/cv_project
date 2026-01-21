# backend/services/build_stats_cache.py
import sys
import os

# Добавляем корневую директорию проекта в путь Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from backend.services.stats_cache import get_cached_stats
    
    def main():
        print("🏗️ Построение первоначального кеша статистики...")
        try:
            csv_path = os.path.join("backend", "data", "books_local.csv")
            stats = get_cached_stats(csv_path, force_refresh=True)
            print(f"✅ Кеш построен! Обработано {stats['total_books']} книг")
            print(f"📊 Файл кеша: backend/data/stats_cache.json")
        except Exception as e:
            print(f"❌ Ошибка при построении кеша: {e}")
            import traceback
            traceback.print_exc()

    if __name__ == "__main__":
        main()
        
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Проверьте структуру проекта и пути импорта")
