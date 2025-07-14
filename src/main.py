from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from src.middleware import auth_middleware
from src.router import (
    Consulta, issuer, receiver, concept, tax, tax_summary, payment,
    cfdi_relation, report, notification, auditlog, batchjob,
    register_user, login_user, logout, visualize, upload_cfdi,
    operations_statics
)
from src.ml.router import sospechoso_router, routerCFDI
from src.event_bus.consumers.login_consumer import start_login_consumer
# from src.event_bus.publisher import init_event_bus, close_event_bus  futuras mejoras
from src.database import db
import asyncio
import os
import logging
from dotenv import load_dotenv
# from pyinstrument import Profiler  

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Verificar variables críticas
if "DATABASE_URL" not in os.environ:
    logger.warning("ADVERTENCIA: DATABASE_URL no está configurada.")
if "SECRET_KEY" not in os.environ:
    logger.warning("ADVERTENCIA: SECRET_KEY no está configurada.")

# Configuración de FastAPI
app = FastAPI(
    title="Web API Fiscal",
    description="API para la gestión de CFDI y autenticación de contribuyentes.",
    version="1.0.0"
)

# OAuth2 para manejar el token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Ajustado al puerto del frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware de autenticación
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)

# Middleware de profiling (opcional)
# @app.middleware("http")
# async def profile_request(request, call_next):
#     profiler = Profiler()
#     profiler.start()
#     response = await call_next(request)
#     profiler.stop()
#     logger.info(profiler.output_text(unicode=True, color=True))
#     return response

# Incluir routers con prefijo /api/v1
app.include_router(Consulta.router, prefix="/api/v1")
app.include_router(issuer.router, prefix="/api/v1")
app.include_router(receiver.router, prefix="/api/v1")
app.include_router(concept.router, prefix="/api/v1")
app.include_router(tax.router, prefix="/api/v1")
app.include_router(tax_summary.router, prefix="/api/v1")
app.include_router(payment.router, prefix="/api/v1")
app.include_router(cfdi_relation.router, prefix="/api/v1")
app.include_router(report.router, prefix="/api/v1")
app.include_router(notification.router, prefix="/api/v1")
app.include_router(auditlog.router, prefix="/api/v1")
app.include_router(batchjob.router, prefix="/api/v1")
app.include_router(register_user.router, prefix="/api/v1")
app.include_router(login_user.router, prefix="/api/v1")
app.include_router(logout.router, prefix="/api/v1")
app.include_router(visualize.router, prefix="/api/v1")
app.include_router(upload_cfdi.router, prefix="/api/v1")
app.include_router(sospechoso_router.router, prefix="/api/v1")
app.include_router(routerCFDI.router, prefix="/api/v1")
app.include_router(operations_statics.router, prefix="/api/v1")

# Eventos de ciclo de vida
@app.on_event("startup")
async def startup():
    try:
        await db.connect()
        # await init_event_bus()  # Inicializar el event bus
        asyncio.create_task(start_login_consumer())
        logger.info("✅ Aplicación iniciada, Prisma y event bus conectados")
    except Exception as e:
        logger.error(f"❌ Error en startup: {str(e)}")
        raise e

@app.on_event("shutdown")
async def shutdown():
    try:
        await db.disconnect()
        # await close_event_bus()  # Cerrar el event bus
        logger.info("🔌 Aplicación cerrada, Prisma y event bus desconectados")
    except Exception as e:
        logger.error(f"❌ Error en shutdown: {str(e)}")
        raise e

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="debug",
        loop="asyncio"
    )