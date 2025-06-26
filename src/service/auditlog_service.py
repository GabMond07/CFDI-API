from prisma import Prisma
from datetime import datetime
from fastapi import HTTPException
from src.Models.FiltroAuditLog import FiltroAuditLog

async def consultar_logs(filtros: FiltroAuditLog, user_rfc: str):
    db = Prisma()
    await db.connect()

    where = {
        "user_id": {"equals": user_rfc}
    }

    if filtros.action:
        where["action"] = {"contains": filtros.action}

    if filtros.fecha_inicio:
        where["created_at"] = {"gte": datetime.combine(filtros.fecha_inicio, datetime.min.time())}

    if filtros.fecha_fin:
        where.setdefault("created_at", {})["lte"] = datetime.combine(filtros.fecha_fin, datetime.max.time())

    ordenar_por = filtros.ordenar_por if filtros.ordenar_por in ["action", "created_at"] else "created_at"
    ordenar_dir = filtros.ordenar_dir

    skip = (filtros.pagina - 1) * filtros.por_pagina
    take = filtros.por_pagina

    total = await db.auditlog.count(where=where)

    resultados = await db.auditlog.find_many(
        where=where,
        skip=skip,
        take=take,
        order={ordenar_por: ordenar_dir},
        include={"user": True}  # opcional, muestra RFC o info del usuario
    )

    await db.disconnect()

    return {
        "pagina": filtros.pagina,
        "por_pagina": filtros.por_pagina,
        "total_resultados": total,
        "total_paginas": (total + filtros.por_pagina - 1) // filtros.por_pagina,
        "datos": resultados
    }
