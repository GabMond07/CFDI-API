from fastapi import FastAPI, HTTPException, Depends, Request, Query, UploadFile, File
from fastapi.security import OAuth2PasswordBearer
from datetime import timedelta, datetime
from .auth import authenticate_user, create_access_token, create_user, ACCESS_TOKEN_EXPIRE_MINUTES
from .models import UserCredentials, UserRegister, Token, CFDIFilter, CFDISort, PaginatedCFDIResponse, CFDIFilter, CFDISort
from .middleware import auth_middleware
from prisma import Prisma
import jwt
from .auth import SECRET_KEY, ALGORITHM
import xml.etree.ElementTree as ET
from typing import Optional, List
import lxml.etree as lxml_etree
import logging
import base64

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


app = FastAPI(title="Web API Fiscal")
app.middleware("http")(auth_middleware)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@app.post("/auth/register", response_model=Token)
async def register(user: UserRegister):
    try:
        new_user = await create_user(rfc=user.rfc, password=user.password, role_id=1)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(data={"sub": new_user["rfc"], "role_id": new_user["role_id"]}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/login", response_model=Token)
async def login(credentials: UserCredentials):
    user = await authenticate_user(credentials.rfc, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect RFC or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(data={"sub": user["rfc"], "role_id": user["role_id"]}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/logout")
async def logout(request: Request):
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token missing or invalid format")
    token = token.replace("Bearer ", "")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_rfc = payload.get("sub")
        if not user_rfc:
            raise HTTPException(status_code=400, detail="Invalid token payload")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    prisma = Prisma()
    await prisma.connect()
    try:
        # Marcar el token como revocado en lugar de eliminarlo
        await prisma.authtoken.update_many(
            where={"token": token, "user_id": user_rfc, "revoke_at": None},
            data={"revoke_at": datetime.now()}
        )
        return {"message": "Successfully logged out"}
    finally:
        await prisma.disconnect()

@app.get("/cfdi", response_model=PaginatedCFDIResponse)
async def get_cfdis(request: Request, filters: CFDIFilter = Depends(), sort: CFDISort = Depends(), page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=100)):
    user_rfc = request.state.user["sub"]
    prisma = Prisma()
    await prisma.connect()
    try:
        where_conditions = {"user_id": user_rfc}
        if filters.start_date: where_conditions["issue_date"] = {"gte": filters.start_date}
        if filters.end_date: where_conditions["issue_date"] = {"lte": filters.end_date}
        if filters.status: where_conditions["status"] = filters.status
        if filters.type: where_conditions["type"] = filters.type
        total = await prisma.cfdi.count(where=where_conditions)
        cfdis = await prisma.cfdi.find_many(where=where_conditions, order={sort.field: sort.direction}, skip=(page - 1) * page_size, take=page_size)
        cfdi_list = [{"id": cfdi.id, "uuid": cfdi.uuid, "issue_date": cfdi.issue_date, "payment_method": cfdi.payment_method, "currency": cfdi.currency, "type": cfdi.type, "total": cfdi.total, "subtotal": cfdi.subtotal, "user_id": cfdi.user_id, "payment_form": cfdi.payment_form, "issuer_id": cfdi.issuer_id, "cfdi_use": cfdi.cfdi_use} for cfdi in cfdis]
        return {"items": cfdi_list, "total": total, "page": page, "page_size": page_size}
    finally:
        await prisma.disconnect()

@app.get("/cfdi", response_model=PaginatedCFDIResponse)
async def get_cfdis(
    request: Request,
    filters: CFDIFilter = Depends(),
    sort: CFDISort = Depends(),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    include_details: bool = Query(False)
):
    user_rfc = request.state.user["sub"]
    prisma = Prisma()
    await prisma.connect()
    try:
        where_conditions = {"user_id": user_rfc}
        if filters.start_date: where_conditions["issue_date"] = {"gte": filters.start_date}
        if filters.end_date: where_conditions["issue_date"] = {"lte": filters.end_date}
        if filters.status: where_conditions["status"] = filters.status
        if filters.type: where_conditions["type"] = filters.type
        total = await prisma.cfdi.count(where=where_conditions)
        cfdis = await prisma.cfdi.find_many(where=where_conditions, order={sort.field: sort.direction}, skip=(page - 1) * page_size, take=page_size)
        
        cfdi_list = []
        for cfdi in cfdis:
            cfdi_data = {
                "id": cfdi.id,
                "uuid": cfdi.uuid,
                "version": cfdi.version,
                "serie": cfdi.serie,
                "folio": cfdi.folio,
                "issue_date": cfdi.issue_date,
                "seal": cfdi.seal,
                "certificate_no": cfdi.certificate_no,
                "certificate": cfdi.certificate,
                "place_of_issue": cfdi.place_of_issue,
                "type": cfdi.type,
                "currency": cfdi.currency,
                "total": cfdi.total,
                "subtotal": cfdi.subtotal,
                "payment_method": cfdi.payment_method,
                "payment_form": cfdi.payment_form,
                "user_id": cfdi.user_id,
                "issuer_id": cfdi.issuer_id,
                "cfdi_use": cfdi.cfdi_use,
                "related_cfdis": cfdi.related_cfdis,
                "global_info": cfdi.global_info
            }
            if include_details:
                concepts = await prisma.concept.find_many(where={"cfdi_id": cfdi.id})
                taxes = await prisma.taxes.find_many(where={"concept_id": {"in": [c.id for c in concepts]}})
                cfdi_data["concepts"] = [{"id": c.id, "fiscal_key": c.fiscal_key, "description": c.description, "quantity": c.quantity, "unit_value": c.unit_value, "amount": c.amount, "discount": c.discount} for c in concepts]
                cfdi_data["taxes"] = [{"id": t.id, "tax_type": t.tax_type, "rate": t.rate, "amount": t.amount} for t in taxes]
            cfdi_list.append(cfdi_data)

        return {"items": cfdi_list, "total": total, "page": page, "page_size": page_size}
    finally:
        await prisma.disconnect()

@app.post("/cfdi/import")
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

    prisma = Prisma()
    await prisma.connect()
    try:
        # Verificar si el issuer existe, si no, crearlo
        issuer_rfc = root.find(".//{http://www.sat.gob.mx/cfd/4}Emisor").get("Rfc")
        issuer = await prisma.issuer.find_unique(where={"rfc_issuer": issuer_rfc})
        if not issuer:
            issuer = await prisma.issuer.create({
                "rfc_issuer": issuer_rfc,
                "name_issuer": root.find(".//{http://www.sat.gob.mx/cfd/4}Emisor").get("Nombre"),
                "tax_regime": root.find(".//{http://www.sat.gob.mx/cfd/4}Emisor").get("RegimenFiscal")
            })

        # Insertar el CFDI con conexiones a user e issuer
        cfdi = await prisma.cfdi.create({
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
            created_concept = await prisma.concept.create({
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
                await prisma.taxes.create({
                    **tax_data
                })

        # Almacenar el archivo XML como adjunto codificado en Base64
        await prisma.cfdiattachment.create({
            "cfdi_id": cfdi.id,
            "file_type": "xml",
            "file_content": base64.b64encode(xml_content).decode('utf-8')  # Codificar a Base64
        })

        # Procesar relaciones (si aplica, por ejemplo, para E o P)
        related_cfdis = root.find(".//{http://www.sat.gob.mx/cfd/4}CfdiRelacionados")
        if related_cfdis is not None:
            for related in related_cfdis.findall(".//{http://www.sat.gob.mx/cfd/4}CfdiRelacionado"):
                await prisma.cfdirelation.create({
                    "cfdi_id": cfdi.id,
                    "related_uuid": related.get("UUID"),
                    "relation_type": related_cfdis.get("TipoRelacion", "01")
                })

        return {"message": "CFDI imported successfully", "uuid": cfdi.uuid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing CFDI: {str(e)}")
    finally:
        await prisma.disconnect()