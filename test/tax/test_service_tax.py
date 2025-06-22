import pytest
from unittest.mock import AsyncMock, patch
from src.Models.filtro_tax import FiltroTax
from src.service.tax_service import consultar_taxes

@pytest.mark.asyncio
@patch("src.service.tax_service.Prisma")
async def test_sin_cfdis(prisma_mock):
    filtros = FiltroTax()
    mock_db = AsyncMock()
    prisma_mock.return_value = mock_db
    mock_db.cfdi.find_many.return_value = []

    result = await consultar_taxes(filtros, user_rfc="RFC_MOCK")

    assert result["datos"] == []
    assert result["total_resultados"] == 0

@pytest.mark.asyncio
@patch("src.service.tax_service.Prisma")
async def test_sin_conceptos(prisma_mock):
    filtros = FiltroTax()
    mock_db = AsyncMock()
    prisma_mock.return_value = mock_db
    mock_db.cfdi.find_many.return_value = [AsyncMock(CFDI_ID=1)]
    mock_db.concept.find_many.return_value = []

    result = await consultar_taxes(filtros, user_rfc="RFC_MOCK")

    assert result["datos"] == []
    assert result["total_resultados"] == 0

@pytest.mark.asyncio
@patch("src.service.tax_service.Prisma")
async def test_con_datos(prisma_mock):
    filtros = FiltroTax(ordenar_por="Tax_ID", ordenar_dir="asc", pagina=1, por_pagina=10)
    mock_db = AsyncMock()
    prisma_mock.return_value = mock_db

    mock_db.cfdi.find_many.return_value = [AsyncMock(CFDI_ID=1)]
    mock_db.concept.find_many.return_value = [AsyncMock(Concept_ID=1)]
    mock_db.taxes.count.return_value = 2
    mock_db.taxes.find_many.return_value = [
        {
            "Tax_ID": 1,
            "Type": "traslado",
            "Tax": "IVA",
            "Rate": 0.16,
            "Amount": 100.0,
            "Concept_ID": 1,
            "concepto": {
                "cfdi": {
                    "issuer": {},
                    "receiver": {}
                }
            }
        }
    ]

    result = await consultar_taxes(filtros, user_rfc="RFC_MOCK")

    assert result["total_resultados"] == 2
    assert len(result["datos"]) == 1
    assert result["datos"][0]["Tax"] == "IVA"

@pytest.mark.asyncio
@patch("src.service.tax_service.Prisma")
async def test_concept_id_no_valido(prisma_mock):
    filtros = FiltroTax(concept_id=999)
    mock_db = AsyncMock()
    prisma_mock.return_value = mock_db

    mock_db.cfdi.find_many.return_value = [AsyncMock(CFDI_ID=1)]
    mock_db.concept.find_many.return_value = [AsyncMock(Concept_ID=1)]

    result = await consultar_taxes(filtros, user_rfc="RFC_MOCK")

    assert result["datos"] == []
    assert result["total_resultados"] == 0
