from src.database import db
from src.Models.visualize import CFDIFilter
from typing import Dict, Optional, List
import math

class CFDIProcessor:
    def __init__(self, user_rfc: str):
        self.user_rfc = user_rfc

    def _build_where_conditions(self, filters: Optional[CFDIFilter]) -> Dict:
        """Construye condiciones de filtrado para consultas Prisma."""
        where_conditions = {"user_id": self.user_rfc}
        if filters:
            if filters.start_date:
                where_conditions["issue_date"] = where_conditions.get("issue_date", {})
                where_conditions["issue_date"]["gte"] = filters.start_date
            if filters.end_date:
                where_conditions["issue_date"] = where_conditions.get("issue_date", {})
                where_conditions["issue_date"]["lte"] = filters.end_date
            if filters.type:
                where_conditions["type"] = filters.type
            if filters.serie:
                where_conditions["serie"] = filters.serie
            if filters.folio:
                where_conditions["folio"] = filters.folio
            if filters.issuer_id:
                where_conditions["issuer_id"] = filters.issuer_id
            if filters.receiver_id:
                where_conditions["receiver_id"] = filters.receiver_id
            if filters.currency:
                where_conditions["currency"] = filters.currency
            if filters.payment_method:
                where_conditions["payment_method"] = filters.payment_method
            if filters.payment_form:
                where_conditions["payment_form"] = filters.payment_form
            if filters.cfdi_use:
                where_conditions["cfdi_use"] = filters.cfdi_use
            if filters.export_status:
                where_conditions["export_status"] = filters.export_status
            if filters.min_total is not None:
                where_conditions["total"] = where_conditions.get("total", {})
                where_conditions["total"]["gte"] = filters.min_total
            if filters.max_total is not None:
                where_conditions["total"] = where_conditions.get("total", {})
                where_conditions["total"]["lte"] = filters.max_total
        return where_conditions

    async def process_data(self, filters: CFDIFilter, aggregation: str, include_details: bool, page: int = 1, page_size: int = 100) -> Dict:
        """Procesa datos CFDI con agregaciones.

        Args:
            filters (CFDIFilter): Filtros a aplicar a la consulta.
            aggregation (str): Tipo de agregación (sum, count, avg, min, max).
            include_details (bool): Indica si se deben incluir detalles en la respuesta.
            page (int): Número de página (comienza en 1).
            page_size (int): Cantidad de registros por página.

        Returns:
            Dict: Resultado de la agregación, detalles opcionales, número de páginas y tamaño de página.
        """
        where_conditions = self._build_where_conditions(filters)
        
        # Contar el total de registros para calcular el número de páginas
        total_count = await db.cfdi.count(where=where_conditions)
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

        # Obtener los registros paginados
        cfdis = await db.cfdi.find_many(
            where=where_conditions,
            include={"concepts": include_details, "issuer": True},
            take=page_size,
            skip=(page - 1) * page_size
        )

        # Convertir resultados a lista
        data = [c for c in cfdis]

        # Aplicar agregaciones
        result = {
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
        if aggregation == "sum":
            result["total_amount"] = sum(cfdi.total for cfdi in data) if data else 0
        elif aggregation == "count":
            result["cfdi_count"] = len(data)
        elif aggregation == "avg":
            result["average_total"] = sum(cfdi.total for cfdi in data) / len(data) if data else 0
        elif aggregation == "min":
            result["min_total"] = min(cfdi.total for cfdi in data) if data else 0
        elif aggregation == "max":
            result["max_total"] = max(cfdi.total for cfdi in data) if data else 0

        # Incluir detalles si se solicita
        if include_details:
            result["details"] = [
                {
                    "uuid": cfdi.uuid,
                    "total": cfdi.total,
                    "issuer_name": cfdi.issuer.name_issuer if cfdi.issuer else None,
                    "concepts": [{"description": c.description, "amount": c.amount} for c in cfdi.concepts] if cfdi.concepts else []
                }
                for cfdi in data
            ]

        return result