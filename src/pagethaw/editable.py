"""Flowing Word output for single-column forms, without positioned text boxes.

This deliberately supports less than the layout renderer. PDF line/span provenance
is kept until emission; ambiguous columns, grids and text/graphic overlays fail.
No PDF-specific names, wording or fonts are used to reconstruct the document.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import io
import re
from statistics import median

import pymupdf
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor
from .ruled_tables import find_grids, partition
from .text_spacing import TextSpacing


class UnsupportedLayout(ValueError):
    pass


def reject(detail):
    raise UnsupportedLayout('Editable mode: '+detail+' Use Preserve layout for this PDF.')


@dataclass
class Line:
    spans: list
    bbox: pymupdf.Rect
    block: int

    @property
    def text(self):
        return ''.join(c['c'] for s in self.spans for c in s['chars'])

    @property
    def size(self):
        return max(s['size'] for s in self.spans)

    @property
    def field(self):
        return bool(re.search(r'(?<!\w)_{3,}(?!\w)', self.text))

    @property
    def bold(self):
        return all(s['flags'] & 16 for s in self.spans if any(c['c'].strip() for c in s['chars']))


def cancelled(event):
    if event and event.is_set():
        raise InterruptedError('Conversion cancelled.')


def lines_on(page):
    lines = []
    for bi, block in enumerate(page.get_text('rawdict')['blocks']):
        for raw in block.get('lines', []):
            spans = [s for s in raw['spans'] if s['chars']]
            if not spans:
                continue
            # PDF engines can expose horizontally separated portions of one row
            # as separate lines. Combine only the same block and baseline.
            y = spans[0]['origin'][1]
            same = next((l for l in reversed(lines) if l.block == bi and
                         abs(l.spans[0]['origin'][1]-y) < .5), None)
            if same:
                same.spans.extend(spans)
                same.spans.sort(key=lambda s: s['origin'][0])
                same.bbox |= pymupdf.Rect(raw['bbox'])
            else:
                lines.append(Line(spans, pymupdf.Rect(raw['bbox']), bi))
    return sorted(lines, key=lambda l: (round(l.bbox.y0, 1), l.bbox.x0))


def intersects(a, b, tolerance=.5):
    r = a & b
    return r.width > tolerance and r.height > tolerance


def contains(outer, inner, tolerance=1):
    return (outer+(-tolerance, -tolerance, tolerance, tolerance)).contains(inner)


def graphics_on(page, lines):
    """Separate simple outer boxes/rules from standalone graphics such as logos."""
    boxes, rules, rects = [], [], []
    drawings = page.get_drawings()
    grids = find_grids(drawings)
    handled = {index for g in grids for index in g.drawings}
    for index, draw in enumerate(drawings):
        if index in handled:
            continue
        rect = pymupdf.Rect(draw['rect'])
        items = draw['items']
        if draw['type'] == 's' and len(items) == 1 and items[0][0] == 're' and rect.width > 40 and rect.height > 25:
            boxes.append(rect)
        elif draw['type'] == 's' and rect.height < 1 and rect.width > 20:
            rules.append(rect)
        else:
            if rect.is_empty and (rect.width > .1 or rect.height > .1):
                reject('vertical or degenerate drawing paths are not supported.')
            rects.append(rect)
    rects.extend(pymupdf.Rect(i['bbox']) for i in page.get_image_info())
    for i, grid in enumerate(grids):
        if any(intersects(grid.bbox, other.bbox) for other in grids[i+1:]):
            reject('nested or overlapping table borders are not supported.')
        if any(grid.bbox.intersects(r+(-.1, -.1, .1, .1)) for r in boxes+rules+rects):
            reject('a ruled table contains unsupported graphics.')
        if any(min(l.bbox.y1, grid.bbox.y1)-max(l.bbox.y0, grid.bbox.y0) > 1 and
               (l.bbox.x1 < grid.bbox.x0 or l.bbox.x0 > grid.bbox.x1) for l in lines):
            reject('text beside a ruled table needs manual reconstruction.')
    for i, box in enumerate(boxes):
        if any(intersects(box, other) for other in boxes[i+1:]):
            reject('nested or overlapping table borders are not supported.')
        if any(intersects(box, r) or (box.y0 < r.y0 < box.y1 and r.x1 > box.x0 and r.x0 < box.x1) for r in rects+rules):
            reject('a table grid or graphics inside a bordered form need manual reconstruction.')
        if any(intersects(box, l.bbox) and not contains(box, l.bbox) for l in lines):
            reject('text crosses a form border.')
    # Join adjacent vector glyphs into one embedded logo. Text is never rasterized.
    clusters = []
    for rect in rects:
        if rect.is_empty:
            continue
        merged = rect
        again = True
        while again:
            again = False
            for old in list(clusters):
                if intersects(merged+(-10, -4, 10, 4), old):
                    merged |= old
                    clusters.remove(old)
                    again = True
        clusters.append(merged)
    for rect in clusters:
        if any(intersects(rect, l.bbox) for l in lines if l.text.strip()):
            reject('graphics overlap selectable text.')
        if rect.height > page.rect.height*.5:
            reject('a large graphic needs manual placement.')
    return boxes, rules, clusters, grids


def check_columns(lines):
    """Reject sustained column gaps, including fragments merged by PDF extraction."""
    blocks = {}
    for line in lines:
        blocks[line.block] = blocks.get(line.block, pymupdf.Rect(line.bbox)) | line.bbox
    values = list(blocks.values())
    for i, a in enumerate(values):
        for b in values[i+1:]:
            if min(a.y1, b.y1)-max(a.y0, b.y0) > 18 and (a.x1+8 < b.x0 or b.x1+8 < a.x0):
                reject('multiple body columns are not supported.')
    rows = {}
    for line in lines:
        if line.field or line.text.strip().startswith('('):
            continue
        baseline = round(line.spans[0]['origin'][1])
        rows.setdefault(baseline, []).extend((c, s['size']) for s in line.spans for c in s['chars'] if c['c'].strip())
    gaps = []
    for y, chars in rows.items():
        chars.sort(key=lambda pair: pair[0]['bbox'][0])
        for (a, size), (b, _) in zip(chars, chars[1:]):
            if b['bbox'][0]-a['bbox'][2] > max(24, size*3):
                gaps.append((y, a['bbox'][2], b['bbox'][0]))
    for y, x0, x1 in gaps:
        matching = {yy for yy, a, b in gaps if min(b, x1)-max(a, x0) > 12 and abs(yy-y) < 100}
        if len(matching) >= 3:
            reject('multiple body columns are not supported.')


def element(name, **attrs):
    node = OxmlElement('w:'+name)
    for key, value in attrs.items():
        node.set(qn('w:'+key), str(value))
    return node


def cell_margins(cell, value=0):
    pr = cell._tc.get_or_add_tcPr()
    for old in pr.findall(qn('w:tcMar')):
        pr.remove(old)
    margins = element('tcMar')
    for edge in ('top', 'left', 'bottom', 'right'):
        margins.append(element(edge, w=value, type='dxa'))
    pr.append(margins)


def cell_borders(cell, borders):
    pr = cell._tc.get_or_add_tcPr()
    for old in pr.findall(qn('w:tcBorders')):
        pr.remove(old)
    pr.insert_element_before(borders, 'w:shd', 'w:noWrap', 'w:tcMar', 'w:textDirection',
                             'w:tcFitText', 'w:vAlign', 'w:hideMark', 'w:headers',
                             'w:cellIns', 'w:cellDel', 'w:cellMerge', 'w:tcPrChange')


def table_at(parent, widths, border=False):
    if hasattr(parent, 'sections'):
        table = parent.add_table(rows=1, cols=len(widths))
    else:
        table = parent.add_table(rows=1, cols=len(widths))
        # Word requires a final paragraph in every cell. It should not add a
        # default-sized blank line after each nested form row.
        tail = parent.paragraphs[-1]
        tail.paragraph_format.space_after = Pt(0)
        tail.paragraph_format.line_spacing = Pt(.05)
        tail.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        tail.add_run().font.size = Pt(1)
    table.autofit = False
    pr = table._tbl.tblPr
    pr.append(element('tblInd', w=0, type='dxa'))
    borders = element('tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        borders.append(element(edge, val='single' if border and edge[:6] != 'inside' else 'nil', sz=6, color='000000'))
    pr.append(borders)
    for col, cell, width in zip(table.columns, table.rows[0].cells, widths):
        col.width = cell.width = Pt(width)
        cell_margins(cell, 50 if border else 0)
    return table


def table_separator(parent):
    # Adjacent tables in Word merge into a single grid unless a paragraph
    # separates them; that changes the widths of unrelated form fields.
    p = parent.add_paragraph() if hasattr(parent, 'sections') else parent.paragraphs[-1]
    p.paragraph_format.space_before = p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = Pt(.05)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    p.add_run().font.size = Pt(1)
    return p


class Writer:
    def __init__(self, doc, mapping, width, left, dpi, cancel):
        self.doc, self.mapping = doc, mapping
        self.width, self.left, self.dpi, self.cancel = width, left, dpi, cancel
        self.expected = []
        self.field_count = 0
        self.last_field = None
        self.spacing = TextSpacing(mapping)

    def text_metrics(self, para, lines, responsive=True):
        """Set paragraph-mark metrics too, including empty form/caption cells."""
        span = max((s for line in lines for s in line.spans), key=lambda s: s['size'])
        face = self.mapping[span['font']]
        pr = para._p.get_or_add_pPr()
        mark = element('rPr')
        mark.append(element('rFonts', ascii=face.family, hAnsi=face.family, eastAsia=face.family, cs=face.family))
        mark.append(element('b', val=int(face.bold)))
        mark.append(element('i', val=int(face.italic)))
        mark.append(element('sz', val=round(span['size']*2)))
        mark.append(element('szCs', val=round(span['size']*2)))
        pr.append(mark)
        multiple = self.spacing.multiple(lines) if responsive else None
        if multiple is not None:
            para.paragraph_format.line_spacing = multiple

    def run(self, para, span, text):
        face = self.mapping[span['font']]
        run = para.add_run(text)
        run.font.name = face.family
        fonts = run._r.get_or_add_rPr().rFonts
        for attr in ('ascii', 'hAnsi', 'eastAsia', 'cs'):
            fonts.set(qn('w:'+attr), face.family)
        run.bold, run.italic = face.bold, face.italic
        run.underline = bool(span.get('underline'))
        run.font.size = Pt(span['size'])
        run.font.color.rgb = RGBColor.from_string(f"{span['color']:06X}")
        run._r.get_or_add_rPr().append(element('kern', val=1))
        self.expected.extend((c, face.family, face.bold, face.italic) for c in text if not c.isspace())
        return run

    def paragraph(self, parent, size, before=0):
        if not hasattr(parent, 'sections') and len(parent.paragraphs) == 1 and not parent.paragraphs[0].text and not len(parent.tables):
            para = parent.paragraphs[0]
        else:
            para = parent.add_paragraph()
        pf = para.paragraph_format
        pf.space_before = Pt(max(0, min(before, 18)))
        pf.space_after = Pt(0)
        pf.line_spacing = Pt(size*1.2)
        pf.line_spacing_rule = WD_LINE_SPACING.AT_LEAST
        pf.widow_control = True
        return para

    def text(self, parent, lines, before=0, title=False, left=None, width=None):
        self.last_field = None
        para = self.paragraph(parent, max(l.size for l in lines), before)
        first = lines[0]
        left = self.left if left is None else left
        width = self.width if width is None else width
        pf = para.paragraph_format
        starts = [l.bbox.x0 for l in lines]
        ends = [l.bbox.x1 for l in lines]
        centers = [(a+b)/2 for a, b in zip(starts, ends)]
        tolerance = max(2, first.size*.4)
        if title:
            para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        elif len(lines) == 1 and re.fullmatch(r'(?:[-–—.·=]\s*){5,}', first.text.strip()):
            # Decorative separators have no paragraph indent. Keeping their
            # literal characters in the full text width avoids a stray last dash.
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif (all(abs(c-(left+width/2)) < tolerance for c in centers) and
              all(l.bbox.width < width*.85 for l in lines) and
              (len(lines) > 1 or first.bold or first.text.lstrip().startswith('('))):
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif all(abs(x-(left+width)) < tolerance for x in ends) and min(starts)-left > width*.15:
            para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        else:
            # Reconstruct the continuation margin, then a first-line/hanging
            # indent. An indented address is not automatically a centered title.
            continuation = median(starts[1:]) if len(starts) > 1 else starts[0]
            inset = max(0, min(width*.8, continuation-left))
            pf.left_indent = Pt(inset)
            pf.first_line_indent = Pt(max(-inset, min(width*.4, starts[0]-continuation)))
            if len(lines) >= 3 and all(abs(x-(left+width)) < tolerance for x in ends[:-1]):
                para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        if len(lines) > 1:
            baselines = [l.spans[0]['origin'][1] for l in lines]
            leading = median(b-a for a, b in zip(baselines, baselines[1:]))
            if first.size <= leading <= first.size*2:
                pf.line_spacing = Pt(leading)
        self.text_metrics(para, lines, responsive=not title)
        pf.keep_with_next = first.bold and len(lines) == 1
        for index, line in enumerate(lines):
            if index:
                # Keep hyphens, but never concatenate Cyrillic/Latin words merely
                # because PDF line boundaries are not actual space characters.
                previous = lines[index-1].text.rstrip()
                if previous and not previous.endswith(('-', '\u00ad')):
                    self.run(para, line.spans[0], ' ')
            previous_x = None
            for si, span in enumerate(line.spans):
                text = ''.join(c['c'] for c in span['chars'])
                if si == 0:
                    text = text.lstrip()
                if si == len(line.spans)-1:
                    text = text.rstrip()
                if previous_x is not None and span['bbox'][0]-previous_x > span['size']*.65 and text and not text[0].isspace():
                    self.run(para, span, ' ')
                self.run(para, span, re.sub(r'\s+', ' ', text))
                previous_x = span['bbox'][2]
        return para

    def field(self, parent, line, width):
        # Every label/value portion gets an expanding cell. Replacing a blank
        # with several lines grows the row and moves following content naturally.
        chars = [(c, s) for s in line.spans for c in s['chars']]
        text = ''.join(c['c'] for c, _ in chars)
        matches = list(re.finditer(r'(?<!\w)_{3,}(?!\w)', text))
        parts, pos = [], 0
        for match in matches:
            if match.start() > pos:
                parts.append((chars[pos:match.start()], False))
            parts.append((chars[match.start():match.end()], True))
            pos = match.end()
        if pos < len(chars):
            parts.append((chars[pos:], False))
        parts = [(cs, blank) for cs, blank in parts if blank or ''.join(c['c'] for c, _ in cs).strip()]
        natural = [max(2, cs[-1][0]['bbox'][2]-cs[0][0]['bbox'][0]) for cs, _ in parts]
        total = sum(natural)
        # Full-width source blanks should reach the same right margin. Short
        # signatures remain short, leaving real layout space to the right.
        available = min(width, max(total, line.bbox.width))
        # Reserve a little extra width for label glyph metrics; blanks absorb the
        # difference. Labels should not wrap because of PDF/Word rounding.
        label_widths = [v+line.size*.8 if not blank else 0 for v, (_, blank) in zip(natural, parts)]
        blank_total = sum(v for v, (_, blank) in zip(natural, parts) if blank)
        blank_space = available-sum(label_widths)
        if blank_space <= len(matches)*2:
            reject('a form row has insufficient space for editable values.')
        widths = [v/blank_total*blank_space if blank else label for v, label, (_, blank) in zip(natural, label_widths, parts)]
        table = table_at(parent, widths)
        for cell, (cs, blank) in zip(table.rows[0].cells, parts):
            para = self.paragraph(cell, line.size)
            self.text_metrics(para, [line])
            if blank:
                self.field_count += 1
                borders = element('tcBorders')
                borders.append(element('bottom', val='single', sz=4, color='000000'))
                cell_borders(cell, borders)
                self.run(para, cs[0][1], ' ')
            else:
                current, text = cs[0][1], ''
                for char, span in cs:
                    if span is not current:
                        self.run(para, current, text)
                        current, text = span, ''
                    text += char['c']
                self.run(para, current, text)
        separator = table_separator(parent)
        self.last_field = (widths, parts, line, table, separator)
        return table

    def caption(self, parent, line):
        if not self.last_field:
            return False
        chars = [(c, s) for s in line.spans for c in s['chars']]
        text = ''.join(c['c'] for c, _ in chars)
        matches = list(re.finditer(r'\([^()]*\)', text))
        if not matches or re.sub(r'\([^()]*\)', '', text).strip():
            return False
        widths, parts, field_line, field_table, separator = self.last_field
        if not -line.size < line.bbox.y0-field_line.bbox.y1 < line.size:
            return False
        # The value and its caption are one field, even at a page boundary.
        for cell in field_table.rows[0].cells:
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.keep_with_next = True
        separator.paragraph_format.keep_with_next = True
        blanks = [(i, (cs[0][0]['bbox'][0]+cs[-1][0]['bbox'][2])/2)
                  for i, (cs, blank) in enumerate(parts) if blank]
        table = table_at(parent, widths)
        used = set()
        for match in matches:
            cs = chars[match.start():match.end()]
            center = (cs[0][0]['bbox'][0]+cs[-1][0]['bbox'][2])/2
            choices = [(abs(center-x), i) for i, x in blanks if i not in used]
            if not choices:
                reject('form captions cannot be assigned to distinct fields.')
            _, index = min(choices)
            used.add(index)
            p = self.paragraph(table.cell(0, index), line.size)
            self.text_metrics(p, [line])
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            span, text = cs[0][1], ''
            for char, current in cs:
                if current is not span:
                    self.run(p, span, text)
                    span, text = current, ''
                text += char['c']
            self.run(p, span, text)
        # Empty cells must have the same small, expanding paragraph metrics.
        for i, cell in enumerate(table.rows[0].cells):
            if i not in used:
                self.text_metrics(self.paragraph(cell, line.size), [line])
        table_separator(parent)
        self.last_field = None
        return True

    def image(self, parent, page, rect, width=None):
        para = self.paragraph(parent, 1)
        pix = page.get_pixmap(matrix=pymupdf.Matrix(self.dpi/72, self.dpi/72), clip=rect+(-.5, -.5, .5, .5), alpha=False)
        para.add_run().add_picture(io.BytesIO(pix.tobytes('png')), width=Pt(min(width or rect.width, self.width)))

    def grid(self, parent, grid, cells):
        inset = max(0, grid.xs[0]-self.left)
        scale = min(1, (self.width-inset)/grid.bbox.width)
        widths = [(b-a)*scale for a, b in zip(grid.xs, grid.xs[1:])]
        table = table_at(parent, widths)
        table._tbl.tblPr.find(qn('w:tblInd')).set(qn('w:w'), str(round(inset*20)))
        for _ in cells[1:]:
            table.add_row()
        for r, row in enumerate(cells):
            for c, lines in enumerate(row):
                cell = table.cell(r, c)
                cell.width = Pt(widths[c])
                cell_margins(cell, 50)
                borders = element('tcBorders')
                for edge, (size, color) in [('top', grid.horizontal[r]), ('bottom', grid.horizontal[r+1]),
                                             ('left', grid.vertical[c]), ('right', grid.vertical[c+1])]:
                    borders.append(element(edge, val='single', sz=size, color=color))
                cell_borders(cell, borders)
                if lines:
                    self.flow(cell, lines, widths[c]-5, grid.ys[r], left=grid.xs[c]+2.5)
                else:
                    self.paragraph(cell, 8)
        table_separator(parent)
        return table

    def flow(self, parent, lines, width, top=None, left=None):
        check_columns(lines)
        self.spacing.flow(lines)
        left = self.left if left is None else left
        self.last_field = None
        pending = []
        previous = None
        before = 0
        def flush():
            nonlocal pending
            if pending:
                self.text(parent, pending, before, left=left, width=width)
                pending = []
        for line in lines:
            cancelled(self.cancel)
            gap = line.bbox.y0-(previous.bbox.y1 if previous else (top if top is not None else line.bbox.y0))
            boundary = (previous is None or line.block != previous.block or line.field or previous.field or
                        (previous.bold and not line.bold) or
                        bool(re.match(r'^\s*(?:[-•·]|\d+[.)])\s', line.text)) or
                        (previous is not None and bool(re.match(r'^\s*[-•·]\s', previous.text)) and
                         previous.bbox.x1 < left+width-line.size*4) or
                        gap > line.size*.6 or
                        (previous.bbox.x1 < left+width-max(line.size*4, width*.12) and
                         previous.bbox.x0 < left+width*.1 and
                         (previous.text.rstrip().endswith(('.', ':', ';', ')')) or
                          line.text.lstrip()[:1].isupper() or re.match(r'^\s*[\w -]{2,35}:', line.text))))
            if boundary:
                flush()
                before = max(0, gap)
            if line.field:
                if (previous is not None and not previous.field and
                        previous.bbox.width < width*.6 and
                        not previous.text.lstrip().startswith('(') and parent.paragraphs):
                    # Short labels immediately above a signature/value belong
                    # with that field rather than at the foot of the prior page.
                    parent.paragraphs[-1].paragraph_format.keep_with_next = True
                if before > 1 and parent.paragraphs:
                    parent.paragraphs[-1].paragraph_format.space_after = Pt(min(before, 12))
                self.field(parent, line, width)
            elif self.caption(parent, line):
                pass
            else:
                # A later parenthetical is narrative, not the earlier field's
                # caption. Do this when queuing text, before deferred emission.
                self.last_field = None
                pending.append(line)
            previous = line
        flush()


def build_document(pdf, mapping, dpi=144, cancel=None):
    pages = []
    for page in pdf:
        cancelled(cancel)
        lines = lines_on(page)
        boxes, rules, graphics, grids = graphics_on(page, lines)
        tables = [(grid, *partition(grid, lines, reject)) for grid in grids]
        consumed = {item for _, _, ids in tables for item in ids}
        sequence = [(l.bbox.y0, [l]) for l in lines if id(l) not in consumed]
        sequence += [(g.ys[0], [l for row in cells for cell in row for l in cell]) for g, cells, _ in tables]
        reading = [l for _, group in sorted(sequence, key=lambda pair: pair[0]) for l in group]
        pages.append((lines, boxes, rules, graphics, tables, reading))
    all_lines = [l for lines, *_ in pages for l in lines if l.text.strip()]
    left = min(72, max(12, min(l.bbox.x0 for l in all_lines)))
    right = min(72, max(12, pdf[0].rect.width-max(l.bbox.x1 for l in all_lines)))
    width = pdf[0].rect.width-left-right
    doc = Document()
    default_span = max((s for l in all_lines for s in l.spans), key=lambda s: len(s['chars']))
    normal = doc.styles['Normal']
    normal.font.name = mapping[default_span['font']].family
    normal.font.size = Pt(default_span['size'])
    normal.paragraph_format.space_before = normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.line_spacing = 1.0
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Pt(pdf[0].rect.width), Pt(pdf[0].rect.height)
    sec.left_margin, sec.right_margin = Pt(left), Pt(right)
    sec.top_margin = sec.bottom_margin = Pt(18)
    writer = Writer(doc, mapping, width, left, dpi, cancel)
    source_chars = Counter(c['c'] for lines, *_ in pages for l in lines for s in l.spans for c in s['chars'] if not c['c'].isspace())
    removed = Counter()
    for page, (lines, boxes, rules, graphics, tables, reading) in zip(pdf, pages):
        # Continue ordinary body pages; a new graphic/title header retains a page
        # boundary. This mode deliberately allows the page count to change.
        body_size = sorted(l.size for l in lines)[len(lines)//2]
        new_title = lines[0].bold and lines[0].size > body_size*1.2
        if page.number and (new_title or any(g.y0 < page.rect.height*.15 for g in graphics)):
            doc.add_page_break()
        consumed = set()
        events = []
        for grid, cells, ids in tables:
            consumed.update(ids)
            events.append((grid.ys[0], 'grid', (grid, cells)))
        for graphic in graphics:
            title = [l for l in lines if l.bbox.x0 > graphic.x1+5 and
                     l.bbox.y0 < graphic.y1+20 and l.bbox.y1 > graphic.y0]
            header = (graphic.y0 < page.rect.height*.15 and graphic.height < page.rect.height*.15 and
                      title and all(l.bold for l in title))
            if header:
                consumed.update(id(l) for l in title)
                events.append((min(graphic.y0, title[0].bbox.y0), 'header', (graphic, title)))
            else:
                events.append((graphic.y0, 'image', graphic))
        for box in boxes:
            inner = [l for l in lines if contains(box, l.bbox)]
            if not inner:
                reject('an empty drawn box is not a supported editable field.')
            consumed.update(id(l) for l in inner)
            events.append((box.y0, 'box', (box, inner)))
        body = [l for l in lines if id(l) not in consumed]
        check_columns(body)
        for line in body:
            events.append((line.bbox.y0, 'line', line))
        for rule in rules:
            underline = [s for l in lines for s in l.spans
                         if abs(s['origin'][1]-rule.y0) < s['size']*.35 and
                         abs(s['bbox'][0]-rule.x0) < 2 and abs(s['bbox'][2]-rule.x1) < 2]
            if underline:
                for span in underline:
                    span['underline'] = True
                continue
            if any(intersects(l.bbox, rule+(0, -.5, 0, .5), .1) for l in lines):
                reject('a drawn line crosses text.')
            events.append((rule.y0, 'rule', rule))
        pending, last_bottom = [], None
        def flush_body():
            nonlocal pending, last_bottom
            if pending:
                writer.flow(doc, pending, width, last_bottom)
                last_bottom = pending[-1].bbox.y1
                pending = []
        for _, kind, data in sorted(events, key=lambda e: e[0]):
            if kind == 'line':
                pending.append(data)
                continue
            flush_body()
            if kind == 'header':
                graphic, title = data
                split = min(width*.45, max(graphic.width+8, min(l.bbox.x0 for l in title)-left-6))
                table = table_at(doc, [split, width-split])
                writer.image(table.cell(0, 0), page, graphic, min(graphic.width, split-4))
                # Each source title line remains a paragraph, not a positioned box.
                for line in title:
                    writer.text(table.cell(0, 1), [line], title=True)
                table_separator(doc)
                last_bottom = max(graphic.y1, title[-1].bbox.y1)
            elif kind == 'box':
                box, inner = data
                if doc.paragraphs:
                    doc.paragraphs[-1].paragraph_format.space_after = Pt(3)
                table = table_at(doc, [width], border=True)
                writer.flow(table.cell(0, 0), inner, width-5, box.y0, left=box.x0+2.5)
                table_separator(doc)
                last_bottom = box.y1
            elif kind == 'image':
                writer.image(doc, page, data)
                last_bottom = data.y1
            elif kind == 'grid':
                grid, cells = data
                writer.grid(doc, grid, cells)
                last_bottom = grid.ys[-1]
            else:
                table = table_at(doc, [min(width, data.width)])
                borders = element('tcBorders')
                borders.append(element('bottom', val='single', sz=4, color='000000'))
                cell_borders(table.cell(0, 0), borders)
                writer.paragraph(table.cell(0, 0), 7.5)
                table_separator(doc)
                last_bottom = data.y1
        flush_body()
        for line in lines:
            for match in re.finditer(r'(?<!\w)_{3,}(?!\w)', line.text):
                removed.update(match.group())
    actual_chars = Counter(c for c, *_ in writer.expected)
    if source_chars != actual_chars+removed:
        raise ValueError('Editable conversion did not account for every source character.')
    # Independently compare the emitted order and face of every non-whitespace
    # character with the extracted reading sequence, rather than trusting only
    # a ledger written by the emitter itself.
    source_signature = []
    for *_, reading in pages:
        for line in reading:
            blanks = {i for m in re.finditer(r'(?<!\w)_{3,}(?!\w)', line.text) for i in range(m.start(), m.end())}
            index = 0
            for span in line.spans:
                face = mapping[span['font']]
                for char in span['chars']:
                    if index not in blanks and not char['c'].isspace():
                        source_signature.append((char['c'], face.family, face.bold, face.italic))
                    index += 1
    if writer.expected != source_signature:
        raise ValueError('Editable output text, reading order or emphasis verification failed.')
    return doc, writer.expected, writer.field_count


def verify_document(doc, expected):
    if list(doc.element.iter(qn('w:txbxContent'))) or list(doc.element.iter(qn('w:framePr'))):
        raise ValueError('Editable output unexpectedly contains positioned text.')
    actual = []
    for run in doc.element.iter(qn('w:r')):
        texts = ''.join(t.text or '' for t in run.iter(qn('w:t')))
        if not texts.strip():
            continue
        rpr = run.find(qn('w:rPr'))
        fonts = rpr.find(qn('w:rFonts')) if rpr is not None else None
        if fonts is None:
            raise ValueError('Editable output contains text without an approved font.')
        def on(name):
            node = rpr.find(qn('w:'+name))
            return node is not None and node.get(qn('w:val'), '1') not in ('0', 'false')
        actual.extend((c, fonts.get(qn('w:ascii')), on('b'), on('i')) for c in texts if not c.isspace())
    if actual != expected:
        raise ValueError('Editable output text, reading order or emphasis verification failed.')
