# from prisma import Prisma
# from datetime import datetime
# import json  # Asegúrate de importar esto
#
# async def login_event(data: dict):
#     rfc = data.get("rfc")
#     timestamp = data.get("timestamp")
#
#     print(f"Login exitoso recibido desde RabbitMQ: {rfc} en {timestamp}")
#
#     db = Prisma()
#     await db.connect()
#     try:
#         await db.auditlog.create(
#             data={
#                 "user_id": rfc,
#                 "action": "login_exitoso",
#                 "details": {
#                     "ip": data.get("ip", "unknown"),
#                     "timestamp": timestamp
#                 },
#                 "created_at": datetime.utcnow()
#             }
#         )
#     finally:
#         await db.disconnect()
