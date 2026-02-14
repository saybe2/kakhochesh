import os
import sys
import requests
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, \
    QPushButton, QMessageBox
from PyQt6.QtGui import QKeyEvent, QPixmap
from PyQt6.QtCore import Qt


class MapApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_key = "f3a0fe3a-b07e-4840-a1da-06f18b2ddf13"
        self.map_file = "map.png"
        self.initUI()
        
        self.lat_input.setText("55.7558")
        self.lon_input.setText("37.6173")
        self.zoom_input.setText("12")
        self.show_map()

    def initUI(self):
        self.setWindowTitle('Карты')
        self.setGeometry(100, 100, 800, 650)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        control_panel = self.create_control_panel()
        main_layout.addLayout(control_panel)

        self.map_label = QLabel()
        self.map_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.map_label.setMinimumSize(600, 450)
        self.map_label.setStyleSheet("border: 1px solid gray;")
        main_layout.addWidget(self.map_label)

        self.status_bar = self.statusBar()

    def create_control_panel(self):
        control_layout = QHBoxLayout()

        lat_label = QLabel('Широта:')
        self.lat_input = QLineEdit()
        self.lat_input.setPlaceholderText('55.7558')
        control_layout.addWidget(lat_label)
        control_layout.addWidget(self.lat_input)

        lon_label = QLabel('Долгота:')
        self.lon_input = QLineEdit()
        self.lon_input.setPlaceholderText('37.6173')
        control_layout.addWidget(lon_label)
        control_layout.addWidget(self.lon_input)

        zoom_label = QLabel('Масштаб:')
        self.zoom_input = QLineEdit()
        self.zoom_input.setPlaceholderText('12')
        control_layout.addWidget(zoom_label)
        control_layout.addWidget(self.zoom_input)

        self.btn_show = QPushButton('Показать карту')
        self.btn_show.clicked.connect(self.show_map)
        control_layout.addWidget(self.btn_show)

        return control_layout

    def validate_inputs(self):
        try:
            lat_text = self.lat_input.text().strip()
            lon_text = self.lon_input.text().strip()
            
            if not lat_text:
                raise ValueError("Введите широту")
            if not lon_text:
                raise ValueError("Введите долготу")
            
            lat = float(lat_text.replace(',', '.'))
            lon = float(lon_text.replace(',', '.'))

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

    def get_map_image(self, lat, lon, zoom):
        try:
            server_address = 'https://static-maps.yandex.ru/v1?'
            
            spn_value = 0.002 * (18 - zoom + 1)
            
            map_request = f"{server_address}ll={lon},{lat}&spn={spn_value},{spn_value}&apikey={self.api_key}"
            
            response = requests.get(map_request)
            
            with open(self.map_file, "wb") as file:
                file.write(response.content)
                
            return True
            
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, 'Ошибка сети', f'Не удалось подключиться к серверу:\n{str(e)}')
            return False
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Не удалось получить карту:\n{str(e)}')
            return False

    def show_map(self):
        result = self.validate_inputs()
        if result:
            lat, lon, zoom = result
            
            if self.get_map_image(lat, lon, zoom):
                pixmap = QPixmap(self.map_file)
                
                scaled_pixmap = pixmap.scaled(
                    self.map_label.size(), 
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                self.map_label.setPixmap(scaled_pixmap)
                self.status_bar.showMessage(f'Координаты: {lat:.4f}, {lon:.4f} | Масштаб: {zoom}')

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.show_map()
        elif event.key() == Qt.Key.Key_Escape:
            self.close()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'map_label') and self.map_label.pixmap() is not None:
            pixmap = QPixmap(self.map_file)
            scaled_pixmap = pixmap.scaled(
                self.map_label.size(), 
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.map_label.setPixmap(scaled_pixmap)

    def closeEvent(self, event):
        if os.path.exists(self.map_file):
            try:
                os.remove(self.map_file)
            except:
                pass


def main():
    app = QApplication(sys.argv)
    
    app.setStyle('Fusion')
    
    window = MapApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
