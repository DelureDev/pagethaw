from dataclasses import replace

import pymupdf
import pytest
from docx import Document
from docx.enum.text import WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Pt
from fontTools.ttLib import TTFont

from pagethaw.editable import build_document, lines_on, verify_document
from pagethaw.fonts import read_font
from pagethaw.text_spacing import TextSpacing
from pagethaw.text_spacing import source_tracking
from pagethaw.editable import Writer
from test_font_embedding import make_font


@pytest.fixture
def tall_font(tmp_path):
    path = tmp_path/'tall.ttf'
    make_font(path)
    with TTFont(path) as font:
        font['OS/2'].version = 4
        font['OS/2'].fsSelection |= 128
        font['OS/2'].sTypoAscender = 1000
        font['OS/2'].sTypoDescender = -300
        font['OS/2'].sTypoLineGap = 20
        font.save(path)
    return read_font(path)


def pdf_lines(face, baselines, texts=None, sizes=None):
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_font(fontname='test', fontfile=face.path)
    for i, y in enumerate(baselines):
        page.insert_text((30, y), (texts or ['ordinary flowing text']*len(baselines))[i],
                         fontname='test', fontsize=(sizes or [10]*len(baselines))[i])
    return pdf, lines_on(page)


def test_multiline_keeps_sizes_with_responsive_leading(tall_font, tmp_path):
    with pdf_lines(tall_font, [60, 72, 84])[0] as pdf:
        mapping = {s['font']:tall_font for l in lines_on(pdf[0]) for s in l.spans}
        doc, expected, _ = build_document(pdf, mapping)
    verify_document(doc, expected)
    target = tmp_path/'flow.docx'
    doc.save(target)
    saved = Document(target)
    para = next(p for p in saved.paragraphs if len(p.runs) > 1)
    assert para.paragraph_format.line_spacing_rule == WD_LINE_SPACING.MULTIPLE
    # Word's line multiple compensates the tall font metrics, not the type size.
    assert 12 <= para.paragraph_format.line_spacing*13.2 <= 12.06
    assert all(r.font.size.pt == 10 for r in para.runs)
    assert not list(saved.element.iter(qn('w:trHeight')))


def test_legacy_font_and_missing_metrics_keep_expanding_fallback(tmp_path):
    face = make_font(tmp_path/'legacy.ttf')
    with pdf_lines(face, [60, 72, 84])[0] as pdf:
        lines = lines_on(pdf[0]); mapping = {s['font']:face for l in lines for s in l.spans}
        doc, _, _ = build_document(pdf, mapping)
        para = next(p for p in doc.paragraphs if p.text)
        assert para.paragraph_format.line_spacing_rule == WD_LINE_SPACING.AT_LEAST
        missing = {name:replace(f, path=str(tmp_path/'absent.ttf')) for name,f in mapping.items()}
        assert TextSpacing(missing).multiple(lines) is None


@pytest.mark.parametrize('baselines,sizes', [([60,72,87],[10,10,10]), ([60,72,84],[10,11,10])])
def test_mixed_sizes_or_irregular_multiline_spacing_not_compressed(tall_font, baselines, sizes):
    pdf, lines = pdf_lines(tall_font, baselines, sizes=sizes)
    try:
        spacing = TextSpacing({s['font']:tall_font for l in lines for s in l.spans})
        assert spacing.multiple(lines) is None
    finally:
        pdf.close()


def test_single_rows_need_repeated_local_evidence_and_reset_between_containers(tall_font):
    pdf, lines = pdf_lines(tall_font, [60,72,84,130])
    try:
        spacing = TextSpacing({s['font']:tall_font for l in lines for s in l.spans})
        spacing.flow(lines)
        assert spacing.multiple([lines[1]]) is not None
        assert spacing.multiple([lines[3]]) is None  # not the page's body default
        spacing.flow(lines[:2])
        assert spacing.multiple([lines[0]]) is None  # one pair is insufficient
        spacing.flow(lines[3:])
        assert spacing.multiple([lines[1]]) is None  # no stale container evidence
    finally:
        pdf.close()


def test_small_paragraph_gap_splits_full_lines_and_retains_spacing(tall_font):
    texts = ['A'*54, 'a'*54, 'a'*53+'.', 'B'*54, 'b'*54, 'b'*53+'.']
    with pdf_lines(tall_font, [60, 72, 84, 97, 109, 121], texts)[0] as pdf:
        lines = lines_on(pdf[0])
        mapping = {s['font']:tall_font for l in lines for s in l.spans}
        doc, expected, _ = build_document(pdf, mapping)
    verify_document(doc, expected)
    paragraphs = [p for p in doc.paragraphs if p.text]
    assert len(paragraphs) == 2
    assert paragraphs[1].text.startswith('B')
    assert all(p.paragraph_format.line_spacing_rule == WD_LINE_SPACING.MULTIPLE for p in paragraphs)
    assert paragraphs[1].paragraph_format.space_before.pt == pytest.approx(1, abs=.05)
    assert all(r.font.size.pt == 10 for p in paragraphs for r in p.runs)


def test_repeated_compact_rows_allow_small_positive_box_gap_without_double_spacing(tall_font):
    pdf, lines = pdf_lines(tall_font, [60, 72, 84], ['- first;', '- second;', '- third.'])
    try:
        # PDF bounding boxes can be slightly shorter than the baseline advance.
        for line in lines:
            line.bbox.y0 = line.spans[0]['origin'][1]-10
            line.bbox.y1 = line.spans[0]['origin'][1]+1.7
        spacing = TextSpacing({s['font']:tall_font for l in lines for s in l.spans})
        spacing.flow(lines)
        assert all(spacing.multiple([line]) is not None for line in lines)
        # Isolated and generously separated rows still have no inferred rhythm.
        spacing.flow(lines[:2])
        assert spacing.multiple([lines[0]]) is None
    finally:
        pdf.close()
    with pdf_lines(tall_font, [60, 72, 84], ['- first;', '- second;', '- third.'])[0] as pdf:
        mapping = {s['font']:tall_font for l in lines_on(pdf[0]) for s in l.spans}
        doc, expected, _ = build_document(pdf, mapping)
    verify_document(doc, expected)
    paragraphs = [p for p in doc.paragraphs if p.text]
    assert len(paragraphs) == 3
    assert all(p.paragraph_format.space_before.pt == 0 for p in paragraphs)


def test_form_cells_grow_and_empty_caption_marks_have_caption_font(tall_font, tmp_path):
    texts = ['Name: __________ Date: _________', '(name)              (date)', 'ordinary text.']
    with pdf_lines(tall_font, [60,72,84], texts)[0] as pdf:
        mapping = {s['font']:tall_font for l in lines_on(pdf[0]) for s in l.spans}
        doc, expected, _ = build_document(pdf, mapping)
    verify_document(doc, expected)
    caption = doc.tables[1]
    for cell in caption.rows[0].cells:
        mark = cell.paragraphs[0]._p.find('./'+qn('w:pPr')+'/'+qn('w:rPr'))
        assert mark.find(qn('w:rFonts')).get(qn('w:ascii')) == tall_font.family
        assert mark.find(qn('w:sz')).get(qn('w:val')) == '20'
    field = doc.tables[0].cell(0,1).paragraphs[0]
    assert field.paragraph_format.line_spacing_rule == WD_LINE_SPACING.MULTIPLE
    field.runs[0].text = 'First\nSecond\nThird'
    doc.save(tmp_path/'edited.docx')
    saved = Document(tmp_path/'edited.docx')
    assert 'Third' in saved.tables[0].cell(0,1).text
    assert not list(saved.element.iter(qn('w:trHeight')))
    assert not list(saved.element.iter(qn('w:txbxContent')))
    for p in saved.paragraphs:
        if p.paragraph_format.line_spacing_rule == WD_LINE_SPACING.EXACTLY:
            assert not p.text.strip()  # fixed tiny spacing only separates tables
            assert p.paragraph_format.line_spacing.twips == 1


def test_paragraph_transition_uses_previously_emitted_leading(tall_font):
    pdf, lines = pdf_lines(tall_font, [60,72,84,97,110,123],
                           ['A'*54, 'a'*54, 'a'*53+'.', 'B'*54, 'b'*54, 'b'*53+'.'])
    try:
        # Distinct source blocks establish a paragraph boundary independently
        # of the inferred extra-gap detector.
        for line in lines[3:]:
            line.block = 99
        mapping = {s['font']:tall_font for l in lines for s in l.spans}
        doc = Document()
        Writer(doc, mapping, 540, 30, 144, None).flow(doc, lines, 540)
        paragraphs = [p for p in doc.paragraphs if p.text]
        assert len(paragraphs) == 2
        assert paragraphs[1].paragraph_format.space_before.pt == pytest.approx(1, abs=.05)
    finally:
        pdf.close()


def test_source_tracking_retains_pair_spacing_with_cumulative_rounding(tall_font):
    pdf, lines = pdf_lines(tall_font, [60], ['Abcd efgh'])
    try:
        span = lines[0].spans[0]
        # A 0.0375pt source pair adjustment cannot be represented independently
        # in Word's 0.05pt units. Preserve its cumulative width instead.
        for i, char in enumerate(span['chars']):
            char['origin'] = (30+i*9.9625, 60)
        values = source_tracking(span, tall_font)
        assert values is not None and values[-1] == 0
        assert abs(sum(values)/20 - (-.0375*(len(values)-1))) <= .025
        assert source_tracking(span, replace(tall_font, postscript='Different', family='Other', full_name='Other', aliases=())) is None
        span['chars'][2]['origin'] = (49, 55)
        assert source_tracking(span, tall_font) is None  # raised/ambiguous source
    finally:
        pdf.close()


def test_soft_break_option_keeps_normal_paragraphs_and_font_sizes(tall_font, tmp_path):
    with pdf_lines(tall_font, [60,72,84], ['A sentence continues', 'on a second line with a hyphen-', 'ated ending.'])[0] as pdf:
        mapping = {s['font']:tall_font for l in lines_on(pdf[0]) for s in l.spans}
        natural, expected, _ = build_document(pdf, mapping)
        doc, preserved, _ = build_document(pdf, mapping, keep_line_breaks=True)
    verify_document(doc, preserved)
    assert expected == preserved
    paras = [p for p in doc.paragraphs if p.text]
    assert len(paras) == len([p for p in natural.paragraphs if p.text]) == 1
    assert paras[0].text == 'A sentence continues\non a second line with a hyphen-\nated ending.'
    assert len(list(doc.element.iter(qn('w:br')))) == 2
    assert not list(natural.element.iter(qn('w:br')))
    assert all(r.font.size.pt == 10 for p in paras for r in p.runs)
    assert not list(doc.element.iter(qn('w:w')))  # no glyph scaling
    assert not list(doc.element.iter(qn('w:txbxContent')))
    assert not list(doc.element.iter(qn('w:framePr')))
    assert not list(doc.element.iter(qn('w:trHeight')))
    for run in paras[0].runs:
        pr = run._r.find(qn('w:rPr'))
        if pr.find(qn('w:spacing')) is not None:
            assert pr.find(qn('w:kern')) is None
    # A normal edit remains a paragraph and survives save/reopen.
    paras[0].add_run(' Added ordinary text.').font.size = Pt(16)
    target = tmp_path/'edited-lines.docx'
    doc.save(target)
    assert Document(target).paragraphs[0].text.endswith('Added ordinary text.')


def test_mixed_size_minimum_uses_descent_and_does_not_double_count_gap(tmp_path):
    face = make_font(tmp_path/'bounded.ttf')
    pdf, lines = pdf_lines(face, [60,79.9,108.02,127.92], sizes=[14,16,14,16])
    try:
        for index, line in enumerate(lines):
            line.block = index//2
        mapping = {s['font']:face for l in lines for s in l.spans}
        spacing = TextSpacing(mapping)
        minimum = spacing.minimum(lines[:2])
        assert minimum[0] == pytest.approx(20.3, abs=.05)
        doc = Document()
        Writer(doc, mapping, 540, 30, 144, None, True).flow(doc, lines, 540)
        paragraphs = [p for p in doc.paragraphs if p.text]
        assert len(paragraphs) == 4  # labels and larger values are separate ordinary paragraphs
        assert all(p.paragraph_format.line_spacing_rule == WD_LINE_SPACING.AT_LEAST for p in paragraphs)
        assert paragraphs[2].paragraph_format.space_before.pt == pytest.approx(10.92, abs=.05)
        assert {r.font.size.pt for p in paragraphs for r in p.runs} == {14,16}
        assert not list(doc.element.iter(qn('w:trHeight')))
        natural = Writer(Document(), mapping, 540, 30, 144, None)
        assert natural.minimum_spacing(lines[:2]) is None
        assert natural.minimum_spacing([lines[0]]) is not None
        # Irregular rhythms and a larger final paragraph mark keep the fallback.
        assert spacing.minimum(lines) is None
        assert spacing.minimum(list(reversed(lines[:2]))) is None
        lines[0].spans[0]['origin'] = (30,58)
        lines[0].spans.append(dict(lines[0].spans[0],origin=(40,60)))
        assert spacing.minimum(lines[:2]) is None
    finally:
        pdf.close()


def test_dense_measured_leading_with_tall_metrics_keeps_type_size(tall_font):
    with pdf_lines(tall_font, [60,70.2,80.4])[0] as pdf:
        lines = lines_on(pdf[0])
        mapping = {s['font']:tall_font for l in lines for s in l.spans}
        doc, expected, _ = build_document(pdf, mapping, keep_line_breaks=True)
    verify_document(doc, expected)
    para = next(p for p in doc.paragraphs if p.text)
    assert para.paragraph_format.line_spacing_rule == WD_LINE_SPACING.MULTIPLE
    assert 10.2 <= para.paragraph_format.line_spacing*13.2 < 10.26
    assert all(r.font.size.pt == 10 for r in para.runs)
    # The multiple scales with an ordinary larger-font edit; it is not a fixed
    # line height that could clip the replacement text.
    para.runs[0].font.size = Pt(20)
    assert para.paragraph_format.line_spacing*26.4 >= 20.4
    pdf, lines = pdf_lines(tall_font, [60,69,78])
    try:
        assert TextSpacing(mapping).multiple(lines) is None  # sub-em source remains uncertain
    finally:
        pdf.close()


def test_minimum_requires_consistent_descent_and_metric_clearance(tmp_path):
    path = tmp_path/'bounded-edge.ttf'
    face = make_font(path)
    pdf, lines = pdf_lines(face,[60,76],sizes=[16,16])
    try:
        mapping = {s['font']:face for l in lines for s in l.spans}
        assert TextSpacing(mapping).minimum(lines)[0] == 16
        lines[1].spans[0]['origin'] = (30,75.9)
        assert TextSpacing(mapping).minimum(lines) is None
        lines[1].spans[0]['origin'] = (30,80)
        with TTFont(path) as font:
            font['OS/2'].usWinDescent = 350
            font.save(path)
        assert TextSpacing(mapping).minimum(lines) is None
    finally:
        pdf.close()


def test_retained_lines_preserve_large_verified_gap_only(tmp_path):
    face = make_font(tmp_path/'gap.ttf')
    pdf, lines = pdf_lines(face,[60,140])
    try:
        mapping = {s['font']:face for l in lines for s in l.spans}
        doc = Document()
        writer = Writer(doc,mapping,540,30,144,None,True)
        writer.flow(doc,lines,540)
        assert doc.paragraphs[1].paragraph_format.space_before.pt == 68
        raw = writer.text(doc,[lines[0]],before=68)
        assert raw.paragraph_format.space_before.pt == 18
    finally:
        pdf.close()
