"""
import sys

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLineEdit, QPushButton, QTextEdit, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal
from yowsup.layers import YowLayerEvent
from yowsup.layers.network import YowNetworkLayer
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity
from yowsup.layers.axolotl import YowAxolotlLayer
from yowsup.stacks import YowStackBuilder
from yowsup.common import YowConstants
from yowsup.layers import YowLayerEvent
from yowsup.profile import YowProfile

class WhatsAppThread(QThread):
    messageReceived = pyqtSignal(str)
    connectionStatus = pyqtSignal(bool)
    
    def __init__(self, phone, password):
        super().__init__()
        self.phone = phone
        self.password = password
        self.stack = None

    def run(self):
        profile = YowProfile(self.phone, self.password)
        stackBuilder = YowStackBuilder()
        self.stack = stackBuilder\
            .pushDefaultLayers(True)\
            .build()
        self.stack.setProfile(profile)
        self.stack.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT))
        try:
            self.stack.loop(timeout=0.5, discrete=0.5)
            self.connectionStatus.emit(True)
        except Exception as e:
            print(f"Error en WhatsApp stack: {str(e)}")
            self.connectionStatus.emit(False)

    def send_message(self, number, message):
        if self.stack:
            entity = TextMessageProtocolEntity(message, to=f"{number}@s.whatsapp.net")
            self.stack.send(entity)

class WhatsAppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WhatsApp Sender")
        self.setGeometry(100, 100, 400, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Tu número de teléfono (con código de país)")
        layout.addWidget(self.phone_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Tu contraseña")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        self.connect_button = QPushButton("Conectar")
        self.connect_button.clicked.connect(self.connect_whatsapp)
        layout.addWidget(self.connect_button)

        self.number_input = QLineEdit()
        self.number_input.setPlaceholderText("Número de destino (con código de país)")
        layout.addWidget(self.number_input)

        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Escribe tu mensaje aquí")
        layout.addWidget(self.message_input)

        self.send_button = QPushButton("Enviar")
        self.send_button.clicked.connect(self.send_message)
        layout.addWidget(self.send_button)

        central_widget.setLayout(layout)

        self.whatsapp_thread = None

    def connect_whatsapp(self):
        phone = self.phone_input.text()
        password = self.password_input.text()
        self.whatsapp_thread = WhatsAppThread(phone, password)
        self.whatsapp_thread.connectionStatus.connect(self.on_connection_status)
        self.whatsapp_thread.start()

    def on_connection_status(self, status):
        if status:
            QMessageBox.information(self, "Conexión", "Conectado a WhatsApp exitosamente")
        else:
            QMessageBox.warning(self, "Error de conexión", "No se pudo conectar a WhatsApp")

    def send_message(self):
        if self.whatsapp_thread:
            number = self.number_input.text()
            message = self.message_input.toPlainText()
            self.whatsapp_thread.send_message(number, message)
            QMessageBox.information(self, "Mensaje enviado", f"Mensaje enviado a {number}")
        else:
            QMessageBox.warning(self, "Error", "No conectado a WhatsApp")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WhatsAppWindow()
    window.show()
    sys.exit(app.exec())
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLineEdit, QPushButton, QTextEdit, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal
#from whatsapp import Client
import whatsapp

class WhatsAppThread(QThread):
    connectionStatus = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        self.whatsapp = None

    def run(self):
        try:
            self.whatsapp = Client()
            self.connectionStatus.emit(True)
        except Exception as e:
            print(f"Error al iniciar WhatsApp: {str(e)}")
            self.connectionStatus.emit(False)

    def send_message(self, number, message):
        if self.whatsapp:
            try:
                self.whatsapp.send_message(number, message)
                return True
            except Exception as e:
                print(f"Error al enviar mensaje: {str(e)}")
                return False
        return False

class WhatsAppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WhatsApp Sender")
        self.setGeometry(100, 100, 400, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        self.connect_button = QPushButton("Iniciar WhatsApp")
        self.connect_button.clicked.connect(self.connect_whatsapp)
        layout.addWidget(self.connect_button)

        self.number_input = QLineEdit()
        self.number_input.setPlaceholderText("Número de destino (con código de país)")
        layout.addWidget(self.number_input)

        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Escribe tu mensaje aquí")
        layout.addWidget(self.message_input)

        self.send_button = QPushButton("Enviar")
        self.send_button.clicked.connect(self.send_message)
        layout.addWidget(self.send_button)

        central_widget.setLayout(layout)

        self.whatsapp_thread = None

    def connect_whatsapp(self):
        self.whatsapp_thread = WhatsAppThread()
        self.whatsapp_thread.connectionStatus.connect(self.on_connection_status)
        self.whatsapp_thread.start()

    def on_connection_status(self, status):
        if status:
            QMessageBox.information(self, "Conexión", "WhatsApp iniciado exitosamente")
        else:
            QMessageBox.warning(self, "Error de conexión", "No se pudo iniciar WhatsApp")

    def send_message(self):
        if self.whatsapp_thread and self.whatsapp_thread.whatsapp:
            number = self.number_input.text()
            message = self.message_input.toPlainText()
            if self.whatsapp_thread.send_message(number, message):
                QMessageBox.information(self, "Mensaje enviado", f"Mensaje enviado a {number}")
            else:
                QMessageBox.warning(self, "Error", "No se pudo enviar el mensaje")
        else:
            QMessageBox.warning(self, "Error", "WhatsApp no está iniciado")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WhatsAppWindow()
    window.show()
    sys.exit(app.exec())