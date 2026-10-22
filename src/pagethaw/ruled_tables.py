"""Recognize complete, axis-aligned ruled grids; leave ambiguous paths untouched."""
from dataclasses import dataclass
import pymupdf

TOLERANCE = .6


@dataclass
class Grid:
    xs: list
    ys: list
    horizontal: list
    vertical: list
    drawings: set

    @property
    def bbox(self):
        return pymupdf.Rect(self.xs[0], self.ys[0], self.xs[-1], self.ys[-1])


def coordinates(values):
    groups = []
    for v in sorted(values):
        if groups and v-groups[-1][0] <= TOLERANCE:
            groups[-1].append(v)
        else:
            groups.append([v])
    return [sum(g)/len(g) for g in groups]


def find_grids(drawings):
    segments = []
    for index, draw in enumerate(drawings):
        if (draw['type'] != 's' or len(draw['items']) != 1 or
                draw.get('stroke_opacity', 1) != 1 or draw.get('dashes', '[] 0').replace(' ', '') != '[]0'):
            continue
        item = draw['items'][0]
        if item[0] == 'l':
            edges = [(item[1], item[2])]
        elif item[0] == 're':
            r = item[1]
            edges = [(r.tl, r.tr), (r.tr, r.br), (r.br, r.bl), (r.bl, r.tl)]
        else:
            continue
        color = draw.get('color')
        if color is None or len(color) != 3:
            continue
        if draw['width'] > 12:
            continue  # Not representable as a Word line border (maximum 96 eighth-points).
        style = (max(2, round(draw['width']*8)), ''.join(f'{round(c*255):02X}' for c in color))
        for a, b in edges:
            if abs(a.y-b.y) < .05 and abs(a.x-b.x) > 4:
                segments.append(('h', (a.y+b.y)/2, min(a.x, b.x), max(a.x, b.x), style, index))
            elif abs(a.x-b.x) < .05 and abs(a.y-b.y) > 4:
                segments.append(('v', (a.x+b.x)/2, min(a.y, b.y), max(a.y, b.y), style, index))
    def rect(s):
        kind, at, start, end, *_ = s
        return pymupdf.Rect(start, at, end, at) if kind == 'h' else pymupdf.Rect(at, start, at, end)
    components = []
    for segment in segments:
        group, bounds = [segment], rect(segment)
        again = True
        while again:
            again = False
            for old in list(components):
                if any((rect(a)+(-TOLERANCE, -TOLERANCE, TOLERANCE, TOLERANCE)).intersects(rect(b)+(-.01, -.01, .01, .01))
                       for a in group for b in old):
                    group.extend(old)
                    components.remove(old)
                    again = True
        components.append(group)
    grids = []
    for group in components:
        xs = coordinates(s[1] for s in group if s[0] == 'v')
        ys = coordinates(s[1] for s in group if s[0] == 'h')
        if len(xs) < 2 or len(ys) < 2 or len(xs) > 21 or len(ys) > 101:
            continue
        if min(b-a for a, b in zip(xs, xs[1:])) < 10 or min(b-a for a, b in zip(ys, ys[1:])) < 8:
            continue
        # A single original rectangle is handled by the existing form-container
        # logic, including underscore fields and their captions.
        ids = {s[5] for s in group}
        if len(xs) == len(ys) == 2 and len(ids) == 1:
            continue
        styles = {'h': [], 'v': []}
        valid = True
        for kind, positions, start, end in [('h', ys, xs[0], xs[-1]), ('v', xs, ys[0], ys[-1])]:
            for at in positions:
                pieces = sorted([s for s in group if s[0] == kind and abs(s[1]-at) <= TOLERANCE], key=lambda s:s[2])
                coverage = start
                if not pieces or len({s[4] for s in pieces}) != 1:
                    valid = False
                    break
                for s in pieces:
                    if s[2] > coverage+TOLERANCE or s[2] < start-TOLERANCE or s[3] > end+TOLERANCE:
                        valid = False
                    coverage = max(coverage, s[3])
                if abs(coverage-end) > TOLERANCE:
                    valid = False
                styles[kind].append(pieces[0][4])
        # Never consume a partially recognized drawing (e.g. tiny extra strokes).
        for index in ids:
            required = 4 if drawings[index]['items'][0][0] == 're' else 1
            if sum(s[5] == index for s in group) != required:
                valid = False
        if valid:
            grids.append(Grid(xs, ys, styles['h'], styles['v'], ids))
    return grids


def partition(grid, lines, reject):
    """Derive cell order from source geometry before emitting any Word content."""
    cells = [[[] for _ in grid.xs[:-1]] for _ in grid.ys[:-1]]
    consumed = set()
    for line in lines:
        if not grid.bbox.intersects(line.bbox):
            continue
        fragments = {}
        previous = None
        for span in line.spans:
            by_cell = {}
            for char in span['chars']:
                box = pymupdf.Rect(char['bbox'])
                x, y = (box.x0+box.x1)/2, (box.y0+box.y1)/2
                col = next((i for i, (a, b) in enumerate(zip(grid.xs, grid.xs[1:])) if a <= x < b), None)
                row = next((i for i, (a, b) in enumerate(zip(grid.ys, grid.ys[1:])) if a <= y < b), None)
                if row is None or col is None:
                    if char['c'].strip():
                        reject('text crosses a ruled table boundary.')
                    continue
                cell = pymupdf.Rect(grid.xs[col], grid.ys[row], grid.xs[col+1], grid.ys[row+1])
                if char['c'].strip() and not (cell+(-1, -1, 1, 1)).contains(box):
                    reject('text crosses a ruled table cell.')
                if char['c'].strip():
                    if previous and previous[0] != (row, col) and box.x0-previous[1] < max(2, span['size']*.75):
                        reject('text crosses a ruled table cell.')
                    previous = ((row, col), box.x1)
                by_cell.setdefault((row, col), []).append(char)
            for identity, chars in by_cell.items():
                box = pymupdf.Rect(chars[0]['bbox'])
                for char in chars[1:]:
                    box |= pymupdf.Rect(char['bbox'])
                fragments.setdefault(identity, []).append(dict(span, chars=chars, bbox=tuple(box), origin=chars[0]['origin']))
        for (row, col), spans in fragments.items():
            box = pymupdf.Rect(spans[0]['bbox'])
            for span in spans[1:]:
                box |= pymupdf.Rect(span['bbox'])
            cells[row][col].append(type(line)(spans, box, line.block))
        consumed.add(id(line))
    if not any(l.text.strip() for row in cells for cell in row for l in cell):
        reject('an empty drawn box is not a supported editable field.')
    return cells, consumed
