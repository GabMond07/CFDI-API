from fastapi import Query, Depends
from typing import Optional
from datetime import datetime
from src.Models.Consulta import FiltroConsulta

def obtener_filtros(
    fecha_inicio: Optional[datetime] = Query(None),
    fecha_fin: Optional[datetime] = Query(None),
    categoria: Optional[str] = Query(None),
    monto_min: Optional[float] = Query(None),
    monto_max: Optional[float] = Query(None),
    ordenar_por: Optional[str] = Query("Total"),
    ordenar_dir: Optional[str] = Query("asc"),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(10, ge=1, le=100)
) -> FiltroConsulta:
    return FiltroConsulta(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        categoria=categoria,
        monto_min=monto_min,
        monto_max=monto_max,
        ordenar_por=ordenar_por,
        ordenar_dir=ordenar_dir,
        pagina=pagina,
        por_pagina=por_pagina
    )
