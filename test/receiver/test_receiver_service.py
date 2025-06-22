import pytest
from pydantic import ValidationError
from src.Models.filtro_receiver import FiltroReceiver

def test_modelo_valido_receiver():
    filtro = FiltroReceiver(
        rfc="XAXX010101000",
        nombre="Empresa de Ejemplo",
        uso_cfdi="G01",
        regimen="General",
        ordenar_por="RFC_Receiver",
        ordenar_dir="asc",
        pagina=1,
        por_pagina=10
    )
    assert filtro.rfc == "XAXX010101000"
    assert filtro.pagina == 1

def test_ordenar_por_invalido_receiver():
    with pytest.raises(ValidationError):
        FiltroReceiver(ordenar_por="invalido")

def test_paginacion_invalida_receiver():
    with pytest.raises(ValidationError):
        FiltroReceiver(pagina=0)

def test_por_pagina_fuera_rango_receiver():
    with pytest.raises(ValidationError):
        FiltroReceiver(por_pagina=101)
