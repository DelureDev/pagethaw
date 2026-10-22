"""Synthetic test that can also run inside the frozen portable application."""
from pathlib import Path
import json
import sys
import os
import pymupdf

from .engine import inspect_pdf, convert_batch
from .fonts import installed_fonts


def run(folder, compare=False):
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
    output = folder/'output'
    records = convert_batch([info], output, {name: face for name in info.fonts})
    assert records[0].get('content_check') == 'passed', records
    original = (output/records[0]['output']).read_bytes()
    repeated = convert_batch([info], output, {name: face for name in info.fonts}, rules=True)
    assert repeated[0].get('content_check') == 'passed', repeated
    assert repeated[0]['output'] == 'synthetic-form (2).docx'
    assert (output/records[0]['output']).read_bytes() == original
    assert {p.name for p in output.iterdir()} == {'synthetic-form.docx', 'synthetic-form (2).docx'}
    comparison = 'not run'
    if compare:
        from .word_review import review_batch
        review_batch([info], output, records=repeated, review_output=folder/'review')
        results = json.loads((folder/'review/comparison-report.json').read_text(encoding='utf-8'))
        assert results[0].get('page_count_check') == 'passed', results
        assert len(list((folder/'review/comparisons/1').glob('page-*.png'))) == 2
        comparison = 'exported; visual inspection required'
    from . import gui
    old_local = os.environ.get('LOCALAPPDATA')
    os.environ['LOCALAPPDATA'] = str(folder/'test-profile')
    app = None
    try:
        app = gui.App()
        app.withdraw()
        app.language.set('en')
        app.switch_language()
        assert app.language.get() == 'ru'
        assert app.font_frame.winfo_manager() == 'grid'
        app.switch_language()
        assert app.language.get() == 'en'
        assert app.font_frame.winfo_manager() == 'grid'
        app.update_idletasks()
    finally:
        if app:
            app.close()
        if old_local is None:
            os.environ.pop('LOCALAPPDATA', None)
        else:
            os.environ['LOCALAPPDATA'] = old_local
    bundled = 'not applicable'
    if getattr(sys, 'frozen', False):
        root = Path(sys._MEIPASS).resolve()
        for name in ('pymupdf', 'docx', 'fontTools', 'PIL', 'tkinter'):
            module = __import__(name)
            assert Path(module.__file__).resolve().is_relative_to(root), name
        bundled = 'passed'
    (folder/'smoke-result.json').write_text(json.dumps({'status': 'passed', 'pages': 2, 'records': records,
        'frozen': bool(getattr(sys, 'frozen', False)), 'bundled_runtime': bundled, 'gui': 'passed',
        'repeat_conversion': 'passed', 'output_only_docx': 'passed', 'comparison': comparison}, indent=2), encoding='utf-8')
    return records
