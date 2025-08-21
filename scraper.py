from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed


class ScrapingEngine:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def es_parrafo_valido(self, texto: str) -> bool:
        """Filtros mejorados para párrafos válidos"""
        if len(texto.strip()) < 50:  # Párrafos muy cortos
            return False
        
        frases_invalidas = [
            "Fuente de la imagen", "Getty Images", "AFP", "Reuters", "EPA",
            "BBC", "Pie de foto", "Copyright", "Derechos de autor",
            "Suscríbete", "Síguenos", "Compartir", "Facebook", "Twitter"
        ]
        
        return not any(frase.lower() in texto.lower() for frase in frases_invalidas)

    def extraer_contenido_articulo(self, url: str) -> Optional[List[str]]:
        """Extrae contenido de un artículo con manejo de errores mejorado"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Buscar diferentes selectores de contenido
            selectores = [
                'div[data-component="text-block"] p',
                'div.rich-text p',
                'article p',
                'div.story-body p',
                '.content p'
            ]
            
            parrafos = []
            for selector in selectores:
                elementos = soup.select(selector)
                if elementos:
                    parrafos = [p.get_text(strip=True) for p in elementos]
                    break
            
            # Fallback a todos los párrafos
            if not parrafos:
                parrafos = [p.get_text(strip=True) for p in soup.find_all("p")]
            
            # Filtrar párrafos válidos
            parrafos_validos = [p for p in parrafos if self.es_parrafo_valido(p)]
            
            return parrafos_validos[:10]  # Limitar a 10 párrafos por artículo
            
        except Exception as e:
            print(f"Error extrayendo {url}: {e}")
            return None

    def obtener_enlaces_noticias(self) -> List[Dict[str, str]]:
        """Obtiene enlaces de noticias de manera más eficiente"""
        url = "https://www.bbc.com/mundo/topics/cg726188yd2t"
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            enlaces_encontrados = []

            # Buscar enlaces con patrones mejorados
            for enlace in soup.find_all("a", href=True):
                href = enlace["href"]
                if "/mundo/articles/" in href or "/mundo/noticias/" in href:
                    titulo = enlace.get_text(strip=True)
                    if titulo and len(titulo) > 10:  # Filtrar títulos muy cortos
                        link_completo = href if href.startswith("http") else "https://www.bbc.com" + href
                        enlaces_encontrados.append({
                            "titulo": titulo,
                            "link": link_completo
                        })

            # Eliminar duplicados manteniendo el orden
            seen = set()
            enlaces_unicos = []
            for enlace in enlaces_encontrados:
                if enlace["link"] not in seen:
                    seen.add(enlace["link"])
                    enlaces_unicos.append(enlace)

            return enlaces_unicos[:15]  # Limitar a 15 artículos

        except Exception as e:
            print(f"Error obteniendo enlaces: {e}")
            return []

    def procesar_articulo(self, enlace: Dict[str, str]) -> Optional[Dict]:
        """Procesa un artículo individual"""
        contenido = self.extraer_contenido_articulo(enlace["link"])
        if contenido:
            return {
                "titulo": enlace["titulo"],
                "link": enlace["link"],
                "contenido": contenido
            }
        return None

    def obtener_noticias_paralelo(self, callback=None) -> List[Dict]:
        """Obtiene noticias usando procesamiento paralelo"""
        print("Obteniendo enlaces...")
        if callback:
            callback("Obteniendo enlaces de noticias...")

        enlaces = self.obtener_enlaces_noticias()
        if not enlaces:
            return []

        print(f"Procesando {len(enlaces)} artículos...")
        if callback:
            callback(f"Procesando {len(enlaces)} artículos...")

        noticias = []
        
        # Procesar artículos en paralelo con ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Enviar todos los trabajos
            future_to_enlace = {
                executor.submit(self.procesar_articulo, enlace): enlace 
                for enlace in enlaces
            }
            
            # Recopilar resultados conforme se completan
            for i, future in enumerate(as_completed(future_to_enlace)):
                if callback:
                    callback(f"Procesando artículo {i+1}/{len(enlaces)}...")
                
                try:
                    resultado = future.result(timeout=15)
                    if resultado:
                        noticias.append(resultado)
                except Exception as e:
                    print(f"Error procesando artículo: {e}")

        print(f"Se obtuvieron {len(noticias)} noticias válidas")
        return noticias