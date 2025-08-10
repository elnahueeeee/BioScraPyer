import customtkinter as ctk
import requests
from bs4 import BeautifulSoup
import webbrowser
import threading
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
import re


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


class App:
    def __init__(self, root):
        self.root = root
        self.noticias = []
        self.indice_actual = 0
        self.scraper = ScrapingEngine()
        self.api = NoticiasAPI("https://8efcd9ae6d70.ngrok-free.app/")  # Cambiar por tu URL
        
        self.setup_ui()

    def setup_ui(self):
        """Configura la interfaz de usuario"""
        self.root.title("Noticias sobre Cambio Climático - Optimizado")
        self.root.geometry("900x700")
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.frame = ctk.CTkFrame(self.root)
        self.frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Botones superiores
        self.frame_botones = ctk.CTkFrame(self.frame)
        self.frame_botones.pack(pady=(10, 5), fill="x")

        self.boton_buscar = ctk.CTkButton(
            self.frame_botones, 
            text="🔍 Buscar noticias", 
            command=self.buscar_async,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.boton_buscar.pack(side="left", padx=10)

        self.boton_resumir_todo = ctk.CTkButton(
            self.frame_botones, 
            text="📝 Resumir todo", 
            command=self.resumir_todo_async,
            font=ctk.CTkFont(size=14)
        )
        self.boton_resumir_todo.pack(side="left", padx=10)

        # Barra de progreso
        self.barra_progreso = ctk.CTkProgressBar(
            self.frame, 
            orientation="horizontal", 
            mode="indeterminate", 
            width=700,
            height=20
        )
        
        # Estado
        self.etiqueta_estado = ctk.CTkLabel(
            self.frame, 
            text="Listo para buscar noticias",
            font=ctk.CTkFont(size=12)
        )
        self.etiqueta_estado.pack(pady=(5, 5))

        self.etiqueta_contador = ctk.CTkLabel(
            self.frame, 
            text="0 noticias encontradas",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.etiqueta_contador.pack(pady=(0, 10))

        # Título
        self.titulo_label = ctk.CTkLabel(
            self.frame, 
            text="", 
            font=ctk.CTkFont(size=22, weight="bold"), 
            wraplength=800, 
            justify="center"
        )
        self.titulo_label.pack(pady=(10, 0))

        # Caja de texto principal
        self.caja_texto = ctk.CTkTextbox(
            self.frame, 
            wrap="word", 
            height=300,
            font=ctk.CTkFont(size=13)
        )
        self.caja_texto.pack(pady=(10, 5), fill="both", expand=True)

        # Link
        self.link_label = ctk.CTkLabel(
            self.frame, 
            text="", 
            font=ctk.CTkFont(size=11), 
            text_color="lightblue", 
            cursor="hand2"
        )
        self.link_label.pack(pady=(0, 10))
        self.link_label.bind("<Button-1>", lambda e: self.abrir_enlace())

        # Navegación
        self.frame_navegacion = ctk.CTkFrame(self.frame)
        self.frame_navegacion.pack(pady=10)

        self.boton_anterior = ctk.CTkButton(
            self.frame_navegacion, 
            text="← Anterior", 
            command=self.anterior, 
            width=120
        )
        self.boton_anterior.pack(side="left", padx=15)

        self.etiqueta_posicion = ctk.CTkLabel(
            self.frame_navegacion, 
            text="0/0",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.etiqueta_posicion.pack(side="left", padx=20)

        self.boton_abrir = ctk.CTkButton(
            self.frame_navegacion, 
            text="🌐 Abrir en navegador", 
            command=self.abrir_enlace, 
            width=180
        )
        self.boton_abrir.pack(side="left", padx=15)

        self.boton_siguiente = ctk.CTkButton(
            self.frame_navegacion, 
            text="Siguiente →", 
            command=self.siguiente, 
            width=120
        )
        self.boton_siguiente.pack(side="left", padx=15)

    def actualizar_estado(self, mensaje: str):
        """Actualiza el mensaje de estado"""
        self.etiqueta_estado.configure(text=mensaje)
        self.root.update()

    def buscar_async(self):
        """Inicia búsqueda en hilo separado"""
        threading.Thread(target=self.buscar, daemon=True).start()

    def buscar(self):
        """Busca noticias de manera optimizada"""
        self.barra_progreso.pack(pady=(5, 10))
        self.barra_progreso.start()
        self.boton_buscar.configure(state="disabled")
        
        try:
            noticias_raw = self.scraper.obtener_noticias_paralelo(self.actualizar_estado)
            
            self.noticias = []
            for noticia in noticias_raw:
                self.noticias.append({
                    "titulo": noticia["titulo"],
                    "link": noticia["link"],
                    "contenido_original": noticia["contenido"],
                    "resumen_generado": None,
                    "resumen_en_proceso": False
                })

            self.indice_actual = 0
            cantidad = len(self.noticias)
            
            self.actualizar_estado("Búsqueda completada")
            self.etiqueta_contador.configure(
                text=f"{cantidad} noticia{'s' if cantidad != 1 else ''} encontrada{'s' if cantidad != 1 else ''}"
            )
            
            if self.noticias:
                self.mostrar_actual()
            else:
                self.titulo_label.configure(text="No se encontraron noticias")
                self.caja_texto.delete("1.0", "end")
                self.caja_texto.insert("end", "Intenta buscar nuevamente en unos minutos.")

        except Exception as e:
            self.actualizar_estado(f"Error en búsqueda: {str(e)}")
        finally:
            self.barra_progreso.stop()
            self.barra_progreso.pack_forget()
            self.boton_buscar.configure(state="normal")

    def resumir_todo_async(self):
        """Inicia resumen de todos los artículos"""
        if not self.noticias:
            return
        threading.Thread(target=self.resumir_todo, daemon=True).start()

    def resumir_todo(self):
        """Resume todos los artículos en lote"""
        self.barra_progreso.pack(pady=(5, 10))
        self.barra_progreso.start()
        self.actualizar_estado("Resumiendo todos los artículos...")

        try:
            # Preparar textos para resumen en lote
            textos_para_resumir = []
            indices_sin_resumen = []
            
            for i, noticia in enumerate(self.noticias):
                if noticia["resumen_generado"] is None:
                    contenido_completo = "\n\n".join(noticia["contenido_original"][:5])  # Primeros 5 párrafos
                    textos_para_resumir.append(contenido_completo)
                    indices_sin_resumen.append(i)

            if textos_para_resumir:
                resumenes = self.api.resumir_batch(textos_para_resumir)
                
                # Asignar resúmenes
                for i, resumen in enumerate(resumenes):
                    if i < len(indices_sin_resumen):
                        indice_noticia = indices_sin_resumen[i]
                        self.noticias[indice_noticia]["resumen_generado"] = resumen

            self.actualizar_estado("Resúmenes completados")
            self.mostrar_actual()  # Actualizar vista actual

        except Exception as e:
            self.actualizar_estado(f"Error resumiendo: {str(e)}")
        finally:
            self.barra_progreso.stop()
            self.barra_progreso.pack_forget()

    def mostrar_actual(self):
        """Muestra la noticia actual con animaciones mejoradas"""
        if not self.noticias:
            self.titulo_label.configure(text="Sin resultados")
            self.caja_texto.delete("1.0", "end")
            self.link_label.configure(text="")
            self.etiqueta_posicion.configure(text="0/0")
            return

        noticia = self.noticias[self.indice_actual]
        total = len(self.noticias)
        
        # Actualizar posición
        self.etiqueta_posicion.configure(text=f"{self.indice_actual + 1}/{total}")

        # Mostrar link
        self.link_label.configure(text=noticia['link'])

        # Mostrar título con efecto
        self.stream_texto_label(self.titulo_label, noticia['titulo'], delay_ms=30)

        # Mostrar contenido
        if noticia["resumen_generado"]:
            self.stream_texto_textbox(self.caja_texto, noticia["resumen_generado"], delay_ms=15)
        else:
            # Mostrar contenido original mientras se genera resumen
            contenido_preview = "\n\n".join(noticia["contenido_original"][:3])
            self.caja_texto.delete("1.0", "end")
            self.caja_texto.insert("end", "📖 Contenido original (sin resumir):\n\n" + contenido_preview)
            
            # Generar resumen si no existe
            if not noticia["resumen_en_proceso"]:
                noticia["resumen_en_proceso"] = True
                threading.Thread(
                    target=self.generar_resumen_individual, 
                    args=(self.indice_actual,), 
                    daemon=True
                ).start()

    def generar_resumen_individual(self, indice: int):
        """Genera resumen para un artículo específico"""
        if indice >= len(self.noticias):
            return
            
        noticia = self.noticias[indice]
        contenido_completo = "\n\n".join(noticia["contenido_original"][:5])
        
        resumen = self.api.pedir_resumen(contenido_completo)
        noticia["resumen_generado"] = resumen
        noticia["resumen_en_proceso"] = False
        
        # Actualizar vista si seguimos en el mismo artículo
        if self.indice_actual == indice:
            self.root.after(100, lambda: self.stream_texto_textbox(self.caja_texto, resumen, delay_ms=10))

    def stream_texto_textbox(self, widget, texto, delay_ms=20, pos=0):
        """Efecto de escritura en textbox optimizado"""
        if pos == 0:
            widget.delete("1.0", "end")

        if pos < len(texto):
            # Insertar caracteres en chunks para mejor rendimiento
            chunk_size = 3
            chunk = texto[pos:pos + chunk_size]
            widget.insert("end", chunk)
            widget.see("end")
            self.root.after(delay_ms, lambda: self.stream_texto_textbox(widget, texto, delay_ms, pos + chunk_size))

    def stream_texto_label(self, widget, texto, delay_ms=30, pos=0):
        """Efecto de escritura en label optimizado"""
        if pos < len(texto):
            widget.configure(text=texto[:pos + 1])
            self.root.after(delay_ms, lambda: self.stream_texto_label(widget, texto, delay_ms, pos + 1))

    def siguiente(self):
        """Navega a la siguiente noticia"""
        if self.indice_actual < len(self.noticias) - 1:
            self.indice_actual += 1
            self.mostrar_actual()

    def anterior(self):
        """Navega a la noticia anterior"""
        if self.indice_actual > 0:
            self.indice_actual -= 1
            self.mostrar_actual()

    def abrir_enlace(self):
        """Abre el enlace en el navegador"""
        if self.noticias and self.indice_actual < len(self.noticias):
            webbrowser.open(self.noticias[self.indice_actual]['link'])


if __name__ == "__main__":
    root = ctk.CTk()
    app = App(root)
    root.mainloop()