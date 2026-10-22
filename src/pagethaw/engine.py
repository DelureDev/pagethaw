"""Conservative PDF preflight and editable positioned-text DOCX conversion."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape, quoteattr
import hashlib
import io
import json
import re
import threading
import unicodedata
import zipfile
import xml.etree.ElementTree as ET

import pymupdf
from docx import Document
from docx.shared import Pt
from docx.oxml import OxmlElement, parse_xml

from .fonts import FontFace, missing_glyphs
from .font_match import FontProof, pdf_font_proofs

# Optional PyMuPDF helpers can change this global during import. Use the core
# metric corrections in both source installs and the lean portable runtime.
pymupdf.TOOLS.unset_quad_corrections(False)

W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
V = 'urn:schemas-microsoft-com:vml'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'


@dataclass
class PDFInfo:
    path: Path
    pages: int = 0
    fonts: dict[str, str] = field(default_factory=dict)
    error: str = ''
    sha256: str = ''
    font_proofs: dict[str, FontProof] = field(default_factory=dict)


def error_message(exc):
    if isinstance(exc, PermissionError):
        return 'Cannot access this file or folder. Close it in other apps or choose a writable folder, then retry.'
    if isinstance(exc, FileNotFoundError):
        return 'File or folder not found. Check that it still exists, then scan again.'
    if isinstance(exc, (NotADirectoryError, IsADirectoryError)):
        return 'This path has the wrong type. Choose a PDF file and a separate output folder.'
    if isinstance(exc, pymupdf.FileDataError):
        return 'This PDF is damaged or unreadable. Try opening it in a PDF viewer and saving a new copy.'
    return str(exc)


def inspect_pdf(path: Path, cancel=None) -> PDFInfo:
    result = PDFInfo(path.resolve())
    try:
        result.sha256 = digest(path)
        with pymupdf.open(path) as pdf:
            if not pdf.is_pdf or pdf.needs_pass:
                raise ValueError('Use an unlocked PDF file.')
            if not len(pdf):
                raise ValueError('The PDF has no pages.')
            result.pages = len(pdf)
            first = pdf[0].rect
            if max(first.width, first.height) > 1584:
                raise ValueError('Pages larger than 22 inches are outside Word page-size limits.')
            fonts = {}
            for page in pdf:
                if cancel and cancel.is_set():
                    raise InterruptedError('Scan cancelled. Scan again before converting.')
                prefix = f'Page {page.number+1}: '
                if page.rotation:
                    raise ValueError(prefix+'rotated pages are not supported yet.')
                if abs(page.rect.width-first.width) > .1 or abs(page.rect.height-first.height) > .1:
                    raise ValueError('Mixed page sizes are not supported yet.')
                if list(page.widgets()):
                    raise ValueError(prefix+'interactive form fields are not supported yet.')
                for trace in page.get_texttrace():
                    if trace.get('type', 0) != 0 or trace.get('opacity', 1) < .999:
                        raise ValueError(prefix+'hidden, transparent or outlined text is not supported (including OCR layers).')
                found = False
                for block in page.get_text('dict')['blocks']:
                    for line in block.get('lines', []):
                        if abs(line['dir'][0]-1) > .001 or abs(line['dir'][1]) > .001:
                            raise ValueError(prefix+'rotated/vertical text is not supported yet.')
                        for span in line['spans']:
                            text = span['text']
                            # Whitespace-only runs still have a font and survive
                            # as editable text. Include them in the font choice
                            # list rather than failing later on an unknown font.
                            if text:
                                fonts.setdefault(span['font'], set()).update(text)
                            if not text.strip():
                                continue
                            found = True
                            if '\ufffd' in text or any(unicodedata.category(c) == 'Co' for c in text):
                                raise ValueError(prefix+'unmapped PDF characters need a different extraction workflow.')
                            if any(unicodedata.bidirectional(c) in {'R', 'AL', 'AN'} for c in text):
                                raise ValueError(prefix+'right-to-left text is not supported yet.')
                            if any(ord(c) < 32 and not c.isspace() for c in text):
                                raise ValueError(prefix+'unsupported control characters.')
                if not found:
                    raise ValueError(prefix+'no selectable text; scanned pages need OCR first.')
            result.fonts = {name: ''.join(sorted(chars)) for name, chars in sorted(fonts.items())}
            result.font_proofs = pdf_font_proofs(pdf, cancel=cancel)
    except InterruptedError:
        raise
    except Exception as exc:
        result.error = error_message(exc)
    return result


def segments(page, rules=False, fonts=None):
    """Underscores stay literal unless standalone form blanks are explicitly enabled."""
    for block in page.get_text('rawdict')['blocks']:
        for line in block.get('lines', []):
            for raw in line['spans']:
                chars = raw['chars']
                if not chars:
                    continue
                text = ''.join(c['c'] for c in chars)
                blanks = list(re.finditer(r'(?<!\w)_{3,}(?!\w)', text)) if rules else []
                ranges = []
                start = 0
                for blank in blanks:
                    if blank.start() > start:
                        ranges.append((start, blank.start(), False))
                    ranges.append((blank.start(), blank.end(), True))
                    start = blank.end()
                if start < len(chars):
                    ranges.append((start, len(chars), False))
                for start, end, is_rule in ranges:
                    cuts = [start]
                    if fonts and not is_rule:
                        font = fonts[raw['font']]
                        for i in range(start, end-1):
                            if chars[i]['c'].isspace() and not chars[i+1]['c'].isspace():
                                advance = chars[i+1]['origin'][0]-chars[i]['origin'][0]
                                nominal = font.glyph_advance(ord(chars[i]['c']))*raw['size']
                                if abs(advance-nominal) > max(.15, .08*raw['size']):
                                    cuts.append(i+1)
                    cuts.append(end)
                    for left, right in zip(cuts, cuts[1:]):
                        group = chars[left:right]
                        yield dict(raw, chars=group, text=''.join(c['c'] for c in group), rule=is_rule,
                                   origin=group[0]['origin'],
                                   bbox=(group[0]['bbox'][0], raw['bbox'][1], group[-1]['bbox'][2], raw['bbox'][3]))


def validate_mapping(info: PDFInfo, mapping: dict[str, FontFace]):
    if info.error:
        raise ValueError(info.error)
    if digest(info.path) != info.sha256:
        raise ValueError('The source PDF changed after scanning. Scan it again before conversion.')
    for name, chars in info.fonts.items():
        if name not in mapping:
            raise ValueError('Choose a font for '+name+'. No substitution was applied.')
        face = mapping[name]
        if face.sha256 and digest(face.path) != face.sha256:
            raise ValueError('Installed fonts changed. Scan files & fonts again before converting.')
        if not face.installed:
            raise ValueError('Install '+face.full_name+' before conversion so Word can use it.')
        missing = missing_glyphs(face, chars)
        if missing:
            raise ValueError(face.full_name+' lacks characters: '+repr(''.join(missing[:24])))


def check_geometry(pdf, mapping, proofs=None):
    """Check letter advances, excluding justified word spaces. Keep short-word evidence."""
    fonts = {}
    for page in pdf:
        for span in segments(page):
            face = mapping[span['font']]
            proof = (proofs or {}).get(span['font'])
            if not face.matches(span['font']) and not (proof and proof.complete):
                continue
            if face.path not in fonts:
                fonts[face.path] = pymupdf.Font(fontfile=face.path)
            font = fonts[face.path]
            chars = span['chars']
            distance = expected = 0
            for char, following in zip(chars, chars[1:]):
                if char['c'].isspace():
                    continue
                code = ord(char['c'])
                widths = proof.widths.get(code, set()) if proof and proof.complete else set()
                width = next(iter(widths)) if len(widths) == 1 else font.glyph_advance(code)
                distance += following['origin'][0]-char['origin'][0]
                expected += width*span['size']
            if expected > 12 and abs(distance / expected - 1) > .08:
                raise ValueError(f'Page {page.number+1}: stretched or unusually spaced text needs manual conversion.')


def convert_pdf(info, target, mapping, rules=False, dpi=144, cancel=None, mode='layout'):
    if mode == 'editable':
        return convert_editable(info, target, mapping, dpi, cancel)
    if mode != 'layout':
        raise ValueError('Choose Editable text or Preserve layout.')
    """Write atomically and refuse replacement of any existing output."""
    target = Path(target)
    if target.exists():
        raise FileExistsError('Output already exists: '+target.name)
    if dpi not in (96, 144, 192):
        raise ValueError('Choose 96, 144 or 192 DPI for graphics.')
    validate_mapping(info, mapping)
    expected_pages = []
    with pymupdf.open(info.path) as pdf:
        check_geometry(pdf, mapping, info.font_proofs)
        fonts = {name: pymupdf.Font(fontfile=mapping[name].path) for name in info.fonts}
        doc = Document()
        doc.core_properties.author = 'PageThaw'
        doc.core_properties.title = info.path.stem
        doc.core_properties.comments = 'Converted locally with PageThaw; PDF processing by PyMuPDF/MuPDF (AGPL-3.0).'
        section = doc.sections[0]
        section.page_width = Pt(pdf[0].rect.width)
        section.page_height = Pt(pdf[0].rect.height)
        section.top_margin = section.bottom_margin = section.left_margin = section.right_margin = Pt(0)
        for index, page in enumerate(pdf):
            if cancel and cancel.is_set():
                raise InterruptedError('Cancelled before the next page.')
            parts = list(segments(page, rules, fonts))
            expected_pages.append((''.join(s['text'] for s in parts if not s['rule']), sum(s['rule'] for s in parts)))
            paragraph = doc.add_paragraph()
            fmt = paragraph.paragraph_format
            fmt.space_before = fmt.space_after = Pt(0)
            fmt.line_spacing = Pt(1)
            fmt.page_break_before = index > 0
            with pymupdf.open() as graphics:
                graphics.insert_pdf(pdf, from_page=index, to_page=index)
                background = graphics[0]
                for span in parts:
                    background.add_redact_annot(span['bbox'], fill=False)
                background.apply_redactions(images=0, graphics=0, text=0)
                png = background.get_pixmap(matrix=pymupdf.Matrix(dpi/72, dpi/72), alpha=False).tobytes('png')
            rid, _ = doc.part.get_or_add_image(io.BytesIO(png))
            append_shape(paragraph, f'<v:shape xmlns:v="{V}" xmlns:r="{R}" id="background{index}" type="#_x0000_t75" style="position:absolute;left:0;top:0;width:{page.rect.width}pt;height:{page.rect.height}pt;z-index:-1;mso-position-horizontal-relative:page;mso-position-vertical-relative:page" stroked="f"><v:imagedata r:id="{rid}"/></v:shape>')
            for number, span in enumerate(parts):
                x, y, right, bottom = span['bbox']
                size = span['size']
                if span['rule']:
                    baseline = span['origin'][1]+size*.1195
                    append_shape(paragraph, f'<v:line xmlns:v="{V}" id="rule{index}_{number}" style="position:absolute;left:0;top:0;z-index:2;mso-position-horizontal-relative:page;mso-position-vertical-relative:page" from="{x:.3f}pt,{baseline:.3f}pt" to="{right:.3f}pt,{baseline:.3f}pt" strokecolor="#{span["color"]:06x}" strokeweight="{size*.083:.3f}pt"/>')
                    continue
                face = mapping[span['font']]
                family = quoteattr(face.family)
                style = f'position:absolute;margin-left:{x:.3f}pt;margin-top:{y:.3f}pt;width:{max(right-x+20,25):.3f}pt;height:{max(bottom-y+5,15):.3f}pt;z-index:1;mso-position-horizontal-relative:page;mso-position-vertical-relative:page;mso-wrap-style:none'
                append_shape(paragraph, f'''<v:shape xmlns:v="{V}" xmlns:w="{W}" id="text{index}_{number}" style="{style}" stroked="f" filled="f"><v:textbox inset="0,0,0,0"><w:txbxContent><w:p><w:pPr><w:spacing w:before="0" w:after="0" w:line="{round(size*1.25*20)}" w:lineRule="exact"/><w:widowControl w:val="0"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii={family} w:hAnsi={family} w:eastAsia={family} w:cs={family}/><w:b w:val="{int(face.bold)}"/><w:bCs w:val="{int(face.bold)}"/><w:i w:val="{int(face.italic)}"/><w:iCs w:val="{int(face.italic)}"/><w:kern w:val="1"/><w:sz w:val="{round(size*2)}"/><w:szCs w:val="{round(size*2)}"/><w:color w:val="{span['color']:06x}"/><w:w w:val="100"/></w:rPr><w:t xml:space="preserve">{escape(span['text'])}</w:t></w:r></w:p></w:txbxContent></v:textbox></v:shape>''')
        if cancel and cancel.is_set():
            raise InterruptedError('Cancelled before saving the document.')
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix('.partial.docx')
        if temporary.exists():
            raise FileExistsError('A partial conversion already exists: '+temporary.name)
        try:
            doc.save(temporary)
            verify_docx(temporary, expected_pages)
            # Exclusive create prevents a race with another conversion or user-created file.
            owned = False
            try:
                with target.open('xb') as destination:
                    owned = True
                    destination.write(temporary.read_bytes())
            except BaseException:
                if owned:
                    target.unlink(missing_ok=True)
                raise
        finally:
            temporary.unlink(missing_ok=True)
    return {'status': 'converted; visual review required', 'pages': info.pages,
            'content_check': 'passed', 'sha256': digest(target),
            'substitutions': [name for name in info.fonts if not mapping[name].matches(name)]}


def append_shape(paragraph, xml):
    picture = OxmlElement('w:pict')
    picture.append(parse_xml(xml))
    paragraph.add_run()._r.append(picture)


def verify_docx(path, expected):
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read('word/document.xml'))
    paragraphs = root.find('{'+W+'}body').findall('{'+W+'}p')
    if len(paragraphs) != len(expected):
        raise ValueError('DOCX page-anchor verification failed.')
    for p, (text, rules) in zip(paragraphs, expected):
        actual = ''.join(t.text or '' for t in p.iter('{'+W+'}t'))
        if actual != text or len(list(p.iter('{'+V+'}line'))) != rules:
            raise ValueError('DOCX text/rule verification failed. No output was accepted.')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def convert_editable(info, target, mapping, dpi=144, cancel=None):
    from .editable import build_document, verify_document, cancelled
    target = Path(target)
    if target.exists():
        raise FileExistsError('Output already exists: '+target.name)
    if dpi not in (96, 144, 192):
        raise ValueError('Choose 96, 144 or 192 DPI for graphics.')
    validate_mapping(info, mapping)
    cancelled(cancel)
    with pymupdf.open(info.path) as pdf:
        doc, expected, fields = build_document(pdf, mapping, dpi, cancel)
    doc.core_properties.author = 'PageThaw'
    doc.core_properties.title = info.path.stem
    doc.core_properties.comments = 'Flowing paragraphs and expanding form cells. Pagination may differ from the PDF. Review before use.'
    verify_document(doc, expected)
    cancelled(cancel)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.partial.docx')
    owned = False
    try:
        with temporary.open('xb') as stream:
            owned = True
            doc.save(stream)
        verify_document(Document(temporary), expected)
        cancelled(cancel)
        output_owned = False
        try:
            with target.open('xb') as destination:
                output_owned = True
                destination.write(temporary.read_bytes())
        except BaseException:
            if output_owned:
                target.unlink(missing_ok=True)
            raise
    finally:
        if owned:
            temporary.unlink(missing_ok=True)
    return {'status': 'converted; visual review required', 'mode': 'editable',
            'source_pages': info.pages, 'content_check': 'passed', 'fields': fields,
            'pagination': 'reflowed; inspect in Word', 'sha256': digest(target),
            'substitutions': [name for name in info.fonts if not mapping[name].matches(name)]}


def convert_batch(infos, output, mapping, *, rules=False, dpi=144, cancel=None, progress=None, write_report=False, mode='layout'):
    if mode not in ('layout', 'editable'):
        raise ValueError('Choose Editable text or Preserve layout.')
    output = Path(output)
    if output.is_file():
        raise NotADirectoryError('Choose an output folder, not a file.')
    output.mkdir(parents=True, exist_ok=True)
    report = output / 'pagethaw-report.json'
    if write_report and report.exists():
        raise FileExistsError('Choose a new output folder; this folder already contains a PageThaw report.')
    records = []
    reserved = {p.name.casefold() for p in output.iterdir()}
    names = []
    for info in infos:
        name = info.path.stem+'.docx'
        number = 2
        while name.casefold() in reserved or Path(name).with_suffix('.partial.docx').name.casefold() in reserved:
            name = f'{info.path.stem} ({number}).docx'
            number += 1
        reserved.add(name.casefold())
        reserved.add(Path(name).with_suffix('.partial.docx').name.casefold())
        names.append(name)
    for index, info in enumerate(infos):
        record = {'input': info.path.name, 'source': str(info.path), 'output': names[index], 'mode': mode}
        record['input_sha256'] = info.sha256
        records.append(record)
        if cancel and cancel.is_set():
            record.update(status='cancelled')
        else:
            try:
                record.update(convert_pdf(info, output/record['output'], mapping, rules, dpi, cancel, mode=mode))
            except InterruptedError as exc:
                record.update(status='cancelled', error=str(exc))
            except Exception as exc:
                record.update(status='failed', error=error_message(exc), detail=str(exc))
        if write_report:
            report.write_text(json.dumps({'version': 1, 'files': records,
                'visual_review': 'not run; open outputs in Word and compare every page'}, ensure_ascii=False, indent=2), encoding='utf-8')
        if progress:
            progress(index+1, len(infos), record)
    return records
