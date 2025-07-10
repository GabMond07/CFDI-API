from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from prisma import Prisma
from typing import List
from src.auth import get_current_user
from src.service.upload_cfdi_service import process_cfdi
import base64

router = APIRouter()

@router.post("/upload_cfdi")
async def upload_cfdi(
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user),
):
    """Endpoint para subir y procesar archivos CFDI XML y PDF."""
    xml_file = None
    pdf_file = None
    for file in files:
        if file.filename.endswith('.xml'):
            xml_file = file
        elif file.filename.endswith('.pdf'):
            pdf_file = file
        else:
            raise HTTPException(status_code=400, detail="Invalid file type. Only XML and PDF files are accepted.")

    if not xml_file:
        raise HTTPException(status_code=400, detail="XML file is required.")

    # Leer el contenido del XML como bytes
    xml_content = await xml_file.read()

    # Procesar el CFDI usando el servicio dentro de un contexto de base de datos
    async with Prisma() as db:
        user_id = current_user['rfc']
        cfdi_record = await process_cfdi(xml_content, user_id, db)

        # Guardar el XML como string en la base de datos
        xml_str = xml_content.decode('utf-8')
        await db.cfdiattachment.create(data={
            'cfdi_id': cfdi_record.id,
            'file_type': 'xml',
            'file_content': xml_str,
        })

        # Guardar el PDF si existe
        if pdf_file:
            pdf_content = await pdf_file.read()
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
            await db.cfdiattachment.create(data={
                'cfdi_id': cfdi_record.id,
                'file_type': 'pdf',
                'file_content': pdf_base64,
            })

    return {"message": "CFDI processed successfully"}