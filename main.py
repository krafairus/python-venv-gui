#!/usr/bin/env python3

import os
import sys
import subprocess
import json
import shlex
import re 
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QWidget, QHBoxLayout,
    QMessageBox, QStackedWidget, QToolButton, QInputDialog, QDialog,
    QComboBox, QDialogButtonBox, QFileDialog, QScrollArea, QSizePolicy,
    QTabWidget, QTextEdit
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize, QTranslator, QCoreApplication, QObject, QDir

# --- Definición del Tema (Modo Oscuro Fijo) ---

COLOR_BG_PRIMARY = "#1c1c1c"
COLOR_BG_SECONDARY = "#2e2e2e"
COLOR_BG_TERTIARY = "#333"
COLOR_BORDER = "#444444"
COLOR_BUTTON_BG = "#444"
COLOR_BUTTON_HOVER = "#555"
COLOR_TEXT = "#ffffff"
COLOR_PLACEHOLDER = "#BEBEBE"

# Estilo Base Común (Dark Mode Fijo)
DARK_STYLE = f"""
    QMainWindow, QWidget, QDialog {{
        background-color: {COLOR_BG_PRIMARY};
        color: {COLOR_TEXT};
        font-family: 'Cantarell', sans-serif;
        font-size: 11pt;
    }}
    QToolBar {{
        background-color: {COLOR_BG_SECONDARY};
    }}
    /* Aplicar estilo consistente de QPushButton */
    QPushButton {{
        border: 1px solid #555;
        border-radius: 5px;
        padding: 5px 12px;
        background-color: {COLOR_BUTTON_BG};
        color: {COLOR_TEXT};
        min-height: 25px; 
    }}
    QPushButton:hover {{
        background-color: {COLOR_BUTTON_HOVER};
    }}
    /* Botones de Icono ToolButton */
    QToolButton {{
        background-color: transparent;
        color: {COLOR_TEXT};
        border: none;
        padding: 5px;
    }}
    QToolButton:hover {{
        background-color: {COLOR_BG_SECONDARY};
    }}
    QLineEdit, QComboBox {{
        background-color: {COLOR_BG_TERTIARY};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER};
        padding: 5px;
        border-radius: 5px;
        min-height: 25px;
    }}
    QListWidget {{
        border: 1px solid #555;
        border-radius: 5px;
        padding: 5px;
        background-color: {COLOR_BG_TERTIARY};
        color: {COLOR_PLACEHOLDER};
    }}
    QListWidget::item {{
        background-color: {COLOR_BG_SECONDARY};
        color: {COLOR_TEXT};
        border-radius: 5px;
        padding: 5px;
    }}
    QListWidget::item:selected {{
        border: 1px solid #555;
        background-color: {COLOR_BUTTON_HOVER};
        border-radius: 5px;
        padding: 5px;
    }}
    QMenu {{
        background-color: {COLOR_BG_SECONDARY};
        color: {COLOR_TEXT};
        border: 1px solid {COLOR_BORDER};
    }}
    QMenu::item:selected {{
        background-color: {COLOR_BUTTON_HOVER};
    }}
    QScrollBar:vertical {{
        background-color: {COLOR_BG_SECONDARY};
        width: 12px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {COLOR_BUTTON_HOVER};
        min-height: 20px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        background-color: {COLOR_BG_SECONDARY};
        height: 0;
    }}
    /* Estilo específico para la barra de título */
    #title_bar {{
        background-color: #262626; 
        border-bottom: 1px solid #333333;
    }}
    QTabWidget::pane {{
        border: 1px solid {COLOR_BORDER};
        background-color: {COLOR_BG_SECONDARY};
    }}
    QTabBar::tab {{
        background-color: {COLOR_BG_TERTIARY};
        color: {COLOR_TEXT};
        padding: 8px 16px;
        border: 1px solid {COLOR_BORDER};
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}
    QTabBar::tab:selected {{
        background-color: {COLOR_BG_SECONDARY};
        border-bottom: 1px solid {COLOR_BG_SECONDARY};
    }}
    QTabBar::tab:hover {{
        background-color: {COLOR_BUTTON_HOVER};
    }}
"""

# --- Rutas y Constantes de Configuración ---

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RESOURCES_DIR = os.path.join(BASE_DIR, 'resources')
TRANSLATIONS_DIR = os.path.join(BASE_DIR, 'translations') 

# Directorio fijo para guardar la configuración y el registro de la aplicación
CONFIG_BASE_DIR = os.path.expanduser('~/.env-creator-ui').rstrip('/')
ARCHIVO_REGISTRO = os.path.join(CONFIG_BASE_DIR, 'registro_env.txt')
ARCHIVO_CONFIG = os.path.join(CONFIG_BASE_DIR, 'config.json')

# Lista de rutas comunes de binarios de Python para búsqueda
COMMON_PYTHON_PATHS = [
    sys.executable,  
    '/usr/bin/python3',
    '/usr/bin/python',
    '/usr/local/bin/python3',
    '/usr/local/bin/python',
    '/opt/homebrew/bin/python3', 
    os.path.expanduser('~/.pyenv/shims/python') 
]
COMMON_PYTHON_PATHS = list(set([p for p in COMMON_PYTHON_PATHS if os.path.exists(p)]))
COMMON_PYTHON_PATHS.sort(reverse=True)

# Definición de terminales disponibles
system_terminals = {
    "GNOME Terminal": ["/usr/bin/gnome-terminal", "/usr/local/bin/gnome-terminal"],
    "Deepin Terminal": ["/usr/bin/deepin-terminal", "/usr/local/bin/deepin-terminal"],
    "Konsole (KDE)": ["/usr/bin/konsole", "/usr/local/bin/konsole"],
    "XFCE Terminal": ["/usr/bin/xfce4-terminal", "/usr/local/bin/xfce4-terminal"],
    "Kitty": ["/usr/bin/kitty", "/usr/local/bin/kitty"],
    "Alacritty": ["/usr/bin/alacritty", "/usr/local/bin/alacritty"],
    "Terminator": ["/usr/bin/terminator", "/usr/local/bin/terminator"],
    "Tilix": ["/usr/bin/tilix", "/usr/local/bin/tilix"],
    "Rxvt": ["/usr/bin/rxvt", "/usr/bin/urxvt", "/usr/local/bin/rxvt", "/usr/local/bin/urxvt"],
    "XTerm": ["/usr/bin/xterm", "/usr/local/bin/xterm"]
}

# Comandos específicos para cada terminal. Usan {command} como placeholder para 'bash --init-file /tmp/activate_venv.sh'
# La ejecución se maneja en iniciar_entorno_terminal para mayor robustez.
terminal_commands = {
    "GNOME Terminal": "-- bash -c '{command}'", 
    "Deepin Terminal": "-e '{command}'", 
    "Konsole (KDE)": "-e '{command}'",
    "XFCE Terminal": "-x '{command}'",
    "Kitty": "bash -c '{command}'",
    "Alacritty": "-e '{command}'",
    "Terminator": "-x '{command}'",
    "Tilix": "-e '{command}'",
    "Rxvt": "-e '{command}'",
    "XTerm": "-e '{command}'",
    "Otro": "{custom_command}" 
}

# Clase que maneja la carga y aplicación de traducciones
class TranslationManager(QObject):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.translator = QTranslator(self)
        self.fallback_translator = QTranslator(self)

    def load_language(self, lang_code, base_dir):
        QCoreApplication.removeTranslator(self.translator)
        
        qm_file = f"env_creator_ui_{lang_code}.qm"
        translations_dir = os.path.join(base_dir, 'translations')
        qm_path = os.path.join(translations_dir, qm_file)
        
        if self.translator.load(qm_path):
             QCoreApplication.installTranslator(self.translator)
             print(f"Cargado traductor: {qm_path}")
        else:
             print(f"Error al cargar traductor en: {qm_path}. Usando idioma fuente.")
             QCoreApplication.removeTranslator(self.translator)

# --- Diálogo de Información del Entorno ---

class EntornoInfoDialog(QDialog):
    def __init__(self, parent=None, entorno_path="", entorno_name=""):
        super().__init__(parent)
        self.entorno_path = entorno_path
        self.entorno_name = entorno_name
        self.setWindowTitle(f"Información del Entorno: {entorno_name}")
        self.setFixedSize(600, 500)
        self.setup_ui()
        self.cargar_informacion()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Crear widget de pestañas
        self.tab_widget = QTabWidget()
        
        # Pestaña Básica
        self.basica_tab = QWidget()
        self.setup_basica_tab()
        self.tab_widget.addTab(self.basica_tab, "Básica")
        
        # Pestaña Librerías
        self.librerias_tab = QWidget()
        self.setup_librerias_tab()
        self.tab_widget.addTab(self.librerias_tab, "Librerías")
        
        layout.addWidget(self.tab_widget)

        # Botón de cerrar
        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_cerrar.clicked.connect(self.close)
        layout.addWidget(self.btn_cerrar)

    def setup_basica_tab(self):
        layout = QVBoxLayout(self.basica_tab)
        
        # Área de scroll para la información básica
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        self.info_basica_text = QTextEdit()
        self.info_basica_text.setReadOnly(True)
        self.info_basica_text.setStyleSheet("background-color: #2e2e2e; color: white; border: none;")
        scroll_layout.addWidget(self.info_basica_text)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

    def setup_librerias_tab(self):
        layout = QVBoxLayout(self.librerias_tab)
        
        # Área de scroll para las librerías
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        self.librerias_text = QTextEdit()
        self.librerias_text.setReadOnly(True)
        self.librerias_text.setStyleSheet("background-color: #2e2e2e; color: white; border: none;")
        scroll_layout.addWidget(self.librerias_text)
        
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

    def cargar_informacion(self):
        self.cargar_info_basica()
        self.cargar_librerias()

    def cargar_info_basica(self):
        info_text = f"""Información Básica del Entorno Virtual

Nombre: {self.entorno_name}
Ruta: {self.entorno_path}

"""
        # Información del directorio
        if os.path.exists(self.entorno_path):
            stat_info = os.stat(self.entorno_path)
            from datetime import datetime
            fecha_creacion = datetime.fromtimestamp(stat_info.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
            fecha_modificacion = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            
            info_text += f"""Información del Directorio:
- Creado: {fecha_creacion}
- Modificado: {fecha_modificacion}
- Tamaño: {self.calcular_tamaño_directorio(self.entorno_path)}

"""

        # Información de Python del entorno
        python_path = self.obtener_python_del_entorno()
        if python_path and os.path.exists(python_path):
            try:
                result = subprocess.run([python_path, '--version'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    info_text += f"Versión de Python: {result.stdout.strip()}\n"
                
                # Información de la plataforma
                result = subprocess.run([python_path, '-c', 'import sys; print(f"Plataforma: {sys.platform}")'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    info_text += f"{result.stdout.strip()}\n"
                
                # Información de implementación
                result = subprocess.run([python_path, '-c', 'import sys; print(f"Implementación: {sys.implementation.name}")'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    info_text += f"{result.stdout.strip()}\n"
                    
            except Exception as e:
                info_text += f"Error al obtener información de Python: {str(e)}\n"

        self.info_basica_text.setPlainText(info_text)

    def cargar_librerias(self):
        librerias_text = "Librerias Instaladas\n\n"
        
        pip_path = self.obtener_pip_del_entorno()
        if pip_path and os.path.exists(pip_path):
            try:
                result = subprocess.run([pip_path, 'list', '--format=freeze'], capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    librerias = result.stdout.strip().split('\n')
                    if librerias and librerias[0]:
                        for libreria in sorted(librerias):
                            librerias_text += f"{libreria}\n"
                    else:
                        librerias_text += "No se encontraron librerías instaladas.\n"
                else:
                    librerias_text += f"Error al obtener la lista de librerías: {result.stderr}\n"
            except Exception as e:
                librerias_text += f"Error al ejecutar pip: {str(e)}\n"
        else:
            librerias_text += "No se pudo encontrar el ejecutable de pip en el entorno virtual.\n"

        self.librerias_text.setPlainText(librerias_text)

    def obtener_python_del_entorno(self):
        # Buscar el ejecutable de Python en el entorno virtual
        posibles_rutas = [
            os.path.join(self.entorno_path, 'bin', 'python'),
            os.path.join(self.entorno_path, 'bin', 'python3'),
            os.path.join(self.entorno_path, 'Scripts', 'python.exe') if sys.platform == 'win32' else ''
        ]
        
        for ruta in posibles_rutas:
            if os.path.exists(ruta):
                return ruta
        return None

    def obtener_pip_del_entorno(self):
        # Buscar el ejecutable de pip en el entorno virtual
        posibles_rutas = [
            os.path.join(self.entorno_path, 'bin', 'pip'),
            os.path.join(self.entorno_path, 'bin', 'pip3'),
            os.path.join(self.entorno_path, 'Scripts', 'pip.exe') if sys.platform == 'win32' else ''
        ]
        
        for ruta in posibles_rutas:
            if os.path.exists(ruta):
                return ruta
        return None

    def calcular_tamaño_directorio(self, path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        
        # Convertir a formato legible
        for unit in ['B', 'KB', 'MB', 'GB']:
            if total_size < 1024.0:
                return f"{total_size:.1f} {unit}"
            total_size /= 1024.0
        return f"{total_size:.1f} TB"

# --- Diálogo para Selección de Python ---

class SeleccionadorPythonDialog(QDialog):
    def __init__(self, parent=None, initial_path=None):
        super().__init__(parent)
        self.parent = parent
        self.selected_path = initial_path
        self.setWindowTitle(self.tr("Seleccionar intérprete de Python"))
        self.setup_ui()
        self.setFixedSize(500, 450)

    def tr(self, text):
        return QCoreApplication.translate("SeleccionadorPythonDialog", text)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)

        explanation_label = QLabel(self.tr("Elige la ruta del ejecutable de Python para crear los entornos virtuales:"))
        layout.addWidget(explanation_label)
        
        self.path_input = QLineEdit() 
        self.path_input.setPlaceholderText(self.tr("Ruta del ejecutable"))
        if self.selected_path:
            self.path_input.setText(self.selected_path)

        self.list_widget = QListWidget()
        self.list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.list_widget.itemSelectionChanged.connect(self.update_path_from_list)
        layout.addWidget(self.list_widget)
        
        self.cargar_opciones_python() 

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_input) 
        
        self.btn_browse = QPushButton(self.tr("Buscar"))
        self.btn_browse.clicked.connect(self.browse_for_python)
        path_layout.addWidget(self.btn_browse)
        layout.addLayout(path_layout)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.btn_cancel = QPushButton(self.tr("Cancelar"))
        self.btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(self.btn_cancel)
        
        self.btn_save = QPushButton(self.tr("Aceptar"))
        self.btn_save.clicked.connect(self.accept_selection)
        buttons_layout.addWidget(self.btn_save)
        
        layout.addLayout(buttons_layout)

    def get_python_version_and_path(self, path):
        try:
            result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                version_match = re.search(r'Python (\d+\.\d+(\.\d+)?)', result.stdout.strip())
                if version_match:
                    version = version_match.group(1)
                    return version, path
        except Exception:
            pass 
        return "Desconocida", path

    def cargar_opciones_python(self):
        self.list_widget.clear()
        
        potential_paths = set(COMMON_PYTHON_PATHS)
        
        for i in range(7, 13):
            potential_paths.add(f'/usr/bin/python3.{i}')
            potential_paths.add(f'/usr/local/bin/python3.{i}')

        valid_paths = [p for p in potential_paths if os.path.exists(p) and os.access(p, os.X_OK)]
        valid_paths = list(set(valid_paths)) 
        
        current_selection_item = None
        
        for path in valid_paths:
            version, _ = self.get_python_version_and_path(path)
            if version != "Desconocida":
                item_text = f"Python {version} ({path})"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, path)
                self.list_widget.addItem(item)
                
                if path == self.selected_path:
                    current_selection_item = item

        if current_selection_item:
            self.list_widget.setCurrentItem(current_selection_item)
            self.list_widget.scrollToItem(current_selection_item)
            
    def update_path_from_list(self):
        item = self.list_widget.currentItem()
        if item:
            self.path_input.setText(item.data(Qt.UserRole)) 

    def browse_for_python(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 
            self.tr("Seleccionar ejecutable de Python"), 
            QDir.homePath(), 
            self.tr("Ejecutables (*)")
        )
        if path:
            self.path_input.setText(path)
            
    def accept_selection(self):
        selected_path = self.path_input.text().strip()
        if not selected_path:
            QMessageBox.warning(self, self.tr("Advertencia"), self.tr("Por favor, introduce una ruta válida."))
            return
            
        if not os.path.exists(selected_path):
            QMessageBox.warning(self, self.tr("Advertencia"), self.tr("El ejecutable no existe. Por favor, verifica la ruta."))
            return
            
        self.selected_path = selected_path
        self.accept()
# ----------------------------------------------------

# --- Diálogo para Configuración de Terminal Personalizada (Corregido) ---
class CustomTerminalDialog(QDialog):
    def __init__(self, main_window, parent=None): 
        super().__init__(parent)
        self.main_window = main_window
        self.nombre = None
        self.ruta = None
        self.comando = None
        self.setWindowTitle(self.main_window.get_string("custom_terminal")) 
        self.setFixedSize(500, 300)
        self.setup_ui()

    def tr(self, text):
        return QCoreApplication.translate("CustomTerminalDialog", text)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        parent = self.main_window

        layout.addWidget(QLabel(parent.get_string("terminal_name")))
        self.input_nombre = QLineEdit()
        layout.addWidget(self.input_nombre)
        
        layout.addWidget(QLabel(parent.get_string("terminal_path")))
        ruta_layout = QHBoxLayout()
        self.input_ruta = QLineEdit("/usr/bin/")
        ruta_layout.addWidget(self.input_ruta)
        self.btn_browse_ruta = QPushButton(parent.get_string("browse"))
        self.btn_browse_ruta.clicked.connect(self.browse_for_terminal)
        ruta_layout.addWidget(self.btn_browse_ruta)
        layout.addLayout(ruta_layout)
        
        # --- INICIO DE LA CORRECCIÓN: Ajuste de Texto ---
        label_comando = QLabel(parent.get_string("custom_command_full"))
        label_comando.setWordWrap(True) # ¡Asegura que el texto se ajuste!
        layout.addWidget(label_comando)
        # --- FIN DE LA CORRECCIÓN ---

        self.input_comando = QLineEdit("-e 'bash --init-file {script}'")
        layout.addWidget(self.input_comando)
        
        layout.addStretch()

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, Qt.Horizontal, self)
        buttons.accepted.connect(self.check_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def browse_for_terminal(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 
            self.main_window.get_string("select_terminal_executable"), 
            QDir.homePath(), 
            self.tr("Ejecutables (*)")
        )
        if path:
            self.input_ruta.setText(path)

    def check_and_accept(self):
        nombre = self.input_nombre.text().strip()
        ruta = self.input_ruta.text().strip()
        comando = self.input_comando.text().strip()
        parent = self.main_window

        if not nombre or not ruta or not comando:
            QMessageBox.warning(self, parent.get_string("warning"), parent.get_string("provide_all_custom_terminal_fields"))
            return
            
        if not os.path.exists(ruta):
            respuesta = QMessageBox.question(self, parent.get_string("executable_not_found"), parent.get_string("continue_anyway"), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if respuesta == QMessageBox.StandardButton.No: return
            
        self.nombre = nombre
        self.ruta = ruta
        self.comando = comando
        self.accept()

# --- Diálogo de Configuración (Modificado - Eliminada pestaña de Gestión de Entornos) ---

class ConfigDialog(QDialog):
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.parent = parent 
        self.config = config
        self.setup_ui()

    def tr(self, text):
        return QCoreApplication.translate("ConfigDialog", text)

    def setup_ui(self):
        self.setWindowTitle(self.tr("Configuración"))
        self.setFixedSize(600, 500)

        layout = QVBoxLayout(self)

        # Crear el widget de pestañas
        self.tab_widget = QTabWidget()
        
        # Pestaña 1: Configuración General
        self.general_tab = QWidget()
        self.setup_general_tab()
        self.tab_widget.addTab(self.general_tab, self.tr("General"))
        
        layout.addWidget(self.tab_widget)

        # Solo un botón de Cerrar
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.btn_ok = QPushButton(self.tr("Cerrar"))
        self.btn_ok.clicked.connect(self.accept_changes) 
        buttons_layout.addWidget(self.btn_ok)
        
        layout.addLayout(buttons_layout)

    def setup_general_tab(self):
        """Configura la pestaña de configuración general"""
        layout = QVBoxLayout(self.general_tab)

        # 1. Selector de Idioma
        lang_layout = QHBoxLayout()
        lang_label = QLabel(self.tr("Idioma") + ":")
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Español", "es")
        self.lang_combo.addItem("English", "en")
        self.lang_combo.addItem("Português", "pt")
        
        current_lang = self.config.get('idioma', 'es')
        index = self.lang_combo.findData(current_lang)
        if index >= 0:
            self.lang_combo.setCurrentIndex(index)
        
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        layout.addLayout(lang_layout)
        
        # 2. Directorio Base de Entornos
        layout.addWidget(QLabel(self.parent.get_string("base_env_directory") + ":"))
        
        env_dir_layout = QHBoxLayout()
        self.env_dir_input = QLineEdit(self.config.get('directorio_base_env'))
        self.env_dir_input.setReadOnly(True) 
        env_dir_layout.addWidget(self.env_dir_input)
        
        self.btn_browse_env_dir = QPushButton(self.parent.get_string("change_button"))
        self.btn_browse_env_dir.clicked.connect(self.browse_env_directory)
        env_dir_layout.addWidget(self.btn_browse_env_dir)
        layout.addLayout(env_dir_layout)
        
        # 3. Terminales personalizadas
        layout.addWidget(QLabel(self.tr("Terminales personalizadas") + ":"))
        self.terminals_list = QListWidget()
        self.actualizar_lista_terminales()
        layout.addWidget(self.terminals_list)
        
        # Botones para terminales (Añadir y Eliminar)
        terminals_buttons_layout = QHBoxLayout()
        self.btn_add_terminal = QPushButton(self.parent.get_string("add_custom_terminal_button")) 
        self.btn_add_terminal.clicked.connect(self.add_custom_terminal)
        terminals_buttons_layout.addWidget(self.btn_add_terminal)
        
        self.btn_eliminar_terminal = QPushButton(self.tr("Eliminar seleccionada"))
        self.btn_eliminar_terminal.clicked.connect(self.eliminar_terminal_seleccionada)
        terminals_buttons_layout.addWidget(self.btn_eliminar_terminal)
        layout.addLayout(terminals_buttons_layout)

        layout.addStretch()

    def browse_env_directory(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, 
            self.parent.get_string("browse_env_dir_title"), 
            self.env_dir_input.text()
        )
        if dir_path:
            self.env_dir_input.setText(dir_path)

    def add_custom_terminal(self):
        dialog = CustomTerminalDialog(self.parent, self) 
        if dialog.exec() == QDialog.DialogCode.Accepted:
            nombre = dialog.nombre
            ruta = dialog.ruta
            comando = dialog.comando
            
            if 'terminales_personalizados' not in self.config: self.config['terminales_personalizados'] = {}
            self.config['terminales_personalizados'][nombre] = {'ruta': ruta, 'comando': comando}
            self.parent.guardar_config()
            self.actualizar_lista_terminales()
            QMessageBox.information(self, self.tr("Éxito"), self.parent.get_string("terminal_added_successfully"))

    def accept_changes(self):
        new_env_dir = self.env_dir_input.text().strip()
        if not new_env_dir or not os.path.isdir(new_env_dir):
            QMessageBox.warning(self, self.tr("Advertencia"), self.parent.get_string("invalid_env_dir"))
            return
            
        self.config['directorio_base_env'] = new_env_dir
        
        current_lang = self.config.get('idioma')
        nuevo_idioma = self.lang_combo.currentData()
        self.config['idioma'] = nuevo_idioma

        self.parent.guardar_config()
        
        if nuevo_idioma != current_lang:
            QMessageBox.information(self, self.parent.get_string("success"), self.parent.get_string("restart_for_changes"))

        super().accept()

    def actualizar_lista_terminales(self):
        self.terminals_list.clear()
        terminales_personalizados = self.config.get('terminales_personalizados', {})
        for nombre, datos in terminales_personalizados.items():
            item_text = f"{nombre} - {datos['ruta']}"
            self.terminals_list.addItem(item_text)

    def eliminar_terminal_seleccionada(self):
        current_item = self.terminals_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, self.tr("Advertencia"), self.tr("Selecciona una terminal para eliminar"))
            return

        item_text = current_item.text()
        nombre_terminal = item_text.split(" - ")[0]

        respuesta = QMessageBox.question(
            self,
            self.tr("Confirmar eliminación"),
            f"{self.tr('¿Estás seguro de que quieres eliminar la terminal')} '{nombre_terminal}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            if 'terminales_personalizados' in self.config:
                if nombre_terminal in self.config['terminales_personalizados']:
                    del self.config['terminales_personalizados'][nombre_terminal]
                    self.parent.guardar_config()
                    self.actualizar_lista_terminales()
                    QMessageBox.information(self, self.tr("Éxito"), self.tr("Terminal eliminada correctamente"))

# --- Diálogo de Importación de Entornos ---

class ImportEnvDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle(self.parent.get_string("import_envs_button"))
        self.setFixedSize(400, 200)
        self.setup_ui()

    def tr(self, text):
        return QCoreApplication.translate("ImportEnvDialog", text)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)

        explanation_label = QLabel(self.parent.get_string("import_dialog_explanation"))
        explanation_label.setWordWrap(True)
        layout.addWidget(explanation_label)
        layout.addStretch()

        self.btn_select_and_search = QPushButton(self.parent.get_string("select_and_search_button"))
        self.btn_select_and_search.clicked.connect(self.select_and_search)
        layout.addWidget(self.btn_select_and_search)

        self.btn_close = QPushButton(self.parent.get_string("close"))
        self.btn_close.clicked.connect(self.close)
        layout.addWidget(self.btn_close)
        
    def select_and_search(self):
        self.parent.buscar_entornos_existentes()
        self.accept() 


# --- Clase Principal CreadorEntornos (Modificado) ---

class CreadorEntornos(QMainWindow):
    def tr(self, text):
        return QCoreApplication.translate("CreadorEntornos", text)
        
    def __init__(self):
        super().__init__()

        self.setup_icons()
        self.cargar_config()
        
        os.makedirs(CONFIG_BASE_DIR, exist_ok=True)
        os.makedirs(self.config['directorio_base_env'], exist_ok=True)
        
        self.translation_manager = TranslationManager(QApplication.instance(), self)
        self.cargar_idioma() 
        self.iniciar_ui()
        self.cargar_entornos_desde_registro()
    
    def get_string(self, key):
        string_map = {
            "app_title": "Entornos Virtuales (py)",
            "create_env": "Crear entorno",
            "env_name_placeholder": "Nombre del entorno",
            "delete_selected": "Eliminar seleccionado",
            "open_directory": "Abrir directorio",
            "open_terminal": "Abrir terminal",
            "config_title": "Configuración",
            "warning": "Advertencia",
            "success": "Éxito",
            "select_terminal": "Seleccionar Terminal",
            "choose_terminal": "Elige una terminal:",
            "custom_terminal": "Terminal Personalizada",
            "terminal_name": "Nombre para esta terminal:",
            "terminal_path": "Ruta del ejecutable:",
            "custom_command": "Comando personalizado (usa {script} para el script):",
            "custom_command_full": "Comando personalizado de la terminal (usa {script} para el script de activación):",
            "executable_not_found": "Ejecutable no encontrado",
            "continue_anyway": "¿La ruta no existe. Deseas continuar de todos modos?",
            "missing_fields": "Campos faltantes",
            "provide_name": "Por favor, proporciona un nombre para el entorno.",
            "env_created": "Entorno creado correctamente.",
            "error": "Error",
            "venv_error": "Error al crear el entorno. Verifica si el módulo 'venv' está instalado. Asegúrate de que el intérprete de Python seleccionado sea válido.",
            "delete_env": "Eliminar entorno",
            "confirm_delete_env": "¿Estás seguro de que quieres eliminar el entorno",
            "about_title": "Acerca de Python Venv Gui",
            "about_content": "Python Venv Gui v1.2.0\n\nDesarrollado por krafairus\n\nMás información en:\nhttps://github.com/krafairus/py-venv-gui",
            "close": "Cerrar",
            "restart_for_changes": "Los cambios de idioma requieren reiniciar la aplicación",
            "terminal_error": "No se pudo abrir la terminal",
            "select_interpreter": "Seleccionar intérprete de Python",
            "base_env_directory": "Directorio base de entornos virtuales",
            "change_button": "Cambiar",
            "browse_env_dir_title": "Seleccionar Directorio Base para Entornos",
            "import_envs_button": "Importar entornos existentes",
            "select_scan_directory": "Seleccionar Directorio para Escanear Entornos",
            "no_new_envs_found": "No se encontraron nuevos entornos virtuales en el directorio seleccionado.",
            "added_new_envs": "Se añadieron %d nuevos entornos a la lista.",
            "invalid_env_dir": "La ruta seleccionada para el directorio de entornos no es válida.",
            "add_custom_terminal_button": "Añadir Terminal Personalizada",
            "terminal_added_successfully": "Terminal personalizada añadida correctamente",
            "select_terminal_executable": "Seleccionar ejecutable de Terminal",
            "provide_all_custom_terminal_fields": "Por favor, proporciona el nombre, la ruta y el comando de la terminal personalizada.",
            "import_dialog_explanation": "Selecciona el directorio que deseas escanear. La aplicación buscará subcarpetas que contengan una estructura de entorno virtual (por ejemplo, 'bin/activate') y los añadirá a tu lista.",
            "select_and_search_button": "Seleccionar directorio y buscar",
        }
        
        return self.tr(string_map.get(key, key))

    def setup_icons(self):
        """Configura las rutas de los íconos"""
        self.icono_app = os.path.join(RESOURCES_DIR, 'icon.svg')
        self.icono_eliminar = os.path.join(RESOURCES_DIR, 'delete.png')
        self.icono_abrir_directorio = os.path.join(RESOURCES_DIR, 'folder.png')
        self.icono_acerca_de = os.path.join(RESOURCES_DIR, 'info.png')
        self.icono_abrir_terminal = os.path.join(RESOURCES_DIR, 'open.png')
        self.icono_configuracion = os.path.join(RESOURCES_DIR, 'settings.png')
        self.icono_python = os.path.join(RESOURCES_DIR, 'python.png') 
        self.icono_import_envs = os.path.join(RESOURCES_DIR, 'search.png') 
        self.icono_info = os.path.join(RESOURCES_DIR, 'info.png')  # Nuevo ícono para información
        
        if os.path.exists(self.icono_app):
            self.setWindowIcon(QIcon(self.icono_app))

    def cargar_config(self):
        """Carga la configuración desde el archivo JSON"""
        config_default = {
            "ultima_terminal": None,
            "terminales_personalizados": {},
            "idioma": "es",
            "current_python_interpreter": sys.executable,
            "directorio_base_env": os.path.expanduser('~/.virtualenvs').rstrip('/')
        }
        
        if os.path.exists(ARCHIVO_CONFIG):
            try:
                with open(ARCHIVO_CONFIG, 'r') as f:
                    loaded_config = json.load(f)
                    if 'theme' in loaded_config: del loaded_config['theme'] 
                    self.config = {**config_default, **loaded_config}
            except:
                self.config = config_default
        else:
            self.config = config_default

    def cargar_idioma(self):
        """Carga la traducción Qt (.qm) según el idioma seleccionado"""
        idioma = self.config.get('idioma', 'es')
        self.translation_manager.load_language(idioma, BASE_DIR)

    def guardar_config(self):
        """Guarda la configuración en el archivo JSON"""
        os.makedirs(os.path.dirname(ARCHIVO_CONFIG), exist_ok=True)
        with open(ARCHIVO_CONFIG, 'w') as f:
            json.dump(self.config, f, indent=4)

    def detectar_terminales_disponibles(self):
        terminales_disponibles = []
        
        for terminal, paths in system_terminals.items():
            for path in paths:
                if os.path.exists(path):
                    terminales_disponibles.append({'nombre': terminal, 'tipo': 'sistema', 'ruta': path, 'comando': terminal_commands[terminal]})
                    break
        
        for nombre, datos in self.config.get('terminales_personalizados', {}).items():
            terminales_disponibles.append({'nombre': nombre, 'tipo': 'personalizado', 'ruta': datos['ruta'], 'comando': datos['comando']})
        
        return terminales_disponibles

    def seleccionar_terminal(self):
        terminales_disponibles = self.detectar_terminales_disponibles()
        nombres_terminales = [f"{term['nombre']} ({term['tipo']})" for term in terminales_disponibles]
        
        default_index = 0
        if self.config.get('ultima_terminal'):
            ultima_nombre = self.config['ultima_terminal']['nombre']
            for i, term in enumerate(terminales_disponibles):
                if term['nombre'] == ultima_nombre:
                    default_index = i
                    break
        
        items, ok = QInputDialog.getItem(
            self, 
            self.get_string("select_terminal"), 
            self.get_string("choose_terminal"), 
            nombres_terminales, 
            default_index, 
            False
        )

        if ok and items:
            selected_index = nombres_terminales.index(items)
            terminal_seleccionada = terminales_disponibles[selected_index]
            
            self.config['ultima_terminal'] = {
                'nombre': terminal_seleccionada['nombre'],
                'ruta': terminal_seleccionada['ruta'],
                'comando': terminal_seleccionada['comando']
            }
            self.guardar_config()
                
            return terminal_seleccionada
        
        return None

    def seleccionar_version_python(self):
        initial_path = self.config.get('current_python_interpreter', sys.executable)
        dialog = SeleccionadorPythonDialog(self, initial_path)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_path = dialog.selected_path
            if new_path != self.config.get('current_python_interpreter'):
                self.config['current_python_interpreter'] = new_path
                self.guardar_config()
                QMessageBox.information(self, self.get_string("success"), f"{self.get_string('select_interpreter')}: {new_path}")

    def abrir_configuracion(self):
        dialog = ConfigDialog(self, self.config)
        result = dialog.exec()
        
    def abrir_import_dialog(self):
        dialog = ImportEnvDialog(self)
        dialog.exec()

    def mostrar_info_entorno(self):
        """Muestra la información del entorno seleccionado"""
        item_actual = self.lista_entornos.currentItem()
        if item_actual:
            # Obtener el nombre del entorno del widget personalizado
            widget = self.lista_entornos.itemWidget(item_actual)
            if widget:
                labels = widget.findChildren(QLabel)
                if labels and len(labels) > 0:
                    nombre_entorno = labels[0].text()
                else:
                    # Fallback: obtener del texto del item
                    item_text = item_actual.text()
                    nombre_entorno = item_text.split('\n')[0]
            else:
                # Fallback: obtener del texto del item
                item_text = item_actual.text()
                nombre_entorno = item_text.split('\n')[0]
                
            ruta_entorno = item_actual.data(Qt.UserRole)
            
            # Abrir diálogo de información
            dialog = EntornoInfoDialog(self, ruta_entorno, nombre_entorno)
            dialog.exec()

    def acortar_ruta(self, ruta_completa, max_caracteres=50):
        """Acorta una ruta mostrando solo las partes finales si es necesario"""
        if len(ruta_completa) <= max_caracteres:
            return ruta_completa
        
        # Dividir la ruta en partes
        partes = ruta_completa.split(os.sep)
        
        # Si la ruta es muy larga, mostrar solo las últimas partes
        if len(partes) > 3:
            # Tomar las últimas 3 partes y unirlas con "..."
            partes_finales = partes[-3:]
            ruta_acortada = "..." + os.sep + os.sep.join(partes_finales)
            
            # Si aún es muy larga, acortar más
            if len(ruta_acortada) > max_caracteres:
                # Mostrar solo las últimas 2 partes
                partes_finales = partes[-2:]
                ruta_acortada = "..." + os.sep + os.sep.join(partes_finales)
                
                # Si aún es muy larga, truncar el nombre
                if len(ruta_acortada) > max_caracteres:
                    nombre_final = partes[-1]
                    if len(nombre_final) > max_caracteres - 10:
                        nombre_final = nombre_final[:max_caracteres - 13] + "..."
                    ruta_acortada = "..." + os.sep + nombre_final
        else:
            # Para rutas con pocas partes, simplemente truncar
            ruta_acortada = "..." + ruta_completa[-(max_caracteres-3):]
        
        return ruta_acortada

    def iniciar_ui(self):
        self.setWindowTitle(self.get_string("app_title"))
        self.resize(400, 450)  # Aumentado el ancho para mostrar mejor las rutas

        self.dragging = False 
        self.setWindowFlags(Qt.FramelessWindowHint)
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
        self.lista_entornos.setToolTipDuration(3000)
        main_hbox.addWidget(self.lista_entornos)

        self.side_bar_layout = QVBoxLayout()

        # Botones de la barra lateral
        self.btn_info = QToolButton(self)
        if os.path.exists(self.icono_info):
            self.btn_info.setIcon(QIcon(self.icono_info))
        else:
            self.btn_info.setText("ℹ") 
        self.btn_info.setIconSize(QSize(25, 25))
        self.btn_info.clicked.connect(self.mostrar_info_entorno)
        self.btn_info.setToolTip("Información del entorno")
        self.side_bar_layout.addWidget(self.btn_info)
        self.btn_info.hide()

        self.btn_eliminar = QToolButton(self)
        self.btn_eliminar.setIcon(QIcon(self.icono_eliminar))
        self.btn_eliminar.setIconSize(QSize(25, 25))
        self.btn_eliminar.clicked.connect(self.eliminar_entorno)
        self.btn_eliminar.setToolTip(self.get_string("delete_selected"))
        self.side_bar_layout.addWidget(self.btn_eliminar)
        self.btn_eliminar.hide()

        self.btn_abrir_directorio = QToolButton(self)
        self.btn_abrir_directorio.setIcon(QIcon(self.icono_abrir_directorio))
        self.btn_abrir_directorio.setIconSize(QSize(25, 25))
        self.btn_abrir_directorio.clicked.connect(self.abrir_directorio_entorno)
        self.btn_abrir_directorio.setToolTip(self.get_string("open_directory"))
        self.side_bar_layout.addWidget(self.btn_abrir_directorio)
        self.btn_abrir_directorio.hide()

        self.btn_iniciar_terminal = QToolButton(self)
        self.btn_iniciar_terminal.setIcon(QIcon(self.icono_abrir_terminal))
        self.btn_iniciar_terminal.setIconSize(QSize(25, 25))
        self.btn_iniciar_terminal.clicked.connect(self.iniciar_entorno_terminal)
        self.btn_iniciar_terminal.setToolTip(self.get_string("open_terminal"))
        self.side_bar_layout.addWidget(self.btn_iniciar_terminal)
        self.btn_iniciar_terminal.hide()

        main_hbox.addLayout(self.side_bar_layout)
        entornos_layout.addLayout(main_hbox)

        # Contenedor para Input y Botón de Python
        env_input_layout = QHBoxLayout()

        self.entrada_nombre_entorno = QLineEdit()
        self.entrada_nombre_entorno.setPlaceholderText(self.get_string("env_name_placeholder"))
        env_input_layout.addWidget(self.entrada_nombre_entorno)
        
        self.btn_select_python = QToolButton(self)
        if os.path.exists(self.icono_python):
             self.btn_select_python.setIcon(QIcon(self.icono_python))
        
        self.btn_select_python.setIconSize(QSize(25, 25))
        self.btn_select_python.setToolTip(self.get_string("select_interpreter"))
        self.btn_select_python.clicked.connect(self.seleccionar_version_python)
        env_input_layout.addWidget(self.btn_select_python)

        entornos_layout.addLayout(env_input_layout)

        self.boton_crear = QPushButton(self.get_string("create_env"))
        self.boton_crear.clicked.connect(self.crear_entorno)
        entornos_layout.addWidget(self.boton_crear)

        self.entornos_page.setLayout(entornos_layout)
        self.stacked_widget.addWidget(self.entornos_page)

        self.lista_entornos.itemSelectionChanged.connect(self.update_side_bar_buttons)

    def crear_barra_titulo(self):
        """Crea una barra de título personalizada."""
        self.title_bar = QWidget(self)
        self.title_bar.setFixedHeight(40)
        self.title_bar.setObjectName("title_bar")

        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        title_layout.setSpacing(0)
        
        # Botón Importar Entornos
        import_button = QToolButton()
        if os.path.exists(self.icono_import_envs):
            import_button.setIcon(QIcon(self.icono_import_envs))
        else:
            import_button.setText("⏏") 
        
        import_button.setIconSize(QSize(25, 25))
        import_button.setToolTip(self.get_string("import_envs_button")) 
        import_button.clicked.connect(self.abrir_import_dialog)
        title_layout.addWidget(import_button)

        # Botón Configuración
        config_button = QToolButton()
        config_button.setIcon(QIcon(self.icono_configuracion))
        config_button.setIconSize(QSize(25, 25))
        config_button.setToolTip(self.get_string("config_title")) 
        config_button.clicked.connect(self.abrir_configuracion)
        title_layout.addWidget(config_button)

        # Botón Acerca de
        about_button = QToolButton()
        about_button.setIcon(QIcon(self.icono_acerca_de))
        about_button.setIconSize(QSize(25, 25))
        about_button.setToolTip(self.tr("Ver información de la app")) 
        about_button.clicked.connect(self.mostrar_acerca_de)
        title_layout.addWidget(about_button)

        title_layout.addStretch()

        # Botones de Minimizar y Cerrar
        minimize_button = QPushButton("─")
        minimize_button.setFixedSize(40, 40)
        minimize_button.setStyleSheet("""
            QPushButton {background-color: transparent; color: #BEBEBE; font-size: 16px; border: none; padding: 0;}
            QPushButton:hover {background-color: #4A4A4A;}
            QPushButton:pressed {background-color: #323232;}
        """)
        minimize_button.clicked.connect(self.showMinimized)
        title_layout.addWidget(minimize_button)

        close_button = QPushButton("✕")
        close_button.setFixedSize(40, 40)
        close_button.setStyleSheet("""
            QPushButton {background-color: transparent; color: #BEBEBE; font-size: 16px; border: none; padding: 0;}
            QPushButton:hover {background-color: #d32f2f;}
            QPushButton:pressed {background-color: #b71c1c;}
        """)
        close_button.clicked.connect(self.close)
        title_layout.addWidget(close_button)

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
            self.btn_info.show()
            self.btn_eliminar.show()
            self.btn_abrir_directorio.show()
            self.btn_iniciar_terminal.show()
        else:
            self.btn_info.hide()
            self.btn_eliminar.hide()
            self.btn_abrir_directorio.hide()
            self.btn_iniciar_terminal.hide()

    def cargar_entornos_desde_registro(self):
        """Carga los entornos desde el archivo de registro"""
        self.lista_entornos.clear()
        if os.path.exists(ARCHIVO_REGISTRO):
            with open(ARCHIVO_REGISTRO, "r") as log_file:
                for line in log_file:
                    line = line.strip()
                    if not line: 
                        continue
                    
                    nombre_entorno = ""
                    base_path = ""
                    
                    try:
                        nombre_entorno, base_path = line.split('|', 1)
                        full_path = os.path.join(base_path, nombre_entorno)
                    except ValueError:
                        # Formato antiguo - convertir al nuevo formato
                        nombre_entorno = line
                        base_path = self.config.get('directorio_base_env', CONFIG_BASE_DIR)
                        full_path = os.path.join(base_path, nombre_entorno)
                        
                        # Actualizar el registro al nuevo formato
                        self.actualizar_registro_a_nuevo_formato()

                    if os.path.exists(full_path):
                        # Crear el item y establecer el texto con la ruta acortada
                        ruta_acortada = self.acortar_ruta(full_path)
                        item_text = f"{nombre_entorno}\n{ruta_acortada}"
                        
                        item = QListWidgetItem(item_text)
                        item.setData(Qt.UserRole, full_path)
                        item.setToolTip(full_path)  # Tooltip con la ruta completa
                        
                        # Crear widget personalizado
                        custom_widget = QWidget()
                        custom_layout = QVBoxLayout(custom_widget)
                        custom_layout.setContentsMargins(5, 5, 5, 5)
                        custom_layout.setSpacing(2)
                        
                        entorno_label = QLabel(nombre_entorno)
                        entorno_label.setStyleSheet("font-weight: bold;")
                        
                        ruta_label = QLabel(ruta_acortada)
                        ruta_label.setStyleSheet("font-size: 9pt; color: #BEBEBE;")
                        
                        custom_layout.addWidget(entorno_label)
                        custom_layout.addWidget(ruta_label)
                        
                        self.lista_entornos.addItem(item)
                        self.lista_entornos.setItemWidget(item, custom_widget)

    def actualizar_registro_a_nuevo_formato(self):
        """Actualiza el archivo de registro del formato antiguo al nuevo formato"""
        if os.path.exists(ARCHIVO_REGISTRO):
            with open(ARCHIVO_REGISTRO, "r") as f:
                lineas = f.readlines()
            
            # Verificar si hay líneas en formato antiguo
            lineas_actualizadas = []
            formato_antiguo_encontrado = False
            
            for linea in lineas:
                linea = linea.strip()
                if not linea:
                    continue
                
                # Si la línea no contiene '|', está en formato antiguo
                if '|' not in linea:
                    formato_antiguo_encontrado = True
                    # Convertir al nuevo formato
                    nueva_linea = f"{linea}|{self.config.get('directorio_base_env', CONFIG_BASE_DIR)}"
                    lineas_actualizadas.append(nueva_linea + "\n")
                else:
                    lineas_actualizadas.append(linea + "\n")
            
            # Si se encontró formato antiguo, actualizar el archivo
            if formato_antiguo_encontrado:
                with open(ARCHIVO_REGISTRO, "w") as f:
                    f.writelines(lineas_actualizadas)
                print("Registro actualizado al nuevo formato")

    def crear_entorno(self):
        nombre_entorno = self.entrada_nombre_entorno.text()
        if not nombre_entorno:
            self.entrada_nombre_entorno.setFocus()
            QMessageBox.warning(self, self.get_string("missing_fields"), self.get_string("provide_name"))
            return

        base_dir = self.config['directorio_base_env']
        ruta_entorno = os.path.join(base_dir, nombre_entorno)
        
        if os.path.exists(ruta_entorno):
            QMessageBox.warning(self, self.get_string("warning"), f"El entorno '{nombre_entorno}' ya existe en la ruta {base_dir}.")
            return
            
        os.makedirs(ruta_entorno, exist_ok=True)

        python_interpreter = self.config.get('current_python_interpreter', sys.executable)
        comando = [python_interpreter, '-m', 'venv', ruta_entorno]
        
        try:
            subprocess.run(comando, capture_output=True, text=True, check=True)
            
            # Usar siempre el nuevo formato
            with open(ARCHIVO_REGISTRO, "a") as log_file:
                log_file.write(f"{nombre_entorno}|{base_dir}\n")

            # Crear el item y establecer el texto con la ruta acortada
            ruta_acortada = self.acortar_ruta(ruta_entorno)
            item_text = f"{nombre_entorno}\n{ruta_acortada}"
            
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, ruta_entorno)
            item.setToolTip(ruta_entorno)  # Tooltip con la ruta completa
            
            # Crear widget personalizado
            custom_widget = QWidget()
            custom_layout = QVBoxLayout(custom_widget)
            custom_layout.setContentsMargins(5, 5, 5, 5)
            custom_layout.setSpacing(2)
            
            entorno_label = QLabel(nombre_entorno)
            entorno_label.setStyleSheet("font-weight: bold;")
            
            ruta_label = QLabel(ruta_acortada)
            ruta_label.setStyleSheet("font-size: 9pt; color: #BEBEBE;")
            
            custom_layout.addWidget(entorno_label)
            custom_layout.addWidget(ruta_label)
            
            self.lista_entornos.addItem(item)
            self.lista_entornos.setItemWidget(item, custom_widget)
            
            self.entrada_nombre_entorno.clear()
            
            QMessageBox.information(self, self.get_string("success"), f"{self.get_string('env_created')} '{nombre_entorno}' usando {python_interpreter}")
            
        except subprocess.CalledProcessError as e:
            QMessageBox.warning(self, self.get_string("error"), f"{self.get_string('venv_error')}\n\nDetalle:\n{e.stderr}")
        except FileNotFoundError:
            QMessageBox.warning(self, self.get_string("error"), f"{self.get_string('venv_error')}\n\nDetalle: El intérprete de Python en '{python_interpreter}' no fue encontrado.")
        except Exception as e:
            QMessageBox.warning(self, self.get_string("error"), f"{self.get_string('venv_error')}\n\nDetalle:\n{str(e)}")


    def eliminar_entorno(self):
        item_actual = self.lista_entornos.currentItem()
        if item_actual:
            # Obtener el nombre del entorno del widget personalizado
            widget = self.lista_entornos.itemWidget(item_actual)
            if widget:
                labels = widget.findChildren(QLabel)
                if labels and len(labels) > 0:
                    nombre_entorno = labels[0].text()
                else:
                    # Fallback: obtener del texto del item
                    item_text = item_actual.text()
                    nombre_entorno = item_text.split('\n')[0]
            else:
                # Fallback: obtener del texto del item
                item_text = item_actual.text()
                nombre_entorno = item_text.split('\n')[0]
                
            ruta_entorno = item_actual.data(Qt.UserRole)
            base_path = os.path.dirname(ruta_entorno)

            respuesta = QMessageBox.question(self, self.get_string("delete_env"), f"{self.get_string('confirm_delete_env')} '{nombre_entorno}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if respuesta == QMessageBox.StandardButton.Yes:
                try:
                    subprocess.run(['rm', '-rf', ruta_entorno])

                    if os.path.exists(ARCHIVO_REGISTRO):
                        line_to_remove = f"{nombre_entorno}|{base_path}\n"
                        
                        with open(ARCHIVO_REGISTRO, "r") as log_file:
                            lineas = log_file.readlines()
                        
                        with open(ARCHIVO_REGISTRO, "w") as log_file:
                            for linea in lineas:
                                if linea.strip() != line_to_remove.strip(): 
                                    log_file.write(linea)

                    row = self.lista_entornos.row(item_actual)
                    self.lista_entornos.takeItem(row)
                    QMessageBox.information(self, self.get_string("success"), f"Entorno '{nombre_entorno}' eliminado correctamente.")

                except Exception as e:
                    QMessageBox.critical(self, self.get_string("error"), f"No se pudo eliminar el entorno: {str(e)}")

    def abrir_directorio_entorno(self):
        item_actual = self.lista_entornos.currentItem()
        if item_actual:
            ruta_entorno = item_actual.data(Qt.UserRole)
            subprocess.run(['xdg-open', ruta_entorno])

    def iniciar_entorno_terminal(self):
        item_actual = self.lista_entornos.currentItem()
        if item_actual:
            # Obtener el nombre del entorno del widget personalizado
            widget = self.lista_entornos.itemWidget(item_actual)
            if widget:
                labels = widget.findChildren(QLabel)
                if labels and len(labels) > 0:
                    nombre_entorno = labels[0].text()
                else:
                    # Fallback: obtener del texto del item
                    item_text = item_actual.text()
                    nombre_entorno = item_text.split('\n')[0]
            else:
                # Fallback: obtener del texto del item
                item_text = item_actual.text()
                nombre_entorno = item_text.split('\n')[0]
                
            ruta_entorno = item_actual.data(Qt.UserRole)

            terminal_seleccionada = self.seleccionar_terminal()
            if terminal_seleccionada:
                temp_script_path = "/tmp/activate_venv.sh"
                
                # Crear script de activación
                with open(temp_script_path, 'w') as temp_script:
                    temp_script.write("#!/bin/bash\n")
                    temp_script.write(f"source \"{ruta_entorno}/bin/activate\"\n") 
                    temp_script.write(f"echo \"Entorno virtual activado: {nombre_entorno}\"\n")
                    temp_script.write(f"echo \"Directorio: {ruta_entorno}\"\n")
                    temp_script.write(f"echo \"\"\n")
                    temp_script.write("exec bash\n")

                os.chmod(temp_script_path, 0o755)

                try:
                    executable = terminal_seleccionada['ruta']
                    
                    if terminal_seleccionada['tipo'] == 'sistema':
                        if terminal_seleccionada['nombre'] == "Deepin Terminal":
                            # SOLUCIÓN SIMPLE PARA DEEPIN TERMINAL (como en tu versión que funciona)
                            subprocess.Popen([executable, '-e', temp_script_path])
                            
                        elif terminal_seleccionada['nombre'] == "GNOME Terminal":
                            subprocess.Popen([executable, '--', '/bin/bash', '-i', '-c', temp_script_path])
                            
                        else:
                            # Para otras terminales, usar la lógica del template
                            comando_template = terminal_seleccionada['comando']
                            command_to_run = f"bash --init-file {temp_script_path}"
                            comando_final = comando_template.format(command=command_to_run)
                            args_list = shlex.split(comando_final, posix=True)
                            full_command = [executable] + args_list
                            subprocess.Popen(full_command)
                            
                    elif terminal_seleccionada['tipo'] == 'personalizado':
                        custom_command = terminal_seleccionada['comando'].replace('{script}', temp_script_path)
                        subprocess.Popen(['bash', '-c', custom_command])
                        
                except Exception as e:
                    QMessageBox.critical(self, self.get_string("error"), f"{self.get_string('terminal_error')}: {str(e)}")

    def buscar_entornos_existentes(self):
        """Permite al usuario seleccionar una carpeta para escanear y añadir entornos venv existentes."""
        dir_to_scan = QFileDialog.getExistingDirectory(
            self, 
            self.get_string("select_scan_directory"), 
            QDir.homePath()
        )
        
        if not dir_to_scan:
            return

        registered_paths = set()
        if os.path.exists(ARCHIVO_REGISTRO):
            with open(ARCHIVO_REGISTRO, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    try:
                        nombre, base_path = line.split('|', 1)
                        registered_paths.add(os.path.join(base_path, nombre))
                    except ValueError:
                        # Formato antiguo
                        registered_paths.add(os.path.join(self.config.get('directorio_base_env', CONFIG_BASE_DIR), line))

        found_new_envs = []
        
        for item in os.listdir(dir_to_scan):
            env_path = os.path.join(dir_to_scan, item)
            
            activate_script_path = os.path.join(env_path, 'bin', 'activate')
            
            if os.path.isdir(env_path) and os.path.exists(activate_script_path):
                if env_path not in registered_paths:
                    found_new_envs.append((item, dir_to_scan)) 

        if not found_new_envs:
            QMessageBox.information(self, self.get_string("success"), self.get_string("no_new_envs_found"))
            return

        # Usar siempre el nuevo formato al guardar
        with open(ARCHIVO_REGISTRO, "a") as log_file:
            for env_name, base_path in found_new_envs:
                log_file.write(f"{env_name}|{base_path}\n")
        
        # Actualizar el registro a nuevo formato si es necesario
        self.actualizar_registro_a_nuevo_formato()
        
        self.lista_entornos.clear()
        self.cargar_entornos_desde_registro()
        
        QMessageBox.information(
            self, 
            self.get_string("success"), 
            self.get_string("added_new_envs") % len(found_new_envs)
        )

    def mostrar_acerca_de(self):
        acerca_de_dialogo = QDialog(self)
        acerca_de_dialogo.setWindowTitle(self.get_string("about_title"))
        acerca_de_dialogo.setFixedSize(400, 200)

        layout = QVBoxLayout(acerca_de_dialogo)
        label = QLabel(self.get_string("about_content"))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        close_button = QPushButton(self.get_string("close"))
        close_button.clicked.connect(acerca_de_dialogo.close)
        layout.addWidget(close_button)

        acerca_de_dialogo.exec()


def main():
    app = QApplication(sys.argv)
    
    if not os.path.exists(TRANSLATIONS_DIR):
        os.makedirs(TRANSLATIONS_DIR)

    app.setStyleSheet(DARK_STYLE)

    window = CreadorEntornos()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()