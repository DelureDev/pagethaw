"""Conservative local matching of used PDF glyphs; no font files are extracted to disk."""
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
import hashlib
import io
import json

from fontTools.cffLib import CFFFontSet
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.ttLib import TTFont

from .fonts import normalized, missing_glyphs


@dataclass
class FontProof:
    glyphs: dict[int, set[str]] = field(default_factory=dict)
    widths: dict[int, set[float]] = field(default_factory=dict)
    complete: bool = True


def signature(glyphset, name, scale):
    glyph = glyphset[name]
    pen = DecomposingRecordingPen(glyphset)
    glyph.draw(pen)
    drawing = [(op, [None if point is None else [round(v*scale, 6) for v in point]
                      for point in points]) for op, points in pen.value]
    width = round(glyph.width*scale, 6)
    return hashlib.sha256(json.dumps([width, drawing]).encode()).hexdigest(), width


def pdf_font_proofs(pdf):
    proofs, loaded, aliases = {}, {}, {}
    for page in pdf:
        resources = page.get_fonts(full=True)
        for ref, _, _, base, *_ in resources:
            aliases.setdefault(ref, set()).add(normalized(base))
            if ref in loaded:
                continue
            try:
                _, ext, _, data = pdf.extract_font(ref)
                if ext == 'cff':
                    cff = CFFFontSet()
                    cff.decompile(io.BytesIO(data), None)
                    top = cff.topDictIndex[0]
                    matrix = top.FontMatrix
                    if matrix[1:3] != [0, 0] or matrix[0] != matrix[3] or matrix[4:] != [0, 0]:
                        raise ValueError('Unsupported font transform')
                    loaded[ref] = (top.CharStrings, top.charset, matrix[0], {})
                    aliases[ref].update(normalized(n) for n in cff.fontNames)
                else:
                    font = TTFont(io.BytesIO(data))
                    loaded[ref] = (font.getGlyphSet(), font.getGlyphOrder(), 1/font['head'].unitsPerEm, {})
                    aliases[ref].update(normalized(font['name'].getDebugName(n) or '') for n in (4, 6))
            except Exception:
                loaded[ref] = None
        for trace in page.get_texttrace():
            proof = proofs.setdefault(trace['font'], FontProof())
            refs = {row[0] for row in resources if normalized(trace['font']) in aliases[row[0]]}
            if len(refs) != 1:
                proof.complete = False
                continue
            ref = next(iter(refs))
            try:
                glyphset, order, scale, cache = loaded[ref]
                for code, gid, *_ in trace['chars']:
                    if code < 32:
                        continue
                    if gid not in cache:
                        cache[gid] = signature(glyphset, order[gid], scale)
                    digest, width = cache[gid]
                    proof.glyphs.setdefault(code, set()).add(digest)
                    proof.widths.setdefault(code, set()).add(width)
            except Exception:
                # Unsupported/absent embedded fonts need an explicit user choice.
                proof.complete = False
    return proofs


@lru_cache(maxsize=128)
def installed_signatures(path, modified, codes):
    with TTFont(path) as font:
        glyphset, cmap = font.getGlyphSet(), font.getBestCmap() or {}
        return {code: signature(glyphset, cmap[code], 1/font['head'].unitsPerEm)[0]
                for code in codes if code in cmap}


def match_status(infos, name, face):
    """verified / different / unverified, across every document using this name."""
    relevant = [info for info in infos if not info.error and name in info.fonts]
    proofs = [info.font_proofs.get(name) for info in relevant]
    if not proofs or any(p is None or not p.complete or not p.glyphs for p in proofs):
        return 'unverified'
    codes = tuple(sorted({code for proof in proofs for code in proof.glyphs}))
    try:
        actual = installed_signatures(face.path, Path(face.path).stat().st_mtime_ns, codes)
        for proof in proofs:
            if any(expected != {actual.get(code)} for code, expected in proof.glyphs.items()):
                return 'different'
    except Exception:
        return 'unverified'
    return 'verified'


@lru_cache(maxsize=256)
def file_digest(path, modified):
    return hashlib.sha256(Path(path).read_bytes()).digest()


def family_conflicts(face, faces):
    """Word selects a family/style, not a file path; conflicting versions are unsafe."""
    key = lambda f: (normalized(f.family), f.bold, f.italic)
    candidates = [f for f in faces if key(f) == key(face)] + [face]
    try:
        return len({file_digest(f.path, Path(f.path).stat().st_mtime_ns) for f in candidates}) > 1
    except OSError:
        return True


def automatic_mapping(infos, faces):
    """Names narrow candidates, glyphs verify them. Ambiguity always needs a choice."""
    chars = {}
    for info in infos:
        if not info.error:
            for name, text in info.fonts.items():
                chars[name] = chars.get(name, '') + text
    mapping = {}
    for name, text in chars.items():
        matches = [face for face in faces if face.matches(name) and not missing_glyphs(face, text)
                   and match_status(infos, name, face) == 'verified' and not family_conflicts(face, faces)]
        if len(matches) == 1:
            mapping[name] = matches[0]
    return mapping
