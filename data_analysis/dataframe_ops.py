from typing import Optional, Tuple, Union
import os

import pandas as pd
from pathlib import Path

from .image_analysis import calculate_brightness_range


def create_dataframe_from_csv(csv_path: str) -> pd.DataFrame:
    """
    Создание DataFrame из CSV файла аннотации

    Args:
        csv_path: путь к CSV файлу аннотации

    Returns:
        pd.DataFrame: DataFrame с колонками абсолютного и относительного пути

    Raises:
        FileNotFoundError: если CSV файл не найден
        ValueError: если CSV файл имеет неверный формат
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV файл не найден: {csv_path}")

    try:
        # Чтение CSV файла
        df = pd.read_csv(csv_path)

        # Проверка наличия необходимых колонок
        required_columns = ["absolute_path", "relative_path"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"В CSV файле отсутствует колонка: '{col}'")

        # Оставляем только нужные колонки
        result_df = df[["absolute_path", "relative_path"]].copy()

        # Добавляем дополнительные колонки если они есть в исходном CSV
        if "keyword" in df.columns:
            result_df["keyword"] = df["keyword"]

        print(f"DataFrame создан. Загружено записей: {len(result_df)}")
        print(f"Колонки: {list(result_df.columns)}")

        return result_df

    except pd.errors.EmptyDataError:
        raise ValueError("CSV файл пуст")
    except pd.errors.ParserError as e:
        raise ValueError(f"Ошибка парсинга CSV файла: {e}")


def add_brightness_range_columns(
    df: pd.DataFrame, base_dir: Optional[str] = None
) -> pd.DataFrame:
    """
    Добавление колонок с диапазоном яркости по каналам RGB

    Args:
        df: исходный DataFrame
        base_dir: базовая директория для относительных путей

    Returns:
        pd.DataFrame: DataFrame с добавленными колонками
    """

    # Копируем DataFrame чтобы не изменять оригинал
    result_df = df.copy()

    # Создаем пустые колонки для результатов
    result_df["brightness_range_r"] = None
    result_df["brightness_range_g"] = None
    result_df["brightness_range_b"] = None
    result_df["total_brightness_range"] = None

    processed_count = 0
    error_count = 0

    for idx, row in result_df.iterrows():
        try:
            # Определяем путь к файлу
            if pd.isna(row["absolute_path"]) or not os.path.exists(
                row["absolute_path"]
            ):
                if base_dir and not pd.isna(row["relative_path"]):
                    file_path = os.path.join(base_dir, row["relative_path"])
                else:
                    print(f"Предупреждение: не найден путь для записи {idx}")
                    error_count += 1
                    continue
            else:
                file_path = row["absolute_path"]

            # Вычисляем диапазон яркости
            ranges = calculate_brightness_range(file_path)

            if ranges:
                result_df.at[idx, "brightness_range_r"] = ranges["r"]
                result_df.at[idx, "brightness_range_g"] = ranges["g"]
                result_df.at[idx, "brightness_range_b"] = ranges["b"]
                result_df.at[idx, "total_brightness_range"] = ranges["total"]
                processed_count += 1
            else:
                error_count += 1

        except Exception as e:
            print(f"Ошибка обработки файла {idx}: {e}")
            error_count += 1

    print(f"Обработано изображений: {processed_count}")
    print(f"Ошибок обработки: {error_count}")

    return result_df


def sort_by_column(
    df: pd.DataFrame, column: str, ascending: bool = True
) -> pd.DataFrame:
    """
    Сортировка DataFrame по указанной колонке

    Args:
        df: исходный DataFrame
        column: колонка для сортировки
        ascending: направление сортировки (True - по возрастанию)

    Returns:
        pd.DataFrame: отсортированный DataFrame
    """
    if column not in df.columns:
        raise ValueError(f"Колонка '{column}' не существует в DataFrame")

    # Удаляем строки с NaN значениями в колонке для сортировки
    sorted_df = df.dropna(subset=[column]).copy()

    # Сортируем
    sorted_df = sorted_df.sort_values(by=column, ascending=ascending)

    # Добавляем колонку с порядковым номером после сортировки
    sorted_df = sorted_df.reset_index(drop=True)
    sorted_df["sorted_index"] = sorted_df.index

    print(f"Отсортировано по колонке '{column}' (ascending={ascending})")
    print(f"Записей после удаления NaN: {len(sorted_df)} из {len(df)}")

    return sorted_df


def filter_by_column(
    df: pd.DataFrame,
    column: str,
    condition: Union[str, Tuple[float, float], float],
    operator: str = ">",
) -> pd.DataFrame:
    """
    Фильтрация DataFrame по колонке

    Args:
        df: исходный DataFrame
        column: колонка для фильтрации
        condition: условие фильтрации
        operator: оператор сравнения ('>', '<', '==', '>=', '<=', 'between')

    Returns:
        pd.DataFrame: отфильтрованный DataFrame
    """
    if column not in df.columns:
        raise ValueError(f"Колонка '{column}' не существует в DataFrame")

    # Удаляем строки с NaN значениями
    filtered_df = df.dropna(subset=[column]).copy()

    # Применяем фильтрацию в зависимости от оператора
    if operator == ">":
        filtered_df = filtered_df[filtered_df[column] > condition]
    elif operator == "<":
        filtered_df = filtered_df[filtered_df[column] < condition]
    elif operator == "==":
        filtered_df = filtered_df[filtered_df[column] == condition]
    elif operator == ">=":
        filtered_df = filtered_df[filtered_df[column] >= condition]
    elif operator == "<=":
        filtered_df = filtered_df[filtered_df[column] <= condition]
    elif operator == "between":
        if isinstance(condition, tuple) and len(condition) == 2:
            min_val, max_val = condition
            filtered_df = filtered_df[
                (filtered_df[column] >= min_val) & (filtered_df[column] <= max_val)
            ]
        else:
            raise ValueError(
                "Для оператора 'between' condition должен быть кортежем (min, max)"
            )
    elif operator == "range":
        # Фильтрация по диапазону значений
        filtered_df = filtered_df[filtered_df[column].between(*condition)]
    else:
        raise ValueError(f"Неподдерживаемый оператор: {operator}")

    print(f"Отфильтровано по колонке '{column}' {operator} {condition}")
    print(f"Записей после фильтрации: {len(filtered_df)} из {len(df)}")

    return filtered_df


def save_dataframe(df: pd.DataFrame, output_path: str, format: str = "csv") -> None:
    """
    Сохранение DataFrame в файл

    Args:
        df: DataFrame для сохранения
        output_path: путь для сохранения
        format: формат файла ('csv', 'excel', 'json')
    """
    # Создаем директорию если ее нет
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    if format.lower() == "csv":
        df.to_csv(output_path, index=False, encoding="utf-8")
        print(f"DataFrame сохранен в CSV: {output_path}")

    elif format.lower() == "excel":
        df.to_excel(output_path, index=False)
        print(f"DataFrame сохранен в Excel: {output_path}")

    elif format.lower() == "json":
        df.to_json(output_path, orient="records", indent=2)
        print(f"DataFrame сохранен в JSON: {output_path}")

    else:
        raise ValueError(f"Неподдерживаемый формат: {format}")
