
import cv2
import numpy as np
import pickle
import os
import sys
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox, QComboBox
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap

from ..utils import load_icon
from ..data.repositories import update_user_profile


class FacialData:
    def __init__(self):
        # Verificar existencia de módulo face (contrib)
        if not hasattr(cv2, 'face'):
            raise Exception("El módulo 'cv2.face' no está disponible. Instale opencv-contrib-python.")

        # Resolver path del haarcascade robustamente para PyInstaller
        cascade_fn = 'haarcascade_frontalface_default.xml'
        cascade_path = os.path.join(cv2.data.haarcascades, cascade_fn)
        
        # En modo frozen onefile, a veces cv2.data.haarcascades falla o apunta mal.
        # Intentamos buscar en _MEIPASS si existe.
        if not os.path.exists(cascade_path):
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                # Intento 1: root del temp
                p1 = os.path.join(sys._MEIPASS, cascade_fn)
                # Intento 2: dentro de cv2/data (si se incluyó así)
                p2 = os.path.join(sys._MEIPASS, 'cv2', 'data', cascade_fn)
                
                if os.path.exists(p1):
                    cascade_path = p1
                elif os.path.exists(p2):
                    cascade_path = p2
        
        if not os.path.exists(cascade_path):
            # Fallback final: intentar cargar directo esperando que cv2 lo resuelva interno
            cascade_path = cascade_fn

        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            # Si falló, intentar una carga cruda por si cv2 lo tiene en built-ins
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + cascade_fn)
            if self.face_cascade.empty():
                 raise FileNotFoundError(f"No se pudo cargar el modelo Haar Cascade: {cascade_fn}")

        # Reconocedor LBPH
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()

    def train_and_serialize(self, images, labels):
        # images: lista de arrays numpy (roi gray)
        # labels: lista de ids (int)
        self.recognizer.train(images, np.array(labels))
        # Serializar modelo a bytes
        # OpenCV no tiene un "dumps" directo para el modelo completo en Python fácilmente portable,
        # pero para un solo usuario podemos guardar el histograma o usar write a archivo temporal.
        # TRUCO: LBPH es chico. Para simplificar en User unico, guardaremos las IMÁGENES DE ENTRENAMIENTO
        # o un modelo YML.
        # Mejor enfoque para este caso: Guardar el modelo en un archivo temporal y leer los bytes.
        import tempfile, os
        fd, path = tempfile.mkstemp('.yml')
        os.close(fd)
        self.recognizer.save(path)
        with open(path, 'rb') as f:
            data = f.read()
        os.remove(path)
        return data

    def load_from_bytes(self, data):
        if not data: return False
        import tempfile, os
        fd, path = tempfile.mkstemp('.yml')
        os.write(fd, data)
        os.close(fd)
        try:
            self.recognizer.read(path)
            os.remove(path)
            return True
        except:
            if os.path.exists(path): os.remove(path)
            return False

class FaceCaptureDialog(QDialog):
    def __init__(self, user_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración Facial")
        self.setWindowIcon(load_icon("scan.svg"))
        self.setFixedSize(600, 500)
        self.user_id = user_id
        
        # UI
        layout = QVBoxLayout(self)
        
        self.lbl_info = QLabel("Mira a la cámara. Se tomarán 40 fotos para entrenar tu perfil.")
        self.lbl_info.setWordWrap(True)
        self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_info)
        
        self.video_label = QLabel()
        self.video_label.setFixedSize(540, 380)
        self.video_label.setStyleSheet("background: #000; border: 2px solid #333;")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.video_label, 0, Qt.AlignmentFlag.AlignHCenter)
        
        self.btn_start = QPushButton("Iniciar Captura")
        self.btn_start.clicked.connect(self.start_capture)
        self.btn_start.setProperty("class", "primary")
        layout.addWidget(self.btn_start)
        
        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        
        self.capturing = False
        self.count = 0
        self.max_samples = 40
        self.samples = []
        try:
            self.face_helper = FacialData()
        except Exception as e:
            self.face_helper = None
            self.lbl_info.setText(f"Error inicializando biometría: {str(e)}")
            self.btn_start.setEnabled(False)

    def start_capture(self):
        if not self.face_helper:
            QMessageBox.critical(self, "Error", "El sistema biométrico no está disponible.")
            return

        if self.cap is None:
            # Use CAP_DSHOW on Windows for faster init
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)
        
        if not self.cap.isOpened():
            QMessageBox.warning(self, "Error", "No se detectó cámara web.")
            return
            
        self.capturing = True
        self.count = 0
        self.samples = []
        self.btn_start.setEnabled(False)
        self.btn_start.setText("Capturando...")
        self.timer.start(30) # ~30fps

    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret: return
        
        frame = cv2.flip(frame, 1) # Espejo
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_helper.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        for (x,y,w,h) in faces:
            cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)
            
            if self.capturing and self.count < self.max_samples:
                # Guardar ROI
                self.samples.append(gray[y:y+h, x:x+w])
                self.count += 1
                self.lbl_info.setText(f"Capturando: {self.count}/{self.max_samples}")
            
        # Convert to Qt
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(qt_img).scaled(self.video_label.size(), Qt.AspectRatioMode.KeepAspectRatio))
        
        if self.capturing and self.count >= self.max_samples:
            self.finish_training()

    def finish_training(self):
        self.capturing = False
        self.timer.stop()
        self.lbl_info.setText("Procesando modelo biométrico... Espere.")
        QTimer.singleShot(100, self._process_model)

    def _process_model(self):
        try:
            # Entrenar modelo solo con este usuario (ID arbitrario 1, ya que guardamos 1 modelo por usuario en BD)
            labels = [1] * len(self.samples)
            blob = self.face_helper.train_and_serialize(self.samples, labels)
            
            # Guardar en BD
            update_user_profile(self.user_id, {"face_data": blob})
            
            QMessageBox.information(self, "Éxito", "Reconocimiento facial configurado correctamente.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Fallo al guardar biometría: {e}")
            self.reject()
        finally:
            if self.cap: self.cap.release()

    def closeEvent(self, event):
        if self.cap: self.cap.release()
        self.timer.stop()
        super().closeEvent(event)


class FaceLoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login Facial")
        self.setWindowIcon(load_icon("scan.svg"))
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout(self)
        self.lbl = QLabel("Buscando rostro...")
        self.lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl)
        
        self.video = QLabel()
        self.video.setFixedSize(480, 320)
        self.video.setStyleSheet("background: #000")
        self.video.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.video, 0, Qt.AlignmentFlag.AlignHCenter)
        
        self.cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.scan)
        
        self.helpers = {} # map user_id -> recognizer
        self.users_map = {} # map user_id -> username
        self.matches_consecutive = 0
        self.detected_user = None

        # Postpone heavyweight init to avoid freezing UI on show
        QTimer.singleShot(100, self.startup)

    def startup(self):
        # 1. Load models first
        self.load_models()
        
        if not self.helpers:
            QMessageBox.warning(self, "Aviso", "No hay usuarios con biometría configurada.")
            self.reject()
            return

        # 2. Init Camera
        try:
            # Use CAP_DSHOW on Windows
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap or not self.cap.isOpened():
                 self.cap = cv2.VideoCapture(0)
            
            if not self.cap or not self.cap.isOpened():
                QMessageBox.critical(self, "Error", "No se detectó cámara web.")
                self.reject()
                return
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al iniciar cámara: {e}")
            self.reject()
            return
            
        self.timer.start(100) # Scan mas lento para no saturar

    def load_models(self):
        from ..data.repositories import session_scope
        from ..data.models import User
        with session_scope() as session:
            users = session.query(User).filter(User.face_data != None).all()
            for u in users:
                try:
                    helper = FacialData()
                    if helper.load_from_bytes(u.face_data):
                        self.helpers[u.id] = helper
                        self.users_map[u.id] = u.username
                except Exception:
                    # Si falla al cargar FacialData (ej. haarcascade missing), saltar este usuario
                    continue

    def scan(self):
        ret, frame = self.cap.read()
        if not ret: return
        
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Usamos helper generico para cascade
        generic = FacialData()
        faces = generic.face_cascade.detectMultiScale(gray, 1.3, 5)
        
        found_id = None
        min_conf = 100 # LBPH: Menor es mejor. < 50 es muy buena coincidencia.
        
        for (x,y,w,h) in faces:
            cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,255), 2)
            roi = gray[y:y+h, x:x+w]
            
            # Probar contra todos los modelos cargados
            for uid, helper in self.helpers.items():
                try:
                    lid, conf = helper.recognizer.predict(roi)
                    # lid siempre será 1 porque entrenamos asi. Lo importante es 'conf'
                    if conf < 60: # Threshold aceptable
                        if conf < min_conf:
                            min_conf = conf
                            found_id = uid
                except:
                    pass
        
        # Render
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt = QImage(rgb.data, w, h, ch*w, QImage.Format.Format_RGB888)
        self.video.setPixmap(QPixmap.fromImage(qt).scaled(self.video.size(), Qt.AspectRatioMode.KeepAspectRatio))
        
        if found_id:
            if self.detected_user == found_id:
                self.matches_consecutive += 1
            else:
                self.detected_user = found_id
                self.matches_consecutive = 0
                
            if self.matches_consecutive > 5: # 5 frames seguidos confirmando
                self.authenticated_user = self.users_map[found_id]
                self.accept()
        else:
            self.matches_consecutive = 0

    def closeEvent(self, e):
        if self.cap: self.cap.release()
        self.timer.stop()
        super().closeEvent(e)
