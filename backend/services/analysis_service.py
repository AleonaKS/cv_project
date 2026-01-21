import cv2
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from backend.covers.analysis import analyze_cover
from backend.services.dataset_loader import load_books

def create_statistics_plots(stats_data, output_dir="backend/data/stats"):
    """Создает графики статистики и сохраняет их"""
    os.makedirs(output_dir, exist_ok=True)
    
    # График распределения типов дизайна
    design_counts = {
        'Минималистичные': stats_data['minimalistic'],
        'Сбалансированные': stats_data['total_books'] - stats_data['minimalistic'] - stats_data['overloaded'],
        'Перегруженные': stats_data['overloaded']
    }
    
    plt.figure(figsize=(10, 6))
    plt.subplot(2, 2, 1)
    plt.pie(design_counts.values(), labels=design_counts.keys(), autopct='%1.1f%%')
    plt.title('Распределение типов дизайна')
    
    # График наличия лиц
    plt.subplot(2, 2, 2)
    face_counts = [stats_data['faces'], stats_data['total_books'] - stats_data['faces']]
    plt.bar(['С лицами', 'Без лиц'], face_counts, color=['lightblue', 'lightcoral'])
    plt.title('Наличие лиц на обложках')
    
    # График цветового контраста
    plt.subplot(2, 2, 3)
    if stats_data['color_contrast']:
        plt.hist(stats_data['color_contrast'], bins=20, alpha=0.7, color='lightgreen')
        plt.axvline(np.mean(stats_data['color_contrast']), color='red', linestyle='--', label=f'Среднее: {np.mean(stats_data["color_contrast"]):.2f}')
        plt.legend()
        plt.title('Распределение цветового контраста')
    
    # График теплоты/холода
    plt.subplot(2, 2, 4)
    if stats_data['warm_cold_balance']:
        warm_cold = ['Теплые' if x > 0 else 'Холодные' for x in stats_data['warm_cold_balance']]
        warm_count = warm_cold.count('Теплые')
        cold_count = len(warm_cold) - warm_count
        
        plt.bar(['Теплые', 'Холодные'], [warm_count, cold_count], color=['orange', 'blue'])
        plt.title('Баланс теплых/холодных тонов')
    
    plt.tight_layout()
    plot_path = os.path.join(output_dir, 'stats_summary.png')
    plt.savefig(plot_path)
    plt.close()
    
    return plot_path

def dataset_stats(csv_path="backend/data/books_local.csv", limit=100):
    df = load_books(csv_path, limit=limit)
    
    results = {
        "total_books": len(df),
        "placeholders": 0,
        "minimalistic": 0,
        "overloaded": 0,
        "faces": 0,
        "color_contrast": [],
        "warm_cold_balance": [],
        "monochrome": [],
        "design_details": [],
        "individual_analyses": []
    }

    for _, row in df.iterrows():
        image_path = row.get("image_path")
        if not image_path or not os.path.exists(image_path):
            results["placeholders"] += 1
            continue

        img = cv2.imread(image_path)
        if img is None:
            results["placeholders"] += 1
            continue

        analysis = analyze_cover(img)
        results["individual_analyses"].append({
            "title": row.get("title", "Unknown"),
            "genre": row.get("genre", "Unknown"),
            "analysis": analysis
        })

        if analysis.get("type") == "placeholder":
            results["placeholders"] += 1
            continue

        # Собираем данные для статистики
        results["design_details"].append(analysis["design"])
        
        if analysis["design"] == "минималистичная":
            results["minimalistic"] += 1
        elif analysis["design"] == "перегруженная":
            results["overloaded"] += 1

        if analysis["face"]:
            results["faces"] += 1

        results["color_contrast"].append(analysis["color_contrast"])
        results["warm_cold_balance"].append(analysis["warm_cold_balance"])
        results["monochrome"].append(analysis["color_contrast"] < 20)

    # Вычисляем средние значения
    results["avg_color_contrast"] = float(np.mean(results["color_contrast"])) if results["color_contrast"] else 0
    results["avg_warm_cold_balance"] = float(np.mean(results["warm_cold_balance"])) if results["warm_cold_balance"] else 0
    results["monochrome_percentage"] = 100 * sum(results["monochrome"]) / len(results["monochrome"]) if results["monochrome"] else 0
    
    # Создаем графики
    plot_path = create_statistics_plots(results)
    results["plot_path"] = plot_path
    
    return results
