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
