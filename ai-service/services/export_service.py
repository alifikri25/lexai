"""
Export Service
Generate PDF report from analysis results using ReportLab
"""
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY


def create_analysis_pdf(title: str, summary: str, clauses: list, risk_score: int) -> bytes:
    """Generate a PDF report from analysis results."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=18,
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=10,
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#16213e'),
        spaceBefore=15,
        spaceAfter=8,
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
    )
    
    story = []
    
    # Title
    story.append(Paragraph("📋 LexAI - Laporan Analisis Dokumen", title_style))
    story.append(Spacer(1, 5 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#0f3460')))
    story.append(Spacer(1, 5 * mm))
    
    # Document title
    story.append(Paragraph(f"<b>Dokumen:</b> {title}", body_style))
    story.append(Spacer(1, 3 * mm))
    
    # Risk score
    risk_color = '#27ae60' if risk_score < 33 else '#f39c12' if risk_score < 66 else '#e74c3c'
    story.append(Paragraph(
        f'<b>Skor Risiko:</b> <font color="{risk_color}"><b>{risk_score}/100</b></font>',
        body_style
    ))
    story.append(Spacer(1, 8 * mm))
    
    # Summary
    story.append(Paragraph("Ringkasan Dokumen", heading_style))
    story.append(Paragraph(summary, body_style))
    story.append(Spacer(1, 8 * mm))
    
    # Clauses analysis
    story.append(Paragraph("Analisis Klausul", heading_style))
    story.append(Spacer(1, 3 * mm))
    
    for clause in clauses:
        risk_level = clause.get('risk_level', 'low')
        if risk_level == 'high':
            badge = '<font color="#e74c3c"><b>🔴 RISIKO TINGGI</b></font>'
        elif risk_level == 'medium':
            badge = '<font color="#f39c12"><b>🟡 RISIKO SEDANG</b></font>'
        else:
            badge = '<font color="#27ae60"><b>🟢 RISIKO RENDAH</b></font>'
        
        clause_title = clause.get('title', f"Klausul {clause.get('number', '')}")
        story.append(Paragraph(f"<b>{clause.get('number', '')}. {clause_title}</b> — {badge}", body_style))
        story.append(Spacer(1, 2 * mm))
        
        clause_text = clause.get('text', '')
        if clause_text:
            story.append(Paragraph(f"<i>\"{clause_text[:300]}{'...' if len(clause_text) > 300 else ''}\"</i>", body_style))
            story.append(Spacer(1, 2 * mm))
        
        explanation = clause.get('explanation', '')
        if explanation:
            story.append(Paragraph(f"<b>Analisis:</b> {explanation}", body_style))
        
        story.append(Spacer(1, 5 * mm))
        story.append(HRFlowable(width="80%", thickness=0.5, color=colors.lightgrey))
        story.append(Spacer(1, 3 * mm))
    
    # Footer
    story.append(Spacer(1, 10 * mm))
    footer_style = ParagraphStyle(
        'Footer', parent=styles['Normal'],
        fontSize=8, textColor=colors.grey, alignment=TA_CENTER,
    )
    story.append(Paragraph(
        "Laporan ini dihasilkan oleh LexAI — AI Copilot untuk Praktisi Hukum Indonesia. "
        "Hasil analisis bersifat bantuan dan tidak menggantikan konsultasi hukum profesional.",
        footer_style
    ))
    
    doc.build(story)
    return buffer.getvalue()
