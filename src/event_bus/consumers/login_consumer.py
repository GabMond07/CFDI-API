# src/event_bus/consumers/login_consumer.py
import json
from aio_pika import connect_robust
from src.event_bus.handlers.login_handler import handle_login_event
import asyncio

async def start_login_consumer():
    try:
        connection = await connect_robust("amqp://guest:guest@localhost/")
        channel = await connection.channel()
        queue = await channel.declare_queue("login_event", durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    payload = json.loads(message.body)
                    await handle_login_event(payload)
    except asyncio.CancelledError:
        print("Consumidor cancelado por cierre de aplicación (shutdown).")
    except Exception as e:
        print(f"Error en consumidor de login: {e}")
