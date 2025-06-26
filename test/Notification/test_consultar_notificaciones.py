import pytest
from unittest.mock import AsyncMock, patch
from datetime import date
from src.Models.FiltroNotification import FiltroNotification
from src.service.notification_service import consultar_notificaciones

@pytest.mark.asyncio
@patch("src.service.notification_service.Prisma")
async def test_consultar_notificaciones_con_mock(prisma_mock):
    # Configurar filtros simulados
    filtros = FiltroNotification(
        type="correo",
        status="enviado",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 12, 31),
        ordenar_por="created_at",
        ordenar_dir="desc",
        pagina=1,
        por_pagina=5
    )

    # Mock de la conexión a la base de datos
    mock_db = AsyncMock()
    prisma_mock.return_value = mock_db

    # Simular resultados
    mock_db.notification.count.return_value = 2
    mock_db.notification.find_many.return_value = [
        {
            "id": 1,
            "type": "correo",
            "status": "enviado",
            "created_at": "2024-04-01T12:00:00",
            "sent_at": "2024-04-01T12:01:00",
            "cfdi_id": 10,
            "cfdi": {"uuid": "uuid-de-ejemplo"}
        },
        {
            "id": 2,
            "type": "correo",
            "status": "enviado",
            "created_at": "2024-04-02T12:00:00",
            "sent_at": "2024-04-02T12:01:00",
            "cfdi_id": 11,
            "cfdi": {"uuid": "otro-uuid"}
        },
    ]

    # Ejecutar la función con los mocks
    resultado = await consultar_notificaciones(filtros, user_rfc="RFC123456789")

    # Verificaciones
    assert resultado["pagina"] == 1
    assert resultado["por_pagina"] == 5
    assert resultado["total_resultados"] == 2
    assert len(resultado["datos"]) == 2
    assert resultado["datos"][0]["type"] == "correo"
    assert resultado["datos"][0]["cfdi"]["uuid"] == "uuid-de-ejemplo"
