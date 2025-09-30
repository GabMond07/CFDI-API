import os
import asyncio
import httpx
import logging
from pathlib import Path
from itertools import islice

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración del endpoint y credenciales
ENDPOINT_URL = "http://localhost:8000/api/v1/upload_cfdi"  # Cambiar por tu URL del endpoint
AUTH_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJST0xGMDIxMjI0QlVBIiwicm9sZV9pZCI6MSwiZXhwIjoxNzU1NzIyNTEwLCJzY29wZXMiOlsicmVhZF9jZmRpcyIsIndyaXRlX2NmZGlzIiwicmVwb3J0czpnZW5lcmF0ZSIsImpvaW46ZXhlY3V0ZSIsInNldHM6ZXhlY3V0ZSIsInN0YXRzOnJlYWQiXX0.zlUwlTV0g-5eLnhqF3z2qbeTS1nQVaujhTkm7iHpGvg"  # Cambiar por tu token JWT
FOLDER_PATH = "C:/Users/Gabriel/Desktop/07-octubre2023_anonimizados"  # Cambiar por la ruta de tu carpeta con archivos XML
BATCH_SIZE = 50  # Número de archivos por solicitud
RETRY_ATTEMPTS = 2  # Número de reintentos para archivos fallidos

async def upload_batch(client: httpx.AsyncClient, batch_files: list[Path], attempt: int = 1):
    """Sube un lote de archivos XML al endpoint."""
    try:
        logger.info(f"Intento {attempt} - Procesando lote de {len(batch_files)} archivos: {[f.name for f in batch_files]}")
        
        # Preparar archivos para la solicitud
        files = []
        file_objects = []
        for file_path in batch_files:
            file = open(file_path, 'rb')  # Abrir archivo y mantenerlo abierto
            file_objects.append(file)
            files.append(("files", (file_path.name, file, "application/xml")))
        
        headers = {"Authorization": AUTH_TOKEN}
        
        # Enviar la solicitud al endpoint
        response = await client.post(ENDPOINT_URL, files=files, headers=headers)
        
        # Cerrar archivos después de enviar la solicitud
        for file in file_objects:
            file.close()
        
        if response.status_code == 200:
            logger.info(f"Lote procesado exitosamente: {response.json()}")
            return True, []
        else:
            logger.error(f"Error al procesar el lote: {response.status_code} - {response.text}")
            return False, batch_files
                
    except Exception as e:
        logger.error(f"Excepción al procesar el lote en intento {attempt}: {str(e)}")
        # Cerrar archivos en caso de excepción
        for file in file_objects:
            file.close()
        if attempt < RETRY_ATTEMPTS:
            logger.info(f"Reintentando lote (intento {attempt + 1}/{RETRY_ATTEMPTS})...")
            await asyncio.sleep(1)  # Pausa antes de reintentar
            return await upload_batch(client, batch_files, attempt + 1)
        return False, batch_files

async def upload_file(client: httpx.AsyncClient, file_path: Path, attempt: int = 1):
    """Sube un archivo XML individualmente (usado para reintentos)."""
    try:
        logger.info(f"Intento {attempt} - Reintentando archivo: {file_path.name}")
        with open(file_path, 'rb') as file:
            files = {"files": (file_path.name, file, "application/xml")}
            headers = {"Authorization": AUTH_TOKEN}
            response = await client.post(ENDPOINT_URL, files=files, headers=headers)
            
            if response.status_code == 200:
                logger.info(f"Archivo {file_path.name} procesado exitosamente: {response.json()}")
                return True
            else:
                logger.error(f"Error al reintentar {file_path.name}: {response.status_code} - {response.text}")
                return False
                
    except Exception as e:
        logger.error(f"Excepción al reintentar {file_path.name} en intento {attempt}: {str(e)}")
        if attempt < RETRY_ATTEMPTS:
            logger.info(f"Reintentando archivo {file_path.name} (intento {attempt + 1}/{RETRY_ATTEMPTS})...")
            await asyncio.sleep(1)  # Pausa antes de reintentar
            return await upload_file(client, file_path, attempt + 1)
        return False

async def main():
    """Procesa todos los archivos XML en la carpeta especificada en lotes."""
    folder = Path(FOLDER_PATH)
    
    if not folder.exists():
        logger.error(f"La carpeta {FOLDER_PATH} no existe.")
        return
    
    # Obtener lista de archivos XML
    xml_files = list(folder.glob("*.xml"))
    total_files = len(xml_files)
    logger.info(f"Encontrados {total_files} archivos XML para procesar.")
    
    if total_files == 0:
        logger.warning("No se encontraron archivos XML en la carpeta.")
        return
    
    successful = 0
    failed_files = []
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Procesar archivos en lotes
        for i in range(0, total_files, BATCH_SIZE):
            batch = list(islice(xml_files, i, i + BATCH_SIZE))
            success, failed_batch = await upload_batch(client, batch)
            
            if success:
                successful += len(batch)
            else:
                failed_files.extend(failed_batch)
            
            # Pausa para evitar saturar el servidor
            await asyncio.sleep(0.5)
    
        # Reintentar archivos fallidos individualmente
        if failed_files:
            logger.info(f"Reintentando {len(failed_files)} archivos fallidos individualmente...")
            failed_files_copy = failed_files.copy()
            for file_path in failed_files_copy:
                success = await upload_file(client, file_path)
                if success:
                    successful += 1
                    failed_files.remove(file_path)
                await asyncio.sleep(0.1)
    
    logger.info(f"Procesamiento completado: {successful} archivos exitosos, {len(failed_files)} fallidos.")
    if failed_files:
        logger.info(f"Archivos fallidos: {[f.name for f in failed_files]}")

if __name__ == "__main__":
    asyncio.run(main())