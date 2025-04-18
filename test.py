from main import ClienteYFinanceMCP, SolicitudHistorico, Intervalo
from datetime import datetime, timedelta

# Inicializar cliente
cliente = ClienteYFinanceMCP()

# Obtener datos recientes de GGAL (últimos 30 días)
desde = datetime.now() - timedelta(days=30)
solicitud = SolicitudHistorico(
    simbolo="GGAL",
    desde=desde,
    intervalo=Intervalo.DIA_1
)

# Ejecutar consulta
print("Obteniendo datos de GGAL...")
respuesta = cliente.obtener_historico(solicitud)

# Mostrar resultados
if respuesta.estado == "OK" and respuesta.datos:
    print(f"Se obtuvieron {len(respuesta.datos)} registros")
    for cotizacion in respuesta.datos[:5]:  # Mostrar primeros 5 días
        print(f"{cotizacion.timestamp.date()}: Apertura: {cotizacion.apertura:.2f}, Cierre: {cotizacion.cierre:.2f}")
else:
    print(f"Error: {respuesta.mensaje}")

# Probar obtener la última cotización del Merval
print("\nObteniendo última cotización del Merval...")
ultima = cliente.obtener_ultima_cotizacion("MERVAL")
if ultima:
    print(f"Fecha: {ultima.timestamp.date()}")
    print(f"Cierre: {ultima.cierre:.2f}")
else:
    print("No se pudo obtener la cotización del Merval")