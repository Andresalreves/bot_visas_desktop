from datetime import datetime, date, timedelta
from evpn import ExpressVpnApi
import subprocess
import requests
import random
import json
import os
import uuid
import locale

url = 'http://127.0.0.1:5000/'
#url = 'https://tuvisa.onrender.com/'

# Establecer la configuración regional a español
locale.setlocale(locale.LC_TIME, 'es_CO.utf8')

from urllib.parse import urlparse

def extraer_primer_segmento(url):
    parsed_url = urlparse(url)
    path_segments = parsed_url.path.split('/')
    primer_segmento = next((segment for segment in path_segments if segment), None)
    return primer_segmento

def fecha_en_rango(fecha_str, dias_rango=90):
    # Convertir la fecha string a objeto datetime
    try:
        fecha = datetime.strptime(fecha_str, "%d %B, %Y")
    except Exception as e:
        print(e)
        return None
    # Obtener la fecha actual
    hoy = datetime.now()
    # Calcular la fecha límite (90 días desde hoy)
    fecha_limite = hoy + timedelta(days=dias_rango)
    # Verificar si la fecha está dentro del rango
    if(hoy <= fecha <= fecha_limite):
        return fecha.strftime('%Y-%m-%d')
    else:
        return None

def check_activation(mac):
    try:
        response = requests.post(url+'init', json={'mac': mac})
        response.raise_for_status()  # Esto lanzará una excepción para códigos de estado HTTP no exitosos
        return response.json()  # Tu API devuelve True o False
    except requests.RequestException as e:
        print(f"Error en la solicitud HTTP: {e}")
        return False  # Asumimos que no está activado si hay un error
    
def validar_licencia():
    try:
        response = requests.post(url+'validar_licencia', json={'mac': get_mac_address()})
        #print(response.json())
        response.raise_for_status()  # Esto lanzará una excepción para códigos de estado HTTP no exitosos
        return response.json()
    except requests.RequestException as e:
        print(f"Error en la solicitud HTTP: {e}")
        return False  # Asumimos que no está activado si hay un error

def get_mac_address():
    return ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0,48,8)][::-1])

def change_ip():
    with ExpressVpnApi() as api:
        locations = api.locations # get available locations
        loc = random.choice(locations)
        api.connect(loc["id"])

def extract_data_file(file):
    # Verificar si el archivo existe
    if os.path.exists(file):
        with open(file, 'r') as archivo:
            datos = json.load(archivo)
    else:
        # Si el archivo no existe, crearlo con una lista vacía
        datos = []
        with open(file, 'w') as archivo:
            json.dump(datos, archivo, indent=4)
        print(f"El archivo {file} no existía y fue creado.")
    return datos

def select_consulados(consulado):
    nombre_consulados = [
        'Mexico City', #70
        'Guadalajara', #66
        'Monterrey', #71
        'Ciudad Juarez', #65
        'Hermosillo', #67
        'Matamoros', #68
        'Merida', #69
        'Nogales', #72
        'Nuevo Laredo', #73
        'Tijuana' #74
    ]
    consulados = []
    cas = []
    fechas = []
    list_consulados = ['70','66','71','65','67','68','69','72','73','74']
    list_cas = ['82','77','83','76','78','79','81','84','85','88']
    # Recorre la lista original usando enumerate()
    for indice, elemento in enumerate(nombre_consulados):
        # Agrega el índice a la lista de índices
        if elemento in consulado:
            consulados.append(list_consulados[indice])
            fechas.append(consulado[elemento])
            # Agrega el elemento a la lista de elementos
            cas.append(list_cas[indice])
    return {"consulados":consulados,"cas":cas,"fechas":fechas}

def search_prev_options(consulado):
    list_consulados = ['70','66','71','65','67','68','69','72','73','74']
    list_cas = ['82','77','83','76','78','79','81','84','85','88']
    index_option = list_consulados.index(consulado)
    if index_option > 0:
        prev_consulado = list_consulados[(index_option-1)]
        prev_cas = list_cas[(index_option-1)]
    else:
        prev_consulado = list_consulados[(index_option+1)]
        prev_cas = list_cas[(index_option+1)]
    return {"consulado":prev_consulado,"cas":prev_cas}

def verificar_fecha(fecha_texto,rango):
    fecha_a_verificar = datetime.strptime(fecha_texto, "%Y-%m-%d").date()
    fecha_actual = date.today()
    fecha_limite = fecha_actual + timedelta(days=rango)
    if fecha_a_verificar >= fecha_actual and fecha_a_verificar <= fecha_limite:
        return True
    else:
        return False

def escribir_json(nombre_archivo, datos):
    with open(nombre_archivo, 'w') as archivo:
        json.dump(datos, archivo, indent=4)

def process_response(results,archivo_original):
    fecha = datetime.now().strftime('%Y-%m-%d')
    ruta_agendadas = f"./agendadas/cuentas_completadas_{fecha}.json"
    ruta_logs = f"./logs/logs_{fecha}.json"
    # Leer los datos del archivo JSON original
    cuentas = extract_data_file(archivo_original)
    agendadas = extract_data_file(ruta_agendadas)
    logs = extract_data_file(ruta_logs)
    for result in results:
        if result['estatus'] == 'ok':
            agendadas.append(result)
        else:
            logs.append(result)
    escribir_json(ruta_agendadas,agendadas)
    escribir_json(ruta_logs,logs)
    for agendada in agendadas: 
        for cuenta in cuentas:
            if cuenta['email'] == agendada['cuenta']['email']:
                cuentas.remove(cuenta)

    escribir_json(archivo_original, cuentas)

def matar_proceso_por_puerto(puerto):
    comando = f"lsof -t -i:{puerto}"
    try:
        resultado = subprocess.check_output(comando, shell=True, text=True)
        pid = resultado.strip()
        # Matamos el proceso
        os.kill(int(pid), 9)
        print(f"Proceso con PID {pid} que estaba usando el puerto {puerto} ha sido eliminado.")
    except subprocess.CalledProcessError:
        print(f"No se encontró ningún proceso escuchando en el puerto {puerto}")