#!/usr/bin/env python3
"""
Asistente de Voz con IA - Versión Modular
"""
import sys
import os
import json
from config import BASE_DIR
from ai.chat import BigModelChat
from audio.text_to_speech import PiperTTS
from audio.speech_to_text import VoskSTT
from utils.helpers import AnimacionPensando, formatear_mensaje

class AsistenteVoz:
    def __init__(self):
        # Inicializar componentes
        self.chat = BigModelChat()
        self.tts = PiperTTS()
        self.stt = VoskSTT()
        self.animacion = AnimacionPensando()
        
        self.running = False
        self.config_flujo = self._cargar_configuracion()
    
    def _cargar_configuracion(self):
        """Cargar la configuración de la secuencia de preguntas desde un archivo JSON"""
        try:
            with open('config_secuencia.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("❌ Error: No se encuentra el archivo 'config_secuencia.json'")
            return None
    
    def verificar_configuracion(self):
        """Verificar que todos los componentes estén listos"""
        print("🎤 Asistente de Voz con IA - Lector de Suerte")
        print("=" * 40)
        print(f"📂 Directorio base: {BASE_DIR}")
        
        if not self.config_flujo:
            return False
            
        # Verificar TTS
        if not self.tts.verificar_configuracion():
            return False
        
        # Verificar STT
        if not self.stt.initialize():
            print("❌ No se pudo configurar Vosk")
            return False
        
        return True
    
    def iniciar(self):
        """Iniciar el asistente"""
        if not self.verificar_configuracion():
            return
        
        if not self.stt.start_listening():
            print("❌ No se pudo iniciar la escucha")
            return
        
        self.running = True
        print("🎯 Sistema listo (Ctrl+C para salir)")
        print("-" * 40)
        
        try:
            self._bucle_principal()
        except KeyboardInterrupt:
            print("\n👋 Deteniendo asistente...")
        finally:
            self.detener()
            
    def _bucle_principal(self):
        """Bucle principal de escucha y respuesta"""
        print(f"\n{formatear_mensaje('ai', self.config_flujo['bienvenida'])}")
        self.tts.speak(self.config_flujo['bienvenida'])
        
        datos_usuario = {}
        
        # Bucle para las preguntas secuenciales
        for paso in self.config_flujo['preguntas_secuencia']:
            pregunta = paso['pregunta']
            variable = paso['variable']
            
            print(f"\n{formatear_mensaje('ai', pregunta)}")
            self.tts.speak(pregunta)
            
            respuesta_obtenida = None
            while not respuesta_obtenida:
                texto_completo, texto_parcial = self.stt.listen_once()
                if texto_completo:
                    respuesta_obtenida = texto_completo
                    print(f"\n{formatear_mensaje('user', respuesta_obtenida)}")
                elif texto_parcial:
                    print(f"👂 Escuchando: {texto_parcial}", end='\r')
            
            datos_usuario[variable] = respuesta_obtenida
            
        # Pregunta final para la elección del tema
        tema_elegido = None
        pregunta_tema = self.config_flujo['pregunta_tema']
        print(f"\n{formatear_mensaje('ai', pregunta_tema)}")
        self.tts.speak(pregunta_tema)
        while not tema_elegido:

            
            texto_completo, texto_parcial = self.stt.listen_once()
            if texto_completo:
                texto_completo = texto_completo.lower()
                
                amor_keywords = ['amor', 'corazón', 'pareja', 'relación']
                trabajo_keywords = ['trabajo', 'empleo', 'carrera', 'profesional']
                finanzas_keywords = ['finanzas', 'dinero', 'riqueza', 'fortuna']
                
                if any(word in texto_completo for word in amor_keywords):
                    tema_elegido = 'amor'
                elif any(word in texto_completo for word in trabajo_keywords):
                    tema_elegido = 'trabajo'
                elif any(word in texto_completo for word in finanzas_keywords):
                    tema_elegido = 'finanzas'
                else:
                    print(f"\n{formatear_mensaje('ai', 'No entendí el tema, por favor repite.')}")
                    self.tts.speak("No entendí el tema, por favor repite.")
            elif texto_parcial:
                print(f"👂 Escuchando: {texto_parcial}", end='\r')

        # --- CAMBIOS AQUI ---
        # 1. Importar la biblioteca datetime para obtener la fecha y hora
        from datetime import datetime

        # 2. Obtener la fecha y hora actual
        fecha_actual = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        
        # 3. Construir el mensaje final para el LLM, incluyendo la fecha
        prompt_final = self.config_flujo['instrucciones_llm']
        prompt_final = prompt_final.replace('{tema_elegido}', tema_elegido)
        
        # Agregar la fecha actual como el primer dato
        datos_str = f"Fecha actual: {fecha_actual}\n"
        for key, value in datos_usuario.items():
            datos_str += f"{key.capitalize()}: {value}\n"
        
        prompt_final += "\n" + datos_str.strip()
        
        # Obtener respuesta del LLM
        print("\n🔮 Buscando tu suerte...")
        self.animacion.iniciar()
        respuesta = self.chat.send_message(prompt_final)
        self.animacion.detener()
        
        # Mostrar y reproducir respuesta
        print(f"\r{formatear_mensaje('ai', respuesta)}")
        print("🔊 Reproduciendo respuesta...")
        self.tts.speak(respuesta)
        
        print("-" * 40)
        print(f"\n{formatear_mensaje('ai', 'Gracias por usar el asistente. Puedes detenerlo con Ctrl+C.')}")
    
    def detener(self):
        """Detener el asistente"""
        self.running = False
        self.stt.stop_listening()
        self.animacion.detener()

def main():
    """Función principal"""
    asistente = AsistenteVoz()
    asistente.iniciar()

if __name__ == "__main__":
    main()