from prisma import Prisma
from src.Models.FiltroNotification import FiltroNotification
from datetime import datetime
from fastapi import HTTPException

async def consultar_notificaciones(filtros: FiltroNotification, user_rfc: str):
    db = Prisma()
    await db.connect()

    where = {
        "user_id": {"equals": user_rfc}
    }

    if filtros.type:
        where["type"] = {"equals": filtros.type}

    if filtros.status:
        where["status"] = {"equals": filtros.status}

    if filtros.cfdi_id:
        where["cfdi_id"] = {"equals": filtros.cfdi_id}

    if filtros.fecha_inicio:
        where["created_at"] = {"gte": datetime.combine(filtros.fecha_inicio, datetime.min.time())}

    if filtros.fecha_fin:
        where.setdefault("created_at", {})["lte"] = datetime.combine(filtros.fecha_fin, datetime.max.time())

    ordenar_por = filtros.ordenar_por if filtros.ordenar_por in ["id", "type", "status", "created_at", "sent_at"] else "created_at"
    ordenar_dir = filtros.ordenar_dir
    skip = (filtros.pagina - 1) * filtros.por_pagina
    take = filtros.por_pagina

    total = await db.notification.count(where=where)

    resultados = await db.notification.find_many(
        where=where,
        order={ordenar_por: ordenar_dir},
        skip=skip,
        take=take,
        include={
            "cfdi": True
        }
    )

    await db.disconnect()

    return {
        "pagina": filtros.pagina,
        "por_pagina": filtros.por_pagina,
        "total_resultados": total,
        "total_paginas": (total + filtros.por_pagina - 1) // filtros.por_pagina,
        "datos": resultados
    }
