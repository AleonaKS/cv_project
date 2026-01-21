import pandas as pd

def load_books(csv_path, limit=100):
    """Загружает данные о книгах из CSV файла"""
    try:
        df = pd.read_csv(csv_path)
        
        # Если указан лимит, берем только первые N записей
        if limit is not None and len(df) > limit:
            df = df.head(limit)
            
        return df
    except Exception as e:
        print(f"Ошибка загрузки CSV {csv_path}: {e}")
        return pd.DataFrame()  # Возвращаем пустой DataFrame при ошибке
