import pytest
from unittest.mock import AsyncMock, patch
from datetime import date
from src.Models.FiltroAuditLog import FiltroAuditLog
from src.service.auditlog_service import consultar_logs  # Ajusta según tu estructura real

@pytest.mark.asyncio
@patch("src.service.auditlog_service.Prisma")
async def test_consultar_logs_exito(prisma_mock):
    filtros = FiltroAuditLog(
        action="login",
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 1, 31),
        ordenar_por="created_at",
        ordenar_dir="desc",
        pagina=1,
        por_pagina=5
    )
    user_rfc = "RFC123456"

    # Mock de la instancia Prisma y sus métodos
    mock_db = AsyncMock()
    prisma_mock.return_value = mock_db

    # Configurar respuestas simuladas
    mock_db.auditlog.count.return_value = 3
    mock_db.auditlog.find_many.return_value = [
        {
            "id": 1,
            "action": "login",
            "created_at": "2024-01-10T08:00:00",
            "user": {"rfc": user_rfc}
        },
        {
            "id": 2,
            "action": "login",
            "created_at": "2024-01-15T09:30:00",
            "user": {"rfc": user_rfc}
        },
        {
            "id": 3,
            "action": "logout",
            "created_at": "2024-01-20T17:00:00",
            "user": {"rfc": user_rfc}
        },
    ]

    resultado = await consultar_logs(filtros, user_rfc)

    # Validaciones
    assert resultado["pagina"] == 1
    assert resultado["por_pagina"] == 5
    assert resultado["total_resultados"] == 3
    assert resultado["total_paginas"] == 1
    assert len(resultado["datos"]) == 3
    assert resultado["datos"][0]["action"] == "login"

    mock_db.connect.assert_awaited_once()
    mock_db.disconnect.assert_awaited_once()
    mock_db.auditlog.count.assert_awaited_once()
    mock_db.auditlog.find_many.assert_awaited_once()
