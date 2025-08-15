from src.database import db
from src.Models.operation.common import CFDIFilter, TableType
from src.service.operation.export_service import generate_report_from_data
from typing import Dict, List, Optional
import math
import logging
from datetime import datetime
from fastapi import HTTPException

logger = logging.getLogger(__name__)

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

    def get_predefined_joins(self, page: int = 1, page_size: int = 100) -> Dict:
        """Devuelve una lista de consultas predefinidas disponibles con paginación."""
        predefined_joins = [
            {
                "id": 1,
                "name": "cfdi_with_issuer",
                "description": "CFDI con información del emisor",
                "tables": ["CFDI", "Issuer"],
                "join_type": "inner"
            },
            {
                "id": 2,
                "name": "cfdi_with_receiver",
                "description": "CFDI con información del receptor",
                "tables": ["CFDI", "Receiver"],
                "join_type": "left"
            },
            {
                "id": 3,
                "name": "cfdi_full",
                "description": "CFDI con emisor y receptor",
                "tables": ["CFDI", "Issuer", "Receiver"],
                "join_type": "inner_left"
            },
            {
                "id": 4,
                "name": "cfdi_with_concepts",
                "description": "CFDI con sus conceptos",
                "tables": ["CFDI", "Concept"],
                "join_type": "inner"
            },
            {
                "id": 5,
                "name": "cfdi_with_concepts_taxes",
                "description": "CFDI con conceptos y taxes",
                "tables": ["CFDI", "Concept", "Taxes"],
                "join_type": "inner"
            },
            {
                "id": 6,
                "name": "cfdi_tax_summary",
                "description": "Resumen de impuestos por CFDI",
                "tables": ["CFDI", "Concept", "Taxes"],
                "join_type": "inner"
            },
            {
                "id": 7,
                "name": "user_reports",
                "description": "Reportes del usuario",
                "tables": ["Report", "CFDI"],
                "join_type": "left"
            },
            {
                "id": 8,
                "name": "user_visualizations",
                "description": "Visualizaciones del usuario",
                "tables": ["Visualization", "CFDI"],
                "join_type": "left"
            },
            {
                "id": 9,
                "name": "user_notifications",
                "description": "Notificaciones del usuario",
                "tables": ["Notification", "CFDI"],
                "join_type": "left"
            },
            {
                "id": 10,
                "name": "cfdi_with_payment_complements",
                "description": "CFDI con complementos de pago",
                "tables": ["CFDI", "PaymentComplement"],
                "join_type": "inner"
            },
            {
                "id": 11,
                "name": "cfdi_with_attachments",
                "description": "CFDI con adjuntos (sin contenido de archivo)",
                "tables": ["CFDI", "CFDIAttachment"],
                "join_type": "inner"
            },
            {
                "id": 12,
                "name": "cfdi_with_relations",
                "description": "CFDI con sus relaciones",
                "tables": ["CFDI", "CFDIRelation"],
                "join_type": "inner"
            },
            {
                "id": 13,
                "name": "cfdi_monthly_summary",
                "description": "Resumen mensual de CFDI",
                "tables": ["CFDI"],
                "join_type": "none"
            },
            {
                "id": 14,
                "name": "cfdi_by_issuer",
                "description": "Resumen por emisor",
                "tables": ["CFDI", "Issuer"],
                "join_type": "inner"
            },
            {
                "id": 15,
                "name": "cfdi_by_type",
                "description": "Resumen por tipo de CFDI",
                "tables": ["CFDI"],
                "join_type": "none"
            },
            {
                "id": 16,
                "name": "user_info",
                "description": "Información del usuario con rol y tenant",
                "tables": ["User", "Roles", "Tenant"],
                "join_type": "inner_left"
            },
            {
                "id": 17,
                "name": "user_batch_jobs",
                "description": "Jobs del usuario",
                "tables": ["BatchJob"],
                "join_type": "none"
            },
            {
                "id": 18,
                "name": "cfdi_complete",
                "description": "Vista completa de CFDI con toda la información relacionada",
                "tables": ["CFDI", "Issuer", "Receiver", "Concept", "CFDIAttachment", "PaymentComplement"],
                "join_type": "inner_left"
            },
            {
                "id": 19,
                "name": "cfdi_by_receiver",
                "description": "Resumen por receptor",
                "tables": ["CFDI", "Receiver"],
                "join_type": "inner"
            },
            {
                "id": 20,
                "name": "cfdi_with_concepts_relations",
                "description": "CFDI con conceptos y relaciones",
                "tables": ["CFDI", "Concept", "CFDIRelation"],
                "join_type": "inner"
            },
            {
                "id": 21,
                "name": "payment_complement_monthly",
                "description": "Resumen mensual de complementos de pago",
                "tables": ["CFDI", "PaymentComplement"],
                "join_type": "inner"
            },
            {
                "id": 22,
                "name": "cfdi_with_cancellation_status",
                "description": "CFDI con estado de cancelación",
                "tables": ["CFDI", "Cancellation"],
                "join_type": "left"
            }
        ]
        total_count = len(predefined_joins)
        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
        start = (page - 1) * page_size
        end = start + page_size
        return {
            "joins": predefined_joins[start:end],
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "total_count": total_count
        }

    async def execute_predefined_join(self, join_id: int, filters: Optional[CFDIFilter], page: int, page_size: int) -> Dict:
        """Ejecuta una consulta predefinida por su ID."""
        predefined_joins = self.get_predefined_joins(page=1, page_size=1000)["joins"]
        join_def = next((j for j in predefined_joins if j["id"] == join_id), None)
        if not join_def:
            raise HTTPException(status_code=404, detail="Predefined join not found")

        where_conditions = self._build_where_conditions(filters)
        include = {}
        result = []
        total_count = 0
        total_pages = 1

        # Validar que las fechas estén definidas para consultas de resumen
        if join_def["name"] in ["cfdi_monthly_summary", "cfdi_by_issuer", "cfdi_by_type", "payment_complement_monthly"]:
            if not filters or not filters.start_date or not filters.end_date:
                raise HTTPException(status_code=400, detail="start_date and end_date are required for summary queries")

        # Consulta 1: CFDI con información del emisor
        if join_def["id"] == 1:
            include["issuer"] = True
            total_count = await db.cfdi.count(where=where_conditions)
            cfdis = await db.cfdi.find_many(
                where=where_conditions,
                include=include,
                take=page_size,
                skip=(page - 1) * page_size,
                order={"issue_date": "desc"}
            )
            for cfdi in cfdis:
                result.append({
                    "id": cfdi.id,
                    "uuid": cfdi.uuid,
                    "serie": cfdi.serie,
                    "folio": cfdi.folio,
                    "issue_date": cfdi.issue_date.isoformat() if cfdi.issue_date else None,
                    "total": cfdi.total,
                    "subtotal": cfdi.subtotal,
                    "issuer_name": cfdi.issuer.name_issuer if cfdi.issuer else None,
                    "issuer_tax_regime": cfdi.issuer.tax_regime if cfdi.issuer else None
                })

        # Consulta 2: CFDI con información del receptor
        elif join_def["id"] == 2:
            include["receiver"] = True
            total_count = await db.cfdi.count(where=where_conditions)
            cfdis = await db.cfdi.find_many(
                where=where_conditions,
                include=include,
                take=page_size,
                skip=(page - 1) * page_size,
                order={"issue_date": "desc"}
            )
            for cfdi in cfdis:
                result.append({
                    "id": cfdi.id,
                    "uuid": cfdi.uuid,
                    "serie": cfdi.serie,
                    "folio": cfdi.folio,
                    "total": cfdi.total,
                    "receiver_rfc": cfdi.receiver.rfc_receiver if cfdi.receiver else None,
                    "receiver_name": cfdi.receiver.name_receiver if cfdi.receiver else None,
                    "receiver_tax_regime": cfdi.receiver.tax_regime if cfdi.receiver else None
                })

        # Consulta 3: CFDI completo con emisor y receptor
        elif join_def["id"] == 3:
            include["issuer"] = True
            include["receiver"] = True
            total_count = await db.cfdi.count(where=where_conditions)
            cfdis = await db.cfdi.find_many(
                where=where_conditions,
                include=include,
                take=page_size,
                skip=(page - 1) * page_size,
                order={"issue_date": "desc"}
            )
            for cfdi in cfdis:
                result.append({
                    "id": cfdi.id,
                    "uuid": cfdi.uuid,
                    "serie": cfdi.serie,
                    "folio": cfdi.folio,
                    "issue_date": cfdi.issue_date.isoformat() if cfdi.issue_date else None,
                    "total": cfdi.total,
                    "subtotal": cfdi.subtotal,
                    "type": cfdi.type,
                    "issuer_name": cfdi.issuer.name_issuer if cfdi.issuer else None,
                    "issuer_tax_regime": cfdi.issuer.tax_regime if cfdi.issuer else None,
                    "receiver_rfc": cfdi.receiver.rfc_receiver if cfdi.receiver else None,
                    "receiver_name": cfdi.receiver.name_receiver if cfdi.receiver else None,
                    "receiver_tax_regime": cfdi.receiver.tax_regime if cfdi.receiver else None
                })

        # Consulta 4: CFDI con conceptos
        elif join_def["id"] == 4:
            include["concepts"] = True
            total_count = await db.cfdi.count(where=where_conditions)
            cfdis = await db.cfdi.find_many(
                where=where_conditions,
                include=include,
                take=page_size,
                skip=(page - 1) * page_size,
                order={"issue_date": "desc"}
            )
            for cfdi in cfdis:
                for concept in cfdi.concepts:
                    result.append({
                        "id": cfdi.id,
                        "uuid": cfdi.uuid,
                        "serie": cfdi.serie,
                        "folio": cfdi.folio,
                        "total": cfdi.total,
                        "fiscal_key": concept.fiscal_key,
                        "description": concept.description,
                        "quantity": concept.quantity,
                        "unit_value": concept.unit_value,
                        "amount": concept.amount
                    })

        # Consulta 5: CFDI con conceptos y taxes
        elif join_def["id"] == 5:
            include["concepts"] = {"include": {"taxes": True}}
            total_count = await db.cfdi.count(where=where_conditions)
            cfdis = await db.cfdi.find_many(
                where=where_conditions,
                include=include,
                take=page_size,
                skip=(page - 1) * page_size,
                order={"issue_date": "desc"}
            )
            for cfdi in cfdis:
                for concept in cfdi.concepts:
                    for tax in concept.taxes:
                        result.append({
                            "id": cfdi.id,
                            "uuid": cfdi.uuid,
                            "serie": cfdi.serie,
                            "folio": cfdi.folio,
                            "description": concept.description,
                            "concept_amount": concept.amount,
                            "tax_type": tax.tax_type,
                            "rate": tax.rate,
                            "tax_amount": tax.amount
                        })

        # Consulta 6: Resumen de impuestos por CFDI
        elif join_def["id"] == 6:
            cfdis = await db.cfdi.find_many(
                where=where_conditions,
                include={"concepts": {"include": {"taxes": True}}},
                take=page_size,
                skip=(page - 1) * page_size,
                order={"issue_date": "desc"}
            )
            tax_summary = {}
            for cfdi in cfdis:
                for concept in cfdi.concepts:
                    for tax in concept.taxes:
                        key = (cfdi.id, cfdi.uuid, cfdi.total, tax.tax_type)
                        if key not in tax_summary:
                            tax_summary[key] = {"total_tax_amount": 0, "tax_count": 0}
                        tax_summary[key]["total_tax_amount"] += tax.amount
                        tax_summary[key]["tax_count"] += 1
            for (id, uuid, total, tax_type), summary in tax_summary.items():
                result.append({
                    "id": id,
                    "uuid": uuid,
                    "total": total,
                    "tax_type": tax_type,
                    "total_tax_amount": summary["total_tax_amount"],
                    "tax_count": summary["tax_count"]
                })
            total_count = len(tax_summary)

        # Consulta 7: Reportes del usuario
        elif join_def["id"] == 7:
            total_count = await db.report.count(where={"user_id": self.user_rfc})
            reports = await db.report.find_many(
                where={"user_id": self.user_rfc},
                include={"cfdi": True},
                take=page_size,
                skip=(page - 1) * page_size,
                order={"created_at": "desc"}
            )
            for report in reports:
                result.append({
                    "id": report.id,
                    "format": report.format,
                    "created_at": report.created_at.isoformat() if report.created_at else None,
                    "cfdi_uuid": report.cfdi.uuid if report.cfdi else None,
                    "cfdi_serie": report.cfdi.serie if report.cfdi else None,
                    "cfdi_folio": report.cfdi.folio if report.cfdi else None,
                    "cfdi_total": report.cfdi.total if report.cfdi else None
                })

        # Consulta 8: Visualizaciones del usuario
        elif join_def["id"] == 8:
            total_count = await db.visualization.count(where={"user_id": self.user_rfc})
            visualizations = await db.visualization.find_many(
                where={"user_id": self.user_rfc},
                include={"cfdi": True},
                take=page_size,
                skip=(page - 1) * page_size,
                order={"created_at": "desc"}
            )
            for vis in visualizations:
                result.append({
                    "id": vis.id,
                    "type": vis.type,
                    "config": vis.config,
                    "created_at": vis.created_at.isoformat() if vis.created_at else None,
                    "cfdi_uuid": vis.cfdi.uuid if vis.cfdi else None,
                    "cfdi_serie": vis.cfdi.serie if vis.cfdi else None,
                    "cfdi_folio": vis.cfdi.folio if vis.cfdi else None
                })

        # Consulta 9: Notificaciones del usuario
        elif join_def["id"] == 9:
            total_count = await db.notification.count(where={"user_id": self.user_rfc})
            notifications = await db.notification.find_many(
                where={"user_id": self.user_rfc},
                include={"cfdi": True},
                take=page_size,
                skip=(page - 1) * page_size,
                order={"created_at": "desc"}
            )
            for notif in notifications:
                result.append({
                    "id": notif.id,
                    "type": notif.type,
                    "status": notif.status,
                    "created_at": notif.created_at.isoformat() if notif.created_at else None,
                    "sent_at": notif.sent_at.isoformat() if notif.sent_at else None,
                    "cfdi_uuid": notif.cfdi.uuid if notif.cfdi else None,
                    "cfdi_serie": notif.cfdi.serie if notif.cfdi else None,
                    "cfdi_folio": notif.cfdi.folio if notif.cfdi else None
                })

        # Consulta 10: CFDI con complementos de pago
        elif join_def["id"] == 10:
            total_count = await db.cfdi.count(where=where_conditions)
            cfdis = await db.cfdi.find_many(
                where=where_conditions,
                include={"payment_complements": True},
                take=page_size,
                skip=(page - 1) * page_size,
                order={"issue_date": "desc"}
            )
            for cfdi in cfdis:
                for pc in cfdi.payment_complements:
                    result.append({
                        "id": cfdi.id,
                        "uuid": cfdi.uuid,
                        "serie": cfdi.serie,
                        "folio": cfdi.folio,
                        "total": cfdi.total,
                        "payment_date": pc.payment_date.isoformat() if pc.payment_date else None,
                        "payment_form": pc.payment_form,
                        "payment_amount": pc.payment_amount
                    })

        # Consulta 11: CFDI con adjuntos
        elif join_def["id"] == 11:
            total_count = await db.cfdi.count(where=where_conditions)
            cfdis = await db.cfdi.find_many(
                where=where_conditions,
                include={"attachments": True},
                take=page_size,
                skip=(page - 1) * page_size,
                order={"issue_date": "desc"}
            )
            for cfdi in cfdis:
                for attachment in cfdi.attachments:
                    result.append({
                        "id": cfdi.id,
                        "uuid": cfdi.uuid,
                        "serie": cfdi.serie,
                        "folio": cfdi.folio,
                        "attachment_id": attachment.id,
                        "file_type": attachment.file_type,
                        "created_at": attachment.created_at.isoformat() if attachment.created_at else None
                    })

        # Consulta 12: CFDI con relaciones
        elif join_def["id"] == 12:
            total_count = await db.cfdi.count(where=where_conditions)
            cfdis = await db.cfdi.find_many(
                where=where_conditions,
                include={"relations": True},
                take=page_size,
                skip=(page - 1) * page_size,
                order={"issue_date": "desc"}
            )
            for cfdi in cfdis:
                for relation in cfdi.relations:
                    result.append({
                        "id": cfdi.id,
                        "uuid": cfdi.uuid,
                        "serie": cfdi.serie,
                        "folio": cfdi.folio,
                        "related_uuid": relation.related_uuid,
                        "relation_type": relation.relation_type
                    })

        # Consulta 13: Resumen mensual de CFDI
        elif join_def["id"] == 13:
            cfdis = await db.cfdi.find_many(
                where=where_conditions,
                take=page_size,
                skip=(page - 1) * page_size,
                order={"issue_date": "desc"}
            )
            monthly_summary = {}
            for cfdi in cfdis:
                month = cfdi.issue_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                month_key = month.isoformat()
                if month_key not in monthly_summary:
                    monthly_summary[month_key] = {"cfdi_count": 0, "total_amount": 0.0, "avg_amount": 0.0}
                monthly_summary[month_key]["cfdi_count"] += 1
                monthly_summary[month_key]["total_amount"] += cfdi.total
            for month, summary in monthly_summary.items():
                summary["avg_amount"] = summary["total_amount"] / summary["cfdi_count"] if summary["cfdi_count"] > 0 else 0
                result.append({
                    "month": month,
                    "cfdi_count": summary["cfdi_count"],
                    "total_amount": summary["total_amount"],
                    "avg_amount": summary["avg_amount"]
                })
            total_count = len(monthly_summary)
            result.sort(key=lambda x: x["month"], reverse=True)

        # Consulta 14: Resumen por emisor
        elif join_def["id"] == 14:
            include["issuer"] = True
            cfdis = await db.cfdi.find_many(
                where=where_conditions,
                include=include,
                take=page_size,
                skip=(page - 1) * page_size,
                order={"total": "desc"}
            )
            issuer_summary = {}
            for cfdi in cfdis:
                issuer_key = cfdi.issuer.rfc_issuer
                if issuer_key not in issuer_summary:
                    issuer_summary[issuer_key] = {
                        "rfc_issuer": issuer_key,
                        "name_issuer": cfdi.issuer.name_issuer,
                        "cfdi_count": 0,
                        "total_amount": 0.0
                    }
                issuer_summary[issuer_key]["cfdi_count"] += 1
                issuer_summary[issuer_key]["total_amount"] += cfdi.total
            result = list(issuer_summary.values())
            total_count = len(issuer_summary)

        # Consulta 15: Resumen por tipo de CFDI
        elif join_def["id"] == 15:
            cfdis = await db.cfdi.find_many(
                where=where_conditions,
                take=page_size,
                skip=(page - 1) * page_size,
                order={"total": "desc"}
            )
            type_summary = {}
            for cfdi in cfdis:
                type_key = cfdi.type
                if type_key not in type_summary:
                    type_summary[type_key] = {"type": type_key, "cfdi_count": 0, "total_amount": 0.0}
                type_summary[type_key]["cfdi_count"] += 1
                type_summary[type_key]["total_amount"] += cfdi.total
            result = list(type_summary.values())
            total_count = len(type_summary)

        # Consulta 16: Información del usuario con rol y tenant
        elif join_def["id"] == 16:
            total_count = await db.user.count(where={"rfc": self.user_rfc})
            users = await db.user.find_many(
                where={"rfc": self.user_rfc},
                include={"role": True, "tenant": True},
                take=page_size,
                skip=(page - 1) * page_size
            )
            for user in users:
                result.append({
                    "rfc": user.rfc,
                    "username": user.username,
                    "email": user.email,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "role": user.role.role if user.role else None,
                    "tenant_name": user.tenant.name if user.tenant else None
                })

        # Consulta 17: Jobs del usuario
        elif join_def["id"] == 17:
            total_count = await db.batchjob.count(where={"user_id": self.user_rfc})
            jobs = await db.batchjob.find_many(
                where={"user_id": self.user_rfc},
                take=page_size,
                skip=(page - 1) * page_size,
                order={"created_at": "desc"}
            )
            for job in jobs:
                result.append({
                    "id": job.id,
                    "status": job.status,
                    "result_count": job.result_count,
                    "created_at": job.created_at.isoformat() if job.created_at else None
                })

        # Consulta 18: Vista completa de CFDI
        elif join_def["id"] == 18:
            include = {
                "issuer": True,
                "receiver": True,
                "concepts": True,
                "attachments": True,
                "payment_complements": True
            }
            total_count = await db.cfdi.count(where=where_conditions)
            cfdis = await db.cfdi.find_many(
                where=where_conditions,
                include=include,
                take=page_size,
                skip=(page - 1) * page_size,
                order={"issue_date": "desc"}
            )
            for cfdi in cfdis:
                result.append({
                    "id": cfdi.id,
                    "uuid": cfdi.uuid,
                    "serie": cfdi.serie,
                    "folio": cfdi.folio,
                    "issue_date": cfdi.issue_date.isoformat() if cfdi.issue_date else None,
                    "total": cfdi.total,
                    "type": cfdi.type,
                    "issuer_name": cfdi.issuer.name_issuer if cfdi.issuer else None,
                    "issuer_tax_regime": cfdi.issuer.tax_regime if cfdi.issuer else None,
                    "receiver_rfc": cfdi.receiver.rfc_receiver if cfdi.receiver else None,
                    "receiver_name": cfdi.receiver.name_receiver if cfdi.receiver else None,
                    "concept_count": len(cfdi.concepts),
                    "attachment_count": len(cfdi.attachments),
                    "payment_complement_count": len(cfdi.payment_complements)
                })

        # Consulta 19: Resumen por receptor
        elif join_def["id"] == 19:
            include["receiver"] = True
            cfdis = await db.cfdi.find_many(
                where=where_conditions,
                include=include,
                take=page_size,
                skip=(page - 1) * page_size,
                order={"total": "desc"}
            )
            receiver_summary = {}
            for cfdi in cfdis:
                receiver_key = cfdi.receiver.rfc_receiver
                if receiver_key not in receiver_summary:
                    receiver_summary[receiver_key] = {
                        "rfc_receiver": receiver_key,
                        "name_receiver": cfdi.receiver.name_receiver,
                        "cfdi_count": 0,
                        "total_amount": 0.0
                    }
                receiver_summary[receiver_key]["cfdi_count"] += 1
                receiver_summary[receiver_key]["total_amount"] += cfdi.total
            result = list(receiver_summary.values())
            total_count = len(receiver_summary)

        # Consulta 20: CFDI con conceptos y relaciones
        elif join_def["id"] == 20:
            include["concepts"] = True
            include["relations"] = True
            total_count = await db.cfdi.count(where=where_conditions)
            cfdis = await db.cfdi.find_many(
                where=where_conditions,
                include=include,
                take=page_size,
                skip=(page - 1) * page_size,
                order={"issue_date": "desc"}
            )
            for cfdi in cfdis:
                for concept in cfdi.concepts:
                    for relation in cfdi.relations:
                        result.append({
                            "id": cfdi.id,
                            "uuid": cfdi.uuid,
                            "serie": cfdi.serie,
                            "folio": cfdi.folio,
                            "total": cfdi.total,
                            "fiscal_key": concept.fiscal_key,
                            "concept_description": concept.description,
                            "concept_amount": concept.amount,
                            "related_uuid": relation.related_uuid,
                            "relation_type": relation.relation_type
                        })

        # Consulta 21: Resumen mensual de complementos de pago
        elif join_def["id"] == 21:
            cfdis = await db.cfdi.find_many(
                where=where_conditions,
                include={"payment_complements": True},
                take=page_size,
                skip=(page - 1) * page_size,
                order={"issue_date": "desc"}
            )
            monthly_summary = {}
            for cfdi in cfdis:
                for pc in cfdi.payment_complements:
                    month = pc.payment_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    month_key = month.isoformat()
                    if month_key not in monthly_summary:
                        monthly_summary[month_key] = {"payment_count": 0, "total_payment_amount": 0.0}
                    monthly_summary[month_key]["payment_count"] += 1
                    monthly_summary[month_key]["total_payment_amount"] += pc.payment_amount
            for month, summary in monthly_summary.items():
                result.append({
                    "month": month,
                    "payment_count": summary["payment_count"],
                    "total_payment_amount": summary["total_payment_amount"]
                })
            total_count = len(monthly_summary)
            result.sort(key=lambda x: x["month"], reverse=True)

        # Consulta 22: CFDI con estado de cancelación
        elif join_def["id"] == 22:
            include["cancellation"] = True
            total_count = await db.cfdi.count(where=where_conditions)
            cfdis = await db.cfdi.find_many(
                where=where_conditions,
                include=include,
                take=page_size,
                skip=(page - 1) * page_size,
                order={"issue_date": "desc"}
            )
            for cfdi in cfdis:
                result.append({
                    "id": cfdi.id,
                    "uuid": cfdi.uuid,
                    "serie": cfdi.serie,
                    "folio": cfdi.folio,
                    "total": cfdi.total,
                    "cancellation_status": cfdi.cancellation.status if cfdi.cancellation else "active",
                    "cancellation_date": cfdi.cancellation.cancellation_date.isoformat() if cfdi.cancellation and cfdi.cancellation.cancellation_date else None
                })

        total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1

        return {
            "content": result,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }