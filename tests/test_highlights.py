from pathlib import Path
import hashlib
import pymupdf
import pytest
from docx import Document
from docx.oxml.ns import qn
from pagethaw.editable import build_document, UnsupportedLayout
from pagethaw.engine import inspect_pdf, convert_pdf
from pagethaw.fonts import read_font


def fixture(path, custom=False, overlay=False, cut=False, blend='Multiply'):
    font = Path('C:/Windows/Fonts/arial.ttf')
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_font(fontname='fixture',fontfile=font)
        page.insert_text((30,60), 'Before highlighted after', fontname='fixture',fontsize=10)
        page.insert_text((30,72), 'Second highlighted row', fontname='fixture',fontsize=10)
        lines = [l for b in page.get_text('rawdict')['blocks'] for l in b.get('lines',[])]
        cs = lines[0]['spans'][0]['chars']
        r1 = pymupdf.Rect(cs[7]['bbox']) | pymupdf.Rect(cs[17]['bbox'])
        cs = lines[1]['spans'][0]['chars']
        r2 = pymupdf.Rect(cs[0]['bbox']) | pymupdf.Rect(cs[5]['bbox'])
        if cut:r1.x0 += 1
        annot = page.add_highlight_annot([r1,r2])
        annot.set_colors(stroke=(1,.5,0));annot.set_opacity(.4);annot.set_blendmode('Multiply');annot.update()
        xref = int(pdf.xref_get_key(annot.xref,'AP/N')[1].split()[0])
        pdf.xref_set_key(xref,'Resources',f'<< /ExtGState << /H << /Type /ExtGState /ca .4 /BM /{blend} >> >> >>')
        content = 'q /H gs 1 .5 0 rg\n'+''.join(f'{r.x0} {page.rect.height-r.y1} {r.width} {r.height} re f\n' for r in [r1,r2])+'Q'
        if custom:content += f'\nq 0 0 0 rg {r1.x0} {page.rect.height-r1.y1} 2 2 re f Q'
        pdf.update_stream(xref,content.encode())
        if overlay:page.draw_rect(r1,color=None,fill=(1,0,0),fill_opacity=.2)
        pdf.save(path)
    return read_font(font,installed=True)


@pytest.mark.parametrize('keep',[False,True])
def test_partial_run_and_multiline_highlights_stay_editable(tmp_path,keep):
    path=tmp_path/'source.pdf';face=fixture(path)
    before=hashlib.sha256(path.read_bytes()).hexdigest()
    info=inspect_pdf(path);out=tmp_path/'out.docx'
    result=convert_pdf(info,out,{name:face for name in info.fonts},mode='editable',keep_line_breaks=keep)
    assert result['content_check']=='passed'
    doc=Document(out)
    shaded=[];plain=[]
    for run in doc.element.iter(qn('w:r')):
        text=''.join(t.text or '' for t in run.iter(qn('w:t')))
        shd=list(run.iter(qn('w:shd')))
        (shaded if shd else plain).append(text)
        if shd:assert shd[0].get(qn('w:fill'))=='FFCC99'
    assert ''.join(shaded)=='highlightedSecond'
    assert 'Before' in ''.join(plain) and 'highlighted row' in ''.join(plain)
    assert not doc.element.xpath('.//wp:anchor')
    assert not list(doc.element.iter(qn('w:txbxContent')))
    assert hashlib.sha256(path.read_bytes()).hexdigest()==before
    with pymupdf.open(path) as pdf:
        trailer = pdf.pdf_trailer()
        build_document(pdf,{name:face for name in info.fonts})
        assert pdf.pdf_trailer() == trailer
        page=pdf[0]
        assert len(list(page.annots()))==1  # Even the caller's in-memory PDF is untouched.


@pytest.mark.parametrize('case',['custom','overlay','cut'])
def test_unproven_highlights_and_unrelated_overlays_remain_blocked(tmp_path,case):
    path=tmp_path/'bad.pdf';face=fixture(path,**{case:True})
    info=inspect_pdf(path);out=tmp_path/'out.docx'
    with pytest.raises(UnsupportedLayout):
        convert_pdf(info,out,{name:face for name in info.fonts},mode='editable')
    assert not out.exists()


@pytest.mark.parametrize('blend',['Normal','Screen','Difference'])
def test_custom_appearance_blend_cannot_hide_behind_annotation_metadata(tmp_path,blend):
    path=tmp_path/'blend.pdf';face=fixture(path,blend=blend)
    info=inspect_pdf(path);out=tmp_path/'out.docx'
    with pytest.raises(UnsupportedLayout, match='blend'):
        convert_pdf(info,out,{name:face for name in info.fonts},mode='editable')
    assert not out.exists()
