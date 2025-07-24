from fastapi import HTTPException
from prisma import Prisma
from prisma.errors import PrismaError
from src.Models.filtro_receiver import FiltroReceiver

async def consultar_receiver(filtros: FiltroReceiver, user_rfc: str):
    db = Prisma()
    try:
        await db.connect()

        cfdis_del_usuario = await db.cfdi.find_many(
            where={"user_id": user_rfc}
        )

        receptores_ids = list({cfdi.receiver_id for cfdi in cfdis_del_usuario if cfdi.receiver_id})

        if not receptores_ids:
            return {
                "pagina": filtros.pagina,
                "por_pagina": filtros.por_pagina,
                "total_resultados": 0,
                "total_paginas": 0,
                "datos": []
            }

        where = {"id": {"in": receptores_ids}}

        if filtros.rfc:
            where["rfc_receiver"] = {"contains": filtros.rfc}
        if filtros.nombre:
            where["name_receiver"] = {"contains": filtros.nombre}
        if filtros.uso_cfdi:
            where["cfdi_use"] = {"equals": filtros.uso_cfdi}
        if filtros.regimen:
            where["tax_regime"] = {"equals": filtros.regimen}

        # Validar campo de orden
        campos_validos = ["rfc_receiver", "name_receiver", "cfdi_use", "tax_regime"]
        if filtros.ordenar_por not in campos_validos:
            raise HTTPException(
                status_code=400,
                detail=f"Campo inválido para ordenar: {filtros.ordenar_por}. Debe ser uno de: {campos_validos}"
            )

        skip = (filtros.pagina - 1) * filtros.por_pagina
        take = filtros.por_pagina

        total = await db.receiver.count(where=where)

        if total == 0:
            return {
                "pagina": filtros.pagina,
                "por_pagina": filtros.por_pagina,
                "total_resultados": 0,
                "total_paginas": 0,
                "datos": []
            }

        resultados = await db.receiver.find_many(
            where=where,
            order={filtros.ordenar_por: filtros.ordenar_dir},
            skip=skip,
            take=take,
            include={"cfdis": True}
        )

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
