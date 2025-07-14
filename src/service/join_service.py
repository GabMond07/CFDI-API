from src.database import db
from src.Models.visualize import CFDIFilter, JoinRequest, TableType
from typing import Dict, List, Optional

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

    async def join_data(self, request: JoinRequest) -> List[Dict]:
        """Combina datos de múltiples tablas (joins virtuales).

        Args:
            request (JoinRequest): The join request specifying sources, join type, and filters.

        Returns:
            List[Dict]: A list of combined data from the specified tables.
        """
        where_conditions = self._build_where_conditions(request.filters)
        include = {}
        if TableType.RECEIVER in request.sources:
            include["receiver"] = True
        if TableType.ISSUER in request.sources:
            include["issuer"] = True
        if TableType.CONCEPT in request.sources:
            include["concepts"] = True

        cfdis = await db.cfdi.find_many(
            where=where_conditions,
            include=include
        )
        result = []
        for cfdi in cfdis:
            item = {
                "uuid": cfdi.uuid,
                "total": cfdi.total,
                "issuer_name": cfdi.issuer.name_issuer if cfdi.issuer and TableType.ISSUER in request.sources else None,
                "receiver_name": cfdi.receiver.name_receiver if cfdi.receiver and TableType.RECEIVER in request.sources else None
            }
            if TableType.CONCEPT in request.sources:
                item["concepts"] = [{"description": concept.description, "amount": concept.amount} for concept in cfdi.concepts] if cfdi.concepts else []
            result.append(item)
        return result