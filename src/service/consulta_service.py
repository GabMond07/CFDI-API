from prisma import Prisma
from datetime import date
from src.Models.Consulta import FiltroConsulta

async def filtrar_cfdi(filtros: FiltroConsulta, user_rfc: str):
    db = Prisma()
    await db.connect()

    cfdis_usuario = await db.cfdi.find_many(where={"User_RFC": user_rfc})
    cfdi_ids = [c.CFDI_ID for c in cfdis_usuario]

    if not cfdi_ids:
        await db.disconnect()
        return {
            "pagina": filtros.pagina,
            "por_pagina": filtros.por_pagina,
            "total_resultados": 0,
            "total_paginas": 0,
            "datos": []
        }

    where_clause = {
        "CFDI_ID": {"in": cfdi_ids}
    }

    # Filtro por fechas
    if filtros.fecha_inicio:
        where_clause.setdefault("Issue_Date", {})["gte"] = filtros.fecha_inicio
    if filtros.fecha_fin:
        where_clause.setdefault("Issue_Date", {})["lte"] = filtros.fecha_fin

    # Filtro por categoría
    if filtros.categoria:
        where_clause["receiver"] = {"CFDI_Use": filtros.categoria}

    # Filtros por monto
    if filtros.monto_min is not None:
        where_clause.setdefault("Total", {})["gte"] = filtros.monto_min
    if filtros.monto_max is not None:
        where_clause.setdefault("Total", {})["lte"] = filtros.monto_max

    # Paginación
    skip = (filtros.pagina - 1) * filtros.por_pagina
    take = filtros.por_pagina

    total = await db.cfdi.count(where=where_clause)

    datos = await db.cfdi.find_many(
        where=where_clause,
        order={filtros.ordenar_por: filtros.ordenar_dir},
        skip=skip,
        take=take,
        include={"issuer": True, "receiver": True}
    )

    # Validar si no se encontró nada con la categoría especificada
    if total == 0 and filtros.categoria:
        await db.disconnect()
        return {
            "mensaje": f"No se encontraron CFDIs con la categoría '{filtros.categoria}' para el usuario.",
            "pagina": filtros.pagina,
            "por_pagina": filtros.por_pagina,
            "total_resultados": 0,
            "total_paginas": 0,
            "datos": []
        }

    await db.disconnect()

    return {
        "pagina": filtros.pagina,
        "por_pagina": filtros.por_pagina,
        "total_resultados": total,
        "total_paginas": (total + filtros.por_pagina - 1) // filtros.por_pagina,
        "datos": datos
    }
