"""Synthetic test that can also run inside the frozen portable application."""
from pathlib import Path
import json
import pymupdf

from .engine import inspect_pdf, convert_batch
from .fonts import installed_fonts


def run(folder):
    folder = Path(folder).resolve()
    folder.mkdir(parents=True, exist_ok=False)
    faces = installed_fonts()
    face = next((f for f in faces if f.family == 'Arial' and not f.bold and not f.italic), None)
    if face is None:
        raise RuntimeError('The synthetic smoke test needs the Windows Arial regular font.')
    source = folder/'synthetic-form.pdf'
    with pymupdf.open() as pdf:
        for page_number in range(2):
            page = pdf.new_page()
            page.insert_font(fontname='testfont', fontfile=face.path)
            page.insert_text((35, 55), f'PageThaw sample form — page {page_number+1}', fontname='testfont', fontsize=16)
            page.insert_text((35, 90), 'Name: _____________________', fontname='testfont', fontsize=11)
            page.insert_text((35, 115), 'Reference: account_id / Test 123', fontname='testfont', fontsize=11)
            page.draw_rect(pymupdf.Rect(30, 140, 560, 240), color=(.1, .5, .55))
            page.insert_text((40, 165), 'An editable form with a retained graphic border.', fontname='testfont', fontsize=11)
        pdf.save(source)
    info = inspect_pdf(source)
    assert not info.error, info.error
    records = convert_batch([info], folder/'output', {name: face for name in info.fonts})
    assert records[0].get('content_check') == 'passed', records
    (folder/'smoke-result.json').write_text(json.dumps({'status': 'passed', 'pages': 2, 'records': records}, indent=2), encoding='utf-8')
    return records
