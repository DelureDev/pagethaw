from dataclasses import replace
from pathlib import Path
import os

import pymupdf
import pytest
from fontTools.ttLib import TTFont

from pagethaw.engine import inspect_pdf
from pagethaw.fonts import read_font
from pagethaw.font_match import match_status, automatic_mapping, family_conflicts


@pytest.fixture
def sample(tmp_path):
    face = read_font(Path(os.environ.get('WINDIR', 'C:/Windows'))/'Fonts/arial.ttf', True)
    path = tmp_path/'synthetic.pdf'
    with pymupdf.open() as pdf:
        page = pdf.new_page()
        page.insert_font(fontname='fixture', fontfile=face.path)
        page.insert_text((30, 60), 'Test / Пример / é', fontname='fixture')
        pdf.subset_fonts()
        pdf.save(path)
    return inspect_pdf(path), face


def test_subset_font_verifies_against_full_installed_face(sample):
    info, face = sample
    name = next(iter(info.fonts))
    assert match_status([info], name, face) == 'verified'
    assert automatic_mapping([info], [face]) == {name: face}


def test_same_name_changed_metrics_is_not_automatically_accepted(sample, tmp_path):
    info, face = sample
    changed = tmp_path/'changed.ttf'
    with TTFont(face.path) as font:
        name = font.getBestCmap()[ord('T')]
        advance, bearing = font['hmtx'][name]
        font['hmtx'][name] = (advance+120, bearing)
        font.save(changed)
    other = read_font(changed, True)
    name = next(iter(info.fonts))
    assert other.matches(name)
    assert match_status([info], name, other) == 'different'
    assert not automatic_mapping([info], [other])
    assert family_conflicts(face, [face, other])
    assert not automatic_mapping([info], [face, other])


def test_no_embedded_proof_needs_explicit_choice(sample):
    info, face = sample
    info.font_proofs.clear()
    assert match_status([info], next(iter(info.fonts)), face) == 'unverified'
    assert not automatic_mapping([info], [face])


def test_all_documents_must_verify(sample):
    info, face = sample
    another = replace(info, font_proofs={})
    assert not automatic_mapping([info, another], [face])


def test_renamed_exact_face_can_be_verified_when_selected(sample):
    info, face = sample
    renamed = replace(face, family='User supplied family', full_name='User supplied face', postscript='Renamed')
    assert match_status([info], next(iter(info.fonts)), renamed) == 'verified'
