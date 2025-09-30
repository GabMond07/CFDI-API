from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from prisma import Prisma
from typing import List
from src.auth import get_current_user
from src.service.upload_cfdi_service import process_cfdi
import base64
import logging
from src.permission import require_permissions

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Upload CFDI"])

@router.post("/upload_cfdi", dependencies=[Depends(require_permissions(["write:cfdis"]))])
async def upload_cfdi(
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Endpoint para subir y procesar múltiples archivos CFDI XML y PDF."""
    xml_files = []
    pdf_files = []
    
    # Separar archivos XML y PDF
    for file in files:
        if file.filename.endswith('.xml'):
            xml_files.append(file)
        elif file.filename.endswith('.pdf'):
            pdf_files.append(file)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid file type for {file.filename}. Only XML and PDF files are accepted.")

    if not xml_files:
        raise HTTPException(status_code=400, detail="At least one XML file is required.")

    results = []
    async with Prisma() as db:
        user_id = current_user['rfc']
        
        # Procesar cada archivo XML
        for xml_file in xml_files:
            try:
                logger.info(f"Procesando archivo XML: {xml_file.filename}")
                # Leer el contenido del XML
                xml_content = await xml_file.read()
                
                # Procesar el CFDI
                cfdi_record = await process_cfdi(xml_content, user_id, db)
                
                # Guardar el XML como string en la base de datos
                xml_str = xml_content.decode('utf-8')
                # await db.cfdiattachment.create(data={
                #     'cfdi_id': cfdi_record.id,
                #     'file_type': 'xml',
                #     'file_content': xml_str,
                # })
                
                # Buscar PDF correspondiente (si lo hay) basado en el nombre del archivo
                # pdf_file = next((pdf for pdf in pdf_files if pdf.filename.startswith(xml_file.filename.split('.')[0])), None)
                # if pdf_file:
                #     logger.info(f"Procesando archivo PDF asociado: {pdf_file.filename}")
                #     pdf_content = await pdf_file.read()
                #     pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
                #     await db.cfdiattachment.create(data={
                #         'cfdi_id': cfdi_record.id,
                #         'file_type': 'pdf',
                #         'file_content': pdf_base64,
                #     })
                
                results.append({
                    "filename": xml_file.filename,
                    "status": "success",
                    "message": "CFDI processed successfully"
                })
                
            except Exception as e:
                logger.error(f"Error al procesar {xml_file.filename}: {str(e)}")
                results.append({
                    "filename": xml_file.filename,
                    "status": "error",
                    "message": f"Failed to process: {str(e)}"
                })
                continue  # Continuar con el siguiente archivo

    return {"results": results}