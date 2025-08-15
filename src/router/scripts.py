from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from src.service.script_service import ScriptService, ScriptExecutionError, SecurityError
from src.Models.operation.visualize_copy import ScriptRequest, SQLScriptRequest
from typing import Dict, Any
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

# Cache simple para consultas frecuentes
_query_cache = {}
_cache_timeout = 300  # 5 minutos

def get_script_service(request: Request) -> ScriptService:
    """Dependency para obtener el servicio de scripts."""
    user_rfc = request.state.user.get("sub")
    if not user_rfc:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    return ScriptService(user_rfc)

async def log_script_execution(user_rfc: str, script_type: str, success: bool, execution_time: float):
    """Log de ejecución en background."""
    try:
        logger.info(f"Script execution - User: {user_rfc}, Type: {script_type}, Success: {success}, Time: {execution_time:.2f}s")
    except Exception as e:
        logger.error(f"Error logging script execution: {str(e)}")

@router.post("/scripts/execute")
async def execute_script(
    request: Request,
    background_tasks: BackgroundTasks,
    script_request: ScriptRequest,
    service: ScriptService = Depends(get_script_service)
) -> JSONResponse:
    """
    Ejecuta scripts personalizados en Python, R o SQL.
    
    Args:
        script_request: Configuración del script a ejecutar
        
    Returns:
        JSONResponse con el resultado del script
        
    Raises:
        HTTPException: En caso de errores de validación o ejecución
    """
    start_time = datetime.now()
    user_rfc = request.state.user["sub"]
    
    try:
        # Validación básica
        if not script_request.script.strip():
            raise HTTPException(
                status_code=400, 
                detail="El script no puede estar vacío"
            )
            
        if len(script_request.script) > 50000:
            raise HTTPException(
                status_code=400,
                detail="El script excede el tamaño máximo permitido (50KB)"
            )
        
        logger.info(f"Executing {script_request.language} script for user {user_rfc}")
        
        # Ejecutar script
        result = await service.execute_script(script_request)
        
        # Calcular tiempo de ejecución
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Log en background
        background_tasks.add_task(
            log_script_execution, 
            user_rfc, 
            script_request.language, 
            True, 
            execution_time
        )
        
        return JSONResponse(
            content={
                "success": True,
                "result": result,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "cached": False,
                "metadata": {}
            },
            status_code=200
        )
        
    except SecurityError as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        background_tasks.add_task(
            log_script_execution, 
            user_rfc, 
            script_request.language, 
            False, 
            execution_time
        )
        
        logger.warning(f"Security error for user {user_rfc}: {str(e)}")
        raise HTTPException(
            status_code=403,
            detail=f"Error de seguridad: {str(e)}"
        )
        
    except ScriptExecutionError as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        background_tasks.add_task(
            log_script_execution, 
            user_rfc, 
            script_request.language, 
            False, 
            execution_time
        )
        
        logger.error(f"Script execution error for user {user_rfc}: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail=f"Error de ejecución: {str(e)}"
        )
        
    except asyncio.TimeoutError:
        execution_time = (datetime.now() - start_time).total_seconds()
        background_tasks.add_task(
            log_script_execution, 
            user_rfc, 
            script_request.language, 
            False, 
            execution_time
        )
        
        logger.error(f"Script timeout for user {user_rfc}")
        raise HTTPException(
            status_code=408,
            detail="El script excedió el tiempo límite de ejecución"
        )
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        background_tasks.add_task(
            log_script_execution, 
            user_rfc, 
            script_request.language, 
            False, 
            execution_time
        )
        
        logger.error(f"Unexpected error for user {user_rfc}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )

@router.post("/scripts/sql")
async def execute_sql(
    request: Request,
    background_tasks: BackgroundTasks,
    sql_request: SQLScriptRequest,
    service: ScriptService = Depends(get_script_service)
) -> JSONResponse:
    """
    Ejecuta consultas SQL predefinidas o personalizadas sobre CFDI.
    
    Args:
        sql_request: Configuración de la consulta SQL
        
    Returns:
        JSONResponse con el resultado de la consulta
        
    Raises:
        HTTPException: En caso de errores de validación o ejecución
    """
    start_time = datetime.now()
    user_rfc = request.state.user["sub"]
    
    try:
        # Validación básica
        if not sql_request.query.strip():
            raise HTTPException(
                status_code=400,
                detail="La consulta SQL no puede estar vacía"
            )
            
        if len(sql_request.query) > 10000:
            raise HTTPException(
                status_code=400,
                detail="La consulta SQL excede el tamaño máximo permitido (10KB)"
            )
        
        # Generar cache key
        cache_key = f"{user_rfc}:{hash(sql_request.query + str(sql_request.filters))}"
        
        # Verificar cache
        if sql_request.use_cache and cache_key in _query_cache:
            cached_result, cache_time = _query_cache[cache_key]
            if (datetime.now() - cache_time).total_seconds() < _cache_timeout:
                logger.info(f"Returning cached SQL result for user {user_rfc}")
                return JSONResponse(
                    content={
                        "success": True,
                        "result": cached_result,
                        "execution_time": 0.0,
                        "timestamp": datetime.now().isoformat(),
                        "cached": True,
                        "metadata": {}
                    },
                    status_code=200
                )
        
        logger.info(f"Executing SQL query for user {user_rfc}")
        
        # Ejecutar consulta
        result = await service.execute_sql(sql_request.query, sql_request.filters)
        
        # Guardar en cache
        if sql_request.use_cache:
            _query_cache[cache_key] = (result, datetime.now())
        
        # Limpiar cache si es muy grande
        if len(_query_cache) > 100:
            oldest_key = min(_query_cache.keys(), key=lambda k: _query_cache[k][1])
            del _query_cache[oldest_key]
        
        # Calcular tiempo de ejecución
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Log en background
        background_tasks.add_task(
            log_script_execution, 
            user_rfc, 
            "sql", 
            True, 
            execution_time
        )
        
        # Incluir plan de ejecución si se solicita
        metadata = {}
        if sql_request.explain:
            # Nota: Esto requiere implementación adicional en ScriptService
            metadata["explain"] = await service.get_explain_plan(sql_request.query, sql_request.filters)
        
        return JSONResponse(
            content={
                "success": True,
                "result": result,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "cached": False,
                "metadata": metadata
            },
            status_code=200
        )
        
    except SecurityError as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        background_tasks.add_task(
            log_script_execution, 
            user_rfc, 
            "sql", 
            False, 
            execution_time
        )
        
        logger.warning(f"SQL security error for user {user_rfc}: {str(e)}")
        raise HTTPException(
            status_code=403,
            detail=f"Error de seguridad: {str(e)}"
        )
        
    except ScriptExecutionError as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        background_tasks.add_task(
            log_script_execution, 
            user_rfc, 
            "sql", 
            False, 
            execution_time
        )
        
        logger.error(f"SQL execution error for user {user_rfc}: {str(e)}")
        raise HTTPException(
            status_code=422,
            detail=f"Error de ejecución: {str(e)}"
        )
        
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        background_tasks.add_task(
            log_script_execution, 
            user_rfc, 
            "sql", 
            False, 
            execution_time
        )
        
        logger.error(f"Unexpected SQL error for user {user_rfc}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )

@router.get("/scripts/queries/predefined")
async def get_predefined_queries(
    request: Request,
    service: ScriptService = Depends(get_script_service)
) -> JSONResponse:
    """
    Obtiene la lista de consultas SQL predefinidas disponibles.
    
    Returns:
        JSONResponse con la lista de consultas predefinidas
    """
    try:
        predefined_queries = {
            "average_by_type": {
                "name": "Promedio por tipo",
                "description": "Calcula el promedio de totales por tipo de CFDI",
                "parameters": ["type"],
                "example": "Promedio de ingresos"
            },
            "sum_by_type": {
                "name": "Suma por tipo",
                "description": "Calcula la suma total por tipo de CFDI",
                "parameters": ["type"],
                "example": "Total de ingresos"
            },
            "count_by_type": {
                "name": "Conteo por tipo",
                "description": "Cuenta la cantidad de CFDIs por tipo",
                "parameters": ["type"],
                "example": "Cantidad de facturas de ingreso"
            },
            "total_by_issuer": {
                "name": "Total por emisor",
                "description": "Agrupa totales por emisor",
                "parameters": [],
                "example": "Ingresos por cada emisor"
            },
            "total_by_currency": {
                "name": "Total por moneda",
                "description": "Agrupa totales por moneda",
                "parameters": [],
                "example": "Ingresos en MXN vs USD"
            },
            "count_by_payment_method": {
                "name": "Conteo por método de pago",
                "description": "Cuenta CFDIs por método de pago",
                "parameters": [],
                "example": "Distribución de métodos de pago"
            },
            "count_by_cfdi_use": {
                "name": "Conteo por uso de CFDI",
                "description": "Cuenta CFDIs por uso",
                "parameters": [],
                "example": "Distribución de usos de CFDI"
            },
            "top_10_by_total": {
                "name": "Top 10 por total",
                "description": "Los 10 CFDIs con mayor total",
                "parameters": ["type"],
                "example": "Las 10 facturas más altas"
            },
            "avg_by_date": {
                "name": "Promedio por fecha",
                "description": "Promedio de totales agrupado por fecha",
                "parameters": [],
                "example": "Evolución diaria del promedio"
            },
            "min_total_by_type": {
                "name": "Mínimo por tipo",
                "description": "Valor mínimo por tipo de CFDI",
                "parameters": ["type"],
                "example": "Factura más pequeña"
            },
            "max_total_by_type": {
                "name": "Máximo por tipo",
                "description": "Valor máximo por tipo de CFDI",
                "parameters": ["type"],
                "example": "Factura más grande"
            }
        }
        
        return JSONResponse(
            content={
                "success": True,
                "queries": predefined_queries,
                "timestamp": datetime.now().isoformat()
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Error getting predefined queries: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )

@router.get("/scripts/examples")
async def get_script_examples(
    request: Request,
    language: str = "python"
) -> JSONResponse:
    """
    Obtiene ejemplos de scripts para diferentes lenguajes.
    
    Args:
        language: Lenguaje del script (python, r, sql)
        
    Returns:
        JSONResponse con ejemplos de scripts
    """
    try:
        examples = {
            "python": {
                "basic_stats": {
                    "name": "Estadísticas básicas",
                    "description": "Calcula estadísticas descriptivas de los totales",
                    "code": """# Estadísticas básicas de los totales
import pandas as pd
import numpy as np

# Calcular estadísticas descriptivas
stats = data['total'].describe()
result = {
    'count': int(stats['count']),
    'mean': float(stats['mean']),
    'std': float(stats['std']),
    'min': float(stats['min']),
    'max': float(stats['max']),
    'median': float(data['total'].median())
}"""
                },
                "monthly_analysis": {
                    "name": "Análisis mensual",
                    "description": "Agrupa datos por mes y calcula totales",
                    "code": """# Análisis mensual de ingresos
import pandas as pd
from datetime import datetime

# Convertir fechas y agrupar por mes
data['issue_date'] = pd.to_datetime(data['issue_date'])
data['month'] = data['issue_date'].dt.to_period('M')

# Agrupar por mes
monthly_data = data.groupby('month').agg({
    'total': ['sum', 'count', 'mean']
}).round(2)

result = monthly_data.to_dict('index')"""
                },
                "top_issuers": {
                    "name": "Top emisores",
                    "description": "Encuentra los emisores con mayores totales",
                    "code": """# Top 10 emisores por volumen
import pandas as pd

# Agrupar por emisor
issuer_stats = data.groupby(['issuer_id', 'issuer_name']).agg({
    'total': ['sum', 'count', 'mean']
}).round(2)

# Ordenar por total y tomar top 10
issuer_stats.columns = ['total_sum', 'total_count', 'total_mean']
top_issuers = issuer_stats.sort_values('total_sum', ascending=False).head(10)

result = top_issuers.to_dict('index')"""
                },
                "currency_analysis": {
                    "name": "Análisis de monedas",
                    "description": "Analiza la distribución por monedas",
                    "code": """# Análisis por moneda
import pandas as pd

# Agrupar por moneda
currency_stats = data.groupby('currency').agg({
    'total': ['sum', 'count', 'mean'],
    'uuid': 'nunique'
}).round(2)

currency_stats.columns = ['total_sum', 'total_count', 'total_mean', 'unique_cfdis']

# Calcular porcentajes
currency_stats['percentage'] = (currency_stats['total_sum'] / currency_stats['total_sum'].sum() * 100).round(2)

result = currency_stats.to_dict('index')"""
                }
            },
            "r": {
                "basic_stats": {
                    "name": "Estadísticas básicas",
                    "description": "Calcula estadísticas descriptivas con R",
                    "code": """# Estadísticas básicas con R
library(dplyr)

# Convertir a data frame
df <- data.frame(data)

# Calcular estadísticas
stats <- df %>%
  summarise(
    count = n(),
    mean = mean(total, na.rm = TRUE),
    median = median(total, na.rm = TRUE),
    sd = sd(total, na.rm = TRUE),
    min = min(total, na.rm = TRUE),
    max = max(total, na.rm = TRUE)
  )

result <- stats"""
                },
                "monthly_trend": {
                    "name": "Tendencia mensual",
                    "description": "Análisis de tendencia mensual",
                    "code": """# Tendencia mensual
library(dplyr)
library(lubridate)

# Convertir fechas
df <- data.frame(data)
df$issue_date <- as.Date(df$issue_date)
df$month <- floor_date(df$issue_date, "month")

# Agrupar por mes
monthly_trend <- df %>%
  group_by(month) %>%
  summarise(
    total_amount = sum(total, na.rm = TRUE),
    count = n(),
    avg_amount = mean(total, na.rm = TRUE)
  ) %>%
  arrange(month)

result <- monthly_trend"""
                },
                "correlation_analysis": {
                    "name": "Análisis de correlación",
                    "description": "Correlación entre variables numéricas",
                    "code": """# Análisis de correlación
library(dplyr)

# Seleccionar variables numéricas
df <- data.frame(data)
numeric_vars <- df %>%
  select_if(is.numeric) %>%
  select(total, subtotal)

# Calcular correlación
correlation_matrix <- cor(numeric_vars, use = "complete.obs")

result <- list(
  correlation_matrix = correlation_matrix,
  summary = summary(numeric_vars)
)"""
                }
            },
            "sql": {
                "basic_aggregation": {
                    "name": "Agregación básica",
                    "description": "Consulta SQL básica de agregación",
                    "code": """SELECT 
    type,
    COUNT(*) as count,
    SUM(total) as total_sum,
    AVG(total) as total_avg,
    MIN(total) as total_min,
    MAX(total) as total_max
FROM cfdi 
WHERE user_id = :user_rfc
GROUP BY type
ORDER BY total_sum DESC"""
                },
                "monthly_report": {
                    "name": "Reporte mensual",
                    "description": "Reporte agrupado por mes",
                    "code": """SELECT 
    DATE_FORMAT(issue_date, '%Y-%m') as month,
    COUNT(*) as cfdi_count,
    SUM(total) as monthly_total,
    AVG(total) as monthly_avg
FROM cfdi 
WHERE user_id = :user_rfc
GROUP BY DATE_FORMAT(issue_date, '%Y-%m')
ORDER BY month DESC"""
                },
                "top_transactions": {
                    "name": "Top transacciones",
                    "description": "Las transacciones más grandes",
                    "code": """SELECT 
    uuid,
    serie,
    folio,
    total,
    issue_date,
    issuer_id
FROM cfdi 
WHERE user_id = :user_rfc
ORDER BY total DESC
LIMIT 20"""
                }
            }
        }
        
        if language not in examples:
            raise HTTPException(
                status_code=400,
                detail=f"Lenguaje no soportado: {language}"
            )
        
        return JSONResponse(
            content={
                "success": True,
                "language": language,
                "examples": examples[language],
                "timestamp": datetime.now().isoformat()
            },
            status_code=200
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting script examples: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )

@router.get("/scripts/status")
async def get_script_status(
    request: Request,
    service: ScriptService = Depends(get_script_service)
) -> JSONResponse:
    """
    Obtiene el estado del servicio de scripts y recursos disponibles.
    
    Returns:
        JSONResponse con el estado del servicio
    """
    try:
        user_rfc = request.state.user["sub"]
        
        # Verificar estado de Docker
        docker_status = "healthy"
        try:
            service.docker_client.ping()
        except Exception:
            docker_status = "unhealthy"
        
        # Información del cache
        cache_info = {
            "cached_queries": len(_query_cache),
            "cache_timeout": _cache_timeout
        }
        
        # Límites de recursos
        resource_limits = {
            "basic": {"cpu": "0.5", "memory": "256m", "timeout": 30},
            "intermediate": {"cpu": "1", "memory": "512m", "timeout": 60},
            "advanced": {"cpu": "2", "memory": "1g", "timeout": 120}
        }
        
        return JSONResponse(
            content={
                "success": True,
                "status": {
                    "docker": docker_status,
                    "cache": cache_info,
                    "resource_limits": resource_limits,
                    "supported_languages": ["python", "r", "sql"],
                    "user_rfc": user_rfc
                },
                "timestamp": datetime.now().isoformat()
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Error getting script status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )

@router.delete("/scripts/cache")
async def clear_cache(
    request: Request,
    service: ScriptService = Depends(get_script_service)
) -> JSONResponse:
    """
    Limpia el cache de consultas SQL.
    
    Returns:
        JSONResponse confirmando la limpieza del cache
    """
    try:
        user_rfc = request.state.user["sub"]
        
        # Limpiar cache del usuario
        user_keys = [key for key in _query_cache.keys() if key.startswith(f"{user_rfc}:")]
        for key in user_keys:
            del _query_cache[key]
        
        logger.info(f"Cache cleared for user {user_rfc}, removed {len(user_keys)} entries")
        
        return JSONResponse(
            content={
                "success": True,
                "message": f"Cache limpiado exitosamente. Se eliminaron {len(user_keys)} entradas.",
                "timestamp": datetime.now().isoformat()
            },
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )