import subprocess
from src.ml.service.predictor import clasificar_todos_cfdis_service
import httpx
import asyncio
from datetime import datetime


async def run_subprocess(command):
    """Ejecuta un subproceso de manera asíncrona"""
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        raise RuntimeError(f"Error en subproceso {command}: {stderr.decode()}")

    return stdout.decode()


async def procesar_mensaje(data):
    print("Mensaje recibido:", data)

    try:
        # Ejecutar los pasos del flujo de ML
        print("Ejecutando extracción de CFDI...")
        await run_subprocess(["python", "src/ml/entrenamiento/extraer_cfdi.py"])

        print("Etiquetando sospechosos...")
        await run_subprocess(["python", "src/ml/entrenamiento/etiquetar_sospechosos.py"])

        print("Entrenando modelo...")
        await run_subprocess(["python", "src/ml/entrenamiento/entrenar_modelo.py"])

        print("Clasificando CFDIs...")
        await run_subprocess(["python", "src/ml/service/predictor.py"])

        # Obtener resultados
        resultados = await clasificar_todos_cfdis_service()

        # Preparar datos para el webhook
        webhook_data = {
            "status": "completed",
            "results": data,
            "timestamp": datetime.now().isoformat()
        }

        # Enviar los resultados al webhook
        headers = {
            "Authorization": f"Bearer {data.get('auth_token', '')}",
            "Content-Type": "application/json"
        }

        if 'callback_url' not in data:
            raise ValueError("No se proporcionó callback_url en los datos")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                data['callback_url'],
                json=webhook_data,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()

        print("Flujo completado y resultados enviados.")

    except Exception as e:
        print(f"Error en procesamiento: {str(e)}")

        # Notificar error al webhook si tenemos URL
        if 'callback_url' in data:
            error_data = {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        data['callback_url'],
                        json=error_data,
                        headers=headers,
                        timeout=30.0
                    )
            except Exception as inner_e:
                print(f"Error al notificar fallo: {str(inner_e)}")

        raise  # Re-lanzar para manejo adicional si es necesario
