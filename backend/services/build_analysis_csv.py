# backend/services/build_analysis_csv.py
import os
import cv2
import pandas as pd
from backend.covers.analysis import analyze_cover
from backend.covers.placeholder_ocr import detect_placeholder_text

CSV_INPUT = "backend/data/books_local.csv"
CSV_OUTPUT = "backend/data/books_analysis.csv"

def main():
    if not os.path.exists(CSV_INPUT):
        print(f"❌ CSV файл не найден: {CSV_INPUT}")
        return

    df = pd.read_csv(CSV_INPUT)
    print(f"📊 Начинаем анализ {len(df)} изображений...")

    results = []

    for i, row in enumerate(df.itertuples(), start=1):
        image_path = getattr(row, "image_path", None)
        if not image_path or not os.path.exists(image_path):
            print(f"⚠️ Файл не найден: {image_path}")
            continue

        img = cv2.imread(image_path)
        if img is None:
            print(f"⚠️ Не удалось прочитать изображение: {image_path}")
            continue

        # Placeholder OCR
        placeholder_ocr = detect_placeholder_text(img)

        # Полный анализ
        analysis = analyze_cover(img)
        placeholder_text = False
        found_phrases = ""

        if analysis.get("type") == "placeholder":
            placeholder_text = analysis["placeholder"]["ocr"].get("is_placeholder_text", False)
            found_phrases = ",".join(
                analysis["placeholder"]["ocr"].get("found_phrases", [])
            )


        result_row = {
            "id": getattr(row, "id", None),
            "title": getattr(row, "title", None),
            "genre": getattr(row, "genre", None),
            "image_path": image_path,

            # Placeholder
            "placeholder_auto": analysis.get("type") == "placeholder",
            "placeholder_text": placeholder_ocr["is_placeholder_text"],
            "found_phrases": ",".join(placeholder_ocr["found_phrases"]),

            # Дизайн и композиция
            "design": analysis.get("design"),
            "face": analysis.get("face"),
            "face_position": analysis.get("face_position"),
            "text_density": analysis.get("text_density"),
            "edge_density": analysis.get("edge_density"),
            "negative_space": analysis.get("negative_space"),

            # Цвет
            "colors": str(analysis.get("colors")),
            "color_contrast": analysis.get("color_contrast"),
            "warm_cold_balance": analysis.get("warm_cold_balance"),
            "monochrome": analysis.get("color_contrast") < 20
        }

        results.append(result_row)
        print(f"[{i}/{len(df)}] {getattr(row, 'title', '')} - обработано")
        print(
                analysis.get("design"),
                analysis.get("face"),
                analysis.get("color_contrast"),
                analysis.get("warm_cold_balance")
            )

    df_out = pd.DataFrame(results)
    df_out.to_csv(CSV_OUTPUT, index=False)
    print(f"✅ Анализ завершен. CSV сохранен: {CSV_OUTPUT}")


if __name__ == "__main__":
    main()
