from src.database import db
from src.Models.visualize import CFDIFilter, JoinRequest
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

    async def join_data(self, request: JoinRequest) -> List[Dict]:
        """Combina datos de múltiples tablas (joins virtuales).

        Args:
            request (JoinRequest): The join request specifying sources, join type, and filters.

        Returns:
            List[Dict]: A list of combined data from the specified tables.
        """
        where_conditions = self._build_where_conditions(request.filters)
        include = {}
        if "receiver" in request.sources:
            include["receiver"] = True
        if "issuer" in request.sources:
            include["issuer"] = True

        cfdis = await db.cfdi.find_many(
            where=where_conditions,
            include=include
        )
        return [
            {
                "uuid": cfdi.uuid,
                "total": cfdi.total,
                "issuer_name": cfdi.issuer.name_issuer if cfdi.issuer and "issuer" in request.sources else None,
                "receiver_name": cfdi.receiver.name_receiver if cfdi.receiver and "receiver" in request.sources else None
            }
            for cfdi in cfdis
        ]