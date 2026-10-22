"""Local preferences. A remembered replacement is scoped to the approved PDFs."""
import hashlib
import json
import os
import tempfile
from pathlib import Path

from .font_match import family_conflicts, match_status
from .fonts import missing_glyphs


def preference_path():
    return Path(os.environ.get('LOCALAPPDATA', Path.home()/'.config'))/'PageThaw'/'settings.json'


def load(path=None):
    try:
        value = json.loads((path or preference_path()).read_text(encoding='utf-8'))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def save(values, path=None):
    path = path or preference_path()
    temporary = None
    try:
        current = load(path)
        current.update(values)
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(current, stream, ensure_ascii=False, indent=2)
        temporary.replace(path)
        return True
    except OSError:
        return False
    finally:
        if temporary:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def font_hash(face):
    return hashlib.sha256(Path(face.path).read_bytes()).hexdigest()


def remember_font(name, face, infos):
    sources = sorted({i.sha256 for i in infos if not i.error and name in i.fonts and i.sha256})
    if not sources:
        return True
    try:
        entry = dict(name=name, path=str(Path(face.path).resolve()), sha256=font_hash(face), sources=sources)
    except OSError:
        return False
    entries = load().get('font_approvals', [])
    if not isinstance(entries, list):
        entries = []
    entries = [e for e in entries if isinstance(e, dict) and e.get('name') != name]
    return save({'font_approvals': (entries+[entry])[-200:]})


def restore_fonts(infos, faces, settings=None):
    entries = (settings if settings is not None else load()).get('font_approvals', [])
    if not isinstance(entries, list):
        return {}
    restored = {}
    by_path = {str(Path(face.path).resolve()): face for face in faces if face.installed}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        name, path = entry.get('name'), entry.get('path')
        if not isinstance(name, str) or not isinstance(path, str):
            continue
        relevant = [i for i in infos if not i.error and name in i.fonts]
        face = by_path.get(path)
        if not face or not relevant:
            continue
        try:
            if font_hash(face) != entry.get('sha256') or family_conflicts(face, faces):
                continue
            if missing_glyphs(face, ''.join(i.fonts[name] for i in relevant)):
                continue
            sources = entry.get('sources', [])
            if not isinstance(sources, list):
                continue
            same_sources = all(i.sha256 and i.sha256 in sources for i in relevant)
            if same_sources or match_status(relevant, name, face) == 'verified':
                restored[name] = face
        except (OSError, ValueError):
            continue
    return restored
