from pathlib import Path
import threading

import pymupdf
import pytest
from docx import Document
from docx.oxml.ns import qn

from pagethaw.editable import build_document, verify_document, UnsupportedLayout
from pagethaw.engine import inspect_pdf, convert_batch, convert_pdf
from pagethaw.fonts import read_font


@pytest.fixture
def face():
    path = Path('C:/Windows/Fonts/arial.ttf')
    if not path.exists():
        pytest.skip('Windows Arial is required for these fixtures.')
    return read_font(path, installed=True)


def source(tmp_path, face, draw=None):
    path = tmp_path/'form.pdf'
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_font(fontname='fixture', fontfile=face.path)
        if draw:
            draw(page)
        else:
            page.insert_text((30, 60), 'Name: __________________', fontname='fixture', fontsize=12)
            page.insert_text((30, 100), 'A paragraph with ordinary editable text.', fontname='fixture', fontsize=12)
        pdf.save(path)
    info = inspect_pdf(path)
    assert not info.error
    return info, {name: face for name in info.fonts}


def test_flowing_text_and_expanding_fields(tmp_path, face):
    info, mapping = source(tmp_path, face)
    target = tmp_path/'result.docx'
    result = convert_pdf(info, target, mapping, mode='editable')
    doc = Document(target)
    assert result['content_check'] == 'passed' and result['fields'] == 1
    assert result['source_pages'] == 1 and 'pages' not in result
    assert not list(doc.element.iter(qn('w:txbxContent')))
    assert not list(doc.element.iter(qn('w:framePr')))
    assert not list(doc.element.iter(qn('w:trHeight')))
    assert any('ordinary editable text' in p.text for p in doc.paragraphs)
    assert len(doc.tables) == 1
    field = doc.tables[0].cell(0, 1)
    field.paragraphs[0].runs[0].text = 'First line\nSecond line\nThird line'
    doc.save(tmp_path/'edited.docx')
    edited = Document(tmp_path/'edited.docx')
    assert 'Third line' in edited.tables[0].cell(0, 1).text
    assert any('ordinary editable text' in p.text for p in edited.paragraphs)


@pytest.mark.parametrize('boxed', [False, True])
@pytest.mark.parametrize('order', ['row', 'column'])
def test_columns_rejected_before_publication(tmp_path, face, boxed, order):
    def draw(page):
        positions = [(column, row) for column in range(2) for row in range(3)]
        if order == 'row':
            positions.sort(key=lambda x: (x[1], x[0]))
        for column, row in positions:
            page.insert_text((35+column*260, 80+row*20), f'Column {column} line {row}', fontname='fixture', fontsize=12)
        if boxed:
            page.draw_rect(pymupdf.Rect(25, 55, 560, 135))
    info, mapping = source(tmp_path, face, draw)
    with pytest.raises(UnsupportedLayout, match='columns'):
        convert_pdf(info, tmp_path/'result.docx', mapping, mode='editable')
    assert not (tmp_path/'result.docx').exists()
    assert not (tmp_path/'result.partial.docx').exists()


@pytest.mark.parametrize('shape', ['vertical', 'four-stroke-box', 'grid'])
def test_unsupported_drawing_cannot_disappear(tmp_path, face, shape):
    def draw(page):
        page.insert_text((35, 50), 'Drawing test', fontname='fixture', fontsize=12)
        if shape == 'vertical':
            page.draw_line((30, 70), (30, 140))
        elif shape == 'four-stroke-box':
            for a, b in [((30, 70), (300, 70)), ((300, 70), (300, 140)), ((300, 140), (30, 140)), ((30, 140), (30, 70))]:
                page.draw_line(a, b)
        else:
            page.draw_rect(pymupdf.Rect(30, 70, 300, 150))
            page.draw_line((30, 110), (300, 110))
            page.insert_text((40, 95), 'Cell', fontname='fixture')
    info, mapping = source(tmp_path, face, draw)
    with pytest.raises(UnsupportedLayout):
        convert_pdf(info, tmp_path/'result.docx', mapping, mode='editable')
    assert not (tmp_path/'result.docx').exists()


def test_cyrillic_wrapped_lines_keep_word_boundary_and_inline_fonts(tmp_path, face):
    bold = read_font(Path('C:/Windows/Fonts/arialbd.ttf'), installed=True)
    def draw(page):
        page.insert_font(fontname='strong', fontfile=bold.path)
        page.insert_text((30, 60), 'Начало предложения и', fontname='fixture', fontsize=12)
        page.insert_text((30, 74), 'продолжение строки.', fontname='fixture', fontsize=12)
        page.insert_text((30, 110), 'Жирный', fontname='strong', fontsize=12)
        x = 30+pymupdf.Font(fontfile=bold.path).text_length('Жирный', fontsize=12)
        page.insert_text((x, 110), 'Текст', fontname='fixture', fontsize=12)
    info, mapping = source(tmp_path, face, draw)
    mapping = {n: bold if 'Bold' in n else face for n in info.fonts}
    with pymupdf.open(info.path) as pdf:
        doc, expected, _ = build_document(pdf, mapping)
    verify_document(doc, expected)
    texts = '\n'.join(p.text for p in doc.paragraphs)
    assert 'и продолжение' in texts
    assert 'ЖирныйТекст' in texts
    assert any(r.bold and r.text == 'Жирный' for p in doc.paragraphs for r in p.runs)
    target_run = next(r for p in doc.paragraphs for r in p.runs if r.text == 'Жирный')
    target_run.bold = False
    with pytest.raises(ValueError, match='emphasis'):
        verify_document(doc, expected)


def test_cancel_and_existing_partial_are_preserved(tmp_path, face):
    info, mapping = source(tmp_path, face)
    target = tmp_path/'result.docx'
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(InterruptedError):
        convert_pdf(info, target, mapping, mode='editable', cancel=cancel)
    assert not target.exists()
    partial = tmp_path/'result.partial.docx'
    partial.write_bytes(b'user-owned')
    with pytest.raises(FileExistsError):
        convert_pdf(info, target, mapping, mode='editable')
    assert partial.read_bytes() == b'user-owned'
    assert not target.exists()


def test_editable_batch_reuses_folder_without_reports(tmp_path, face):
    info, mapping = source(tmp_path, face)
    out = tmp_path/'out'
    first = convert_batch([info], out, mapping, mode='editable')
    original = (out/'form.docx').read_bytes()
    second = convert_batch([info], out, mapping, mode='editable')
    assert first[0]['mode'] == second[0]['mode'] == 'editable'
    assert second[0]['output'] == 'form (2).docx'
    assert (out/'form.docx').read_bytes() == original
    assert {p.suffix for p in out.iterdir()} == {'.docx'}


def test_unknown_mode_does_not_create_output(tmp_path, face):
    info, mapping = source(tmp_path, face)
    with pytest.raises(ValueError, match='Choose Editable'):
        convert_batch([info], tmp_path/'out', mapping, mode='wrong')
    assert not (tmp_path/'out').exists()


def test_narrative_parenthetical_is_not_reordered_as_field_caption(tmp_path, face):
    def draw(page):
        page.insert_text((30, 50), 'Name: _____________________', fontname='fixture', fontsize=12)
        page.insert_text((30, 100), 'Please read these instructions before you fill in the form.', fontname='fixture', fontsize=12)
        page.insert_text((30, 114), '(This instruction applies to all applicants.)', fontname='fixture', fontsize=12)
    info, mapping = source(tmp_path, face, draw)
    target = tmp_path/'result.docx'
    convert_pdf(info, target, mapping, mode='editable')
    doc = Document(target)
    text = '\n'.join(p.text for p in doc.paragraphs)
    assert text.index('Please read') < text.index('(This instruction')
    assert len(doc.tables) == 1


def test_immediate_field_caption_has_its_own_following_row(tmp_path, face):
    def draw(page):
        page.insert_text((30, 50), 'Name: ____________________________', fontname='fixture', fontsize=12)
        page.insert_text((80, 64), '(Full name)', fontname='fixture', fontsize=12)
        page.insert_text((30, 100), 'Following paragraph.', fontname='fixture', fontsize=12)
    info, mapping = source(tmp_path, face, draw)
    target = tmp_path/'result.docx'
    convert_pdf(info, target, mapping, mode='editable')
    doc = Document(target)
    assert len(doc.tables) == 2
    assert '(Full name)' in doc.tables[1].cell(0, 1).text.replace('\xa0', ' ')
    assert all(p.paragraph_format.keep_with_next for c in doc.tables[0].rows[0].cells for p in c.paragraphs)
    separator = doc.tables[0]._tbl.getnext()
    assert separator.find('./'+qn('w:pPr')+'/'+qn('w:keepNext')) is not None
    assert any('Following paragraph.' in p.text for p in doc.paragraphs)


def test_signature_label_stays_with_following_field(tmp_path, face):
    def draw(page):
        page.insert_text((30, 60), 'Signature of applicant', fontname='fixture', fontsize=12)
        page.insert_text((30, 85), '____________________________', fontname='fixture', fontsize=12)
    info, mapping = source(tmp_path, face, draw)
    with pymupdf.open(info.path) as pdf:
        doc, expected, _ = build_document(pdf, mapping)
    verify_document(doc, expected)
    label = next(p for p in doc.paragraphs if 'Signature of applicant' in p.text)
    assert label.paragraph_format.keep_with_next
