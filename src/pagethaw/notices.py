"""Expose bundled license texts without requiring files beside the executable."""
from pathlib import Path
import shutil
import sys


def export_notices(destination):
    source = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[1]))/'pagethaw_notices'
    if not (source/'LICENSE').is_file():
        raise ValueError('Bundled notices are available in the portable release. See LICENSE and THIRD_PARTY.md in the source checkout.')
    # Refuse an existing destination, including an empty one, to preserve user files.
    shutil.copytree(source, Path(destination))
