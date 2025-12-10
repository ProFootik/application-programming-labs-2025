import sys
import os

from PyQt5.QtWidgets import QApplication
from main_window import ImageViewer


# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Основная функция запуска приложения"""

    # Создание приложения
    app = QApplication(sys.argv)
    app.setApplicationName("Image Viewer - Lab 5")
    app.setOrganizationName("Samara University")

    # Создание и отображение главного окна
    window = ImageViewer()
    window.show()

    # Запуск главного цикла приложения
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
