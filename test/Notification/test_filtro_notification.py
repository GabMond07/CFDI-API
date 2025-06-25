import pytest
from datetime import date
from fastapi import HTTPException
from src.Models.FiltroNotification import FiltroNotification


def test_filtro_notification_valido():
    filtro = FiltroNotification(
        type="alerta",
        status="enviado",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 12, 31),
        cfdi_id=123,
        ordenar_por="created_at",
        ordenar_dir="asc",
        pagina=1,
        por_pagina=10
    )
    assert filtro.status == "enviado"
    assert filtro.ordenar_por == "created_at"
    assert filtro.pagina == 1


def test_fecha_inicio_mayor_a_fecha_fin():
    with pytest.raises(HTTPException) as exc_info:
        FiltroNotification(
            fecha_inicio=date(2024, 12, 31),
            fecha_fin=date(2024, 1, 1)
        )
    assert "La fecha de inicio no puede ser mayor que la fecha final" in str(exc_info.value)


def test_ordenar_por_invalido():
    with pytest.raises(HTTPException) as exc_info:
        FiltroNotification(ordenar_por="invalido")
    assert "Campo inválido para ordenar" in str(exc_info.value)


def test_status_invalido():
    with pytest.raises(HTTPException) as exc_info:
        FiltroNotification(status="completado")  # No está en {'pendiente', 'enviado', 'fallido'}
    assert "Estado inválido" in str(exc_info.value)


def test_paginacion_invalida():
    with pytest.raises(Exception):  # pydantic.ValidationError internamente
        FiltroNotification(pagina=0)

    with pytest.raises(Exception):
        FiltroNotification(por_pagina=101)
