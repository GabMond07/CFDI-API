from src.database import db
from src.Models.visualize import CFDIFilter
from typing import Dict, Optional

class AggregationService:
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
            if filters.status:
                where_conditions["status"] = filters.status
            if filters.type:
                where_conditions["type"] = filters.type
            if filters.serie:
                where_conditions["serie"] = filters.serie
            if filters.folio:
                where_conditions["folio"] = filters.folio
            if filters.issuer_id:
                where_conditions["issuer_id"] = filters.issuer_id
        return where_conditions

    async def aggregate_data(self, operation: str, field: str, filters: Optional[CFDIFilter], include_details: bool) -> Dict:
        """Procesa agregaciones básicas (sum, count, avg, min, max).

        Args:
            operation (str): The aggregation operation to perform (sum, count, avg, min, max).
            field (str): The field to aggregate (total, subtotal).
            filters (Optional[CFDIFilter]): Filters to apply to the query.
            include_details (bool): Whether to include detailed CFDI data in the response.

        Returns:
            Dict: The aggregation result with optional details.
        """
        where_conditions = self._build_where_conditions(filters)
        cfdis = await db.cfdi.find_many(
            where=where_conditions,
            include={"concepts": include_details, "issuer": True}
        )
        data = [c for c in cfdis]
        
        result = {}
        if operation == "sum":
            result = {"total_amount": sum(getattr(cfdi, field) for cfdi in data)}
        elif operation == "count":
            result = {"cfdi_count": len(data)}
        elif operation == "avg":
            result = {"average_total": sum(getattr(cfdi, field) for cfdi in data) / len(data) if data else 0}
        elif operation == "min":
            result = {"min_total": min(getattr(cfdi, field) for cfdi in data) if data else 0}
        elif operation == "max":
            result = {"max_total": max(getattr(cfdi, field) for cfdi in data) if data else 0}

        if include_details:
            result["details"] = [
                {
                    "uuid": cfdi.uuid,
                    field: getattr(cfdi, field),
                    "concepts": [{"description": c.description, "amount": c.amount} for c in cfdi.concepts]
                }
                for cfdi in data
            ]

        return result