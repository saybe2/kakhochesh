import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, \
    QPushButton, QMessageBox, QTextBrowser
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt
import webbrowser


class MapApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Карта по координатам')
        self.setGeometry(100, 100, 1000, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        control_panel = self.create_control_panel()
        main_layout.addLayout(control_panel)

        self.map_info = QTextBrowser()
        self.map_info.setOpenExternalLinks(True)
        main_layout.addWidget(self.map_info)

        self.status_bar = self.statusBar()

        self.default_coordinates()

    def create_control_panel(self):
        control_layout = QHBoxLayout()

        lat_label = QLabel('Широта:')
        self.lat_input = QLineEdit()
        self.lat_input.setPlaceholderText('Например: 55.7558')
        control_layout.addWidget(lat_label)
        control_layout.addWidget(self.lat_input)

        lon_label = QLabel('Долгота:')
        self.lon_input = QLineEdit()
        self.lon_input.setPlaceholderText('Например: 37.6173')
        control_layout.addWidget(lon_label)
        control_layout.addWidget(self.lon_input)

        zoom_label = QLabel('Масштаб:')
        self.zoom_input = QLineEdit()
        self.zoom_input.setPlaceholderText('От 1 до 18')
        control_layout.addWidget(zoom_label)
        control_layout.addWidget(self.zoom_input)

        self.btn_show = QPushButton('Показать карту')
        self.btn_show.clicked.connect(self.show_map)
        control_layout.addWidget(self.btn_show)

        self.btn_browser = QPushButton('Открыть в браузере')
        self.btn_browser.clicked.connect(self.open_in_browser)
        control_layout.addWidget(self.btn_browser)

        self.btn_default = QPushButton('По умолчанию')
        self.btn_default.clicked.connect(self.default_coordinates)
        control_layout.addWidget(self.btn_default)

        return control_layout

    def default_coordinates(self):
        self.lat_input.setText('55.7558')
        self.lon_input.setText('37.6173')
        self.zoom_input.setText('12')
        self.show_map()

    def validate_inputs(self):
        try:
            lat = float(self.lat_input.text().strip())
            lon = float(self.lon_input.text().strip())

            if not (-90 <= lat <= 90):
                raise ValueError("Широта должна быть от -90 до 90 градусов")

            if not (-180 <= lon <= 180):
                raise ValueError("Долгота должна быть от -180 до 180 градусов")

            zoom_text = self.zoom_input.text().strip()
            if zoom_text:
                zoom = int(zoom_text)
                if not (1 <= zoom <= 18):
                    raise ValueError("Масштаб должен быть от 1 до 18")
            else:
                zoom = 12

            return lat, lon, zoom

        except ValueError as e:
            QMessageBox.warning(self, 'Ошибка', f'Некорректные данные:\n{str(e)}')
            return None

    def generate_map_url(self, lat, lon, zoom):
        return f"https://www.openstreetmap.org/#map={zoom}/{lat}/{lon}"

    def generate_static_map(self, lat, lon, zoom):
        size = "800x600"
        markers = f"&markers={lat},{lon}"
        url = f"https://staticmap.openstreetmap.de/staticmap.php?center={lat},{lon}&zoom={zoom}&size={size}{markers}"
        return url

    def show_map(self):
        result = self.validate_inputs()
        if result:
            lat, lon, zoom = result

            try:
                map_url = self.generate_map_url(lat, lon, zoom)
                static_map_url = self.generate_static_map(lat, lon, zoom)

                html_content = f"""
                <html>
                <head>
                    <meta charset="UTF-8">
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        .map-container {{ text-align: center; margin: 20px 0; }}
                        .map-image {{ max-width: 100%; border: 1px solid #ccc; box-shadow: 2px 2px 10px rgba(0,0,0,0.1); }}
                        .info {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                        .links {{ margin-top: 20px; }}
                        a {{ color: #0066cc; text-decoration: none; font-weight: bold; }}
                        a:hover {{ text-decoration: underline; }}
                    </style>
                </head>
                <body>
                    <div class="info">
                        <h2>Координаты карты</h2>
                        <p><strong>Широта:</strong> {lat:.6f}</p>
                        <p><strong>Долгота:</strong> {lon:.6f}</p>
                        <p><strong>Масштаб:</strong> {zoom}</p>
                    </div>

                    <div class="map-container">
                        <h3>Статическое изображение карты</h3>
                        <img src="{static_map_url}" alt="Карта" class="map-image">
                        <p><small>Изображение предоставлено OpenStreetMap</small></p>
                    </div>

                    <div class="links">
                        <h3>Ссылки на карту:</h3>
                        <p><a href="https://yandex.ru/maps/?pt={lon},{lat}&z={zoom}&l=map" target="_blank">Открыть в Яндекс.Картах</a></p>
                    </div>

                </body>
                </html>
                """

                self.map_info.setHtml(html_content)
                self.status_bar.showMessage(f'Координаты: {lat:.4f}, {lon:.4f} | Масштаб: {zoom}')

            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Не удалось создать карту:\n{str(e)}')

    def open_in_browser(self):
        result = self.validate_inputs()
        if result:
            lat, lon, zoom = result
            map_url = self.generate_map_url(lat, lon, zoom)
            webbrowser.open(map_url)


    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            self.show_map()


def main():
    app = QApplication(sys.argv)

    window = MapApp()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
