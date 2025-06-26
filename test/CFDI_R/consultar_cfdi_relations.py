import pytest
from unittest.mock import AsyncMock, patch
from src.Models.filtro_cfdi_relation import FiltroCFDIRelation
from src.service.cfdi_relation_service import consultar_cfdi_relations


@pytest.mark.asyncio
@patch("src.service.cfdi_relation_service.Prisma")
async def test_consultar_cfdi_relations_sin_cfdis(prisma_mock):
    filtros = FiltroCFDIRelation(pagina=1, por_pagina=10)

    mock_db = AsyncMock()
    prisma_mock.return_value = mock_db

    # Simular que no hay cfdis para el usuario
    mock_db.cfdi.find_many.return_value = []

    result = await consultar_cfdi_relations(filtros, user_rfc="RFC123")

    assert result["total_resultados"] == 0
    assert result["datos"] == []
    assert result["pagina"] == 1
    assert result["por_pagina"] == 10


@pytest.mark.asyncio
@patch("src.service.cfdi_relation_service.Prisma")
async def test_consultar_cfdi_relations_con_datos(prisma_mock):
    filtros = FiltroCFDIRelation(
        related_uuid="123e4567-e89b-12d3-a456-426614174000",
        relation_type="04",
        ordenar_por="relation_type",
        ordenar_dir="asc",
        pagina=2,
        por_pagina=5
    )

    mock_db = AsyncMock()
    prisma_mock.return_value = mock_db

    # Simular cfdis del usuario
    mock_db.cfdi.find_many.return_value = [
        AsyncMock(id=1),
        AsyncMock(id=2),
        AsyncMock(id=3),
    ]

    # Simular conteo y resultados de relaciones CFDI
    mock_db.cfdirelation.count.return_value = 7
    mock_db.cfdirelation.find_many.return_value = [
        {
            "id": 10,
            "cfdi_id": 1,
            "related_uuid": "123e4567-e89b-12d3-a456-426614174000",
            "relation_type": "04",
            "cfdi": {"some": "data"}
        },
        {
            "id": 11,
            "cfdi_id": 2,
            "related_uuid": "123e4567-e89b-12d3-a456-426614174000",
            "relation_type": "04",
            "cfdi": {"some": "data"}
        }
    ]

    result = await consultar_cfdi_relations(filtros, user_rfc="RFC123")

    assert result["total_resultados"] == 7
    assert result["pagina"] == 2
    assert result["por_pagina"] == 5
    assert len(result["datos"]) == 2
    assert all("cfdi" in item for item in result["datos"])
    assert result["datos"][0]["relation_type"] == "04"


@pytest.mark.asyncio
@patch("src.service.cfdi_relation_service.Prisma")
async def test_consultar_cfdi_relations_filtro_no_match(prisma_mock):
    filtros = FiltroCFDIRelation(
        related_uuid="no-existe",
        pagina=1,
        por_pagina=10
    )

    mock_db = AsyncMock()
    prisma_mock.return_value = mock_db

    # Simular cfdis del usuario
    mock_db.cfdi.find_many.return_value = [AsyncMock(id=1)]

    # Simular que no hay resultados en cfdirelation para el filtro
    mock_db.cfdirelation.count.return_value = 0
    mock_db.cfdirelation.find_many.return_value = []

    result = await consultar_cfdi_relations(filtros, user_rfc="RFC123")

    assert result["total_resultados"] == 0
    assert result["datos"] == []
