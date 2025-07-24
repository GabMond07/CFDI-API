from pydantic import BaseModel, validator, Field
from typing import Dict, List, Optional, Literal, Any
from datetime import datetime
from enum import Enum
import re 

class AnalysisLevel(str, Enum):
    """Niveles de análisis disponibles con diferentes recursos."""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class ScriptLanguage(str, Enum):
    """Lenguajes de script soportados."""
    PYTHON = "python"
    R = "r"
    SQL = "sql"

class OperationType(str, Enum):
    """Tipos de operación para combinación de filtros."""
    UNION = "union"
    INTERSECTION = "intersection"

class TableType(str, Enum):
    """Tipos de tabla disponibles para consultas."""
    CFDI = "cfdi"
    ISSUER = "issuer"
    RECEIVER = "receiver"
    CONCEPT = "concept"

class CFDIType(str, Enum):
    """Tipos de CFDI válidos."""
    INGRESO = "I"
    EGRESO = "E"
    TRASLADO = "T"
    NOMINA = "N"
    PAGO = "P"

class CFDIFilter(BaseModel):
    start_date: Optional[datetime] = Field(None, description="Fecha inicial de filtrado")
    end_date: Optional[datetime] = Field(None, description="Fecha final de filtrado")
    type: Optional[str] = Field(None, max_length=20, description="Tipo de CFDI")
    serie: Optional[str] = Field(None, max_length=25, description="Serie del CFDI")
    folio: Optional[str] = Field(None, max_length=25, description="Folio del CFDI")
    issuer_id: Optional[str] = Field(None, max_length=13, description="RFC del emisor")
    receiver_id: Optional[int] = Field(None, description="ID del receptor")
    currency: Optional[str] = Field(None, max_length=10, description="Moneda")
    payment_method: Optional[str] = Field(None, max_length=50, description="Método de pago")
    payment_form: Optional[str] = Field(None, max_length=50, description="Forma de pago")
    cfdi_use: Optional[str] = Field(None, max_length=50, description="Uso del CFDI")
    export_status: Optional[str] = Field(None, max_length=20, description="Estado de exportación")
    min_total: Optional[float] = Field(None, ge=0, description="Monto mínimo")
    max_total: Optional[float] = Field(None, ge=0, description="Monto máximo")
    status: Optional[str] = Field(None, max_length=20, description="Estado del CFDI")

    @validator('end_date')
    def validate_date_range(cls, v, values):
        if v and values.get('start_date') and v < values['start_date']:
            raise ValueError('end_date must be greater than or equal to start_date')
        return v
    
    @validator('max_total')
    def validate_total_range(cls, v, values):
        if v and values.get('min_total') and v < values['min_total']:
            raise ValueError('max_total must be greater than or equal to min_total')
        return v

class DataSource(BaseModel):
    table: TableType = Field(..., description="Tabla a consultar")
    filters: Optional[CFDIFilter] = Field(None, description="Filtros a aplicar")
    
    class Config:
        use_enum_values = True

class SetOperationRequest(BaseModel):
    operation: OperationType = Field(..., description="Tipo de operación de conjunto")
    sources: List[DataSource] = Field(..., min_items=1, max_items=10, description="Fuentes de datos")
    
    class Config:
        use_enum_values = True
    
    @validator('sources')
    def validate_sources(cls, v):
        if len(v) < 2 and any(source.table == TableType.CFDI for source in v):
            # Para operaciones de conjunto necesitamos al menos 2 fuentes
            pass  # Permitir 1 fuente para casos especiales
        return v
    
class CFDISort(BaseModel):
    field: Literal["issue_date", "total"] = "issue_date"
    direction: Literal["asc", "desc"] = "desc"

class CFDIResponse(BaseModel):
    id: int
    uuid: str
    version: str
    serie: Optional[str]
    folio: Optional[str]
    issue_date: datetime
    seal: Optional[str]
    certificate_number: Optional[str]
    certificate: Optional[str]
    place_of_issue: Optional[str]
    type: str
    total: float
    subtotal: float
    payment_method: Optional[str]
    payment_form: Optional[str]
    currency: Optional[str]
    user_id: str
    issuer_id: str
    issuer_name: Optional[str]
    cfdi_use: Optional[str]

class PaginatedCFDIResponse(BaseModel):
    items: List[CFDIResponse]
    total: int
    page: int
    page_size: int

class AggregationRequest(BaseModel):
    operation: Literal["sum", "count", "avg", "min", "max"]
    field: Literal["total", "subtotal"]
    filters: Optional[CFDIFilter] = None
    include_details: bool = False

class JoinRequest(BaseModel):
    sources: List[Literal["cfdi", "receiver", "issuer"]]
    join_type: Literal["inner", "left"] = "inner"
    on: Dict[str, str]
    filters: Optional[CFDIFilter] = None

class StatsRequest(BaseModel):
    field: Literal["total", "subtotal"]
    filters: Optional[CFDIFilter] = None

class AggregationResponse(BaseModel):
    result: Dict[str, float | int]
    details: Optional[List[Dict]] = None

class JoinResponse(BaseModel):
    items: List[Dict]

class CentralTendencyResponse(BaseModel):
    average: float
    median: float
    mode: float

class BasicStatsResponse(BaseModel):
    range: float
    variance: float
    standard_deviation: float
    coefficient_of_variation: float

class SetOperationResponse(BaseModel):
    items: List[Dict]

class ScriptRequest(BaseModel):
    """Solicitud de ejecución de script con validaciones mejoradas."""
    
    script: str = Field(
        ..., 
        min_length=1, 
        max_length=50000,
        description="Código del script a ejecutar"
    )
    language: ScriptLanguage = Field(
        ..., 
        description="Lenguaje del script"
    )
    analysis_level: AnalysisLevel = Field(
        AnalysisLevel.BASIC, 
        description="Nivel de análisis (determina recursos disponibles)"
    )
    filters: Optional[CFDIFilter] = Field(
        None, 
        description="Filtros para los datos CFDI"
    )
    timeout: Optional[int] = Field(
        None, 
        ge=10, 
        le=300, 
        description="Timeout personalizado en segundos (10-300)"
    )
    variables: Optional[Dict[str, Any]] = Field(
        None, 
        description="Variables adicionales para el script"
    )
    output_format: Optional[str] = Field(
        "json", 
        description="Formato de salida (json, csv, excel)"
    )
    
    @validator('script')
    def validate_script_content(cls, v, values):
        """Valida el contenido del script."""
        if not v.strip():
            raise ValueError('El script no puede estar vacío')
        
        language = values.get('language')
        
        if language == ScriptLanguage.PYTHON:
            cls._validate_python_script(v)
        elif language == ScriptLanguage.R:
            cls._validate_r_script(v)
        elif language == ScriptLanguage.SQL:
            cls._validate_sql_script(v)
        
        return v
    
    @staticmethod
    def _validate_python_script(script: str):
        """Valida script de Python."""
        prohibited_imports = [
            'os', 'sys', 'subprocess', 'socket', 'urllib', 'requests',
            'pickle', 'marshal', 'shelve', 'dbm', 'sqlite3', 'mysql',
            'psycopg2', 'pymongo', 'redis', 'paramiko', 'ftplib',
            'smtplib', 'imaplib', 'poplib', 'telnetlib', 'webbrowser'
        ]
        
        for imp in prohibited_imports:
            if re.search(rf'\bimport\s+{imp}\b', script, re.IGNORECASE):
                raise ValueError(f'Import prohibido: {imp}')
            if re.search(rf'\bfrom\s+{imp}\s+import\b', script, re.IGNORECASE):
                raise ValueError(f'Import prohibido: {imp}')
        
        prohibited_functions = [
            'eval', 'exec', 'compile', '__import__', 'globals', 'locals',
            'open', 'file', 'input', 'raw_input', 'reload', 'exit', 'quit'
        ]
        
        for func in prohibited_functions:
            if re.search(rf'\b{func}\s*\(', script, re.IGNORECASE):
                raise ValueError(f'Función prohibida: {func}')
    
    @staticmethod
    def _validate_r_script(script: str):
        """Valida script de R."""
        prohibited_functions = [
            'system', 'shell', 'download.file', 'url', 'file.choose',
            'source', 'eval', 'parse', 'quit', 'q', 'stop'
        ]
        
        for func in prohibited_functions:
            if re.search(rf'\b{func}\s*\(', script, re.IGNORECASE):
                raise ValueError(f'Función prohibida: {func}')
    
    @staticmethod
    def _validate_sql_script(script: str):
        """Valida script de SQL."""
        prohibited_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE',
            'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE'
        ]
        
        script_upper = script.upper()
        for keyword in prohibited_keywords:
            if keyword in script_upper:
                raise ValueError(f'Palabra clave prohibida: {keyword}')
    
    @validator('timeout')
    def validate_timeout_by_level(cls, v, values):
        """Valida timeout según el nivel de análisis."""
        level = values.get('analysis_level')
        max_timeouts = {
            AnalysisLevel.BASIC: 60,
            AnalysisLevel.INTERMEDIATE: 180,
            AnalysisLevel.ADVANCED: 300
        }
        
        if v and level and v > max_timeouts[level]:
            raise ValueError(f'Timeout máximo para {level.value}: {max_timeouts[level]}s')
        
        return v

class SQLScriptRequest(BaseModel):
    """Solicitud específica para consultas SQL."""
    
    query: str = Field(
        ..., 
        min_length=1, 
        max_length=10000,
        description="Consulta SQL a ejecutar"
    )
    filters: Optional[CFDIFilter] = Field(
        None, 
        description="Filtros adicionales para la consulta"
    )
    use_cache: bool = Field(
        True, 
        description="Usar cache para consultas repetidas"
    )
    explain: bool = Field(
        False, 
        description="Incluir plan de ejecución"
    )
    limit: Optional[int] = Field(
        None, 
        ge=1, 
        le=10000, 
        description="Límite de resultados"
    )
    
    @validator('query')
    def validate_sql_query(cls, v):
        """Valida la consulta SQL."""
        if not v.strip():
            raise ValueError('La consulta no puede estar vacía')
        
        if not v.strip().upper().startswith('SELECT'):
            raise ValueError('Solo se permiten consultas SELECT')
        
        prohibited = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
        query_upper = v.upper()
        
        for word in prohibited:
            if word in query_upper:
                raise ValueError(f'Palabra prohibida: {word}')
        
        return v

class ScriptResponse(BaseModel):
    """Respuesta estándar para ejecución de scripts."""
    
    success: bool = Field(description="Indica si la ejecución fue exitosa")
    result: Optional[Any] = Field(None, description="Resultado de la ejecución")
    error: Optional[str] = Field(None, description="Mensaje de error si aplica")
    execution_time: Optional[float] = Field(None, description="Tiempo de ejecución en segundos")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp de ejecución")
    cached: bool = Field(False, description="Indica si el resultado vino del cache")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadatos adicionales")

class ScriptExample(BaseModel):
    """Ejemplo de script con información descriptiva."""
    
    name: str = Field(description="Nombre del ejemplo")
    description: str = Field(description="Descripción del ejemplo")
    language: ScriptLanguage = Field(description="Lenguaje del script")
    code: str = Field(description="Código del ejemplo")
    level: AnalysisLevel = Field(description="Nivel de análisis requerido")
    tags: List[str] = Field(default_factory=list, description="Tags para categorización")
    expected_output: Optional[str] = Field(None, description="Salida esperada del ejemplo")

class ValidationError(BaseModel):
    """Error de validación detallado."""
    
    field: str = Field(description="Campo que causó el error")
    message: str = Field(description="Mensaje de error")
    code: str = Field(description="Código de error")
    context: Optional[Dict[str, Any]] = Field(None, description="Contexto adicional")