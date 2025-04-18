"""
Utilidades adicionales para el MCP con yfinance
Incluye análisis y visualización de datos para el mercado argentino
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging

# Importamos las clases del MCP principal
from main import (
    ClienteYFinanceMCP, SolicitudHistorico, Intervalo, Cotizacion, 
    EstadoRespuesta, TipoActivo, Mercado, Moneda, PanelMercado
)

class AnalizadorMercadoArgentino:
    """Clase para realizar análisis del mercado argentino"""
    
    def __init__(self):
        self.cliente = ClienteYFinanceMCP()
        self.logger = logging.getLogger("AnalizadorMercadoArgentino")
    
    def obtener_dataframe_historico(self, simbolo: str, desde: datetime, hasta: datetime = None,
                                  intervalo: Intervalo = Intervalo.DIA_1) -> Optional[pd.DataFrame]:
        """Obtiene un DataFrame con datos históricos para un símbolo"""
        if hasta is None:
            hasta = datetime.now()
            
        solicitud = SolicitudHistorico(
            simbolo=simbolo,
            desde=desde,
            hasta=hasta,
            intervalo=intervalo
        )
        
        respuesta = self.cliente.obtener_historico(solicitud)
        
        if respuesta.estado != EstadoRespuesta.OK or not respuesta.datos:
            self.logger.warning(f"No se pudieron obtener datos para {simbolo}: {respuesta.mensaje}")
            return None
            
        # Convertir los datos a DataFrame
        datos = []
        for cotizacion in respuesta.datos:
            datos.append({
                'fecha': cotizacion.timestamp,
                'simbolo': cotizacion.simbolo,
                'apertura': cotizacion.apertura,
                'maximo': cotizacion.maximo,
                'minimo': cotizacion.minimo,
                'cierre': cotizacion.cierre,
                'volumen': cotizacion.volumen_nominal
            })
            
        df = pd.DataFrame(datos)
        df.set_index('fecha', inplace=True)
        return df
    
    def calcular_rendimiento(self, df: pd.DataFrame) -> Tuple[float, float, float]:
        """Calcula el rendimiento para un DataFrame de cotizaciones"""
        if df is None or df.empty:
            return 0.0, 0.0, 0.0
            
        primer_precio = df['cierre'].iloc[0]
        ultimo_precio = df['cierre'].iloc[-1]
        
        # Rendimiento total
        rendimiento_total = (ultimo_precio - primer_precio) / primer_precio * 100
        
        # Rendimiento anualizado
        dias = (df.index[-1] - df.index[0]).days
        if dias > 0:
            rendimiento_anualizado = ((1 + rendimiento_total/100) ** (365/dias) - 1) * 100
        else:
            rendimiento_anualizado = 0.0
            
        # Volatilidad (desviación estándar de rendimientos diarios)
        rendimientos_diarios = df['cierre'].pct_change() * 100
        volatilidad = rendimientos_diarios.std()
        
        return rendimiento_total, rendimiento_anualizado, volatilidad
    
    def comparar_activos(self, simbolos: List[str], desde: datetime, 
                         hasta: datetime = None) -> Dict[str, Dict]:
        """Compara el rendimiento de varios activos"""
        if hasta is None:
            hasta = datetime.now()
            
        resultados = {}
        
        for simbolo in simbolos:
            df = self.obtener_dataframe_historico(simbolo, desde, hasta)
            if df is not None:
                rendimiento_total, rendimiento_anualizado, volatilidad = self.calcular_rendimiento(df)
                
                # Calcular otros indicadores
                maximo = df['cierre'].max()
                minimo = df['cierre'].min()
                ultima = df['cierre'].iloc[-1]
                volumen_promedio = df['volumen'].mean()
                
                resultados[simbolo] = {
                    'rendimiento_total': rendimiento_total,
                    'rendimiento_anualizado': rendimiento_anualizado,
                    'volatilidad': volatilidad,
                    'precio_maximo': maximo,
                    'precio_minimo': minimo,
                    'precio_actual': ultima,
                    'volumen_promedio': volumen_promedio,
                    'cantidad_datos': len(df)
                }
                
                # Obtener información del activo
                activo = self.cliente.obtener_activo(simbolo)
                if activo:
                    resultados[simbolo]['denominacion'] = activo.denominacion
                    resultados[simbolo]['tipo'] = activo.tipo.value
                    resultados[simbolo]['mercado'] = activo.mercado.value
                    resultados[simbolo]['moneda'] = activo.moneda.value
            else:
                self.logger.warning(f"No se pudieron obtener datos para {simbolo}")
                
        return resultados
    
    def graficar_comparacion(self, simbolos: List[str], desde: datetime, 
                            hasta: datetime = None, normalizado: bool = True) -> None:
        """Genera un gráfico comparativo entre varios activos"""
        if hasta is None:
            hasta = datetime.now()
            
        plt.figure(figsize=(12, 6))
        
        # Obtener datos para cada símbolo
        for simbolo in simbolos:
            df = self.obtener_dataframe_historico(simbolo, desde, hasta)
            
            if df is not None:
                # Si normalizado, convertir a base 100
                if normalizado:
                    precios = df['cierre'] / df['cierre'].iloc[0] * 100
                    label = f"{simbolo} (var: {precios.iloc[-1] - 100:.2f}%)"
                else:
                    precios = df['cierre']
                    label = simbolo
                    
                plt.plot(df.index, precios, label=label)
            
        # Configuración del gráfico
        titulo = "Comparación de activos - "
        titulo += "Normalizado (Base 100)" if normalizado else "Precios absolutos"
        plt.title(titulo)
        plt.xlabel("Fecha")
        plt.ylabel("Valor" if normalizado else "Precio")
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()
        
        # Mostrar gráfico
        plt.tight_layout()
        plt.show()
    
    def calcular_matriz_correlacion(self, simbolos: List[str], desde: datetime, 
                                   hasta: datetime = None) -> Optional[pd.DataFrame]:
        """Calcula la matriz de correlación entre varios activos"""
        if hasta is None:
            hasta = datetime.now()
            
        # Obtener datos para cada símbolo y almacenarlos en un DataFrame consolidado
        datos_combinados = pd.DataFrame()
        
        for simbolo in simbolos:
            df = self.obtener_dataframe_historico(simbolo, desde, hasta)
            
            if df is not None:
                # Añadir la columna de cierre al DataFrame combinado
                datos_combinados[simbolo] = df['cierre']
        
        if datos_combinados.empty:
            self.logger.warning("No se pudieron obtener datos para ninguno de los símbolos")
            return None
        
        # Calcular rendimientos diarios
        rendimientos = datos_combinados.pct_change().dropna()
        
        # Calcular matriz de correlación
        matriz_correlacion = rendimientos.corr()
        
        return matriz_correlacion
    
    def calcular_beta(self, simbolo: str, indice: str = "MERVAL", 
                     desde: datetime = None, hasta: datetime = None) -> Optional[float]:
        """Calcula el beta de un activo respecto a un índice (por defecto Merval)"""
        if desde is None:
            desde = datetime.now() - timedelta(days=365)
        if hasta is None:
            hasta = datetime.now()
            
        # Obtener datos del activo y del índice
        df_activo = self.obtener_dataframe_historico(simbolo, desde, hasta)
        df_indice = self.obtener_dataframe_historico(indice, desde, hasta)
        
        if df_activo is None or df_indice is None:
            return None
            
        # Asegurarse de que ambos DataFrames tengan las mismas fechas
        fechas_comunes = df_activo.index.intersection(df_indice.index)
        
        if len(fechas_comunes) < 30:  # Requerir al menos 30 datos
            self.logger.warning(f"Datos insuficientes para calcular beta de {simbolo}")
            return None
            
        # Filtrar ambos DataFrames para tener las mismas fechas
        df_activo = df_activo.loc[fechas_comunes]
        df_indice = df_indice.loc[fechas_comunes]
        
        # Calcular rendimientos
        rendimientos_activo = df_activo['cierre'].pct_change().dropna()
        rendimientos_indice = df_indice['cierre'].pct_change().dropna()
        
        # Calcular beta: Cov(r_a, r_m) / Var(r_m)
        covarianza = rendimientos_activo.cov(rendimientos_indice)
        varianza = rendimientos_indice.var()
        
        if varianza == 0:
            return None
            
        beta = covarianza / varianza
        
        return beta
    
    def calcular_ratios(self, simbolo: str, tasa_libre_riesgo: float = 0.01,
                       desde: datetime = None, hasta: datetime = None) -> Dict[str, float]:
        """Calcula ratios financieros para un activo"""
        if desde is None:
            desde = datetime.now() - timedelta(days=365)
        if hasta is None:
            hasta = datetime.now()
            
        df = self.obtener_dataframe_historico(simbolo, desde, hasta)
        
        if df is None:
            return {}
            
        # Calcular rendimientos diarios
        rendimientos_diarios = df['cierre'].pct_change().dropna()
        
        # Rendimiento anualizado
        rendimiento_anualizado = (1 + rendimientos_diarios.mean()) ** 252 - 1
        
        # Volatilidad anualizada
        volatilidad_anualizada = rendimientos_diarios.std() * np.sqrt(252)
        
        # Ratio de Sharpe
        sharpe = (rendimiento_anualizado - tasa_libre_riesgo) / volatilidad_anualizada if volatilidad_anualizada != 0 else 0
        
        # Sortino (usando solo los rendimientos negativos)
        rendimientos_negativos = rendimientos_diarios[rendimientos_diarios < 0]
        volatilidad_downside = rendimientos_negativos.std() * np.sqrt(252) if not rendimientos_negativos.empty else volatilidad_anualizada
        sortino = (rendimiento_anualizado - tasa_libre_riesgo) / volatilidad_downside if volatilidad_downside != 0 else 0
        
        # Drawdown máximo
        acumulado = (1 + rendimientos_diarios).cumprod()
        maximo_valor = acumulado.cummax()
        drawdown = (acumulado - maximo_valor) / maximo_valor
        max_drawdown = drawdown.min() * 100
        
        return {
            'rendimiento_anualizado': rendimiento_anualizado * 100,
            'volatilidad_anualizada': volatilidad_anualizada * 100,
            'ratio_sharpe': sharpe,
            'ratio_sortino': sortino,
            'maximo_drawdown': max_drawdown
        }
    
    def generar_reporte_mercado(self, desde: datetime = None) -> Dict:
        """Genera un reporte general del mercado argentino"""
        if desde is None:
            desde = datetime.now() - timedelta(days=90)
            
        # Principales activos para analizar
        lideres = ["GGAL", "YPFD", "PAMP", "TXAR", "BYMA", "BBAR", "ALUA"]
        indices = ["MERVAL"]
        
        # Obtener datos de índices
        datos_indices = {}
        for indice in indices:
            df = self.obtener_dataframe_historico(indice, desde)
            if df is not None:
                rendimiento_total, rendimiento_anualizado, volatilidad = self.calcular_rendimiento(df)
                datos_indices[indice] = {
                    'rendimiento_total': rendimiento_total,
                    'rendimiento_anualizado': rendimiento_anualizado,
                    'volatilidad': volatilidad,
                    'ultimo_valor': df['cierre'].iloc[-1]
                }
        
        # Obtener datos de líderes
        datos_lideres = self.comparar_activos(lideres, desde)
        
        # Calcular matriz de correlación
        todos_simbolos = lideres + indices
        matriz_correlacion = self.calcular_matriz_correlacion(todos_simbolos, desde)
        
        # Calcular betas de los líderes respecto al Merval
        betas = {}
        for simbolo in lideres:
            beta = self.calcular_beta(simbolo, "MERVAL", desde)
            if beta is not None:
                betas[simbolo] = beta
        
        # Preparar reporte
        reporte = {
            'fecha_reporte': datetime.now(),
            'periodo': {
                'desde': desde,
                'hasta': datetime.now()
            },
            'indices': datos_indices,
            'lideres': datos_lideres,
            'betas': betas,
            'matriz_correlacion': matriz_correlacion
        }
        
        return reporte
    
    def imprimir_reporte(self, reporte: Dict) -> None:
        """Imprime un reporte de mercado en formato legible"""
        print("=" * 80)
        print(f"REPORTE DE MERCADO ARGENTINO - {reporte['fecha_reporte'].strftime('%d/%m/%Y %H:%M')}")
        print("=" * 80)
        
        # Información del período
        print(f"\nPeríodo analizado: {reporte['periodo']['desde'].strftime('%d/%m/%Y')} al {reporte['periodo']['hasta'].strftime('%d/%m/%Y')}")
        
        # Datos de índices
        print("\nINDICES DE MERCADO:")
        print("-" * 80)
        print(f"{'Indice':<10} {'Último Valor':<15} {'Rend. Total':<15} {'Rend. Anual':<15} {'Volatilidad':<15}")
        print("-" * 80)
        
        for indice, datos in reporte['indices'].items():
            print(f"{indice:<10} {datos['ultimo_valor']:<15,.2f} {datos['rendimiento_total']:<15,.2f}% {datos['rendimiento_anualizado']:<15,.2f}% {datos['volatilidad']:<15,.2f}%")
        
        # Datos de líderes
        print("\nACCIONES LÍDERES:")
        print("-" * 80)
        print(f"{'Símbolo':<10} {'Denominación':<25} {'Último Precio':<15} {'Rend. Total':<15} {'Beta':<10}")
        print("-" * 80)
        
        for simbolo, datos in reporte['lideres'].items():
            beta = reporte['betas'].get(simbolo, 'N/A')
            beta_str = f"{beta:.2f}" if isinstance(beta, float) else beta
            denominacion = datos.get('denominacion', simbolo)[:25]
            print(f"{simbolo:<10} {denominacion:<25} {datos['precio_actual']:<15,.2f} {datos['rendimiento_total']:<15,.2f}% {beta_str:<10}")
        
        # Top 3 rendimientos
        print("\nTOP 3 RENDIMIENTOS:")
        top_rendimientos = sorted(
            [(s, d['rendimiento_total']) for s, d in reporte['lideres'].items()],
            key=lambda x: x[1], reverse=True
        )[:3]
        
        for i, (simbolo, rendimiento) in enumerate(top_rendimientos, 1):
            print(f"{i}. {simbolo}: {rendimiento:.2f}%")
        
        # Matriz de correlación (simplificada)
        if reporte['matriz_correlacion'] is not None:
            print("\nMATRIZ DE CORRELACIÓN (Extracto):")
            mat_corr = reporte['matriz_correlacion']
            
            # Si hay muchos símbolos, mostrar solo una parte
            if len(mat_corr) > 5:
                simbolos_muestra = mat_corr.index[:5]
                print(mat_corr.loc[simbolos_muestra, simbolos_muestra].round(2))
            else:
                print(mat_corr.round(2))
        
        print("\n" + "=" * 80)

# Ejemplo de uso
def ejemplo_uso_utilidades():
    # Inicializar analizador
    analizador = AnalizadorMercadoArgentino()
    
    print("Generando reporte de mercado argentino...\n")
    desde = datetime.now() - timedelta(days=90)
    reporte = analizador.generar_reporte_mercado(desde)
    analizador.imprimir_reporte(reporte)
    
    # Análisis de correlación entre GGAL y YPFD
    print("\nAnalizando correlación entre GGAL y YPFD:")
    matriz_corr = analizador.calcular_matriz_correlacion(["GGAL", "YPFD"], desde)
    if matriz_corr is not None:
        print(matriz_corr.round(2))
    
    # Análisis de ratios financieros para GGAL
    print("\nRatios financieros para GGAL:")
    ratios = analizador.calcular_ratios("GGAL", desde=desde)
    for nombre, valor in ratios.items():
        print(f"{nombre}: {valor:.2f}")
    
    # Ejemplo de gráfico (comentado porque no se puede mostrar en consola)
    # analizador.graficar_comparacion(["GGAL", "YPFD", "MERVAL"], desde, normalizado=True)

if __name__ == "__main__":
    ejemplo_uso_utilidades()