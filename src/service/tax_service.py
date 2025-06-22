from fastapi import HTTPException
from prisma import Prisma
from prisma.errors import PrismaError
from src.Models.filtro_tax import FiltroTax

async def consultar_taxes(filtros: FiltroTax, user_rfc: str):
    db = Prisma()
    try:
        await db.connect()

        # Obtener CFDIs emitidos por el usuario
        cfdis = await db.cfdi.find_many(where={"User_RFC": user_rfc})
        cfdi_ids = [c.CFDI_ID for c in cfdis]

        if not cfdi_ids:
            return {
                "pagina": filtros.pagina,
                "por_pagina": filtros.por_pagina,
                "total_resultados": 0,
                "total_paginas": 0,
                "datos": []
            }

        # Obtener Concept_IDs de esos CFDIs
        conceptos = await db.concept.find_many(where={"CFDI_ID": {"in": cfdi_ids}})
        concept_ids = [c.Concept_ID for c in conceptos]

        if not concept_ids:
            return {
                "pagina": filtros.pagina,
                "por_pagina": filtros.por_pagina,
                "total_resultados": 0,
                "total_paginas": 0,
                "datos": []
            }

        # Validar concept_id si fue proporcionado
        if filtros.concept_id and filtros.concept_id not in concept_ids:
            return {
                "pagina": filtros.pagina,
                "por_pagina": filtros.por_pagina,
                "total_resultados": 0,
                "total_paginas": 0,
                "datos": []
            }

        # Construir filtros
        where = {"Concept_ID": {"in": concept_ids}}

        if filtros.type:
            where["Type"] = {"equals": filtros.type}
        if filtros.tax:
            where["Tax"] = {"equals": filtros.tax}
        if filtros.rate_min is not None:
            where.setdefault("Rate", {})["gte"] = filtros.rate_min
        if filtros.rate_max is not None:
            where.setdefault("Rate", {})["lte"] = filtros.rate_max
        if filtros.amount_min is not None:
            where.setdefault("Amount", {})["gte"] = filtros.amount_min
        if filtros.amount_max is not None:
            where.setdefault("Amount", {})["lte"] = filtros.amount_max
        if filtros.concept_id:
            where["Concept_ID"] = {"equals": filtros.concept_id}

        # Validar campo de ordenamiento
        campos_validos = ["Tax_ID", "Type", "Tax", "Rate", "Amount", "Concept_ID"]
        if filtros.ordenar_por not in campos_validos:
            raise HTTPException(
                status_code=400,
                detail=f"Campo inválido para ordenar: {filtros.ordenar_por}. Opciones válidas: {campos_validos}"
            )

        ordenar_por = filtros.ordenar_por
        ordenar_dir = filtros.ordenar_dir
        skip = (filtros.pagina - 1) * filtros.por_pagina
        take = filtros.por_pagina

        total = await db.taxes.count(where=where)

        resultados = await db.taxes.find_many(
            where=where,
            order={ordenar_por: ordenar_dir},
            skip=skip,
            take=take,
            include={
                "concepto": {
                    "include": {
                        "cfdi": {
                            "include": {
                                "issuer": True,
                                "receiver": True
                            }
                        }
                    }
                }
            }
        )

        return {
            "pagina": filtros.pagina,
            "por_pagina": filtros.por_pagina,
            "total_resultados": total,
            "total_paginas": (total + filtros.por_pagina - 1) // filtros.por_pagina,
            "datos": resultados
        }

    except PrismaError as e:
        raise HTTPException(status_code=500, detail=f"Error en base de datos: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")
    finally:
        await db.disconnect()
