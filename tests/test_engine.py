from dataclasses import replace
from pathlib import Path
import json
import os
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET

import pymupdf
import pytest

from pagethaw.engine import inspect_pdf, convert_pdf, convert_batch, W, V
from pagethaw.fonts import read_font, normalized, missing_glyphs


def test_optional_helper_import_cannot_change_conversion_geometry(tmp_path, face):
    source = make_pdf(tmp_path, face)
    script = '''
from pathlib import Path
import sys
import pymupdf
# Tight glyph boxes make this fixture sensitive to metric corrections.
pymupdf.TOOLS.set_small_glyph_heights(True)
pymupdf.TOOLS.unset_quad_corrections(sys.argv[1] == "True")
from pagethaw.engine import inspect_pdf, convert_pdf
from pagethaw.fonts import read_font
info = inspect_pdf(Path(sys.argv[2]))
face = read_font(Path(sys.argv[3]), installed=True)
convert_pdf(info, Path(sys.argv[4]), {name: face for name in info.fonts})
'''
    outputs = [tmp_path/'core.docx', tmp_path/'optional-helper.docx']
    for setting, output in zip(('False', 'True'), outputs):
        subprocess.run([sys.executable, '-c', script, setting, str(source),
                        face.path, str(output)], check=True, timeout=30)
    with zipfile.ZipFile(outputs[0]) as core, zipfile.ZipFile(outputs[1]) as helper:
        assert core.read('word/document.xml') == helper.read('word/document.xml')


def test_unused_font_is_not_opened(tmp_path, face):
    info = inspect_pdf(make_pdf(tmp_path, face))
    fonts = mapping(info, face)
    fonts['UnusedFont'] = replace(face, path=str(tmp_path/'missing.ttf'))
    assert convert_pdf(info, tmp_path/'result.docx', fonts)['content_check'] == 'passed'


def test_whitespace_only_font_is_in_preflight(tmp_path, face):
    source = tmp_path/'spaces.pdf'
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_font(fontname='fixture', fontfile=face.path)
        page.insert_text((30, 60), 'Visible', fontname='fixture')
        page.insert_text((30, 90), '     ', fontname='cour')
        pdf.save(source)
    info = inspect_pdf(source)
    assert 'Courier' in info.fonts
    assert not info.error
    result = convert_batch([info], tmp_path/'out', {n: face for n in info.fonts if n != 'Courier'})
    assert 'Choose a font for Courier' in result[0]['error']
    result = convert_batch([info], tmp_path/'out', mapping(info, face))
    assert result[0]['content_check'] == 'passed'


def test_font_changed_since_selection_is_rejected(tmp_path, face):
    info = inspect_pdf(make_pdf(tmp_path, face))
    changed = tmp_path/'changed.ttf'
    changed.write_bytes(Path(face.path).read_bytes()+b'changed')
    with pytest.raises(ValueError, match='Installed fonts changed'):
        convert_pdf(info, tmp_path/'result.docx', mapping(info, replace(face, path=str(changed))))
    assert not (tmp_path/'result.docx').exists()


def test_cancellation_during_font_proof_scan_propagates(tmp_path, face, monkeypatch):
    import threading
    from pagethaw import engine
    source = make_pdf(tmp_path, face, pages=2)
    event = threading.Event()
    original = engine.pdf_font_proofs
    def cancel_proof(pdf, cancel):
        cancel.set()
        return original(pdf, cancel=cancel)
    monkeypatch.setattr(engine, 'pdf_font_proofs', cancel_proof)
    with pytest.raises(InterruptedError, match='Scan cancelled'):
        inspect_pdf(source, cancel=event)


def test_damaged_and_missing_pdf_errors_are_readable(tmp_path):
    bad = tmp_path/'broken.pdf'
    bad.write_bytes(b'not a PDF')
    assert 'damaged or unreadable' in inspect_pdf(bad).error
    assert 'not found' in inspect_pdf(tmp_path/'absent.pdf').error


def test_cancel_before_save_leaves_no_output(tmp_path, face, monkeypatch):
    import threading
    from pagethaw import engine
    info = inspect_pdf(make_pdf(tmp_path, face))
    event = threading.Event()
    original = engine.append_shape
    def cancel_after_shape(*args):
        original(*args)
        event.set()
    monkeypatch.setattr(engine, 'append_shape', cancel_after_shape)
    result = convert_batch([info, info], tmp_path/'out', mapping(info, face), cancel=event)
    assert [r['status'] for r in result] == ['cancelled', 'cancelled']
    assert not list((tmp_path/'out').iterdir())


@pytest.fixture
def face():
    path = Path(os.environ.get('WINDIR', 'C:/Windows'))/'Fonts'/'arial.ttf'
    if not path.exists():
        pytest.skip('Windows Arial is required for these synthetic fixtures.')
    return read_font(path, installed=True)


def make_pdf(tmp_path, face, text='Name: __________   account_id', *, name='sample.pdf', pages=1, render_mode=0, stretch=False):
    path = tmp_path/name
    with pymupdf.open() as pdf:
        for _ in range(pages):
            page = pdf.new_page()
            page.insert_font(fontname='fixture', fontfile=face.path)
            extra = {'morph': (pymupdf.Point(30, 60), pymupdf.Matrix(2, 1))} if stretch else {}
            page.insert_text((30, 60), text, fontname='fixture', fontsize=12, render_mode=render_mode, **extra)
            page.draw_rect(pymupdf.Rect(30, 80, 400, 140), color=(0, 0, 0))
        pdf.save(path)
    return path


def content(path):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read('word/document.xml'))
        assert any(n.startswith('word/media/') for n in z.namelist())
    return root, ''.join(t.text or '' for t in root.iter('{'+W+'}t'))


def mapping(info, face):
    return {name: face for name in info.fonts}


def source_text(path):
    # Arial's shared space glyph can decode to NBSP in a generated PDF. Preserve
    # the actual PDF Unicode exactly, then also check the intended visible text.
    with pymupdf.open(path) as pdf:
        return ''.join(c['c'] for page in pdf for block in page.get_text('rawdict')['blocks']
                       for line in block.get('lines', []) for span in line['spans'] for c in span['chars'])


def test_editable_text_literal_underscores_and_pages(tmp_path, face):
    source = make_pdf(tmp_path, face, 'account_id https://example.test/a_b __ ______', pages=2)
    info = inspect_pdf(source)
    target = tmp_path/'result.docx'
    result = convert_pdf(info, target, mapping(info, face))
    assert result['content_check'] == 'passed'
    root, text = content(target)
    assert text == source_text(source)
    assert text.replace('\xa0', ' ') == 'account_id https://example.test/a_b __ ______'*2
    assert len(list(root.iter('{'+V+'}line'))) == 0
    assert len(root.find('{'+W+'}body').findall('{'+W+'}p')) == 2


def test_rules_require_option_and_do_not_destroy_identifiers(tmp_path, face):
    info = inspect_pdf(make_pdf(tmp_path, face, 'account_id a___b Name: ______'))
    target = tmp_path/'rules.docx'
    convert_pdf(info, target, mapping(info, face), rules=True)
    root, text = content(target)
    assert text == source_text(info.path).replace('______', '')
    assert text.replace('\xa0', ' ') == 'account_id a___b Name: '
    assert len(list(root.iter('{'+V+'}line'))) == 1


@pytest.mark.parametrize('mode', [1, 2, 3])
def test_non_filled_and_hidden_text_rejected(tmp_path, face, mode):
    info = inspect_pdf(make_pdf(tmp_path, face, render_mode=mode))
    assert 'hidden, transparent or outlined' in info.error


def test_stretched_text_rejected_before_output(tmp_path, face):
    info = inspect_pdf(make_pdf(tmp_path, face, 'Scaled text must not silently change', stretch=True))
    target = tmp_path/'stretched.docx'
    assert not info.error
    assert all(face.matches(n) for n in info.fonts)
    with pytest.raises(ValueError, match='stretched or unusually spaced'):
        convert_pdf(info, target, mapping(info, face))
    assert not target.exists()


def test_stretched_single_letter_words_are_still_rejected(tmp_path, face):
    info = inspect_pdf(make_pdf(tmp_path, face, 'a a a a a a a a a a a', stretch=True))
    with pytest.raises(ValueError, match='stretched or unusually spaced'):
        convert_pdf(info, tmp_path/'short-words.docx', mapping(info, face))


@pytest.mark.parametrize('rules', [False, True])
def test_justified_spaces_preserve_text_and_word_origins(tmp_path, face, rules):
    from fontTools.ttLib import TTFont
    from pagethaw.engine import segments
    import re
    source = make_pdf(tmp_path, face, 'First  second\xa0third _____ last')
    with TTFont(face.path) as f:
        space = f'{f.getGlyphID(f.getBestCmap()[32]):04x}'.encode()
    # PDF TJ shifts only word spaces; glyphs themselves remain at natural scale.
    with pymupdf.open(source) as pdf:
        xref = pdf[0].get_contents()[0]
        stream = pdf.xref_stream(xref)
        def spaced(match):
            codes = [match[1][i:i+4] for i in range(0, len(match[1]), 4)]
            return b'<' + b''.join(c + (b'> -300 <' if c == space else b'') for c in codes) + b'>'
        pdf.update_stream(xref, re.sub(rb'<([0-9a-f]+)>', spaced, stream))
        justified = tmp_path/'justified.pdf'
        pdf.save(justified)
    info = inspect_pdf(justified)
    target = tmp_path/'justified.docx'
    convert_pdf(info, target, mapping(info, face), rules=rules)
    root, text = content(target)
    expected = source_text(justified)
    assert text == (expected.replace('_____', '') if rules else expected)
    with pymupdf.open(justified) as pdf:
        parts = list(segments(pdf[0], rules, {n: pymupdf.Font(fontfile=face.path) for n in info.fonts}))
        assert len(parts) >= 5
        assert all(s['text'] == ''.join(c['c'] for c in s['chars']) for s in parts)
        starts = [s['bbox'][0] for s in parts if not s['rule']]
    shapes = [s for s in root.iter('{'+V+'}shape') if s.get('id', '').startswith('text')]
    positions = [float(re.search(r'margin-left:([\d.]+)pt', s.get('style'))[1]) for s in shapes]
    assert positions == pytest.approx(starts, abs=.001)


def test_ordinary_text_is_not_split_into_words(tmp_path, face):
    from pagethaw.engine import segments
    info = inspect_pdf(make_pdf(tmp_path, face, 'Ordinary text stays grouped'))
    with pymupdf.open(info.path) as pdf:
        parts = list(segments(pdf[0], fonts={n: pymupdf.Font(fontfile=face.path) for n in info.fonts}))
    assert len(parts) == 1


def test_missing_font_requires_explicit_mapping(tmp_path, face):
    info = inspect_pdf(make_pdf(tmp_path, face))
    with pytest.raises(ValueError, match='Choose a font'):
        convert_pdf(info, tmp_path/'missing.docx', {})
    assert not (tmp_path/'missing.docx').exists()


def test_uninstalled_font_rejected(tmp_path, face):
    info = inspect_pdf(make_pdf(tmp_path, face))
    with pytest.raises(ValueError, match='Install'):
        convert_pdf(info, tmp_path/'missing.docx', mapping(info, replace(face, installed=False)))


def test_existing_output_unchanged(tmp_path, face):
    info = inspect_pdf(make_pdf(tmp_path, face))
    target = tmp_path/'old.docx'
    target.write_bytes(b'keep this')
    with pytest.raises(FileExistsError):
        convert_pdf(info, target, mapping(info, face))
    assert target.read_bytes() == b'keep this'


def test_duplicate_names_get_distinct_outputs_without_reports(tmp_path, face):
    info = inspect_pdf(make_pdf(tmp_path, face))
    output = tmp_path/'out'
    results = convert_batch([info, info], output, mapping(info, face))
    assert [r['output'] for r in results] == ['sample.docx', 'sample (2).docx']
    assert all(r['content_check'] == 'passed' for r in results)
    assert {p.name for p in output.iterdir()} == {'sample.docx', 'sample (2).docx'}


def test_repeated_batch_preserves_old_files_and_ignores_legacy_report(tmp_path, face):
    info = inspect_pdf(make_pdf(tmp_path, face))
    output = tmp_path/'out'
    output.mkdir()
    (output/'SAMPLE.docx').write_bytes(b'previous document')
    (output/'pagethaw-report.json').write_text('previous report')
    (output/'sample (2).partial.docx').write_bytes(b'previous partial file')
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    results = convert_batch([info], output, mapping(info, face))
    assert results[0]['output'] == 'sample (3).docx'
    assert results[0]['content_check'] == 'passed'
    assert all((output/name).read_bytes() == data for name, data in before.items())
    assert set(p.name for p in output.iterdir()) == set(before) | {'sample (3).docx'}


def test_batch_continues_independent_valid_file(tmp_path, face):
    valid = inspect_pdf(make_pdf(tmp_path, face))
    invalid = inspect_pdf(make_pdf(tmp_path, face, name='hidden.pdf', render_mode=3))
    results = convert_batch([invalid, valid], tmp_path/'out', mapping(valid, face), write_report=True)
    assert results[0]['status'] == 'failed'
    assert results[1]['content_check'] == 'passed'
    assert json.loads((tmp_path/'out'/'pagethaw-report.json').read_text())['visual_review'].startswith('not run')


@pytest.mark.parametrize('kind,expected', [('scan','no selectable'), ('rotation','rotated'), ('sizes','Mixed page'), ('widget','interactive'), ('encrypted','unlocked')])
def test_unsupported_inputs(tmp_path, face, kind, expected):
    path = tmp_path/'unsupported.pdf'
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        if kind != 'scan':
            page.insert_text((30, 60), 'Visible text')
        if kind == 'rotation':
            page.set_rotation(90)
        if kind == 'sizes':
            pdf.new_page(width=300, height=400)
        if kind == 'widget':
            widget = pymupdf.Widget()
            widget.field_name = 'field'
            widget.field_type = pymupdf.PDF_WIDGET_TYPE_TEXT
            widget.rect = pymupdf.Rect(30, 90, 200, 120)
            page.add_widget(widget)
        if kind == 'encrypted':
            pdf.save(path, encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw='owner', user_pw='user')
        else:
            pdf.save(path)
    assert expected in inspect_pdf(path).error


def test_regular_bold_italic_faces_and_cyrillic(tmp_path, face):
    for filename, bold, italic in [('arial.ttf',False,False), ('arialbd.ttf',True,False), ('ariali.ttf',False,True)]:
        selected = read_font(Path(face.path).with_name(filename), installed=True)
        assert (selected.bold, selected.italic) == (bold, italic)
        source = make_pdf(tmp_path, selected, 'Sample / Пример / café', name=filename+'.pdf')
        info = inspect_pdf(source)
        target = tmp_path/(filename+'.docx')
        convert_pdf(info, target, mapping(info, selected))
        root, text = content(target)
        assert text == source_text(source)
        assert text.replace('\xa0', ' ') == 'Sample / Пример / café'
        assert any(b.get('{'+W+'}val') == str(int(bold)) for b in root.iter('{'+W+'}b'))
        assert any(b.get('{'+W+'}val') == str(int(italic)) for b in root.iter('{'+W+'}i'))


def test_font_name_normalization_and_coverage(face):
    assert normalized('ABCDEF+Example-Bold') == normalized('Example Bold')
    assert not missing_glyphs(face, 'Latin / Кириллица / café')
    assert missing_glyphs(face, '\U0010ffff')


def test_cancellation_creates_no_deliverable(tmp_path, face):
    import threading
    info = inspect_pdf(make_pdf(tmp_path, face))
    cancel = threading.Event()
    cancel.set()
    records = convert_batch([info], tmp_path/'out', mapping(info, face), cancel=cancel)
    assert records[0]['status'] == 'cancelled'
    assert not list((tmp_path/'out').glob('*.docx'))


def test_changed_input_rejected(tmp_path, face):
    path = make_pdf(tmp_path, face)
    info = inspect_pdf(path)
    path.write_bytes(path.read_bytes()+b'\n% edited after scan\n')
    with pytest.raises(ValueError, match='changed after scanning'):
        convert_pdf(info, tmp_path/'changed.docx', mapping(info, face))


def test_write_failure_removes_owned_final_output(tmp_path, face, monkeypatch):
    info = inspect_pdf(make_pdf(tmp_path, face))
    target = tmp_path/'disk-full.docx'
    original = Path.open
    class FailingWriter:
        def __enter__(self):
            self.stream = original(target, 'xb')
            return self
        def write(self, data):
            self.stream.write(data[:16])
            raise OSError('simulated disk full')
        def __exit__(self, *args):
            self.stream.close()
    def failing_open(path, mode='r', *args, **kwargs):
        return FailingWriter() if path == target and mode == 'xb' else original(path, mode, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', failing_open)
    with pytest.raises(OSError, match='simulated disk full'):
        convert_pdf(info, target, mapping(info, face))
    assert not target.exists()
    assert not target.with_suffix('.partial.docx').exists()
