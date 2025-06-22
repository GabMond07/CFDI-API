from prisma import Prisma
from src.Models.filtro_payment import FiltroPayment
from datetime import datetime

async def consultar_pagos(filtros: FiltroPayment, user_rfc: str):
    db = Prisma()
    await db.connect()

    # Obtener CFDIs del usuario autenticado
    cfdis = await db.cfdi.find_many(
        where={"User_RFC": user_rfc}
    )
    cfdi_ids = [c.CFDI_ID for c in cfdis]

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
        "CFDI_ID": {"in": cfdi_ids}
    }

    if filtros.fecha_inicio:
        where["Payment_Date"] = {"gte": datetime.combine(filtros.fecha_inicio, datetime.min.time())}
    if filtros.fecha_fin:
        where.setdefault("Payment_Date", {})["lte"] = datetime.combine(filtros.fecha_fin, datetime.max.time())
    if filtros.forma_pago:
        where["Payment_Form"] = {"equals": filtros.forma_pago}
    if filtros.moneda:
        where["Payment_Currency"] = {"equals": filtros.moneda}
    if filtros.monto_min is not None:
        where["Payment_Amount"] = {"gte": filtros.monto_min}
    if filtros.monto_max is not None:
        where.setdefault("Payment_Amount", {})["lte"] = filtros.monto_max

    ordenar_por = filtros.ordenar_por if filtros.ordenar_por in [
        "Payment_ID", "Payment_Date", "Payment_Form", "Payment_Amount"
    ] else "Payment_Date"

    skip = (filtros.pagina - 1) * filtros.por_pagina
    take = filtros.por_pagina

    total = await db.paymentcomplement.count(where=where)

    resultados = await db.paymentcomplement.find_many(
        where=where,
        skip=skip,
        take=take,
        order={ordenar_por: filtros.ordenar_dir},
        include={
            "cfdi": {
                "include": {
                    "issuer": True,
                    "receiver": True
                }
            }
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
