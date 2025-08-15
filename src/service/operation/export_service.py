from src.database import db
from src.event_bus.publisher import publish_event
from typing import Any, Dict, Optional
import json
import pandas as pd
from dicttoxml import dicttoxml
import base64
import io
import logging
from datetime import datetime, timezone
from fastapi import HTTPException
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

logger = logging.getLogger(__name__)

def flatten_dict(d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
    """Aplana diccionarios anidados para CSV, Excel y otros formatos."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        elif isinstance(v, (list, tuple)):
            items.append((new_key, json.dumps(v)))  # Convertir listas a JSON string
        else:
            items.append((new_key, v))
    return dict(items)

async def generate_report_from_data(
    data: Any,
    format_type: str,
    user: Dict,
    cfdi_id: Optional[int] = None,
    save_report: bool = False,
    name: Optional[str] = None,
    description: Optional[str] = None,
    filters: Optional[Dict] = None,
    operation: Optional[str] = None
) -> Dict:
    """
    Genera un reporte a partir de datos proporcionados en el formato especificado (json, xml, csv, excel, pdf).
    Opcionalmente guarda el reporte en la base de datos y publica un evento.

    Args:
        data: Datos a convertir en reporte (se aceptan listas, diccionarios o valores simples).
        format_type: Formato del reporte (json, xml, csv, excel, pdf).
        user: Información del usuario (incluye rfc).
        cfdi_id: ID del CFDI asociado (opcional).
        save_report: Indica si se debe guardar el reporte en la DB.
        name: Nombre del reporte (opcional).
        description: Descripción del reporte (opcional).
        filters: Filtros utilizados en la consulta (opcional).
        operation: Operación ejecutada (e.g., visualize, join).

    Returns:
        Dict: Contiene el contenido del reporte, tipo de contenido y ID del reporte (si se guarda).
    """
    start_time = datetime.now(timezone.utc)
    format_type = format_type.lower()

    # Validar formato
    if format_type not in ["json", "xml", "csv", "excel", "pdf"]:
        logger.error(f"Formato inválido recibido: {format_type}")
        raise HTTPException(status_code=400, detail="Invalid format. Use json, xml, csv, excel, or pdf")

    # Normalizar datos de entrada a una lista
    if data is None:
        logger.warning("Datos nulos recibidos para la generación del reporte")
        data = []
    elif not isinstance(data, list):
        logger.info(f"Convirtiendo datos no lista a lista: tipo recibido {type(data)}")
        data = [data] if isinstance(data, dict) else [{"value": data}]

    # Validar que los elementos sean procesables
    if data and not all(isinstance(item, dict) for item in data):
        logger.error(f"Datos inválidos: todos los elementos deben ser diccionarios, recibido: {data}")
        raise HTTPException(status_code=400, detail=f"Invalid data: all items must be dictionaries, got {type(data[0]) if data else None}")

    # Definir tipo de contenido
    content_type = {
        "json": "application/json",
        "xml": "application/xml",
        "csv": "text/csv",
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pdf": "application/pdf"
    }[format_type]

    # Generar contenido según el formato
    file_content = None  # Contenido para la respuesta HTTP
    file_content_base64 = None  # Contenido para almacenamiento en DB

    try:
        if format_type == "json":
            file_content = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
            file_content_base64 = file_content.decode('utf-8')

        elif format_type == "xml":
            file_content = dicttoxml(data, custom_root="data", attr_type=False).decode("utf-8").encode('utf-8')
            file_content_base64 = file_content.decode('utf-8')

        elif format_type == "csv":
            flattened_data = [flatten_dict(item) for item in data]
            df = pd.DataFrame(flattened_data if data else [])
            file_content = df.to_csv(index=False, encoding='utf-8').encode('utf-8') if not df.empty else b""
            file_content_base64 = file_content.decode('utf-8') if file_content else ""

        elif format_type == "excel":
            flattened_data = [flatten_dict(item) for item in data]
            df = pd.DataFrame(flattened_data if data else [])
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False)
            file_content = output.getvalue()
            file_content_base64 = base64.b64encode(file_content).decode("utf-8")
            output.close()

        elif format_type == "pdf":
            output = io.BytesIO()
            doc = SimpleDocTemplate(output, pagesize=letter)
            elements = []

            if data:
                # Crear tabla para los datos
                table_data = [list(data[0].keys())]  # Encabezados
                for row in data:
                    table_data.append([str(value) if value is not None else "" for value in row.values()])

                table = Table(table_data)
                style = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),  # Reducir tamaño de fuente
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ])
                table.setStyle(style)
                elements.append(table)
            else:
                # Manejar datos vacíos
                styles = getSampleStyleSheet()
                elements.append(Paragraph("No hay datos disponibles", styles['Normal']))

            doc.build(elements)
            file_content = output.getvalue()
            file_content_base64 = base64.b64encode(file_content).decode("utf-8")
            output.close()

    except Exception as e:
        logger.error(f"Error generando reporte en formato {format_type}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate {format_type} report: {str(e)}")

    # Guardar el reporte en la base de datos si se solicita
    report_id = None
    if save_report:
        try:
            report_data = {
                "format": format_type.upper(),
                "file_content": file_content_base64,
                "user_id": user["rfc"],
                "name": name,
                "description": description,
                "filters": json.dumps(filters) if filters else None,
                "operation": operation
            }
            if cfdi_id is not None:
                report_data["cfdi_id"] = cfdi_id

            report = await db.report.create(data=report_data)
            report_id = report.id

            # Publicar evento de reporte generado
            await publish_event("report_generated", {
                "report_id": report_id,
                "user_id": user["rfc"],
                "format": format_type,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

            logger.info(f"Reporte guardado con ID: {report_id} para RFC: {user['rfc']} en formato {format_type}")
        except Exception as e:
            logger.error(f"Error al guardar el reporte: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to save report: {str(e)}")

    logger.info(
        f"Reporte generado (formato: {format_type}, guardado: {save_report}, "
        f"nombre: {name}, descripción: {description}, operación: {operation}) "
        f"para RFC: {user['rfc']} en {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos"
    )
    return {
        "content": file_content,
        "content_type": content_type,
        "report_id": report_id
    }