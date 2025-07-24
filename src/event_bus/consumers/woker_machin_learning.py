from src.event_bus.consumer import start_consumer
from src.handlers.handlers_prediccion_sospechoso import procesar_mensaje
import asyncio

if __name__ == "__main__":
    asyncio.run(start_consumer("prediccion_sospechoso", procesar_mensaje))

