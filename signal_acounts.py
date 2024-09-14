from PyQt6.QtCore import QThread, pyqtSignal
import socket
import json

class SignalAcounts(QThread):
    signal_terminate = pyqtSignal(dict)
    def __init__(self):
        super().__init__()
        self.running = False
        self.conn = None

    def run(self):
        self.running = True
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('localhost', 8888))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1)  # Set a timeout for accept()
            while self.running:
                try:
                    self.conn, addr = self.server_socket.accept()
                    with self.conn:
                        data = self.conn.recv(1024)
                        message = json.loads(data.decode('utf-8'))
                        self.signal_terminate.emit(message)
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        self.signal_terminate.emit({'accion':2,'message':f'Error: {str(e)}'})
        except Exception as e:
            self.signal_terminate.emit({'accion':2,'message':f'Error al iniciar el socket: {str(e)}'})
        finally:
            self.close_socket()

    def close_socket(self):
        if self.server_socket:
            try:
                self.server_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                # El socket ya puede estar cerrado, lo ignoramos
                pass
            try:
                self.server_socket.close()
            except OSError:
                # El socket ya puede estar cerrado, lo ignoramos
                pass
        self.server_socket = None
        self.signal_terminate.emit({'accion':2,'message':f'Socket notificacion cerrado.'})