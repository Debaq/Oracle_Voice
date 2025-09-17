import os
import tempfile
import subprocess
import pyaudio
import wave
from config import PIPER_EXECUTABLE, PIPER_DATA_DIR, MODELO_VOZ, BASE_DIR

class PiperTTS:
    def __init__(self):
        self.piper_executable = PIPER_EXECUTABLE
        self.piper_data_dir = PIPER_DATA_DIR
        self.modelo_voz = MODELO_VOZ
        self.base_dir = BASE_DIR
  
    def speak(self, texto):
        """Convertir texto a voz y reproducir"""
        try:
            # Limpiar el texto antes de enviarlo a Piper
            texto_limpio = self._limpiar_texto(texto)
            
            modelo_path = os.path.join(self.piper_data_dir, self.modelo_voz)
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                output_file = temp_file.name
            
            # Configurar entorno
            piper_dir = os.path.join(self.base_dir, "piper")
            env = os.environ.copy()
            env['LD_LIBRARY_PATH'] = f"{piper_dir}:{env.get('LD_LIBRARY_PATH', '')}"
            env['ESPEAK_DATA_PATH'] = os.path.join(piper_dir, "espeak-ng-data")
            
            # Crear archivo temporal con el texto limpio
            with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as texto_file:
                texto_file.write(texto_limpio)
                texto_file_path = texto_file.name
            
            # Ejecutar piper directamente
            cmd = [self.piper_executable, '--model', modelo_path, '--output_file', output_file]
            
            with open(texto_file_path, 'r', encoding='utf-8') as input_file:
                result = subprocess.run(cmd, stdin=input_file, capture_output=True, 
                                    text=True, timeout=30, env=env)
            
            # Limpiar archivo de texto
            os.remove(texto_file_path)
            
            if result.returncode == 0 and os.path.exists(output_file):
                # Reproducir usando PyAudio directamente
                self._reproducir_wav(output_file)
                os.remove(output_file)
                return True
            else:
                print(f"Error en Piper: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Error TTS: {e}")
            return False

    def _limpiar_texto(self, texto):
        """Limpiar texto eliminando símbolos innecesarios pero manteniendo puntuación y números"""
        import re
        
        # Preservar - entre números (menos)
        texto = re.sub(r'(\d)\s*-\s*(\d)', r'\1 menos \2', texto)
        
        # Eliminar símbolos innecesarios (reemplazar por espacio)
        simbolos_eliminar = ['*', '[', ']', '>', '<', '#', '@', '{', '}', '|', '\\', '^', '~', '`']
        for simbolo in simbolos_eliminar:
            texto = texto.replace(simbolo, ' ')
        
        # Eliminar guiones que no son entre números
        texto = re.sub(r'-', ' ', texto)
        
        # Limpiar espacios múltiples
        texto = re.sub(r'\s+', ' ', texto).strip()
        
        return texto
        
    def _reproducir_wav(self, archivo_wav):
        """Reproducir archivo WAV usando PyAudio"""
        try:
            with wave.open(archivo_wav, 'rb') as wf:
                # Configurar PyAudio para reproducción
                p = pyaudio.PyAudio()
                
                stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                               channels=wf.getnchannels(),
                               rate=wf.getframerate(),
                               output=True)
                
                # Leer y reproducir el archivo por chunks
                chunk_size = 1024
                data = wf.readframes(chunk_size)
                
                while data:
                    stream.write(data)
                    data = wf.readframes(chunk_size)
                
                # Limpiar
                stream.stop_stream()
                stream.close()
                p.terminate()
                
        except Exception as e:
            print(f"Error reproduciendo audio: {e}")
    
    def verificar_configuracion(self):
        """Verificar que Piper y el modelo estén disponibles"""
        if not os.path.exists(self.piper_executable):
            print(f"❌ Error: No se encuentra Piper en: {self.piper_executable}")
            return False
        
        modelo_path = os.path.join(self.piper_data_dir, self.modelo_voz)
        if not os.path.exists(modelo_path):
            print(f"❌ Error: No se encuentra el modelo: {modelo_path}")
            print(f"📁 Directorio piper_data: {self.piper_data_dir}")
            if os.path.exists(self.piper_data_dir):
                print("Modelos disponibles:")
                for f in os.listdir(self.piper_data_dir):
                    if f.endswith('.onnx'):
                        print(f"  - {f}")
            return False
        
        print(f"✅ Piper configurado correctamente")
        print(f"📁 Modelo de voz: {self.modelo_voz}")
        return True