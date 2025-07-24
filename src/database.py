from prisma import Prisma
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar cliente Prisma como singleton
db = Prisma(auto_register=True)

async def connect():
    try:
        await db.connect()
        logger.info("✅ Prisma conectado exitosamente")
    except Exception as e:
        logger.error(f"❌ Error al conectar con Prisma: {str(e)}")
        raise e

async def disconnect():
    try:
        if db.is_connected():
            await db.disconnect()
            logger.info("🔌 Prisma desconectado exitosamente")
    except Exception as e:
        logger.error(f"❌ Error al desconectar Prisma: {str(e)}")
        raise e