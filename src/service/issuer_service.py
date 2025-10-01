from prisma import Prisma
from src.Models.filtro_issuer import FiltroIssuer
from prisma.errors import PrismaError
from fastapi import HTTPException

async def consultar_issuer(filtros: FiltroIssuer, user_rfc: str):
    db = Prisma()
    try:
        await db.connect()

        cfdis = await db.cfdi.find_many(
            where={"user_id": user_rfc}
        )

        issuer_ids = list({cfdi.issuer_id for cfdi in cfdis})

        if not issuer_ids:
           await db.disconnect()
           return {
                "pagina": filtros.pagina,
                "por_pagina": filtros.por_pagina,
                "total_resultados": 0,
                "total_paginas": 0,
                "datos": []
            }

        where = {
            "rfc_issuer": {"in": issuer_ids},
            "cfdis": {"some": {}}
        }

        if filtros.rfc:
            where["rfc_issuer"] = {"contains": filtros.rfc}

        if filtros.nombre:
            where["name_issuer"] = {"contains": filtros.nombre}

        if filtros.regimen:
            where["tax_regime"] = {"equals": filtros.regimen}

        ordenar_por = filtros.ordenar_por if filtros.ordenar_por in ["rfc_issuer", "name_issuer", "tax_regime"] else "rfc_issuer"
        ordenar_dir = filtros.ordenar_dir

        skip = (filtros.pagina - 1) * filtros.por_pagina
        take = filtros.por_pagina

        total = await db.issuer.count(where=where)

        resultados = await db.issuer.find_many(
            where=where,
            order={ordenar_por: ordenar_dir},
            skip=skip,
            take=take,
            include = {"cfdis": True}
        )

        await db.disconnect()

        return {
            "pagina": filtros.pagina,
            "por_pagina": filtros.por_pagina,
            "total_resultados": total,
            "total_paginas": (total + filtros.por_pagina - 1) // filtros.por_pagina,
            "datos": resultados
        }
    except PrismaError as e:
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    finally:
        await db.disconnect()