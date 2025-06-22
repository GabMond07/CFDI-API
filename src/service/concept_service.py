from prisma import Prisma
from prisma.errors import PrismaError
from src.Models.filtro_concept import FiltroConcept
from fastapi import HTTPException

async def consultar_conceptos(filtros: FiltroConcept, user_rfc: str):
    db = Prisma()
    try:
        await db.connect()

        cfdis = await db.cfdi.find_many(where={"User_RFC": user_rfc})
        cfdi_ids = [c.CFDI_ID for c in cfdis]

        if not cfdi_ids:
            return {
                "pagina": filtros.pagina,
                "por_pagina": filtros.por_pagina,
                "total_resultados": 0,
                "total_paginas": 0,
                "datos": []
            }

        if filtros.cfdi_id and filtros.cfdi_id not in cfdi_ids:
            return {
                "pagina": filtros.pagina,
                "por_pagina": filtros.por_pagina,
                "total_resultados": 0,
                "total_paginas": 0,
                "datos": []
            }

        where = {
            "CFDI_ID": {"in": cfdi_ids}
        }

        if filtros.description:
            where["Description"] = {"contains": filtros.description}
        if filtros.monto_min is not None:
            where["Amount"] = {"gte": filtros.monto_min}
        if filtros.monto_max is not None:
            where.setdefault("Amount", {})["lte"] = filtros.monto_max
        if filtros.cfdi_id:
            where["CFDI_ID"] = filtros.cfdi_id

        campos_validos = ["Concept_ID", "Description", "Amount", "Quantity", "Unit_Value"]
        if filtros.ordenar_por not in campos_validos:
            raise HTTPException(status_code=400, detail=f"Campo inválido para ordenar: {filtros.ordenar_por}")

        # Agrega esta parte al armar el 'where'
        if filtros.solo_con_impuestos is True:
            where["impuestos"] = {"some": {}}
        elif filtros.solo_con_impuestos is False:
            where["impuestos"] = {"none": {}}

        skip = (filtros.pagina - 1) * filtros.por_pagina
        take = filtros.por_pagina

        total = await db.concept.count(where=where)

        resultados = await db.concept.find_many(
            where=where,
            skip=skip,
            take=take,
            order={filtros.ordenar_por: filtros.ordenar_dir},
            include={
                "impuestos": True,
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
