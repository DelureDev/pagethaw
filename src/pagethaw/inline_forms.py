"""Conservative recognition of inline squares and paired continuation borders."""
import copy
import pymupdf


def open_border(draw):
    r = pymupdf.Rect(draw['rect'])
    if (draw['type'] != 's' or len(draw['items']) != 3 or r.width < 40 or r.height < 25
            or draw.get('stroke_opacity', 1) != 1 or draw.get('dashes', '[] 0').replace(' ', '') != '[]0'):
        return None
    edges = set()
    for item in draw['items']:
        if item[0] != 'l':
            return None
        a, b = item[1:]
        candidates = {'left': (r.tl, r.bl), 'right': (r.tr, r.br),
                      'top': (r.tl, r.tr), 'bottom': (r.bl, r.br)}
        matches = [name for name, (c, d) in candidates.items()
                   if min(abs(a-c)+abs(b-d), abs(a-d)+abs(b-c)) < .1]
        if len(matches) != 1:
            return None
        edges.add(matches[0])
    if edges == {'left', 'right', 'top'}:
        return 'start'
    if edges == {'left', 'right', 'bottom'}:
        return 'end'


def continuation_borders(pdf):
    result = {}
    for n in range(len(pdf)-1):
        starts = [(i,d) for i,d in enumerate(pdf[n].get_drawings()) if open_border(d) == 'start'
                  and 0 <= pdf[n].rect.height-d['rect'].y1 <= 24]
        ends = [(i,d) for i,d in enumerate(pdf[n+1].get_drawings()) if open_border(d) == 'end'
                and 0 <= d['rect'].y0 <= 24]
        for i,a in starts:
            matches = [(j,b) for j,b in ends if abs(a['rect'].x0-b['rect'].x0) < .5
                       and abs(a['rect'].x1-b['rect'].x1) < .5
                       and abs(a['width']-b['width']) < .1 and a['color'] == b['color']]
            if len(starts) == len(matches) == len(ends) == 1:
                j,b = matches[0]
                result[n,i] = ('start', (n,i))
                result[n+1,j] = ('end', (n,i))
    return result


def attach_square(page, draw, lines):
    """Use only a plain empty square wholly occupying whitespace on one text row.

    An inline picture preserves its actual outline without assuming another font
    contains a checkbox glyph. It moves with the surrounding editable text.
    """
    r = pymupdf.Rect(draw['rect'])
    if (draw['type'] != 's' or len(draw['items']) != 1 or draw['items'][0][0] != 're'
            or not 4 <= r.width <= 18 or abs(r.width-r.height) > .3
            or draw.get('stroke_opacity', 1) != 1
            or draw.get('dashes', '[] 0').replace(' ', '') != '[]0'
            or not 0 < draw['width'] <= 2 or len(draw.get('color') or ()) != 3):
        return False
    candidates = []
    for line in lines:
        for si, span in enumerate(line.spans):
            cs = span['chars']
            hits = [i for i,c in enumerate(cs) if pymupdf.Rect(c['bbox']).intersects(r)]
            if hits and all(cs[i]['c'].isspace() for i in hits):
                a,b = min(hits), max(hits)+1
                extent = pymupdf.Rect(cs[a]['bbox']) | pymupdf.Rect(cs[b-1]['bbox'])
                if (extent.x0 <= r.x0 and extent.x1 >= r.x1
                        and r.y0 <= span['origin'][1] <= r.y1
                        and r.y1-extent.y1 <= 1 and not span.get('inline_square')):
                    candidates.append((line,si,span,a,b))
    if len(candidates) != 1:
        return False
    # Reject a mark/check, other artwork, or selectable text crossing this square.
    if any(pymupdf.Rect(c['bbox']).intersects(r) and not c['c'].isspace()
           for l in lines for s in l.spans for c in s['chars']):
        return False
    if any(d != draw and (r+(-.1,-.1,.1,.1)).intersects(d['rect']+(-.1,-.1,.1,.1))
           and (r.contains(d['rect']) or not d['rect'].contains(r) or d['type'] != 's')
           for d in page.get_drawings()):
        return False
    if any(r.intersects(pymupdf.Rect(i['bbox'])) for i in page.get_image_info()):
        return False
    line,si,span,a,b = candidates[0]
    pieces = []
    for start,end,square in [(0,a,False),(a,b,True),(b,len(span['chars']),False)]:
        if start == end:
            continue
        part = copy.copy(span)
        part['chars'] = span['chars'][start:end]
        rect = pymupdf.Rect(part['chars'][0]['bbox']) | pymupdf.Rect(part['chars'][-1]['bbox'])
        part['bbox'] = tuple(rect)
        part['origin'] = part['chars'][0]['origin']
        if square:
            pad = draw['width']/2
            # Render just the proven outline, never neighboring page content.
            with pymupdf.open() as icon:
                canvas = icon.new_page(width=r.width+2*pad, height=r.height+2*pad)
                canvas.draw_rect(pymupdf.Rect(pad,pad,pad+r.width,pad+r.height),
                                 color=draw['color'], width=draw['width'])
                data = canvas.get_pixmap(matrix=pymupdf.Matrix(4,4),alpha=True).tobytes('png')
            part['inline_square'] = (data, r.width+2*pad, r.height+2*pad)
        pieces.append(part)
    line.spans[si:si+1] = pieces
    return True
