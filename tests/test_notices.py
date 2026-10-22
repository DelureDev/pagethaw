import sys
import pytest
from pagethaw.notices import export_notices


def test_notices_export_preserves_existing_destination(tmp_path, monkeypatch):
    source = tmp_path/'runtime'/'pagethaw_notices'
    source.mkdir(parents=True)
    (source/'LICENSE').write_text('license text')
    monkeypatch.setattr(sys, '_MEIPASS', str(source.parent), raising=False)
    destination = tmp_path/'export'
    export_notices(destination)
    assert (destination/'LICENSE').read_text() == 'license text'
    (destination/'LICENSE').write_text('user file')
    with pytest.raises(FileExistsError):
        export_notices(destination)
    assert (destination/'LICENSE').read_text() == 'user file'
