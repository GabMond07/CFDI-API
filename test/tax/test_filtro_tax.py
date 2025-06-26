import pytest
from pydantic import ValidationError
from src.Models.filtro_tax import FiltroTax


def test_filtro_valido():
    """Verifica que se crea correctamente un filtro válido"""
    filtro = FiltroTax(
        type="traslado",
        tax="IVA",
        rate_min=0.1,
        rate_max=0.16,
        amount_min=100,
        amount_max=1000,
        concept_id=5,
        ordenar_por="amount",
        ordenar_dir="asc",
        pagina=2,
        por_pagina=20
    )

    assert filtro.type == "traslado"
    assert filtro.ordenar_por == "amount"
    assert filtro.pagina == 2
    assert filtro.por_pagina == 20


def test_tasa_min_mayor_a_max():
    """Valida que se rechace una tasa mínima mayor a la máxima"""
    with pytest.raises(ValidationError) as exc_info:
        FiltroTax(rate_min=0.20, rate_max=0.10)
    assert "tasa mínima no puede ser mayor que la tasa máxima" in str(exc_info.value)


def test_monto_min_mayor_a_max():
    """Valida que se rechace un monto mínimo mayor al máximo"""
    with pytest.raises(ValidationError) as exc_info:
        FiltroTax(amount_min=500, amount_max=100)
    assert "monto mínimo no puede ser mayor que el monto máximo" in str(exc_info.value)


def test_ordenar_por_invalido():
    """Valida que el campo 'ordenar_por' solo acepte valores válidos"""
    with pytest.raises(ValidationError) as exc_info:
        FiltroTax(ordenar_por="no_existente")
    assert "'ordenar_por' debe ser uno de" in str(exc_info.value)


def test_por_pagina_fuera_de_rango():
    """Valida que por_pagina no permita más de 100 elementos"""
    with pytest.raises(ValidationError):
        FiltroTax(por_pagina=150)


def test_pagina_menor_a_1():
    """Valida que la paginación no acepte páginas menores a 1"""
    with pytest.raises(ValidationError):
        FiltroTax(pagina=0)


def test_valores_limite_validos():
    """Verifica que los valores en el límite (rate_min = rate_max, amount_min = amount_max) son aceptados"""
    filtro = FiltroTax(rate_min=0.16, rate_max=0.16, amount_min=1000, amount_max=1000)
    assert filtro.rate_min == 0.16
    assert filtro.amount_max == 1000
