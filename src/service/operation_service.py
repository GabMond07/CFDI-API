from src.database import db
from typing import Dict, List, Optional
from datetime import datetime
import logging
from src.Models.visualize import CFDIFilter, SetOperationRequest, OperationType, TableType

logger = logging.getLogger(__name__)

class SetOperationService:
    def __init__(self, user_rfc: str):
        self.user_rfc = user_rfc
    
    def _build_where_conditions(self, filters: Optional[CFDIFilter]) -> Dict:
        """Construye condiciones de filtrado para consultas Prisma basadas en el modelo CFDI."""
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
        
        # Filtros de campos exactos
        exact_filters = {
            "type": filters.type,
            "serie": filters.serie,
            "folio": filters.folio,
            "issuer_id": filters.issuer_id,
            "receiver_id": filters.receiver_id,
            "currency": filters.currency,
            "payment_method": filters.payment_method,
            "payment_form": filters.payment_form,
            "cfdi_use": filters.cfdi_use,
            "export_status": filters.export_status
        }
        
        for field, value in exact_filters.items():
            if value is not None:
                where_conditions[field] = value
        
        # Filtros de rango de montos
        if filters.min_total or filters.max_total:
            total_filter = {}
            if filters.min_total:
                total_filter["gte"] = filters.min_total
            if filters.max_total:
                total_filter["lte"] = filters.max_total
            where_conditions["total"] = total_filter
        
        return where_conditions
    
    async def _fetch_cfdi_data(self, filters: Optional[CFDIFilter]) -> List[Dict]:
        """Obtiene datos de CFDI basados en filtros con relaciones incluidas."""
        where_conditions = self._build_where_conditions(filters)
        
        try:
            cfdis = await db.cfdi.find_many(
                where=where_conditions,
                include={
                    "issuer": True,
                    "receiver": True,
                    "concepts": True
                }
            )
            
            # Ordenar los resultados en Python si es necesario
            sorted_cfdis = sorted(cfdis, key=lambda x: x.issue_date, reverse=True)
            
            return [
                {
                    "id": cfdi.id,
                    "uuid": cfdi.uuid,
                    "version": cfdi.version,
                    "serie": cfdi.serie,
                    "folio": cfdi.folio,
                    "issue_date": cfdi.issue_date.isoformat() if cfdi.issue_date else None,
                    "type": cfdi.type,
                    "total": float(cfdi.total) if cfdi.total else 0.0,
                    "subtotal": float(cfdi.subtotal) if cfdi.subtotal else 0.0,
                    "currency": cfdi.currency,
                    "payment_method": cfdi.payment_method,
                    "payment_form": cfdi.payment_form,
                    "cfdi_use": cfdi.cfdi_use,
                    "export_status": cfdi.export_status,
                    "place_of_issue": cfdi.place_of_issue,
                    "issuer": {
                        "rfc": cfdi.issuer.rfc_issuer,
                        "name": cfdi.issuer.name_issuer
                    } if cfdi.issuer else None,
                    "receiver": {
                        "id": cfdi.receiver.id,
                        "name": getattr(cfdi.receiver, 'name', None)
                    } if cfdi.receiver else None,
                    "concepts_count": len(cfdi.concepts) if cfdi.concepts else 0
                }
                for cfdi in sorted_cfdis
            ]
        except Exception as e:
            logger.error(f"Error fetching CFDI data: {str(e)}")
            raise
    
    async def set_operation(self, request: SetOperationRequest) -> Dict:
        """Realiza operaciones de conjuntos con metadatos completos."""
        if not request.sources:
            return {"items": [], "metadata": {"total_count": 0, "operation": request.operation}}
        
        # Obtener datos de todas las fuentes
        source_results = []
        source_metadata = []
        
        for i, source in enumerate(request.sources):
            try:
                if source.table == TableType.CFDI:
                    data = await self._fetch_cfdi_data(source.filters)
                    source_results.append(data)
                    source_metadata.append({
                        "source_index": i,
                        "table": source.table,
                        "record_count": len(data),
                        "filters_applied": source.filters.dict(exclude_none=True) if source.filters else {}
                    })
                else:
                    # Para futuras implementaciones de otras tablas
                    logger.warning(f"Table type {source.table} not yet supported")
                    source_results.append([])
                    source_metadata.append({
                        "source_index": i,
                        "table": source.table,
                        "record_count": 0,
                        "error": "Table type not supported"
                    })
            except Exception as e:
                logger.error(f"Error processing source {i}: {str(e)}")
                source_results.append([])
                source_metadata.append({
                    "source_index": i,
                    "table": source.table,
                    "record_count": 0,
                    "error": str(e)
                })
        
        # Aplicar operación de conjunto
        if request.operation == OperationType.UNION:
            result_items = self._perform_union(source_results)
        elif request.operation == OperationType.INTERSECTION:
            result_items = self._perform_intersection(source_results)
        else:
            result_items = []
        
        return {
            "items": result_items,
            "metadata": {
                "total_count": len(result_items),
                "operation": request.operation,
                "sources_processed": len(request.sources),
                "source_details": source_metadata,
                "execution_timestamp": datetime.now().isoformat()
            }
        }
    
    def _perform_union(self, results: List[List[Dict]]) -> List[Dict]:
        """Realiza unión eliminando duplicados por UUID."""
        union_dict = {}
        for result in results:
            for item in result:
                uuid = item.get("uuid")
                if uuid and uuid not in union_dict:
                    union_dict[uuid] = item
        
        return list(union_dict.values())
    
    def _perform_intersection(self, results: List[List[Dict]]) -> List[Dict]:
        """Realiza intersección basada en UUID."""
        if not results or len(results) < 2:
            return results[0] if results else []
        
        # Crear diccionarios por UUID
        result_dicts = []
        for result in results:
            result_dict = {item.get("uuid"): item for item in result if item.get("uuid")}
            result_dicts.append(result_dict)
        
        # Encontrar UUIDs comunes
        common_uuids = set(result_dicts[0].keys())
        for result_dict in result_dicts[1:]:
            common_uuids &= set(result_dict.keys())
        
        return [result_dicts[0][uuid] for uuid in common_uuids]