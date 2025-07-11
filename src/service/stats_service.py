from src.database import db
from src.Models.visualize import CFDIFilter
from typing import Dict, Optional
import statistics

class StatsService:
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

    async def central_tendency(self, field: str, filters: Optional[CFDIFilter]) -> Dict:
        """Calcula medidas de tendencia central (promedio, mediana, moda).

        Args:
            field (str): The field to analyze (total, subtotal).
            filters (Optional[CFDIFilter]): Filters to apply to the query.

        Returns:
            Dict: Average, median, and mode of the specified field.
        """
        where_conditions = self._build_where_conditions(filters)
        cfdis = await db.cfdi.find_many(
            where=where_conditions
        )
        values = [getattr(cfdi, field) for cfdi in cfdis]
        
        if not values:
            return {"average": 0, "median": 0, "mode": 0}
        
        average = sum(values) / len(values)
        median = statistics.median(values)
        mode = statistics.mode(values) if len(set(values)) < len(values) else values[0]
        
        return {
            "average": average,
            "median": median,
            "mode": mode
        }

    async def basic_stats(self, field: str, filters: Optional[CFDIFilter]) -> Dict:
        """Calcula estadísticas básicas (rango, varianza, desviación estándar, coeficiente de variación).

        Args:
            field (str): The field to analyze (total, subtotal).
            filters (Optional[CFDIFilter]): Filters to apply to the query.

        Returns:
            Dict: Range, variance, standard deviation, and coefficient of variation.
        """
        where_conditions = self._build_where_conditions(filters)
        cfdis = await db.cfdi.find_many(
            where=where_conditions
        )
        values = [getattr(cfdi, field) for cfdi in cfdis]
        
        if not values:
            return {
                "range": 0,
                "variance": 0,
                "standard_deviation": 0,
                "coefficient_of_variation": 0
            }
        
        average = sum(values) / len(values)
        variance = sum((x - average) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        range_val = max(values) - min(values)
        cv = (std_dev / average * 100) if average != 0 else 0
        
        return {
            "range": range_val,
            "variance": variance,
            "standard_deviation": std_dev,
            "coefficient_of_variation": cv
        }