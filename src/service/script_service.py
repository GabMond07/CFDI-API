from src.database import db
from src.Models.operation.visualize_copy import CFDIFilter, ScriptRequest, AnalysisLevel
from typing import Dict, Optional, List, Any
import docker
import sqlparse
import pandas as pd
import json
import logging
import tempfile
import os
import asyncio
from datetime import datetime
import re
import shutil

logger = logging.getLogger(__name__)

class ScriptExecutionError(Exception):
    """Excepción personalizada para errores de ejecución de scripts."""
    pass

class SecurityError(Exception):
    """Excepción para errores de seguridad."""
    pass

class ScriptService:
    def __init__(self, user_rfc: str):
        self.user_rfc = user_rfc
        self.docker_client = docker.from_env()
        
        # Consultas SQL predefinidas y seguras con marcadores posicionales
        self.allowed_queries = {
            "average_by_type": "SELECT AVG(total) AS average FROM cfdi WHERE type = $1 AND user_id = $2",
            "sum_by_type": "SELECT SUM(total) AS total FROM cfdi WHERE type = $1 AND user_id = $2",
            "count_by_type": "SELECT COUNT(*) AS count FROM cfdi WHERE type = $1 AND user_id = $2",
            "min_total_by_type": "SELECT MIN(total) AS min_total FROM cfdi WHERE type = $1 AND user_id = $2",
            "max_total_by_type": "SELECT MAX(total) AS max_total FROM cfdi WHERE type = $1 AND user_id = $2",
            "top_10_by_total": "SELECT uuid, total FROM cfdi WHERE type = $1 AND user_id = $2 ORDER BY total DESC LIMIT 10",
            "total_by_issuer": "SELECT issuer_id, SUM(total) AS total_by_issuer FROM cfdi WHERE user_id = $1 GROUP BY issuer_id",
            "avg_by_date": "SELECT DATE(issue_date) AS date, AVG(total) AS avg_total FROM cfdi WHERE user_id = $1 GROUP BY DATE(issue_date)",
            "total_by_currency": "SELECT currency, SUM(total) AS total_by_currency FROM cfdi WHERE user_id = $1 GROUP BY currency",
            "count_by_payment_method": "SELECT payment_method, COUNT(*) AS count_by_method FROM cfdi WHERE user_id = $1 GROUP BY payment_method",
            "count_by_cfdi_use": "SELECT cfdi_use, COUNT(*) AS count_by_use FROM cfdi WHERE user_id = $1 GROUP BY cfdi_use"
        }

    def _build_where_conditions(self, filters: Optional[CFDIFilter]) -> Dict[str, Any]:
        """Construye condiciones de filtrado para consultas Prisma."""
        where_conditions = {"user_id": self.user_rfc}
        
        if not filters:
            return where_conditions
            
        # Filtros de fecha
        if filters.start_date or filters.end_date:
            date_filter = {}
            if filters.start_date:
                date_filter["gte"] = filters.start_date
            if filters.end_date:
                date_filter["lte"] = filters.end_date
            where_conditions["issue_date"] = date_filter
            
        # Filtros de monto
        if filters.min_total is not None or filters.max_total is not None:
            total_filter = {}
            if filters.min_total is not None:
                total_filter["gte"] = filters.min_total
            if filters.max_total is not None:
                total_filter["lte"] = filters.max_total
            where_conditions["total"] = total_filter
        
        # Filtros de texto exacto
        text_filters = [
            'type', 'serie', 'folio', 'issuer_id', 'currency', 
            'payment_method', 'payment_form', 'cfdi_use', 'export_status', 'status'
        ]
        
        for field in text_filters:
            value = getattr(filters, field, None)
            if value:
                where_conditions[field] = value
                
        # Filtro numérico
        if filters.receiver_id:
            where_conditions["receiver_id"] = filters.receiver_id
            
        return where_conditions

    async def _fetch_cfdi_data(self, filters: Optional[CFDIFilter]) -> List[Dict[str, Any]]:
        """Obtiene datos CFDI filtrados con manejo de errores mejorado."""
        try:
            where_conditions = self._build_where_conditions(filters)
            
            cfdis = await db.cfdi.find_many(
                where=where_conditions,
                include={"issuer": True, "receiver": True}
            )
            
            # Aplanar los datos para evitar estructuras anidadas
            return [
                {
                    "uuid": cfdi.uuid,
                    "total": float(cfdi.total) if cfdi.total else 0.0,
                    "subtotal": float(cfdi.subtotal) if cfdi.subtotal else 0.0,
                    "issue_date": cfdi.issue_date.isoformat() if cfdi.issue_date else None,
                    "type": cfdi.type,
                    "serie": cfdi.serie,
                    "folio": cfdi.folio,
                    "issuer_id": cfdi.issuer_id,
                    "issuer_name": cfdi.issuer.name_issuer if cfdi.issuer and hasattr(cfdi.issuer, 'name_issuer') else None,
                    "receiver_id": cfdi.receiver_id,
                    "receiver_name": cfdi.receiver.name_receiver if cfdi.receiver and hasattr(cfdi.receiver, 'name_receiver') else None,
                    "currency": cfdi.currency,
                    "payment_method": cfdi.payment_method,
                    "payment_form": cfdi.payment_form,
                    "cfdi_use": cfdi.cfdi_use,
                    "export_status": cfdi.export_status,
                }
                for cfdi in cfdis
            ]
            
        except Exception as e:
            logger.error(f"Error fetching CFDI data: {str(e)}")
            raise ScriptExecutionError(f"Error al obtener datos CFDI: {str(e)}")

    def _validate_sql_query(self, query: str) -> bool:
        """Valida que la consulta SQL sea segura."""
        try:
            query = query.strip().upper()
            prohibited_words = [
                'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 
                'TRUNCATE', 'EXEC', 'EXECUTE', 'GRANT', 'REVOKE', 'MERGE',
                'CALL', 'REPLACE', 'LOAD', 'OUTFILE', 'INFILE', 'BACKUP',
                'RESTORE', 'SHUTDOWN', 'KILL', 'SLEEP', 'WAITFOR'
            ]
            
            for word in prohibited_words:
                if word in query:
                    return False
            
            parsed = sqlparse.parse(query)
            if not parsed:
                return False
                
            for statement in parsed:
                if statement.get_type().upper() != "SELECT":
                    return False
                    
                allowed_tables = ['cfdi', 'issuer', 'receiver', 'concept']
                common_columns = [
                    'uuid', 'total', 'subtotal', 'issue_date', 'type', 'serie', 'folio', 
                    'issuer_id', 'receiver_id', 'currency', 'payment_method', 'payment_form', 
                    'cfdi_use', 'export_status', 'status', 'name_issuer', 'name_receiver'
                ]
                
                for token in statement.tokens:
                    if isinstance(token, sqlparse.sql.Identifier) and token.get_name().lower() not in allowed_tables:
                        if token.get_name().lower() not in common_columns:
                            if not (len(token.get_name()) <= 10 and token.get_name().isidentifier()):
                                return False
                                
            return True
            
        except Exception as e:
            logger.error(f"Error validating SQL query: {str(e)}")
            return False

    async def execute_sql(self, query: str, filters: Optional[CFDIFilter] = None) -> List[Dict[str, Any]]:
        """Ejecuta consultas SQL predefinidas o validadas."""
        try:
            if query in self.allowed_queries:
                sql_query = self.allowed_queries[query]
                params = [filters.type, self.user_rfc] if filters and filters.type else [self.user_rfc]
            else:
                def relaxed_validate(query):
                    query_up = query.strip().upper()
                    prohibited_words = [
                        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 
                        'TRUNCATE', 'EXEC', 'EXECUTE', 'GRANT', 'REVOKE', 'MERGE',
                        'CALL', 'REPLACE', 'LOAD', 'OUTFILE', 'INFILE', 'BACKUP',
                        'RESTORE', 'SHUTDOWN', 'KILL', 'SLEEP', 'WAITFOR'
                    ]
                    for word in prohibited_words:
                        if word in query_up:
                            return False
                    parsed = sqlparse.parse(query)
                    if not parsed:
                        return False
                    for statement in parsed:
                        if statement.get_type().upper() != "SELECT":
                            return False
                        allowed_tables = ['cfdi', 'issuer', 'receiver', 'concept']
                        allowed_functions = [
                            'AVG', 'SUM', 'COUNT', 'MIN', 'MAX', 'AS', 'ON', 'WHERE', 'GROUP', 
                            'ORDER', 'HAVING', 'LIMIT', 'DISTINCT', 'COALESCE', 'CASE', 'WHEN', 
                            'THEN', 'ELSE', 'END'
                        ]
                        common_columns = [
                            'uuid', 'total', 'subtotal', 'issue_date', 'type', 'serie', 'folio', 
                            'issuer_id', 'receiver_id', 'currency', 'payment_method', 'payment_form', 
                            'cfdi_use', 'export_status', 'status', 'name_issuer', 'name_receiver'
                        ]
                        for token in statement.tokens:
                            if isinstance(token, sqlparse.sql.Identifier) and token.get_name().lower() not in allowed_tables:
                                val = token.get_name().lower()
                                if val not in [s.lower() for s in allowed_functions] and val not in common_columns:
                                    if not (len(val) <= 10 and val.isidentifier()):
                                        return False
                    return True
                
                if not relaxed_validate(query):
                    raise SecurityError("Consulta SQL no permitida o insegura. Revisa sintaxis, tablas y columnas.")
                
                # Reemplazar :user_rfc por $1 y manejar otros parámetros
                sql_query = query.replace(":user_rfc", "$1")
                params = [self.user_rfc]

            # Log para depuración
            logger.debug(f"Executing SQL query: {sql_query} with params: {params}")
            
            result = await db.query_raw(sql_query, *params)
            if isinstance(result, List):
                for row in result:
                    if isinstance(row, Dict):
                        for key, value in row.items():
                            if hasattr(value, '__float__'):
                                row[key] = float(value)
            return result
            
        except SecurityError as se:
            logger.error(f"Error de seguridad en SQL: {str(se)}")
            raise ScriptExecutionError(f"Error de seguridad: {str(se)}")
        except Exception as e:
            logger.error(f"Error executing SQL query: {str(e)}")
            raise ScriptExecutionError(f"Error ejecutando consulta SQL: {str(e)}")

    async def execute_script(self, request: ScriptRequest) -> Dict[str, Any]:
        """Ejecuta scripts personalizados con manejo mejorado de errores y recursos."""
        try:
            data = await self._fetch_cfdi_data(request.filters)
            
            if not data:
                return {"result": "No se encontraron datos para los filtros especificados"}
            
            resource_limits = {
                AnalysisLevel.BASIC: {"cpu": "0.5", "memory": "256m", "timeout": 30},
                AnalysisLevel.INTERMEDIATE: {"cpu": "1", "memory": "512m", "timeout": 60},
                AnalysisLevel.ADVANCED: {"cpu": "2", "memory": "1g", "timeout": 120}
            }
            limits = resource_limits[request.analysis_level]

            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(data, temp_file, default=str, ensure_ascii=False, indent=2)
                temp_file_path = temp_file.name

            script_file_path = None
            
            try:
                if request.language == "sql":
                    return {"result": await self.execute_sql(request.script, request.filters)}
                
                elif request.language == "python":
                    return await self._execute_python_script(request.script, temp_file_path, limits)
                
                elif request.language == "r":
                    return await self._execute_r_script(request.script, temp_file_path, limits)
                
                else:
                    raise ValueError(f"Lenguaje no soportado: {request.language}")
                    
            finally:
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                if script_file_path and os.path.exists(script_file_path):
                    os.unlink(script_file_path)
                    
        except Exception as e:
            logger.error(f"Error executing script: {str(e)}")
            raise ScriptExecutionError(f"Error ejecutando script: {str(e)}")

    async def _execute_python_script(self, script: str, data_file_path: str, limits: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta script de Python en contenedor Docker."""
        if not self._validate_python_script(script):
            raise SecurityError("Script de Python contiene código no permitido")
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as script_file:
            script_content = f"""
import pandas as pd
import numpy as np
import scipy.stats as stats
import json
import sys
import traceback

try:
    data = pd.read_json('{data_file_path}')
    {self._indent_script(script)}
    result = locals().get('result', 'Script ejecutado exitosamente')
    print(json.dumps({{"success": True, "result": result}}, default=str, ensure_ascii=False))
except Exception as e:
    error_info = {{
        "success": False,
        "error": str(e),
        "traceback": traceback.format_exc()
    }}
    print(json.dumps(error_info, default=str, ensure_ascii=False))
"""
            script_file.write(script_content)
            script_file_path = script_file.name

        return await self._run_docker_container(
            image="cfdi-python",
            command=f"python {script_file_path}",
            data_file_path=data_file_path,
            limits=limits
        )

    async def _execute_r_script(self, script: str, data_file_path: str, limits: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta script de R en contenedor Docker."""
        with tempfile.TemporaryDirectory() as temp_dir:
            data_file_name = os.path.basename(data_file_path)
            temp_data_file_path = os.path.join(temp_dir, data_file_name)
            if os.path.dirname(data_file_path) != temp_dir:
                shutil.copy(data_file_path, temp_data_file_path)
            
            script_file_name = 'script.R'
            script_file_path = os.path.join(temp_dir, script_file_name)
            
            with open(script_file_path, 'w', encoding='utf-8') as script_file:
                script_content = f"""
library(jsonlite)
library(dplyr)

tryCatch({{
    json_data <- read_json('/app/{data_file_name}', simplifyDataFrame = TRUE)
    data <- as.data.frame(json_data)
    str_data <- capture.output(str(data))
    cat("Data structure:\\n", str_data, "\\n\\n")
    {self._indent_script(script)}
    result <- if (exists('result')) result else 'Script ejecutado exitosamente'
    cat(toJSON(list(success=TRUE, result=result), auto_unbox=TRUE, pretty=TRUE))
}}, error = function(e) {{
    error_info <- list(
        success = FALSE,
        error = as.character(e),
        traceback = capture.output(traceback())
    )
    cat(toJSON(error_info, auto_unbox=TRUE, pretty=TRUE))
}})
"""
                script_file.write(script_content)
            
            return await self._run_docker_container(
                image="cfdi-r",
                command=f"Rscript /app/{script_file_name}",
                data_file_path=temp_data_file_path,
                limits=limits
            )

    async def _run_docker_container(self, image: str, command: str, data_file_path: str, limits: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta contenedor Docker con manejo de errores mejorado."""
        try:
            container = self.docker_client.containers.run(
                image=image,
                command=command,
                volumes={os.path.dirname(data_file_path): {'bind': '/app', 'mode': 'ro'}},
                mem_limit=limits["memory"],
                cpu_quota=int(float(limits["cpu"]) * 100000),
                cpu_period=100000,
                remove=True,
                detach=True,
                network_mode="none"
            )
            
            try:
                result = await container.wait(timeout=limits["timeout"])
                output = container.logs().decode('utf-8')
                
                if result['StatusCode'] != 0:
                    raise ScriptExecutionError(f"Script falló con código {result['StatusCode']}: {output}")
                
                try:
                    parsed_output = json.loads(output)
                    if isinstance(parsed_output, dict) and not parsed_output.get("success", True):
                        raise ScriptExecutionError(parsed_output.get("error", "Error desconocido"))
                    return parsed_output
                except json.JSONDecodeError:
                    return {"result": output.strip()}
                    
            except asyncio.TimeoutError:
                container.kill()
                raise ScriptExecutionError(f"Script excedió el tiempo límite de {limits['timeout']} segundos")
                
        except docker.errors.DockerException as e:
            logger.error(f"Error Docker: {str(e)}")
            raise ScriptExecutionError(f"Error de ejecución en contenedor: {str(e)}")

    def _validate_python_script(self, script: str) -> bool:
        """Valida que el script de Python sea seguro."""
        prohibited_patterns = [
            r'import\s+os',
            r'import\s+sys',
            r'import\s+subprocess',
            r'import\s+socket',
            r'import\s+urllib',
            r'import\s+requests',
            r'import\s+pickle',
            r'__import__',
            r'eval\s*\(',
            r'exec\s*\(',
            r'open\s*\(',
            r'file\s*\(',
            r'input\s*\(',
            r'raw_input\s*\('
        ]
        
        for pattern in prohibited_patterns:
            if re.search(pattern, script, re.IGNORECASE):
                return False
                
        return True

    def _indent_script(self, script: str) -> str:
        """Indenta el script del usuario para insertar en el template."""
        return '\n'.join(f'    {line}' for line in script.split('\n'))

    async def get_explain_plan(self, query: str, filters: Optional[CFDIFilter]) -> List[Dict[str, Any]]:
        """Obtiene el plan de ejecución para una consulta SQL."""
        try:
            if query in self.allowed_queries:
                sql_query = f"EXPLAIN {self.allowed_queries[query]}"
                params = [filters.type, self.user_rfc] if filters and filters.type else [self.user_rfc]
            else:
                if not self._validate_sql_query(query):
                    raise SecurityError("Consulta SQL no permitida para EXPLAIN")
                sql_query = f"EXPLAIN {query.replace(':user_rfc', '$1')}"
                params = [self.user_rfc]
            
            logger.debug(f"Executing EXPLAIN query: {sql_query} with params: {params}")
            result = await db.query_raw(sql_query, *params)
            return result
        except Exception as e:
            logger.error(f"Error getting explain plan: {str(e)}")
            raise ScriptExecutionError(f"Error obteniendo plan de ejecución: {str(e)}")
