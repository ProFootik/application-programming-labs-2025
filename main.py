import argparse
import os
import sys

import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd

from utils.file_ops import (
    validate_csv_file,
    setup_output_directory,
    print_dataframe_info,
)
from data_analysis.dataframe_ops import (
    create_dataframe_from_csv,
    add_brightness_range_columns,
    sort_by_column,
    filter_by_column,
    save_dataframe,
)
from visualization.plotting import (
    plot_brightness_ranges,
    plot_brightness_histogram,
    plot_combined_ranges,
)

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def parse_arguments() -> argparse.Namespace:
    """
    Парсинг аргументов командной строки
    """
    parser = argparse.ArgumentParser(
        description="Анализ диапазонов яркости изображений из аннотации CSV"
    )

    parser.add_argument(
        "--annotation",
        "-a",
        type=str,
        required=True,
        help="Путь к CSV файлу аннотации (из лабораторной работы 2)",
    )

    parser.add_argument(
        "--base-dir",
        "-b",
        type=str,
        default=None,
        help="Базовая директория для относительных путей (если не указана, используются абсолютные пути)",
    )

    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default="lab4_results",
        help="Директория для сохранения результатов",
    )

    parser.add_argument(
        "--sort-by",
        type=str,
        default="total_brightness_range",
        choices=[
            "brightness_range_r",
            "brightness_range_g",
            "brightness_range_b",
            "total_brightness_range",
        ],
        help="Колонка для сортировки",
    )

    parser.add_argument(
        "--sort-order",
        type=str,
        default="ascending",
        choices=["ascending", "descending"],
        help="Порядок сортировки",
    )

    parser.add_argument(
        "--filter-column",
        type=str,
        default=None,
        choices=[
            "brightness_range_r",
            "brightness_range_g",
            "brightness_range_b",
            "total_brightness_range",
        ],
        help="Колонка для фильтрации",
    )

    parser.add_argument(
        "--filter-operator",
        type=str,
        default=">",
        choices=[">", "<", ">=", "<=", "==", "between"],
        help="Оператор фильтрации",
    )

    parser.add_argument(
        "--filter-value",
        type=float,
        default=50.0,
        help="Значение для фильтрации (или минимальное значение для between)",
    )

    parser.add_argument(
        "--filter-value2",
        type=float,
        default=200.0,
        help="Максимальное значение для оператора between",
    )

    parser.add_argument(
        "--plot-type",
        type=str,
        default="ranges",
        choices=["ranges", "histogram", "combined", "all"],
        help="Тип графика для построения",
    )

    parser.add_argument(
        "--skip-image-analysis",
        action="store_true",
        help="Пропустить анализ изображений (использовать существующие данные)",
    )

    parser.add_argument(
        "--load-existing",
        type=str,
        default=None,
        help="Загрузить существующий DataFrame из файла",
    )

    return parser.parse_args()


def main() -> None:
    """
    Основная функция программы
    """
    print("=" * 70)
    print("ЛАБОРАТОРНАЯ РАБОТА №4: АНАЛИЗ И ВИЗУАЛИЗАЦИЯ ДАННЫХ")
    print("Анализ диапазонов яркости изображений")
    print("=" * 70)

    # 1. Парсинг аргументов
    args = parse_arguments()

    # 2. Валидация входного файла
    if not args.skip_image_analysis and args.load_existing is None:
        print(f"\n[1/8] Валидация входного файла: {args.annotation}")
        is_valid, message = validate_csv_file(args.annotation)

        if not is_valid:
            print(f"✗ ОШИБКА: {message}")
            sys.exit(1)

        print(f"✓ {message}")

    # 3. Настройка директории для результатов
    print("\n[2/8] Настройка директории для результатов")
    results_dir = setup_output_directory(args.output_dir)
    data_dir = Path(results_dir) / "data"
    plots_dir = Path(results_dir) / "plots"

    # 4. Загрузка или создание DataFrame
    print("\n[3/8] Работа с данными")

    if args.load_existing:
        # Загрузка существующего DataFrame
        print(f"Загрузка существующего DataFrame из: {args.load_existing}")
        try:
            if args.load_existing.endswith(".csv"):
                df = pd.read_csv(args.load_existing)
            elif args.load_existing.endswith(".xlsx"):
                df = pd.read_excel(args.load_existing)
            else:
                raise ValueError("Неподдерживаемый формат файла")
            print(f"Загружено {len(df)} записей")
        except Exception as e:
            print(f"✗ Ошибка загрузки: {e}")
            sys.exit(1)

    elif args.skip_image_analysis:
        # Создание DataFrame без анализа изображений
        print("Создание базового DataFrame (без анализа изображений)")
        df = create_dataframe_from_csv(args.annotation)

    else:
        # Полный процесс: создание DataFrame + анализ изображений
        print("Создание и анализ DataFrame")
        df = create_dataframe_from_csv(args.annotation)

        # Добавление колонок с диапазонами яркости
        print("\n[4/8] Анализ изображений...")
        df = add_brightness_range_columns(df, args.base_dir)

    # Вывод информации о DataFrame
    print_dataframe_info(df, "Исходные данные")

    # 5. Фильтрация (если указана)
    if args.filter_column:
        print("\n[5/8] Применение фильтрации")

        # Определяем условие фильтрации
        if args.filter_operator == "between":
            condition = (args.filter_value, args.filter_value2)
        else:
            condition = args.filter_value

        try:
            df_filtered = filter_by_column(
                df, args.filter_column, condition, args.filter_operator
            )

            if len(df_filtered) > 0:
                df = df_filtered
                print_dataframe_info(df, "Отфильтрованные данные")
            else:
                print("⚠ ВНИМАНИЕ: После фильтрации не осталось записей!")
                print("Продолжаем работу с исходными данными")

        except Exception as e:
            print(f"✗ Ошибка фильтрации: {e}")
            print("Продолжаем работу с исходными данными")

    # 6. Сортировка
    print("\n[6/8] Сортировка данных")

    sort_ascending = args.sort_order == "ascending"

    try:
        df_sorted = sort_by_column(df, args.sort_by, sort_ascending)

        if len(df_sorted) > 0:
            df = df_sorted
            print_dataframe_info(df, "Отсортированные данные")
        else:
            print("⚠ ВНИМАНИЕ: После сортировки не осталось записей!")
            print("Проверьте наличие данных в колонке для сортировки")

    except Exception as e:
        print(f"✗ Ошибка сортировки: {e}")
        sys.exit(1)

    # 7. Построение графиков
    print("\n[7/8] Построение графиков")

    try:
        plots_created = []

        if args.plot_type in ["ranges", "all"]:
            # График диапазонов яркости
            plot_path = plots_dir / "brightness_ranges.png"
            fig1 = plot_brightness_ranges(df, str(plot_path))
            plots_created.append(str(plot_path))
            plt.close(fig1)

        if args.plot_type in ["histogram", "all"]:
            # Гистограмма
            plot_path = plots_dir / "brightness_histogram.png"
            fig2 = plot_brightness_histogram(df, str(plot_path))
            plots_created.append(str(plot_path))
            plt.close(fig2)

        if args.plot_type in ["combined", "all"]:
            # Комбинированный график
            plot_path = plots_dir / "combined_plot.png"
            fig3 = plot_combined_ranges(df, str(plot_path))
            plots_created.append(str(plot_path))
            plt.close(fig3)

        print(f"Создано графиков: {len(plots_created)}")
        for plot in plots_created:
            print(f"  ✓ {plot}")

    except Exception as e:
        print(f"✗ Ошибка построения графиков: {e}")
        import traceback

        traceback.print_exc()

    # 8. Сохранение результатов
    print("\n[8/8] Сохранение результатов")

    try:
        # Сохранение DataFrame в разных форматах
        csv_path = data_dir / "analysis_results.csv"
        excel_path = data_dir / "analysis_results.xlsx"
        json_path = data_dir / "analysis_results.json"

        save_dataframe(df, str(csv_path), "csv")
        save_dataframe(df, str(excel_path), "excel")
        save_dataframe(df, str(json_path), "json")

        print("\n" + "=" * 70)
        print("АНАЛИЗ УСПЕШНО ЗАВЕРШЕН!")
        print("=" * 70)
        print("\nСОЗДАННЫЕ ФАЙЛЫ:")
        print(f"1. CSV с результатами: {csv_path}")
        print(f"2. Excel с результатами: {excel_path}")
        print(f"3. JSON с результатами: {json_path}")

        for plot in plots_created:
            print(f"4. График: {plot}")

        print("\nОБЩАЯ СТАТИСТИКА:")
        print(f"  • Всего обработано записей: {len(df)}")

        if "brightness_range_r" in df.columns:
            print(f"  • Средний диапазон R: {df['brightness_range_r'].mean():.1f}")
            print(f"  • Средний диапазон G: {df['brightness_range_g'].mean():.1f}")
            print(f"  • Средний диапазон B: {df['brightness_range_b'].mean():.1f}")
            print(
                f"  • Средний общий диапазон: {df['total_brightness_range'].mean():.1f}"
            )

        print("\nДиректория с результатами: {results_dir}")
        print("=" * 70)

    except Exception as e:
        print(f"✗ Ошибка сохранения результатов: {e}")


if __name__ == "__main__":

    main()
