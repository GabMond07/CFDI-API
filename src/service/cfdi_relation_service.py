from prisma import Prisma
from fastapi import HTTPException
from prisma.errors import PrismaError
from src.Models.filtro_cfdi_relation import FiltroCFDIRelation

async def consultar_cfdi_relations(filtros: FiltroCFDIRelation, user_rfc: str):
    db = Prisma()
    try:
        await db.connect()

        where = {
            "cfdi": {
                "user_id": user_rfc
            }
        }

        if filtros.related_uuid:
            where["related_uuid"] = {"contains": filtros.related_uuid}

        if filtros.relation_type:
            where["relation_type"] = {"equals": filtros.relation_type}

        # Validación de campos de orden
        campos_validos = [ "relation_type", "related_uuid"]
        ordenar_por = filtros.ordenar_por if filtros.ordenar_por in campos_validos else "relation_type"
        ordenar_dir = filtros.ordenar_dir

        skip = (filtros.pagina - 1) * filtros.por_pagina
        take = filtros.por_pagina

        # Total de registros
        total = await db.cfdirelation.count(where=where)

        # Resultados con la relación
        resultados = await db.cfdirelation.find_many(
            where=where,
            order={ordenar_por: ordenar_dir},
            skip=skip,
            take=take,
            include={"cfdi": True}
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
