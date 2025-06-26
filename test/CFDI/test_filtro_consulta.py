import pytest
from pydantic import ValidationError
from src.Models.Consulta import FiltroConsulta
from fastapi import HTTPException
from datetime import datetime

def test_valid_filtro_consulta():
    filtro = FiltroConsulta(
        fecha_inicio=datetime(2024, 1, 1),
        fecha_fin=datetime(2024, 12, 31),
        monto_min=100,
        monto_max=500,
        ordenar_por="total",
        ordenar_dir="desc",
        pagina=1,
        por_pagina=20
    )
    assert filtro.ordenar_por == "total"
    assert filtro.ordenar_dir == "desc"

def test_fecha_inicio_mayor_a_fecha_fin():
    with pytest.raises(ValueError) as excinfo:
        FiltroConsulta(
            fecha_inicio=datetime(2025, 1, 1),
            fecha_fin=datetime(2024, 1, 1)
        )
    assert "fecha de inicio no puede ser mayor" in str(excinfo.value)

def test_monto_min_mayor_que_max():
    with pytest.raises(HTTPException) as excinfo:
        FiltroConsulta(
            monto_min=1000,
            monto_max=500
        )
    assert excinfo.value.status_code == 400
    assert "monto mínimo no puede ser mayor" in str(excinfo.value.detail)

def test_ordenar_por_invalido_usa_valor_default():
    filtro = FiltroConsulta(ordenar_por="Invalido")
    assert filtro.ordenar_por == "Issue_Date"

def test_ordenar_dir_invalido_usa_asc():
    filtro = FiltroConsulta(ordenar_dir="desc")
    assert filtro.ordenar_dir == "desc"
