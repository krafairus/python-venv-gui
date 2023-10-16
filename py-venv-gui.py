import os
import sys
import subprocess
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit, QPushButton,
                             QListWidget, QListWidgetItem, QWidget, QToolBar, QAction, QHBoxLayout,
                             QMessageBox, QStackedWidget, QToolButton, QInputDialog)
from PyQt5.QtGui import (QIcon, QMovie, QPixmap)
from PyQt5.QtCore import Qt
import tempfile

DIRECTORIO_ENV = os.path.expanduser('~/.env-creator-ui').rstrip('/')
ARCHIVO_REGISTRO = os.path.join(DIRECTORIO_ENV, 'registro_env.txt')
ARCHIVO_CONFIG = os.path.join(DIRECTORIO_ENV, 'config.json')


class CreadorEntornos(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowIcon(QIcon("./icons/icon.svg"))
        self.icono_eliminar = "./icons/delete.png"
        self.icono_entornos = "./icons/list.png"
        self.icono_abrir_directorio = "./icons/folder.png"
        self.icono_acerca_de = "./icons/info.png"

        self.cargar_config()
        self.iniciar_ui()
        self.cargar_entornos_desde_registro()

    def cargar_config(self):
        if os.path.exists(ARCHIVO_CONFIG):
            with open(ARCHIVO_CONFIG, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {"favoritos": []}

    def iniciar_ui(self):
        self.setWindowTitle("Administrador De Entornos Virtuales (py)")
        self.resize(400, 400)

        self.toolbar = QToolBar(self)
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)

        list_action = QAction(QIcon(self.icono_entornos), "Entornos", self)
        list_action.triggered.connect(self.mostrar_pagina_entornos)
        self.toolbar.addAction(list_action)

        about_action = QAction(QIcon(self.icono_acerca_de), "Acerca de", self)
        about_action.triggered.connect(self.mostrar_acerca_de)
        self.toolbar.addAction(about_action)

        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

        self.central_widget = QWidget()
        main_layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.entornos_page = QWidget()
        entornos_layout = QVBoxLayout(self.entornos_page)
        main_hbox = QHBoxLayout()

        self.lista_entornos = QListWidget()
        main_hbox.addWidget(self.lista_entornos)
        self.side_bar_layout = QVBoxLayout()

        self.btn_eliminar = QToolButton(self)
        self.btn_eliminar.setIcon(QIcon(self.icono_eliminar))
        self.btn_eliminar.clicked.connect(self.eliminar_entorno)
        self.side_bar_layout.addWidget(self.btn_eliminar)
        self.btn_eliminar.hide()

        self.btn_abrir_directorio = QToolButton(self)
        self.btn_abrir_directorio.setIcon(QIcon(self.icono_abrir_directorio))
        self.btn_abrir_directorio.clicked.connect(self.abrir_directorio_entorno)
        self.side_bar_layout.addWidget(self.btn_abrir_directorio)
        self.btn_abrir_directorio.hide()

        self.btn_iniciar_terminal = QToolButton(self)
        self.btn_iniciar_terminal.setIcon(QIcon("./icons/terminal.png"))
        self.btn_iniciar_terminal.clicked.connect(self.iniciar_entorno_terminal)
        self.side_bar_layout.addWidget(self.btn_iniciar_terminal)
        self.btn_iniciar_terminal.hide()

        main_hbox.addLayout(self.side_bar_layout)
        entornos_layout.addLayout(main_hbox)

        self.entrada_nombre_entorno = QLineEdit()
        self.entrada_nombre_entorno.setPlaceholderText("Nombre del entorno")
        entornos_layout.addWidget(self.entrada_nombre_entorno)

        self.boton_crear = QPushButton("Crear entorno")
        self.boton_crear.clicked.connect(self.crear_entorno)
        entornos_layout.addWidget(self.boton_crear)

        self.entornos_page.setLayout(entornos_layout)
        self.stacked_widget.addWidget(self.entornos_page)

        self.lista_entornos.itemSelectionChanged.connect(self.update_side_bar_buttons)

    def update_side_bar_buttons(self):
        if self.lista_entornos.selectedItems():
            self.btn_eliminar.show()
            self.btn_abrir_directorio.show()
            self.btn_iniciar_terminal.show()
        else:
            self.btn_eliminar.hide()
            self.btn_abrir_directorio.hide()
            self.btn_iniciar_terminal.hide()

    def cargar_entornos_desde_registro(self):
        if os.path.exists(ARCHIVO_REGISTRO):
            with open(ARCHIVO_REGISTRO, "r") as log_file:
                nombres_entornos = log_file.readlines()

            for nombre_entorno in nombres_entornos:
                nombre_entorno = nombre_entorno.strip()
                custom_widget = QWidget()
                custom_layout = QHBoxLayout(custom_widget)

                item = QListWidgetItem()
                entorno_label = QLabel(nombre_entorno)

                custom_layout.addWidget(entorno_label)

                self.lista_entornos.addItem(item)
                self.lista_entornos.setItemWidget(item, custom_widget)

    def crear_entorno(self):
        nombre_entorno = self.entrada_nombre_entorno.text()
        if not nombre_entorno:
            QMessageBox.warning(self, "Campos faltantes", "Por favor, proporciona un nombre para el entorno.")
            return

        ruta_entorno = os.path.join(DIRECTORIO_ENV, nombre_entorno)
        if not os.path.exists(ruta_entorno):
            os.makedirs(ruta_entorno)

        resultado = subprocess.run(['python', '-m', 'venv', ruta_entorno])

        if resultado.returncode == 0:
            with open(ARCHIVO_REGISTRO, "a") as log_file:
                log_file.write(nombre_entorno + "\n")

            # Crear un widget personalizado para el nuevo entorno
            custom_widget = QWidget()
            custom_layout = QHBoxLayout(custom_widget)
            entorno_label = QLabel(nombre_entorno)
            custom_layout.addWidget(entorno_label)

            item = QListWidgetItem()
            self.lista_entornos.addItem(item)
            self.lista_entornos.setItemWidget(item, custom_widget)
        else:
            QMessageBox.warning(self, "Error", "Error al crear el entorno. Verifica si el módulo 'venv' está instalado.")

    def mostrar_pagina_entornos(self):
        self.stacked_widget.setCurrentWidget(self.entornos_page)

    def eliminar_entorno(self):
        item_actual = self.lista_entornos.currentItem()
        if item_actual:
            # Obtener el widget (QLabel) asociado al elemento y luego su texto
            custom_widget = self.lista_entornos.itemWidget(item_actual)
            if custom_widget:
                children = custom_widget.findChildren(QLabel)
                if children and isinstance(children[0], QLabel):
                    nombre_entorno = children[0].text()
                    respuesta = QMessageBox.question(self, "Eliminar entorno", f"¿Estás seguro de que quieres eliminar el entorno '{nombre_entorno}'?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if respuesta == QMessageBox.Yes:
                        ruta_entorno = os.path.join(DIRECTORIO_ENV, nombre_entorno)
                        subprocess.run(['rm', '-rf', ruta_entorno])

                        if os.path.exists(ARCHIVO_REGISTRO):
                            with open(ARCHIVO_REGISTRO, "r") as log_file:
                                lineas = log_file.readlines()
                            with open(ARCHIVO_REGISTRO, "w") as log_file:
                                for linea in lineas:
                                    if linea.strip() != nombre_entorno:
                                        log_file.write(linea)

                            # Elimina el ítem de la lista visual
                            row = self.lista_entornos.row(item_actual)
                            self.lista_entornos.takeItem(row)

    def seleccionar_terminal(self):
        terminales = [
            ("Deepin Terminal", "deepin-terminal"),
            ("Konsole (KDE)", "konsole"),
            ("GNOME Terminal", "gnome-terminal"),
            ("XFCE Terminal", "xfce4-terminal"),
        ]

        items, ok = QInputDialog.getItem(self, "Seleccionar Terminal", "Elige una terminal:", [terminal[0] for terminal in terminales], 0, False)

        if ok and items:
            terminal_elegido = next((terminal[1] for terminal in terminales if terminal[0] == items), None)
            return terminal_elegido
        return None

    def abrir_directorio_entorno(self):
        item_actual = self.lista_entornos.currentItem()
        if item_actual:
            # Obtener el widget (QLabel) asociado al elemento y luego su texto
            custom_widget = self.lista_entornos.itemWidget(item_actual)
            if custom_widget:
                children = custom_widget.findChildren(QLabel)
                if children and isinstance(children[0], QLabel):
                    nombre_entorno = children[0].text()
                    ruta_entorno = os.path.join(DIRECTORIO_ENV, nombre_entorno)
                    subprocess.run(['xdg-open', ruta_entorno])

    def iniciar_entorno_terminal(self):
        item_actual = self.lista_entornos.currentItem()
        if item_actual:
            # Obtener el widget (QLabel) asociado al elemento y luego su texto
            custom_widget = self.lista_entornos.itemWidget(item_actual)
            if custom_widget:
                children = custom_widget.findChildren(QLabel)
                if children and isinstance(children[0], QLabel):
                    nombre_entorno = children[0].text()

                    print(f"Nombre del entorno seleccionado: {nombre_entorno}")  # Puedes mantener esta línea para verificar
                    ruta_entorno = os.path.join(DIRECTORIO_ENV, nombre_entorno)

                    terminal_seleccionado = self.seleccionar_terminal()
                    if terminal_seleccionado:
                        temp_script_path = "/tmp/activate_temp.sh"

                        with open(temp_script_path, 'w') as temp_script:
                            temp_script.write("#!/bin/bash\n")
                            temp_script.write(f"source {ruta_entorno}/bin/activate\n")
                            temp_script.write(f"echo Se Cargo El Entorno Virtual: {nombre_entorno}\n")
                            temp_script.write(f"\n")
                            temp_script.write("bash\n")  # Esto debería mantener la terminal abierta

                        os.chmod(temp_script_path, 0o755)

                        if terminal_seleccionado == "gnome-terminal":
                            subprocess.Popen([terminal_seleccionado, '--', '/bin/bash', '-i', '-c', temp_script_path])
                        else:
                            subprocess.Popen([terminal_seleccionado, '-e', temp_script_path])

    def mostrar_acerca_de(self):
        mensaje = (
            "Python Venv Gui v1.0\n\n"
            "Desarrollado por krafairus\n\n"
            "Más información en:\n"
            "https://github.com/krafairus/py-venv-gui"
        )

        acerca_de_dialogo = QMessageBox(self)
        acerca_de_dialogo.setWindowTitle("Acerca de Python Venv Gui")
        acerca_de_dialogo.setText(mensaje)

        pixmap = QPixmap("./icons/icon.svg")
        pixmap_scaled = pixmap.scaled(85, 85, Qt.KeepAspectRatio)
        acerca_de_dialogo.setIconPixmap(pixmap_scaled)

        acerca_de_dialogo.exec_()

def main():
    app = QApplication(sys.argv)
    window = CreadorEntornos()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

