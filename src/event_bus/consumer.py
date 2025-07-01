import json
from aio_pika import connect_robust

async def start_consumer(queue_name: str, callback):
    connection = await connect_robust("amqp://guest:guest@localhost/")
    channel = await connection.channel()
    queue = await channel.declare_queue(queue_name, durable=True)

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                data = json.loads(message.body)
                await callback(data)
