from io import BytesIO

from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
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
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], alignment=TA_CENTER, fontSize=6.5, leading=8)
    name_cell_style = ParagraphStyle('NameCell', parent=cell_style, alignment=TA_LEFT)
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
            Paragraph(text(servidor.nome), name_cell_style),
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
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(table)
    doc.build(story)
    return buffer.getvalue()


def servidor_ficha_pdf_bytes(servidor, observacoes, eventos):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=22,
        leftMargin=22,
        topMargin=22,
        bottomMargin=22,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('FichaTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=15, leading=18)
    subtitle_style = ParagraphStyle('FichaSub', parent=styles['Normal'], textColor=colors.HexColor('#667085'), fontSize=8.5, leading=11)
    section_style = ParagraphStyle('FichaSection', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9.5, leading=12)
    label_style = ParagraphStyle('FichaLabel', parent=styles['Normal'], textColor=colors.HexColor('#667085'), fontSize=7.5, leading=9)
    value_style = ParagraphStyle('FichaValue', parent=styles['Normal'], fontSize=8.2, leading=10)
    small_style = ParagraphStyle('FichaSmall', parent=styles['Normal'], fontSize=7.5, leading=9)

    def pair(label, value):
        return [Paragraph(label, label_style), Paragraph(text(value) or '-', value_style)]

    story = [
        Paragraph('Ficha funcional', subtitle_style),
        Paragraph(text(servidor.nome), title_style),
        Paragraph(f'{text(servidor.escola.nome)} · {text(servidor.cargo) or "Cargo não informado"}', subtitle_style),
        Spacer(1, 8),
    ]

    resumo = Table([[
        Paragraph(f'<b>Status</b><br/>{ "Ativo" if servidor.ativo else "Inativo" }', value_style),
        Paragraph(f'<b>Vínculo</b><br/>{ text(servidor.vinculo) or "-" }', value_style),
        Paragraph(f'<b>Carga horária</b><br/>{ text(servidor.carga_horaria) or "-" }', value_style),
    ]], colWidths=[175, 175, 175])
    resumo.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#d7dde5')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7fafc')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    story.extend([resumo, Spacer(1, 8)])

    blocos = [
        ('Identificação', [
            pair('CPF', servidor.cpf),
            pair('RG', servidor.rg),
            pair('Sexo', servidor.sexo),
            pair('Nascimento', servidor.data_nascimento.strftime('%d/%m/%Y') if servidor.data_nascimento else '-'),
            pair('Telefone', servidor.telefone),
            pair('Email', servidor.email),
        ]),
        ('Endereço', [
            pair('Logradouro', servidor.logradouro),
            pair('Número', servidor.numero),
            pair('Bairro / Vila', servidor.bairro),
            pair('Zona', servidor.zona),
            pair('Município', servidor.municipio),
            pair('Estado', servidor.estado),
            pair('CEP', servidor.cep),
        ]),
        ('Formação e lotação', [
            pair('Escolaridade', servidor.escolaridade),
            pair('Formação', servidor.formacao),
            pair('Instituição', servidor.instituicao),
            pair('Função', servidor.funcao),
            pair('Cargo', servidor.cargo),
        ]),
        ('Datas', [
            pair('Admissão', servidor.data_admissao.strftime('%d/%m/%Y') if servidor.data_admissao else '-'),
            pair('Início', servidor.data_inicio.strftime('%d/%m/%Y') if servidor.data_inicio else '-'),
            pair('Saída', servidor.data_saida.strftime('%d/%m/%Y') if servidor.data_saida else '-'),
        ]),
    ]

    rows = []
    for titulo, pares in blocos:
        rows.append([Paragraph(titulo, section_style), ''])
        for index in range(0, len(pares), 2):
            esquerda = pares[index]
            direita = pares[index + 1] if index + 1 < len(pares) else ['', '']
            rows.append([
                Paragraph(f'<b>{esquerda[0].getPlainText()}</b>: {esquerda[1].getPlainText()}', small_style),
                Paragraph(f'<b>{direita[0].getPlainText()}</b>: {direita[1].getPlainText()}', small_style) if direita[0] else '',
            ])
    dados_table = Table(rows, colWidths=[262, 262])
    dados_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#d7dde5')),
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eef6f8')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.extend([dados_table, Spacer(1, 8)])

    obs_rows = [[Paragraph('Observações da ficha', section_style)]]
    for observacao in observacoes[:5]:
        data = observacao.criado_em.strftime('%d/%m/%Y %H:%M')
        obs_rows.append([Paragraph(f'<b>{data}</b> · {text(observacao.texto)}', small_style)])
    if len(obs_rows) == 1:
        obs_rows.append([Paragraph('Nenhuma observação manual registrada.', small_style)])
    obs_table = Table(obs_rows, colWidths=[525])
    obs_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#d7dde5')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eef6f8')),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.extend([obs_table, Spacer(1, 8)])

    evento_rows = [[Paragraph('Alterações funcionais', section_style)]]
    for evento in eventos[:5]:
        data = evento['data'].strftime('%d/%m/%Y %H:%M')
        evento_rows.append([Paragraph(f'<b>{data} · {text(evento["titulo"])}</b><br/>{text(evento["texto"])}', small_style)])
    if len(evento_rows) == 1:
        evento_rows.append([Paragraph('Nenhuma alteração de cargo, função ou carga horária registrada.', small_style)])
    evento_table = Table(evento_rows, colWidths=[525])
    evento_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.35, colors.HexColor('#d7dde5')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eef6f8')),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(evento_table)
    doc.build(story)
    return buffer.getvalue()
