from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer
from .middleware import auth_middleware
from src.router import Consulta
from src.router import issuer
from src.router import receiver
from src.router import concept
from src.router import tax
from src.router import tax_summary
from src.router import payment
from src.router import cfdi_relation
from src.router import report
from src.router import notification
from src.router import auditlog
from src.router import batchjob
from src.router import register_user
from src.router import login_user
from src.router import logout
from src.router import visualize
from src.router import upload_cfdi
from src.ml.router import sospechoso_router
from src.router import operations_statics
import asyncio
from src.event_bus.consumers.login_consumer import start_login_consumer
from fastapi.middleware.cors import CORSMiddleware
from src.middleware import auth_middleware
from starlette.middleware.base import BaseHTTPMiddleware
from src.ml.router import routerCFDI
from src.database import db

app = FastAPI(title="Web API Fiscal", description="API para la gestión de CFDI y autenticación de contribuyentes.", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Luego agrega tu middleware personalizado
from .middleware import auth_middleware
app.middleware("http")(auth_middleware)

# OAuth2 para manejar el token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

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

app.include_router(routerCFDI.router, prefix="/api/v1")

app.include_router(visualize.router, prefix="/api/v1")

app.include_router(upload_cfdi.router, prefix="/api/v1")

app.include_router(sospechoso_router.router, prefix="/api/v1")

app.include_router(operations_statics.router, prefix="/api/v1")


@app.on_event("startup")
async def startup():
    await db.connect()
    asyncio.create_task(start_login_consumer())

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()  # Desconectar al cerrar la aplicación
