import pytest
from pydantic import ValidationError
from src.Models.filtro_concept import FiltroConcept

def test_filtro_valido():
    filtro = FiltroConcept(
        description="producto A",
        monto_min=10,
        monto_max=100,
        cfdi_id=1,
        ordenar_por="Amount",
        ordenar_dir="desc",
        pagina=1,
        por_pagina=10,
        solo_con_impuestos=True
    )
    assert filtro.monto_min == 10
    assert filtro.ordenar_por == "Amount"


def test_monto_min_negativo():
    with pytest.raises(ValidationError):
        FiltroConcept(monto_min=-5)


def test_monto_max_menor_a_monto_min():
    with pytest.raises(ValidationError) as exc:
        FiltroConcept(monto_min=100, monto_max=50)
    assert "monto_max no puede ser menor que monto_min" in str(exc.value)


def test_ordenar_por_invalido():
    with pytest.raises(ValidationError) as exc:
        FiltroConcept(ordenar_por="campo_invalido")
    assert "ordenar_por debe ser uno de" in str(exc.value)


def test_paginacion_fuera_de_rango():
    with pytest.raises(ValidationError):
        FiltroConcept(pagina=0)

    with pytest.raises(ValidationError):
        FiltroConcept(por_pagina=150)
