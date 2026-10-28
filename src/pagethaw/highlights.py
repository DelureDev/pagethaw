"""Turn proven rectangular PDF text highlights into editable run shading.

Annotation appearances are drawings too. Never dismiss an arbitrary text/graphic
overlap: only remove a highlight after validating its appearance and glyph range.
"""
from contextlib import contextmanager
import copy
import math
import pymupdf


def rectangle_path(draw, rect):
    if max(abs(a-b) for a, b in zip(draw['rect'], rect)) > .05:
        return False
    items = draw['items']
    if len(items) == 1 and items[0][0] == 're':
        return True
    if len(items) not in (3, 4) or any(i[0] != 'l' for i in items):
        return False
    points = [items[0][1]]+[i[2] for i in items]
    if any(abs(a[2]-b[1]) > .05 for a, b in zip(items, items[1:])):
        return False
    if len(points) == 5:
        if abs(points[0]-points[-1]) > .05:
            return False
        points.pop()
    corners = [rect.tl, rect.tr, rect.br, rect.bl]
    return any(all(abs(p-corners[(start+direction*i) % 4]) < .05 for i, p in enumerate(points))
               for start in range(4) for direction in (-1, 1))


def validate_blends(pdf, xref, reject, seen=None):
    """Check nested appearance resources, not just annotation /BM metadata."""
    seen = set() if seen is None else seen
    if xref in seen:
        return
    if len(seen) >= 64:
        reject('a complex highlight appearance needs manual conversion.')
    seen.add(xref)

    def dictionary(entry):
        kind, value = entry
        if kind == 'null':
            return None
        if kind == 'xref':
            return int(value.split()[0])
        if kind != 'dict':
            reject('a custom highlight resource needs manual conversion.')
        result = pdf.get_new_xref()
        pdf.update_object(result, value)
        return result

    resources = dictionary(pdf.xref_get_key(xref, 'Resources'))
    if resources is None:
        return
    states = dictionary(pdf.xref_get_key(resources, 'ExtGState'))
    if states:
        for key in pdf.xref_get_keys(states):
            state = dictionary(pdf.xref_get_key(states, key))
            if state is None:
                reject('an empty highlight graphics state needs manual conversion.')
            if pdf.xref_get_key(state, 'BM')[1] not in ('null', '/Multiply'):
                reject('a custom highlight blend mode needs manual conversion.')
    objects = dictionary(pdf.xref_get_key(resources, 'XObject'))
    if objects:
        for key in pdf.xref_get_keys(objects):
            child = dictionary(pdf.xref_get_key(objects, key))
            if child is None:
                reject('an empty highlight resource needs manual conversion.')
            validate_blends(pdf, child, reject, seen)


def validate_appearance(page, index, annot, rects, color, opacity, reject):
    # Isolate the annotation in a private one-page copy. Its AP may contain
    # custom text/images or geometry unrelated to QuadPoints; those stay blocked.
    with pymupdf.open() as isolated:
        isolated.insert_pdf(page.parent, from_page=page.number, to_page=page.number)
        clean = isolated[0]
        annots = list(clean.annots())
        if index >= len(annots) or annots[index].vertices != annot.vertices:
            reject('a highlight annotation could not be isolated.')
        chosen = annots[index]
        kind, appearance = isolated.xref_get_key(chosen.xref, 'AP/N')
        if kind != 'xref':
            reject('a custom highlight appearance needs manual conversion.')
        validate_blends(isolated, int(appearance.split()[0]), reject)
        for i, other in enumerate(annots):
            if i != index:
                clean.delete_annot(other)
        xref = isolated.get_new_xref()
        isolated.update_object(xref, '<<>>')
        isolated.update_stream(xref, b'')
        clean.set_contents(xref)
        drawings = clean.get_drawings()
        if clean.get_texttrace() or clean.get_image_info() or len(drawings) != len(rects):
            reject('a custom highlight appearance needs manual conversion.')
        remaining = list(rects)
        for draw in drawings:
            matches = [r for r in remaining if rectangle_path(draw, r)]
            fill = draw.get('fill') or ()
            if (draw['type'] != 'f' or len(fill) != 3 or
                    any(abs(a-b) > .001 for a, b in zip(fill, color)) or len(matches) != 1):
                reject('only plain rectangular text highlights are supported.')
            remaining.remove(matches[0])
        # get_drawings can omit an AP's nested opacity/clip state. Confirm the
        # actual appearance covers every selected rectangle at the stated alpha.
        if chosen.rect.width > 2000 or chosen.rect.height > 2000:
            reject('an oversized highlight needs manual conversion.')
        pix = chosen.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=True)
        # A declared Multiply state could be unused. On black, a real Multiply
        # highlight leaves every pixel black; ordinary paint/Screen does not.
        clean.draw_rect(clean.rect, color=None, fill=(0, 0, 0), overlay=False)
        black = clean.get_pixmap(matrix=pymupdf.Matrix(2, 2), clip=chosen.rect, alpha=False)
        if any(value > 3 for value in black.samples):
            reject('a highlight appearance does not use the declared blend mode.')
        samples = pix.samples
        checked = 0
        for rect in rects:
            for y in range(math.ceil(rect.y0*2)+1, math.floor(rect.y1*2)-1):
                for x in range(math.ceil(rect.x0*2)+1, math.floor(rect.x1*2)-1):
                    px, py = x-pix.x, y-pix.y
                    if not (0 <= px < pix.width and 0 <= py < pix.height):
                        reject('a highlight appearance does not cover its text.')
                    alpha = samples[py*pix.stride+px*pix.n+pix.n-1]
                    if abs(alpha-opacity*255) > 3:
                        reject('a custom highlight opacity or clipping needs manual conversion.')
                    checked += 1
        if not checked:
            reject('a highlight is too small to verify.')


def extract(page, reject):
    ranges = []
    annotations = list(page.annots())
    for index, annot in enumerate(annotations):
        if annot.type[0] != pymupdf.PDF_ANNOT_HIGHLIGHT:
            continue
        color = annot.colors.get('stroke') or ()
        opacity = annot.opacity if annot.opacity >= 0 else 1
        vertices = annot.vertices or []
        if (len(color) != 3 or not all(0 <= c <= 1 for c in color) or not 0 < opacity <= 1 or
                annot.blendmode not in (None, '', 'Multiply') or not vertices or len(vertices) % 4 or
                annot.flags & (pymupdf.PDF_ANNOT_IS_HIDDEN | pymupdf.PDF_ANNOT_IS_INVISIBLE | pymupdf.PDF_ANNOT_IS_NO_VIEW)):
            reject('this highlight style needs manual conversion.')
        rects = []
        for start in range(0, len(vertices), 4):
            quad = pymupdf.Quad(vertices[start:start+4])
            r = quad.rect
            if (r.is_empty or not page.rect.contains(r) or
                    any(abs(a-b) > .05 for a, b in zip([quad.ul, quad.ur, quad.ll, quad.lr], [r.tl, r.tr, r.bl, r.br]))):
                reject('rotated or skewed highlights need manual conversion.')
            if any(r.intersects(previous) for previous, _ in ranges) or any(r.intersects(previous) for previous in rects):
                reject('overlapping highlights need manual conversion.')
            rects.append(r)
        validate_appearance(page, index, annot, rects, color, opacity, reject)
        shade = ''.join(f'{round((1-opacity+opacity*c)*255):02X}' for c in color)
        ranges.extend((r, shade) for r in rects)
    # Delete only annotations whose appearance was proved above. The source PDF
    # is never changed: this page belongs to prepared_pdf's in-memory copy.
    for annot in annotations:
        if annot.type[0] == pymupdf.PDF_ANNOT_HIGHLIGHT:
            page.delete_annot(annot)
    return ranges


@contextmanager
def prepared_pdf(pdf, reject):
    if not any(a.type[0] == pymupdf.PDF_ANNOT_HIGHLIGHT for p in pdf for a in p.annots()):
        yield pdf, {}
        return
    with pymupdf.open(stream=pdf.tobytes(no_new_id=True), filetype='pdf') as clean:
        ranges = {p.number: extract(p, reject) for p in clean}
        yield clean, ranges


def apply_highlights(lines, ranges, reject):
    hits = [0]*len(ranges)
    for line in lines:
        spans = []
        for span in line.spans:
            groups = []
            for char in span['chars']:
                bbox = pymupdf.Rect(char['bbox'])
                shades = []
                for i, (rect, shade) in enumerate(ranges):
                    if (rect+(-.06, -.06, .06, .06)).contains(bbox):
                        shades.append(shade)
                        if char['c'].strip():
                            hits[i] += 1
                    elif (rect & bbox).get_area() > bbox.get_area()*.5 and char['c'].strip():
                        reject('a highlight cuts through a text character.')
                selected = shades[0] if shades else None
                if not groups or groups[-1][0] != selected:
                    groups.append((selected, []))
                groups[-1][1].append(char)
            for shade, chars in groups:
                part = copy.copy(span)
                part['chars'] = chars
                part['origin'] = chars[0]['origin']
                part['bbox'] = tuple(pymupdf.Rect(chars[0]['bbox']) | pymupdf.Rect(chars[-1]['bbox']))
                if shade:
                    part['highlight_fill'] = shade
                spans.append(part)
        line.spans = spans
    if not all(hits):
        reject('a highlight could not be matched to complete text characters.')
