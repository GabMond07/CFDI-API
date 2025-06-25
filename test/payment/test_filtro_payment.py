import pytest
from datetime import date
from fastapi import HTTPException
from src.Models.filtro_payment import FiltroPayment

def test_filtro_valido():
    filtro = FiltroPayment(
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 12, 31),
        forma_pago="01",
        moneda="MXN",
        monto_min=100.0,
        monto_max=1000.0,
        ordenar_por="amount",
        ordenar_dir="desc",
        pagina=1,
        por_pagina=20
    )
    assert filtro.monto_min == 100.0
    assert filtro.ordenar_dir == "desc"
    assert filtro.ordenar_por == "amount"

def test_fecha_inicio_mayor_a_fecha_fin():
    with pytest.raises(HTTPException) as exc_info:
        FiltroPayment(
            fecha_inicio=date(2024, 12, 31),
            fecha_fin=date(2024, 1, 1)
        )
    assert "fecha_inicio no puede ser mayor que fecha_fin" in str(exc_info.value.detail)

def test_monto_min_negativo():
    with pytest.raises(HTTPException) as exc_info:
        FiltroPayment(monto_min=-1)
    assert "monto_min no puede ser negativo" in str(exc_info.value.detail)

def test_monto_max_negativo():
    with pytest.raises(HTTPException) as exc_info:
        FiltroPayment(monto_max=-1)
    assert "monto_max no puede ser negativo" in str(exc_info.value.detail)

def test_monto_min_mayor_a_max():
    with pytest.raises(HTTPException) as exc_info:
        FiltroPayment(monto_min=500, monto_max=100)
    assert "monto_min no puede ser mayor que monto_max" in str(exc_info.value.detail)

def test_ordenar_por_invalido():
    with pytest.raises(HTTPException) as exc_info:
        FiltroPayment(ordenar_por="campo_invalido")
    assert "ordenar_por debe ser uno de" in str(exc_info.value.detail)

def test_ordenar_dir_invalido():
    with pytest.raises(HTTPException) as exc_info:
        FiltroPayment(ordenar_dir="sube")
    assert "ordenar_dir debe ser 'asc' o 'desc'" in str(exc_info.value.detail)
