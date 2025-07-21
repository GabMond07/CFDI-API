from src.database import db
from src.Models.visualize import CFDIFilter, SetOperationRequest, OperationType, TableType
from typing import Dict, List, Optional
from datetime import datetime
import logging
import math

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
    
    async def _serialize_filters(self, filters: Optional[CFDIFilter]) -> Dict:
        """Serializa los campos datetime de CFDIFilter a strings."""
        if not filters:
            return {}
        filter_dict = filters.dict(exclude_none=True)
        if "start_date" in filter_dict and filter_dict["start_date"]:
            filter_dict["start_date"] = filter_dict["start_date"].isoformat()
        if "end_date" in filter_dict and filter_dict["end_date"]:
            filter_dict["end_date"] = filter_dict["end_date"].isoformat()
        return filter_dict
    
    async def _fetch_cfdi_data(self, filters: Optional[CFDIFilter], page: int, page_size: int) -> Dict:
        """Obtiene datos de CFDI basados en filtros con relaciones incluidas."""
        where_conditions = self._build_where_conditions(filters)
        
        try:
            # Count total records for pagination
            total_count = await db.cfdi.count(where=where_conditions)
            total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

            cfdis = await db.cfdi.find_many(
                where=where_conditions,
                include={
                    "issuer": True,
                    "receiver": True
                },
                take=page_size,
                skip=(page - 1) * page_size
            )
            
            # Ordenar los resultados en Python, manejando None en issue_date
            sorted_cfdis = sorted(
                cfdis,
                key=lambda x: x.issue_date or datetime(1970, 1, 1),
                reverse=True
            )
            
            result = [
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
                        "name": cfdi.issuer.name_issuer,
                        "created_at": cfdi.issuer.created_at.isoformat() if cfdi.issuer and getattr(cfdi.issuer, 'created_at', None) else None,
                        "updated_at": cfdi.issuer.updated_at.isoformat() if cfdi.issuer and getattr(cfdi.issuer, 'updated_at', None) else None
                    } if cfdi.issuer else None,
                    "receiver": {
                        "id": cfdi.receiver.id,
                        "name": getattr(cfdi.receiver, 'name', None),
                        "created_at": cfdi.receiver.created_at.isoformat() if cfdi.receiver and getattr(cfdi.receiver, 'created_at', None) else None,
                        "updated_at": cfdi.receiver.updated_at.isoformat() if cfdi.receiver and getattr(cfdi.receiver, 'updated_at', None) else None
                    } if cfdi.receiver else None
                }
                for cfdi in sorted_cfdis
            ]
            
            logger.debug(f"Fetched CFDI data: {result}")
            
            return {
                "items": result,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        except Exception as e:
            logger.error(f"Error fetching CFDI data: {str(e)}")
            raise
    
    async def set_operation(self, request: SetOperationRequest, page: int = 1, page_size: int = 100) -> Dict:
        """Realiza operaciones de conjuntos con metadatos completos."""
        if not request.sources:
            return {
                "items": [],
                "metadata": {
                    "total_count": 0,
                    "operation": request.operation,
                    "sources_processed": 0,
                    "source_details": [],
                    "execution_timestamp": datetime.now().isoformat(),
                    "page": page,
                    "page_size": page_size,
                    "total_pages": 1
                }
            }
        
        # Obtener datos de todas las fuentes
        source_results = []
        source_metadata = []
        
        for i, source in enumerate(request.sources):
            try:
                if source.table == TableType.CFDI:
                    data = await self._fetch_cfdi_data(source.filters, page, page_size)
                    source_results.append(data["items"])
                    source_metadata.append({
                        "source_index": i,
                        "table": source.table,
                        "record_count": len(data["items"]),
                        "total_pages": data["total_pages"],
                        "filters_applied": await self._serialize_filters(source.filters)
                    })
                else:
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
        
        # Aplicar paginación en el resultado final
        total_count = len(result_items)
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_items = result_items[start_idx:end_idx]
        
        response = {
            "items": paginated_items,
            "metadata": {
                "total_count": total_count,
                "operation": request.operation,
                "sources_processed": len(request.sources),
                "source_details": source_metadata,
                "execution_timestamp": datetime.now().isoformat(),
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages
            }
        }
        
        logger.debug(f"Set operation response: {response}")
        
        return response
    
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