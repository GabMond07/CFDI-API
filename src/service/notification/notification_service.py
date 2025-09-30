from src.database import db
from typing import Dict, Optional
import httpx
import logging
from datetime import datetime, timezone
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class   NotificationService:
    @staticmethod
    async def notify_webhook(
        user_rfc: str,
        event_type: str,
        payload: Dict,
        cfdi_id: Optional[int] = None
    ) -> None:
        """
        Envía una notificación a través del webhook configurado por el usuario y guarda el registro en la base de datos.

        Args:
            user_rfc: RFC del usuario.
            event_type: Tipo de evento (e.g., 'analysis_ready').
            payload: Datos a enviar en el webhook (e.g., {'report_id': 123, 'format': 'excel'}).
            cfdi_id: ID del CFDI asociado (opcional).

        Raises:
            HTTPException: Si no se encuentra el usuario o no tiene webhook configurado.
        """
        start_time = datetime.now(timezone.utc)
        logger.info(f"Iniciando notificación para RFC: {user_rfc}, event_type: {event_type}, cfdi_id: {cfdi_id}")

        # Obtener el usuario y su webhook_url
        user = await db.user.find_first(where={"rfc": user_rfc})
        if not user:
            logger.error(f"Usuario con RFC {user_rfc} no encontrado")
            raise HTTPException(status_code=404, detail=f"User with RFC {user_rfc} not found")
        
        if not user.webhook_url:
            logger.warning(f"No se encontró webhook_url para el usuario con RFC {user_rfc}")
            raise HTTPException(status_code=400, detail="No webhook configured for this user")

        # Crear registro de notificación con estado 'pending'
        notification_data = {
            "user_id": user_rfc,
            "cfdi_id": cfdi_id,
            "type": event_type,
            "status": "pending",
            "payload": payload,
            "created_at": start_time
        }
        notification = await db.notification.create(data=notification_data)
        logger.info(f"Notificación creada con ID: {notification.id}, estado: pending")

        # Enviar solicitud al webhook
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    user.webhook_url,
                    json={
                        "event_type": event_type,
                        "payload": payload,
                        "timestamp": start_time.isoformat()
                    }
                )
                response.raise_for_status()
                # Actualizar estado a 'sent'
                await db.notification.update(
                    where={"id": notification.id},
                    data={"status": "sent", "sent_at": datetime.now(timezone.utc)}
                )
                logger.info(
                    f"Notificación {notification.id} enviada exitosamente a {user.webhook_url} "
                    f"para RFC: {user_rfc}, event_type: {event_type}, "
                    f"en {(datetime.now(timezone.utc) - start_time).total_seconds():.2f} segundos"
                )
        except httpx.HTTPStatusError as e:
            # Actualizar estado a 'failed' si hay un error HTTP
            await db.notification.update(
                where={"id": notification.id},
                data={"status": "failed"}
            )
            logger.error(
                f"Error al enviar notificación {notification.id} a {user.webhook_url}: "
                f"HTTP {e.response.status_code} - {e.response.text}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send webhook notification: HTTP {e.response.status_code}"
            )
        except httpx.RequestError as e:
            # Actualizar estado a 'failed' si hay un error de conexión
            await db.notification.update(
                where={"id": notification.id},
                data={"status": "failed"}
            )
            logger.error(
                f"Error de conexión al enviar notificación {notification.id} a {user.webhook_url}: {str(e)}"
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send webhook notification: {str(e)}"
            )