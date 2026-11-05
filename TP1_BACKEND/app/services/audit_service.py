import io
import csv
from typing import List
from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.repositories.audit_repository import AuditRepository
from app.models.audit_trail import AuditTrail

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from PyPDF2 import PdfReader, PdfWriter


class AuditService:
    def __init__(self, repository: AuditRepository):
        self.repository = repository

    def record_action(
        self, user_id: int, action: str, resource: str, detail: str
    ) -> AuditTrail:
        """Método polimórfico global para trazabilidad inmutable (FDA 21 CFR Part 11)"""
        log_dict = {
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "detail": detail,
            "created_at": datetime.now(ZoneInfo("America/Lima")),
        }
        return self.repository.create_log(log_dict)

    def get_report_data(
        self, desde: date | None = None, hasta: date | None = None
    ) -> List[dict]:
        db_logs = self.repository.get_all(limit=500, desde=desde, hasta=hasta) or []

        formatted_logs = []
        for log in db_logs:
            user_name = (
                log.user.full_name
                if hasattr(log, "user") and log.user
                else "System/Unknown"
            )

            timestamp_str = (
                log.created_at.astimezone(ZoneInfo("America/Lima")).strftime(
                    "%d/%m/%Y %H:%M:%S"
                )
                if log.created_at
                else "N/A"
            )

            formatted_logs.append(
                {
                    "id": log.id,
                    "action": log.action,
                    "user": user_name,
                    "timestamp": timestamp_str,
                    "details": log.detail,
                }
            )

        return formatted_logs

    def get_pipeline_history(self, limit: int = 50) -> List[dict]:
        """Historial de entrenamientos MLOps (exitosos, rechazados y fallidos) con su motivo."""
        status_map = {
            "ML_MODEL_PROMOTED": "SUCCESS",
            "ML_MODEL_REJECTED": "REJECTED",
            "ML_RETRAIN_FAILED": "FAILED",
        }
        history = []
        for log in self.repository.get_by_resource("MLOPS_PIPELINE", limit=limit):
            if log.action not in status_map:
                continue
            history.append(
                {
                    "id": log.id,
                    "status": status_map[log.action],
                    "user": log.user.full_name if log.user else "System/Unknown",
                    "timestamp": log.created_at.astimezone(ZoneInfo("America/Lima")).strftime(
                        "%d/%m/%Y %H:%M:%S"
                    )
                    if log.created_at
                    else "N/A",
                    "detail": log.detail,
                }
            )
        return history

    def export_applied_recommendations_csv(
        self, desde: date | None = None, hasta: date | None = None
    ):
        logs = self.get_report_data(desde, hasta)
        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer, fieldnames=["id", "action", "user", "timestamp", "details"]
        )
        writer.writeheader()
        for log in logs:
            writer.writerow(log)
        buffer.seek(0)
        # utf-8-sig: Excel muestra bien los acentos
        return io.BytesIO(buffer.getvalue().encode("utf-8-sig"))

    def export_applied_recommendations_pdf(
        self, desde: date | None = None, hasta: date | None = None
    ):
        logs = self.get_report_data(desde, hasta)
        buffer = io.BytesIO()

        # Crear documento PDF con ReportLab
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # Encabezado
        elements.append(
            Paragraph("Reporte de Recomendaciones Aplicadas - GxP", styles["Title"])
        )
        elements.append(Spacer(1, 20))

        # Tabla con datos
        data = [["Fecha/Hora", "Usuario", "Acción", "Detalle"]]
        for log in logs:
            data.append([log["timestamp"], log["user"], log["action"], log["details"]])

        table = Table(data, colWidths=[100, 120, 120, 200])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#003366")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ]
            )
        )
        elements.append(table)

        # Pie de página
        elements.append(Spacer(1, 30))
        elements.append(
            Paragraph(
                "Generado por sistema de auditoría – FDA 21 CFR Part 11",
                styles["Normal"],
            )
        )
        elements.append(
            Paragraph(
                "Documento protegido con firma digital simulada.", styles["Italic"]
            )
        )

        doc.build(elements)
        buffer.seek(0)

        # Simulación de firma digital con PyPDF2
        reader = PdfReader(buffer)
        writer = PdfWriter()
        writer.append(reader)

        # Metadatos de firma simulada
        writer.add_metadata(
            {
                "/Signed": "True",
                "/Signer": "Sistema GxP (Simulado)",
                "/Reason": "Auditoría regulatoria - Firma simulada",
                "/Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        # Añadir una página con bloque de firma simulada
        from reportlab.pdfgen import canvas

        sig_buffer = io.BytesIO()
        c = canvas.Canvas(sig_buffer, pagesize=A4)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(100, 700, "Firma Digital Simulada")
        c.setFont("Helvetica", 12)
        c.drawString(100, 680, "Firmado electrónicamente por: Sistema GxP")
        c.drawString(100, 660, "Fecha: " + datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        c.drawString(
            100,
            640,
            "Este documento incluye una firma simulada para fines de demostración.",
        )
        c.save()
        sig_buffer.seek(0)

        sig_reader = PdfReader(sig_buffer)
        writer.append(sig_reader)

        signed_buffer = io.BytesIO()
        writer.write(signed_buffer)
        signed_buffer.seek(0)

        return signed_buffer
