"""Esportazioni Word e PDF semplici ma strutturate (titoli, paragrafi, tabelle)."""
from __future__ import annotations
from pathlib import Path
import re


def _iter_blocks(content: str):
    """Parser markdown MINIMO: supporta solo il sottoinsieme prodotto dal renderer."""
    lines = content.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith('|'):
            raw = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                raw.append([x.strip() for x in lines[i].strip().strip('|').split('|')])
                i += 1
            rows = [r for r in raw if not all(re.fullmatch(r':?-+:?', x) for x in r)]
            if rows:
                yield 'table', rows
            continue
        if line.startswith('### '):
            yield 'h3', line[4:]
        elif line.startswith('## '):
            yield 'h2', line[3:]
        elif line.startswith('# '):
            yield 'h1', line[2:]
        elif line.startswith('- '):
            yield 'bullet', line[2:]
        elif line.startswith('> '):
            yield 'quote', line[2:]
        else:
            yield 'paragraph', line
        i += 1


def _plain(text: str) -> str:
    return text.replace('  ', ' ').replace('\\|', '|').replace('**', '').replace('*', '')


def _docx_paragraph(paragraph, text):
    parts = re.split(r'(\*\*.*?\*\*)', text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            run = paragraph.add_run(part[2:-2]); run.bold = True
        else:
            paragraph.add_run(_plain(part))


def markdown_to_docx(content: str, target: Path) -> None:
    try:
        from docx import Document
        from docx.shared import Cm, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError as exc:
        raise RuntimeError("Per Word: pip install '.[documents]'") from exc
    document = Document()
    section = document.sections[0]
    section.top_margin, section.bottom_margin = Cm(1.75), Cm(1.75)
    section.left_margin, section.right_margin = Cm(2.2), Cm(2.2)
    normal = document.styles['Normal']
    normal.font.name = 'Aptos'
    normal.font.size = Pt(9.3)
    normal.paragraph_format.space_after = Pt(4)
    normal.paragraph_format.line_spacing = 1.13
    for level in (1, 2, 3):
        style = document.styles[f'Heading {level}']
        style.font.name = 'Aptos Display'
        style.font.color.rgb = RGBColor(27, 61, 95)
        style.font.size = Pt({1: 15, 2: 12, 3: 10.5}[level])
        style.paragraph_format.space_before = Pt({1: 0, 2: 9, 3: 7}[level])
        style.paragraph_format.space_after = Pt(4)
    for kind, value in _iter_blocks(content):
        if kind.startswith('h'):
            document.add_heading(_plain(value), level=int(kind[1]))
        elif kind == 'table':
            widths = len(value[0])
            tbl = document.add_table(rows=1, cols=widths)
            tbl.style = 'Table Grid'
            for j, title in enumerate(value[0]):
                tbl.rows[0].cells[j].text = _plain(title)
                for r in tbl.rows[0].cells[j].paragraphs[0].runs:
                    r.bold = True; r.font.size = Pt(8)
            for row in value[1:]:
                cells = tbl.add_row().cells
                for j in range(widths):
                    cells[j].text = _plain(row[j] if j < len(row) else '')
                    for p in cells[j].paragraphs:
                        p.paragraph_format.space_after = Pt(1)
                        for r in p.runs:
                            r.font.size = Pt(8)
            document.add_paragraph().paragraph_format.space_after = Pt(0)
        else:
            if kind == 'bullet':
                p = document.add_paragraph(style='List Bullet')
            else:
                p = document.add_paragraph()
            if kind == 'quote':
                p.style = 'Quote'
            _docx_paragraph(p, value)
    footer = section.footer.paragraphs[0]
    footer.text = 'VERBALIA OPEN — Documento in bozza da verificare'
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in footer.runs:
        run.font.size = Pt(7)
    document.save(target)


def markdown_to_pdf(content: str, target: Path) -> None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError as exc:
        raise RuntimeError("Per PDF: pip install '.[documents]'") from exc
    from xml.sax.saxutils import escape
    font = 'Helvetica'
    installed = Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
    if installed.exists():
        pdfmetrics.registerFont(TTFont('VerbaliaSans', str(installed)))
        font = 'VerbaliaSans'
    styles = getSampleStyleSheet()
    body = ParagraphStyle('VerbaliaBody', parent=styles['BodyText'], fontName=font, fontSize=8.5, leading=12, spaceAfter=4)
    title = ParagraphStyle('VerbaliaTitle', parent=body, textColor=colors.HexColor('#1B3D5F'), fontSize=14, leading=18, spaceAfter=10)
    h2 = ParagraphStyle('VerbaliaHeading2', parent=body, textColor=colors.HexColor('#1B3D5F'), fontSize=11, leading=14, spaceBefore=10, spaceAfter=5)
    h3 = ParagraphStyle('VerbaliaHeading3', parent=body, textColor=colors.HexColor('#1B3D5F'), fontSize=9.3, leading=12, spaceBefore=8, spaceAfter=4)
    note = ParagraphStyle('VerbaliaNote', parent=body, fontSize=7.5, leading=10, textColor=colors.HexColor('#555555'))
    width = A4[0] - 84
    story = []
    def pdf_text(t):
        t = escape(t.replace('\\|', '|'))
        return re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', t)
    for kind, value in _iter_blocks(content):
        if kind == 'table':
            colnum = len(value[0])
            t = Table([[Paragraph(pdf_text(x), body) for x in row] for row in value], colWidths=[width / colnum] * colnum, repeatRows=1, hAlign='LEFT')
            t.setStyle(TableStyle([('GRID', (0, 0), (-1, -1), .3, colors.HexColor('#C9D4DF')), ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E9EFF6')), ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3)]))
            story.append(t); story.append(Spacer(1, 5))
        else:
            style = {'h1':title,'h2':h2,'h3':h3,'quote':note}.get(kind, body)
            if kind == 'bullet':
                value = '• ' + value
            story.append(Paragraph(pdf_text(value), style))
    doc = SimpleDocTemplate(str(target), pagesize=A4, leftMargin=42, rightMargin=42, topMargin=38, bottomMargin=38)
    doc.build(story)
