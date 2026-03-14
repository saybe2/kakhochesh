import os
import sys

import requests
from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QKeyEvent, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MapApp(QMainWindow):
    MIN_ZOOM = 1
    MAX_ZOOM = 18
    MIN_LAT = -85.0
    MAX_LAT = 85.0
    MIN_LON = -180.0
    MAX_LON = 180.0

    def __init__(self):
        super().__init__()
        self.api_key = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"
        self.map_file = "map.png"
        self.dark_theme = False
        self.init_ui()

        self.lat_input.setText("55.7558")
        self.lon_input.setText("37.6173")
        self.zoom_input.setText("12")
        self.show_map()

    def init_ui(self):
        self.setWindowTitle("Карты")
        self.setGeometry(100, 100, 800, 650)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.addLayout(self.create_control_panel())

        self.map_label = QLabel()
        self.map_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.map_label.setMinimumSize(600, 450)
        self.map_label.setStyleSheet("border: 1px solid gray;")
        main_layout.addWidget(self.map_label)

        self.status_bar = self.statusBar()

        self.lat_input.installEventFilter(self)
        self.lon_input.installEventFilter(self)
        self.zoom_input.installEventFilter(self)

    def create_control_panel(self):
        control_layout = QHBoxLayout()

        lat_label = QLabel("Широта:")
        self.lat_input = QLineEdit()
        self.lat_input.setPlaceholderText("55.7558")
        control_layout.addWidget(lat_label)
        control_layout.addWidget(self.lat_input)

        lon_label = QLabel("Долгота:")
        self.lon_input = QLineEdit()
        self.lon_input.setPlaceholderText("37.6173")
        control_layout.addWidget(lon_label)
        control_layout.addWidget(self.lon_input)

        zoom_label = QLabel("Масштаб:")
        self.zoom_input = QLineEdit()
        self.zoom_input.setPlaceholderText("12")
        control_layout.addWidget(zoom_label)
        control_layout.addWidget(self.zoom_input)

        self.btn_show = QPushButton("Показать карту")
        self.btn_show.clicked.connect(self.show_map)
        control_layout.addWidget(self.btn_show)

        self.btn_theme = QPushButton("Тема: светлая")
        self.btn_theme.clicked.connect(self.toggle_theme)
        control_layout.addWidget(self.btn_theme)

        return control_layout

    @staticmethod
    def clamp(value, low, high):
        return max(low, min(high, value))

    def get_span(self, zoom):
        return 0.002 * (self.MAX_ZOOM - zoom + 1)

    def validate_inputs(self):
        try:
            lat_text = self.lat_input.text().strip()
            lon_text = self.lon_input.text().strip()

            if not lat_text:
                raise ValueError("Введите широту")
            if not lon_text:
                raise ValueError("Введите долготу")

            lat = float(lat_text.replace(",", "."))
            lon = float(lon_text.replace(",", "."))

            lat = self.clamp(lat, self.MIN_LAT, self.MAX_LAT)
            lon = self.clamp(lon, self.MIN_LON, self.MAX_LON)

            zoom_text = self.zoom_input.text().strip()
            zoom = int(zoom_text) if zoom_text else 12
            zoom = int(self.clamp(zoom, self.MIN_ZOOM, self.MAX_ZOOM))

            return lat, lon, zoom
        except ValueError as exc:
            QMessageBox.warning(self, "Ошибка", f"Некорректные данные:\n{exc}")
            return None

    def get_map_image(self, lat, lon, zoom):
        try:
            span_value = self.get_span(zoom)
            theme = "dark" if self.dark_theme else "light"
            request_url = (
                "https://static-maps.yandex.ru/v1?"
                f"ll={lon},{lat}&spn={span_value},{span_value}"
                f"&theme={theme}&apikey={self.api_key}"
            )
            response = requests.get(request_url, timeout=10)
            response.raise_for_status()
            with open(self.map_file, "wb") as file:
                file.write(response.content)
            return True
        except requests.exceptions.RequestException as exc:
            QMessageBox.critical(self, "Ошибка сети", f"Не удалось получить карту:\n{exc}")
            return False

    def show_map(self):
        result = self.validate_inputs()
        if not result:
            return

        lat, lon, zoom = result
        self.lat_input.setText(f"{lat:.6f}")
        self.lon_input.setText(f"{lon:.6f}")
        self.zoom_input.setText(str(zoom))

        if not self.get_map_image(lat, lon, zoom):
            return

        pixmap = QPixmap(self.map_file)
        scaled_pixmap = pixmap.scaled(
            self.map_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.map_label.setPixmap(scaled_pixmap)

        theme_text = "тёмная" if self.dark_theme else "светлая"
        self.status_bar.showMessage(
            f"Координаты: {lat:.4f}, {lon:.4f} | Масштаб: {zoom} | Тема: {theme_text}"
        )

    def toggle_theme(self):
        self.dark_theme = not self.dark_theme
        self.btn_theme.setText("Тема: тёмная" if self.dark_theme else "Тема: светлая")
        self.show_map()

    def change_zoom(self, delta):
        result = self.validate_inputs()
        if not result:
            return

        _, _, zoom = result
        new_zoom = int(self.clamp(zoom + delta, self.MIN_ZOOM, self.MAX_ZOOM))
        if new_zoom == zoom:
            return

        self.zoom_input.setText(str(new_zoom))
        self.show_map()

    def move_center(self, dx, dy):
        result = self.validate_inputs()
        if not result:
            return

        lat, lon, zoom = result
        step = self.get_span(zoom) * 0.5

        new_lon = self.clamp(lon + dx * step, self.MIN_LON, self.MAX_LON)
        new_lat = self.clamp(lat + dy * step, self.MIN_LAT, self.MAX_LAT)

        self.lat_input.setText(f"{new_lat:.6f}")
        self.lon_input.setText(f"{new_lon:.6f}")
        self.show_map()

    def handle_hotkey(self, key):
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.show_map()
            return True
        if key == Qt.Key.Key_PageUp:
            self.change_zoom(1)
            return True
        if key == Qt.Key.Key_PageDown:
            self.change_zoom(-1)
            return True
        if key == Qt.Key.Key_Left:
            self.move_center(-1, 0)
            return True
        if key == Qt.Key.Key_Right:
            self.move_center(1, 0)
            return True
        if key == Qt.Key.Key_Up:
            self.move_center(0, 1)
            return True
        if key == Qt.Key.Key_Down:
            self.move_center(0, -1)
            return True
        if key == Qt.Key.Key_Escape:
            self.close()
            return True
        if key == Qt.Key.Key_T:
            self.toggle_theme()
            return True
        return False

    def eventFilter(self, watched, event):
        if (
            watched in (self.lat_input, self.lon_input, self.zoom_input)
            and event.type() == QEvent.Type.KeyPress
            and self.handle_hotkey(event.key())
        ):
            return True
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event: QKeyEvent):
        if not self.handle_hotkey(event.key()):
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "map_label") and self.map_label.pixmap() is not None:
            pixmap = QPixmap(self.map_file)
            scaled_pixmap = pixmap.scaled(
                self.map_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.map_label.setPixmap(scaled_pixmap)

    def closeEvent(self, event):
        if os.path.exists(self.map_file):
            try:
                os.remove(self.map_file)
            except OSError:
                pass


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MapApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
