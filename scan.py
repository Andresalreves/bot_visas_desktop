from playwright.sync_api import sync_playwright, TimeoutError, Error as PlaywrightError
from common_functions import fecha_en_rango, extraer_primer_segmento, change_ip
from fake_useragent import UserAgent
from PyQt6.QtCore import QThread , pyqtSignal
from urllib.parse import urlparse
from datetime import datetime
import multiprocessing
import time
import socket
import json
import random

def retry_with_exponential_backoff(func, max_retries=4, initial_delay=1, max_delay=60):
    def wrapper(*args, **kwargs):
        delay = initial_delay
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    change_ip()
                    raise
                wait = min(delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                print(f"Attempt {attempt + 1} failed. Retrying in {wait:.2f} seconds...")
                time.sleep(wait)
    return wrapper

def check_connectivity(page):
    try:
        return page.evaluate("() => navigator.onLine")
    except:
        return False

@retry_with_exponential_backoff
def safe_reload(page):
    try:
        page.reload(wait_until="networkidle", timeout=60000)
    except PlaywrightError as e:
        if "net::ERR_EMPTY_RESPONSE" in str(e):
            print("Received empty response. Waiting and retrying...")
            time.sleep(5)
            page.goto(page.url, wait_until="networkidle", timeout=60000)
        

def get_random_user_agent():
    ua = UserAgent()
    return ua.random

def get_ip_info():
    try:
        response = requests.get('https://ipapi.co/json/')
        data = response.json()
        return {
            'country': data.get('country_code'),
            'timezone': data.get('timezone'),
            'language': data.get('languages', 'en-US').split(',')[0]
        }
    except:
        # En caso de error, devolver valores predeterminados
        return {
            'country': 'US',
            'timezone': 'America/New_York',
            'language': 'en-US'
        }
            
class scan(QThread):
    agendador = pyqtSignal(dict)
    def __init__(self,console,cuentas, config):
        super().__init__()
        self.queue = multiprocessing.Queue()
        self.config = config
        self.console = console
        num_processes = len(cuentas)
        self.page = None
        self.message = None
        self.rango_busqueda = config['rango_busqueda']
        self.url = config['url']
        self.show_browser_scan = config['show_browser_scan']
        self.time_refresh = config['time_refresh']
        self.wait_scan = config['wait_scan']
        self.idioma = extraer_primer_segmento(self.url)
        self.user_agent = get_random_user_agent()
        self.ip_info = get_ip_info()
        self.estado_actual = 'login'
        self.current_url = self.url
        self.estados = {
            'login': self.login,
            'continuar': self.continuar,
            'acordeon': self.Acordeon,
            'ExtractData': self.ExtractData
        }
        self.processes = []
        self.eventos = [multiprocessing.Event() for _ in range(num_processes)]
        for i, cuenta in enumerate(cuentas):
            siguiente = (i + 1) % num_processes
            pro = multiprocessing.Process(target=self.proceso, args=(i, self.eventos[i], self.eventos[siguiente], cuenta['email'], cuenta['password'],self.queue))
            self.processes.append(pro)
            pro.start()
        self.eventos[0].set()

    def run(self):
        while True:
            data = self.queue.get()
            if data:
                if data['tipo'] == 2:
                    self.agendador.emit({'fechas':data['data'],'config':self.config})
                else:
                    self.console.append(data['message'])
                    self.console.ensureCursorVisible()
 

    def proceso(self, id, event_actual, event_siguiente, email, password,queue):
        try:
            queue.put({'tipo':1,'message':f'Navegador:{id+1}\nCuenta:{email}\nIniciando navegador.\n'})
            with sync_playwright() as p:
                self.browser = p.firefox.launch(headless=self.show_browser_scan, slow_mo=self.wait_scan)
                self.context = self.browser.new_context(                    
                    #user_agent=self.user_agent,
                    #locale=self.ip_info['language'],
                    #timezone_id=self.ip_info['timezone'],
                    viewport={"width": 400, "height": 400})
                self.context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                """)
                self.page = self.context.new_page()
                while self.estado_actual != 'Fin':
                    self.estados[self.estado_actual](id, event_actual, event_siguiente, email, password,queue)
        except Exception as e:
            queue.put({'tipo':1,'message':f'Navegador:{id+1}\nCuenta:{email}\nError: {str(e)}\n'})
            self.verificar_bloqueo(e)
        finally:
            queue.put({'tipo':1,'message':f'Navegador:{id+1}\nCuenta:{email}\nScan Finalizado.\n'})

    def verificar_bloqueo(self,e):
        if 'net::ERR_CONNECTION_REFUSED' in str(e) or 'net::ERR_CONNECTION_CLOSED' in str(e) or 'NS_ERROR_CONNECTION_REFUSED' in str(e):
            change_ip()
            time.sleep(8)
        elif 'net::ERR_INTERNET_DISCONNECTED' in str(e):
            time.sleep(5)
        elif 'context or browser has been closed' in str(e):
            self.estado_actual = 'Fin'
        elif 'net::ERR_NAME_NOT_RESOLVED' in str(e):
            time.sleep(5)

    def login(self, id, event_actual, event_siguiente, email, password,queue):
        try:
            queue.put({'tipo':1,'message':f'Navegador:{id+1}\nCuenta:{email}\nRealizando login.\n'})
            self.page.goto(self.url, timeout=120000)
            username_field = self.page.locator("#user_email")
            password_field = self.page.locator("#user_password")
            checkbox = self.page.wait_for_selector('//*[@id="sign_in_form"]/div[3]/label/div', timeout=10000)
            username_field.fill(email)
            password_field.fill(password)
            checkbox.click()
            try:
                self.page.wait_for_selector('//*[@id="sign_in_form"]/p[1]/input', timeout=20000).click()
                self.page.wait_for_load_state('networkidle', timeout=30000)
                if self.current_url != self.page.url:
                    self.current_url = self.page.url
                    self.estado_actual = 'continuar'
            except Exception as e:
                queue.put({'tipo':1,'message':f'Navegador:{id+1}\nCuenta:{email}\nError: {str(e)}\nReintentando login ...\n'})
                self.verificar_bloqueo(e)
        except Exception as e:
            queue.put({'tipo':1,'message':f'Navegador:{id+1}\nCuenta:{email}\nError: {str(e)}\nReintentando login ...\n'})
            self.verificar_bloqueo(e)

    def continuar(self, id, event_actual, event_siguiente, email, password,queue):
        try:
            queue.put({'tipo':1,'message':f'Navegador:{id+1}\nCuenta:{email}\nlogin ok ...\nClick boton continuar.\n'})
            self.page.wait_for_selector(
                f"xpath=//a[starts-with(@href, '/{self.idioma}/niv/schedule/') and substring(@href, string-length(@href) - string-length('/continue_actions') + 1) = '/continue_actions']",
                state="visible",
                timeout=8000
            ).click()
            self.page.wait_for_load_state('networkidle', timeout=20000)
            if self.current_url != self.page.url:
                self.current_url = self.page.url
                self.estado_actual = 'acordeon'
        except Exception as e:
            safe_reload(self.page)
            queue.put({'tipo':1,'message':f'Navegador:{id+1}\nCuenta:{email}\nError: {str(e)}\nReintentando boton continuar.\n'})
            self.verificar_bloqueo(e)

    def Acordeon(self, id, event_actual, event_siguiente, email, password,queue):
        try:
            queue.put({'tipo':1,'message':f'Navegador:{id+1}\nCuenta:{email}\nEntrando al acordeon.\n'})
            self.visa_number = self.page.url.split("/")[-2]
            self.page.goto(f"https://ais.usvisa-info.com/{self.idioma}/niv/schedule/{self.visa_number}/continue")
            if self.current_url != self.page.url:
                self.estado_actual = 'ExtractData'
        except Exception as e:
            safe_reload(self.page)
            queue.put({'tipo':1,'message':f'Navegador:{id+1}\nCuenta:{email}\nError:{str(e)}.\nReintentando Acordeon.\n'})
            self.verificar_bloqueo(e)

    def ExtractData(self, id, event_actual, event_siguiente, email, password,queue):
        try:
            while True:
                queue.put({'tipo':1,'message':f'Navegador:{id+1}\nCuenta:{email}\nBuscando fechas dentro del rango.\n'})
                event_actual.wait()
                #if not check_connectivity(self.page):
                    #while not check_connectivity(self.page):
                        #time.sleep(5)
                try:
                    self.espera_aleatoria(1,2)
                    self.page.wait_for_selector('//*[@id="paymentOptions"]/div[2]/table', timeout=30000)
                    rows = self.page.locator('//*[@id="paymentOptions"]/div[2]/table//tr')
                    fechas_validas = {}
                    agendar = ''
                    for row in rows.all():
                        consu = row.locator('td').first.inner_text().strip()
                        fecha = row.locator('td').last.inner_text().strip()
                        #if not 'No hay citas disponibles' in fecha:
                        fecha_rango = fecha_en_rango(fecha, self.rango_busqueda)
                        if fecha_rango:
                            agendar += f"\n{consu} : {fecha_rango}"
                            fechas_validas[consu] = fecha_rango
                    
                    if fechas_validas:
                        try:
                            """client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            client_socket.connect(('localhost', self.port))
                            client_socket.sendall(json.dumps(fechas_validas).encode('utf-8'))
                            client_socket.close()"""
                            queue.put({'tipo':2,'data':fechas_validas})
                            queue.put({'tipo':1,'message':f'Navegador:{id+1}\nCuenta:{email}\nFechas encontradas dentro del rango dado:\n{fechas_validas}\nIniciando Agendador.\n'})
                        except ConnectionRefusedError:
                            queue.put({'tipo':1,'message':f'Navegador:{id+1}\nCuenta:{email}\nError:No se pudo enviar la señal al Agendador. Asegúrate de que esté en ejecución.\n'})
                        except Exception as e:
                            queue.put({'tipo':1,'message':f'Navegador:{id+1}\nCuenta:{email}\nError:{str(e)}.\nReintentando buscar fechas.\n'})
                    else:
                        queue.put({'tipo':1,'message':f'Navegador:{id+1}\nCuenta:{email}\nNo se encontraron fechas para agendar en el rango especificado..\n'})
                    
                    for i in range(1, self.time_refresh):
                        print(f"Proceso {id}: {i}")
                        time.sleep(1)
                    
                    safe_reload(self.page)
                except TimeoutError:
                    queue.put({'tipo':1,'message':f'Navegador:{id+1}\nCuenta:{email}\nError:Timeout esperando el selector.\n Reintentando extraer fechas proximas....\n'})
                    self.verificar_bloqueo(e)
                except Exception as e:
                    queue.put({'tipo':1,'message':f'Navegador:{id+1}\nCuenta:{email}\nError:{str(e)}\n Reintentando extraer fechas proximas....\n'})
                    self.verificar_bloqueo(e)

                event_actual.clear()
                event_siguiente.set()

        except Exception as e:
            queue.put({'tipo':1,'message':f'Navegador:{id+1}\nCuenta:{email}\nError:{str(e)}\n Reintentando extraer fechas proximas....\n'})
            self.verificar_bloqueo(e)
            safe_reload(self.page)

    def espera_aleatoria(self,min_segundos,max_segundos):
        tiempo_aleatorio = random.randint(min_segundos * 1000, max_segundos * 1000)
        self.page.wait_for_timeout(tiempo_aleatorio)

    def stop_scan(self):
        for process in self.processes:
            process.terminate()
        for process in self.processes:
            process.join()