import requests
from config import API_KEY, BIGMODEL_URL

class BigModelChat:
    def __init__(self):
        self.api_key = API_KEY
        self.url = BIGMODEL_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def send_message(self, mensaje):
        """Enviar mensaje a BigModel y obtener respuesta"""
        data = {
            "model": "glm-4-flash",
            "messages": [{"role": "user", "content": mensaje}],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(self.url, headers=self.headers, json=data)
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                return f"Error: {response.status_code}"
        except Exception as e:
            return f"Error de conexión: {str(e)}"