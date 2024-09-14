from playwright.sync_api import sync_playwright, TimeoutError, expect
from common_functions import search_prev_options, verificar_fecha, extraer_primer_segmento, fecha_en_rango, validar_licencia, change_ip
from fake_useragent import UserAgent
from database import Database, UpdateCuentaSchema
from datetime import datetime
import time
import re
import random


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

class bot():          
    def __init__(self,cuenta_id,id,nombre_usuario,password,pais,result_scan,url,show_browser_bot,wait_bot,port,rango,queue):
        self.count0 = 0
        self.count1 = 0
        self.count2 = 0
        self.count3 = 0
        self.count4 = 0
        self.db = Database()
        self.cuenta_id = cuenta_id
        self.id = id
        self.browser = None
        self.context = None
        self.page = None
        self.stop_flag = False
        self.nombre_usuario = nombre_usuario
        self.password = password
        self.pais = pais
        self.result_scan = result_scan
        self.url = url
        self.show_browser_bot = show_browser_bot
        self.wait_bot = wait_bot
        self.idioma = extraer_primer_segmento(url)
        self.user_agent = get_random_user_agent()
        self.ip_info = get_ip_info()
        self.port = port
        self.rango_busqueda = rango
        self.visa_number = None
        self.prev_options = None
        self.fechas = None
        self.fechas_cas = None
        self.horas = None
        self.horas_cas = None
        self.selectable_days = None
        self.selectable_days_cas = None
        self.selectable_hours = None
        self.selectable_hours_cas = None
        self.appointments_consulate = None
        self.appointments_cas = None
        self.appointment_date = None
        self.appointment_date_cas = None
        self.appointment_time = None
        self.appointment_time_cas = None
        self.create_appointment = None 
        self.estado_actual = 'login'
        self.current_url = url
        self.queue = queue
        self.estados = {
            'login': self.login,
            'continuar': self.continuar,
            'acordeon': self.Acordeon,
            'FormularioMexico': self.LlenandoFormularioMexico,
            'FormularioPeru': self.LlenandoFormularioPeru,
            'SelectConsulado': self.SelectConsulado,
            'seleccionar_fecha': self.seleccionar_fecha,
            'seleccionar_hora': self.seleccionar_hora,
            'SelectCas': self.SelectCas,
            'seleccionar_fecha_cas': self.seleccionar_fecha_cas,
            'seleccionar_hora_cas': self.seleccionar_hora_cas,
            'Submit': self.Submit
        }
        self.init_bot()

    def init_bot(self):
        try:
            with sync_playwright() as p:
                self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nIniciando Navegador...\n'})
                self.browser = p.chromium.launch(headless=self.show_browser_bot, slow_mo=self.wait_bot)  # Use browser instead of navegador (Spanish for browser)
                self.context = self.browser.new_context(                    
                    user_agent=self.user_agent,
                    locale=self.ip_info['language'],
                    timezone_id=self.ip_info['timezone'],
                    viewport={"width": 800, "height": 800})
                self.context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                """)
                self.page = self.context.new_page()
                while self.estado_actual != 'Fin':
                    self.estados[self.estado_actual]()
        except Exception as e:
            self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nError:{str(e)}...\n'})
            self.verificar_bloqueo(e)
        finally:
            self.queue.put({'tipo':8,'pais':self.pais})

    def verificar_bloqueo(self,e):
        if 'net::ERR_CONNECTION_REFUSED' in str(e) or 'net::ERR_CONNECTION_CLOSED' in str(e) or 'NS_ERROR_CONNECTION_REFUSED' in str(e):
            change_ip()
            time.sleep(8)
        elif 'net::ERR_INTERNET_DISCONNECTED' in str(e):
            time.sleep(5)
        elif 'context or browser has been closed' in str(e) or 'net::ERR_EMPTY_RESPONSE' in str(e):
            self.estado_actual = 'Fin'
        elif 'net::ERR_NAME_NOT_RESOLVED' in str(e):
            time.sleep(5)

    def login(self):
        self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nIniciando Agendamiento para la cuenta: {self.nombre_usuario} Login...\n'})
        self.page.goto(self.url,timeout=120000)
        username_field = self.page.locator("#user_email")
        password_field = self.page.locator("#user_password")
        checkbox = self.page.wait_for_selector('//*[@id="sign_in_form"]/div[3]/label/div',timeout=10000)
        username_field.fill(self.nombre_usuario)
        password_field.fill(self.password)
        checkbox.click()
        try:
            self.page.wait_for_selector('//*[@id="sign_in_form"]/p[1]/input',timeout=20000).click()
            self.page.wait_for_load_state('networkidle', timeout=20000)
            if self.current_url != self.page.url:
                self.current_url = self.page.url
                self.estado_actual = 'continuar'
            else:
                error_selector = '#sign_in_form p.error.animated.bounceIn'
                error_element = self.page.locator(error_selector)
                is_visible = error_element.is_visible()
                if is_visible:
                    self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta: {self.nombre_usuario}\nCorreo electronico o contraseña invalida.\n'})
                    self.estado_actual = 'Fin'
        except Exception as e:
            self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nError: {str(e)}\nReintentando Login...\n'})
            self.verificar_bloqueo(e)

    def continuar(self):
        self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nBoton continuar...\n'})
        try:
            self.page.wait_for_selector(
                #"//*[@id="main"]/div[2]/div[2]/div[1]/div/div/div[1]/div[2]/ul/li/a"
                f"xpath=//a[starts-with(@href, '/{self.idioma}/niv/schedule/') and substring(@href, string-length(@href) - string-length('/continue_actions') + 1) = '/continue_actions']",
                state="visible",
                timeout=8000
            ).click()
            self.page.wait_for_load_state('networkidle', timeout=20000)
            if self.current_url != self.page.url:
                self.current_url = self.page.url
                self.estado_actual = 'acordeon'
        except Exception as e:
            self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nError: {str(e)}\nReintentando boton continuar...\n'})
            self.page.reload()
            self.verificar_bloqueo(e)

    def handle(self,request):
        url_ajax = f'https://ais.usvisa-info.com/{self.idioma}/niv/schedule/{self.visa_number}/appointment/days/115.json?appointments[expedite]=false'
        try:
            if request.url == url_ajax:
                response = request.response()
                if response:
                    self.fechas = response.json()
        except Exception as e:
            self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nError: {str(e)}\nReintentando handle request...\n'})
            self.verificar_bloqueo(e)

    def Acordeon(self):
        self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nEntrando al acordeon...\n'})
        self.page.wait_for_load_state('networkidle', timeout=60000)
        try:
            self.visa_number = self.page.url.split("/")[-2]
            elemento = self.page.get_by_text("Reprogramar cita")
            if elemento.count() > 0:
                print('entro aqui.')
                url = f"https://ais.usvisa-info.com/{self.idioma}/niv/schedule/{self.visa_number}/appointment"
            else:
                url = f"https://ais.usvisa-info.com/{self.idioma}/niv/schedule/{self.visa_number}/continue"
            #print(url)
            #time.sleep(6000)
            if self.idioma == 'es-pe':
                xpath_boton = 'input[type="submit"][value="Continue"]'
                self.page.on("request", self.handle)
            else:
                xpath_boton = '//*[@id="main"]/div[3]/form/div[2]/div/input'
            #self.page.locator('//*[@id="forms"]/ul/li[1]').click()
            #self.page.locator(f'a[href="/es-mx/niv/schedule/{self.visa_number}/continue"]').click()
            self.page.goto(url)
            checkbox_reagendar = self.page.locator('div.icheckbox.icheck-item')
            if checkbox_reagendar.count() > 0 and self.pais == 'Peru':
                print('si existe el checkbox')
                checkbox_reagendar.click()
            reagendar = self.page.locator(xpath_boton)
            if reagendar.count() > 0:
                print('si existe el boton')
                reagendar.click()
            if self.current_url != self.page.url:
                self.current_url = self.page.url
                if self.idioma == 'es-pe':
                    print('Estas son las fechas.',self.fechas)
                    self.estado_actual = 'FormularioPeru'
                else:
                    self.estado_actual = 'FormularioMexico'
        except Exception as e:
            print(e)
            self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nError: {str(e)}\nReintentando acordeon...\n'})
            self.page.reload()
            self.verificar_bloqueo(e)

    def check_response(self,response):
        data = None
        match = re.search('consulate_id', response.url)
        url_ajax_fecha = f'https://ais.usvisa-info.com/{self.idioma}/niv/schedule/{self.visa_number}/appointment/days/{self.result_scan["consulados"][self.count0]}.json?appointments[expedite]=false'
        try:
            if url_ajax_fecha in response.url:
                data = response
        except:
            pass
            if match:
                data = response
        finally:
            if data:
                return data
        
                
    def SelectConsulado(self):
        try:
            if self.count0 <= (len(self.result_scan['consulados']) - 1):
                self.prev_options = search_prev_options(self.result_scan['consulados'][self.count0])
                self.appointments_consulate.select_option(self.prev_options['consulado'])
                try:
                    self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nSeleccionando consulado.\n'})
                    with self.page.expect_response(self.check_response,timeout=10000) as response_info:
                        self.appointments_consulate.select_option(self.result_scan['consulados'][self.count0])
                    self.fechas = response_info.value.json()
                    
                    #self.appointments_consulate.select_option(self.result_scan['consulados'][self.count0])
                    #self.fechas = [{'date':self.result_scan['fechas'][self.count0]}]
                except Exception as e:
                    self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nError:{str(e)}.\n'})
                    self.fechas = [{'date':self.result_scan['fechas'][self.count0]}]
                    #self.verificar_bloqueo(e)
                #print(self.fechas)
                if self.fechas:
                    self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nConsulado seleccionado.\n'})
                    self.appointment_date = self.page.wait_for_selector('//*[@id="appointments_consulate_appointment_date"]',timeout=10000)
                    #self.appointment_date.evaluate("el => el.removeAttribute('readonly')")
                    self.estado_actual = 'seleccionar_fecha'
                else:
                    self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nNo se encontraron fechas en la peticion ajax SelectConsulado.\n'})
                    self.count0 += 1
                    self.estado_actual = 'SelectConsulado'
            else:
                self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nNo se encontraron fechas disponibles para ningun consulado.\n'})
                self.estado_actual = 'Fin'
        except Exception as e:
            self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nError:{str(e)}.\n'})
            self.verificar_bloqueo(e)
            #print(e)

    def LlenandoFormularioMexico(self):
        self.page.locator('#appointments_consulate_address').focus()
        self.appointments_consulate = self.page.wait_for_selector('//*[@id="appointments_consulate_appointment_facility_id"]',timeout=10000)
        self.estado_actual = 'SelectConsulado'

    def format_error(self,e):
        print(e)
        fecha = datetime.now().strftime('%Y-%m-%d')
        hora = datetime.now().strftime('%H:%M:%S')
        error = str(e)
        response = f"\nestatus : Error\nmessage :{error}\nCuenta : {self.nombre_usuario}\nfecha  : {fecha}\nhora : {hora}"
        #self.consola.append(response)

    def seleccionar_fecha(self):
        try:
            self.appointment_date.click()
            self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nSeleccionando fecha consulado.\n'})
            #print('seccion seleccionar fechas.',self.fechas)
            if self.count1 <= (len(self.fechas) - 1):
                if verificar_fecha(self.fechas[self.count1]['date'],self.rango_busqueda):
                    print('Esta es la fecha a seleccionar',self.fechas[self.count1]['date'])
                    #self.appointment_date.fill(self.fechas[self.count1]['date'])
                    url_ajax_hora = f'https://ais.usvisa-info.com/{self.idioma}/niv/schedule/{self.visa_number}/appointment/times/{self.result_scan["consulados"][self.count0]}.json?date={self.fechas[self.count1]["date"]}&appointments[expedite]=false'
                    self.horas = self.select_date(self.fechas[self.count1]['date'],url_ajax_hora)
                    print('Estas son las horas disponibles.',self.horas)
                    self.page.locator('#appointments_consulate_address').click()
                    self.appointment_time = self.page.wait_for_selector("#appointments_consulate_appointment_time",timeout=10000)
                    #self.consola.append("Fecha seleccionada.")
                    # Esperar a que exista al menos una opción con valor
                    if self.horas:                       
                        self.estado_actual = 'seleccionar_hora'
                    else:
                        self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nNo se encontraron horas disponibles para esta fecha: {self.fechas[self.count1]["date"]}, reintentando con otra fecha.\n'})
                        #print('Entrando al error de seleccionar fechas')
                        self.count1 += 1
                else:
                    if self.idioma == 'es-mx':
                        self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nFecha fuera de rango.\n'})
                        self.count0 += 1
                        self.estado_actual = 'SelectConsulado'
                    else:
                        self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nNo se encontraron fechas disponibles.\n'})
                        self.estado_actual = 'Fin'
            else:
                if self.idioma == 'es-mx':
                    self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nNo se encontraron fechas disponibles para este consulado.Escogiendo otro consulado...\n'})
                    self.count0 += 1
                    self.estado_actual = 'SelectConsulado'
                else:
                    self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nNo se encontraron fechas disponibles para este consulado, esperando nuevas fechas disponibles.\n'})
                    #print('No se encontraron fechas disponibles para este consulado.')
                    self.estado_actual = 'Fin'
        except Exception as e:
            self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nError: {str(e)}\n'})
            self.verificar_bloqueo(e)

    def seleccionar_hora(self):
        self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nSeleccionar hora consulado.\n'})
        #print(self.horas['available_times'][self.count2],self.horas)
        try:
            #print(self.horas)
            if self.count2 <= (len(self.horas) - 1):
                if self.idioma == 'es-mx':
                    """
                    url_ajax_hora = f'https://ais.usvisa-info.com/{self.idioma}/niv/schedule/{self.visa_number}/appointment/times/{self.result_scan["cas"][self.count0]}.json?date={self.fechas[self.count1]["date"]}&appointments[expedite]=false'
                    try:
                        with self.page.expect_response(lambda response: url_ajax_hora == response.url,timeout=20000) as response_info3:
                            self.appointment_time.select_option(self.horas['available_times'][self.count2])
                        self.fechas_cas = response_info3.value.json()
                    except Exception as e:
                        self.format_error(e)
                    """
                    self.appointment_time.select_option(self.horas['available_times'][self.count2])

                    self.appointments_cas = self.page.wait_for_selector('//*[@id="appointments_asc_appointment_facility_id"]',timeout=10000)
                    self.appointments_cas.click()
                    self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nHora consulado seleccionada.\n'})
                    #self.consola.append("hora seleccionada.")
                    self.espera_aleatoria(1,2)
                    self.estado_actual = 'SelectCas'
                else:
                    self.appointment_time.select_option(self.horas['available_times'][self.count2])
                    self.create_appointment = self.page.wait_for_selector('//*[@id="appointments_submit"]',timeout=10000)
                    self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nHora consulado seleccionada.\n'})
                    self.estado_actual = 'Submit'
            else:
                self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nNo se encontro hora disponible para esta fecha y este consulado, reintentando con otra fecha...\n'})
                self.count1 += 1
                self.estado_actual = 'seleccionar_fecha'
        except Exception as e:
            self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nError: {str(e)}.\n'})
            self.verificar_bloqueo(e)

    def SelectCas(self):
        try:
            self.appointments_cas.select_option(self.prev_options['cas'])
            self.espera_aleatoria(1,2)
            url_ajax_fecha_cas = f'https://ais.usvisa-info.com/{self.idioma}/niv/schedule/{self.visa_number}/appointment/days/{self.result_scan["cas"][self.count0]}.json?&consulate_id={self.result_scan["consulados"][self.count0]}&consulate_date={self.fechas[self.count1]["date"]}&consulate_time={self.horas["available_times"][self.count2]}&appointments[expedite]=false'
            try:
                if not self.fechas_cas:
                    self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nSelecionando cas.\n'})
                    with self.page.expect_response(lambda response: url_ajax_fecha_cas == response.url,timeout=20000) as response_info:
                        self.appointments_cas.select_option(self.result_scan['cas'][self.count0])
                    self.fechas_cas = response_info.value.json()
            except Exception as e:
                self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nError: {str(e)}.\n'})
                if not self.fechas_cas:
                    with self.page.expect_response(lambda response: url_ajax_fecha_cas == response.url,timeout=20000) as response_info:
                        self.appointments_cas.select_option(self.result_scan['cas'][self.count0])
                    self.fechas_cas = response_info.value.json()
            if self.fechas_cas:
                self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nCas selecionado.\n'})
                self.appointment_date_cas = self.page.wait_for_selector("#appointments_asc_appointment_date",timeout=10000)
                self.appointment_date_cas.click()
                #self.appointment_date_cas.evaluate("el => el.removeAttribute('readonly')")
                self.estado_actual = 'seleccionar_fecha_cas'
            else:
                self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nNo se encontraron fechas para este cas, probando con otra fecha de consulado.\n'})
                self.count1 += 1
                self.estado_actual = 'seleccionar_fecha'
        except Exception as e:
            self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nError: {str(e)}.\n'})
            self.verificar_bloqueo(e)

    def seleccionar_fecha_cas(self):
        try:
            self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nSeleccionando fecha cas.\n'})
            if self.count3 <= (len(self.fechas_cas) - 1):
                limit_date = datetime.strptime(self.fechas[self.count1]['date'], "%Y-%m-%d")
                date = datetime.strptime(self.fechas_cas[self.count3]['date'], "%Y-%m-%d")
                if date < limit_date:
                    #self.appointment_date_cas.fill(self.fechas_cas[self.count3]['date'])
                    url_ajax_hora_cas = f'https://ais.usvisa-info.com/{self.idioma}/niv/schedule/{self.visa_number}/appointment/times/{self.result_scan["cas"][self.count0]}.json?date={self.fechas_cas[self.count3]["date"]}&consulate_id={self.result_scan["consulados"][self.count0]}&consulate_date={self.fechas[self.count1]["date"]}&consulate_time={self.horas["available_times"][self.count2]}&appointments[expedite]=false'
                    self.horas_cas = self.select_date(self.fechas_cas[self.count3]['date'],url_ajax_hora_cas)
                    self.page.locator('#appointments_asc_address').click()
                    self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nFecha cas selecionada....\n'})
                    if self.horas_cas:
                        self.appointment_time_cas = self.page.wait_for_selector("#appointments_asc_appointment_time",timeout=10000)
                        self.estado_actual = 'seleccionar_hora_cas'
                    else:
                        self.count3 += 1
                else:
                    ####### Cuando se habilite la opcion se puede devolver a buscar otro consulado tener en cuenta ########.
                    self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nNo se encontro fecha para este cas....\n'})
                    self.count2 += 1
                    self.estado_actual = 'seleccionar_fecha'
            else:
                ####### Cuando se habilite la opcion se puede devolver a buscar otro consulado tener en cuenta ########.
                self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nNo se encontraron fechas para este cas....\n'})
                self.count2 += 1
                self.estado_actual = 'seleccionar_fecha'
        except Exception as e:
            self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nError: {str(e)}\n'})
            self.verificar_bloqueo(e)

    def seleccionar_hora_cas(self):
        self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nSelecionando hora cas....\n'})
        try:
            if self.count4 <= (len(self.horas_cas['available_times']) - 1):
                self.appointment_time_cas.select_option(self.horas_cas['available_times'][self.count4])
                self.create_appointment = self.page.locator('#appointments_submit')
                is_enabled = self.create_appointment.is_enabled()
                if is_enabled:
                    self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nHora cas seleccionada....\n'})
                    self.estado_actual = 'Submit'
                else:
                    self.count4 += 1
            else:
                self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nNo se encontro hora disponible para esta fecha reintentando con otra fecha cas....\n'})
                self.count2 += 1
                self.estado_actual = 'seleccionar_fecha'
        except Exception as e:
            self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nError: {str(e)}\n'})    
            self.verificar_bloqueo(e)


    def LlenandoFormularioPeru(self):
        self.page.locator('#appointments_consulate_address').focus()
        self.appointment_date = self.page.wait_for_selector('//*[@id="appointments_consulate_appointment_date"]',timeout=10000)
        #self.appointment_date.evaluate("el => el.removeAttribute('readonly')")
        self.estado_actual = 'seleccionar_fecha'

    def Submit(self):
        #Submit appointment
        is_enabled = self.create_appointment.is_enabled()
        if is_enabled:
            #self.create_appointment.click()
            try:
                #flash_messages = self.page.wait_for_selector("#flash_messages .notice", state="visible")
                #texto_mensaje = flash_messages.inner_text()
                response = validar_licencia()
                self.queue.put({'tipo':2,'event':response,'cuenta':self.nombre_usuario,'cuenta_id':self.cuenta_id})
                try:
                    cuenta_update = UpdateCuentaSchema(id=self.cuenta_id,status=0)
                    self.db.update_cuenta(cuenta_update)
                except Exception as e:
                    self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nError: {str(e)}\n'})
                self.browser.close()
                self.estado_actual = 'Fin'
            except Exception as e:
                self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nError: {str(e)}\n'})

    def select_date(self,target_date,url):
        # Convertir la fecha objetivo a un objeto datetime
        target_date = datetime.strptime(target_date, "%Y-%m-%d")
        while True:
            current_month = self.page.locator('.ui-datepicker-month').first.inner_text()
            current_year = int(self.page.locator('.ui-datepicker-year').first.inner_text())
            current_date = datetime(current_year, self.month_to_number(current_month), 1)
            
            if current_date.year == target_date.year and current_date.month == target_date.month:
                break
            print('Pase de la seleccion de fechas cas y estoy aqui.')
            # Si la fecha objetivo es posterior, hacer clic en "Next"
            if current_date < target_date:
                next_button = self.page.locator('.ui-datepicker-next')
                if next_button.is_visible():
                    next_button.click()
                else:
                    raise Exception("No se puede navegar más allá en el futuro")
            else:
                prev_button = self.page.locator('.ui-datepicker-prev')
                if prev_button.is_visible():
                    prev_button.click()
                else:
                    raise Exception("No se puede navegar más atrás en el pasado")
        # Seleccionar el día
        day_selector = f"td[data-handler='selectDay'][data-month='{target_date.month - 1}'][data-year='{target_date.year}'] a:text-is('{target_date.day}')"
        #day_selector = f'//td[@data-handler="selectDay"]/a[text()="{target_date.day}"]'
        try:
            self.page.wait_for_selector(day_selector, state="visible", timeout=5000)
            available_day = self.page.locator(day_selector)
            #available_day = page.locator(day_selector)
            if available_day.count() > 0:
                with self.page.expect_response(lambda response: url == response.url,timeout=20000) as response_info2:
                    available_day.click()
                data = response_info2.value.json()
                print(data)
                return data
            else:
                self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nError:Fecha invalida.\n'})
        except Exception as e:
            self.queue.put({'tipo':1,'message':f'Navegador:{self.id}\nCuenta:{self.nombre_usuario}\nError:{str(e)}.\n'})
            """
            self.appointment_date.click()
            selectable_days_selector = "td[data-handler='selectDay'], td.ui-datepicker-current-day"
            self.page.wait_for_selector(selectable_days_selector, state="visible")
            first_selectable_day = self.page.locator(selectable_days_selector).first
            with self.page.expect_response(lambda response: url_ajax_hora == response.url,timeout=10000) as response_info2:
                first_selectable_day.click()
            self.horas = response_info2.value.json()
            """

    def month_to_number(self,month):
        months = ['January', 'February', 'March', 'April', 'May', 'June', 
                'July', 'August', 'September', 'October', 'November', 'December']
        return months.index(month) + 1
    
    def espera_aleatoria(self,min_segundos,max_segundos):
        tiempo_aleatorio = random.randint(min_segundos * 1000, max_segundos * 1000)
        self.page.wait_for_timeout(tiempo_aleatorio)

"""
if __name__ == "__main__":
    print(sys.argv)

diccionario_peru = {'consulados': ['115'],'fechas': ['2026-01-08']}
bot("omarvs2024@hotmail.com",
    "peru2023",
    diccionario_peru,
    MyConsola,
    "https://ais.usvisa-info.com/es-pe/niv/users/sign_in",
    False,
    100,
    5555,
    900
)
"""
"""
diccionario = {'consulados': ['65', '67', '68', '69', '72', '73', '74'], 'cas': ['76', '78', '79', '81', '84', '85', '88'], 'fechas': ['2026-01-08', '2026-03-09', '2025-09-11', '2026-08-04', '2026-01-05', '2025-08-19', '2025-10-31']}
bot(#"mperezcastillo828@gmail.com",
    #"),5(Qq>g+v",
    'SaidRubioCh01@gmail.com',
    'VISA2024',
    diccionario,
    MyConsola,
    "https://ais.usvisa-info.com/es-mx/niv/users/sign_in",
    False,
    100,
    5554,
    900
)
"""