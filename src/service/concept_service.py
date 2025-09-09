from prisma import Prisma
from prisma.errors import PrismaError
from src.Models.filtro_concept import FiltroConcept
from fastapi import HTTPException

async def consultar_conceptos(filtros: FiltroConcept, user_rfc: str):
    db = Prisma()
    try:
        await db.connect()
        where = {
            "cfdi": {
                "user_id": user_rfc
            }
        }

        if filtros.cfdi_id:
            where["cfdi_id"] = filtros.cfdi_id


        if filtros.cfdi_id and filtros.cfdi_id:
            return {
                "pagina": filtros.pagina,
                "por_pagina": filtros.por_pagina,
                "total_resultados": 0,
                "total_paginas": 0,
                "datos": []
            }

        if filtros.description:
            where["description"] = {"contains": filtros.description}
        if filtros.fiscal_key:
            where["fiscal_key"] = {"contains": filtros.fiscal_key}
        if filtros.monto_min is not None:
            where["amount"] = {"gte": filtros.monto_min}
        if filtros.monto_max is not None:
            where.setdefault("amount", {})["lte"] = filtros.monto_max
        if filtros.unit_value_min is not None:
            where.setdefault("unit_value", {})["gte"] = filtros.unit_value_min
        if filtros.unit_value_max is not None:
            where.setdefault("unit_value", {})["lte"] = filtros.unit_value_max
        if filtros.quantity_min is not None:
            where.setdefault("quantity", {})["gte"] = filtros.quantity_min
        if filtros.quantity_max is not None:
            where.setdefault("quantity", {})["lte"] = filtros.quantity_max
        if filtros.discount_min is not None:
            where.setdefault("discount", {})["gte"] = filtros.discount_min
        if filtros.discount_max is not None:
            where.setdefault("discount", {})["lte"] = filtros.discount_max

        if filtros.cfdi_id:
            where["cfdi_id"] = filtros.cfdi_id

        campos_validos = ["id", "description", "amount", "quantity", "unit_value", "discount"]
        if filtros.ordenar_por not in campos_validos:
            raise HTTPException(status_code=400, detail=f"Campo inválido para ordenar: {filtros.ordenar_por}")

        if filtros.solo_con_impuestos is True:
            where["taxes"] = {"some": {}}
        elif filtros.solo_con_impuestos is False:
            where["taxes"] = {"none": {}}

        skip = (filtros.pagina - 1) * filtros.por_pagina
        take = filtros.por_pagina

        total = await db.concept.count(where=where)

        resultados = await db.concept.find_many(
            where=where,
            skip=skip,
            take=take,
            order={filtros.ordenar_por: filtros.ordenar_dir},
            include={
                "taxes": True,
                "cfdi": {
                    "include": {
                        "issuer": True,
                        "receiver": True
                    }
                }
            }
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