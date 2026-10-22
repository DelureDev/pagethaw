"""Optional desktop Word export, isolated by process identity and a deadline."""
from pathlib import Path
import json
import os
import subprocess
import sys

import pymupdf
from PIL import Image, ImageDraw
from .engine import digest


def read_state(path):
    try:
        value = json.loads(path.read_text(encoding='utf-8-sig'))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def export_word(docx, output, timeout=60):
    if sys.platform != 'win32':
        raise ValueError('Word comparison requires Windows and desktop Microsoft Word.')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    state = output/'worker.json'
    pdf = output/'word.pdf'
    if state.exists() or pdf.exists():
        raise FileExistsError('Comparison already exists. Choose a new output batch.')
    scripts = Path(__file__).parent
    powershell = Path(os.environ.get('SystemRoot', 'C:/Windows'))/'System32/WindowsPowerShell/v1.0/powershell.exe'
    if not powershell.is_file():
        raise RuntimeError('Windows PowerShell is unavailable. Conversion works without Word comparison.')
    with (output/'worker.log').open('wb') as log:
        worker = subprocess.Popen([str(powershell), '-NoProfile', '-File', str(scripts/'word_worker.ps1'),
            '-Docx', str(Path(docx).resolve()), '-Pdf', str(pdf.resolve()), '-State', str(state.resolve()), '-Method', 'saveas'],
            stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            worker.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            worker.kill()
            worker.wait(timeout=10)
            detail = read_state(state)
            error = f'Word export timed out after {timeout} seconds.'
            (output/'failure.txt').write_text(error, encoding='utf-8')
            if detail.get('word_pid') and detail.get('word_started'):
                try:
                    cleanup = subprocess.run([str(powershell), '-NoProfile', '-File', str(scripts/'stop_owned_word.ps1'),
                        '-State', str(state.resolve())], capture_output=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
                    if cleanup.returncode:
                        error += ' Owned-process cleanup failed; inspect worker.json.'
                except subprocess.TimeoutExpired:
                    error += ' Owned-process cleanup timed out; inspect worker.json.'
            else:
                error += ' No confirmed process identity; no Word process was terminated.'
            if pdf.exists():
                pdf.rename(output/'partial.pdf')
            (output/'failure.txt').write_text(error, encoding='utf-8')
            raise RuntimeError(error)
    detail = read_state(state)
    if worker.returncode or detail.get('status') != 'passed' or not pdf.exists():
        raise RuntimeError(detail.get('error', 'Word export failed. See worker.log.'))
    return pdf


def review_batch(infos, output, cancel=None, progress=None, *, records=None, review_output=None):
    review_output = Path(review_output) if review_output is not None else Path(output)
    review_output.mkdir(parents=True, exist_ok=True)
    report_path = review_output/'comparison-report.json'
    if report_path.exists():
        raise FileExistsError('This batch already has a comparison report. Preserve it and choose a new batch.')
    results = []
    if records is None:
        records = json.loads((Path(output)/'pagethaw-report.json').read_text(encoding='utf-8'))['files']
    accepted = {}
    for record in records:
        if record.get('content_check') == 'passed':
            accepted.setdefault(record.get('source', record['input']), []).append(record)
    eligible = []
    for info in infos:
        matches = accepted.get(str(info.path)) or accepted.get(info.path.name)
        if matches:
            eligible.append((info, matches.pop(0)))
    if not eligible:
        report_path.write_text('[]', encoding='utf-8')
        return 'No successfully converted documents are available for comparison.'
    for index, (info, record) in enumerate(eligible, 1):
        if cancel and cancel.is_set():
            completed = len(results)
            results.extend({'input': item.path.name, 'status': 'cancelled', 'visual_review': 'not run'}
                           for item, _ in eligible[index-1:])
            report_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
            return f'Comparison cancelled: {completed} of {len(eligible)} documents exported. Remaining comparisons were not run.'
        result = {'input': info.path.name, 'status': 'failed', 'visual_review': 'not run'}
        results.append(result)
        try:
            docx = Path(output)/record.get('output', info.path.stem+'.docx')
            if digest(info.path) != record.get('input_sha256') or digest(docx) != record.get('sha256'):
                raise ValueError('Source or DOCX changed since conversion. Convert a fresh batch before comparing.')
            if progress:
                progress(f'Word comparison: {info.path.name}')
            directory = review_output/'comparisons'/str(index)
            rendered = export_word(docx, directory)
            with pymupdf.open(info.path) as source, pymupdf.open(rendered) as doc:
                pages = len(source)
                if len(source) != len(doc):
                    raise ValueError(f'Page count changed: {len(source)} → {len(doc)}')
                for number, (a, b) in enumerate(zip(source, doc), 1):
                    panels = []
                    for page, label in ((a, 'Original PDF'), (b, 'Word export')):
                        pixmap = page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False)
                        panel = Image.new('RGB', (pixmap.width, pixmap.height+30), '#eef2f6')
                        panel.paste(Image.frombytes('RGB', (pixmap.width, pixmap.height), pixmap.samples), (0, 30))
                        ImageDraw.Draw(panel).text((10, 8), f'{label} | Page {number}', fill='black')
                        panels.append(panel)
                    pair = Image.new('RGB', (sum(p.width for p in panels)+12, max(p.height for p in panels)), '#cbd5e1')
                    pair.paste(panels[0], (0, 0))
                    pair.paste(panels[1], (panels[0].width+12, 0))
                    pair.save(directory/f'page-{number}.png')
            result.update(status='exported; inspect comparison images', page_count_check='passed', pages=pages)
        except Exception as exc:
            result['error'] = str(exc)
        report_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
        if result['status'] == 'failed':
            return 'Comparison stopped: '+result['error']+' See comparison-report.json.'
    return 'Comparison images are ready in the comparisons folder. Inspect every page; visual review is not automatic.'
