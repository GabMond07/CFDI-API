from prisma import Prisma
from prisma.errors import PrismaError
from fastapi import HTTPException
from collections import defaultdict

async def resumen_impuestos_por_usuario(user_rfc: str):
    db = Prisma()
    try:
        await db.connect()

        # Obtener CFDIs del usuario
        cfdis = await db.cfdi.find_many(where={"User_RFC": user_rfc})
        cfdi_ids = [c.CFDI_ID for c in cfdis]

        if not cfdi_ids:
            return {"por_tipo": [], "por_tasa": [], "por_tipo_tasa": []}

        # Obtener conceptos relacionados con esos CFDIs
        conceptos = await db.concept.find_many(where={"CFDI_ID": {"in": cfdi_ids}})
        concept_ids = [c.Concept_ID for c in conceptos]

        if not concept_ids:
            return {"por_tipo": [], "por_tasa": [], "por_tipo_tasa": []}

        # Obtener impuestos
        impuestos = await db.taxes.find_many(where={"Concept_ID": {"in": concept_ids}})

        # Agrupar los datos
        por_tipo = defaultdict(lambda: {"cantidad": 0, "total": 0.0})
        por_tasa = defaultdict(lambda: {"cantidad": 0, "total": 0.0})
        por_tipo_tasa = defaultdict(lambda: {"cantidad": 0, "total": 0.0})

        for imp in impuestos:
            tipo = imp.Type or "Desconocido"
            tasa = imp.Rate if imp.Rate is not None else 0.0
            monto = imp.Amount if imp.Amount is not None else 0.0

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
