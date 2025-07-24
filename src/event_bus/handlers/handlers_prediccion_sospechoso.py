import subprocess
from src.event_bus.consumer import start_consumer

async def procesar_mensaje(data):
    print("Mensaje recibido:", data)

    print("Ejecutando extracción de CFDI...")
    subprocess.run(["python", "src/ml/entrenamiento/extraer_cfdi.py"])

    print("Etiquetando sospechosos...")
    subprocess.run(["python", "src/ml/entrenamiento/etiquetar_sospechosos.py"])

    print("Entrenando modelo...")
    subprocess.run(["python", "src/ml/entrenamiento/entrenar_modelo.py"])

    print("Clasificando CFDIs...")
    subprocess.run(["python", "src/ml/service/predictor.py"])

    print("Flujo completado.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(start_consumer("prediccion_sospechoso", procesar_mensaje))
