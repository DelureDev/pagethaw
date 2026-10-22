from dataclasses import replace
from pathlib import Path
import json

import pytest

from pagethaw import __main__, engine, fonts, font_match


@pytest.mark.parametrize('conflict', [False, True])
def test_explicit_cli_mapping_cannot_override_windows_family_conflict(tmp_path, monkeypatch, conflict):
    path = tmp_path/'chosen.ttf'
    path.write_bytes(b'font1')
    face = fonts.FontFace(str(path), 'Example', 'Example', 'Example', False, False, True)
    faces = [face]
    if conflict:
        duplicate = tmp_path/'duplicate.ttf'
        duplicate.write_bytes(b'font2')
        faces.append(replace(face, path=str(duplicate)))
    mapping = tmp_path/'mapping.json'
    mapping.write_text(json.dumps({'MissingFont': str(path)}))
    source = tmp_path/'form.pdf'
    info = engine.PDFInfo(source, 1, {'MissingFont': 'Test'})
    monkeypatch.setattr(engine, 'inspect_pdf', lambda _: info)
    monkeypatch.setattr(fonts, 'installed_fonts', lambda: faces)
    monkeypatch.setattr(fonts, 'read_font', lambda _: face)
    monkeypatch.setattr(font_match, 'automatic_mapping', lambda *_: {})
    calls = []
    def convert(*args, **kwargs):
        calls.append(args[2])
        return [{'content_check': 'passed'}]
    monkeypatch.setattr(engine, 'convert_batch', convert)
    monkeypatch.setattr('sys.argv', ['pagethaw', '--convert', str(source), '--output', str(tmp_path/'out'), '--font-map', str(mapping)])
    if conflict:
        with pytest.raises(ValueError, match='Conflicting installed font versions'):
            __main__.main()
        assert not calls
    else:
        assert __main__.main() == 0
        assert calls == [{'MissingFont': face}]
