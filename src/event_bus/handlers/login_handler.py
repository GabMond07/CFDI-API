from prisma import Prisma
from datetime import datetime
import json

async def handle_login_event(data: dict):
    print(f"Login exitoso recibido desde RabbitMQ: {data['rfc']} en {data['timestamp']}")
    db = Prisma()
    await db.connect()

    try:
        await db.auditlog.create(data={
            "user_id": data["rfc"],
            "action": "Login",
            "details": json.dumps({
                "timestamp": data["timestamp"]
            }),
            "created_at": datetime.fromisoformat(data["timestamp"])
        })
    except Exception as e:
        print(f"Error guardando AuditLog: {e}")
    finally:
        await db.disconnect()
