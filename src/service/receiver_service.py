from prisma import Prisma
from src.Models.filtro_receiver import FiltroReceiver

async def consultar_receiver(filtros: FiltroReceiver, user_rfc: str):
    db = Prisma()
    await db.connect()

    cfdis_del_usuario = await db.cfdi.find_many(
        where={"User_RFC": user_rfc}
    )
    receptores_ids = list({cfdi.Receiver_ID for cfdi in cfdis_del_usuario})

    if not receptores_ids:
        await db.disconnect()
        return {
            "pagina": filtros.pagina,
            "por_pagina": filtros.por_pagina,
            "total_resultados": 0,
            "total_paginas": 0,
            "datos": []
        }
    where = {"Receiver_ID": {"in": receptores_ids}}

    if filtros.rfc:
        where["RFC_Receiver"] = {"contains": filtros.rfc}
    if filtros.nombre:
        where["Name_Receiver"] = {"contains": filtros.nombre}
    if filtros.uso_cfdi:
        where["CFDI_Use"] = {"equals": filtros.uso_cfdi}
    if filtros.regimen:
        where["Tax_Regime"] = {"equals": filtros.regimen}

    ordenar_por = filtros.ordenar_por if filtros.ordenar_por in ["RFC_Receiver", "Name_Receiver", "CFDI_Use", "Tax_Regime"] else "RFC_Receiver"
    ordenar_dir = filtros.ordenar_dir

    skip = (filtros.pagina - 1) * filtros.por_pagina
    take = filtros.por_pagina

    total = await db.receiver.count(where=where)

    resultados = await db.receiver.find_many(
        where=where,
        order={ordenar_por: ordenar_dir},
        skip=skip,
        take=take,
        include = {"cfdis": True}
    )

    await db.disconnect()

    return {
        "pagina": filtros.pagina,
        "por_pagina": filtros.por_pagina,
        "total_resultados": total,
        "total_paginas": (total + filtros.por_pagina - 1) // filtros.por_pagina,
        "datos": resultados
    }
