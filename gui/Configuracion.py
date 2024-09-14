from PyQt6 import uic
from PyQt6.QtWidgets import QMessageBox
from database import Database, ConfiguracionSchema
import requests
import re

class Configuracion():
    def __init__(self,args):
        self.Configuracion = uic.loadUi('gui/configuracion.ui')
        self.Configuracion.show()
        self.db = Database()
        self.data = None
        self.pais = args['pais']
        self.init_form()
        self.Configuracion.GuardarConfiguracion.clicked.connect(self.SetConfiguracion)

    def init_form(self):
        self.Configuracion.MensajeInicioConfiguracion.setText(f'Configuracion {self.pais}')
        self.data = self.db.get_configuracion_by_pais(self.pais)
        # Crear el modelo de tabla
        self.Configuracion.CuentasSimultaneas.setValue(self.data['max_cuentas'])
        self.Configuracion.CuentasSimultaneasScan.setValue(self.data['max_cuentas_scan'])
        self.Configuracion.TiempoRefrescado.setValue(self.data['time_refresh'])
        self.Configuracion.RangoBusqueda.setValue(self.data['rango_busqueda'])
        self.Configuracion.MostrarScan.setChecked(not self.data['show_browser_scan'])
        self.Configuracion.MostrarBot.setChecked(not self.data['show_browser_bot'])
        self.Configuracion.DelayScan.setValue(self.data['wait_scan'])
        self.Configuracion.DelayBot.setValue(self.data['wait_bot'])
        self.Configuracion.url.setText(self.data['url'])
        self.Configuracion.puerto.setValue(self.data['port'])

    def SetConfiguracion(self):
        Configuracion = ConfiguracionSchema(
            id = self.data['id'],
            pais=self.pais,
            max_cuentas = self.Configuracion.CuentasSimultaneas.value(),
            max_cuentas_scan = self.Configuracion.CuentasSimultaneasScan.value(),
            time_refresh = self.Configuracion.TiempoRefrescado.value(),
            rango_busqueda = self.Configuracion.RangoBusqueda.value(),
            show_browser_scan = not self.Configuracion.MostrarScan.isChecked(),
            show_browser_bot = not self.Configuracion.MostrarBot.isChecked(),
            wait_scan = self.Configuracion.DelayScan.value(),
            wait_bot = self.Configuracion.DelayBot.value(),
            url = self.Configuracion.url.text(),
            port = self.Configuracion.puerto.value()
        )
        # Actualizar la configuración en la base de datos
        response = self.db.update_configuracion(Configuracion)
        #print(response)
        QMessageBox.information(
            self.Configuracion,
            response['title'],
            response['message'],
            QMessageBox.StandardButton.Ok
        )