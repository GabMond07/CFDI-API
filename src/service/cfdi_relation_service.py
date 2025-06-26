from prisma import Prisma
from fastapi import HTTPException
from src.Models.filtro_cfdi_relation import FiltroCFDIRelation

async def consultar_cfdi_relations(filtros: FiltroCFDIRelation, user_rfc: str):
    db = Prisma()
    await db.connect()

    # Obtener los CFDI del usuario autenticado
    cfdis = await db.cfdi.find_many(
        where={"user_id": user_rfc}
    )
    cfdi_ids = [c.id for c in cfdis]

    if not cfdi_ids:
        await db.disconnect()
        return {
            "pagina": filtros.pagina,
            "por_pagina": filtros.por_pagina,
            "total_resultados": 0,
            "total_paginas": 0,
            "datos": []
        }

    # Armar filtros
    where = {
        "cfdi_id": {"in": cfdi_ids}
    }

    if filtros.related_uuid:
        where["related_uuid"] = {"contains": filtros.related_uuid}

    if filtros.relation_type:
        where["relation_type"] = {"equals": filtros.relation_type}

    ordenar_por = filtros.ordenar_por if filtros.ordenar_por in ["id", "relation_type", "related_uuid"] else "id"
    ordenar_dir = filtros.ordenar_dir

    skip = (filtros.pagina - 1) * filtros.por_pagina
    take = filtros.por_pagina

    total = await db.cfdirelation.count(where=where)

    resultados = await db.cfdirelation.find_many(
        where=where,
        order={ordenar_por: ordenar_dir},
        skip=skip,
        take=take,
        include={"cfdi": True}
    )

    await db.disconnect()

    return {
        "pagina": filtros.pagina,
        "por_pagina": filtros.por_pagina,
        "total_resultados": total,
        "total_paginas": (total + filtros.por_pagina - 1) // filtros.por_pagina,
        "datos": resultados
    }
