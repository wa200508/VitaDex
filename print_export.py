"""Offline, single-card print proofs with complete fact/reference appendices."""

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4
from xml.sax.saxutils import escape

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

FONT_DIR = Path(__file__).parent / 'assets' / 'fonts'
TRIM_WIDTH, TRIM_HEIGHT = 180, 252  # 2.5 x 3.5 inches, 72 points/inch
BLEED = 9  # 0.125 inches


@dataclass(frozen=True)
class ExportResult:
    path: Path
    warnings: tuple[str, ...]


def register_fonts():
    if 'VitaDex' not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont('VitaDex', str(FONT_DIR / 'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('VitaDexBold', str(FONT_DIR / 'DejaVuSans-Bold.ttf')))


def artwork_path(card, root):
    root = Path(root).resolve()
    for value in (card.local_art_asset, card.photo_asset):
        if value:
            path = (root / value).resolve()
            if path.is_relative_to(root) and path.is_file():
                return path
    return None


def export_card(card, root, destination, paper='Letter'):
    """Create a front/back proof and full reference pages, without fetching anything."""
    if paper not in ('Letter', 'A4'):
        raise ValueError('Choose Letter or A4 paper.')
    register_fonts()
    entry = card.organism
    fields = [('Description', entry.description), ('Habitat', entry.habitat),
              ('Size', entry.physical_dimensions), ('Ecological role', entry.environment_role),
              ('Safety', entry.safety_message), ('Notes', entry.notes)]
    # Fail explicitly instead of silently producing missing-glyph squares.
    strings = [entry.name, entry.scientific_name, card.observed_at] + [v for _, v in fields]
    strings += list(entry.references)
    glyphs = pdfmetrics.getFont('VitaDex').face.charToGlyph
    if any(ord(char) not in glyphs for value in strings for char in value if not char.isspace()):
        raise ValueError('This card contains characters not supported by the print font yet.')
    status = ('FICTIONAL DEMO' if entry.is_demo else
              'REVIEWED FACTS / SUGGESTED ID' if entry.review_status == 'reviewed' else
              'DRAFT FACTS / SUGGESTED ID')
    warnings = ['Print at actual size (100%). Confirm duplex alignment and paper requirements with your printer.']
    art = artwork_path(card, root)
    if art is None:
        warnings.append('No local artwork is available; the front uses a blank illustration panel.')
    else:
        with Image.open(art) as image:
            if min(image.width / (156 / 72), image.height / (130 / 72)) < 300:
                warnings.append('Artwork may print softly at this size (below 300 dpi).')
    page_size = letter if paper == 'Letter' else A4
    body_style = ParagraphStyle('Body', fontName='VitaDex', fontSize=10, leading=15,
                                spaceAfter=10, splitLongWords=True)
    heading_style = ParagraphStyle('Heading', parent=body_style, fontName='VitaDexBold',
                                   fontSize=15, leading=20, spaceBefore=12)
    tiny_style = ParagraphStyle('Card', fontName='VitaDex', fontSize=8, leading=11)

    def paragraph(text, style=body_style):
        return Paragraph(escape(text).replace('\n', '<br/>'), style)

    def fitted(canvas, text, x, top, width, max_height, bold=False):
        for size in range(15 if bold else 10, 6, -1):
            style = ParagraphStyle('fit', fontName='VitaDexBold' if bold else 'VitaDex',
                                   fontSize=size, leading=size * 1.25)
            item = paragraph(text, style)
            _, height = item.wrap(width, max_height)
            if height <= max_height:
                item.drawOn(canvas, x, top - height)
                return
        raise ValueError('Card title is too long to print legibly.')

    def draw_page(canvas, document):
        page = canvas.getPageNumber()
        canvas.saveState()
        canvas.setFont('VitaDex', 8)
        canvas.setFillColor(colors.HexColor('#52636a'))
        canvas.drawString(36, 22, f'VitaDex print proof | {paper} | page {page}')
        if page > 2:
            canvas.restoreState()
            return
        x, y = (page_size[0] - TRIM_WIDTH) / 2, (page_size[1] - TRIM_HEIGHT) / 2
        canvas.setFillColor(colors.HexColor('#e5f1e9'))
        canvas.rect(x - BLEED, y - BLEED, TRIM_WIDTH + 2 * BLEED,
                    TRIM_HEIGHT + 2 * BLEED, stroke=0, fill=1)
        canvas.setStrokeColor(colors.HexColor('#536c60'))
        canvas.setLineWidth(.4)
        for dx in (0, TRIM_WIDTH):
            for dy in (0, TRIM_HEIGHT):
                sign_x, sign_y = (-1 if dx == 0 else 1), (-1 if dy == 0 else 1)
                canvas.line(x + dx + sign_x * 11, y + dy, x + dx + sign_x * 20, y + dy)
                canvas.line(x + dx, y + dy + sign_y * 11, x + dx, y + dy + sign_y * 20)
        canvas.setFillColor(colors.HexColor('#153b2a'))
        fitted(canvas, entry.name, x + 12, y + 237, 156, 38, bold=True)
        if page == 1:
            canvas.setFillColor(colors.HexColor('#ffffff'))
            canvas.rect(x + 12, y + 55, 156, 130, stroke=0, fill=1)
            if art:
                canvas.drawImage(str(art), x + 12, y + 55, width=156, height=130,
                                 preserveAspectRatio=True, anchor='c', mask='auto')
            canvas.setFillColor(colors.HexColor('#153b2a'))
            fitted(canvas, entry.scientific_name or 'VitaDex sample', x + 12, y + 45, 156, 24)
        else:
            # Keep a fixed readable excerpt; complete facts are always in the appendix.
            summary = entry.description
            if len(summary) > 210:
                summary = summary[:207].rsplit(' ', 1)[0] + '...'
            item = paragraph(summary, tiny_style)
            _, height = item.wrap(156, 125)
            if height > 125:
                raise ValueError('Description cannot fit the card back.')
            item.drawOn(canvas, x + 12, y + 183 - height)
            fitted(canvas, f'Fact revision {entry.revision}\nFull facts and sources: attached guide.',
                   x + 12, y + 55, 156, 35)
        canvas.setFont('VitaDexBold', 6)
        canvas.drawString(x + 12, y + 10, status)
        canvas.setFont('VitaDex', 9)
        canvas.drawCentredString(page_size[0] / 2, y - 38,
                                'FRONT' if page == 1 else 'BACK - test duplex alignment first')
        canvas.drawCentredString(page_size[0] / 2, y - 54,
                                'Trim 2.5 x 3.5 in | bleed 0.125 in | print at 100%')
        canvas.restoreState()

    story = [Spacer(1, 1), PageBreak(), Spacer(1, 1), PageBreak(),
             paragraph(entry.name + ' - field guide', heading_style), paragraph(status),
             paragraph(f'Fact revision: {entry.revision}. Recorded: {card.observed_at or "not recorded"}.')]
    for label, value in fields:
        if value:
            story.extend([paragraph(label, heading_style), paragraph(value)])
    story.append(paragraph('References and attribution', heading_style))
    if entry.references:
        for index, source in enumerate(entry.references, 1):
            topics = [field for field, sources in entry.fact_sources.items() if source in sources]
            story.append(paragraph(f'[{index}] {source}' + (f' | Fields: {", ".join(topics)}' if topics else '')))
    else:
        story.append(paragraph('No scientific references recorded.'))
    story.append(paragraph('Printing notes', heading_style))
    story.extend(paragraph(warning) for warning in warnings)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(f'.{destination.name}.{uuid4().hex}.tmp')
    try:
        document = SimpleDocTemplate(str(temporary), pagesize=page_size, leftMargin=42,
                                     rightMargin=42, topMargin=42, bottomMargin=42,
                                     title=f'VitaDex - {entry.name}', author='VitaDex')
        document.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return ExportResult(destination, tuple(warnings))
