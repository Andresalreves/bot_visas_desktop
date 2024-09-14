from PyQt6.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt6.QtWidgets import QHeaderView, QPushButton, QHBoxLayout, QWidget, QStyledItemDelegate, QComboBox
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QSize
from PyQt6 import uic
from database import Database, CuentaSchema, CuentaFalsaSchema
import requests
import re

class ComboBoxDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        if index.column() == 2:  # País
            editor.addItems(['Mexico', 'Peru'])
        elif index.column() in [3, 4]:  # Consulado 1 y 2
            editor.addItems([
                'Mexico City',
                'Guadalajara',
                'Monterrey',
                'Ciudad Juarez',
                'Hermosillo',
                'Matamoros',
                'Merida',
                'Nogales',
                'Nuevo Laredo',
                'Tijuana'
            ])
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.ItemDataRole.EditRole)
        editor.setCurrentText(value)

    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value, Qt.ItemDataRole.EditRole)

class ButtonDelegate(QStyledItemDelegate):
    edit_clicked = pyqtSignal(int, int)  # Cambiado para incluir ID y fila
    delete_clicked = pyqtSignal(int, int)  # Cambiado para incluir ID y fila

    def paint(self, painter, option, index):
        if not self.parent().indexWidget(index):
            button_widget = QWidget()
            edit_button = QPushButton()
            delete_button = QPushButton()
            
            # Configurar iconos
            edit_button.setIcon(QIcon("editar.png"))
            delete_button.setIcon(QIcon("borrar.png"))
            
            # Configurar tamaño de los botones
            button_size = QSize(20, 20)  # Ajusta este tamaño según necesites
            edit_button.setIconSize(button_size)
            delete_button.setIconSize(button_size)
            edit_button.setFixedSize(button_size)
            delete_button.setFixedSize(button_size)
            
            # Quitar el borde de los botones
            edit_button.setStyleSheet("QPushButton { border: none; }")
            delete_button.setStyleSheet("QPushButton { border: none; }")

            layout = QHBoxLayout(button_widget)
            layout.addWidget(edit_button)
            layout.addWidget(delete_button)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(5)  # Espacio entre los botones
            button_widget.setLayout(layout)

            # Obtener el ID de los datos del modelo
            id_data = index.data(Qt.ItemDataRole.UserRole)

            edit_button.clicked.connect(lambda _, row=index.row(), id=id_data: self.edit_clicked.emit(id, row))
            delete_button.clicked.connect(lambda _, row=index.row(), id=id_data: self.delete_clicked.emit(id, row))

            self.parent().setIndexWidget(index, button_widget)

class AgregarCuentas(QObject):
    def __init__(self,args):
        super().__init__()
        self.AgregarCuentas = uic.loadUi('gui/cuentas.ui')
        self.AgregarCuentas.show()
        self.db = Database()
        self.pais = args['pais']
        self.tipo = args['tipo']
        self.init_table()
        self.AgregarCuentas.BtnAgregarCuenta.clicked.connect(self.AgregarCuenta)
        if self.tipo != 1 or self.pais != "Mexico":
            self.AgregarCuentas.Consulado.hide()
            self.AgregarCuentas.Cas.hide()

    def init_table(self):
        if self.tipo == 1:
            self.cuentas_activas = self.db.get_cuentas_activas(self.pais)
        else:
            self.cuentas_activas = self.db.get_cuentas_falsas_activas(self.pais)
        # Crear el modelo de tabla
        self.model = QStandardItemModel()

        if not self.cuentas_activas:
            self.model.setHorizontalHeaderLabels(['Mensaje'])
            row = [
                QStandardItem("Por favor agregue cuentas para que el bot funcione.")
            ]
            self.model.appendRow(row)
        else:
            if self.tipo == 1 and self.pais == "Mexico":
                titles = ['Email', 'Password', 'Pais', 'Consulado 1', 'Consulado 2', 'Acciones']
            else:
                titles = ['Email', 'Password', 'Pais', 'Acciones']

            self.model.setHorizontalHeaderLabels(titles)

            # Rellenar el modelo con los datos
            for cuenta in self.cuentas_activas:
                if self.tipo == 1 and self.pais == "Mexico":
                    row = [
                        QStandardItem(cuenta["email"]),
                        QStandardItem(cuenta['password']),
                        QStandardItem(cuenta['pais']),
                        QStandardItem(cuenta['consulado']),
                        QStandardItem(cuenta['cas']),
                        QStandardItem('')  # Columna para los botones
                    ]
                else:
                    row = [
                        QStandardItem(cuenta["email"]),
                        QStandardItem(cuenta['password']),
                        QStandardItem(cuenta['pais']),
                        QStandardItem('')  # Columna para los botones
                    ]

                # Almacenar el ID en el último item (botones) usando setData
                row[-1].setData(cuenta['id'], Qt.ItemDataRole.UserRole)

                self.model.appendRow(row)

        # Configurar la tabla con el modelo
        self.AgregarCuentas.TablaCuentas.setModel(self.model)
        self.AgregarCuentas.TablaCuentas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.AgregarCuentas.TablaCuentas.horizontalHeader().setSectionResizeMode(self.model.columnCount()-1, QHeaderView.ResizeMode.Fixed)
        self.AgregarCuentas.TablaCuentas.setColumnWidth(self.model.columnCount()-1, 60)  # Ajusta este valor según necesites

        # Configurar el delegado para los botones
        button_delegate = ButtonDelegate(self.AgregarCuentas.TablaCuentas)
        button_delegate.edit_clicked.connect(self.editar_cuenta)
        button_delegate.delete_clicked.connect(self.eliminar_cuenta)
        self.AgregarCuentas.TablaCuentas.setItemDelegateForColumn(self.model.columnCount()-1, button_delegate)

        # Configurar el delegado para los ComboBox
        combo_delegate = ComboBoxDelegate()
        self.AgregarCuentas.TablaCuentas.setItemDelegateForColumn(2, combo_delegate)  # País
        if self.tipo == 1 and self.pais == "Mexico":
            self.AgregarCuentas.TablaCuentas.setItemDelegateForColumn(3, combo_delegate)  # Consulado 1
            self.AgregarCuentas.TablaCuentas.setItemDelegateForColumn(4, combo_delegate)  # Consulado 2

    def editar_cuenta(self, id, row):
        email = self.model.item(row, 0).text()
        password = self.model.item(row, 1).text()
        pais = self.model.item(row, 2).text()
        
        if self.tipo == 1:
            if self.pais == "Mexico":
                consulado = self.model.item(row, 3).text()
                cas = self.model.item(row, 4).text()
                cuenta = CuentaSchema(id=id, pais=pais, email=email, password=password, consulado=consulado, cas=cas, status=1)
            else:
                cuenta = CuentaSchema(id=id, pais=pais, email=email, password=password, status=1)
            self.db.update_cuenta(cuenta)
        else:
            cuenta = CuentaFalsaSchema(id=id, pais=pais, email=email, password=password, status=1)
            self.db.update_cuenta_falsa(cuenta)
        
        self.init_table()

    def eliminar_cuenta(self, id, row):
        if self.tipo == 1:
            self.db.delete_cuenta(id)
        else:
            self.db.delete_cuenta_falsa(id)
        self.init_table()

    def AgregarCuenta(self):
        email = self.AgregarCuentas.AddEmail.text()
        password = self.AgregarCuentas.AddPassword.text()
        patron_email = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not email and not password:
            self.AgregarCuentas.ErrorMensaje.setText('Debe ingresar datos en los campos requeridos.')
        elif not email:
            self.AgregarCuentas.ErrorMensaje.setText('Email requerido.')
        elif not password:
            self.AgregarCuentas.ErrorMensaje.setText('Password requerido.')
        else:
            if re.match(patron_email, email):
                if self.tipo == 1:
                    if self.pais == "Mexico":
                        consulado = self.AgregarCuentas.Consulado.currentText()
                        cas = self.AgregarCuentas.Cas.currentText()
                        if consulado == 'Consulado 1':
                            self.AgregarCuentas.ErrorMensaje.setText('Debe elegir un valor para Consulado 1')
                        elif cas == 'Consulado 2':
                            self.AgregarCuentas.ErrorMensaje.setText('Debe elegir un valor para Consulado 2')
                        else:
                            Cuenta = CuentaSchema(pais=self.pais,email=email, password=password, consulado=consulado, cas=cas, status=1)
                            self.db.insert_cuenta(Cuenta)
                            self.AgregarCuentas.AddEmail.clear()
                            self.AgregarCuentas.AddPassword.clear()
                            self.init_table()
                            self.AgregarCuentas.ErrorMensaje.setText('')
                    else:
                        Cuenta = CuentaSchema(pais=self.pais,email=email, password=password, status=1)
                        self.db.insert_cuenta(Cuenta)
                        self.AgregarCuentas.AddEmail.clear()
                        self.AgregarCuentas.AddPassword.clear()
                        self.init_table()
                        self.AgregarCuentas.ErrorMensaje.setText('')
                else:
                    Cuenta = CuentaFalsaSchema(pais=self.pais,email=email, password=password, status=1)
                    self.db.insert_cuenta_falsa(Cuenta)
                    self.AgregarCuentas.AddEmail.clear()
                    self.AgregarCuentas.AddPassword.clear()
                    self.init_table()
                    self.AgregarCuentas.ErrorMensaje.setText('')
            else:
                self.AgregarCuentas.ErrorMensaje.setText('Correo electronico no valido.')