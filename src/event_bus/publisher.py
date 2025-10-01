import json
from aio_pika import connect_robust, Message, DeliveryMode

async def publish_event(queue_name: str, payload: dict):
    connection = await connect_robust("amqps://hcwrkxpe:nlP9Uxlzr5Gp83TVLK7yB3twzwrT2VMk@shark.rmq.cloudamqp.com/hcwrkxpe")
    channel = await connection.channel()
    await channel.declare_queue(queue_name, durable=True)



    message = Message(
        body=json.dumps(payload).encode(),
        delivery_mode=DeliveryMode.PERSISTENT
    )

    await channel.default_exchange.publish(message, routing_key=queue_name)
    await connection.close()
