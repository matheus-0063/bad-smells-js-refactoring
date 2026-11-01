"""Gera o relatório a partir do Markdown e das saídas reais de validação."""

import json
import re
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image as PILImage, ImageDraw, ImageFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle, XPreformatted,
)

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / 'docs'
EVIDENCE = DOCS / 'evidencias'
OUTPUT = ROOT / 'output' / 'pdf' / 'relatorio-bad-smells.pdf'
DATA = json.loads((DOCS / 'dados-relatorio.json').read_text())
METRICS = json.loads((EVIDENCE / 'resumo.json').read_text())
INK = colors.HexColor('#172b45')
BLUE = colors.HexColor('#185b8c')
LIGHT = colors.HexColor('#edf3f8')
FONT_DIRECTORY = Path('/System/Library/Fonts/Supplemental')
SANS, SANS_BOLD, MONO = 'Helvetica', 'Helvetica-Bold', 'Courier'
if (FONT_DIRECTORY / 'Arial.ttf').exists():
    for name, filename in [
        ('ReportSans', 'Arial.ttf'),
        ('ReportSans-Bold', 'Arial Bold.ttf'),
        ('ReportSans-Italic', 'Arial Italic.ttf'),
        ('ReportMono', 'Courier New.ttf'),
    ]:
        pdfmetrics.registerFont(TTFont(name, str(FONT_DIRECTORY / filename)))
    pdfmetrics.registerFontFamily('ReportSans', normal='ReportSans',
                                  bold='ReportSans-Bold', italic='ReportSans-Italic',
                                  boldItalic='ReportSans-Bold')
    SANS, SANS_BOLD, MONO = 'ReportSans', 'ReportSans-Bold', 'ReportMono'


def render_terminal_output():
    """Cria uma imagem legível da saída capturada; não simula uma UI."""
    content = (EVIDENCE / 'eslint-antes.txt').read_text().strip()
    lines = []
    for line in content.splitlines():
        lines.extend(textwrap.wrap(line, 112, subsequent_indent='    ') or [''])
    font_path = Path('/System/Library/Fonts/Menlo.ttc')
    font = ImageFont.truetype(str(font_path), 19) if font_path.exists() else ImageFont.load_default(size=19)
    image = PILImage.new('RGB', (1440, 96 + len(lines) * 31), '#13243a')
    draw = ImageDraw.Draw(image)
    draw.text((28, 20), 'ESLint | saída real do código original', font=font, fill='#89c5ff')
    for index, line in enumerate(lines):
        draw.text((28, 68 + index * 31), line, font=font, fill='#edf4ff')
    image.save(EVIDENCE / 'eslint-antes.png')


def rich(text):
    text = escape(text)
    text = re.sub(r'`([^`]+)`', rf'<font name="{MONO}" size="8.4">\1</font>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', text)
    return text


STYLES = getSampleStyleSheet()
STYLES.add(ParagraphStyle('Text', fontName=SANS, fontSize=9.4, leading=12.8,
                          textColor=INK, spaceAfter=7))
STYLES.add(ParagraphStyle('Section', parent=STYLES['Text'], fontName=SANS_BOLD,
                          fontSize=16, leading=20, textColor=BLUE, spaceAfter=12,
                          spaceBefore=7, keepWithNext=True))
STYLES.add(ParagraphStyle('Subsection', parent=STYLES['Text'], fontName=SANS_BOLD,
                          fontSize=11, leading=14, spaceBefore=8, spaceAfter=7,
                          keepWithNext=True))
STYLES.add(ParagraphStyle('ListItem', parent=STYLES['Text'], leftIndent=10,
                          firstLineIndent=-7, spaceAfter=5))
STYLES.add(ParagraphStyle('CodeBlock', fontName=MONO, fontSize=8,
                          leading=10.5, backColor=LIGHT, borderPadding=9,
                          spaceBefore=4, spaceAfter=12, textColor=INK))
STYLES.add(ParagraphStyle('Caption', parent=STYLES['Text'], fontSize=8,
                          leading=10.4, textColor=colors.HexColor('#536579')))
STYLES.add(ParagraphStyle('CoverTitle', fontName=SANS_BOLD, fontSize=28,
                          leading=34, textColor=INK, spaceAfter=24))
STYLES.add(ParagraphStyle('CoverLabel', parent=STYLES['Text'], fontSize=11,
                          leading=17, textColor=BLUE, spaceAfter=14))
STYLES.add(ParagraphStyle('CoverText', parent=STYLES['Text'], fontSize=12,
                          leading=20, spaceAfter=10))
STYLES.add(ParagraphStyle('Metric', fontName=SANS_BOLD, fontSize=21,
                          leading=27, textColor=BLUE, alignment=TA_CENTER))
STYLES.add(ParagraphStyle('MetricLabel', parent=STYLES['Text'], fontSize=8.5,
                          leading=11, alignment=TA_CENTER))


def table_from_markdown(lines):
    rows = [[cell.strip() for cell in line.strip().strip('|').split('|')] for line in lines]
    rows = [row for row in rows if not all(re.fullmatch(r'[-: ]+', cell) for cell in row)]
    cells = [[Paragraph(rich(cell), STYLES['Text']) for cell in row] for row in rows]
    table = Table(cells, colWidths=[254, 130, 127], repeatRows=1, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT),
        ('LINEBELOW', (0, 0), (-1, 0), 1, BLUE),
        ('LINEBELOW', (0, 1), (-1, -1), 0.35, colors.HexColor('#d7e0e9')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    return table


def markdown_story():
    lines = (DOCS / 'RELATORIO.md').read_text().splitlines()
    story = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line == '<!-- pagebreak -->':
            story.append(PageBreak())
        elif line.startswith('```'):
            code = []
            index += 1
            while not lines[index].startswith('```'):
                code.append(lines[index])
                index += 1
            story.append(KeepTogether([XPreformatted(escape('\n'.join(code)), STYLES['CodeBlock'])]))
        elif line.startswith('|'):
            table_lines = []
            while index < len(lines) and lines[index].startswith('|'):
                table_lines.append(lines[index])
                index += 1
            story.extend([table_from_markdown(table_lines), Spacer(1, 10)])
            continue
        elif line.startswith('!['):
            path = DOCS / re.search(r'\]\((.+)\)', line)[1]
            with PILImage.open(path) as source:
                height = 511 * source.height / source.width
            story.extend([Spacer(1, 3), Image(str(path), width=511, height=height), Spacer(1, 7)])
        elif line.startswith('## '):
            story.append(Paragraph(rich(line[3:]), STYLES['Subsection']))
        elif line.startswith('# '):
            story.append(Paragraph(rich(line[2:]), STYLES['Section']))
        elif line.startswith('- '):
            story.append(Paragraph('- ' + rich(line[2:]), STYLES['ListItem']))
        else:
            style = STYLES['Caption'] if line.startswith('*Figura') else STYLES['Text']
            story.append(Paragraph(rich(line), style))
        index += 1
    return story


def page_decoration(canvas, document):
    canvas.saveState()
    canvas.setStrokeColor(BLUE)
    canvas.setLineWidth(2)
    canvas.line(42, A4[1] - 30, A4[0] - 42, A4[1] - 30)
    canvas.setFont(SANS, 8)
    canvas.setFillColor(colors.HexColor('#617389'))
    canvas.drawString(42, 24, f"{DATA['disciplina']} | {DATA['nome']}")
    canvas.drawRightString(A4[0] - 42, 24, f'{document.page}')
    canvas.restoreState()


def generate():
    assert METRICS['passedTests'] == METRICS['totalTests'] == 33
    assert METRICS['refactoredLintErrors'] == 0
    render_terminal_output()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    story = [Spacer(1, 76), Paragraph(DATA['disciplina'].upper(), STYLES['CoverLabel']),
             Paragraph(DATA['titulo'], STYLES['CoverTitle']),
             Paragraph('Relatório de análise e refatoração de código JavaScript', STYLES['CoverLabel']),
             Spacer(1, 34),
             Paragraph(f"<b>Aluno:</b> {DATA['nome']}", STYLES['CoverText']),
             Paragraph(f"<b>Matrícula:</b> {DATA['matricula']}", STYLES['CoverText']),
             Paragraph(f"<b>Data:</b> {DATA['data']}", STYLES['CoverText']), Spacer(1, 44)]
    values = ['33/33', '27 → 2', '0']
    labels = ['testes aprovados', 'complexidade do método', 'erros na versão refatorada']
    metrics = Table([
        [Paragraph(value.replace('→', '-&gt;'), STYLES['Metric']) for value in values],
        [Paragraph(label, STYLES['MetricLabel']) for label in labels],
    ], colWidths=[170, 170, 171])
    metrics.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT),
        ('TOPPADDING', (0, 0), (-1, 0), 15),
        ('BOTTOMPADDING', (0, -1), (-1, -1), 12),
    ]))
    story.extend([metrics, Spacer(1, 28),
                  Paragraph('<b>Repositório da entrega</b>', STYLES['Text']),
                  Paragraph(f'<link href="{DATA["repositorio"]}">{DATA["repositorio"]}</link>', STYLES['Text']),
                  PageBreak()])
    story.extend(markdown_story())
    document = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=42,
                                 leftMargin=42, topMargin=43, bottomMargin=43,
                                 title=DATA['titulo'], author=DATA['nome'])
    document.build(story, onFirstPage=page_decoration, onLaterPages=page_decoration)
    print(OUTPUT)


if __name__ == '__main__':
    generate()
