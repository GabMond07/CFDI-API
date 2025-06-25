import pytest
from pydantic import ValidationError
from src.Models.filtro_issuer import FiltroIssuer

def test_modelo_valido():
    filtro = FiltroIssuer(
        rfc="ABC123456789",
        nombre="Empresa X",
        regimen="General",
        ordenar_por="rfc_issuer",
        ordenar_dir="asc",
        pagina=2,
        por_pagina=20
    )
    assert filtro.rfc == "ABC123456789"
    assert filtro.pagina == 2

def test_ordenar_por_invalido():
    with pytest.raises(ValidationError) as exc_info:
        FiltroIssuer(ordenar_por="invalido")
    assert "ordenar_por" in str(exc_info.value)

def test_pagina_menor_a_1():
    with pytest.raises(ValidationError):
        FiltroIssuer(pagina=0)

def test_por_pagina_fuera_de_rango():
    with pytest.raises(ValidationError):
        FiltroIssuer(por_pagina=200)
