import json
import threading
from pathlib import Path
from pagethaw.engine import PDFInfo, digest
from pagethaw import word_review
import pymupdf


def prepare(tmp_path):
    infos, records = [], []
    for n in range(2):
        path = tmp_path/f'sample-{n}.pdf'
        with pymupdf.open() as pdf:
            page = pdf.new_page()
            page.insert_text((30, 50), 'Synthetic review fixture')
            pdf.save(path)
        docx = path.with_suffix('.docx')
        docx.write_bytes(b'synthetic stand-in; exporter mocked')
        infos.append(PDFInfo(path))
        records.append({'input': path.name, 'content_check': 'passed',
                        'input_sha256': digest(path), 'sha256': digest(docx)})
    (tmp_path/'pagethaw-report.json').write_text(json.dumps({'files': records}), encoding='utf-8')
    return infos


def test_cancel_before_any_comparison(tmp_path):
    infos = prepare(tmp_path)
    cancel = threading.Event()
    cancel.set()
    message = word_review.review_batch(infos, tmp_path, cancel=cancel)
    assert 'cancelled: 0 of 2' in message
    records = json.loads((tmp_path/'comparison-report.json').read_text())
    assert [r['status'] for r in records] == ['cancelled', 'cancelled']


def test_cancel_between_comparisons(tmp_path, monkeypatch):
    infos = prepare(tmp_path)
    cancel = threading.Event()
    def fake_export(docx, output):
        Path(output).mkdir(parents=True)
        cancel.set()
        return docx.with_suffix('.pdf')
    monkeypatch.setattr(word_review, 'export_word', fake_export)
    message = word_review.review_batch(infos, tmp_path, cancel=cancel)
    assert 'cancelled: 1 of 2' in message
    records = json.loads((tmp_path/'comparison-report.json').read_text())
    assert records[0]['page_count_check'] == 'passed'
    assert records[1]['status'] == 'cancelled'


def test_in_memory_review_uses_numbered_output_and_separate_folder(tmp_path, monkeypatch):
    infos = prepare(tmp_path)
    records = json.loads((tmp_path/'pagethaw-report.json').read_text())['files']
    for info, record in zip(infos, records):
        numbered = tmp_path/(info.path.stem+' (2).docx')
        info.path.with_suffix('.docx').rename(numbered)
        record.update(source=str(info.path), output=numbered.name)
    (tmp_path/'pagethaw-report.json').unlink()
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir() if p.is_file()}
    seen = []
    def fake_export(docx, output):
        seen.append(docx.name)
        Path(output).mkdir(parents=True)
        return next(info.path for info in infos if docx.stem == info.path.stem+' (2)')
    monkeypatch.setattr(word_review, 'export_word', fake_export)
    review = tmp_path/'separate-review'
    word_review.review_batch(infos, tmp_path, records=records, review_output=review)
    assert seen == [r['output'] for r in records]
    assert all(r['page_count_check'] == 'passed' for r in json.loads((review/'comparison-report.json').read_text()))
    assert all((tmp_path/name).read_bytes() == value for name, value in before.items())
    assert not (tmp_path/'pagethaw-report.json').exists()
    assert not (tmp_path/'comparison-report.json').exists()


def test_comparison_retains_each_duplicate_source_occurrence(tmp_path, monkeypatch):
    info = prepare(tmp_path)[0]
    original = info.path.with_suffix('.docx')
    second = tmp_path/(info.path.stem+' (2).docx')
    second.write_bytes(b'second converted output')
    records = [{'input': info.path.name, 'source': str(info.path), 'output': path.name,
                'content_check': 'passed', 'input_sha256': digest(info.path), 'sha256': digest(path)}
               for path in (original, second)]
    seen = []
    def fake_export(docx, output):
        seen.append(docx.name)
        Path(output).mkdir(parents=True)
        return info.path
    monkeypatch.setattr(word_review, 'export_word', fake_export)
    word_review.review_batch([info, info], tmp_path, records=records, review_output=tmp_path/'review')
    assert seen == [original.name, second.name]


def test_editable_comparison_keeps_extra_reflowed_pages(tmp_path, monkeypatch):
    info = prepare(tmp_path)[0]
    record = json.loads((tmp_path/'pagethaw-report.json').read_text())['files'][0]
    record['mode'] = 'editable'
    exported = tmp_path/'reflowed.pdf'
    with pymupdf.open() as pdf:
        for label in ('First page', 'Reflowed second page'):
            pdf.new_page().insert_text((30, 50), label)
        pdf.save(exported)
    def fake_export(docx, output):
        Path(output).mkdir(parents=True)
        return exported
    monkeypatch.setattr(word_review, 'export_word', fake_export)
    review = tmp_path/'review'
    word_review.review_batch([info], tmp_path, records=[record], review_output=review)
    result = json.loads((review/'comparison-report.json').read_text())[0]
    assert result['source_pages'] == 1 and result['pages'] == 2
    assert result['page_count_check'] == 'not required for editable mode'
    assert (review/'comparisons/1/page-2.png').exists()
    # The same page-count drift remains a failure in Preserve layout.
    record['mode'] = 'layout'
    layout = tmp_path/'layout-review'
    word_review.review_batch([info], tmp_path, records=[record], review_output=layout)
    failed = json.loads((layout/'comparison-report.json').read_text())[0]
    assert failed['status'] == 'failed'
    assert 'Page count changed' in failed['error']
