import multiprocessing
from bot_playwright import bot
from PyQt6.QtCore import QThread, pyqtSignal
from common_functions import change_ip, extract_data_file, select_consulados, process_response, matar_proceso_por_puerto
from database import Database

class Agendador(QThread):
    event = pyqtSignal(dict)
    def __init__(self,console,config,data):
        super().__init__()
        self.db = Database()
        self.processes = []
        self.response = []
        self.console = console
        self.data = data
        self.proceso_en_ejecucion = False
        self.url = config['url']
        self.show_browser_bot = config['show_browser_bot']
        self.wait_bot = config['wait_bot']
        self.port = config['port']
        self.pais = config['pais']
        self.max_cuentas = config['max_cuentas']
        self.rango = config['rango_busqueda']
        self.server_socket = None
        self.running = False
        self.procesos_finalizados = 0

    def run(self):
        try:
            queue = multiprocessing.Queue()
            indices = list(self.data.keys())
            if self.pais == 'Mexico': 
                cuentas = self.db.get_x_cuentas_activas(self.pais, self.max_cuentas, indices)
            else:
                cuentas = self.db.get_x_cuentas_activas_peru(self.pais, self.max_cuentas)
            #print(cuentas)
            if cuentas:
                #array_consulados = {'consulados':['71','69'],'cas':['83','81'],'fechas':['2024-10-08','2024-12-12']}
                #print(array_consulados)
                #{'id': 1, 'email': 'SaidRubioCh01@gmail.com', 'password': 'VISA2024', 'pais': 'Mexico', 'status': 1}
                search_consulados = {}
                count = 0
                for cuenta in cuentas:
                    count += 1
                    if self.pais == 'Mexico':
                        if cuenta['consulado'] in indices:
                            search_consulados[cuenta['consulado']] = self.data[cuenta['consulado']]

                        if cuenta['cas'] in indices:
                            search_consulados[cuenta['cas']] = self.data[cuenta['cas']]
                        #diccionario_peru = {'consulados': ['115'],'fechas': ['2026-01-08']}
                        array_consulados = select_consulados(search_consulados)
                    else:
                        fechas = []
                        array_consulados = {'consulados':['115'],'fechas':list(self.data.values())}
                    #print(array_consulados)
                    process = multiprocessing.Process(target=bot, args=(cuenta['id'],count,cuenta['email'],cuenta['password'],self.pais,array_consulados,self.url,self.show_browser_bot,self.wait_bot,self.port,self.rango,queue))
                    process.start()
                    self.processes.append(process)

                #for process in self.processes:
                    #process.join()
                #print(response)
                #process_response(self.response,"cuentas.json")
                # Cambiar ip con ExpressVPN
                #change_ip()
                #self.proceso_en_ejecucion = False
                #self.response = []

                count_cuentas = len(cuentas) 
                while True:
                    data = queue.get()
                    if data:
                        if data['tipo'] == 1:
                            self.console.append(data['message'])
                            self.console.ensureCursorVisible()
                        elif data['tipo'] == 8:
                            self.procesos_finalizados += 1
                            if self.procesos_finalizados >= count_cuentas:
                                self.event.emit(data)
                        else:
                            self.event.emit(data)

            else:
                self.console.append(f"No se encontraron cuentas para agendar en estos consulados {self.data}, por favor inserte cuentas para iniciar el proceso.")
                self.console.ensureCursorVisible()
        except Exception as e:
            self.console.append(f'Error: {str(e)}')
            self.console.ensureCursorVisible()
            
    def stop_agendador(self):
        self.running = False
        #self.close_socket()
        for process in self.processes:
            try:
                process.terminate()
                process.join(timeout=1)
            except Exception as e:
                self.queue.put({'tipo':1,'message':f"Error al terminar el proceso: {e}"})
        self.processes.clear()
