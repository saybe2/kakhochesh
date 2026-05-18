import math
import os
import sys

import requests
from PyQt6.QtCore import QEvent, QTimer, Qt, QPoint
from PyQt6.QtGui import QKeyEvent, QPixmap, QMouseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
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
    MAX_ZOOM = 20
    MIN_LAT = -85.0
    MAX_LAT = 85.0
    MIN_LON = -180.0
    MAX_LON = 180.0

    def __init__(self):
        super().__init__()
        self.static_api_key = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"
        self.geocoder_api_key = "8013b162-6b42-4997-9691-77b7074026e0"
        self.map_file = "map.png"
        self.dark_theme = False
        self.search_point = None
        self.found_address = None
        self.include_postal_code = False
        self.last_search_query = None
        self.last_search_coords = None
        self.current_center_lat = 55.7558
        self.current_center_lon = 37.6173
        self.current_zoom = 16
        self.orig_map_width = 650
        self.orig_map_height = 450

        self.init_ui()

        self.lat_input.setText("55.7558")
        self.lon_input.setText("37.6173")
        self.zoom_input.setText("16")
        QTimer.singleShot(0, self.show_map)

    def init_ui(self):
        self.setWindowTitle("Карты")
        self.setGeometry(100, 100, 900, 750)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.addLayout(self.create_control_panel())
        main_layout.addLayout(self.create_search_panel())

        self.map_label = QLabel()
        self.map_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.map_label.setMinimumSize(700, 500)
        self.map_label.setStyleSheet("border: 1px solid gray;")
        self.map_label.setScaledContents(False)
        # Включаем возможность получения событий мыши
        self.map_label.setMouseTracking(True)
        main_layout.addWidget(self.map_label)

        address_layout = QHBoxLayout()
        address_label = QLabel("Адрес:")
        self.address_display = QLineEdit()
        self.address_display.setReadOnly(True)
        address_layout.addWidget(address_label)
        address_layout.addWidget(self.address_display)
        main_layout.addLayout(address_layout)

        self.status_bar = self.statusBar()

        self.lat_input.installEventFilter(self)
        self.lon_input.installEventFilter(self)
        self.zoom_input.installEventFilter(self)
        self.search_input.installEventFilter(self)

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
        self.zoom_input.setPlaceholderText("16")
        control_layout.addWidget(zoom_label)
        control_layout.addWidget(self.zoom_input)

        self.btn_show = QPushButton("Показать карту")
        self.btn_show.clicked.connect(self.show_map)
        control_layout.addWidget(self.btn_show)

        self.btn_theme = QPushButton("Тема: светлая")
        self.btn_theme.clicked.connect(self.toggle_theme)
        control_layout.addWidget(self.btn_theme)

        return control_layout

    def create_search_panel(self):
        search_layout = QHBoxLayout()

        search_label = QLabel("Поиск:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите адрес или объект")
        self.search_input.returnPressed.connect(self.search_object)

        self.search_button = QPushButton("Искать")
        self.search_button.clicked.connect(self.search_object)

        self.reset_button = QPushButton("Сброс")
        self.reset_button.clicked.connect(self.reset_search)

        self.postal_checkbox = QCheckBox("Показывать почтовый индекс")
        self.postal_checkbox.stateChanged.connect(self.on_postal_checkbox_changed)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.reset_button)
        search_layout.addWidget(self.postal_checkbox)

        return search_layout

    def mousePressEvent(self, event: QMouseEvent):
        """Обработка клика мыши по карте"""
        # Проверяем, что клик был по метке карты
        if event.button() == Qt.MouseButton.LeftButton:
            # Получаем позицию клика относительно map_label
            map_label_pos = self.map_label.mapFromGlobal(event.globalPosition().toPoint())
            
            # Проверяем, что клик в пределах map_label
            if (0 <= map_label_pos.x() <= self.map_label.width() and 
                0 <= map_label_pos.y() <= self.map_label.height() and
                self.map_label.pixmap() is not None):
                
                # Получаем размеры и позицию пиксмапа внутри map_label
                pixmap = self.map_label.pixmap()
                pixmap_rect = pixmap.rect()
                
                # Вычисляем отступы для центрированного изображения
                x_offset = (self.map_label.width() - pixmap.width()) // 2
                y_offset = (self.map_label.height() - pixmap.height()) // 2
                
                # Корректируем координаты клика относительно пиксмапа
                click_x = map_label_pos.x() - x_offset
                click_y = map_label_pos.y() - y_offset
                
                # Проверяем, что клик в пределах пиксмапа
                if 0 <= click_x <= pixmap.width() and 0 <= click_y <= pixmap.height():
                    # Конвертируем координаты клика в географические координаты
                    lon, lat = self.pixel_to_geo(click_x, click_y, pixmap.width(), pixmap.height())
                    
                    if lon is not None and lat is not None:
                        # Выполняем поиск объекта по координатам
                        self.search_by_coordinates(lat, lon)

    def pixel_to_geo(self, pixel_x, pixel_y, map_width, map_height):
        """Конвертирует координаты пикселя в географические координаты (Web Mercator)"""
        try:
            lat = self.current_center_lat
            lon = self.current_center_lon
            zoom = self.current_zoom

            # Размер всего мира в пикселях при данном зуме
            world_size = 256 * (2 ** zoom)

            # Конвертируем центр карты в пиксельные координаты мира
            center_x = (lon + 180.0) / 360.0 * world_size

            lat_rad = math.radians(lat)
            center_y = (1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * world_size

            # Пересчитываем координаты клика из масштабированного изображения
            # в оригинальные пиксели API (1 оригинальный пиксель = 1 мировой пиксель)
            scale_x = self.orig_map_width / map_width
            scale_y = self.orig_map_height / map_height
            orig_x = pixel_x * scale_x
            orig_y = pixel_y * scale_y

            # Пиксельные координаты клика в мировой системе
            click_world_x = center_x + (orig_x - self.orig_map_width / 2.0)
            click_world_y = center_y + (orig_y - self.orig_map_height / 2.0)

            # Конвертируем обратно в географические координаты
            click_lon = click_world_x / world_size * 360.0 - 180.0

            n = 1.0 - 2.0 * click_world_y / world_size
            click_lat = math.degrees(math.atan(math.sinh(math.pi * n)))

            # Ограничиваем координаты допустимыми значениями
            click_lat = self.clamp(click_lat, self.MIN_LAT, self.MAX_LAT)
            click_lon = self.clamp(click_lon, self.MIN_LON, self.MAX_LON)

            return click_lon, click_lat
        except Exception as e:
            self.status_bar.showMessage(f"Ошибка конвертации координат: {str(e)}")
            return None, None

    def search_by_coordinates(self, lat, lon):
        """Поиск объекта по координатам (обратное геокодирование)"""
        try:
            # Сначала получаем адрес по координатам
            address = self.get_address_by_coords(lat, lon)
            
            # Добавляем почтовый индекс, если нужно
            if self.postal_checkbox.isChecked():
                postindex = self.get_postcode_osm(lat, lon)
                if postindex:
                    address += f" (Индекс: {postindex})"
                else:
                    address += " (Индекс: не найден)"
            
            # Сохраняем результаты поиска
            self.search_point = (lon, lat)
            self.found_address = address
            self.last_search_coords = (lon, lat)
            self.last_search_query = None  # Сбрасываем текстовый запрос
            
            # Обновляем интерфейс
            self.address_display.setText(address)
            self.lat_input.setText(f"{lat:.6f}")
            self.lon_input.setText(f"{lon:.6f}")
            self.search_input.clear()  # Очищаем поле поиска
            
            # Показываем карту с новой меткой
            self.show_map()
            
            self.status_bar.showMessage(f"Найден объект по координатам: {address[:50]}...")
            
        except requests.exceptions.RequestException as exc:
            QMessageBox.critical(self, "Ошибка сети", f"Ошибка поиска по координатам:\n{exc}")
        except Exception as exc:
            QMessageBox.critical(self, "Ошибка", f"Не удалось найти объект:\n{exc}")

    def on_postal_checkbox_changed(self, state):
        """Обработчик изменения состояния чекбокса почтового индекса"""
        if self.search_point is not None and self.last_search_coords is not None:
            self.update_address_for_coords(self.last_search_coords[0], self.last_search_coords[1])
        elif self.found_address is not None and self.search_point is not None:
            lon, lat = self.search_point
            self.update_address_for_coords(lon, lat)

    def update_address_for_coords(self, lon, lat):
        """Обновляет адрес для заданных координат с учетом состояния чекбокса"""
        try:
            address = self.get_address_by_coords(lat, lon)
            
            if self.postal_checkbox.isChecked():
                postindex = self.get_postcode_osm(lat, lon)
                if postindex:
                    address += f" (Индекс: {postindex})"
                else:
                    address += " (Индекс: не найден)"
            
            self.found_address = address
            self.address_display.setText(address)
            self.status_bar.showMessage(f"Адрес обновлен: {address[:50]}...")
            
        except Exception as e:
            self.status_bar.showMessage(f"Ошибка обновления адреса: {str(e)}")

    def get_address_by_coords(self, lat, lon):
        """Получает адрес по координатам через геокодер"""
        geocoder_url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            "apikey": self.geocoder_api_key,
            "geocode": f"{lon},{lat}",
            "format": "json",
        }
        
        response = requests.get(geocoder_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        members = data["response"]["GeoObjectCollection"]["featureMember"]
        if members:
            geo_obj = members[0]["GeoObject"]
            address = geo_obj["metaDataProperty"]["GeocoderMetaData"]["text"]
            return address
        return "Адрес не найден"

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
            zoom = int(zoom_text) if zoom_text else 16
            zoom = int(self.clamp(zoom, self.MIN_ZOOM, self.MAX_ZOOM))

            return lat, lon, zoom
        except ValueError as exc:
            QMessageBox.warning(self, "Ошибка", f"Некорректные данные:\n{exc}")
            return None

    def get_map_image(self, lat, lon, zoom):
        try:
            theme = "dark" if self.dark_theme else "light"
            request_url = (
                "https://static-maps.yandex.ru/v1?"
                f"ll={lon},{lat}&z={zoom}"
                f"&theme={theme}&apikey={self.static_api_key}"
            )

            if self.search_point is not None:
                point_lon, point_lat = self.search_point
                request_url += f"&pt={point_lon},{point_lat},pm2rdm"

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
        # Сохраняем текущие параметры для конвертации координат
        self.current_center_lat = lat
        self.current_center_lon = lon
        self.current_zoom = zoom
        
        self.lat_input.setText(f"{lat:.6f}")
        self.lon_input.setText(f"{lon:.6f}")
        self.zoom_input.setText(str(zoom))

        if not self.get_map_image(lat, lon, zoom):
            return

        pixmap = QPixmap(self.map_file)
        self.orig_map_width = pixmap.width()
        self.orig_map_height = pixmap.height()
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

    def find_object_center_and_address(self, query):
        geocoder_url = "https://geocode-maps.yandex.ru/1.x/"
        params = {
            "apikey": self.geocoder_api_key,
            "geocode": query,
            "format": "json",
        }

        response = requests.get(geocoder_url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        members = data["response"]["GeoObjectCollection"]["featureMember"]
        if not members:
            return None, None

        geo_obj = members[0]["GeoObject"]
        address = geo_obj["metaDataProperty"]["GeocoderMetaData"]["text"]

        point_lon, point_lat = map(float, geo_obj["Point"]["pos"].split())
        
        self.last_search_coords = (point_lon, point_lat)
        
        if self.postal_checkbox.isChecked():
            postindex = self.get_postcode_osm(point_lat, point_lon)
            if postindex:
                address += f" (Индекс: {postindex})"
            else:
                address += " (Индекс: не найден)"

        return (point_lon, point_lat), address

    def search_object(self):
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.information(self, "Поиск", "Введите запрос для поиска.")
            return

        try:
            self.last_search_query = query
            center, address = self.find_object_center_and_address(query)
            if center is None:
                QMessageBox.information(self, "Поиск", "Объект не найден.")
                return

            lon, lat = center
            self.search_point = (lon, lat)
            self.found_address = address
            self.address_display.setText(address)
            self.lon_input.setText(f"{lon:.6f}")
            self.lat_input.setText(f"{lat:.6f}")
            self.show_map()
        except requests.exceptions.RequestException as exc:
            QMessageBox.critical(self, "Ошибка сети", f"Ошибка поиска:\n{exc}")

    def reset_search(self):
        self.search_point = None
        self.found_address = None
        self.last_search_query = None
        self.last_search_coords = None
        self.search_input.clear()
        self.address_display.clear()
        self.postal_checkbox.setChecked(False)
        self.show_map()

    def toggle_theme(self):
        self.dark_theme = not self.dark_theme
        theme_label = "Тема: тёмная" if self.dark_theme else "Тема: светлая"
        self.btn_theme.setText(theme_label)
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

        self.lon_input.setText(f"{new_lon:.6f}")
        self.lat_input.setText(f"{new_lat:.6f}")
        self.show_map()

    def handle_hotkey(self, key):
        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.search_input.hasFocus() and self.search_input.text().strip():
                self.search_object()
            else:
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
        return False

    def eventFilter(self, watched, event):
        if (
            watched in (self.lat_input, self.lon_input, self.zoom_input, self.search_input)
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
            if not pixmap.isNull():
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

    def get_postcode_osm(self, lat, lon):
        """Получает почтовый индекс через OSM Nominatim"""
        geocoder_url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "format": "json",
            "countrycodes": "ru",
            "lat": lat,
            "lon": lon,
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.2; Win64; x64)\
            AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.7292.124 Safari/537.36"
        }

        try:
            response = requests.get(geocoder_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            postcode = data["address"].get("postcode")
            return postcode
        except:
            return None


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MapApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
