from pathlib import Path
import json
import string
import time

import pytest

from pagethaw import gui, i18n
from pagethaw.engine import PDFInfo
from pagethaw.fonts import FontFace


def test_translation_placeholders_match():
    fields = lambda text: {field for _, field, _, _ in string.Formatter().parse(text) if field}
    for source, target in i18n.RU.items():
        assert fields(source) == fields(target), source


def test_known_diagnostics_translate_without_changing_filenames():
    message = 'Page 2: no selectable text; scanned pages need OCR first.'
    assert i18n.translate('ru', message) == 'Страница 2: нет выделяемого текста; скан сначала нужно распознать (OCR).'
    progress = '1/2: Test_{name}.pdf — converted; visual review required'
    assert i18n.translate('ru', progress) == '1/2: Test_{name}.pdf — готово; нужна проверка страниц'
    assert i18n.translate('en', progress) == progress
    # Unknown library messages retain diagnostic codes and exact paths.
    unknown = 'OS error 42: C:/Docs/{form}.pdf'
    assert i18n.translate('ru', unknown) == unknown


def test_comparison_failure_translates_nested_reason():
    message = 'Comparison stopped: Page count changed: 2 → 3 See comparison-report.json.'
    assert i18n.translate('ru', message) == 'Сравнение остановлено: Изменилось число страниц: 2 → 3 См. comparison-report.json.'


def test_language_persistence_and_invalid_settings(tmp_path, monkeypatch):
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path))
    monkeypatch.setattr(i18n.locale, 'getlocale', lambda: ('en_US', 'UTF-8'))
    assert i18n.load_language() == 'en'
    assert i18n.save_language('ru')
    assert i18n.load_language() == 'ru'
    i18n.preference_path().write_text('broken JSON', encoding='utf-8')
    assert i18n.load_language() == 'en'
    i18n.preference_path().write_text('[]', encoding='utf-8')
    assert i18n.load_language() == 'en'
    monkeypatch.setattr(i18n.locale, 'getlocale', lambda: ('ru_RU', 'UTF-8'))
    assert i18n.load_language() == 'ru'
    with pytest.raises(ValueError):
        i18n.save_language('xx')


def test_unwritable_preference_is_nonfatal(tmp_path, monkeypatch):
    blocked = tmp_path/'not-a-directory'
    blocked.write_text('keep')
    monkeypatch.setattr(i18n, 'preference_path', lambda: blocked/'settings.json')
    assert not i18n.save_language('ru')
    assert blocked.read_text() == 'keep'


@pytest.fixture(scope='module')
def app(tmp_path_factory):
    # One Tcl interpreter per process, just as the desktop application uses.
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv('LOCALAPPDATA', str(tmp_path_factory.mktemp('gui-settings')))
        patch.setattr(gui, 'load_language', lambda: 'en')
        instance = gui.App()
        instance.withdraw()
        yield instance
        instance.close()


def test_switch_retains_files_fonts_options_results_and_selection(app, tmp_path):
    source = tmp_path/'Synthetic.pdf'
    face = FontFace('unused.ttf', 'Example', 'Example Bold', 'Example-Bold', True, False, True)
    app.paths = [source]
    app.infos = [PDFInfo(source, pages=2, fonts={'Example-Bold': 'Test'})]
    app.font_chars = {'Example-Bold': 'Test'}
    app.mapping = {'Example-Bold': face}
    app.faces = [face]
    app.output.set(str(tmp_path/'result'))
    app.rules.set(True)
    app.dpi.set('192')
    records = [{'status': 'converted; visual review required', 'content_check': 'passed'}]
    app.converted(records)
    app.refresh_fonts()
    app.file_tree.selection_set('0')
    app.font_tree.selection_set('Example-Bold')
    app.language_button.invoke()
    app.update_idletasks()
    assert app.language.get() == 'ru'
    assert app.title() == 'PageThaw — PDF в Word'
    assert app.language_button.cget('text') == 'English'
    assert app.file_tree.set('0', 'status') == 'готово; нужна проверка страниц'
    assert app.font_tree.set('Example-Bold', 'target') == 'Example Bold [Полужирный]'
    assert app.status.get().startswith('Готово: 1; ошибок: 0; отменено: 0.')
    assert app.mapping['Example-Bold'] is face
    assert app.paths == [source]
    assert app.file_tree.selection() == ('0',)
    assert app.font_tree.selection() == ('Example-Bold',)
    assert app.output.get() == str(tmp_path/'result')
    assert app.rules.get() and app.dpi.get() == '192'
    assert json.loads(i18n.preference_path().read_text())['language'] == 'ru'
    app.language_button.invoke()
    assert app.language.get() == 'en'
    assert app.file_tree.set('0', 'status') == records[0]['status']
    assert app.status.get().startswith('1 converted; 0 failed; 0 cancelled.')


def test_switch_is_disabled_during_job_and_returns_after_completion(app):
    app.switch_language()
    result = 'No successfully converted documents are available for comparison.'
    app.run_job(lambda: result, app.set_status, 'Converting locally…')
    assert 'disabled' in app.language_button.state()
    app.switch_language()
    assert app.language.get() == 'ru'
    deadline = time.monotonic()+5
    while app.busy and time.monotonic() < deadline:
        app.update()
        time.sleep(.01)
    assert not app.busy
    assert 'disabled' not in app.language_button.state()
    assert app.status.get() == 'Нет успешно сконвертированных документов для сравнения.'


def test_language_switch_does_not_restore_stale_fonts_after_file_change(app, tmp_path, monkeypatch):
    app.font_chars = {'PreviousFont': 'Test'}
    monkeypatch.setattr(gui.filedialog, 'askopenfilenames', lambda **kwargs: (str(tmp_path/'another.pdf'),))
    app.add_files()
    app.switch_language()
    assert app.infos == []
    assert app.mapping == {}
    assert app.font_chars == {}
    assert app.font_tree.get_children() == ()
