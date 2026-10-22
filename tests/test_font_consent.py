"""Exercise the actual GUI decision handlers without installing fonts or opening dialogs."""
from pathlib import Path
from types import SimpleNamespace
import os

import pytest

from pagethaw import gui
from pagethaw.fonts import read_font
from pagethaw.i18n import translate


@pytest.fixture(params=['en', 'ru'])
def language(request):
    return request.param


def localize(app, language):
    app.language = SimpleNamespace(get=lambda: language)
    app.t = lambda text, **values: translate(language, text, **values)
    return app


@pytest.fixture
def face():
    path = Path(os.environ.get('WINDIR', 'C:/Windows'))/'Fonts'/'arial.ttf'
    if not path.exists():
        pytest.skip('Windows Arial required')
    return read_font(path, installed=True)


def test_convert_waits_for_missing_font_choice(monkeypatch, language):
    warnings = []
    app = localize(SimpleNamespace(infos=[object()], font_chars={'MissingFont': 'Test'}, mapping={}), language)
    monkeypatch.setattr(gui.messagebox, 'showwarning', lambda *args: warnings.append(args))
    gui.App.convert(app)
    assert len(warnings) == 1
    assert 'MissingFont' in warnings[0][1]
    assert warnings[0][0] == translate(language, 'Fonts need your choice')


@pytest.mark.parametrize('approve', [False, True])
@pytest.mark.parametrize('same_name', [False, True])
def test_substitute_requires_positive_consent(monkeypatch, face, approve, language, same_name):
    calls = []
    source = face.postscript if same_name else 'MissingFont'
    app = localize(SimpleNamespace(font_chars={source: 'Test'}, mapping={}, infos=[], faces=[face],
                          refresh_fonts=lambda: calls.append('refresh'), refresh_files=lambda: None), language)
    dialog = SimpleNamespace(app=app, t=app.t, source=source, visible=[face],
                             list=SimpleNamespace(curselection=lambda: (0,)),
                             destroy=lambda: calls.append('close'))
    monkeypatch.setattr(gui.messagebox, 'askyesno', lambda *args, **kwargs: approve)
    gui.FontDialog.accept(dialog)
    assert (source in app.mapping) == approve
    assert calls == (['refresh', 'close'] if approve else [])


def test_declining_font_install_does_not_install(monkeypatch, face, language):
    app = localize(SimpleNamespace(font_chars={'MissingFont': 'Test'}, faces=[]), language)
    dialog = SimpleNamespace(app=app, t=app.t, source='MissingFont')
    monkeypatch.setattr(gui.filedialog, 'askopenfilename', lambda **kwargs: face.path)
    monkeypatch.setattr(gui.messagebox, 'askyesno', lambda *args, **kwargs: False)
    def forbidden(*args):
        pytest.fail('Font installation ran without consent')
    monkeypatch.setattr(gui, 'install_for_current_user', forbidden)
    gui.FontDialog.add(dialog)
    assert not app.faces
