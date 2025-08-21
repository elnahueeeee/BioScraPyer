import requests
from typing import List


class NoticiasAPI:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def pedir_resumen(self, texto: str) -> str:
        """Solicita resumen con timeout y manejo de errores mejorado"""
        url = f"{self.base_url}/resumir"
        try:
            response = self.session.post(
                url, 
                json={"contenido": texto},
                timeout=30,  # timeout de 30 segundos
                headers={'ngrok-skip-browser-warning': 'true'}
            )
            if response.status_code == 200:
                return response.json()["resumen"]
            else:
                return f"Error del servidor: {response.status_code}"
        except requests.exceptions.Timeout:
            return "Timeout: El servidor tardó demasiado en responder"
        except requests.exceptions.ConnectionError:
            return "Error: No se pudo conectar al servidor"
        except Exception as e:
            return f"Error: {str(e)}"

    def resumir_batch(self, textos: List[str]) -> List[str]:
        """Procesa múltiples textos en paralelo"""
        url = f"{self.base_url}/resumir_batch"
        try:
            response = self.session.post(
                url,
                json={"contenidos": textos},
                timeout=60,
                headers={'ngrok-skip-browser-warning': 'true'}
            )
            if response.status_code == 200:
                return response.json()["resumenes"]
            else:
                # Fallback a procesamiento individual
                return [self.pedir_resumen(texto) for texto in textos]
        except:
            # Fallback a procesamiento individual
            return [self.pedir_resumen(texto) for texto in textos]