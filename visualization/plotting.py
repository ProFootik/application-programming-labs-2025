from typing import Optional
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def plot_brightness_ranges(
    df: pd.DataFrame, save_path: Optional[str] = None
) -> plt.Figure:
    """
    Построение графика диапазонов яркости по каналам RGB

    Args:
        df: DataFrame с данными
        save_path: путь для сохранения графика

    Returns:
        plt.Figure: объект графика
    """
    # Проверяем наличие необходимых колонок
    required_columns = [
        "brightness_range_r",
        "brightness_range_g",
        "brightness_range_b",
        "sorted_index",
    ]

    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"В DataFrame отсутствует колонка: '{col}'")

    # Создаем фигуру
    fig, ax = plt.subplots(figsize=(12, 6))

    # Получаем данные
    x = df["sorted_index"]
    y_r = df["brightness_range_r"]
    y_g = df["brightness_range_g"]
    y_b = df["brightness_range_b"]

    # Строим графики для каждого канала
    ax.plot(x, y_r, "r-", linewidth=2, alpha=0.7, label="Red channel")
    ax.plot(x, y_g, "g-", linewidth=2, alpha=0.7, label="Green channel")
    ax.plot(x, y_b, "b-", linewidth=2, alpha=0.7, label="Blue channel")

    # Настройка графика
    ax.set_xlabel("Номер изображения (отсортировано)", fontsize=12)
    ax.set_ylabel("Диапазон яркости (max - min)", fontsize=12)
    ax.set_title(
        "Диапазон яркости по каналам RGB для изображений",
        fontsize=14,
        fontweight="bold",
    )

    # Добавляем сетку
    ax.grid(True, alpha=0.3)

    # Добавляем легенду
    ax.legend(loc="best", fontsize=10)

    # Настраиваем пределы осей
    ax.set_xlim([0, len(df)])

    # Автоматическая настройка пределов оси Y
    all_values = pd.concat([y_r, y_g, y_b])
    y_min = all_values.min() * 0.9
    y_max = all_values.max() * 1.1
    ax.set_ylim([max(0, y_min), y_max])

    # Добавляем информацию о данных
    stats_text = (
        f"Всего изображений: {len(df)}\n"
        f"Средний диапазон R: {y_r.mean():.1f}\n"
        f"Средний диапазон G: {y_g.mean():.1f}\n"
        f"Средний диапазон B: {y_b.mean():.1f}"
    )

    ax.text(
        0.02,
        0.98,
        stats_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )

    plt.tight_layout()

    if save_path:
        save_plot(fig, save_path)

    return fig


def plot_brightness_histogram(
    df: pd.DataFrame, save_path: Optional[str] = None
) -> plt.Figure:
    """
    Построение гистограммы диапазонов яркости

    Args:
        df: DataFrame с данными
        save_path: путь для сохранения графика

    Returns:
        plt.Figure: объект графика
    """
    # Проверяем наличие необходимых колонок
    required_columns = [
        "brightness_range_r",
        "brightness_range_g",
        "brightness_range_b",
    ]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"В DataFrame отсутствует колонка: '{col}'")

    # Создаем фигуру с тремя подграфиками
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Данные для каждого канала
    channels = {
        "Red": df["brightness_range_r"],
        "Green": df["brightness_range_g"],
        "Blue": df["brightness_range_b"],
    }

    colors = ["red", "green", "blue"]

    for idx, (channel_name, data) in enumerate(channels.items()):
        ax = axes[idx]

        # Определяем диапазоны для гистограммы
        # Автоматически определяем количество бинов
        n_bins = min(20, len(data) // 5)
        n_bins = max(5, n_bins)  # Минимум 5 бинов

        # Строим гистограмму
        ax.hist(
            data.dropna(), bins=n_bins, color=colors[idx], alpha=0.7, edgecolor="black"
        )

        # Настройки графика
        ax.set_xlabel(f"Диапазон яркости ({channel_name})", fontsize=10)
        ax.set_ylabel("Количество изображений", fontsize=10)
        ax.set_title(
            f"Гистограмма: {channel_name} канал", fontsize=12, fontweight="bold"
        )

        # Добавляем сетку
        ax.grid(True, alpha=0.3)

        # Добавляем статистику
        mean_val = data.mean()
        std_val = data.std()

        stats_text = (
            f"Среднее: {mean_val:.1f}\n"
            f"Ст. отклонение: {std_val:.1f}\n"
            f"Мин: {data.min():.1f}\n"
            f"Макс: {data.max():.1f}"
        )

        ax.text(
            0.05,
            0.95,
            stats_text,
            transform=ax.transAxes,
            fontsize=8,
            verticalalignment="top",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        )

    plt.suptitle(
        "Гистограммы диапазонов яркости по каналам RGB", fontsize=14, fontweight="bold"
    )
    plt.tight_layout()

    if save_path:
        save_plot(fig, save_path)

    return fig


def plot_combined_ranges(
    df: pd.DataFrame, save_path: Optional[str] = None
) -> plt.Figure:
    """
    Комбинированный график: линии + гистограмма

    Args:
        df: DataFrame с данными
        save_path: путь для сохранения графика

    Returns:
        plt.Figure: объект графика
    """
    # Проверяем наличие необходимых колонок
    required_columns = [
        "brightness_range_r",
        "brightness_range_g",
        "brightness_range_b",
        "sorted_index",
    ]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"В DataFrame отсутствует колонка: '{col}'")

    # Создаем фигуру с двумя подграфиками
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # График 1: Линии диапазонов яркости
    x = df["sorted_index"]
    ax1.plot(x, df["brightness_range_r"], "r-", alpha=0.7, label="Red", linewidth=1.5)
    ax1.plot(x, df["brightness_range_g"], "g-", alpha=0.7, label="Green", linewidth=1.5)
    ax1.plot(x, df["brightness_range_b"], "b-", alpha=0.7, label="Blue", linewidth=1.5)

    ax1.set_xlabel("Номер изображения", fontsize=11)
    ax1.set_ylabel("Диапазон яркости", fontsize=11)
    ax1.set_title(
        "Динамика диапазонов яркости по изображениям", fontsize=13, fontweight="bold"
    )
    ax1.legend(loc="best")
    ax1.grid(True, alpha=0.3)

    # График 2: Гистограмма общего диапазона
    total_range = df[
        ["brightness_range_r", "brightness_range_g", "brightness_range_b"]
    ].mean(axis=1)

    n_bins = min(15, len(total_range) // 10)
    n_bins = max(5, n_bins)

    ax2.hist(total_range, bins=n_bins, color="purple", alpha=0.7, edgecolor="black")
    ax2.set_xlabel("Средний диапазон яркости (по всем каналам)", fontsize=11)
    ax2.set_ylabel("Количество изображений", fontsize=11)
    ax2.set_title(
        "Распределение среднего диапазона яркости", fontsize=13, fontweight="bold"
    )
    ax2.grid(True, alpha=0.3)

    # Добавляем статистику на гистограмму
    stats_text = (
        f"Среднее: {total_range.mean():.1f}\n"
        f"Медиана: {total_range.median():.1f}\n"
        f"Всего: {len(total_range)}"
    )

    ax2.text(
        0.05,
        0.95,
        stats_text,
        transform=ax2.transAxes,
        fontsize=9,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )

    plt.tight_layout()

    if save_path:
        save_plot(fig, save_path)

    return fig


def save_plot(fig: plt.Figure, save_path: str, dpi: int = 150) -> None:
    """
    Сохранение графика в файл

    Args:
        fig: объект графика
        save_path: путь для сохранения
        dpi: разрешение (точек на дюйм)
    """
    # Создаем директорию если ее нет
    output_dir = Path(save_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Сохраняем график
    fig.savefig(save_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    print(f"График сохранен: {save_path}")
