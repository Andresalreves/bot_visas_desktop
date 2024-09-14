from common_functions import get_mac_address , url
from gui.myapp import MyApp
from PyQt6 import uic
import requests
import re

mac = get_mac_address()

class Activation():
    def __init__(self):
        self.Activation = uic.loadUi('gui/activation.ui')
        self.Activation.show()

        # Conectar el botón con la función de envío
        self.Activation.ButtonActivation.clicked.connect(self.enviar_token)
        #self.key = "784G1lgso7qRQlCkT4QhsJIs0zM2UDEJUlivV3ebN5Eh0vOoXc"
        #self.cipher_suite = Fernet(self.key)

    def enviar_token(self):
        # Obtener el token del input
        patron = re.compile(r"^[A-Za-z0-9]{28}$")
        token = self.Activation.InputActivation.text()
        # Encriptar el token
        #token_encriptado = self.cipher_suite.encrypt(token.encode())
        if patron.match(token):
            # Enviar la petición a la API
            try:
                response = requests.post(url+'validate_token', json={'token':token,'mac':mac})
                
                # Verificar la respuest
                if response.status_code == 200:
                    data = response.json()
                    message = data.get("message")
                    self.Activation.AlertActivation.setText(message)
                    if data.get("activation") == 1:
                        self.main = MyApp()
                        self.Activation.hide()
                else:
                    self.Activation.AlertActivation.setText("Error en la petición")
            except requests.RequestException:
                self.Activation.AlertActivation.setText("Error de conexión")
        else:
            self.Activation.AlertActivation.setText("Formato de Token no valido")