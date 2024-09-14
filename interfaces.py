from PyQt6.QtWidgets import QApplication
from gui.AgregarCuentas import AgregarCuentas
from gui.Configuracion import Configuracion
from gui.activation import Activation
from gui.myapp import MyApp

class TuVisa():
    def __init__(self):
        self.app = QApplication([])
        self.TuVisa = Activation()
        self.app.exec()

class Panel():
    def __init__(self):
        self.ventana = QApplication([])
        self.Panel = MyApp() 
        self.ventana.exec()

class ModalAgregarCuentas():
    def __init__(self):
        self.modalAgregarCuentas = QApplication([])
        self.modalAgregarCuentas = AgregarCuentas() 
        self.modalAgregarCuentas.exec()

class ModalConfiguracion():
    def __init__(self):
        self.modalConfiguracion = QApplication([])
        self.modalConfiguracion = Configuracion() 
        self.modalConfiguracion.exec()