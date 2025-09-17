import threading
import time

class AnimacionPensando:
    def __init__(self):
        self.pensando_terminado = None
        self.hilo_pensando = None
    
    def iniciar(self):
        """Iniciar animación de 'pensando...'"""
        self.pensando_terminado = threading.Event()
        self.hilo_pensando = threading.Thread(target=self._mostrar_animacion)
        self.hilo_pensando.start()
    
    def detener(self):
        """Detener animación"""
        if self.pensando_terminado:
            self.pensando_terminado.set()
        if self.hilo_pensando:
            self.hilo_pensando.join()
    
    def _mostrar_animacion(self):
        """Mostrar animación de puntos"""
        puntos = 0
        while not self.pensando_terminado.is_set():
            print(f"\rPensando{'.' * (puntos % 4):<3}", end='', flush=True)
            puntos += 1
            time.sleep(0.5)

def formatear_mensaje(speaker, mensaje):
    """Formatear mensaje para mostrar en consola"""
    emojis = {
        'user': '🗣️ ',
        'ai': '🤖 ',
        'system': '⚙️ '
    }
    
    emoji = emojis.get(speaker, '')
    return f"{emoji} {speaker.capitalize()}: {mensaje}"