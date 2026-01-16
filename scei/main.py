
import sys
import os

# Asegurar que el directorio raíz está en el path para imports absolutos si se corre directo
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from PyQt6.QtWidgets import QApplication, QDialog

# Imports locales asumiendo estructura de paquete 'scei' o local
try:
    from scei.bootstrap import run_bootstrap
    from scei.logger import load_logs
    from scei.utils import apply_light_theme
    from scei.ui.dialogs import LoginDialog
    from scei.ui.window import MainWindow
except ImportError:
    # Fallback si se ejecuta dentro de la carpeta scei
    from bootstrap import run_bootstrap
    from logger import load_logs
    from utils import apply_light_theme
    from ui.dialogs import LoginDialog
    from ui.window import MainWindow

def run():
    # Inicialización de BD y recursos
    run_bootstrap()
    load_logs()

    
    # Iniciar App
    app = QApplication(sys.argv)
    
    # Apply Global Premium Theme (Loaded from resources/theme/light.qss)
    app.setStyle("Fusion") 
    apply_light_theme(app)
    
    # Login Modal
    login = LoginDialog()
    if login.exec() != QDialog.DialogCode.Accepted:
        sys.exit(0)
    
    # Ventana Principal
    win = MainWindow()
    win.resize(1200, 600)
    win.showMaximized()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    run()
