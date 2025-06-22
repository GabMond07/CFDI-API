import pytest
from unittest.mock import AsyncMock, patch
from src.Models.filtro_receiver import FiltroReceiver
from src.service.receiver_service import consultar_receiver

@pytest.mark.asyncio
@patch("src.service.receiver_service.Prisma")
async def test_consultar_receiver_mockeado(prisma_mock):
    filtros = FiltroReceiver(
        rfc="XAXX",
        nombre="Empresa",
        uso_cfdi="G03",
        regimen="General",
        ordenar_por="RFC_Receiver",
        ordenar_dir="asc",
        pagina=1,
        por_pagina=5
    )

    mock_db = AsyncMock()
    prisma_mock.return_value = mock_db

    mock_db.cfdi.find_many.return_value = [
        AsyncMock(Receiver_ID=1),
        AsyncMock(Receiver_ID=2),
    ]

    mock_db.receiver.count.return_value = 2
    mock_db.receiver.find_many.return_value = [
        {
            "Receiver_ID": 1,
            "RFC_Receiver": "XAXX010101000",
            "Name_Receiver": "Empresa 1",
            "CFDI_Use": "G03",
            "Tax_Regime": "General",
            "cfdis": []
        },
        {
            "Receiver_ID": 2,
            "RFC_Receiver": "ABC123456TST",
            "Name_Receiver": "Empresa 2",
            "CFDI_Use": "G03",
            "Tax_Regime": "Simplificado",
            "cfdis": []
        }
    ]

    result = await consultar_receiver(filtros, user_rfc="RFC_PRUEBA")

    assert isinstance(result, dict)
    assert result["pagina"] == 1
    assert result["por_pagina"] == 5
    assert result["total_resultados"] == 2
    assert len(result["datos"]) == 2
    assert result["datos"][0]["RFC_Receiver"] == "XAXX010101000"
