from prisma import Prisma
from src.Models.FiltroBatchJob import FiltroBatchJob
from datetime import datetime
from fastapi import HTTPException

async def consultar_batchjobs(filtros: FiltroBatchJob, user_rfc: str):
    db = Prisma()
    await db.connect()

    where = {
        "user_id": {"equals": user_rfc}
    }

    if filtros.status:
        where["status"] = {"equals": filtros.status}

    if filtros.min_resultados is not None:
        where["result_count"] = {"gte": filtros.min_resultados}
    if filtros.max_resultados is not None:
        where.setdefault("result_count", {})["lte"] = filtros.max_resultados

    if filtros.fecha_inicio:
        where["created_at"] = {"gte": datetime.combine(filtros.fecha_inicio, datetime.min.time())}

    if filtros.fecha_fin:
        where.setdefault("created_at", {})["lte"] = datetime.combine(filtros.fecha_fin, datetime.max.time())

    ordenar_por = filtros.ordenar_por if filtros.ordenar_por in ["id", "created_at", "status", "result_count"] else "created_at"
    ordenar_dir = filtros.ordenar_dir

    skip = (filtros.pagina - 1) * filtros.por_pagina
    take = filtros.por_pagina

    total = await db.batchjob.count(where=where)

    resultados = await db.batchjob.find_many(
        where=where,
        skip=skip,
        take=take,
        order={ordenar_por: ordenar_dir},
        include={"user": True}
    )

    await db.disconnect()

    return {
        "pagina": filtros.pagina,
        "por_pagina": filtros.por_pagina,
        "total_resultados": total,
        "total_paginas": (total + filtros.por_pagina - 1) // filtros.por_pagina,
        "datos": resultados
    }
