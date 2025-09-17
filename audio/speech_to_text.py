import os
import json
import zipfile
import requests
import vosk
import pyaudio
from config import VOSK_MODEL_DIR

class VoskSTT:
    def __init__(self):
        self.vosk_model_dir = VOSK_MODEL_DIR
        self.model = None
        self.recognizer = None
        self.audio_stream = None
        self.pyaudio_instance = None
    
    def initialize(self):
        """Inicializar Vosk y configurar modelo"""
        modelo_path = self._configurar_modelo()
        if not modelo_path:
            return False
        
        try:
            self.model = vosk.Model(modelo_path)
            self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
            return True
        except Exception as e:
            print(f"Error inicializando Vosk: {e}")
            return False
    
    def start_listening(self):
        """Iniciar captura de audio"""
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            self.audio_stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=8000
            )
            self.audio_stream.start_stream()
            return True
        except Exception as e:
            print(f"Error iniciando audio: {e}")
            return False
    
    def listen_once(self):
        """Escuchar una vez y devolver texto reconocido o None"""
        if not self.audio_stream or not self.recognizer:
            return None, None
        
        try:
            data = self.audio_stream.read(4000, exception_on_overflow=False)
            
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                if result.get('text'):
                    return result['text'], None
            else:
                partial = json.loads(self.recognizer.PartialResult())
                if partial.get('partial'):
                    return None, partial['partial']
            
            return None, None
        except Exception as e:
            print(f"Error en reconocimiento: {e}")
            return None, None
    
    def stop_listening(self):
        """Detener captura de audio"""
        try:
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            if self.pyaudio_instance:
                self.pyaudio_instance.terminate()
        except Exception as e:
            print(f"Error deteniendo audio: {e}")
    
    def _configurar_modelo(self):
        """Configurar modelo Vosk (usar incluido o descargar)"""
        # Intentar usar el modelo incluido primero
        if os.path.exists(self.vosk_model_dir):
            print(f"Usando modelo Vosk incluido: {self.vosk_model_dir}")
            return self.vosk_model_dir
        
        # Si no existe, buscar en directorio actual (modo desarrollo)
        for item in os.listdir("."):
            if item.startswith("vosk-model-small-es") and os.path.isdir(item):
                print(f"Modelo Vosk encontrado: {item}")
                return item
        
        # Como último recurso, descargar
        return self._descargar_modelo()
    
    def _descargar_modelo(self):
        """Descargar modelo Vosk si no existe"""
        modelo_zip = "vosk-model-small-es-0.42.zip"
        modelo_url = "https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip"
        
        print("Descargando modelo Vosk en español...")
        try:
            response = requests.get(modelo_url, stream=True)
            
            with open(modelo_zip, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print("Extrayendo modelo...")
            with zipfile.ZipFile(modelo_zip, 'r') as zip_ref:
                zip_ref.extractall(".")
            
            os.remove(modelo_zip)
            
            for item in os.listdir("."):
                if item.startswith("vosk-model-small-es") and os.path.isdir(item):
                    print(f"Modelo Vosk extraído en {item}")
                    return item
            
            return None
        except Exception as e:
            print(f"Error descargando modelo: {e}")
            return None