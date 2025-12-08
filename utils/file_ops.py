import os
from pathlib import Path
from typing import Tuple

import pandas as pd


def validate_csv_file(csv_path: str) -> Tuple[bool, str]:
    """
    Валидация CSV файла

    Args:
        csv_path: путь к CSV файлу

    Returns:
        Tuple[bool, str]: (успешность, сообщение об ошибке)
    """
    if not os.path.exists(csv_path):
        return False, f"Файл не найден: {csv_path}"

    if not csv_path.lower().endswith(".csv"):
        return False, f"Файл должен иметь расширение .csv: {csv_path}"

    try:
        # Пробуем прочитать файл
        df = pd.read_csv(csv_path, nrows=1)  # Читаем только первую строку
        if len(df.columns) < 2:
            return False, "CSV файл должен содержать минимум 2 колонки"

        # Проверяем наличие необходимых колонок
        required_cols = ["absolute_path", "relative_path"]
        found_cols = [col for col in required_cols if col in df.columns]

        if len(found_cols) < len(required_cols):
            missing = set(required_cols) - set(found_cols)
            return False, f"Отсутствуют колонки: {missing}"

        return True, "CSV файл валиден"

    except pd.errors.EmptyDataError:
        return False, "CSV файл пуст"
    except pd.errors.ParserError as e:
        return False, f"Ошибка парсинга CSV: {e}"
    except Exception as e:
        return False, f"Ошибка при чтении CSV: {e}"


def setup_output_directory(base_dir: str = "lab4_results") -> str:
    """
    Создание директории для результатов

    Args:
        base_dir: имя базовой директории

    Returns:
        str: путь к созданной директории
    """
    # Создаем уникальное имя директории с timestamp
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(base_dir) / f"analysis_{timestamp}"

    # Создаем поддиректории
    (output_dir / "data").mkdir(parents=True, exist_ok=True)
    (output_dir / "plots").mkdir(parents=True, exist_ok=True)

    print(f"Директория для результатов создана: {output_dir}")
    return str(output_dir)


def print_dataframe_info(df: pd.DataFrame, title: str = "DataFrame") -> None:
    """
    Вывод информации о DataFrame

    Args:
        df: DataFrame для анализа
        title: заголовок для вывода
    """
    print("\n" + "=" * 60)
    print(f"ИНФОРМАЦИЯ О {title.upper()}")
    print("=" * 60)

    # Основная информация
    print(f"Размер: {df.shape[0]} строк, {df.shape[1]} колонок")
    print(f"Колонки: {list(df.columns)}")

    # Информация о типах данных
    print("\nТипы данных:")
    for col in df.columns:
        dtype = df[col].dtype
        non_null = df[col].count()
        total = len(df)
        null_percent = ((total - non_null) / total) * 100
        print(
            f"  {col}: {dtype} (не пустых: {non_null}/{total}, "
            f"пустых: {null_percent:.1f}%)"
        )

    # Статистика для числовых колонок
    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns

    if len(numeric_cols) > 0:
        print("\nСтатистика числовых колонок:")
        for col in numeric_cols:
            if df[col].notna().any():
                print(f"  {col}:")
                print(f"    Мин: {df[col].min():.2f}")
                print(f"    Макс: {df[col].max():.2f}")
                print(f"    Среднее: {df[col].mean():.2f}")
                print(f"    Медиана: {df[col].median():.2f}")

    print("=" * 60)
