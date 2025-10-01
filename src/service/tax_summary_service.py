from prisma import Prisma
from prisma.errors import PrismaError
from fastapi import HTTPException
from collections import defaultdict

async def resumen_impuestos_por_usuario(user_rfc: str):
    db = Prisma()
    try:
        await db.connect()

        cfdis = await db.cfdi.find_many(where={"user_id": user_rfc})
        cfdi_ids = [c.id  for c in cfdis]

        if not cfdi_ids:
            return {"por_tipo": [], "por_tasa": [], "por_tipo_tasa": []}

        conceptos = await db.concept.find_many(where={"cfdi_id": {"in": cfdi_ids}})
        concept_ids = [c.id for c in conceptos]

        if not concept_ids:
            return {"por_tipo": [], "por_tasa": [], "por_tipo_tasa": []}

        impuestos = await db.taxes.find_many(where={"concept_id": {"in": concept_ids}})

        por_tipo = defaultdict(lambda: {"cantidad": 0, "total": 0.0})
        por_tasa = defaultdict(lambda: {"cantidad": 0, "total": 0.0})
        por_tipo_tasa = defaultdict(lambda: {"cantidad": 0, "total": 0.0})

        for imp in impuestos:
            tipo = imp.tax_type or "Desconocido"
            tasa = imp.rate if imp.rate is not None else 0.0
            monto = imp.amount if imp.amount is not None else 0.0

            por_tipo[tipo]["cantidad"] += 1
            por_tipo[tipo]["total"] += monto

            por_tasa[tasa]["cantidad"] += 1
            por_tasa[tasa]["total"] += monto

            clave_compuesta = f"{tipo} ({tasa}%)"
            por_tipo_tasa[clave_compuesta]["cantidad"] += 1
            por_tipo_tasa[clave_compuesta]["total"] += monto

        return {
            "por_tipo": [{"tipo": k, **v} for k, v in por_tipo.items()],
            "por_tasa": [{"tasa": k, **v} for k, v in por_tasa.items()],
            "por_tipo_tasa": [{"clave": k, **v} for k, v in por_tipo_tasa.items()]
        }

    except PrismaError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    finally:
        await db.disconnect()
