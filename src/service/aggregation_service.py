from src.database import db
from src.Models.visualize import CFDIFilter
from typing import Dict, Optional, List
import math

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

    async def aggregate_data(self, operation: str, field: str, filters: Optional[CFDIFilter], include_details: bool, page: int = 1, page_size: int = 100) -> Dict:
        """Procesa agregaciones básicas (sum, count, avg, min, max).

        Args:
            operation (str): The aggregation operation (sum, count, avg, min, max).
            field (str): The field to aggregate (total, subtotal).
            filters (Optional[CFDIFilter]): Filters to apply to the query.
            include_details (bool): Whether to include detailed results.
            page (int): Page number (starts at 1).
            page_size (int): Number of records per page.

        Returns:
            Dict: The aggregation result, optionally detailed data, page number, page size, and total pages.
        """
        where_conditions = self._build_where_conditions(filters)
        
        # Count total records to calculate total pages
        total_count = await db.cfdi.count(where=where_conditions)
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

        # Fetch paginated records
        cfdis = await db.cfdi.find_many(
            where=where_conditions,
            take=page_size,
            skip=(page - 1) * page_size
        )
        values = [getattr(cfdi, field) for cfdi in cfdis]
        
        result = {
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
        if operation == "sum":
            result[field] = sum(values) if values else 0
        elif operation == "count":
            result[field] = len(values)
        elif operation == "avg":
            result[field] = sum(values) / len(values) if values else 0
        elif operation == "min":
            result[field] = min(values) if values else 0
        elif operation == "max":
            result[field] = max(values) if values else 0
        
        if include_details:
            result["details"] = [{"uuid": cfdi.uuid, field: getattr(cfdi, field)} for cfdi in cfdis]
        
        return {"result": result}