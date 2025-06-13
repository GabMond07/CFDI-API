from fastapi import FastAPI, HTTPException, Depends, Request, UploadFile, File, Query
from fastapi.security import OAuth2PasswordBearer
from datetime import timedelta, datetime
from .auth import authenticate_user, create_access_token, create_user, ACCESS_TOKEN_EXPIRE_MINUTES
from .models import UserCredentials, UserRegister, Token, CFDIFilter, CFDISort, PaginatedCFDIResponse, CFDIResponse
from .middleware import auth_middleware
from prisma import Prisma
import jwt
import xml.etree.ElementTree as ET
from .auth import SECRET_KEY, ALGORITHM
import base64

app = FastAPI(title="Web API Fiscal")

# Inicializar cliente Prisma como singleton
db = Prisma(auto_register=True)  # Auto-registra y mantiene la conexión viva

# Añade el middleware de autenticación
app.middleware("http")(auth_middleware)

# OAuth2 para manejar el token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@app.on_event("startup")
async def startup():
    await db.connect()  # Conectar al iniciar la aplicación

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()  # Desconectar al cerrar la aplicación

@app.post("/auth/register", response_model=Token)
async def register(user: UserRegister):
    """
    Registra un nuevo contribuyente y devuelve un token JWT.
    """
    try:
        new_user = await create_user(
            rfc=user.rfc,
            password=user.password,
            role_id=1
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": new_user["rfc"], "role_id": new_user["role_id"]},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/login", response_model=Token)
async def login(credentials: UserCredentials):
    """
    Autentica al contribuyente y devuelve un token JWT.
    """
    user = await authenticate_user(credentials.rfc, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect RFC or password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": user["rfc"], "role_id": user["role_id"]},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/logout")
async def logout(request: Request):
    """
    Invalida todos los tokens JWT del usuario eliminándolos de la base de datos.
    """
    token = request.headers.get("Authorization")
    if not token:
        raise HTTPException(status_code=401, detail="Token missing")
    
    if not token.startswith("Bearer "):
        raise HTTPException(status_code=400, detail="Invalid token format")
    
    token = token.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_rfc = payload.get("sub")
        if not user_rfc:
            raise HTTPException(status_code=400, detail="Invalid token payload")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        # Marcar el token como revocado en lugar de eliminarlo
        await db.authtoken.update_many(
            where={"token": token, "user_id": user_rfc, "revoked_at": None},
            data={"revoked_at": datetime.now()}
        )
        return {"message": "Successfully logged out"}
    # Esto elimina el token
    # try:
    #     await db.authtoken.delete_many(
    #         where={"user_id": user_rfc}
    #     )
    #     return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error logging out: {str(e)}")

@app.get("/cfdi", response_model=PaginatedCFDIResponse)
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