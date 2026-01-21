# ./backend/services/visualization.py

import pandas as pd
from backend.covers.analysis import analyze_cover
from backend.services.image_loader import load_image_from_url

def find_extremes(df):
    """
    Находит самую минималистичную и самую перегруженную обложку.
    """
    results = []

    for _, row in df.iterrows():
        try:
            img = load_image_from_url(row["image_link"])
            analysis = analyze_cover(img)
            if "complexity" in analysis:
                results.append({
                    "title": row["title"],
                    "image_link": row["image_link"],
                    "genre": row["genre"],
                    "complexity": analysis["complexity"],
                    "design": analysis["design"],
                    "face": analysis["face"],
                    "face_position": analysis["face_position"],
                    "negative_space": analysis["negative_space"],
                    "text_density": analysis["text_density"],
                    "edge_density": analysis["edge_density"],
                    "color_contrast": analysis["color_contrast"],
                    "warm_cold_balance": analysis["warm_cold_balance"]
                })
        except Exception as e:
            # Логируем ошибки, но не прерываем обработку
            print(f"Ошибка при обработке {row['title']}: {e}")
            continue

    if not results:
        return None, None

    min_cover = min(results, key=lambda x: x["complexity"])
    max_cover = max(results, key=lambda x: x["complexity"])

    return min_cover, max_cover, results  # Возвращаем все результаты для статистики


def compute_genre_stats(df):
    """
    Считает статистику по жанрам:
    - Доля книг с лицами
    - Доля минималистичных/перегруженных обложек
    - Средняя сложность
    """
    genre_stats = {}

    for _, row in df.iterrows():
        try:
            img = load_image_from_url(row["image_link"])
            analysis = analyze_cover(img)

            genre = row["genre"]
            if genre not in genre_stats:
                genre_stats[genre] = {
                    "total": 0,
                    "faces": 0,
                    "minimalistic": 0,
                    "overloaded": 0,
                    "complexity_sum": 0.0
                }

            genre_stats[genre]["total"] += 1
            genre_stats[genre]["faces"] += int(analysis["face"])
            if analysis["design"] == "минималистичная":
                genre_stats[genre]["minimalistic"] += 1
            elif analysis["design"] == "перегруженная":
                genre_stats[genre]["overloaded"] += 1
            genre_stats[genre]["complexity_sum"] += analysis["complexity"]

        except Exception as e:
            print(f"Ошибка при обработке {row['title']}: {e}")
            continue

    # Формируем финальный результат
    result = {}
    for genre, stats in genre_stats.items():
        total = stats["total"]
        result[genre] = {
            "total_books": total,
            "books_with_faces": stats["faces"],
            "face_percentage": round(stats["faces"] / total * 100, 1),
            "minimalistic_books": stats["minimalistic"],
            "overloaded_books": stats["overloaded"],
            "minimalistic_percentage": round(stats["minimalistic"] / total * 100, 1),
            "overloaded_percentage": round(stats["overloaded"] / total * 100, 1),
            "avg_complexity": round(stats["complexity_sum"] / total, 3)
        }

    return result
