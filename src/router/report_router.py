from fastapi import APIRouter, Depends, HTTPException, Response
from src.permission import require_permissions
from src.auth import get_current_user
from src.database import db
import base64
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/download/{report_id}", dependencies=[Depends(require_permissions(["reports_generate"]))])
async def download_report(report_id: int, user: dict = Depends(get_current_user)):
    """
    Descarga un reporte previamente generado por su ID.
    """
    start_time = datetime.now(timezone.utc)
    
    # Buscar el reporte en la base de datos
    report = await db.report.find_unique(where={"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.user_id != user["rfc"]:
        raise HTTPException(status_code=403, detail="Not authorized to access this report")

    # Determinar el tipo de contenido según el formato
    content_type_map = {
        "JSON": "application/json",
        "XML": "application/xml",
        "CSV": "text/csv",
        "EXCEL": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
    content_type = content_type_map.get(report.format, "application/octet-stream")

    # Decodificar el contenido si es Excel
    content = report.file_content
    if report.format == "EXCEL":
        content = base64.b64decode(report.file_content)

    logger.info(f"Reporte {report_id} descargado para RFC: {user['rfc']} en formato {report.format} en {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos")
    return Response(
        content=content,
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename=report_{report_id}.{report.format.lower()}"}
    )