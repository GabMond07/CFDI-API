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
        categoria="G03",
        ordenar_por="Amount",
        ordenar_dir="asc"
    )

    fake_cfdis_usuario = [type("CFDI", (), {"CFDI_ID": 1})()]
    fake_resultados = [{
        "CFDI_ID": 1,
        "Total": 300,
        "receiver": {},
        "issuer": {}
    }]

    mock_db = AsyncMock()
    mock_db.connect.return_value = None
    mock_db.cfdi.find_many.side_effect = [fake_cfdis_usuario, fake_resultados]
    mock_db.cfdi.count.return_value = 1
    mock_db.disconnect.return_value = None
    mock_db.concept.count.return_value = 1
    mock_db.concept.find_many.return_value = fake_resultados

    with patch("src.service.concept_service.Prisma", return_value=mock_db):
        resultado = await consultar_conceptos(filtros, "RFC123")
        assert resultado["total_resultados"] == 1
        assert resultado["datos"][0]["Total"] == 300
