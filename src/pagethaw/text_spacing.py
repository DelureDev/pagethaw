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


class TextSpacing:
    def __init__(self, mapping):
        self.heights = {}
        for name, face in mapping.items():
            try:
                self.heights[name] = _natural_height(face.path, Path(face.path).stat().st_mtime_ns)
            except OSError:
                self.heights[name] = None
        self.single_lines = {}

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
            if style[0] <= delta <= style[0]*style[1] and b.bbox.y0 <= a.bbox.y1:
                candidates.append((a, b, round(delta, 1), style))
        counts = Counter((delta, style) for _, _, delta, style in candidates)
        self.single_lines = {}
        for a, b, delta, style in candidates:
            if counts[delta, style] < 2:
                continue
            for line in (a, b):
                # At a rhythm transition use the roomier local advance.
                self.single_lines[id(line)] = max(self.single_lines.get(id(line), 0), delta)

    def multiple(self, lines):
        style = self.style(lines)
        if style is None:
            return None
        leading = self.measured(lines, style) if len(lines) > 1 else self.single_lines.get(id(lines[0]))
        if leading is None:
            return None
        ratio = leading/(style[0]*style[1])
        # Sub-single leading is intentional, but do not squeeze extreme font
        # metrics. Round upward to Word's 1/240-line resolution.
        if .8 <= ratio <= 1.6:
            return math.ceil(ratio*240)/240
        return None
