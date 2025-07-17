from src.database import db
from src.Models.visualize import CFDIFilter
from typing import Dict, Optional, List

class ScriptService:
    def __init__(self, user_rfc: str):
        self.user_rfc = user_rfc

    def _build_where_conditions(self, filters: Optional[CFDIFilter]) -> Dict:
        """Construye condiciones de filtrado para consultas Prisma."""
        where_conditions = {"user_rfc": self.user_rfc}
        if filters:
            if filters.start_date:
                where_conditions["start_date"] = filters.start_date.isoformat()
            if filters.end_date:
                where_conditions["end_date"] = filters.end_date.isoformat()
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

    async def execute_sql(self, query: str, filters: Optional[CFDIFilter]) -> List[Dict]:
        """Ejecuta consultas SQL predefinidas.

        Args:
            query (str): The SQL query to execute.
            filters (Optional[CFDIFilter]): Filters to apply to the query.

        Returns:
            List[Dict]: The query results.
        """
        allowed_queries = [
            "SELECT AVG(total) AS average FROM cfdi WHERE type = :type AND user_id = :user_rfc",
            "SELECT SUM(total) AS total FROM cfdi WHERE type = :type AND user_id = :user_rfc",
            "SELECT COUNT(*) AS count FROM cfdi WHERE type = :type AND user_id = :user_rfc",
            "SELECT MIN(total) AS min_total FROM cfdi WHERE type = :type AND user_id = :user_rfc",
            "SELECT MAX(total) AS max_total FROM cfdi WHERE type = :type AND user_id = :user_rfc",
            "SELECT uuid, total FROM cfdi WHERE type = :type AND user_id = :user_rfc ORDER BY total DESC LIMIT 10"
        ]
        if query not in allowed_queries:
            raise ValueError("Invalid or unsupported query")
        
        where_conditions = self._build_where_conditions(filters)
        result = await db.query_raw(query, where_conditions)
        return result