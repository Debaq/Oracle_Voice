import os
import sys

# Detectar si estamos ejecutando desde PyInstaller
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# CONFIGURACIÓN - EDITA AQUÍ
API_KEY = "ca36d471ff014587928191ebb8f4f58c.ig5CnGJG9VFTIgYN"
MODELO_VOZ = "es_MX-mario-medium.onnx"

# RUTAS
PIPER_EXECUTABLE = os.path.join(BASE_DIR, "piper", "piper")
PIPER_DATA_DIR = os.path.join(BASE_DIR, "piper_data")
VOSK_MODEL_DIR = os.path.join(BASE_DIR, "vosk-model-small-es-0.42")

# BIGMODEL API
BIGMODEL_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"