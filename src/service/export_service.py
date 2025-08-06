from fastapi import HTTPException
from src.database import db
from src.event_bus.publisher import publish_event
from datetime import datetime, timezone
import json
import pandas as pd
from dicttoxml import dicttoxml
import base64
import os
import logging

logger = logging.getLogger(__name__)

async def generate_report_from_data(data: list, format_type: str, user: dict, cfdi_id: int = None, save_report: bool = False):
    """
    Genera un reporte a partir de datos proporcionados en el formato especificado.
    Opcionalmente guarda el reporte en la base de datos.
    """
    start_time = datetime.now(timezone.utc)
    format_type = format_type.lower()
    if format_type not in ["json", "xml", "csv", "excel"]:
        raise HTTPException(status_code=400, detail="Invalid format. Use json, xml, csv, or excel")

    if not data:
        raise HTTPException(status_code=404, detail="No data provided for report")

    # Generar contenido según el formato
    file_content = None  # Contenido para la respuesta HTTP
    file_content_base64 = None  # Contenido para almacenamiento en DB
    content_type = ""
    
    if format_type == "json":
        file_content = json.dumps(data, ensure_ascii=False)
        file_content_base64 = file_content
        content_type = "application/json"
    elif format_type == "xml":
        file_content = dicttoxml(data, custom_root="data", attr_type=False).decode("utf-8")
        file_content_base64 = file_content
        content_type = "application/xml"
    elif format_type == "csv":
        df = pd.DataFrame(data)
        file_content = df.to_csv(index=False)
        file_content_base64 = file_content
        content_type = "text/csv"
    elif format_type == "excel":
        df = pd.DataFrame(data)
        temp_file = "temp.xlsx"
        output = pd.ExcelWriter(temp_file, engine="openpyxl")
        df.to_excel(output, index=False)
        output.close()
        with open(temp_file, "rb") as f:
            file_content = f.read()
            file_content_base64 = base64.b64encode(file_content).decode("utf-8")
        content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        os.remove(temp_file)

    # Guardar el reporte en la base de datos si se solicita
    report_id = None
    if save_report:
        report_data = {
            "format": format_type.upper(),
            "file_content": file_content_base64,
            "user_id": user["rfc"]
        }
        if cfdi_id is not None:  # Solo incluir cfdi_id si no es None
            report_data["cfdi_id"] = cfdi_id

        report = await db.report.create(data=report_data)
        report_id = report.id

        await publish_event("report_generated", {
            "report_id": report_id,
            "user_id": user["rfc"],
            "format": format_type,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    logger.info(f"Reporte generado (formato: {format_type}, guardado: {save_report}) para RFC: {user['rfc']} en {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos")
    return {"content": file_content, "content_type": content_type, "report_id": report_id}