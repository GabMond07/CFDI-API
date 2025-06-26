import pytest
from pydantic import ValidationError
from datetime import date
from src.Models.FiltroAuditLog import FiltroAuditLog


def test_filtro_auditlog_valido():
    filtro = FiltroAuditLog(
        action="login",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 12, 31),
        ordenar_por="created_at",
        ordenar_dir="desc",
        pagina=1,
        por_pagina=10
    )
    assert filtro.ordenar_por == "created_at"
    assert filtro.ordenar_dir == "desc"
    assert filtro.pagina == 1


def test_filtro_auditlog_fecha_inicio_mayor_a_fecha_fin():
    with pytest.raises(ValidationError) as exc:
        FiltroAuditLog(
            fecha_inicio=date(2024, 12, 31),
            fecha_fin=date(2024, 1, 1)
        )
    assert "La fecha de inicio no puede ser mayor que la fecha final" in str(exc.value)


def test_filtro_auditlog_ordenar_por_invalido():
    with pytest.raises(ValidationError) as exc:
        FiltroAuditLog(ordenar_por="campo_invalido")
    assert "Campo inválido para ordenar" in str(exc.value)


def test_filtro_auditlog_paginacion_fuera_de_rango():
    with pytest.raises(ValidationError):
        FiltroAuditLog(pagina=0)

    with pytest.raises(ValidationError):
        FiltroAuditLog(por_pagina=200)
