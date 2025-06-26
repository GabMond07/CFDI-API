import pytest
from unittest.mock import AsyncMock, patch
from src.Models.filtro_payment import FiltroPayment
from src.service.payment_service import consultar_pagos
from datetime import date

@pytest.mark.asyncio
async def test_consultar_pagos_con_resultados():
    filtros = FiltroPayment(
        pagina=1,
        por_pagina=10,
        ordenar_por="payment_date",
        ordenar_dir="asc"
    )

    # CFDIs de prueba simulados
    fake_cfdis = [type("CFDI", (), {"id": 1})(), type("CFDI", (), {"id": 2})()]

    # Resultados simulados de pagos
    fake_resultados = [
        {
            "id": 101,
            "cfdi_id": 1,
            "payment_date": "2024-06-10",
            "payment_form": "03",
            "payment_amount": 1000.0,
            "cfdi": {
                "issuer": {"rfc": "AAA010101AAA"},
                "receiver": {"rfc": "XAXX010101000"}
            }
        }
    ]

    # Mock del cliente Prisma
    mock_db = AsyncMock()
    mock_db.connect.return_value = None
    mock_db.disconnect.return_value = None
    mock_db.cfdi.find_many.return_value = fake_cfdis
    mock_db.paymentcomplement.count.return_value = 1
    mock_db.paymentcomplement.find_many.return_value = fake_resultados

    with patch("src.service.payment_service.Prisma", return_value=mock_db):
        result = await consultar_pagos(filtros, "RFC123456789")

        assert result["total_resultados"] == 1
        assert result["datos"] == fake_resultados
        assert result["pagina"] == 1
        assert result["por_pagina"] == 10
        assert result["total_paginas"] == 1
