from src.database import db
from src.Models.visualize import CFDIFilter, JoinRequest, TableType
from typing import Dict, List, Optional
import math

class JoinService:
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

    def _validate_join_conditions(self, on: Dict[str, str], sources: List[TableType]) -> None:
        """Valida las condiciones de join especificadas en el campo 'on'."""
        valid_joins = {
            "cfdi.issuer_id": "issuer.rfc",
            "cfdi.receiver_id": "receiver.rfc"
        }
        for left, right in on.items():
            if left not in valid_joins or valid_joins[left] != right:
                raise ValueError(f"Invalid join condition: {left} = {right}")
            # Ensure the joined table is included in sources
            if left.startswith("cfdi.issuer_id") and TableType.ISSUER not in sources:
                raise ValueError("ISSUER must be in sources for cfdi.issuer_id join")
            if left.startswith("cfdi.receiver_id") and TableType.RECEIVER not in sources:
                raise ValueError("RECEIVER must be in sources for cfdi.receiver_id join")

    async def join_data(self, request: JoinRequest, page: int = 1, page_size: int = 100) -> Dict:
        """Combina datos de múltiples tablas (joins virtuales).

        Args:
            request (JoinRequest): The join request specifying sources, join type, on conditions, and filters.
            page (int): Page number (starts at 1).
            page_size (int): Number of records per page.

        Returns:
            Dict: A dictionary containing the combined data, page number, page size, and total pages.
        """
        # Validate join conditions
        self._validate_join_conditions(request.on, request.sources)

        where_conditions = self._build_where_conditions(request.filters)
        include = {}
        if TableType.RECEIVER in request.sources:
            include["receiver"] = True
        if TableType.ISSUER in request.sources:
            include["issuer"] = True

        # Count total records to calculate total pages
        total_count = await db.cfdi.count(where=where_conditions)
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

        # Fetch paginated records
        cfdis = await db.cfdi.find_many(
            where=where_conditions,
            include=include,
            take=page_size,
            skip=(page - 1) * page_size
        )
        
        result = []
        for cfdi in cfdis:
            item = {
                "uuid": cfdi.uuid,
                "total": cfdi.total,
                "issuer_name": cfdi.issuer.name_issuer if cfdi.issuer and TableType.ISSUER in request.sources else None,
                "receiver_name": cfdi.receiver.name_receiver if cfdi.receiver and TableType.RECEIVER in request.sources else None
            }
            result.append(item)
        
        return {
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "items": result
        }