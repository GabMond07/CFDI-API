from src.database import db
from typing import Any, Dict
import json
import xml.etree.ElementTree as ET
import csv
import io
import base64
import pandas as pd
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

async def generate_report_from_data(
    data: Any,
    format_type: str,
    user: Dict,
    cfdi_id: int = None,
    save_report: bool = False
) -> Dict:
    """
    Genera un reporte en el formato especificado (json, xml, csv, excel) y opcionalmente lo guarda en la base de datos.
    JSON, XML y CSV se almacenan como texto plano; Excel se almacena como base64.
    """
    try:
        # Validar format_type
        format_type = format_type.lower()
        if format_type not in ["json", "xml", "csv", "excel"]:
            raise ValueError(f"Invalid format: {format_type}. Must be json, xml, csv, or excel")

        content_type = {
            "json": "application/json",
            "xml": "application/xml",
            "csv": "text/csv",
            "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }[format_type]

        # Generar contenido según el formato
        file_content = None
        file_content_for_db = None

        if format_type == "json":
            file_content = json.dumps(data, ensure_ascii=False)
            file_content_for_db = file_content  # Almacenar como texto plano

        elif format_type == "xml":
            root = ET.Element("Report")
            for item in data:
                record = ET.SubElement(root, "Record")
                for key, value in item.items():
                    field = ET.SubElement(record, key)
                    field.text = str(value) if value is not None else ""
            file_content = ET.tostring(root, encoding="unicode")
            file_content_for_db = file_content  # Almacenar como texto plano

        elif format_type == "csv":
            output = io.StringIO()
            if data:
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            file_content = output.getvalue()
            file_content_for_db = file_content  # Almacenar como texto plano
            output.close()

        elif format_type == "excel":
            output = io.BytesIO()
            df = pd.DataFrame(data)
            df.to_excel(output, index=False, engine="openpyxl")
            file_content = output.getvalue()
            file_content_for_db = base64.b64encode(file_content).decode("utf-8")  # Almacenar como base64
            output.close()

        # Guardar el reporte en la base de datos si save_report es True
        report_id = None
        if save_report:
            try:
                report = await db.report.create({
                    "cfdi_id": cfdi_id,
                    "format": format_type.upper(),
                    "file_content": file_content_for_db,
                    "user_id": user["rfc"]
                })
                report_id = report.id
                logger.info(f"Reporte guardado con ID: {report_id} para RFC: {user['rfc']} en formato {format_type}")
            except Exception as e:
                logger.error(f"Error al guardar el reporte: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to save report: {str(e)}")

        return {
            "content": file_content,
            "content_type": content_type,
            "report_id": report_id
        }

    except Exception as e:
        logger.error(f"Error generando reporte: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")