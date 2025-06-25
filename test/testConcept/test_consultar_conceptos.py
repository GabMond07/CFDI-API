import pytest
from unittest.mock import AsyncMock, patch
from src.Models.filtro_concept import FiltroConcept
from src.service.concept_service import consultar_conceptos

@pytest.mark.asyncio
async def test_sin_cfdi_ids():
    filtros = FiltroConcept(pagina=1, por_pagina=10)

    mock_db = AsyncMock()
    mock_db.connect.return_value = None
    mock_db.cfdi.find_many.return_value = []
    mock_db.disconnect.return_value = None

    with patch("src.service.concept_service.Prisma", return_value=mock_db):
        resultado = await consultar_conceptos(filtros, "RFC123")
        assert resultado["total_resultados"] == 0
        assert resultado["datos"] == []

@pytest.mark.asyncio
async def test_con_datos_filtrados():
    filtros = FiltroConcept(
        pagina=1,
        por_pagina=2,
        ordenar_por="amount",
        ordenar_dir="asc"
    )

    # Simula CFDIs del usuario
    fake_cfdis_usuario = [type("CFDI", (), {"id": 1})()]

    # Simula conceptos devueltos
    fake_resultados = [{
        "id": 1,
        "description": "Producto A",
        "amount": 300.0,
        "quantity": 2,
        "unit_value": 150.0,
        "discount": 0.0,
        "cfdi": {
            "issuer": {"rfc": "AAA010101AAA"},
            "receiver": {"rfc": "BBB010101BBB"}
        },
        "taxes": []
    }]

    mock_db = AsyncMock()
    mock_db.connect.return_value = None
    mock_db.cfdi.find_many.return_value = fake_cfdis_usuario
    mock_db.concept.count.return_value = 1
    mock_db.concept.find_many.return_value = fake_resultados
    mock_db.disconnect.return_value = None

    with patch("src.service.concept_service.Prisma", return_value=mock_db):
        resultado = await consultar_conceptos(filtros, "RFC123")

        assert resultado["total_resultados"] == 1
        assert len(resultado["datos"]) == 1
        assert resultado["datos"][0]["amount"] == 300.0
        assert resultado["datos"][0]["description"] == "Producto A"
