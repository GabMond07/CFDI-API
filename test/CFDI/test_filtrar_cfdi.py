import pytest
from unittest.mock import AsyncMock, patch
from src.service.consulta_service import filtrar_cfdi
from src.Models.Consulta import FiltroConsulta
from datetime import datetime


@pytest.mark.asyncio
async def test_sin_cfdi_ids():
    filtros = FiltroConsulta(pagina=1, por_pagina=10)

    mock_db = AsyncMock()
    mock_db.connect.return_value = None
    mock_db.cfdi.find_many.return_value = []
    mock_db.disconnect.return_value = None

    with patch("src.service.consulta_service.Prisma", return_value=mock_db):  # Ajusta el import
        result = await filtrar_cfdi(filtros, "RFC123")

    assert result["total_resultados"] == 0
    assert result["datos"] == []


@pytest.mark.asyncio
async def test_con_datos_filtrados():
    filtros = FiltroConsulta(pagina=1, por_pagina=2, categoria="G03", ordenar_por="Total", ordenar_dir="asc")

    fake_cfdis_usuario = [type("CFDI", (), {"CFDI_ID": 1})()]
    fake_resultados = [{"CFDI_ID": 1, "Total": 300, "receiver": {}, "issuer": {}}]

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
    filtros = FiltroConsulta(pagina=1, por_pagina=10, categoria="XYZ")

    mock_db = AsyncMock()
    mock_db.connect.return_value = None
    mock_db.cfdi.find_many.side_effect = [[type("CFDI", (), {"CFDI_ID": 1})()], []]
    mock_db.cfdi.count.return_value = 0
    mock_db.disconnect.return_value = None

    with patch("src.service.consulta_service.Prisma", return_value=mock_db):
        result = await filtrar_cfdi(filtros, "RFC123")

    assert result["total_resultados"] == 0
    assert "mensaje" in result
    assert "No se encontraron CFDIs con la categoría" in result["mensaje"]
