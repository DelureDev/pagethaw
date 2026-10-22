from dataclasses import replace
from pathlib import Path
import json
import os
import zipfile
import xml.etree.ElementTree as ET

import pymupdf
import pytest

from pagethaw.engine import inspect_pdf, convert_pdf, convert_batch, W, V
from pagethaw.fonts import read_font, normalized, missing_glyphs


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


def test_duplicate_names_rejected_before_conversion(tmp_path, face):
    info = inspect_pdf(make_pdf(tmp_path, face))
    with pytest.raises(FileExistsError, match='Duplicate'):
        convert_batch([info, info], tmp_path/'out', mapping(info, face))
    assert not list((tmp_path/'out').glob('*.docx'))


def test_batch_continues_independent_valid_file(tmp_path, face):
    valid = inspect_pdf(make_pdf(tmp_path, face))
    invalid = inspect_pdf(make_pdf(tmp_path, face, name='hidden.pdf', render_mode=3))
    results = convert_batch([invalid, valid], tmp_path/'out', mapping(valid, face))
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
