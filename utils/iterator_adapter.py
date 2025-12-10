"""
Адаптер для итератора из лабораторной работы №2
Позволяет использовать итератор в GUI приложении
"""

import os
import pandas as pd
from typing import Optional, List
from pathlib import Path


class ImageIteratorAdapter:
    """
    Адаптер для работы с итератором изображений
    Поддерживает два режима: из папки и из аннотации CSV
    """

    def __init__(self, paths: List[str]):
        """
        Инициализация итератора

        Args:
            paths: список путей к изображениям
        """
        self.paths = paths
        self.current_index = 0
        self.total = len(paths)

        # Проверяем существование файлов
        self.existing_paths = []
        for path in self.paths:
            if isinstance(path, str) and os.path.exists(path):
                self.existing_paths.append(path)

        if len(self.existing_paths) < len(self.paths):
            print(
                f"Предупреждение: {len(self.paths) - len(self.existing_paths)} файлов не найдено"
            )

    @classmethod
    def from_folder(cls, folder_path: str) -> "ImageIteratorAdapter":
        """
        Создание итератора из папки

        Args:
            folder_path: путь к папке с изображениями

        Returns:
            ImageIteratorAdapter

        Raises:
            FileNotFoundError: если папка не существует
            ValueError: если в папке нет изображений
        """
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Папка не найдена: {folder_path}")

        # Поддерживаемые форматы изображений
        image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"}

        # Рекурсивный поиск всех изображений
        paths = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = Path(file)
                if file_path.suffix.lower() in image_extensions:
                    full_path = os.path.join(root, file)
                    paths.append(full_path)

        if not paths:
            raise ValueError(f"В папке не найдено изображений: {folder_path}")

        print(f"Найдено {len(paths)} изображений в папке: {folder_path}")
        return cls(sorted(paths))

    @classmethod
    def from_annotation(
        cls, annotation_path: str, base_dir: Optional[str] = None
    ) -> "ImageIteratorAdapter":
        """
        Создание итератора из CSV аннотации

        Args:
            annotation_path: путь к CSV файлу аннотации
            base_dir: базовая директория для относительных путей

        Returns:
            ImageIteratorAdapter

        Raises:
            FileNotFoundError: если файл аннотации не найден
            ValueError: если CSV файл имеет неверный формат
        """
        if not os.path.exists(annotation_path):
            raise FileNotFoundError(f"Файл аннотации не найден: {annotation_path}")

        try:
            # Чтение CSV файла
            df = pd.read_csv(annotation_path, encoding="utf-8")

            # Пробуем разные кодировки если utf-8 не работает
            if df.empty:
                try:
                    df = pd.read_csv(annotation_path, encoding="cp1251")
                except UnicodeDecodeError:
                    df = pd.read_csv(annotation_path, encoding="latin1")

            # Проверяем что файл не пустой
            if df.empty:
                raise ValueError("CSV файл аннотации пуст")

            # Приводим имена колонок к нижнему регистру для удобства
            df.columns = df.columns.str.strip().str.lower()

            # Определяем какие колонки с путями есть в файле
            paths = []

            # Вариант 1: Абсолютные пути
            abs_path_cols = [
                "абсолютный путь",
                "absolute_path",
                "path",
                "filepath",
                "абсолютный_путь",
            ]
            for col in abs_path_cols:
                if col in df.columns:
                    # Берем не пустые значения
                    abs_paths = df[col].dropna().astype(str).tolist()
                    # Проверяем существование файлов
                    existing_paths = [p for p in abs_paths if os.path.exists(p)]

                    if existing_paths:
                        paths = existing_paths
                        print(f"Используются абсолютные пути из колонки: '{col}'")
                        print(
                            f"Найдено {len(existing_paths)} из {len(abs_paths)} файлов"
                        )
                        break

            # Вариант 2: Относительные пути + базовая директория
            if not paths and base_dir:
                rel_path_cols = [
                    "относительный путь",
                    "relative_path",
                    "relative",
                    "относительный_путь",
                ]
                for col in rel_path_cols:
                    if col in df.columns:
                        rel_paths = df[col].dropna().astype(str).tolist()
                        # Собираем полные пути
                        full_paths = []
                        for rel_path in rel_paths:
                            full_path = os.path.join(base_dir, rel_path)
                            if os.path.exists(full_path):
                                full_paths.append(full_path)

                        if full_paths:
                            paths = full_paths
                            print(
                                f"Используются относительные пути из колонки: '{col}'"
                            )
                            print(
                                f"Найдено {len(full_paths)} из {len(rel_paths)} файлов"
                            )
                            break

            # Вариант 3: Просто имена файлов в первой колонке
            if not paths and len(df.columns) > 0:
                # Предполагаем что первая колонка содержит имена файлов
                first_col = df.columns[0]
                if base_dir:
                    # Пробуем найти файлы в базовой директории
                    filenames = df[first_col].dropna().astype(str).tolist()
                    found_files = []

                    for filename in filenames:
                        # Рекурсивный поиск файла в базовой директории
                        for root, _, files in os.walk(base_dir):
                            if filename in files:
                                found_files.append(os.path.join(root, filename))
                                break

                    if found_files:
                        paths = found_files
                        print(f"Найдены файлы по именам из колонки: '{first_col}'")
                        print(f"Найдено {len(found_files)} файлов")

            if not paths:
                error_msg = "Не удалось извлечь пути к изображениям из аннотации.\n"
                error_msg += f"Доступные колонки: {list(df.columns)}\n"
                if not base_dir:
                    error_msg += "Для относительных путей нужна базовая директория."
                raise ValueError(error_msg)

            return cls(sorted(paths))

        except pd.errors.EmptyDataError:
            raise ValueError("CSV файл аннотации пуст")
        except pd.errors.ParserError as e:
            raise ValueError(f"Ошибка парсинга CSV файла: {str(e)[:100]}")
        except Exception as e:
            raise ValueError(f"Ошибка обработки аннотации: {str(e)}")

    # ========== ОСНОВНЫЕ МЕТОДЫ ИТЕРАТОРА ==========

    def has_next(self) -> bool:
        """Проверка наличия следующего изображения"""
        return self.current_index < len(self.existing_paths) - 1

    def has_previous(self) -> bool:
        """Проверка наличия предыдущего изображения"""
        return self.current_index > 0

    def next(self) -> Optional[str]:
        """Получение следующего изображения"""
        if self.has_next():
            self.current_index += 1
            return self.get_current()
        return None

    def previous(self) -> Optional[str]:
        """Получение предыдущего изображения"""
        if self.has_previous():
            self.current_index -= 1
            return self.get_current()
        return None

    def get_current(self) -> Optional[str]:
        """Получение текущего изображения"""
        if 0 <= self.current_index < len(self.existing_paths):
            return self.existing_paths[self.current_index]
        return None

    def get_by_index(self, index: int) -> Optional[str]:
        """Получение изображения по индексу"""
        if 0 <= index < len(self.existing_paths):
            return self.existing_paths[index]
        return None

    def reset(self):
        """Сброс итератора к началу"""
        self.current_index = 0

    def total_count(self) -> int:
        """Общее количество существующих изображений"""
        return len(self.existing_paths)

    def all_paths(self) -> List[str]:
        """Получение всех путей (включая несуществующие)"""
        return self.paths

    def existing_paths_list(self) -> List[str]:
        """Получение только существующих путей"""
        return self.existing_paths

    # ========== ДОПОЛНИТЕЛЬНЫЕ МЕТОДЫ ==========

    def goto(self, index: int) -> Optional[str]:
        """
        Переход к изображению по индексу

        Args:
            index: индекс изображения (начиная с 0)

        Returns:
            Путь к изображению или None если индекс невалидный
        """
        if 0 <= index < len(self.existing_paths):
            self.current_index = index
            return self.get_current()
        return None

    def get_current_index(self) -> int:
        """Получение текущего индекса"""
        return self.current_index

    def get_file_info(self, index: Optional[int] = None) -> dict:
        """
        Получение информации о файле

        Args:
            index: индекс файла (если None - текущий)

        Returns:
            Словарь с информацией о файле
        """
        if index is None:
            index = self.current_index

        if 0 <= index < len(self.existing_paths):
            path = self.existing_paths[index]
            return {
                "path": path,
                "filename": os.path.basename(path),
                "directory": os.path.dirname(path),
                "exists": os.path.exists(path),
                "size": os.path.getsize(path) if os.path.exists(path) else 0,
                "extension": os.path.splitext(path)[1].lower(),
            }
        return {}

    def search_by_name(self, search_term: str) -> List[int]:
        """
        Поиск изображений по имени

        Args:
            search_term: строка для поиска в именах файлов

        Returns:
            Список индексов найденных файлов
        """
        search_term = search_term.lower()
        indices = []

        for i, path in enumerate(self.existing_paths):
            filename = os.path.basename(path).lower()
            if search_term in filename:
                indices.append(i)

        return indices

    # ========== МАГИЧЕСКИЕ МЕТОДЫ ==========

    def __iter__(self):
        """Возвращает итератор для использования в циклах for"""
        self._iter_index = 0
        return self

    def __next__(self):
        """Получение следующего элемента в цикле for"""
        if self._iter_index < len(self.existing_paths):
            path = self.existing_paths[self._iter_index]
            self._iter_index += 1
            return path
        raise StopIteration

    def __len__(self):
        """Количество существующих изображений"""
        return len(self.existing_paths)

    def __getitem__(self, index: int) -> str:
        """Получение изображения по индексу через квадратные скобки"""
        if 0 <= index < len(self.existing_paths):
            return self.existing_paths[index]
        raise IndexError(
            f"Индекс {index} вне диапазона [0, {len(self.existing_paths) - 1}]"
        )

    def __str__(self):
        """Строковое представление итератора"""
        return f"ImageIteratorAdapter({len(self.existing_paths)}/{len(self.paths)} изображений)"

    def __repr__(self):
        """Представление для отладки"""
        return f"ImageIteratorAdapter(paths={len(self.paths)}, current={self.current_index})"
