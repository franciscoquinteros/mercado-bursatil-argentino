"""
Integración de yfinance con el Modelo de Contexto del Protocolo (MCP)
para el Mercado Bursátil Argentino
"""

import yfinance as yf
import pandas as pd
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union, Any
from datetime import datetime, timedelta
import json
import logging
from enum import Enum

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MCP-Argentina-YFinance")

# Definición de enumeraciones (mantenemos las del MCP original)
class TipoActivo(str, Enum):
    ACCION = "ACCION"
    CEDEAR = "CEDEAR"
    BONO = "BONO"
    ETF = "ETF"
    OPCION = "OPCION"
    FUTURO = "FUTURO"

class PanelMercado(str, Enum):
    LIDER = "LIDER"
    GENERAL = "GENERAL"
    PYMES = "PYMES"
    BONOS = "BONOS"
    LETRAS = "LETRAS"

class Mercado(str, Enum):
    BYMA = "BYMA"
    MAE = "MAE"
    MAV = "MAV"
    ROFEX = "ROFEX"
    NYSE = "NYSE"
    NASDAQ = "NASDAQ"
    
class Moneda(str, Enum):
    ARS = "ARS"
    USD = "USD"
    USD_LINKED = "USD-LINKED"
    EUR = "EUR"

class Intervalo(str, Enum):
    MINUTO_1 = "1m"
    MINUTO_2 = "2m"
    MINUTO_5 = "5m"
    MINUTO_15 = "15m"
    MINUTO_30 = "30m"
    MINUTO_60 = "60m"
    MINUTO_90 = "90m"
    HORA_1 = "1h"
    DIA_1 = "1d"
    DIA_5 = "5d"
    SEMANA_1 = "1wk"
    MES_1 = "1mo"
    MES_3 = "3mo"

class EstadoRespuesta(str, Enum):
    OK = "OK"
    ERROR = "ERROR"

class CodigoError(str, Enum):
    DATA_001 = "DATA_001"  # Símbolo no encontrado
    DATA_002 = "DATA_002"  # Datos no disponibles para el rango solicitado
    DATA_003 = "DATA_003"  # Error en la obtención de datos
    PARAM_001 = "PARAM_001"  # Parámetros incorrectos

# Mapeo de símbolos argentinos a símbolos de Yahoo Finance
# Los activos argentinos en Yahoo Finance suelen tener sufijos como .BA para Buenos Aires
SIMBOLOS_MAPPING = {
    # Acciones líderes
    "GGAL": "GGAL.BA",
    "PAMP": "PAMP.BA",
    "YPF": "YPFD.BA",  # Cambiado de YPF.BA a YPFD.BA que es el correcto
    "YPFD": "YPFD.BA",
    "TXAR": "TXAR.BA",
    "BYMA": "BYMA.BA",
    "BBAR": "BBAR.BA",
    "CEPU": "CEPU.BA",
    "TRAN": "TRAN.BA",
    "TGNO4": "TGNO4.BA",
    "TGSU2": "TGSU2.BA",
    "LOMA": "LOMA.BA",
    "BMA": "BMA.BA",
    "SUPV": "SUPV.BA",
    "CRES": "CRES.BA",
    "ALUA": "ALUA.BA",
    "COME": "COME.BA",
    "MIRG": "MIRG.BA",
    "HARG": "HARG.BA",
    "VALO": "VALO.BA",
    
    # ADRs (cotizados en USD)
    "GGAL.ADR": "GGAL",
    "YPF.ADR": "YPF",  # YPF que cotiza en NYSE
    "BMA.ADR": "BMA",
    "SUPV.ADR": "SUPV",
    "LOMA.ADR": "LOMA",
    "BBAR.ADR": "BBAR",
    "PAM.ADR": "PAM",  # Pampa Energía ADR
    "TEO.ADR": "TEO",  # Telecom Argentina ADR
    "TGS.ADR": "TGS",  # Transportadora Gas del Sur ADR
    
    # ETFs relacionados con Argentina
    "ARGT": "ARGT",    # Global X MSCI Argentina ETF
    
    # Índices
    "MERVAL": "^MERV", # Índice Merval
}

# Clase adaptadora para convertir datos de yfinance al formato MCP
@dataclass
class ActivoFinanciero:
    simbolo: str
    tipo: TipoActivo
    denominacion: str
    panel: PanelMercado = PanelMercado.LIDER
    mercado: Mercado = Mercado.BYMA
    moneda: Moneda = Moneda.ARS
    codigo_isin: Optional[str] = None
    codigo_cfi: Optional[str] = None
    simbolo_yahoo: Optional[str] = None
    
    def to_dict(self):
        return {
            "simbolo": self.simbolo,
            "tipo": self.tipo.value,
            "denominacion": self.denominacion,
            "panel": self.panel.value,
            "mercado": self.mercado.value,
            "moneda": self.moneda.value,
            "codigoISIN": self.codigo_isin,
            "codigoCFI": self.codigo_cfi,
            "simboloYahoo": self.simbolo_yahoo
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            simbolo=data["simbolo"],
            tipo=TipoActivo(data["tipo"]),
            denominacion=data["denominacion"],
            panel=PanelMercado(data["panel"]) if "panel" in data else PanelMercado.LIDER,
            mercado=Mercado(data["mercado"]) if "mercado" in data else Mercado.BYMA,
            moneda=Moneda(data["moneda"]) if "moneda" in data else Moneda.ARS,
            codigo_isin=data.get("codigoISIN"),
            codigo_cfi=data.get("codigoCFI"),
            simbolo_yahoo=data.get("simboloYahoo")
        )

@dataclass
class Cotizacion:
    simbolo: str
    timestamp: datetime
    apertura: float
    maximo: float
    minimo: float
    cierre: float
    volumen_nominal: float
    volumen_monto: float = 0.0
    cantidad_operaciones: int = 0
    ajustado: bool = True
    
    def to_dict(self):
        return {
            "simbolo": self.simbolo,
            "timestamp": self.timestamp.isoformat(),
            "apertura": self.apertura,
            "maximo": self.maximo,
            "minimo": self.minimo,
            "cierre": self.cierre,
            "volumenNominal": self.volumen_nominal,
            "volumenMonto": self.volumen_monto,
            "cantidadOperaciones": self.cantidad_operaciones,
            "ajustado": self.ajustado
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            simbolo=data["simbolo"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            apertura=data["apertura"],
            maximo=data["maximo"],
            minimo=data["minimo"],
            cierre=data["cierre"],
            volumen_nominal=data["volumenNominal"],
            volumen_monto=data.get("volumenMonto", 0.0),
            cantidad_operaciones=data.get("cantidadOperaciones", 0),
            ajustado=data.get("ajustado", True)
        )

# Clases para solicitudes
@dataclass
class SolicitudHistorico:
    simbolo: str
    desde: Optional[datetime] = None
    hasta: Optional[datetime] = None
    intervalo: Intervalo = Intervalo.DIA_1
    ajustado: bool = True
    
    def to_dict(self):
        return {
            "simbolo": self.simbolo,
            "desde": self.desde.isoformat() if self.desde else None,
            "hasta": self.hasta.isoformat() if self.hasta else None,
            "intervalo": self.intervalo.value,
            "ajustado": self.ajustado
        }

@dataclass
class MetadataHistorico:
    simbolo: str
    desde: datetime
    hasta: datetime
    intervalo: str
    registros: int
    ajustado: bool
    
    def to_dict(self):
        return {
            "simbolo": self.simbolo,
            "desde": self.desde.isoformat(),
            "hasta": self.hasta.isoformat(),
            "intervalo": self.intervalo,
            "registros": self.registros,
            "ajustado": self.ajustado
        }

@dataclass
class RespuestaHistorico:
    estado: EstadoRespuesta
    datos: List[Cotizacion] = field(default_factory=list)
    metadata: Optional[MetadataHistorico] = None
    mensaje: Optional[str] = None
    codigo_error: Optional[CodigoError] = None
    
    def to_dict(self):
        result = {
            "estado": self.estado.value
        }
        
        if self.estado == EstadoRespuesta.OK:
            result["datos"] = [cotizacion.to_dict() for cotizacion in self.datos]
            result["metadata"] = self.metadata.to_dict() if self.metadata else None
        else:
            result["mensaje"] = self.mensaje
            result["codigo"] = self.codigo_error.value if self.codigo_error else None
            
        return result

# Cliente de YFinance para el MCP
class ClienteYFinanceMCP:
    def __init__(self):
        self.simbolos_mapping = SIMBOLOS_MAPPING
        self._activos_cache = {}  # Caché para información de activos
    
    def _get_yahoo_symbol(self, simbolo: str) -> str:
        """Obtiene el símbolo correspondiente de Yahoo Finance"""
        if simbolo in self.simbolos_mapping:
            return self.simbolos_mapping[simbolo]
        # Si el símbolo no está en el mapeo, intentamos agregando .BA
        if not simbolo.endswith('.BA') and not simbolo.endswith('.ADR'):
            posible_simbolo = f"{simbolo}.BA"
            logger.info(f"Símbolo no encontrado en mapeo, intentando con {posible_simbolo}")
            return posible_simbolo
        return simbolo
    
    def _convert_yf_history_to_cotizaciones(self, df: pd.DataFrame, simbolo: str) -> List[Cotizacion]:
        """Convierte un DataFrame de historial de yfinance a una lista de Cotizacion"""
        cotizaciones = []
        
        # Verificar si el DataFrame está vacío
        if df.empty:
            return cotizaciones
        
        for index, row in df.iterrows():
            # Verificar si tenemos todos los datos necesarios
            if pd.isna(row['Open']) or pd.isna(row['High']) or pd.isna(row['Low']) or pd.isna(row['Close']):
                continue
                
            cotizacion = Cotizacion(
                simbolo=simbolo,
                timestamp=index.to_pydatetime(),
                apertura=float(row['Open']),
                maximo=float(row['High']),
                minimo=float(row['Low']),
                cierre=float(row['Close']),
                volumen_nominal=float(row['Volume']) if 'Volume' in row and not pd.isna(row['Volume']) else 0.0,
                ajustado=True
            )
            cotizaciones.append(cotizacion)
        
        return cotizaciones
    
    def obtener_historico(self, solicitud: SolicitudHistorico) -> RespuestaHistorico:
        """Obtiene datos históricos de cotizaciones usando yfinance"""
        try:
            # Obtener símbolo de Yahoo Finance
            simbolo_yahoo = self._get_yahoo_symbol(solicitud.simbolo)
            
            # Preparar fechas
            desde = solicitud.desde if solicitud.desde else datetime.now() - timedelta(days=365)
            hasta = solicitud.hasta if solicitud.hasta else datetime.now()
            
            # Obtener intervalo de yfinance
            intervalo = solicitud.intervalo.value
            
            logger.info(f"Obteniendo datos para {simbolo_yahoo} desde {desde} hasta {hasta} con intervalo {intervalo}")
            
            # Obtener datos de yfinance con manejo de errores más robusto
            try:
                ticker = yf.Ticker(simbolo_yahoo)
                df = ticker.history(
                    start=desde.strftime('%Y-%m-%d'),
                    end=hasta.strftime('%Y-%m-%d'),
                    interval=intervalo,
                    auto_adjust=solicitud.ajustado
                )
            except Exception as ticker_error:
                logger.error(f"Error específico de yfinance: {ticker_error}")
                return RespuestaHistorico(
                    estado=EstadoRespuesta.ERROR,
                    mensaje=f"Error al obtener datos de Yahoo Finance para el símbolo {simbolo_yahoo}: {str(ticker_error)}",
                    codigo_error=CodigoError.DATA_003
                )
            
            # Si no hay datos, devolver error
            if df.empty:
                logger.warning(f"DataFrame vacío para {simbolo_yahoo}")
                return RespuestaHistorico(
                    estado=EstadoRespuesta.ERROR,
                    mensaje=f"No se encontraron datos para el símbolo {solicitud.simbolo} ({simbolo_yahoo}) en el período solicitado",
                    codigo_error=CodigoError.DATA_002
                )
            
            # Convertir a formato MCP
            cotizaciones = self._convert_yf_history_to_cotizaciones(df, solicitud.simbolo)
            
            if not cotizaciones:
                logger.warning(f"No se pudieron convertir los datos para {simbolo_yahoo}")
                return RespuestaHistorico(
                    estado=EstadoRespuesta.ERROR,
                    mensaje=f"Los datos obtenidos para {solicitud.simbolo} ({simbolo_yahoo}) no pudieron ser procesados",
                    codigo_error=CodigoError.DATA_003
                )
            
            # Crear metadata
            metadata = MetadataHistorico(
                simbolo=solicitud.simbolo,
                desde=cotizaciones[0].timestamp,
                hasta=cotizaciones[-1].timestamp,
                intervalo=intervalo,
                registros=len(cotizaciones),
                ajustado=solicitud.ajustado
            )
            
            return RespuestaHistorico(
                estado=EstadoRespuesta.OK,
                datos=cotizaciones,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error al obtener datos históricos: {e}")
            return RespuestaHistorico(
                estado=EstadoRespuesta.ERROR,
                mensaje=f"Error en la obtención de datos: {str(e)}",
                codigo_error=CodigoError.DATA_003
            )
    
    def obtener_activo(self, simbolo: str) -> Optional[ActivoFinanciero]:
        """Obtiene información de un activo financiero usando yfinance"""
        try:
            # Verificar caché
            if simbolo in self._activos_cache:
                return self._activos_cache[simbolo]
            
            # Obtener símbolo de Yahoo Finance
            simbolo_yahoo = self._get_yahoo_symbol(simbolo)
            
            # Obtener datos de yfinance con manejo de errores
            try:
                ticker = yf.Ticker(simbolo_yahoo)
                
                # Verificar si hay información disponible
                try:
                    info = ticker.info
                    if not info or len(info) == 0:
                        logger.warning(f"No hay información disponible para {simbolo_yahoo}")
                        # Fallback: obtener el último precio para verificar existencia
                        df = ticker.history(period="1d")
                        if df.empty:
                            logger.error(f"No se pudo confirmar la existencia de {simbolo_yahoo}")
                            return None
                        
                        # Si llegamos aquí, el ticker existe pero no hay info detallada
                        info = {"shortName": simbolo_yahoo}
                except Exception as info_error:
                    logger.warning(f"Error al obtener info del ticker {simbolo_yahoo}: {info_error}")
                    # Intentamos obtener al menos el historial para confirmar que existe
                    df = ticker.history(period="1d")
                    if df.empty:
                        raise Exception(f"No se encontró el símbolo {simbolo_yahoo}")
                    
                    # Si llegamos aquí, el ticker existe pero no hay info detallada
                    info = {"shortName": simbolo_yahoo}
                    
            except Exception as ticker_error:
                logger.error(f"Error al obtener el ticker {simbolo_yahoo}: {ticker_error}")
                return None
            
            # Determinar tipo de activo
            tipo = TipoActivo.ACCION
            if simbolo_yahoo == "^MERV":
                tipo = TipoActivo.BONO
            elif simbolo_yahoo == "ARGT":
                tipo = TipoActivo.ETF
            elif simbolo.endswith('.ADR'):
                tipo = TipoActivo.CEDEAR
            
            # Determinar mercado
            mercado = Mercado.BYMA
            if simbolo_yahoo.endswith('.BA'):
                mercado = Mercado.BYMA
            elif not '.' in simbolo_yahoo or simbolo_yahoo.startswith('^'):
                mercado = Mercado.NYSE
            
            # Determinar moneda
            moneda = Moneda.ARS
            if mercado != Mercado.BYMA:
                moneda = Moneda.USD
            
            # Obtener denominación con manejo de errores
            denominacion = simbolo
            if info:
                if 'longName' in info and info['longName']:
                    denominacion = info['longName']
                elif 'shortName' in info and info['shortName']:
                    denominacion = info['shortName']
            
            # Crear activo
            activo = ActivoFinanciero(
                simbolo=simbolo,
                tipo=tipo,
                denominacion=denominacion,
                panel=PanelMercado.LIDER,
                mercado=mercado,
                moneda=moneda,
                simbolo_yahoo=simbolo_yahoo
            )
            
            # Guardar en caché
            self._activos_cache[simbolo] = activo
            
            return activo
            
        except Exception as e:
            logger.error(f"Error general al obtener información del activo {simbolo}: {e}")
            return None
    
    def obtener_ultima_cotizacion(self, simbolo: str) -> Optional[Cotizacion]:
        """Obtiene la última cotización disponible para un símbolo"""
        try:
            # Obtener símbolo de Yahoo Finance
            simbolo_yahoo = self._get_yahoo_symbol(simbolo)
            
            # Algunos símbolos pueden necesitar ajuste
            if simbolo == "YPF" and simbolo_yahoo == "YPF.BA":
                logger.info(f"Ajustando símbolo YPF a YPFD.BA")
                simbolo_yahoo = "YPFD.BA"
            
            # Intentar obtener datos con manejo de errores
            try:
                logger.info(f"Obteniendo última cotización para {simbolo_yahoo}")
                ticker = yf.Ticker(simbolo_yahoo)
                df = ticker.history(period="1d")
                
                if df.empty:
                    # Si el DataFrame está vacío, intentamos con 5 días
                    logger.warning(f"DataFrame para 1d vacío, intentando con period='5d' para {simbolo_yahoo}")
                    df = ticker.history(period="5d")
                    
                    if df.empty:
                        # Si aún está vacío, intentamos con 1 mes
                        logger.warning(f"DataFrame para 5d vacío, intentando con period='1mo' para {simbolo_yahoo}")
                        df = ticker.history(period="1mo")
                
                if df.empty:
                    logger.error(f"No se encontraron datos para {simbolo_yahoo} en ningún período")
                    return None
                
            except Exception as ticker_error:
                logger.error(f"Error específico de yfinance para {simbolo_yahoo}: {ticker_error}")
                return None
            
            # Convertir a formato MCP
            cotizaciones = self._convert_yf_history_to_cotizaciones(df, simbolo)
            
            if not cotizaciones:
                logger.warning(f"No se pudieron convertir los datos para {simbolo_yahoo}")
                return None
                
            # Devolver la cotización más reciente
            return cotizaciones[0]
            
        except Exception as e:
            logger.error(f"Error general al obtener última cotización para {simbolo}: {e}")
            return None
    
    def obtener_cotizaciones_multiples(self, simbolos: List[str]) -> Dict[str, Optional[Cotizacion]]:
        """Obtiene las últimas cotizaciones para múltiples símbolos"""
        resultado = {}
        
        # Procesamos cada símbolo individualmente para mayor robustez
        for simbolo in simbolos:
            try:
                # Intentamos obtener la última cotización para este símbolo específico
                ultima_cotizacion = self.obtener_ultima_cotizacion(simbolo)
                resultado[simbolo] = ultima_cotizacion
            except Exception as e:
                logger.error(f"Error procesando {simbolo} individualmente: {e}")
                resultado[simbolo] = None
        
        return resultado
    
    def buscar_activos(self, query: str) -> List[ActivoFinanciero]:
        """Busca activos que coincidan con un query"""
        resultados = []
        
        try:
            # Buscar en Yahoo Finance
            tickers = yf.Tickers.search(query)
            
            for ticker_info in tickers[:10]:  # Limitamos a 10 resultados
                ticker_symbol = ticker_info.get('symbol', '')
                
                # Filtrar para activos argentinos
                if '.BA' in ticker_symbol or ticker_symbol in self.simbolos_mapping.values():
                    # Encontrar símbolo original si es posible
                    simbolo_original = next(
                        (k for k, v in self.simbolos_mapping.items() if v == ticker_symbol), 
                        ticker_symbol
                    )
                    
                    activo = ActivoFinanciero(
                        simbolo=simbolo_original,
                        tipo=TipoActivo.ACCION,
                        denominacion=ticker_info.get('shortName', ticker_symbol),
                        simbolo_yahoo=ticker_symbol,
                        mercado=Mercado.BYMA if '.BA' in ticker_symbol else Mercado.NYSE,
                        moneda=Moneda.ARS if '.BA' in ticker_symbol else Moneda.USD
                    )
                    resultados.append(activo)
            
            return resultados
            
        except Exception as e:
            logger.error(f"Error en búsqueda de activos: {e}")
            return []

# Ejemplos de uso
def ejemplo_uso():
    # Inicializar cliente
    cliente = ClienteYFinanceMCP()
    
    # Ejemplo 1: Obtener datos históricos de YPF
    print("\n--- Ejemplo 1: Datos históricos de YPF ---")
    solicitud = SolicitudHistorico(
        simbolo="YPF",
        desde=datetime(2023, 1, 1),
        hasta=datetime(2023, 1, 31),
        intervalo=Intervalo.DIA_1
    )
    
    respuesta = cliente.obtener_historico(solicitud)
    
    if respuesta.estado == EstadoRespuesta.OK:
        print(f"Se obtuvieron {len(respuesta.datos)} registros históricos")
        for cotizacion in respuesta.datos[:3]:  # Mostrar solo los primeros 3
            print(f"{cotizacion.timestamp.date()} - Apertura: {cotizacion.apertura:.2f}, Cierre: {cotizacion.cierre:.2f}")
    else:
        print(f"Error: {respuesta.mensaje}")
    
    # Ejemplo 2: Obtener información de un activo
    print("\n--- Ejemplo 2: Información del activo GGAL ---")
    activo = cliente.obtener_activo("GGAL")
    if activo:
        print(f"Activo: {activo.denominacion} ({activo.simbolo})")
        print(f"Tipo: {activo.tipo.value}, Mercado: {activo.mercado.value}, Moneda: {activo.moneda.value}")
        print(f"Símbolo en Yahoo Finance: {activo.simbolo_yahoo}")
    else:
        print("No se pudo obtener información del activo")
    
    # Ejemplo 3: Obtener última cotización
    print("\n--- Ejemplo 3: Última cotización del Merval ---")
    ultima = cliente.obtener_ultima_cotizacion("MERVAL")
    if ultima:
        print(f"Fecha: {ultima.timestamp}")
        print(f"Apertura: {ultima.apertura:.2f}, Máximo: {ultima.maximo:.2f}")
        print(f"Mínimo: {ultima.minimo:.2f}, Cierre: {ultima.cierre:.2f}")
        print(f"Volumen: {ultima.volumen_nominal}")
    else:
        print("No se pudo obtener la última cotización")
    
    # Ejemplo 4: Obtener cotizaciones múltiples
    print("\n--- Ejemplo 4: Cotizaciones múltiples ---")
    simbolos = ["YPF", "GGAL", "PAMP"]
    cotizaciones = cliente.obtener_cotizaciones_multiples(simbolos)
    
    for simbolo, cotizacion in cotizaciones.items():
        if cotizacion:
            print(f"{simbolo}: Cierre {cotizacion.cierre:.2f} ({cotizacion.timestamp.date()})")
        else:
            print(f"{simbolo}: No disponible")

if __name__ == "__main__":
    ejemplo_uso()

# Función para crear un conjunto de datos de ejemplo más amplio
def generar_datos_ejemplo():
    """Genera un conjunto de datos de ejemplo para análisis"""
    cliente = ClienteYFinanceMCP()
    
    # Lista de símbolos importantes en el mercado argentino
    simbolos = [
        "GGAL", "YPF", "PAMP", "TXAR", "BYMA", "BBAR", 
        "MERVAL", "ALUA", "CEPU", "COME", "CRES"
    ]
    
    # Obtener datos históricos de último año para cada símbolo
    resultados = {}
    desde = datetime.now() - timedelta(days=365)
    hasta = datetime.now()
    
    for simbolo in simbolos:
        print(f"Obteniendo datos para {simbolo}...")
        solicitud = SolicitudHistorico(
            simbolo=simbolo,
            desde=desde,
            hasta=hasta,
            intervalo=Intervalo.DIA_1
        )
        
        respuesta = cliente.obtener_historico(solicitud)
        if respuesta.estado == EstadoRespuesta.OK:
            resultados[simbolo] = respuesta.datos
            print(f"  ✓ Obtenidos {len(respuesta.datos)} registros")
        else:
            print(f"  ✗ Error: {respuesta.mensaje}")
    
    # Calcular algunas estadísticas
    print("\nEstadísticas:")
    for simbolo, cotizaciones in resultados.items():
        if not cotizaciones:
            continue
            
        precios_cierre = [c.cierre for c in cotizaciones]
        promedio = sum(precios_cierre) / len(precios_cierre)
        minimo = min(precios_cierre)
        maximo = max(precios_cierre)
        
        # Calcular variación porcentual
        primer_precio = cotizaciones[0].cierre
        ultimo_precio = cotizaciones[-1].cierre
        variacion = (ultimo_precio - primer_precio) / primer_precio * 100
        
        print(f"{simbolo}:")
        print(f"  Precio promedio: {promedio:.2f}")
        print(f"  Mínimo: {minimo:.2f}, Máximo: {maximo:.2f}")
        print(f"  Variación anual: {variacion:.2f}%")
    
    return resultados

# Descomentar para ejecutar el análisis más amplio
# datos_ejemplo = generar_datos_ejemplo()