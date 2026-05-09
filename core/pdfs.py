from io import BytesIO

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import Frequencia


def text(value):
    return str(value or '')


def image_or_empty(path, width, height):
    if path.exists():
        return Image(str(path), width=width, height=height)
    return ''


def folha_pdf_bytes(linhas, mes, ano, escola=None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=18,
        leftMargin=18,
        topMargin=18,
        bottomMargin=18,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'FolhaTitle',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
    )
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=6.5, leading=8)
    header_style = ParagraphStyle('Header', parent=cell_style, alignment=TA_CENTER, fontName='Helvetica-Bold')

    nome_mes = dict(Frequencia.MESES_CHOICES).get(mes, mes)
    escola_nome = escola.nome if escola else 'SEMED'
    static_dir = settings.BASE_DIR / 'static' / 'img'
    prefeitura_logo = image_or_empty(static_dir / 'prefeitura-logo.png', 58, 40)
    semed_logo = image_or_empty(static_dir / 'semed-logo.png', 48, 50)
    faixa = image_or_empty(static_dir / 'faixa-ref.png', 700, 4)

    header_table = Table(
        [[
            prefeitura_logo,
            [
                Paragraph('ESTADO DO PARA', title_style),
                Paragraph('PREFEITURA MUNICIPAL DE BREJO GRANDE DO ARAGUAIA - PA', title_style),
                Paragraph('SECRETARIA MUNICIPAL DE EDUCACAO - SEMED', title_style),
                Paragraph('CNPJ: 24.081.014/0001-45', title_style),
            ],
            semed_logo,
        ]],
        colWidths=[95, 550, 95],
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    story = [
        header_table,
        Spacer(1, 8),
        faixa,
        Spacer(1, 18),
        Paragraph(f'DEPARTAMENTO DE PESSOAL - DEPS<br/>DOCENTE E APOIO - {nome_mes.upper()} - {ano}<br/>{escola_nome.upper()}', title_style),
        Spacer(1, 14),
    ]

    data = [[
        Paragraph('N.', header_style),
        Paragraph('NOME POR EXTENSO', header_style),
        Paragraph('VINCULO', header_style),
        Paragraph('CARGO', header_style),
        Paragraph('FUNCAO', header_style),
        Paragraph('FORMACAO', header_style),
        Paragraph('CH 200', header_style),
        Paragraph('CH', header_style),
        Paragraph('FALTAS', header_style),
        Paragraph('OBSERVACOES', header_style),
    ]]

    for index, linha in enumerate(linhas, start=1):
        servidor = linha['servidor']
        frequencia = linha['frequencia']
        carga = servidor.carga_horaria
        data.append([
            Paragraph(str(index), cell_style),
            Paragraph(text(servidor.nome), cell_style),
            Paragraph(text(servidor.vinculo), cell_style),
            Paragraph(text(servidor.cargo), cell_style),
            Paragraph(text(servidor.funcao), cell_style),
            Paragraph(text(servidor.escolaridade), cell_style),
            Paragraph('200' if carga == 200 else '-', cell_style),
            Paragraph(str(carga) if carga and carga != 200 else '-', cell_style),
            Paragraph(text(getattr(frequencia, 'faltas', '')), cell_style),
            Paragraph(text(frequencia.get_observacoes_display()).upper() if frequencia else '', cell_style),
        ])

    table = Table(data, colWidths=[22, 190, 52, 88, 90, 68, 34, 34, 42, 110], repeatRows=1)
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.45, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (6, 0), (8, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(table)
    doc.build(story)
    return buffer.getvalue()
