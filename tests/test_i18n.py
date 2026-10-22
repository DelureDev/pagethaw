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
    monkeypatch.setattr(app, 'scan', lambda: None)
    monkeypatch.setattr(gui.filedialog, 'askopenfilenames', lambda **kwargs: (str(tmp_path/'another.pdf'),))
    app.add_files()
    app.switch_language()
    assert app.infos == []
    assert app.mapping == {}
    assert app.font_chars == {}
    assert app.font_tree.get_children() == ()


def test_compact_panels_and_last_conversion_survive_language_switch(app):
    app.options_expanded = False
    last = (Path('output'), [], [])
    app.last_conversion = last
    app.switch_language()
    assert app.font_frame.winfo_manager() == 'grid'
    assert not app.options_frame.winfo_manager()
    app.toggle_options()
    app.switch_language()
    assert app.font_frame.winfo_manager() == 'grid'
    assert app.options_frame.winfo_manager() == 'grid'
    assert app.last_conversion is last


def test_adding_files_starts_scan(app, tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(app, 'scan', lambda: calls.append('scan'))
    monkeypatch.setattr(gui.filedialog, 'askopenfilenames', lambda **kwargs: (str(tmp_path/'new.pdf'),))
    app.add_files()
    assert calls == ['scan']


def test_unverified_font_is_visible_warns_and_blocks_conversion(app, tmp_path, monkeypatch):
    source = tmp_path/'missing.pdf'
    face = FontFace('unused.ttf', 'Example', 'Example', 'Example', False, False, True)
    app.paths = [source]
    app.language.set('en')
    # No embedded proof: a matching name must never silently approve this face.
    monkeypatch.setattr(gui, 'missing_glyphs', lambda *_: [])
    monkeypatch.setattr('pagethaw.font_match.missing_glyphs', lambda *_: [])
    app.scanned(([PDFInfo(source, 1, {'Example': 'Test'})], [face]))
    assert app.font_frame.winfo_manager() == 'grid'
    assert not app.mapping
    assert app.font_tree.selection() == ('Example',)
    assert app.file_tree.set('0', 'status') == 'Choose fonts below'
    assert '1 font(s) need your choice' in app.font_status.get()
    warnings = []
    monkeypatch.setattr(gui.messagebox, 'showwarning', lambda *args: warnings.append(args))
    app.convert()
    assert len(warnings) == 1 and 'Example' in warnings[0][1]
    app.switch_language()
    assert 'Требуют выбора: 1' in app.font_status.get()
    assert app.font_frame.winfo_manager() == 'grid'


def test_gui_auto_scan_and_repeat_conversion_only_write_docx(app, tmp_path, monkeypatch):
    import os
    import pymupdf
    source = tmp_path/'form.pdf'
    font = Path(os.environ.get('WINDIR', 'C:/Windows'))/'Fonts/arial.ttf'
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_font(fontname='fixture', fontfile=str(font))
        page.insert_text((35, 60), 'Name: ______ / Пример', fontname='fixture', fontsize=12)
        pdf.save(source)
    app.paths = []
    app.output.set(str(tmp_path/'chosen-folder'))
    monkeypatch.setattr(gui.filedialog, 'askopenfilenames', lambda **kwargs: (str(source),))
    def unexpected_dialog(*args, **kwargs):
        pytest.fail(f'Unexpected blocking dialog: {args}')
    monkeypatch.setattr(gui.messagebox, 'showerror', unexpected_dialog)
    monkeypatch.setattr(gui.messagebox, 'showwarning', unexpected_dialog)
    def wait_for_job():
        deadline = time.monotonic()+20
        while app.busy and time.monotonic() < deadline:
            app.update()
            time.sleep(.01)
        assert not app.busy
    app.add_files()
    wait_for_job()
    assert app.infos[0].error == ''
    assert set(app.font_chars) <= app.mapping.keys()
    app.convert()
    wait_for_job()
    first = (tmp_path/'chosen-folder/form.docx').read_bytes()
    app.convert()
    wait_for_job()
    output = tmp_path/'chosen-folder'
    assert {p.name for p in output.iterdir()} == {'form.docx', 'form (2).docx'}
    assert (output/'form.docx').read_bytes() == first
    assert app.last_conversion[0] == output
    assert app.last_conversion[2][0]['output'] == 'form (2).docx'


def test_retry_only_failed_files_and_details(app, tmp_path, monkeypatch):
    import shutil
    import pymupdf
    from pagethaw import engine, preferences
    source = tmp_path/'first.pdf'
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_font(fontname='fixture', fontfile='C:/Windows/Fonts/arial.ttf')
        page.insert_text((35, 60), 'Retry form', fontname='fixture')
        pdf.save(source)
    second = tmp_path/'second.pdf'
    shutil.copyfile(source, second)
    app.paths = []
    app.output.set(str(tmp_path/'output'))
    app.language.set('en')
    app.file_results.clear()
    monkeypatch.setattr(gui.filedialog, 'askopenfilenames', lambda **kwargs: (str(source), str(second)))
    original = engine.convert_pdf
    fail = True
    def conversion(info, *args, **kwargs):
        if info.path == second and fail:
            raise PermissionError('File locked by another app')
        return original(info, *args, **kwargs)
    monkeypatch.setattr(engine, 'convert_pdf', conversion)
    def wait():
        deadline = time.monotonic()+20
        while app.busy and time.monotonic() < deadline:
            app.update()
            time.sleep(.01)
        assert not app.busy
    app.add_files()
    wait()
    app.convert()
    wait()
    assert app.file_results[source]['content_check'] == 'passed'
    assert app.file_results[second]['status'] == 'failed'
    assert 'disabled' not in app.retry_button.state()
    details = []
    monkeypatch.setattr(gui.messagebox, 'showinfo', lambda *args: details.append(args))
    app.file_tree.selection_set('1')
    app.file_details()
    assert 'Close it in other apps' in details[0][1]
    assert 'File locked by another app' in details[0][1]
    first_bytes = (tmp_path/'output/first.docx').read_bytes()
    fail = False
    app.retry_button.invoke()
    wait()
    assert app.status.get().startswith('2 converted; 0 failed; 0 cancelled.')
    assert 'disabled' in app.retry_button.state()
    assert {p.name for p in (tmp_path/'output').iterdir()} == {'first.docx', 'second.docx'}
    assert (tmp_path/'output/first.docx').read_bytes() == first_bytes
    assert app.last_conversion[1][0].path == second
    assert preferences.load()['output'] == str(tmp_path/'output')


def test_cancel_rescan_invalidates_previous_scan(app, monkeypatch, tmp_path):
    source = tmp_path/'previous.pdf'
    app.paths = [source]
    app.infos = [PDFInfo(source, 1, {'Example': 'Test'}, sha256='old')]
    app.mapping = {'Example': FontFace('unused.ttf', 'Example', 'Example', 'Example', False, False, True)}
    app.font_chars = {'Example': 'Test'}
    monkeypatch.setattr(gui, 'inspect_pdf', lambda *args, **kwargs: (_ for _ in ()).throw(InterruptedError('Scan cancelled. Scan again before converting.')))
    app.scan()
    deadline = time.monotonic()+5
    while app.busy and time.monotonic() < deadline:
        app.update()
        time.sleep(.01)
    assert not app.busy
    assert not app.infos and not app.mapping
    messages = []
    monkeypatch.setattr(gui.messagebox, 'showinfo', lambda *args: messages.append(args))
    app.convert()
    assert messages[0][0] == app.t('Scan first')
