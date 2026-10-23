"""Conservative PDF note recognition and native, editable Word note parts."""
from dataclasses import dataclass
import re

from docx.opc.constants import CONTENT_TYPE as CT, RELATIONSHIP_TYPE as RT
from docx.opc.packuri import PackURI
from docx.opc.part import XmlPart
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph


def text(span):
    return ''.join(c['c'] for c in span['chars'])


def raised_marker(line, span):
    """Both the inline anchor and the note label must be geometrically raised."""
    if not re.fullmatch(r'(?:[0-9]{1,3}|[*†‡])', text(span).strip()):
        return None
    peers = [s for s in line.spans if s is not span and text(s).strip() and
             s['size'] >= span['size']*1.2]
    if not peers:
        return None
    base = max(peers, key=lambda s: len(text(s).strip()))
    rise = base['origin'][1]-span['origin'][1]
    if not base['size']*.15 <= rise <= base['size']*.7:
        return None
    return text(span).strip(), rise


@dataclass
class Note:
    marker: str
    anchor: dict
    rise: float
    lines: list
    label: dict
    label_rise: float
    number: int = 0


def find_notes(lines, rules, height, reject):
    """Recognize a bottom region only with a separator and unique raised anchors.

    Ordinary footers/exponents do not suffice. Ambiguous note-like regions fail
    rather than moving prose to the wrong anchor. No document wording is used.
    """
    candidates = [(l.bbox.y0, 'line', l) for l in lines
                  if l.bbox.y0 > height*.75 and re.fullmatch(r'\s*_{3,}\s*', l.text)
                  and l.bbox.width > 40]
    candidates += [(r.y0, 'rule', r) for r in rules if r.y0 > height*.75 and r.width > 40]
    for y, kind, separator in sorted(candidates, key=lambda c: c[0]):
        tail = [l for l in lines if l is not separator and l.bbox.y0 >= y and l.text.strip()]
        if not tail:
            continue
        starts = []
        for i, line in enumerate(tail):
            first = next((s for s in line.spans if text(s).strip()), None)
            marker = raised_marker(line, first) if first is not None else None
            if marker:
                starts.append((i, first, marker))
        if not starts or starts[0][0] != 0:
            continue
        # A note footer must sit under its separator, not a signature elsewhere.
        rect = separator.bbox if kind == 'line' else separator
        if abs(tail[0].bbox.x0-rect.x0) > max(3, tail[0].size):
            continue
        body = [l for l in lines if l.bbox.y0 < y]
        notes, markers = [], set()
        for index, (start, label, (marker, label_rise)) in enumerate(starts):
            stop = starts[index+1][0] if index+1 < len(starts) else len(tail)
            content = tail[start:stop]
            if (abs(content[0].bbox.x0-rect.x0) > max(3, content[0].size) or
                    any(raised_marker(line, span) for line in content for span in line.spans
                        if span is not label)):
                # Two note columns can be extracted as a single line. Never
                # absorb the second note/marker into the first one's prose.
                reject('footnote references are ambiguous.')
            # A page number or separate footer below a genuine note must not
            # become part of that note. Only adjacent, similarly aligned prose
            # is attributable to a reference; leave uncertain PDFs unsupported.
            for previous, current in zip(content, content[1:]):
                size = max(previous.size, current.size)
                if (current.bbox.y0-previous.bbox.y0 > size*2.3 or
                        abs(current.bbox.x0-content[0].bbox.x0) > max(12, size*2)):
                    reject('footnote references are ambiguous.')
            anchors = [(s, evidence[1]) for l in body for s in l.spans
                       if (evidence := raised_marker(l, s)) and evidence[0] == marker]
            if marker in markers or len(anchors) != 1 or any(l.field for l in content):
                reject('footnote references are ambiguous.')
            markers.add(marker)
            anchor, rise = anchors[0]
            notes.append(Note(marker, anchor, rise, content, label, label_rise))
        # Native Word lays out notes in anchor order. Preserve footer order too.
        positions = {id(s):i for i, s in enumerate(s for l in body for s in l.spans)}
        if [positions[id(n.anchor)] for n in notes] != sorted(positions[id(n.anchor)] for n in notes):
            reject('footnote references are ambiguous.')
        return notes, {id(l) for l in tail} | ({id(separator)} if kind == 'line' else set()), ({id(separator)} if kind == 'rule' else set())
    return [], set(), set()


class NoteContainer:
    """Small paragraph-only adapter; note bodies are never frames or images."""
    def __init__(self, node, part):
        self.node, self.part = node, part
        self.tables = []

    @property
    def paragraphs(self):
        return [Paragraph(p, self) for p in self.node.findall(qn('w:p'))]

    def add_paragraph(self):
        p = OxmlElement('w:p')
        self.node.append(p)
        return Paragraph(p, self)


def create_part(doc):
    root = OxmlElement('w:footnotes')
    part = XmlPart(PackURI('/word/footnotes.xml'), CT.WML_FOOTNOTES, root, doc.part.package)
    doc.part.relate_to(part, RT.FOOTNOTES)
    for number, name in [(-1, 'separator'), (0, 'continuationSeparator')]:
        note = OxmlElement('w:footnote')
        note.set(qn('w:type'), name); note.set(qn('w:id'), str(number))
        para = OxmlElement('w:p'); run = OxmlElement('w:r')
        run.append(OxmlElement('w:'+name)); para.append(run); note.append(para); root.append(note)
    return part


def add_note(part, number):
    node = OxmlElement('w:footnote'); node.set(qn('w:id'), str(number))
    part.element.append(node)
    return NoteContainer(node, part)


def read_part(doc):
    relations = [r for r in doc.part.rels.values() if r.reltype == RT.FOOTNOTES]
    if len(relations) != 1 or relations[0].is_external or relations[0].target_part.content_type != CT.WML_FOOTNOTES:
        raise ValueError('Editable footnote relationship verification failed.')
    return parse_xml(relations[0].target_part.blob)
