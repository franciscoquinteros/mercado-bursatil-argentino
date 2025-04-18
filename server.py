# server.py

import os
from fastapi import FastAPI, Query
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from main import ClienteYFinanceMCP, SolicitudHistorico, Intervalo

app = FastAPI(title="MCP - Mercado Argentino API")
cliente = ClienteYFinanceMCP()

class HistoricoRequest(BaseModel):
    simbolo: str
    desde: Optional[datetime] = None
    hasta: Optional[datetime] = None
    intervalo: Intervalo = Intervalo.DIA_1

@app.get("/")
def root():
    return {"mensaje": "Bienvenido a la API de Mercado Argentino con yFinance MCP"}

@app.post("/historico")
def obtener_historico(req: HistoricoRequest):
    respuesta = cliente.obtener_historico(req)
    return respuesta.to_dict()

@app.get("/activo")
def obtener_activo(simbolo: str = Query(..., description="Símbolo del activo")):
    activo = cliente.obtener_activo(simbolo)
    return activo.to_dict() if activo else {"error": "Activo no encontrado"}

@app.get("/ultima")
def obtener_ultima(simbolo: str = Query(..., description="Símbolo del activo")):
    cotizacion = cliente.obtener_ultima_cotizacion(simbolo)
    return cotizacion.to_dict() if cotizacion else {"error": "Cotización no disponible"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))