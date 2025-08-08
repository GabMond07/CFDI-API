from src.database import db
import json
import xml.etree.ElementTree as ET
import csv
import io
import base64
import pandas as pd
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

async def generate_report_from_data(data: list, format_type: str, user: dict, cfdi_id: int = None, save_report: bool = False) -> dict:
    """
    Genera un reporte a partir de datos en el formato especificado.
    Opcionalmente guarda el reporte en la base de datos.
    """
    format_type = format_type.lower()
    file_content = None
    content_type = None
    report_id = None

    try:
        if format_type == "json":
            file_content = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
            content_type = "application/json"
        elif format_type == "xml":
            root = ET.Element("Report")
            for item in data:
                record = ET.SubElement(root, "Record")
                for key, value in item.items():
                    field = ET.SubElement(record, key)
                    field.text = str(value)
            file_content = ET.tostring(root, encoding="utf-8")
            content_type = "application/xml"
        elif format_type == "csv":
            if not data:
                file_content = "".encode("utf-8")
            else:
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
                file_content = output.getvalue().encode("utf-8")
                output.close()
            content_type = "text/csv"
        elif format_type == "excel":
            if not data:
                file_content = "".encode("utf-8")
            else:
                # Convertir datos a DataFrame, manejando estructuras anidadas
                df = pd.DataFrame(data)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False, sheet_name="Report")
                file_content = output.getvalue()
                output.close()
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            raise ValueError(f"Unsupported format: {format_type}")

        # Guardar el reporte si save_report es True
        if save_report:
            file_content_base64 = base64.b64encode(file_content).decode("utf-8")
            report = await db.report.create({
                "data": {
                    "format": format_type.upper(),
                    "file_content": file_content_base64,
                    "created_at": datetime.now(timezone.utc),
                    "user_id": user["rfc"],
                    "cfdi_id": cfdi_id
                }
            })
            report_id = report.id
            logger.info(f"Report saved with ID {report_id} for user {user['rfc']}")

        return {
            "content": file_content,
            "content_type": content_type,
            "report_id": report_id
        }

    except Exception as e:
        logger.error(f"Error generating report in format {format_type}: {str(e)}")
        raise Exception(f"Failed to generate report: {str(e)}")