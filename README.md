# MCP - Mercado Argentino con yFinance 📈🇦🇷

Este proyecto implementa un **Model Context Protocol (MCP)** que actúa como un asistente especializado en el análisis del mercado bursátil argentino. Utiliza la librería [yfinance](https://pypi.org/project/yfinance/) para obtener datos en tiempo real y realizar cálculos financieros.

## 🧠 ¿Qué hace este MCP?

- Consulta de precios históricos y actuales de acciones argentinas
- Análisis de rendimiento y volatilidad
- Cálculo de ratios financieros como Sharpe, Sortino y drawdown
- Comparación entre activos e índices (como el MERVAL)
- Generación de reportes de mercado y matriz de correlación

## 📂 Estructura del proyecto

- `main.py`: Cliente MCP principal, con integración a yfinance y manejo de cotizaciones.
- `utilidades_mcp.py`: Funciones analíticas y visualizaciones para estudios más avanzados.

## 🚀 Cómo usarlo

1. Subí el archivo `mcp-mercado-argentino.json` a [https://mcp.so](https://mcp.so)
2. Iniciá sesión con GitHub o Discord
3. Pegá el JSON en “Create MCP” o cargalo como archivo
4. ¡Listo! Probalo y compartilo.

## 📈 Ejemplos de preguntas que podés hacer

- “¿Cómo le fue a GGAL en los últimos 3 meses?”
- “Mostrame los activos argentinos con mayor rendimiento anual”
- “¿Cuál es la beta de ALUA respecto al MERVAL?”
- “Calculá la matriz de correlación entre GGAL, YPFD y PAMP”

## 🛠 Requisitos

- Python 3.8+
- Paquetes:
  - `yfinance`
  - `pandas`
  - `numpy`
  - `matplotlib`

## 📄 Licencia

MIT - Usalo, mejoralo, compartilo.

---

> Creado por Fran 💼🧠
