from src.database import db
from src.Models.visualize import CFDIFilter

class CFDIProcessor:
    def __init__(self, user_rfc: str):
        self.user_rfc = user_rfc

    async def process_data(self, filters: CFDIFilter, aggregation: str, include_details: bool):
        # Construir condiciones de filtrado
        where_conditions = {"user_id": self.user_rfc}
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

        # Consultar CFDI en la base de datos
        cfdis = await db.cfdi.find_many(
            where=where_conditions,
            include={"concepts": include_details, "issuer": True}
        )

        # Convertir resultados a lista
        data = [c for c in cfdis]

        # Aplicar agregaciones
        if aggregation == "sum":
            result = {"total_amount": sum(cfdi.total for cfdi in data)}
        elif aggregation == "count":
            result = {"cfdi_count": len(data)}
        elif aggregation == "avg":
            result = {"average_total": sum(cfdi.total for cfdi in data) / len(data) if data else 0}
        elif aggregation == "min":
            result = {"min_total": min(cfdi.total for cfdi in data) if data else 0}
        elif aggregation == "max":
            result = {"max_total": max(cfdi.total for cfdi in data) if data else 0}

        # Incluir detalles si se solicita
        if include_details:
            result["details"] = [
                {
                    "uuid": cfdi.uuid,
                    "total": cfdi.total,
                    "concepts": [{"description": c.description, "amount": c.amount} for c in cfdi.concepts]
                }
                for cfdi in data
            ]

        return result