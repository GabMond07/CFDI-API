from prisma import Prisma
from src.Models.filtro_payment import FiltroPayment
from datetime import datetime

async def consultar_pagos(filtros: FiltroPayment, user_rfc: str):
    db = Prisma()
    await db.connect()

    where = {
        "cfdi": {
            "user_id": user_rfc
        }
    }

    if filtros.fecha_inicio:
        where["payment_date"] = {"gte": datetime.combine(filtros.fecha_inicio, datetime.min.time())}
    if filtros.fecha_fin:
        where.setdefault("payment_date", {})["lte"] = datetime.combine(filtros.fecha_fin, datetime.max.time())
    if filtros.forma_pago:
        where["payment_form"] = {"equals": filtros.forma_pago}
    if filtros.moneda:
        where["payment_currency"] = {"equals": filtros.moneda}
    if filtros.monto_min is not None:
        where["payment_amount"] = {"gte": filtros.monto_min}
    if filtros.monto_max is not None:
        where.setdefault("payment_amount", {})["lte"] = filtros.monto_max

    ordenar_por = filtros.ordenar_por if filtros.ordenar_por in [
         "payment_date", "payment_form", "payment_amount"
    ] else "payment_form"

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
