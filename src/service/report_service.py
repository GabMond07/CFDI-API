from prisma import Prisma
from src.Models.FiltroReport import FiltroReport
from datetime import datetime, time
from fastapi import HTTPException

async def consultar_reportes(filtros: FiltroReport, user_rfc: str):
    db = Prisma()
    await db.connect()

    try:
        where = {
            "user_id": {"equals": user_rfc}
        }

        if filtros.format:
            where["format"] = {"equals": filtros.format}

        if filtros.cfdi_id:
            where["cfdi_id"] = {"equals": filtros.cfdi_id}

        if filtros.fecha_inicio or filtros.fecha_fin:
            where["created_at"] = {}
            if filtros.fecha_inicio:
                where["created_at"]["gte"] = datetime.combine(filtros.fecha_inicio, time.min)
            if filtros.fecha_fin:
                where["created_at"]["lte"] = datetime.combine(filtros.fecha_fin, time.max)

        campos_validos = ["id", "created_at", "format"]
        ordenar_por = filtros.ordenar_por if filtros.ordenar_por in campos_validos else "created_at"
        ordenar_dir = filtros.ordenar_dir

        skip = (filtros.pagina - 1) * filtros.por_pagina
        take = filtros.por_pagina

        total = await db.report.count(where=where)

        resultados = await db.report.find_many(
            where=where,
            skip=skip,
            take=take,
            order={ordenar_por: ordenar_dir},
            include={"cfdi": True}
        )

        return {
            "pagina": filtros.pagina,
            "por_pagina": filtros.por_pagina,
            "total_resultados": total,
            "total_paginas": (total + filtros.por_pagina - 1) // filtros.por_pagina,
            "datos": resultados
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

    finally:
        await db.disconnect()
