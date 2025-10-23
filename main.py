#!/usr/bin/env python3

import os
import sys
import subprocess
import json
import shlex
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QWidget, QHBoxLayout,
    QMessageBox, QStackedWidget, QToolButton, QInputDialog, QDialog,
    QListWidget, QComboBox, QDialogButtonBox
)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt, QSize


# Obtener el directorio base donde está el script
if getattr(sys, 'frozen', False):
    # Si está empaquetado (PyInstaller)
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Si está ejecutándose desde el código fuente
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Directorios y archivos
RESOURCES_DIR = os.path.join(BASE_DIR, 'resources')
LANGS_DIR = os.path.join(BASE_DIR, 'langs')
DIRECTORIO_ENV = os.path.expanduser('~/.env-creator-ui').rstrip('/')
ARCHIVO_REGISTRO = os.path.join(DIRECTORIO_ENV, 'registro_env.txt')
ARCHIVO_CONFIG = os.path.join(DIRECTORIO_ENV, 'config.json')

# Definición de terminales disponibles
system_terminals = {
    "GNOME Terminal": [
        "/usr/bin/gnome-terminal",
        "/usr/local/bin/gnome-terminal"
    ],
    "Deepin Terminal": [
        "/usr/bin/deepin-terminal",
        "/usr/local/bin/deepin-terminal"
    ],
    "Konsole (KDE)": [
        "/usr/bin/konsole",
        "/usr/local/bin/konsole"
    ],
    "XFCE Terminal": [
        "/usr/bin/xfce4-terminal",
        "/usr/local/bin/xfce4-terminal"
    ],
    "Kitty": [
        "/usr/bin/kitty",
        "/usr/local/bin/kitty"
    ],
    "Alacritty": [
        "/usr/bin/alacritty",
        "/usr/local/bin/alacritty"
    ],
    "Terminator": [
        "/usr/bin/terminator",
        "/usr/local/bin/terminator"
    ],
    "Tilix": [
        "/usr/bin/tilix",
        "/usr/local/bin/tilix"
    ],
    "Rxvt": [
        "/usr/bin/rxvt",
        "/usr/bin/urxvt",
        "/usr/local/bin/rxvt",
        "/usr/local/bin/urxvt"
    ],
    "XTerm": [
        "/usr/bin/xterm",
        "/usr/local/bin/xterm"
    ]
}

# Comandos específicos para cada terminal
terminal_commands = {
    "GNOME Terminal": "-- bash -c 'bash --init-file {script}'",
    "Deepin Terminal": "-e 'bash --init-file {script}'",
    "Konsole (KDE)": "-e 'bash --init-file {script}'",
    "XFCE Terminal": "-x bash -c 'bash --init-file {script}'",
    "Kitty": "bash -c 'bash --init-file {script}'",
    "Alacritty": "-e bash -c 'bash --init-file {script}'",
    "Terminator": "-x bash -c 'bash --init-file {script}'",
    "Tilix": "-e 'bash --init-file {script}'",
    "Rxvt": "-e bash --init-file {script}",
    "XTerm": "-e bash --init-file {script}",
    "Otro": "{custom_command}"
}


class ConfigDialog(QDialog):
    def __init__(self, parent=None, config=None, strings=None):
        super().__init__(parent)
        self.parent = parent
        self.config = config
        self.strings = strings
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle(self.strings["config_title"])
        self.setFixedSize(500, 400)

        layout = QVBoxLayout(self)

        # Selector de idioma
        lang_layout = QHBoxLayout()
        lang_label = QLabel(self.strings["language"] + ":")
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Español", "es")
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("Português", "pt")
        
        # Establecer idioma actual
        current_lang = self.config.get('idioma', 'es')
        index = self.lang_combo.findData(current_lang)
        if index >= 0:
            self.lang_combo.setCurrentIndex(index)
        
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)

        # Terminales personalizadas
        layout.addWidget(QLabel(self.strings["custom_terminals"] + ":"))
        self.terminals_list = QListWidget()
        self.actualizar_lista_terminales()
        layout.addWidget(self.terminals_list)

        # Botones para terminales
        terminals_buttons_layout = QHBoxLayout()
        self.btn_eliminar_terminal = QPushButton(self.strings["delete_selected"])
        self.btn_eliminar_terminal.clicked.connect(self.eliminar_terminal_seleccionada)
        terminals_buttons_layout.addWidget(self.btn_eliminar_terminal)
        layout.addLayout(terminals_buttons_layout)

        # Botones de diálogo
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def actualizar_lista_terminales(self):
        self.terminals_list.clear()
        terminales_personalizados = self.config.get('terminales_personalizados', {})
        for nombre, datos in terminales_personalizados.items():
            item_text = f"{nombre} - {datos['ruta']}"
            self.terminals_list.addItem(item_text)

    def eliminar_terminal_seleccionada(self):
        current_item = self.terminals_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, self.strings["warning"], self.strings["select_terminal_to_delete"])
            return

        item_text = current_item.text()
        nombre_terminal = item_text.split(" - ")[0]

        respuesta = QMessageBox.question(
            self,
            self.strings["confirm_delete"],
            f"{self.strings['confirm_delete_terminal']} '{nombre_terminal}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            if 'terminales_personalizados' in self.config:
                if nombre_terminal in self.config['terminales_personalizados']:
                    del self.config['terminales_personalizados'][nombre_terminal]
                    # Guardar los cambios en la configuración
                    self.parent.guardar_config()
                    self.actualizar_lista_terminales()
                    QMessageBox.information(self, self.strings["success"], self.strings["terminal_deleted"])

    def get_selected_language(self):
        return self.lang_combo.currentData()


class CreadorEntornos(QMainWindow):
    def __init__(self):
        super().__init__()

        # Configurar rutas de íconos
        self.setup_icons()
        
        self.cargar_config()
        self.cargar_idioma()
        self.iniciar_ui()
        self.cargar_entornos_desde_registro()

    def setup_icons(self):
        """Configura las rutas de los íconos"""
        self.icono_app = os.path.join(RESOURCES_DIR, 'icon.svg')
        self.icono_eliminar = os.path.join(RESOURCES_DIR, 'delete.png')
        self.icono_abrir_directorio = os.path.join(RESOURCES_DIR, 'folder.png')
        self.icono_acerca_de = os.path.join(RESOURCES_DIR, 'info.png')
        self.icono_abrir_terminal = os.path.join(RESOURCES_DIR, 'open.png')
        self.icono_configuracion = os.path.join(RESOURCES_DIR, 'settings.png')
        
        # Establecer ícono de la aplicación
        if os.path.exists(self.icono_app):
            self.setWindowIcon(QIcon(self.icono_app))

    def cargar_config(self):
        """Carga la configuración desde el archivo JSON"""
        config_default = {
            "ultima_terminal": None,
            "terminales_personalizados": {},
            "idioma": "es"
        }
        
        if os.path.exists(ARCHIVO_CONFIG):
            try:
                with open(ARCHIVO_CONFIG, 'r') as f:
                    loaded_config = json.load(f)
                    # Combinar con valores por defecto
                    self.config = {**config_default, **loaded_config}
            except:
                self.config = config_default
        else:
            self.config = config_default

    def cargar_idioma(self):
        """Carga las cadenas de texto según el idioma seleccionado"""
        idioma = self.config.get('idioma', 'es')
        archivo_idioma = os.path.join(LANGS_DIR, f"{idioma}.json")
        
        # Textos por defecto en español
        self.strings = {
            "app_title": "Entornos Virtuales (py)",
            "create_env": "Crear entorno",
            "env_name_placeholder": "Nombre del entorno",
            "delete_selected": "Eliminar seleccionado",
            "open_directory": "Abrir directorio",
            "open_terminal": "Abrir terminal",
            "config_title": "Configuración",
            "language": "Idioma",
            "custom_terminals": "Terminales personalizadas",
            "delete_selected": "Eliminar seleccionada",
            "warning": "Advertencia",
            "select_terminal_to_delete": "Selecciona una terminal para eliminar",
            "confirm_delete": "Confirmar eliminación",
            "confirm_delete_terminal": "¿Estás seguro de que quieres eliminar la terminal",
            "success": "Éxito",
            "terminal_deleted": "Terminal eliminada correctamente",
            "select_terminal": "Seleccionar Terminal",
            "choose_terminal": "Elige una terminal:",
            "custom_terminal": "Terminal Personalizado",
            "terminal_name": "Nombre para esta terminal:",
            "terminal_path": "Ruta del ejecutable:",
            "custom_command": "Comando personalizado (usa {script} para el script):",
            "executable_not_found": "Ejecutable no encontrado",
            "continue_anyway": "La ruta no existe. ¿Deseas continuar de todos modos?",
            "missing_fields": "Campos faltantes",
            "provide_name": "Por favor, proporciona un nombre para el entorno.",
            "env_created": "Entorno creado correctamente.",
            "error": "Error",
            "venv_error": "Error al crear el entorno. Verifica si el módulo 'venv' está instalado.",
            "delete_env": "Eliminar entorno",
            "confirm_delete_env": "¿Estás seguro de que quieres eliminar el entorno",
            "about_title": "Acerca de Python Venv Gui",
            "about_content": "Python Venv Gui v1.5.5\n\nDesarrollado por krafairus\n\nMás información en:\nhttps://github.com/krafairus/py-venv-gui",
            "close": "Cerrar",
            "restart_for_changes": "Los cambios de idioma requieren reiniciar la aplicación",
            "terminal_error": "No se pudo abrir la terminal"
        }
        
        # Intentar cargar el archivo de idioma
        if os.path.exists(archivo_idioma):
            try:
                with open(archivo_idioma, 'r', encoding='utf-8') as f:
                    loaded_strings = json.load(f)
                    self.strings.update(loaded_strings)
            except Exception as e:
                print(f"Error cargando idioma: {e}")

    def guardar_config(self):
        """Guarda la configuración en el archivo JSON"""
        os.makedirs(os.path.dirname(ARCHIVO_CONFIG), exist_ok=True)
        with open(ARCHIVO_CONFIG, 'w') as f:
            json.dump(self.config, f, indent=4)

    def detectar_terminales_disponibles(self):
        """Detecta qué terminales están disponibles en el sistema"""
        terminales_disponibles = []
        
        # Detectar terminales del sistema
        for terminal, paths in system_terminals.items():
            for path in paths:
                if os.path.exists(path):
                    terminales_disponibles.append({
                        'nombre': terminal,
                        'tipo': 'sistema',
                        'ruta': path,
                        'comando': terminal_commands[terminal]
                    })
                    break
        
        # Añadir terminales personalizados guardados
        for nombre, datos in self.config.get('terminales_personalizados', {}).items():
            terminales_disponibles.append({
                'nombre': nombre,
                'tipo': 'personalizado',
                'ruta': datos['ruta'],
                'comando': datos.get('comando', terminal_commands['Otro'])
            })
        
        # Siempre añadir la opción "Otro"
        terminales_disponibles.append({
            'nombre': self.strings["custom_terminal"] + "...",
            'tipo': 'otro',
            'ruta': '',
            'comando': terminal_commands['Otro']
        })
        
        return terminales_disponibles

    def seleccionar_terminal(self):
        """Muestra un diálogo para seleccionar terminal con las opciones disponibles"""
        terminales_disponibles = self.detectar_terminales_disponibles()
        
        # Crear lista de nombres para el diálogo
        nombres_terminales = [f"{term['nombre']} ({term['tipo']})" for term in terminales_disponibles]
        
        # Si hay una última terminal usada, seleccionarla por defecto
        default_index = 0
        if self.config.get('ultima_terminal'):
            ultima_nombre = self.config['ultima_terminal']['nombre']
            for i, term in enumerate(terminales_disponibles):
                if term['nombre'] == ultima_nombre:
                    default_index = i
                    break
        
        items, ok = QInputDialog.getItem(
            self, 
            self.strings["select_terminal"], 
            self.strings["choose_terminal"], 
            nombres_terminales, 
            default_index, 
            False
        )

        if ok and items:
            # Encontrar la terminal seleccionada
            selected_index = nombres_terminales.index(items)
            terminal_seleccionada = terminales_disponibles[selected_index]
            
            # Si selecciona "Otro...", pedir detalles
            if terminal_seleccionada['nombre'] == self.strings["custom_terminal"] + "...":
                terminal_seleccionada = self.configurar_terminal_personalizado()
            
            if terminal_seleccionada:
                # Guardar como última terminal usada
                self.config['ultima_terminal'] = {
                    'nombre': terminal_seleccionada['nombre'],
                    'ruta': terminal_seleccionada['ruta'],
                    'comando': terminal_seleccionada['comando']
                }
                self.guardar_config()
                
                return terminal_seleccionada
        
        return None

    def configurar_terminal_personalizado(self):
        """Configura una terminal personalizada"""
        # Pedir nombre
        nombre, ok = QInputDialog.getText(
            self, 
            self.strings["custom_terminal"], 
            self.strings["terminal_name"]
        )
        if not ok or not nombre:
            return None
        
        # Pedir ruta del ejecutable
        ruta, ok = QInputDialog.getText(
            self, 
            self.strings["custom_terminal"], 
            self.strings["terminal_path"],
            text="/usr/bin/"
        )
        if not ok or not ruta:
            return None
        
        # Verificar si el ejecutable existe
        if not os.path.exists(ruta):
            respuesta = QMessageBox.question(
                self,
                self.strings["executable_not_found"],
                self.strings["continue_anyway"],
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if respuesta == QMessageBox.StandardButton.No:
                return None
        
        # Pedir comando personalizado
        comando, ok = QInputDialog.getText(
            self,
            self.strings["custom_terminal"],
            self.strings["custom_command"],
            text=f"{ruta} -e 'bash --init-file {{script}}'"
        )
        if not ok or not comando:
            comando = terminal_commands['Otro']
        
        # Guardar en configuración
        if 'terminales_personalizados' not in self.config:
            self.config['terminales_personalizados'] = {}
        
        self.config['terminales_personalizados'][nombre] = {
            'ruta': ruta,
            'comando': comando
        }
        self.guardar_config()
        
        return {
            'nombre': nombre,
            'tipo': 'personalizado',
            'ruta': ruta,
            'comando': comando
        }

    def abrir_configuracion(self):
        """Abre el diálogo de configuración"""
        dialog = ConfigDialog(self, self.config, self.strings)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Actualizar idioma si cambió
            nuevo_idioma = dialog.get_selected_language()
            if nuevo_idioma != self.config.get('idioma'):
                self.config['idioma'] = nuevo_idioma
                self.guardar_config()
                self.cargar_idioma()
                self.actualizar_ui_idioma()
                QMessageBox.information(self, self.strings["success"], self.strings["restart_for_changes"])

    def actualizar_ui_idioma(self):
        """Actualiza la interfaz con el nuevo idioma"""
        self.setWindowTitle(self.strings["app_title"])
        self.entrada_nombre_entorno.setPlaceholderText(self.strings["env_name_placeholder"])
        self.boton_crear.setText(self.strings["create_env"])
        self.btn_eliminar.setToolTip(self.strings["delete_selected"])
        self.btn_abrir_directorio.setToolTip(self.strings["open_directory"])
        self.btn_iniciar_terminal.setToolTip(self.strings["open_terminal"])

    def iniciar_ui(self):
        self.setWindowTitle(self.strings["app_title"])
        self.resize(400, 400)

        self.dragging = False 

        # Eliminar la barra de título del sistema
        self.setWindowFlags(Qt.FramelessWindowHint)

        # Crear la barra de título personalizada
        self.crear_barra_titulo()

        self.central_widget = QWidget()
        main_layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)

        self.stacked_widget = QStackedWidget()
        main_layout.addWidget(self.stacked_widget)

        self.entornos_page = QWidget()
        entornos_layout = QVBoxLayout(self.entornos_page)
        main_hbox = QHBoxLayout()

        self.lista_entornos = QListWidget()
        self.lista_entornos.setStyleSheet("""
            QListWidget {
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                background-color: #333;
                color: #BEBEBE;
            }
            QListWidget::item {
                padding: 5px;
                min-height: 30px;
                font-family: 'Cantarell', sans-serif;
                font-size: 14pt;
            }
            QListWidget::item:selected {
                border: 1px solid #555;
                background-color: #3e3e3e;
            }
        """)
        self.lista_entornos.setToolTipDuration(3000)
        main_hbox.addWidget(self.lista_entornos)

        self.side_bar_layout = QVBoxLayout()

        self.btn_eliminar = QToolButton(self)
        self.btn_eliminar.setIcon(QIcon(self.icono_eliminar))
        self.btn_eliminar.setIconSize(QSize(25, 25))
        self.btn_eliminar.clicked.connect(self.eliminar_entorno)
        self.btn_eliminar.setToolTip(self.strings["delete_selected"])
        self.side_bar_layout.addWidget(self.btn_eliminar)
        self.btn_eliminar.hide()

        self.btn_abrir_directorio = QToolButton(self)
        self.btn_abrir_directorio.setIcon(QIcon(self.icono_abrir_directorio))
        self.btn_abrir_directorio.setIconSize(QSize(25, 25))
        self.btn_abrir_directorio.clicked.connect(self.abrir_directorio_entorno)
        self.btn_abrir_directorio.setToolTip(self.strings["open_directory"])
        self.side_bar_layout.addWidget(self.btn_abrir_directorio)
        self.btn_abrir_directorio.hide()

        self.btn_iniciar_terminal = QToolButton(self)
        self.btn_iniciar_terminal.setIcon(QIcon(self.icono_abrir_terminal))
        self.btn_iniciar_terminal.setIconSize(QSize(25, 25))
        self.btn_iniciar_terminal.clicked.connect(self.iniciar_entorno_terminal)
        self.btn_iniciar_terminal.setToolTip(self.strings["open_terminal"])
        self.side_bar_layout.addWidget(self.btn_iniciar_terminal)
        self.btn_iniciar_terminal.hide()

        main_hbox.addLayout(self.side_bar_layout)
        entornos_layout.addLayout(main_hbox)

        self.entrada_nombre_entorno = QLineEdit()
        self.entrada_nombre_entorno.setPlaceholderText(self.strings["env_name_placeholder"])
        self.entrada_nombre_entorno.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                background-color: #333;
                color: #BEBEBE;
            }
        """)
        entornos_layout.addWidget(self.entrada_nombre_entorno)

        self.boton_crear = QPushButton(self.strings["create_env"])
        self.boton_crear.clicked.connect(self.crear_entorno)
        self.boton_crear.setStyleSheet("""
            QPushButton {
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                background-color: #444;
                color: #BEBEBE;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        entornos_layout.addWidget(self.boton_crear)

        self.entornos_page.setLayout(entornos_layout)
        self.stacked_widget.addWidget(self.entornos_page)

        self.lista_entornos.itemSelectionChanged.connect(self.update_side_bar_buttons)

    def crear_barra_titulo(self):
        """Crea una barra de título personalizada."""
        self.title_bar = QWidget(self)
        self.title_bar.setFixedHeight(40)
        self.title_bar.setObjectName("title_bar")
        self.title_bar.setStyleSheet("background-color: #262626; border-bottom: 1px solid #333333;")

        # Layout horizontal para la barra de título
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        title_layout.setSpacing(0)

        # Botón "Configuración"
        config_button = QPushButton()
        config_button.setIcon(QIcon(self.icono_configuracion))
        config_button.setIconSize(QSize(25, 25))
        config_button.setToolTip("Configuración")
        config_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4A4A4A;
            }
        """)
        config_button.clicked.connect(self.abrir_configuracion)
        title_layout.addWidget(config_button)

        # Botón "Acerca de"
        about_button = QPushButton()
        about_button.setIcon(QIcon(self.icono_acerca_de))
        about_button.setIconSize(QSize(25, 25))
        about_button.setToolTip("Ver información de la app")
        about_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4A4A4A;
            }
        """)
        about_button.clicked.connect(self.mostrar_acerca_de)
        title_layout.addWidget(about_button)

        # Espacio flexible
        title_layout.addStretch()

        # Botón de minimizar
        minimize_button = QPushButton("─")
        minimize_button.setFixedSize(40, 40)
        minimize_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #BEBEBE;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                background-color: #4A4A4A;
            }
            QPushButton:pressed {
                background-color: #323232;
            }
        """)
        minimize_button.clicked.connect(self.showMinimized)
        title_layout.addWidget(minimize_button)

        # Botón de cerrar
        close_button = QPushButton("✕")
        close_button.setFixedSize(40, 40)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #BEBEBE;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                background-color: #4A4A4A;
            }
            QPushButton:pressed {
                background-color: #323232;
            }
        """)
        close_button.clicked.connect(self.close)
        title_layout.addWidget(close_button)

        # Establecer la barra de título personalizada
        self.setMenuWidget(self.title_bar)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.title_bar.underMouse():
            self.dragging = True
            self.offset = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if self.dragging:
            self.move(event.globalPosition().toPoint() - self.offset)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and self.title_bar.underMouse():
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()

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
            QMessageBox.warning(self, self.strings["missing_fields"], self.strings["provide_name"])
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
            
            # Limpiar el campo de entrada
            self.entrada_nombre_entorno.clear()
            
            QMessageBox.information(self, self.strings["success"], f"{self.strings['env_created']} '{nombre_entorno}'")
        else:
            QMessageBox.warning(self, self.strings["error"], self.strings["venv_error"])

    def eliminar_entorno(self):
        item_actual = self.lista_entornos.currentItem()
        if item_actual:
            # Obtener el widget (QLabel) asociado al elemento y luego su texto
            custom_widget = self.lista_entornos.itemWidget(item_actual)
            if custom_widget:
                children = custom_widget.findChildren(QLabel)
                if children and isinstance(children[0], QLabel):
                    nombre_entorno = children[0].text()
                    respuesta = QMessageBox.question(self, self.strings["delete_env"], f"{self.strings['confirm_delete_env']} '{nombre_entorno}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                    if respuesta == QMessageBox.StandardButton.Yes:
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

                    print(f"Nombre del entorno seleccionado: {nombre_entorno}")
                    ruta_entorno = os.path.join(DIRECTORIO_ENV, nombre_entorno)

                    terminal_seleccionada = self.seleccionar_terminal()
                    if terminal_seleccionada:
                        # Script para activar el entorno
                        temp_script_path = "/tmp/activate_venv.sh"

                        with open(temp_script_path, 'w') as temp_script:
                            temp_script.write("#!/bin/bash\n")
                            temp_script.write(f"source \"{ruta_entorno}/bin/activate\"\n")
                            temp_script.write(f"echo \"Entorno virtual activado: {nombre_entorno}\"\n")
                            temp_script.write(f"echo \"Directorio: {ruta_entorno}\"\n")
                            temp_script.write(f"echo \"\"\n")
                            # Mantener la sesión interactiva
                            temp_script.write("exec bash\n")

                        os.chmod(temp_script_path, 0o755)

                        try:
                            # Construir el comando según la terminal seleccionada
                            comando_final = terminal_seleccionada['comando'].format(script=temp_script_path)
                            
                            # Usar el método original que funcionaba
                            if terminal_seleccionada['tipo'] == 'sistema':
                                # Para terminales del sistema, usar el método que funcionaba antes
                                if terminal_seleccionada['nombre'] == "GNOME Terminal":
                                    subprocess.Popen([terminal_seleccionada['ruta'], '--', 'bash', '-c', f'bash --init-file {temp_script_path}'])
                                elif terminal_seleccionada['nombre'] == "Deepin Terminal":
                                    subprocess.Popen([terminal_seleccionada['ruta'], '-e', f'bash --init-file {temp_script_path}'])
                                elif terminal_seleccionada['nombre'] == "Konsole (KDE)":
                                    subprocess.Popen([terminal_seleccionada['ruta'], '-e', f'bash --init-file {temp_script_path}'])
                                elif terminal_seleccionada['nombre'] == "XFCE Terminal":
                                    subprocess.Popen([terminal_seleccionada['ruta'], '-x', 'bash', '-c', f'bash --init-file {temp_script_path}'])
                                elif terminal_seleccionada['nombre'] == "Kitty":
                                    subprocess.Popen([terminal_seleccionada['ruta'], 'bash', '-c', f'bash --init-file {temp_script_path}'])
                                elif terminal_seleccionada['nombre'] == "Alacritty":
                                    subprocess.Popen([terminal_seleccionada['ruta'], '-e', 'bash', '-c', f'bash --init-file {temp_script_path}'])
                                elif terminal_seleccionada['nombre'] == "Terminator":
                                    subprocess.Popen([terminal_seleccionada['ruta'], '-x', 'bash', '-c', f'bash --init-file {temp_script_path}'])
                                elif terminal_seleccionada['nombre'] == "Tilix":
                                    subprocess.Popen([terminal_seleccionada['ruta'], '-e', f'bash --init-file {temp_script_path}'])
                                elif terminal_seleccionada['nombre'] == "Rxvt":
                                    subprocess.Popen([terminal_seleccionada['ruta'], '-e', f'bash --init-file {temp_script_path}'])
                                elif terminal_seleccionada['nombre'] == "XTerm":
                                    subprocess.Popen([terminal_seleccionada['ruta'], '-e', f'bash --init-file {temp_script_path}'])
                                else:
                                    # Método genérico para otras terminales del sistema
                                    subprocess.Popen([terminal_seleccionada['ruta'], '-e', f'bash --init-file {temp_script_path}'])
                            elif terminal_seleccionada['tipo'] == 'personalizado':
                                # Para terminales personalizadas, usar el comando personalizado
                                subprocess.Popen(['bash', '-c', comando_final])
                            else:
                                # Para "Otro", usar el comando como shell
                                subprocess.Popen(['bash', '-c', comando_final])
                                
                        except Exception as e:
                            QMessageBox.critical(self, self.strings["error"], f"{self.strings['terminal_error']}: {str(e)}")

    def mostrar_acerca_de(self):
        # Crear un diálogo personalizado
        acerca_de_dialogo = QDialog(self)
        acerca_de_dialogo.setWindowTitle(self.strings["about_title"])
        acerca_de_dialogo.setFixedSize(400, 200)

        # Layout vertical para el diálogo
        layout = QVBoxLayout(acerca_de_dialogo)

        # Etiqueta con el mensaje
        label = QLabel(self.strings["about_content"])
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        # Botón para cerrar el diálogo
        close_button = QPushButton(self.strings["close"])
        close_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
                background-color: #444;
                color: #BEBEBE;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)
        close_button.clicked.connect(acerca_de_dialogo.close)
        layout.addWidget(close_button)

        # Mostrar el diálogo
        acerca_de_dialogo.exec()


def main():
    app = QApplication(sys.argv)

    # Hoja de estilo para un tema oscuro similar a libadwaita
    app.setStyleSheet("""
        QMainWindow, QWidget {
            background-color: #1c1c1c;
            color: #ffffff;
            font-family: 'Cantarell', sans-serif;
            font-size: 11pt;
        }
        QToolBar {
            background-color: #2e2e2e;
        }
        QToolButton {
            background-color: transparent;
            color: #ffffff;
            border: none;
            padding: 5px;
        }
        QToolButton:hover {
            background-color: #3e3e3e;
        }
        QPushButton {
            background-color: #2e2e2e;
            border: 1px solid #444444;
            padding: 6px 12px;
            color: #ffffff;
        }
        QPushButton:hover {
            background-color: #3e3e3e;
        }
        QLineEdit {
            background-color: #2e2e2e;
            color: #ffffff;
            border: 1px solid #444444;
            padding: 5px;
        }
        QListWidget {
            border: 1px solid #555;
            border-radius: 5px;
            padding: 5px;
            background-color: #333;
            color: #BEBEBE;
        }
        QListWidget::item {
            background-color: #2e2e2e;
            color: #ffffff;
            border-radius: 5px;
            padding: 5px;
        }
        QListWidget::item:selected {
            border: 1px solid #555;
            background-color: #3e3e3e;
            border-radius: 5px;
            padding: 5px;
        }
        QMenu {
            background-color: #2e2e2e;
            color: #ffffff;
            border: 1px solid #444444;
        }
        QMenu::item:selected {
            background-color: #3e3e3e;
        }
        QScrollBar:vertical {
            background-color: #2e2e2e;
            width: 12px;
        }
        QScrollBar::handle:vertical {
            background-color: #3e3e3e;
            min-height: 20px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            background-color: #2e2e2e;
            height: 0;
        }
    """)

    window = CreadorEntornos()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
