import pytest
from unittest.mock import AsyncMock, patch
from src.service.consulta_service import filtrar_cfdi
from src.Models.Consulta import FiltroConsulta


@pytest.mark.asyncio
async def test_sin_cfdi_ids():
    filtros = FiltroConsulta(pagina=1, por_pagina=10)

    mock_db = AsyncMock()
    mock_db.connect.return_value = None
    mock_db.cfdi.find_many.return_value = []  # Simula que no hay CFDIs
    mock_db.disconnect.return_value = None

    with patch("src.service.consulta_service.Prisma", return_value=mock_db):
        result = await filtrar_cfdi(filtros, "RFC123")

    assert result["total_resultados"] == 0
    assert result["datos"] == []


@pytest.mark.asyncio
async def test_con_datos_filtrados():
    filtros = FiltroConsulta(
        pagina=1,
        por_pagina=2,
        categoria="G03",
        ordenar_por="total",
        ordenar_dir="asc"
    )

    fake_cfdis_usuario = [type("CFDI", (), {"id": 1})()]  # usa `id`
    fake_resultados = [{
        "id": 1,
        "total": 300,
        "receiver": {},
        "issuer": {}
    }]

    mock_db = AsyncMock()
    mock_db.connect.return_value = None
    mock_db.cfdi.find_many.side_effect = [fake_cfdis_usuario, fake_resultados]
    mock_db.cfdi.count.return_value = 1
    mock_db.disconnect.return_value = None

    with patch("src.service.consulta_service.Prisma", return_value=mock_db):
        result = await filtrar_cfdi(filtros, "RFC123")

    assert result["total_resultados"] == 1
    assert result["datos"] == fake_resultados


@pytest.mark.asyncio
async def test_sin_resultados_para_categoria():
    filtros = FiltroConsulta(
        pagina=1,
        por_pagina=10,
        categoria="XYZ"
    )

    fake_cfdis_usuario = [type("id", (), {"id": 1})()]  # usa `id`
    fake_resultados = []

    mock_db = AsyncMock()
    mock_db.connect.return_value = None
    mock_db.cfdi.find_many.side_effect = [fake_cfdis_usuario, fake_resultados]
    mock_db.cfdi.count.return_value = 0
    mock_db.disconnect.return_value = None

    with patch("src.service.consulta_service.Prisma", return_value=mock_db):
        result = await filtrar_cfdi(filtros, "RFC123")

    assert result["total_resultados"] == 0
    assert "mensaje" in result
    assert "No se encontraron CFDIs con la categoría" in result["mensaje"]
