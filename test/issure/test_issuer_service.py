import pytest
from unittest.mock import AsyncMock, patch
from src.Models.filtro_issuer import FiltroIssuer
from src.service.issuer_service import consultar_issuer

@pytest.mark.asyncio
@patch("src.service.issuer_service.Prisma")
async def test_consultar_issuer_con_mock(prisma_mock):
    # Crear filtros simulados
    filtros = FiltroIssuer(
        rfc="ABC",
        nombre="Empresa",
        regimen="General",
        ordenar_por="RFC_Issuer",
        ordenar_dir="asc",
        pagina=1,
        por_pagina=5
    )

    # Crear instancia simulada de Prisma y sus métodos mockeados
    mock_db = AsyncMock()
    prisma_mock.return_value = mock_db

    # Simular respuesta de cfdi.find_many con emisores del usuario
    mock_db.cfdi.find_many.return_value = [
        AsyncMock(Issuer_ID=1),
        AsyncMock(Issuer_ID=2),
    ]

    # Simular respuesta de issuer.count y issuer.find_many
    mock_db.issuer.count.return_value = 2
    mock_db.issuer.find_many.return_value = [
        {
            "Issuer_ID": 1,
            "RFC_Issuer": "ABC123456789",
            "Name_Issuer": "Empresa Mock",
            "Tax_Regime": "General",
            "cfdis": []
        },
        {
            "Issuer_ID": 2,
            "RFC_Issuer": "XYZ987654321",
            "Name_Issuer": "Otra Empresa",
            "Tax_Regime": "Simplificado",
            "cfdis": []
        }
    ]

    # Llamar la función que se está probando
    result = await consultar_issuer(filtros, user_rfc="RFC_MOCK")

    # Verificaciones
    assert isinstance(result, dict)
    assert result["pagina"] == 1
    assert result["por_pagina"] == 5
    assert result["total_resultados"] == 2
    assert len(result["datos"]) == 2
    assert result["datos"][0]["RFC_Issuer"] == "ABC123456789"
