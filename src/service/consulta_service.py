from prisma import Prisma
from datetime import date
from src.Models.Consulta import FiltroConsulta

async def filtrar_cfdi(filtros: FiltroConsulta, user_rfc: str):
    db = Prisma()
    await db.connect()

    cfdis_usuario = await db.cfdi.find_many(where={"user_id": user_rfc})
    cfdi_ids = [c.id for c in cfdis_usuario]

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
        "user_id": user_rfc
    }

    if filtros.fecha_inicio:
        where_clause.setdefault("issue_date", {})["gte"] = filtros.fecha_inicio
    if filtros.fecha_fin:
        where_clause.setdefault("issue_date", {})["lte"] = filtros.fecha_fin

    if filtros.monto_min is not None:
        where_clause.setdefault("total", {})["gte"] = filtros.monto_min
    if filtros.monto_max is not None:
        where_clause.setdefault("total", {})["lte"] = filtros.monto_max

    if filtros.uuid:
        where_clause["uuid"] = {"contains": filtros.uuid}
    if filtros.serie:
        where_clause["serie"] = {"contains": filtros.serie}
    if filtros.folio:
       where_clause["folio"] = {"contains": filtros.folio}
    if filtros.tipo:
        where_clause["type"] = filtros.tipo
    if filtros.payment_method:
        where_clause["payment_method"] = filtros.payment_method
    if filtros.payment_form:
        where_clause["payment_form"] = filtros.payment_form
    if filtros.currency:
        where_clause["currency"] = filtros.currency
    if filtros.cfdi_use:
        where_clause["cfdi_use"] = filtros.cfdi_use
    if filtros.export_status:
        where_clause["export_status"] = filtros.export_status
    if filtros.issuer_id:
        where_clause["issuer_id"] = filtros.issuer_id
    if filtros.receiver_id is not None:
        where_clause["receiver_id"] = filtros.receiver_id

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
