import logging
import webbrowser
from PyQt6 import uic
from PyQt6.QtCore import QTimer, pyqtSlot, pyqtSignal
from PyQt6.QtWidgets import QMainWindow, QMessageBox
from database import Base, engine, Database, ConfiguracionSchema, CuentaFalsaSchema
from gui.AgregarCuentas import AgregarCuentas
from sqlalchemy.exc import SQLAlchemyError
from signal_acounts import SignalAcounts
from scan import scan
from listening_bot import Agendador
from gui.Configuracion import Configuracion

logging.basicConfig(filename='logs/app.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = None
        self.retry_count = 0
        self.max_retries = 3
        self.scan_mexico = None
        self.scan_peru = None
        self.agendamiento_mexico = None
        self.agendamiento_peru = None
        self.agendador_peru_running = False
        self.agendador_mexico_running = False
        self.init_ui()
        self.init_database()

    def init_ui(self):
        self.config_mexico = {}
        self.config_peru = {}
        self.main = uic.loadUi('gui/myapp.ui', self)
        self.main.showMaximized()
        self.main.AgregarCuentasMexico.clicked.connect(lambda: self.AgregarCuentas({'pais':'Mexico','tipo':1}))
        self.main.AgregarCuentasPeru.clicked.connect(lambda: self.AgregarCuentas({'pais':'Peru','tipo':1}))
        self.main.AgregarCuentasFalsasMexico.clicked.connect(lambda: self.AgregarCuentas({'pais':'Mexico','tipo':2}))
        self.main.AgregarCuentasFalsasPeru.clicked.connect(lambda: self.AgregarCuentas({'pais':'Peru','tipo':2}))
        self.main.BotMexico.clicked.connect(self.StartBotMexico)
        self.main.ButtonStopBotMexico.clicked.connect(self.StopBotMexico)
        self.main.ButtonStopBotMexico.setEnabled(False)
        self.main.ButtonStopBotMexico.setStyleSheet("color: black;background: rgb(189, 189, 189);")

        self.main.BotPeru.clicked.connect(self.StartBotPeru)
        self.main.ButtonStopBotPeru.clicked.connect(self.StopBotPeru)
        self.main.ButtonStopBotPeru.setEnabled(False)
        self.main.ButtonStopBotPeru.setStyleSheet("color: black;background: rgb(189, 189, 189);")
        self.main.actionSoporte.triggered.connect(self.abrir_whatsapp)
        self.main.ConfiguracionMexico.triggered.connect(lambda: self.SetConfiguracion({'pais':'Mexico'}))
        self.main.ConfiguracionPeru.triggered.connect(lambda: self.SetConfiguracion({'pais':'Peru'}))

    @pyqtSlot(dict)
    def terminate(self,signal):
        if signal['tipo'] == 8:
            if signal['pais'] == 'Mexico':
                self.main.ConsolaAgendadorMexico.append('Se libero el agendador Mexico y esta disponible para una nueva tarea.')
                print('Se libero el agendador Mexico y esta disponible para una nueva tarea.')
                self.agendador_mexico_running = False
            else:
                self.main.ConsolaAgendadorPeru.append('Se libero el agendador Peru y esta disponible para una nueva tarea.')
                print('Se libero el agendador Peru y esta disponible para una nueva tarea.')
                self.agendador_peru_running = False
        elif signal['event']['activation'] == 0:
            self.StopBotMexico()
            self.StopBotPeru()
            QMessageBox.warning(self, "Licencia expirada.", signal['event']['message'])
            self.main.AgregarCuentasMexico.clicked.disconnect()
            self.main.AgregarCuentasMexico.clicked.connect(self.message_license)
            self.main.AgregarCuentasPeru.clicked.disconnect()
            self.main.AgregarCuentasPeru.clicked.connect(self.message_license)
            self.main.AgregarCuentasFalsasMexico.clicked.disconnect()
            self.main.AgregarCuentasFalsasMexico.clicked.connect(self.message_license)
            self.main.AgregarCuentasFalsasPeru.clicked.disconnect()
            self.main.AgregarCuentasFalsasPeru.clicked.connect(self.message_license)
            self.main.BotMexico.clicked.disconnect()
            self.main.BotMexico.clicked.connect(self.message_license)
            self.main.ButtonStopBotMexico.clicked.disconnect()
            self.main.ButtonStopBotMexico.clicked.connect(self.message_license)
            self.main.BotPeru.clicked.disconnect()
            self.main.BotPeru.clicked.connect(self.message_license)
            self.main.actionSoporte.triggered.disconnect()
            self.main.actionSoporte.triggered.connect(self.message_license)
            self.main.ConfiguracionMexico.triggered.disconnect()
            self.main.ConfiguracionMexico.triggered.connect(self.message_license)
            self.main.ConfiguracionPeru.triggered.disconnect()
            self.main.ConfiguracionPeru.triggered.connect(self.message_license)
        else:
            QMessageBox.warning(self, "Cuenta agendada.", signal['event']['message']+" "+signal['cuenta'])

    def message_license(self):
        QMessageBox.warning(self, "Licencia expirada.", "Por favor introduce una licencia valida.")

    @pyqtSlot(dict)
    def agendador_mexico(self,data):
        if self.agendador_mexico_running:
            self.main.ConsolaAgendadorMexico.append("Agendador Mexico ya está en ejecución. Ignorando nueva solicitud.")
            return

        self.agendamiento_mexico = Agendador(self.main.ConsolaAgendadorMexico,data['config'],data['fechas'])
        if not self.agendamiento_mexico.isRunning():
            self.agendamiento_mexico.event.connect(self.terminate)
            self.agendamiento_mexico.start()
            self.agendador_mexico_running = True

    @pyqtSlot(dict)
    def agendador_peru(self,data):
        if self.agendador_peru_running:
            self.main.ConsolaAgendadorPeru.append("Agendador Peru ya está en ejecución. Ignorando nueva solicitud.")
            return
                
        self.agendamiento_peru = Agendador(self.main.ConsolaAgendadorPeru,data['config'],data['fechas'])
        if not self.agendamiento_peru.isRunning():
            self.agendamiento_peru.event.connect(self.terminate)
            self.agendamiento_peru.start()
            self.agendador_peru_running = True
    
    """
    def StartBotMexico(self):
        self.config_mexico = self.db.get_configuracion_by_pais("Mexico")
        data = {'Ciudad Juarez': '2025-07-17', 'Guadalajara': '2026-02-06', 'Hermosillo': '2025-08-11', 'Matamoros': '2025-06-10', 'Merida': '2026-03-09', 'Mexico City': '2026-02-04', 'Monterrey': '2025-09-04', 'Nogales': '2025-07-02', 'Nuevo Laredo': '2025-08-04', 'Tijuana': '2025-06-23'}
        self.agendamiento = Agendador(self.main.ConsolaAgendadorMexico,self.config_mexico,data)
        if not self.agendamiento.isRunning():
            self.agendamiento.event.connect(self.terminate)
            #self.agendamiento.event.connect(self.terminate)
            self.agendamiento.start()
    """
    def StartBotMexico(self):
        try:
            #self.scraper_manager.start_scrapers()
            self.main.BotMexico.setEnabled(False)
            self.main.BotMexico.setStyleSheet("color: black;background-color: rgb(189, 189, 189);")
            self.main.ButtonStopBotMexico.setEnabled(True)
            self.main.ButtonStopBotMexico.setStyleSheet("color: white;background: #000080;")
            self.config_mexico = self.db.get_configuracion_by_pais("Mexico")
            cuentas_falsas = self.db.get_cuenta_falsa('Mexico',self.config_mexico['max_cuentas_scan'])
            if not cuentas_falsas:
                self.main.ConsolaMexico.setText('No se encontró ninguna cuenta falsa para escanear la página.')
            else:
                self.scan_mexico = scan(self.main.ConsolaMexico,cuentas_falsas,self.config_mexico)
                #self.scan_mexico = scan(self.main.ConsolaMexico,cuentas_falsas,self.config_mexico['rango_busqueda'],self.config_mexico['url'],self.config_mexico['show_browser_scan'],self.config_mexico['wait_scan'],self.config_mexico['port'],self.config_mexico['time_refresh'])
                if not self.scan_mexico.isRunning():
                    self.scan_mexico.agendador.connect(self.agendador_mexico)
                    self.scan_mexico.start()
        except Exception as e:
            print(e)
            self.main.ConsolaMexico.setText(f'Error al iniciar el proceso: {str(e)}')
              
    def StopBotMexico(self):
        self.agendador_mexico_running = False
        if hasattr(self, 'scan_mexico'):
            self.main.BotMexico.setEnabled(True)
            self.main.BotMexico.setStyleSheet("color: white;background-color:#000080;")
            self.main.ButtonStopBotMexico.setEnabled(False)
            self.main.ButtonStopBotMexico.setStyleSheet("color: black;background-color: rgb(189, 189, 189);")
            if self.scan_mexico:
                if self.scan_mexico.isRunning():
                    self.scan_mexico.stop_scan()
            if self.agendamiento_mexico:
                if self.agendamiento_mexico.isRunning():
                    self.agendamiento_mexico.stop_agendador()
            self.main.ConsolaMexico.setText('Scan mexico detenido')
            self.main.ConsolaAgendadorMexico.setText("Agendador mexico detenido.")
        else:
            self.main.ConsolaMexico.setText("No hay un bot en ejecución para detener.")

    def StartBotPeru(self):
        #data = {'fechas': {'Lima': '2025-12-11'}, 'config': {'id': 2, 'pais': 'Peru', 'max_cuentas': 1, 'max_cuentas_scan': 1, 'time_refresh': 20, 'rango_busqueda': 900, 'show_browser_scan': False, 'show_browser_bot': False, 'wait_scan': 100, 'wait_bot': 100, 'url': 'https://ais.usvisa-info.com/es-pe/niv/users/sign_in', 'port': 5555}}
        #self.agendador_peru(data)
        try:
            self.main.BotPeru.setEnabled(False)
            self.main.BotPeru.setStyleSheet("color: black;background-color: rgb(189, 189, 189);")
            self.main.ButtonStopBotPeru.setEnabled(True)
            self.main.ButtonStopBotPeru.setStyleSheet("color: white;background: #000080;")
            config_peru = self.db.get_configuracion_by_pais("Peru")
            cuenta_falsa = self.db.get_cuenta_falsa('Peru',config_peru['max_cuentas_scan'])
            if not cuenta_falsa:
                self.main.ConsolaPeru.setText('No se encontró ninguna cuenta falsa para escanear la página.')
            else:
                self.scan_peru = scan(self.main.ConsolaPeru,cuenta_falsa,config_peru)
                if not self.scan_peru.isRunning():
                    self.scan_peru.agendador.connect(self.agendador_peru)
                    self.scan_peru.start()
        except Exception as e:
            #print(e)
            self.main.ConsolaPeru.setText(f'Error al iniciar el proceso: {str(e)}')

    def StopBotPeru(self):
        self.agendador_peru_running = False
        if hasattr(self, 'scan_peru'):
            self.main.BotPeru.setEnabled(True)
            self.main.BotPeru.setStyleSheet("color: white;background-color:#000080;")
            self.main.ButtonStopBotPeru.setEnabled(False)
            self.main.ButtonStopBotPeru.setStyleSheet("color: black;background-color: rgb(189, 189, 189);")
            if self.scan_peru:
                if self.scan_peru.isRunning():
                    self.scan_peru.stop_scan()
            if self.agendamiento_peru:
                if self.agendamiento_peru.isRunning():
                    self.agendamiento_peru.stop_agendador()
            self.main.ConsolaPeru.setText('Scan peru Detenido')
            self.main.ConsolaAgendadorPeru.setText("Agendador peru detenido.")
        else:
            self.main.ConsolaPeru.setText("No hay un bot en ejecución para detener.")

    
    def SetConfiguracion(self,pais):
        self.modalConfiguracion = Configuracion(pais)

    def AgregarCuentas(self,pais):
        self.modalAgregarCuentas = AgregarCuentas(pais)
    
    def abrir_whatsapp(self):
        url_whatsapp = "https://wa.me/3016969487"
        webbrowser.open(url_whatsapp)

    def init_database(self):
        try:
            Base.metadata.create_all(engine)
            self.db = Database()
            config = self.db.get_configuracion(1)
            cuentas_falsas = self.db.get_cuentas_falsas()
            if not config:
                configs = [
                    ConfiguracionSchema(pais="Mexico", max_cuentas=1,max_cuentas_scan=1, time_refresh=30,rango_busqueda=400,show_browser_scan=True,show_browser_bot=False,wait_scan=100,wait_bot=100,url="https://ais.usvisa-info.com/es-mx/niv/users/sign_in",port=5554, ),
                    ConfiguracionSchema(pais="Peru", max_cuentas=1,max_cuentas_scan=1, time_refresh=30,rango_busqueda=400,show_browser_scan=True,show_browser_bot=False,wait_scan=100,wait_bot=100,url="https://ais.usvisa-info.com/es-pe/niv/users/sign_in",port=5555, )
                ]

                self.db.insert_multiple_configuraciones(configs)
            if not cuentas_falsas:
                CuentasFalsas = [
                    CuentaFalsaSchema(pais="Mexico",email="info19@handersongc.com", password="12345678", status=1),
                    CuentaFalsaSchema(pais="Peru",email="info31@handersongc.com", password="12345678", status=1)
                ]

                self.db.insert_multiple_cuentas_falsas(CuentasFalsas)
            logging.info("Base de datos inicializada correctamente")
            self.retry_count = 0
        except SQLAlchemyError as e:
            logging.error(f"Error al inicializar la base de datos: {e}")
            self.handle_db_error("inicializar")

    def execute_db_operation(self, operation):
        try:
            result = operation()
            self.retry_count = 0
            return result
        except SQLAlchemyError as e:
            logging.error(f"Error en la operación de base de datos: {e}")
            self.handle_db_error("ejecutar operación")
            return None

    def handle_db_error(self, operation):
        self.retry_count += 1
        if self.retry_count <= self.max_retries:
            self.show_error_message(f"Error al {operation} la base de datos. Intento {self.retry_count} de {self.max_retries}")
            QTimer.singleShot(5000, self.retry_connection)
        else:
            self.show_critical_error(f"No se pudo {operation} la base de datos después de {self.max_retries} intentos.")

    def retry_connection(self):
        logging.info("Reintentando conexión a la base de datos...")
        self.init_database()

    def show_error_message(self, message):
        QMessageBox.warning(self, "Error de Base de Datos", message)

    def show_critical_error(self, message):
        QMessageBox.critical(self, "Error Crítico", message)
        self.close()

    def closeEvent(self, event):
        if self.db:
            self.db.close()
        logging.info("Aplicación cerrada")
        super().closeEvent(event)

    def obtener_configuracion(self):
        return self.execute_db_operation(lambda: self.db.get_configuracion(1))