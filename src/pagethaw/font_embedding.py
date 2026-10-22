"""Optional, full-face DOCX embedding of permitted static TrueType fonts.

Font bytes and permission flags are never changed. Preview/print-only fonts are
deliberately excluded from documents intended for editing. See docs/FONTS.md.
"""
from collections import defaultdict
import hashlib
import io
from pathlib import Path
import uuid
import zipfile

from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.opc.packuri import PackURI
from docx.opc.part import Part
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn
from fontTools.ttLib import TTFont

CONTENT_TYPE = 'application/vnd.openxmlformats-officedocument.obfuscatedFont'
FONT_REL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/font'
SLOTS = ('embedRegular', 'embedBold', 'embedItalic', 'embedBoldItalic')


def eligibility(data):
    """Return a user-facing reason to skip; absence means full embedding allowed."""
    try:
        with TTFont(io.BytesIO(data), lazy=False) as font:
            if 'OS/2' not in font:
                return 'Font has no embedding permission information.'
            flags = font['OS/2'].fsType
            if flags & 0x200:
                return 'Font allows bitmap embedding only.'
            if flags & ~0x10E or flags & 0xE not in (0, 2, 4, 8):
                return 'Font has ambiguous embedding permissions.'
            if flags & 2:
                return 'Font restricts embedding.'
            if flags & 4:
                return 'Font permits preview and printing only, not editing.'
            if font.flavor or 'fvar' in font or 'glyf' not in font or 'loca' not in font:
                return 'Embedding currently supports static TrueType outlines only.'
    except Exception:
        return 'Font embedding information could not be read.'
    return None


def obfuscate(data, key):
    # ECMA-376: reverse the canonical GUID bytes, repeat over the first 32 bytes.
    mask = uuid.UUID(str(key)).bytes[::-1]
    return bytes(b ^ mask[i % 16] for i, b in enumerate(data[:32])) + data[32:]


def embed_fonts(doc, faces, cancel=None):
    result = {'embedded_fonts': [], 'font_embedding_skipped': []}
    groups = defaultdict(dict)
    for face in faces:
        slot = SLOTS[int(face.bold) + 2*int(face.italic)]
        groups[(face.family, slot)][face.sha256] = face
    table = doc.part.part_related_by(RT.FONT_TABLE)
    root = parse_xml(table.blob)
    for (family, slot), variants in sorted(groups.items()):
        if cancel and cancel.is_set():
            raise InterruptedError('Conversion cancelled.')
        for face in variants.values():
            data = Path(face.path).read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            if not face.sha256 or digest != face.sha256:
                raise ValueError('Font file changed; choose the font again: '+face.full_name)
            record = {'family': family, 'style': slot[5:], 'sha256': digest}
            reason = 'Conflicting faces use the same family and style.' if len(variants) != 1 else eligibility(data)
            if reason:
                result['font_embedding_skipped'].append(dict(record, reason=reason))
                continue
            nodes = [n for n in root if n.get(qn('w:name')) == family]
            if len(nodes) > 1 or nodes and nodes[0].find(qn('w:'+slot)) is not None:
                raise ValueError('Document already contains a conflicting embedded font.')
            if nodes:
                node = nodes[0]
            else:
                node = OxmlElement('w:font')
                node.set(qn('w:name'), family)
                root.append(node)
            key = uuid.uuid4()
            name = doc.part.package.next_partname('/word/fonts/font%d.odttf')
            part = Part(PackURI(name), CONTENT_TYPE, obfuscate(data, key), doc.part.package)
            rel = table.relate_to(part, FONT_REL)
            entry = OxmlElement('w:'+slot)
            entry.set(qn('r:id'), rel)
            entry.set(qn('w:fontKey'), '{'+str(key).upper()+'}')
            entry.set(qn('w:subsetted'), '0')
            later = SLOTS[SLOTS.index(slot)+1:]
            following = next((n for n in node if n.tag in {qn('w:'+s) for s in later}), None)
            node.insert(list(node).index(following) if following is not None else len(node), entry)
            result['embedded_fonts'].append(record)
    from lxml import etree
    table._blob = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
    if result['embedded_fonts']:
        settings = doc.settings.element
        # These three settings precede saveFormsData and defaultTabStop in CT_Settings.
        for name, value in [('embedTrueTypeFonts', '1'), ('embedSystemFonts', '0'), ('saveSubsetFonts', '0')]:
            for existing in settings.findall(qn('w:'+name)):
                settings.remove(existing)
            node = OxmlElement('w:'+name)
            node.set(qn('w:val'), value)
            settings.insert_element_before(node, 'w:saveFormsData', 'w:mirrorMargins', 'w:alignBordersAndEdges',
                                           'w:bordersDoNotSurroundHeader', 'w:bordersDoNotSurroundFooter',
                                           'w:gutterAtTop', 'w:hideSpellingErrors', 'w:hideGrammaticalErrors',
                                           'w:activeWritingStyle', 'w:proofState', 'w:formsDesign', 'w:attachedTemplate',
                                           'w:linkStyles', 'w:stylePaneFormatFilter', 'w:stylePaneSortMethod', 'w:documentType',
                                           'w:mailMerge', 'w:revisionView', 'w:trackRevisions', 'w:doNotTrackMoves',
                                           'w:doNotTrackFormatting', 'w:documentProtection', 'w:autoFormatOverride',
                                           'w:styleLockTheme', 'w:styleLockQFSet', 'w:defaultTabStop')
    return result


def verify_embedded_fonts(path, result):
    """Reopen the OPC package and prove every embedded face is the approved bytes."""
    expected = {(r['family'], r['style']): r['sha256'] for r in result['embedded_fonts']}
    from docx import Document
    with zipfile.ZipFile(path) as z:
        if len(z.namelist()) != len(set(z.namelist())):
            raise ValueError('Duplicate parts in the Word document.')
    doc = Document(path)
    table = doc.part.part_related_by(RT.FONT_TABLE)
    actual = {}
    for node in parse_xml(table.blob):
        for slot in SLOTS:
            for entry in node.findall(qn('w:'+slot)):
                rel = table.rels[entry.get(qn('r:id'))]
                if rel.is_external or rel.reltype != FONT_REL or rel.target_part.content_type != CONTENT_TYPE:
                    raise ValueError('Invalid embedded font relationship.')
                data = obfuscate(rel.target_part.blob, entry.get(qn('w:fontKey')).strip('{}'))
                identity = (node.get(qn('w:name')), slot[5:])
                if identity in actual or entry.get(qn('w:subsetted')) != '0' or eligibility(data):
                    raise ValueError('Invalid or restricted embedded font.')
                actual[identity] = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise ValueError('Embedded font verification failed.')
