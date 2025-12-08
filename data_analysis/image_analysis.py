import numpy as np
from typing import Dict, Optional
import os

from PIL import Image


def calculate_brightness_range(image_path: str) -> Optional[Dict[str, float]]:
    """
    Вычисление диапазона яркости (max-min) по каждому каналу RGB

    Args:
        image_path: путь к изображению

    Returns:
        Dict с диапазонами для каналов R, G, B и общим диапазоном
        None если не удалось обработать изображение
    """
    if not os.path.exists(image_path):
        print(f"Файл не найден: {image_path}")
        return None

    try:
        # Загружаем изображение
        img = Image.open(image_path)

        # Конвертируем в RGB если нужно
        if img.mode not in ["RGB", "RGBA", "L"]:
            img = img.convert("RGB")

        # Конвертируем в массив numpy
        img_array = np.array(img)

        # Обработка разных форматов изображений
        if len(img_array.shape) == 3:  # Цветное изображение (RGB/RGBA)
            if img_array.shape[2] == 4:  # RGBA
                # Убираем альфа-канал
                img_array = img_array[:, :, :3]

            # Разделяем на каналы
            r_channel = img_array[:, :, 0].astype(np.float32)
            g_channel = img_array[:, :, 1].astype(np.float32)
            b_channel = img_array[:, :, 2].astype(np.float32)

            # Вычисляем диапазон яркости (max - min)
            r_range = r_channel.max() - r_channel.min()
            g_range = g_channel.max() - g_channel.min()
            b_range = b_channel.max() - b_channel.min()

            # Общий диапазон (среднее по каналам)
            total_range = (r_range + g_range + b_range) / 3

        elif len(img_array.shape) == 2:  # Черно-белое изображение (L)
            # Для черно-белых изображений все каналы одинаковые
            gray_channel = img_array.astype(np.float32)
            gray_range = gray_channel.max() - gray_channel.min()

            r_range = g_range = b_range = gray_range
            total_range = gray_range

        else:
            print(f"Неизвестный формат изображения: {img_array.shape}")
            return None

        return {
            "r": float(r_range),
            "g": float(g_range),
            "b": float(b_range),
            "total": float(total_range),
        }

    except Exception as e:
        print(f"Ошибка обработки изображения {image_path}: {e}")
        return None


def calculate_brightness_stats(image_path: str) -> Optional[Dict[str, float]]:
    """
    Вычисление статистики яркости изображения

    Args:
        image_path: путь к изображению

    Returns:
        Dict со статистикой: mean, std, min, max, range
    """
    brightness_range = calculate_brightness_range(image_path)

    if brightness_range is None:
        return None

    # Загружаем изображение для вычисления дополнительной статистики
    try:
        img = Image.open(image_path)
        img_array = np.array(img)

        if len(img_array.shape) == 3 and img_array.shape[2] >= 3:
            # Для цветных изображений вычисляем среднюю яркость
            if img_array.shape[2] == 4:  # RGBA
                img_array = img_array[:, :, :3]

            # Конвертируем в grayscale для вычисления средней яркости
            gray_img = np.dot(img_array[..., :3], [0.2989, 0.5870, 0.1140])
            mean_brightness = float(gray_img.mean())
            std_brightness = float(gray_img.std())

        elif len(img_array.shape) == 2:  # Черно-белое
            mean_brightness = float(img_array.mean())
            std_brightness = float(img_array.std())

        else:
            mean_brightness = 0
            std_brightness = 0

        stats = {
            "mean_brightness": mean_brightness,
            "std_brightness": std_brightness,
            "min_brightness_r": brightness_range["r_min"]
            if "r_min" in brightness_range
            else 0,
            "max_brightness_r": brightness_range["r_max"]
            if "r_max" in brightness_range
            else 255,
            "range_r": brightness_range["r"],
            "range_g": brightness_range["g"],
            "range_b": brightness_range["b"],
            "total_range": brightness_range["total"],
        }

        return stats

    except Exception as e:
        print(f"Ошибка вычисления статистики {image_path}: {e}")
        return None
