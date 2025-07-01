from fastapi import FastAPI, HTTPException, Depends, Request, UploadFile, File, Query
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import FileResponse, JSONResponse
from datetime import timedelta, datetime
from .auth import authenticate_user, create_access_token, create_user, ACCESS_TOKEN_EXPIRE_MINUTES
from .models import UserCredentials, UserRegister, Token, CFDIFilter, CFDISort, PaginatedCFDIResponse, CFDIResponse
from .middleware import auth_middleware
from prisma import Prisma
import jwt
import xml.etree.ElementTree as ET
from .auth import SECRET_KEY, ALGORITHM
from src.router import Consulta
from src.router import issuer
from src.router import receiver
from src.router import concept
from src.router import tax
from src.router import tax_summary
from src.router import payment
from src.router import cfdi_relation
from src.router import report
from src.router import notification
from src.router import auditlog
from src.router import batchjob
from src.router import register_user
from src.router import login_user
from src.router import logout
import base64
import csv
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from src.event_bus.consumer import start_consumer
import asyncio
from src.event_bus.consumers.login_consumer import login_event

app = FastAPI(title="Web API Fiscal", description="API para la gestión de CFDI y autenticación de contribuyentes.", version="1.0.0")

# Inicializar cliente Prisma como singleton
db = Prisma(auto_register=True)  # Auto-registra y mantiene la conexión viva

# Añade el middleware de autenticación
app.middleware("http")(auth_middleware)

# OAuth2 para manejar el token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

app.include_router(Consulta.router, prefix="/api/v1")

app.include_router(issuer.router, prefix="/api/v1")

app.include_router(receiver.router, prefix="/api/v1")

app.include_router(concept.router, prefix="/api/v1")

app.include_router(tax.router, prefix="/api/v1")

app.include_router(tax_summary.router, prefix="/api/v1")

app.include_router(payment.router, prefix="/api/v1")

app.include_router(cfdi_relation.router, prefix="/api/v1")

app.include_router(report.router, prefix="/api/v1")

app.include_router(notification.router, prefix="/api/v1")

app.include_router(auditlog.router, prefix="/api/v1")

app.include_router(batchjob.router, prefix="/api/v1")

app.include_router(register_user.router, prefix="/api/v1")

app.include_router(login_user.router, prefix="/api/v1")

app.include_router(logout.router, prefix="/api/v1")

@app.on_event("startup")
async def startup():
    await db.connect()

    asyncio.create_task(start_consumer("login_exitoso", login_event))

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()  # Desconectar al cerrar la aplicación

@app.get("/cfdi", response_model=PaginatedCFDIResponse, tags=["CFDI"])
async def get_cfdis(
    request: Request,
    filters: CFDIFilter = Depends(),
    sort: CFDISort = Depends(),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100)
):
    """
    Consulta los CFDI del usuario autenticado con filtros, paginación y ordenamiento.
    """
    user_rfc = request.state.user["sub"]

    try:
        where_conditions = {"user_id": user_rfc}

        # Aplicar filtros
        if filters.start_date:
            where_conditions["issue_date"] = where_conditions.get("issue_date", {})
            where_conditions["issue_date"]["gte"] = filters.start_date
        if filters.end_date:
            where_conditions["issue_date"] = where_conditions.get("issue_date", {})
            where_conditions["issue_date"]["lte"] = filters.end_date
        if filters.status:
            where_conditions["status"] = filters.status
        if filters.type:
            where_conditions["type"] = filters.type
        if filters.serie:
            where_conditions["serie"] = filters.serie
        if filters.folio:
            where_conditions["folio"] = filters.folio
        if filters.issuer_id:
            where_conditions["issuer_id"] = filters.issuer_id

        total = await db.cfdi.count(where=where_conditions)

        cfdis = await db.cfdi.find_many(
            where=where_conditions,
            order={sort.field: sort.direction},
            skip=(page - 1) * page_size,
            take=page_size,
            include={
                "issuer": True
            }
        )

        cfdi_list = [
            {
                "id": cfdi.id,
                "uuid": cfdi.uuid,
                "version": cfdi.version,
                "serie": cfdi.serie,
                "folio": cfdi.folio,
                "issue_date": cfdi.issue_date,
                "seal": cfdi.seal,
                "certificate_number": cfdi.certificate_number,
                "certificate": cfdi.certificate,
                "place_of_issue": cfdi.place_of_issue,
                "type": cfdi.type,
                "total": cfdi.total,
                "subtotal": cfdi.subtotal,
                "payment_method": cfdi.payment_method,
                "payment_form": cfdi.payment_form,
                "currency": cfdi.currency,
                "user_id": cfdi.user_id,
                "issuer_id": cfdi.issuer_id,
                "issuer_name": cfdi.issuer.name_issuer if cfdi.issuer else None,
                "cfdi_use": cfdi.cfdi_use
            }
            for cfdi in cfdis
        ]

        return {
            "items": cfdi_list,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying CFDI: {str(e)}")

@app.post("/cfdi/import", tags=["CFDI"])
async def import_cfdi(request: Request, file: UploadFile = File(...)):
    """
    Importa un CFDI a partir de un archivo XML subido por el contribuyente.
    """
    user_rfc = request.state.user["sub"]

    # Leer el contenido del archivo XML
    xml_content = await file.read()
    if not isinstance(xml_content, bytes):
        raise HTTPException(status_code=500, detail="Unexpected file content type")

    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        raise HTTPException(status_code=400, detail="Invalid XML file")

    # Validar que sea un CFDI versión 4.0
    if root.tag != "{http://www.sat.gob.mx/cfd/4}Comprobante":
        raise HTTPException(status_code=400, detail="Invalid CFDI format")

    # Extraer datos del nodo raíz Comprobante
    cfdi_data = {
        "uuid": root.get("UUID"),
        "version": root.get("Version", "4.0"),
        "serie": root.get("Serie"),
        "folio": root.get("Folio"),
        "issue_date": datetime.fromisoformat(root.get("Fecha").replace("Z", "+00:00")),
        "seal": root.get("Sello"),
        "certificate_number": root.get("NoCertificado"),
        "certificate": root.get("Certificado"),
        "place_of_issue": root.get("LugarExpedicion"),
        "type": root.get("TipoDeComprobante"),
        "total": float(root.get("Total", 0)),
        "subtotal": float(root.get("SubTotal", 0)),
        "payment_method": root.get("MetodoPago"),
        "payment_form": root.get("FormaPago"),
        "currency": root.get("Moneda"),
        "cfdi_use": root.find(".//{http://www.sat.gob.mx/cfd/4}Receptor").get("UsoCFDI")
    }

    # Validar tipo de CFDI
    valid_types = ["I", "E", "T", "N", "P", "R"]
    if cfdi_data["type"] not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid TipoDeComprobante")

    try:
        # Verificar si el issuer existe, si no, crearlo
        issuer_rfc = root.find(".//{http://www.sat.gob.mx/cfd/4}Emisor").get("Rfc")
        issuer = await db.issuer.find_unique(where={"rfc_issuer": issuer_rfc})
        if not issuer:
            issuer = await db.issuer.create({
                "rfc_issuer": issuer_rfc,
                "name_issuer": root.find(".//{http://www.sat.gob.mx/cfd/4}Emisor").get("Nombre"),
                "tax_regime": root.find(".//{http://www.sat.gob.mx/cfd/4}Emisor").get("RegimenFiscal")
            })

        # Insertar el CFDI con conexiones a user e issuer
        cfdi = await db.cfdi.create({
            **cfdi_data,
            "user": {"connect": {"rfc": user_rfc}},
            "issuer": {"connect": {"rfc_issuer": issuer_rfc}}
        })

        # Procesar conceptos
        concepts = root.findall(".//{http://www.sat.gob.mx/cfd/4}Concepto")
        for concept in concepts:
            concept_data = {
                "cfdi_id": cfdi.id,
                "fiscal_key": concept.get("ClaveProdServ"),
                "description": concept.get("Descripcion"),
                "quantity": float(concept.get("Cantidad", 0)),
                "unit_value": float(concept.get("ValorUnitario", 0)),
                "amount": float(concept.get("Importe", 0)),
                "discount": float(concept.get("Descuento", 0))
            }
            created_concept = await db.concept.create({
                **concept_data
            })

            # Procesar impuestos
            taxes = concept.findall(".//{http://www.sat.gob.mx/cfd/4}Impuestos//{http://www.sat.gob.mx/cfd/4}Traslado") + \
                    concept.findall(".//{http://www.sat.gob.mx/cfd/4}Impuestos//{http://www.sat.gob.mx/cfd/4}Retencion")
            for tax in taxes:
                tax_data = {
                    "concept_id": created_concept.id,
                    "tax_type": tax.get("Impuesto"),
                    "rate": float(tax.get("TasaOCuota", 0)),
                    "amount": float(tax.get("Importe", 0))
                }
                await db.taxes.create({
                    **tax_data
                })

        # Almacenar el archivo XML como adjunto codificado en Base64
        await db.cfdiattachment.create({
            "cfdi_id": cfdi.id,
            "file_type": "xml",
            "file_content": base64.b64encode(xml_content).decode('utf-8')
        })

        # Procesar relaciones (si aplica, por ejemplo, para E o P)
        related_cfdis = root.find(".//{http://www.sat.gob.mx/cfd/4}CfdiRelacionados")
        if related_cfdis is not None:
            for related in related_cfdis.findall(".//{http://www.sat.gob.mx/cfd/4}CfdiRelacionado"):
                await db.cfdirelation.create({
                    "cfdi_id": cfdi.id,
                    "related_uuid": related.get("UUID"),
                    "relation_type": related_cfdis.get("TipoRelacion", "01")
                })

        return {"message": "CFDI imported successfully", "uuid": cfdi.uuid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing CFDI: {str(e)}")

@app.get("/cfdi/{uuid}/download")
async def download_cfdi(request: Request, uuid: str):
    """
    Descarga el archivo XML de un CFDI previamente importado.
    """
    user_rfc = request.state.user["sub"]

    try:
        # Buscar el CFDI
        cfdi = await db.cfdi.find_unique(
            where={"uuid": uuid},
            include={"user": True, "attachments": True}
        )
        if not cfdi:
            raise HTTPException(status_code=404, detail="CFDI not found")

        # Verificar que el CFDI pertenece al usuario autenticado
        if cfdi.user.rfc != user_rfc:
            raise HTTPException(status_code=403, detail="Unauthorized access to CFDI")

        # Obtener el adjunto (debe haber solo uno por CFDI en este diseño)
        attachment = cfdi.attachments[0] if cfdi.attachments else None
        if not attachment or attachment.file_type != "xml":
            raise HTTPException(status_code=404, detail="No XML attachment found for this CFDI")

        # Decodificar el contenido Base64 a bytes
        xml_content = base64.b64decode(attachment.file_content)

        # Devolver el archivo como respuesta
        return FileResponse(
            path=None,
            content=xml_content,
            media_type="application/xml",
            filename=f"cfdi_{uuid}.xml",
            headers={"Content-Disposition": f"attachment; filename=cfdi_{uuid}.xml"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading CFDI: {str(e)}")

@app.post("/cfdi/visualize")
async def process_data(
    request: Request,
    filters: CFDIFilter = Depends(),
    aggregation: str = Query("sum", regex="^(sum|count|avg|min|max)$"),
    include_details: bool = Query(False)
):
    """
    Procesa datos de CFDI con transformaciones básicas
    """
    user_rfc = request.state.user["sub"]

    try:
        where_conditions = {"user_id": user_rfc}
        if filters.start_date:
            where_conditions["issue_date"] = where_conditions.get("issue_date", {})
            where_conditions["issue_date"]["gte"] = filters.start_date
        if filters.end_date:
            where_conditions["issue_date"] = where_conditions.get("issue_date", {})
            where_conditions["issue_date"]["lte"] = filters.end_date
        if filters.status:
            where_conditions["status"] = filters.status
        if filters.type:
            where_conditions["type"] = filters.type
        if filters.serie:
            where_conditions["serie"] = filters.serie
        if filters.folio:
            where_conditions["folio"] = filters.folio
        if filters.issuer_id:
            where_conditions["issuer_id"] = filters.issuer_id

        cfdis = await db.cfdi.find_many(
            where=where_conditions,
            include={"concepts": include_details, "issuer": True}
        )

        # Agregaciones y transformaciones
        data = [c for c in cfdis]
        if aggregation == "sum":
            result = {"total_amount": sum(cfdi.total for cfdi in data)}
        elif aggregation == "count":
            result = {"cfdi_count": len(data)}
        elif aggregation == "avg":
            result = {"average_total": sum(cfdi.total for cfdi in data) / len(data) if data else 0}
        elif aggregation == "min":
            result = {"min_total": min(cfdi.total for cfdi in data) if data else 0}
        elif aggregation == "max":
            result = {"max_total": max(cfdi.total for cfdi in data) if data else 0}

        # Joins virtuales (incluir conceptos si solicitado)
        if include_details:
            result["details"] = [
                {
                    "uuid": cfdi.uuid,
                    "total": cfdi.total,
                    "concepts": [{"description": c.description, "amount": c.amount} for c in cfdi.concepts]
                }
                for cfdi in data
            ]

        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e)}")
    
@app.post("/cfdi/aggregation")
async def visualize_data(
    request: Request,
    filters: CFDIFilter = Depends(),
    aggregation: str = Query("sum", regex="^(sum|count|avg)$"),
    group_by: Optional[str] = Query(None, regex="^(type|issue_date|serie)$")
):
    """
    Procesa datos de CFDI para visualización con agregación y desagregación.
    """
    user_rfc = request.state.user["sub"]

    try:
        where_conditions = {"user_id": user_rfc}
        if filters.start_date:
            where_conditions["issue_date"] = where_conditions.get("issue_date", {})
            where_conditions["issue_date"]["gte"] = filters.start_date
        if filters.end_date:
            where_conditions["issue_date"] = where_conditions.get("issue_date", {})
            where_conditions["issue_date"]["lte"] = filters.end_date
        if filters.status:
            where_conditions["status"] = filters.status
        if filters.type:
            where_conditions["type"] = filters.type
        if filters.serie:
            where_conditions["serie"] = filters.serie
        if filters.folio:
            where_conditions["folio"] = filters.folio
        if filters.issuer_id:
            where_conditions["issuer_id"] = filters.issuer_id

        cfdis = await db.cfdi.find_many(
            where=where_conditions,
            include={"concepts": True, "issuer": True}
        )

        data = [c for c in cfdis]
        if not data:
            return JSONResponse(content={"message": "No data available"})

        if group_by:
            grouped_data = {}
            for cfdi in data:
                key = getattr(cfdi, group_by)
                if group_by == "issue_date":
                    key = key.isoformat() if key else "Unknown"
                else:
                    key = key if key else "Unknown"
                if key not in grouped_data:
                    grouped_data[key] = []
                grouped_data[key].append(cfdi.total)
            result = {
                "type": "grouped",
                "data": {
                    "labels": list(grouped_data.keys()),
                    "values": [sum(values) for values in grouped_data.values()] if aggregation == "sum" else
                              [len(values) for values in grouped_data.values()] if aggregation == "count" else
                              [sum(values) / len(values) if values else 0 for values in grouped_data.values()] if aggregation == "avg" else []
                }
            }
        else:
            totals = [cfdi.total for cfdi in data]
            result = {
                "type": "aggregate",
                "data": {
                    "label": "Total",
                    "value": sum(totals) if aggregation == "sum" else
                            len(totals) if aggregation == "count" else
                            sum(totals) / len(totals) if aggregation == "avg" else 0
                }
            }

        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error visualizing data: {str(e)}")


# Pendiente -----------------------------------
@app.post("/cfdi/sets")
async def set_operations(
    request: Request,
    filters1: CFDIFilter = Depends(),
    filters2: CFDIFilter = Depends(),
    operation: str = Query("union", regex="^(union|intersection)$")
):
    """
    Realiza operaciones de conjuntos (unión, intersección) entre dos conjuntos de CFDI.
    """
    user_rfc = request.state.user["sub"]

    try:
        # Conjunto 1
        where1 = {"user_id": user_rfc}
        if filters1.start_date:
            where1["issue_date"] = where1.get("issue_date", {})
            where1["issue_date"]["gte"] = filters1.start_date
        if filters1.end_date:
            where1["issue_date"] = where1.get("issue_date", {})
            where1["issue_date"]["lte"] = filters1.end_date
        if filters1.type:
            where1["type"] = filters1.type
        cfdis1 = {cfdi.uuid async for cfdi in db.cfdi.find_many(where=where1)}

        # Conjunto 2
        where2 = {"user_id": user_rfc}
        if filters2.start_date:
            where2["issue_date"] = where2.get("issue_date", {})
            where2["issue_date"]["gte"] = filters2.start_date
        if filters2.end_date:
            where2["issue_date"] = where2.get("issue_date", {})
            where2["issue_date"]["lte"] = filters2.end_date
        if filters2.type:
            where2["type"] = filters2.type
        cfdis2 = {cfdi.uuid async for cfdi in db.cfdi.find_many(where=where2)}

        # Operación de conjuntos
        if operation == "union":
            result_uuids = cfdis1.union(cfdis2)
        elif operation == "intersection":
            result_uuids = cfdis1.intersection(cfdis2)

        result = {"uuids": list(result_uuids)}
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing set operation: {str(e)}")

@app.post("/cfdi/central_tendency")
async def central_tendency(
    request: Request,
    filters: CFDIFilter = Depends(),
    measure: str = Query("avg", regex="^(avg|median|mode)$")
):
    """
    Calcula medidas de tendencia central (promedio, mediana, moda).
    """
    user_rfc = request.state.user["sub"]

    try:
        where_conditions = {"user_id": user_rfc}
        if filters.start_date:
            where_conditions["issue_date"] = where_conditions.get("issue_date", {})
            where_conditions["issue_date"]["gte"] = filters.start_date
        if filters.end_date:
            where_conditions["issue_date"] = where_conditions.get("issue_date", {})
            where_conditions["issue_date"]["lte"] = filters.end_date
        if filters.type:
            where_conditions["type"] = filters.type

        cfdis = await db.cfdi.find_many(
            where=where_conditions
        )

        totals = [cfdi.total for cfdi in cfdis]
        if not totals:
            return JSONResponse(content={"message": "No data available"})

        if measure == "avg":
            result = {"average": np.mean(totals)}
        elif measure == "median":
            result = {"median": np.median(totals)}
        elif measure == "mode":
            result = {"mode": float(np.argmax(np.bincount([int(x) for x in totals])))}

        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating central tendency: {str(e)}")

@app.post("/cfdi/statistics")
async def basic_statistics(
    request: Request,
    filters: CFDIFilter = Depends()
):
    """
    Calcula estadísticas básicas (rango, varianza, desviación estándar, coeficiente de variación).
    """
    user_rfc = request.state.user["sub"]

    try:
        where_conditions = {"user_id": user_rfc}
        if filters.start_date:
            where_conditions["issue_date"] = where_conditions.get("issue_date", {})
            where_conditions["issue_date"]["gte"] = filters.start_date
        if filters.end_date:
            where_conditions["issue_date"] = where_conditions.get("issue_date", {})
            where_conditions["issue_date"]["lte"] = filters.end_date
        if filters.type:
            where_conditions["type"] = filters.type

        cfdis = await db.cfdi.find_many(
            where=where_conditions
        )

        totals = [cfdi.total for cfdi in cfdis]
        if not totals:
            return JSONResponse(content={"message": "No data available"})

        result = {
            "range": max(totals) - min(totals),
            "variance": np.var(totals),
            "std_dev": np.std(totals),
            "cv": (np.std(totals) / np.mean(totals) * 100) if np.mean(totals) != 0 else 0
        }

        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating statistics: {str(e)}")