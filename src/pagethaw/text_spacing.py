"""Responsive Word leading inferred from uniform PDF text and explicit font metrics.

The OpenType USE_TYPO_METRICS flag supplies a portable natural line height.
Older fonts have renderer-dependent metrics, so retain expanding minimum spacing
when those metrics, source baselines or mixed-size text are uncertain.
"""
from collections import Counter
from functools import lru_cache
from pathlib import Path
from statistics import median
import math
import re
import unicodedata

from fontTools.ttLib import TTFont, TTLibError


@lru_cache(maxsize=128)
def _natural_height(path, modified):
    try:
        with TTFont(path, lazy=True) as font:
            os2 = font['OS/2']
            if 'fvar' in font or os2.version < 4 or not os2.fsSelection & 128:
                return None
            ascent, descent, gap = os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap
            height = (ascent-descent+gap)/font['head'].unitsPerEm
            if ascent > 0 and descent <= 0 and gap >= 0 and 1 <= height <= 2:
                return height
    except (OSError, KeyError, ValueError, ZeroDivisionError, TTLibError):
        pass
    return None


@lru_cache(maxsize=128)
def _minimum_metrics(path, modified):
    """Bound a Windows minimum line box without guessing a natural multiple."""
    try:
        with TTFont(path, lazy=True) as font:
            if 'fvar' in font:
                return None
            os2, hhea, em = font['OS/2'], font['hhea'], font['head'].unitsPerEm
            heights = [os2.usWinAscent+os2.usWinDescent,
                       os2.sTypoAscender-os2.sTypoDescender+os2.sTypoLineGap,
                       hhea.ascent-hhea.descent+hhea.lineGap]
            # Windows and horizontal-layout descent must agree. Fonts selecting
            # typographic metrics also have to agree with that descent.
            descents = [os2.usWinDescent, -hhea.descent]
            if os2.version >= 4 and os2.fsSelection & 128:
                descents.append(-os2.sTypoDescender)
            if (1 <= min(heights)/em <= max(heights)/em <= 2
                    and 0 <= min(descents) <= max(descents) <= em*.5
                    and max(descents)-min(descents) <= em*.002):
                return max(heights)/em, max(descents)/em
    except (OSError, KeyError, ValueError, ZeroDivisionError, TTLibError):
        pass
    return None


@lru_cache(maxsize=128)
def _advances(path, modified):
    try:
        with TTFont(path, lazy=True) as font:
            if 'fvar' in font:
                return None
            return {code: font['hmtx'][glyph][0]/font['head'].unitsPerEm
                    for code, glyph in (font.getBestCmap() or {}).items()}
    except (OSError, KeyError, ValueError, ZeroDivisionError, TTLibError):
        return None


def source_tracking(span, face):
    """Return source advance adjustments for simple text, in Word's twips.

    These are normal character-spacing properties in flowing runs, not glyph
    scaling or positioned objects. Font kerning must be off on these runs: the
    PDF's measured pair adjustments already include it. Unsupported shaping or
    mismatched metrics retain the normal Word shaping path.
    """
    if not face.matches(span['font']):
        return None
    try:
        widths = _advances(face.path, Path(face.path).stat().st_mtime_ns)
    except OSError:
        return None
    chars, size = span['chars'], span['size']
    if not widths or len(chars) < 2:
        return None
    for char in chars:
        c = char['c']
        if (len(c) != 1 or ord(c) not in widths or unicodedata.combining(c)
                or (c.isalpha() and not unicodedata.name(c, '').startswith(('LATIN ', 'CYRILLIC ', 'GREEK ')))):
            return None
    values, carry = [], 0
    for a, b in zip(chars, chars[1:]):
        advance = b['origin'][0]-a['origin'][0]
        adjustment = advance-widths[ord(a['c'])]*size
        # Exclude columns, superscripts, reordered/overlapping shaped clusters
        # and incompatible font versions. Large word gaps use justification.
        if abs(a['origin'][1]-b['origin'][1]) > .1 or advance <= 0:
            return None
        if a['c'].isspace():
            adjustment = min(0, adjustment)
            if adjustment < -size*.15:
                return None
        elif abs(adjustment) > size*.15:
            return None
        exact = adjustment*20+carry
        rounded = round(exact)
        carry = exact-rounded
        values.append(rounded)
    return values+[0]  # never infer spacing across a source line boundary


class TextSpacing:
    def __init__(self, mapping):
        self.mapping = mapping
        self.heights = {}
        for name, face in mapping.items():
            try:
                self.heights[name] = _natural_height(face.path, Path(face.path).stat().st_mtime_ns)
            except OSError:
                self.heights[name] = None
        self.single_lines = {}
        self.paragraph_starts = {}

    def style(self, lines):
        spans = [s for line in lines for s in line.spans]
        sizes = [s['size'] for s in spans]
        heights = [self.heights.get(s['font']) for s in spans]
        if not spans or None in heights or max(sizes)-min(sizes) > .02 or max(heights)-min(heights) > .002:
            return None
        # Reject raised/lowered runs, including same-sized superscripts.
        if any(max(s['origin'][1] for s in line.spans)-min(s['origin'][1] for s in line.spans) > .1 for line in lines):
            return None
        return round(median(sizes), 2), round(median(heights), 3)

    @staticmethod
    def measured(lines, style):
        if not style or len(lines) < 2:
            return None
        gaps = [b.spans[0]['origin'][1]-a.spans[0]['origin'][1] for a, b in zip(lines, lines[1:])]
        leading = median(gaps)
        if style[0] <= leading <= style[0]*1.6 and max(abs(g-leading) for g in gaps) <= .15:
            return leading
        return None

    def flow(self, lines):
        # Single source rows do not reveal their internal wrapping rhythm.
        # Approximate only repeated tight row advances in this same container;
        # never borrow a page-wide body style for a caption or a distant field.
        # Larger gaps retain the existing expanding minimum and space-before.
        candidates = []
        for a, b in zip(lines, lines[1:]):
            style = self.style([a, b])
            if style is None:
                continue
            delta = b.spans[0]['origin'][1]-a.spans[0]['origin'][1]
            if style[0] <= delta <= style[0]*style[1] and b.bbox.y0-a.bbox.y1 <= min(.5, style[0]*.06):
                candidates.append((a, b, round(delta, 1), style))
        counts = Counter((delta, style) for _, _, delta, style in candidates)
        self.single_lines = {}
        for a, b, delta, style in candidates:
            if counts[delta, style] < 2:
                continue
            for line in (a, b):
                # At a rhythm transition use the roomier local advance.
                self.single_lines[id(line)] = max(self.single_lines.get(id(line), 0), delta)

        # A small paragraph gap can be invisible in the font's overlapping
        # bounding boxes. Infer it only from a repeated local line rhythm on
        # both sides and an independent sentence/indent cue.
        self.paragraph_starts = {}
        for index in range(1, len(lines)):
            a, b = lines[index-1:index+1]
            style = self.style([a, b])
            if style is None or a.field or b.field:
                continue
            terminal = bool(re.search(r'[.!?;:…)]\s*$', a.text))
            opening = b.text.lstrip()[:1].isupper() or b.bbox.x0-a.bbox.x0 > max(1, b.size*.15)
            if not (terminal and opening):
                continue
            left, right = [], []
            for j in range(max(1, index-4), min(len(lines), index+5)):
                x, y = lines[j-1:j+1]
                if j == index or self.style([x, y]) != style or x.field or y.field:
                    continue
                advance = y.spans[0]['origin'][1]-x.spans[0]['origin'][1]
                if style[0] <= advance <= style[0]*1.6:
                    (left if j < index else right).append(advance)
            delta = b.spans[0]['origin'][1]-a.spans[0]['origin'][1]
            for leading in sorted(left):
                matches = [v for v in left+right if abs(v-leading) <= .15]
                if (len(matches) >= 3 and any(abs(v-leading) <= .15 for v in right)
                        and .4 <= delta-leading <= style[0]*.5):
                    self.paragraph_starts[id(b)] = median(matches)
                    break

    def leading(self, lines):
        style = self.style(lines)
        if style is None:
            return None
        return self.measured(lines, style) if len(lines) > 1 else self.single_lines.get(id(lines[0]))

    def multiple(self, lines):
        style = self.style(lines)
        if style is None:
            return None
        leading = self.leading(lines)
        if leading is None:
            return None
        ratio = leading/(style[0]*style[1])
        # The measured source advance is already at least the type size, and
        # the explicit natural metric height is bounded to 1–2 em. Some fonts
        # reserve generous ascender space, so an arbitrary 0.8-line floor would
        # expand valid dense source text. Keep the measured responsive rhythm.
        if .5 <= ratio <= 1.6:
            return math.ceil(ratio*240)/240
        return None

    def minimum(self, lines):
        """A measured expanding line box for compatible, same-face source rows.

        A minimum line box aligns unequal sizes by their descents. Correct the
        measured baseline advance only when all candidate boxes agree and are
        at least as tall as every possible natural metric height. Otherwise Word keeps
        its existing expanding fallback. No fixed-height text is introduced.
        """
        spans = [s for line in lines for s in line.spans]
        faces = [self.mapping[s['font']] for s in spans]
        if (not spans or len({f.path for f in faces}) != 1
                or any(not f.matches(s['font']) for f, s in zip(faces, spans))
                or any(max(s['origin'][1] for s in l.spans)-min(s['origin'][1] for s in l.spans) > .1 for l in lines)):
            return None
        path = faces[0].path
        try:
            metrics = _minimum_metrics(path, Path(path).stat().st_mtime_ns)
        except OSError:
            return None
        if metrics is None:
            return None
        upper, descent = metrics
        sizes = [max(s['size'] for s in line.spans) for line in lines]
        # A larger paragraph mark on the last row would change the baseline.
        if abs(sizes[-1]-max(sizes)) > .02:
            return None
        candidates = [b.spans[0]['origin'][1]-a.spans[0]['origin'][1]+(sb-sa)*descent
                      for a, b, sa, sb in zip(lines, lines[1:], sizes, sizes[1:])]
        height = median(candidates) if candidates else sizes[0]*1.2
        if (height < math.ceil(max(sizes)*upper*20-1e-3)/20-.001 or height > max(sizes)*2
                or any(abs(c-height) > .15 for c in candidates)):
            return None
        # Word stores minimum heights in twips. Use the emitted value for the
        # following boundary calculation rather than the unrounded source.
        height = math.ceil(height*20-1e-3)/20
        return height, sizes[0]*descent, sizes[-1]*descent, path
