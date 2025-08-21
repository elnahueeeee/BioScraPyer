from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scraper import ScrapingEngine
from noticias_api import NoticiasAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Permitir que React (localhost:3000) haga requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scraper = ScrapingEngine()
api = NoticiasAPI("https://tu-url-de-colab.ngrok-free.app")  # Tu endpoint de resumen

# Modelo para recibir POST de resumen
class Texto(BaseModel):
    contenido: str

class TextosBatch(BaseModel):
    contenidos: List[str]

# Endpoint para buscar noticias
@app.get("/noticias")
async def obtener_noticias():
    noticias_raw = scraper.obtener_noticias_paralelo()
    # Convertir contenido a lista de strings
    noticias = [
        {
            "titulo": n["titulo"],
            "link": n["link"],
            "contenido": n["contenido"][:10]  # primeros 10 párrafos
        }
        for n in noticias_raw
    ]
    return noticias

# Endpoint para resumir una noticia individual
@app.post("/resumir")
async def resumir(texto: Texto):
    resumen = api.pedir_resumen(texto.contenido)
    return {"resumen": resumen}

# Endpoint para resumir múltiples noticias
@app.post("/resumir_batch")
async def resumir_batch(batch: TextosBatch):
    resumenes = api.resumir_batch(batch.contenidos)
    return resumenes
