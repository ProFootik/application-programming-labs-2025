import sys
import os
from typing import Optional

from pathlib import Path
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QComboBox,
    QGroupBox,
    QSpinBox,
    QSlider,
    QProgressBar,
    QStatusBar,
    QAction,
    QSplitter,
    QFrame,
)
from PyQt5.QtGui import QPixmap, QFont, QTransform
from PyQt5.QtCore import Qt

# Импортируем адаптер для итератора
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils.iterator_adapter import ImageIteratorAdapter


class ImageViewer(QMainWindow):
    """
    Главное окно приложения для просмотра изображений
    """

    def __init__(self):
        super().__init__()

        # Инициализация переменных
        self.image_iterator = None
        self.current_image_path = None
        self.current_image_index = 0
        self.total_images = 0
        self.image_cache = {}  # Кэш для загруженных изображений

        # Настройка окна
        self.setWindowTitle("Просмотрщик изображений - Лабораторная работа №5")
        self.setGeometry(100, 100, 1200, 800)  # x, y, width, height

        # Установка стиля
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #ffffff;
                font-size: 12px;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border: 1px solid #666;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            QPushButton:disabled {
                background-color: #252525;
                color: #777;
            }
            QGroupBox {
                color: white;
                border: 2px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                font-size: 13px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QComboBox {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 3px;
            }
            QSpinBox {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 3px;
            }
            QStatusBar {
                background-color: #252525;
                color: white;
            }
        """)

        # Инициализация UI
        self.init_ui()

        # Показать приветственное сообщение
        self.show_welcome_message()

    def init_ui(self):
        """Инициализация пользовательского интерфейса"""

        # Создание центрального виджета
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной вертикальный layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 1. Панель управления (верхняя часть)
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)

        # 2. Разделитель
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter, 1)  # 1 означает растягивание

        # 3. Панель информации (левая часть)
        info_panel = self.create_info_panel()
        splitter.addWidget(info_panel)

        # 4. Панель изображения (правая часть)
        image_panel = self.create_image_panel()
        splitter.addWidget(image_panel)

        # Установка начальных размеров разделителя
        splitter.setSizes([300, 900])

        # 5. Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готов к работе. Загрузите датасет или аннотацию.")

        # 6. Меню бар
        self.create_menu_bar()

    def create_control_panel(self) -> QGroupBox:
        """Создание панели управления"""
        control_group = QGroupBox("Управление")
        control_layout = QHBoxLayout()

        # Кнопка загрузки папки
        self.btn_load_folder = QPushButton("📁 Загрузить папку")
        self.btn_load_folder.setToolTip("Загрузить папку с изображениями")
        self.btn_load_folder.clicked.connect(self.load_folder)
        control_layout.addWidget(self.btn_load_folder)

        # Кнопка загрузки аннотации
        self.btn_load_annotation = QPushButton("📄 Загрузить аннотацию")
        self.btn_load_annotation.setToolTip("Загрузить CSV файл аннотации")
        self.btn_load_annotation.clicked.connect(self.load_annotation)
        control_layout.addWidget(self.btn_load_annotation)

        # Выбор режима отображения
        control_layout.addWidget(QLabel("Режим:"))
        self.combo_display_mode = QComboBox()
        self.combo_display_mode.addItems(
            ["Исходный размер", "Подогнать к окну", "Растянуть"]
        )
        self.combo_display_mode.setCurrentIndex(1)
        self.combo_display_mode.currentIndexChanged.connect(self.update_image_display)
        control_layout.addWidget(self.combo_display_mode)

        # Настройка масштаба
        control_layout.addWidget(QLabel("Масштаб:"))
        self.slider_zoom = QSlider(Qt.Horizontal)
        self.slider_zoom.setRange(10, 200)  # от 10% до 200%
        self.slider_zoom.setValue(100)
        self.slider_zoom.setTickPosition(QSlider.TicksBelow)
        self.slider_zoom.setTickInterval(10)
        self.slider_zoom.valueChanged.connect(self.on_zoom_changed)
        control_layout.addWidget(self.slider_zoom)

        # Отображение текущего масштаба
        self.label_zoom = QLabel("100%")
        self.label_zoom.setMinimumWidth(50)
        control_layout.addWidget(self.label_zoom)

        control_group.setLayout(control_layout)
        return control_group

    def create_info_panel(self) -> QGroupBox:
        """Создание панели информации"""
        info_group = QGroupBox("Информация")
        info_layout = QVBoxLayout()

        # Информация о файле
        self.label_filename = QLabel("Файл: не загружен")
        self.label_filename.setWordWrap(True)
        info_layout.addWidget(self.label_filename)

        self.label_path = QLabel("Путь: -")
        self.label_path.setWordWrap(True)
        info_layout.addWidget(self.label_path)

        self.label_size = QLabel("Размер: -")
        info_layout.addWidget(self.label_size)

        self.label_format = QLabel("Формат: -")
        info_layout.addWidget(self.label_format)

        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        info_layout.addWidget(line)

        # Информация о навигации
        self.label_navigation = QLabel("Изображение: 0/0")
        info_layout.addWidget(self.label_navigation)

        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        info_layout.addWidget(self.progress_bar)

        # Кнопки навигации
        nav_layout = QHBoxLayout()

        self.btn_prev = QPushButton("⏪ Предыдущее")
        self.btn_prev.clicked.connect(self.show_previous_image)
        self.btn_prev.setEnabled(False)
        nav_layout.addWidget(self.btn_prev)

        self.btn_next = QPushButton("Следующее ⏩")
        self.btn_next.clicked.connect(self.show_next_image)
        self.btn_next.setEnabled(False)
        nav_layout.addWidget(self.btn_next)

        info_layout.addLayout(nav_layout)

        # Кнопка перехода к конкретному изображению
        goto_layout = QHBoxLayout()
        goto_layout.addWidget(QLabel("Перейти к:"))

        self.spin_image_index = QSpinBox()
        self.spin_image_index.setRange(1, 1)
        self.spin_image_index.setValue(1)
        self.spin_image_index.valueChanged.connect(self.go_to_image)
        goto_layout.addWidget(self.spin_image_index)

        goto_layout.addWidget(QLabel(f"/ {self.total_images}"))
        info_layout.addLayout(goto_layout)

        # Разделитель
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        info_layout.addWidget(line2)

        # Кнопка информации
        self.btn_info = QPushButton("ℹ️ Подробная информация")
        self.btn_info.clicked.connect(self.show_detailed_info)
        self.btn_info.setEnabled(False)
        info_layout.addWidget(self.btn_info)

        # Растягивающийся spacer
        info_layout.addStretch()

        info_group.setLayout(info_layout)
        return info_group

    def create_image_panel(self) -> QGroupBox:
        """Создание панели для отображения изображения"""
        image_group = QGroupBox("Изображение")
        image_layout = QVBoxLayout()

        # Метка для изображения с выравниванием по центру
        self.label_image = QLabel()
        self.label_image.setAlignment(Qt.AlignCenter)
        self.label_image.setMinimumSize(400, 300)

        # Установка фона для метки изображения
        self.label_image.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 2px solid #444;
                border-radius: 5px;
            }
        """)

        # Текст по умолчанию
        self.label_image.setText("Изображение не загружено")
        self.label_image.setFont(QFont("Arial", 14))

        image_layout.addWidget(self.label_image)

        # Панель управления изображением
        image_control_layout = QHBoxLayout()

        self.btn_fit = QPushButton("Подогнать")
        self.btn_fit.clicked.connect(lambda: self.set_display_mode(1))
        image_control_layout.addWidget(self.btn_fit)

        self.btn_original = QPushButton("Оригинал")
        self.btn_original.clicked.connect(lambda: self.set_display_mode(0))
        image_control_layout.addWidget(self.btn_original)

        self.btn_rotate_left = QPushButton("↺ Повернуть влево")
        self.btn_rotate_left.clicked.connect(self.rotate_left)
        image_control_layout.addWidget(self.btn_rotate_left)

        self.btn_rotate_right = QPushButton("Повернуть вправо ↻")
        self.btn_rotate_right.clicked.connect(self.rotate_right)
        image_control_layout.addWidget(self.btn_rotate_right)

        image_layout.addLayout(image_control_layout)

        image_group.setLayout(image_layout)
        return image_group

    def create_menu_bar(self):
        """Создание меню бара"""
        menubar = self.menuBar()

        # Меню Файл
        file_menu = menubar.addMenu("Файл")

        load_folder_action = QAction("Загрузить папку", self)
        load_folder_action.triggered.connect(self.load_folder)
        file_menu.addAction(load_folder_action)

        load_annotation_action = QAction("Загрузить аннотацию", self)
        load_annotation_action.triggered.connect(self.load_annotation)
        file_menu.addAction(load_annotation_action)

        file_menu.addSeparator()

        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню Вид
        view_menu = menubar.addMenu("Вид")

        zoom_in_action = QAction("Увеличить", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Уменьшить", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)

        view_menu.addSeparator()

        original_size_action = QAction("Оригинальный размер", self)
        original_size_action.triggered.connect(lambda: self.set_display_mode(0))
        view_menu.addAction(original_size_action)

        fit_to_window_action = QAction("Подогнать к окну", self)
        fit_to_window_action.triggered.connect(lambda: self.set_display_mode(1))
        view_menu.addAction(fit_to_window_action)

        # Меню Помощь
        help_menu = menubar.addMenu("Помощь")

        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def show_welcome_message(self):
        """Показать приветственное сообщение"""
        QMessageBox.information(
            self,
            "Добро пожаловать!",
            "Лабораторная работа №5: Просмотрщик изображений\n\n"
            "1. Загрузите папку с изображениями или CSV аннотацию\n"
            "2. Используйте кнопки навигации для просмотра\n"
            "3. Настройте отображение с помощью элементов управления",
        )

    # ========== ОСНОВНЫЕ ФУНКЦИИ ==========

    def load_folder(self):
        """Загрузка папки с изображениями"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Выберите папку с изображениями",
            str(Path.home()),
            QFileDialog.ShowDirsOnly,
        )

        if folder_path:
            try:
                # Создаем итератор на основе папки
                self.image_iterator = ImageIteratorAdapter.from_folder(folder_path)
                self.total_images = self.image_iterator.total_count()
                self.current_image_index = 0

                # Обновляем UI
                self.update_navigation_controls()
                self.show_current_image()

                self.status_bar.showMessage(
                    f"Загружена папка: {folder_path} ({self.total_images} изображений)"
                )

            except Exception as e:
                QMessageBox.critical(
                    self, "Ошибка", f"Не удалось загрузить папку:\n{str(e)}"
                )

    def load_annotation(self):
        """Загрузка CSV аннотации"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите CSV файл аннотации",
            str(Path.home()),
            "CSV Files (*.csv);;All Files (*.*)",
        )

        if file_path:
            try:
                # Создаем итератор на основе аннотации
                self.image_iterator = ImageIteratorAdapter.from_annotation(file_path)
                self.total_images = self.image_iterator.total_count()
                self.current_image_index = 0

                # Обновляем UI
                self.update_navigation_controls()
                self.show_current_image()

                self.status_bar.showMessage(
                    f"Загружена аннотация: {file_path} ({self.total_images} изображений)"
                )

            except Exception as e:
                QMessageBox.critical(
                    self, "Ошибка", f"Не удалось загрузить аннотацию:\n{str(e)}"
                )

    def show_current_image(self):
        """Отображение текущего изображения"""
        if not self.image_iterator or self.total_images == 0:
            return

        try:
            # Получаем путь к текущему изображению
            image_path = self.image_iterator.get_current()
            self.current_image_path = image_path

            # Загружаем изображение
            pixmap = self.load_image(image_path)

            if pixmap:
                # Применяем текущий режим отображения
                self.apply_display_mode(pixmap)

                # Обновляем информацию
                self.update_file_info(image_path, pixmap)
                self.btn_info.setEnabled(True)

                # Добавляем в кэш
                self.image_cache[self.current_image_index] = pixmap

                self.status_bar.showMessage(
                    f"Загружено: {os.path.basename(image_path)}"
                )
            else:
                self.label_image.setText("Не удалось загрузить изображение")
                self.clear_file_info()

        except Exception as e:
            self.label_image.setText(f"Ошибка: {str(e)}")
            self.clear_file_info()

    def load_image(self, image_path: str) -> Optional[QPixmap]:
        """Загрузка изображения с обработкой ошибок"""
        if not os.path.exists(image_path):
            QMessageBox.warning(
                self, "Файл не найден", f"Файл не существует:\n{image_path}"
            )
            return None

        try:
            # Создаем QPixmap из файла
            pixmap = QPixmap(image_path)

            if pixmap.isNull():
                raise ValueError("Неверный формат изображения или файл поврежден")

            return pixmap

        except Exception as e:
            QMessageBox.warning(
                self, "Ошибка загрузки", f"Не удалось загрузить изображение:\n{str(e)}"
            )
            return None

    def apply_display_mode(self, pixmap: QPixmap):
        """Применение выбранного режима отображения"""
        mode = self.combo_display_mode.currentIndex()
        zoom_factor = self.slider_zoom.value() / 100.0

        if mode == 0:  # Исходный размер
            scaled_pixmap = pixmap.scaled(
                pixmap.size() * zoom_factor, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )

        elif mode == 1:  # Подогнать к окну
            label_size = self.label_image.size()
            scaled_pixmap = pixmap.scaled(
                label_size * zoom_factor, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )

        else:  # Растянуть
            label_size = self.label_image.size()
            scaled_pixmap = pixmap.scaled(
                label_size * zoom_factor, Qt.IgnoreAspectRatio, Qt.SmoothTransformation
            )

        # Устанавливаем изображение
        self.label_image.setPixmap(scaled_pixmap)

    def update_image_display(self):
        """Обновление отображения текущего изображения"""
        if self.current_image_path and self.image_iterator:
            # Пробуем получить из кэша
            if self.current_image_index in self.image_cache:
                pixmap = self.image_cache[self.current_image_index]
                self.apply_display_mode(pixmap)
            else:
                self.show_current_image()

    # ========== НАВИГАЦИЯ ==========

    def show_next_image(self):
        """Показать следующее изображение"""
        if self.image_iterator and self.image_iterator.has_next():
            self.image_iterator.next()
            self.current_image_index += 1
            self.show_current_image()
            self.update_navigation_controls()

    def show_previous_image(self):
        """Показать предыдущее изображение"""
        if self.image_iterator and self.image_iterator.has_previous():
            self.image_iterator.previous()
            self.current_image_index -= 1
            self.show_current_image()
            self.update_navigation_controls()

    def go_to_image(self, index: int):
        """Перейти к конкретному изображению"""
        if self.image_iterator and 1 <= index <= self.total_images:
            # Индекс в spinbox начинается с 1, наш индекс с 0
            target_index = index - 1

            if 0 <= target_index < self.total_images:
                # Простой способ: сбрасываем итератор и переходим вперед
                # В реальном проекте нужно реализовать метод goto в итераторе
                self.image_iterator.reset()
                for _ in range(target_index):
                    self.image_iterator.next()

                self.current_image_index = target_index
                self.show_current_image()
                self.update_navigation_controls()

    def update_navigation_controls(self):
        """Обновление элементов управления навигацией"""
        if self.image_iterator:
            # Обновляем спинбокс
            self.spin_image_index.setRange(1, max(1, self.total_images))
            self.spin_image_index.setValue(self.current_image_index + 1)

            # Обновляем метку навигации
            self.label_navigation.setText(
                f"Изображение: {self.current_image_index + 1}/{self.total_images}"
            )

            # Обновляем прогресс бар
            if self.total_images > 0:
                progress = int((self.current_image_index + 1) / self.total_images * 100)
                self.progress_bar.setValue(progress)

            # Активируем/деактивируем кнопки навигации
            self.btn_prev.setEnabled(self.image_iterator.has_previous())
            self.btn_next.setEnabled(self.image_iterator.has_next())

            # Активируем/деактивируем кнопки загрузки
            self.btn_load_folder.setEnabled(True)
            self.btn_load_annotation.setEnabled(True)

    # ========== ИНФОРМАЦИЯ О ФАЙЛЕ ==========

    def update_file_info(self, image_path: str, pixmap: QPixmap):
        """Обновление информации о файле"""
        # Имя файла
        filename = os.path.basename(image_path)
        self.label_filename.setText(f"Файл: {filename}")

        # Путь
        self.label_path.setText(f"Путь: {image_path}")

        # Размер изображения
        width = pixmap.width()
        height = pixmap.height()
        self.label_size.setText(f"Размер: {width} × {height} пикселей")

        # Формат файла
        _, ext = os.path.splitext(image_path)
        self.label_format.setText(f"Формат: {ext.upper().replace('.', '')}")

    def clear_file_info(self):
        """Очистка информации о файле"""
        self.label_filename.setText("Файл: не загружен")
        self.label_path.setText("Путь: -")
        self.label_size.setText("Размер: -")
        self.label_format.setText("Формат: -")
        self.btn_info.setEnabled(False)

    def show_detailed_info(self):
        """Показать подробную информацию об изображении"""
        if not self.current_image_path:
            return

        try:
            import PIL.Image
            from PIL.ExifTags import TAGS

            image = PIL.Image.open(self.current_image_path)

            info_text = "Подробная информация:\n\n"
            info_text += f"Файл: {os.path.basename(self.current_image_path)}\n"
            info_text += f"Путь: {self.current_image_path}\n"
            info_text += f"Размер: {image.width} × {image.height}\n"
            info_text += f"Формат: {image.format}\n"
            info_text += f"Режим: {image.mode}\n"

            # EXIF данные
            exif_data = image._getexif()
            if exif_data:
                info_text += "\nEXIF данные:\n"
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    info_text += f"  {tag}: {value}\n"

            image.close()

            QMessageBox.information(self, "Подробная информация", info_text)

        except Exception as e:
            QMessageBox.warning(
                self, "Ошибка", f"Не удалось получить информацию:\n{str(e)}"
            )

    # ========== УПРАВЛЕНИЕ ОТОБРАЖЕНИЕМ ==========

    def set_display_mode(self, mode: int):
        """Установка режима отображения"""
        self.combo_display_mode.setCurrentIndex(mode)

    def on_zoom_changed(self, value: int):
        """Обработка изменения масштаба"""
        self.label_zoom.setText(f"{value}%")
        self.update_image_display()

    def zoom_in(self):
        """Увеличить масштаб"""
        current = self.slider_zoom.value()
        if current < self.slider_zoom.maximum():
            self.slider_zoom.setValue(current + 10)

    def zoom_out(self):
        """Уменьшить масштаб"""
        current = self.slider_zoom.value()
        if current > self.slider_zoom.minimum():
            self.slider_zoom.setValue(current - 10)

    def rotate_left(self):
        """Повернуть изображение на 90° влево"""
        if self.current_image_index in self.image_cache:
            pixmap = self.image_cache[self.current_image_index]
            
            # Создаем трансформацию для поворота на -90 градусов
            transform = QTransform()
            transform.rotate(-90)
            
            # Применяем трансформацию с сглаживанием
            transformed = pixmap.transformed(
                transform,
                Qt.SmoothTransformation
            )
            
            # Обновляем кэш и отображение
            self.image_cache[self.current_image_index] = transformed
            self.apply_display_mode(transformed)
            
            self.status_bar.showMessage("Изображение повернуто на 90° влево")
    def rotate_right(self):
        """Повернуть изображение на 90° вправо"""
        if self.current_image_index in self.image_cache:
            pixmap = self.image_cache[self.current_image_index]
            
            transform = QTransform()
            transform.rotate(90)  # +90 градусов
            
            transformed = pixmap.transformed(
                transform,
                Qt.SmoothTransformation
            )
            
            self.image_cache[self.current_image_index] = transformed
            self.apply_display_mode(transformed)
            
            self.status_bar.showMessage("Изображение повернуто на 90° вправо")

    # ========== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ==========

    def show_about(self):
        """Показать информацию о программе"""
        about_text = """
        <h2>Просмотрщик изображений</h2>
        <p><b>Лабораторная работа №5</b></p>
        <p>Программа для просмотра датасета изображений из лабораторной работы №2.</p>
        
        <h3>Функции:</h3>
        <ul>
            <li>Загрузка папки с изображениями</li>
            <li>Загрузка CSV аннотации</li>
            <li>Навигация по изображениям</li>
            <li>Различные режимы отображения</li>
            <li>Масштабирование и поворот</li>
            <li>Подробная информация об изображениях</li>
        </ul>
        
        <p><b>Используемые технологии:</b></p>
        <ul>
            <li>PyQt5 для графического интерфейса</li>
            <li>QPixmap для работы с изображениями</li>
            <li>Итератор из лабораторной работы №2</li>
        </ul>
        
        <p>© 2024 Учебный проект</p>
        """

        QMessageBox.about(self, "О программе", about_text)

    # ========== СОБЫТИЯ ==========

    def resizeEvent(self, event):
        """Обработка изменения размера окна"""
        super().resizeEvent(event)
        # Обновляем изображение при изменении размера окна
        if self.combo_display_mode.currentIndex() == 1:  # Режим "Подогнать к окну"
            self.update_image_display()

    def closeEvent(self, event):
        """Обработка закрытия окна"""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите выйти?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
