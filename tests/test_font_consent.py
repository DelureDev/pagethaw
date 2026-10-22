"""Exercise the actual GUI decision handlers without installing fonts or opening dialogs."""
from pathlib import Path
from types import SimpleNamespace
import os

import pytest

from pagethaw import gui
from pagethaw.fonts import read_font


@pytest.fixture
def face():
    path = Path(os.environ.get('WINDIR', 'C:/Windows'))/'Fonts'/'arial.ttf'
    if not path.exists():
        pytest.skip('Windows Arial required')
    return read_font(path, installed=True)


def test_convert_waits_for_missing_font_choice(monkeypatch):
    warnings = []
    app = SimpleNamespace(infos=[object()], font_chars={'MissingFont': 'Test'}, mapping={})
    monkeypatch.setattr(gui.messagebox, 'showwarning', lambda *args: warnings.append(args))
    gui.App.convert(app)
    assert len(warnings) == 1
    assert 'MissingFont' in warnings[0][1]


@pytest.mark.parametrize('approve', [False, True])
def test_substitute_requires_positive_consent(monkeypatch, face, approve):
    calls = []
    app = SimpleNamespace(font_chars={'MissingFont': 'Test'}, mapping={},
                          refresh_fonts=lambda: calls.append('refresh'))
    dialog = SimpleNamespace(app=app, source='MissingFont', visible=[face],
                             list=SimpleNamespace(curselection=lambda: (0,)),
                             destroy=lambda: calls.append('close'))
    monkeypatch.setattr(gui.messagebox, 'askyesno', lambda *args, **kwargs: approve)
    gui.FontDialog.accept(dialog)
    assert ('MissingFont' in app.mapping) == approve
    assert calls == (['refresh', 'close'] if approve else [])


def test_declining_font_install_does_not_install(monkeypatch, face):
    app = SimpleNamespace(font_chars={'MissingFont': 'Test'}, faces=[])
    dialog = SimpleNamespace(app=app, source='MissingFont')
    monkeypatch.setattr(gui.filedialog, 'askopenfilename', lambda **kwargs: face.path)
    monkeypatch.setattr(gui.messagebox, 'askyesno', lambda *args, **kwargs: False)
    def forbidden(*args):
        pytest.fail('Font installation ran without consent')
    monkeypatch.setattr(gui, 'install_for_current_user', forbidden)
    gui.FontDialog.add(dialog)
    assert not app.faces
