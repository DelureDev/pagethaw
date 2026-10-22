from dataclasses import replace
from pathlib import Path
import os

import pytest

from pagethaw import preferences as prefs, i18n
from pagethaw.engine import PDFInfo
from pagethaw.fonts import read_font


@pytest.fixture
def state(tmp_path, monkeypatch):
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path))
    font = tmp_path/'Arial.ttf'
    font.write_bytes((Path(os.environ.get('WINDIR', 'C:/Windows'))/'Fonts/arial.ttf').read_bytes())
    return read_font(font, installed=True), PDFInfo(tmp_path/'sample.pdf', 1, {'OtherFont': 'Test'}, sha256='source-one')


def test_output_font_choice_and_language_coexist(state):
    face, info = state
    assert prefs.save({'output': 'C:/Example output'})
    assert prefs.remember_font('OtherFont', face, [info])
    assert i18n.save_language('ru')
    assert prefs.load()['output'] == 'C:/Example output'
    assert prefs.restore_fonts([info], [face]) == {'OtherFont': face}
    assert i18n.load_language() == 'ru'


def test_replacement_is_not_reused_for_different_or_changed_source(state):
    face, info = state
    prefs.remember_font('OtherFont', face, [info])
    assert not prefs.restore_fonts([replace(info, sha256='changed')], [face])
    assert not prefs.restore_fonts([info, replace(info, sha256='another')], [face])
    assert not prefs.restore_fonts([replace(info, sha256='')], [face])


def test_changed_removed_or_uninstalled_font_requires_new_choice(state):
    face, info = state
    prefs.remember_font('OtherFont', face, [info])
    assert not prefs.restore_fonts([info], [])
    assert not prefs.restore_fonts([info], [replace(face, installed=False)])
    Path(face.path).write_bytes(b'changed')
    assert not prefs.restore_fonts([info], [face])
    Path(face.path).unlink()
    assert not prefs.restore_fonts([info], [face])


def test_new_family_conflict_invalidates_approval(state, tmp_path):
    face, info = state
    prefs.remember_font('OtherFont', face, [info])
    duplicate = tmp_path/'other.ttf'
    duplicate.write_bytes(b'different version')
    assert not prefs.restore_fonts([info], [face, replace(face, path=str(duplicate))])


@pytest.mark.parametrize('entries', [None, 'broken', [None, 4, {}, {'name': [], 'path': {}}]])
def test_malformed_preferences_do_not_break_scan(state, entries):
    face, info = state
    assert not prefs.restore_fonts([info], [face], {'font_approvals': entries})


def test_verified_font_can_be_reused_for_new_pdf(state, monkeypatch):
    face, info = state
    prefs.remember_font('OtherFont', face, [info])
    monkeypatch.setattr(prefs, 'match_status', lambda *args: 'verified')
    assert prefs.restore_fonts([replace(info, sha256='new')], [face]) == {'OtherFont': face}
