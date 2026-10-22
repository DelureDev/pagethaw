"""Read font identities and coverage without extracting fonts from PDFs."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from functools import lru_cache
from pathlib import Path
import hashlib
import os
import re
import shutil
import sys

from fontTools.ttLib import TTFont


def normalized(name: str) -> str:
    name = re.sub(r"^[A-Z]{6}\+", "", name)
    return re.sub(r"[^\w]", "", name).casefold()


@dataclass(frozen=True)
class FontFace:
    path: str
    family: str
    full_name: str
    postscript: str
    bold: bool
    italic: bool
    installed: bool = False
    version: str = ''
    aliases: tuple[str, ...] = ()

    @property
    def label(self):
        return self.full_name + (" [Bold]" if self.bold else "") + (" [Italic]" if self.italic else "") + (f' · {self.version}' if self.version else '')

    def matches(self, pdf_name):
        # Full-face identity only: matching a family alone can select the wrong weight.
        return normalized(pdf_name) in {normalized(n) for n in (self.postscript, self.full_name, *self.aliases)}

    def to_dict(self):
        return asdict(self)


def read_font(path: Path, installed=False) -> FontFace:
    path = path.resolve()
    if path.suffix.lower() not in {'.otf', '.ttf'}:
        raise ValueError('Choose an individual .ttf or .otf face. Font collections are not supported yet.')
    with TTFont(path, lazy=True) as font:
        if 'fvar' in font:
            raise ValueError('Variable fonts are not supported yet; use a static font face.')
        names = font['name']
        get = lambda key: names.getDebugName(key) or ''
        family = get(1)
        if not family or not get(6):
            raise ValueError('Font does not contain a usable family and PostScript identity.')
        style = get(2).casefold()
        flags = font['OS/2'].fsSelection if 'OS/2' in font else 0
        mac = font['head'].macStyle
        return FontFace(str(path), family, get(4) or family, get(6),
                        bool(flags & 32 or mac & 1 or 'bold' in style),
                        bool(flags & 1 or mac & 2 or 'italic' in style or 'oblique' in style), installed,
                        get(5).split(';')[0], (family+' '+get(2),))


@lru_cache(maxsize=128)
def glyphs(path: str, modified: int) -> frozenset[int]:
    with TTFont(path, lazy=True) as font:
        return frozenset(font.getBestCmap() or {})


def missing_glyphs(face, text):
    chars = glyphs(face.path, Path(face.path).stat().st_mtime_ns)
    return sorted({c for c in text if not c.isspace() and ord(c) not in chars})


def installed_fonts() -> list[FontFace]:
    paths = set()
    if sys.platform == 'win32':
        import winreg
        base = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'
        user = Path(os.environ['LOCALAPPDATA']) / 'Microsoft' / 'Windows' / 'Fonts'
        for hive, folder in ((winreg.HKEY_LOCAL_MACHINE, base), (winreg.HKEY_CURRENT_USER, user)):
            try:
                with winreg.OpenKey(hive, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts') as key:
                    for i in range(winreg.QueryInfoKey(key)[1]):
                        _, value, kind = winreg.EnumValue(key, i)
                        if kind not in (winreg.REG_SZ, winreg.REG_EXPAND_SZ):
                            continue
                        path = Path(os.path.expandvars(value))
                        paths.add(path if path.is_absolute() else folder / path)
            except OSError:
                pass
    else:
        for base in (Path('/usr/share/fonts'), Path('/Library/Fonts'), Path.home()/'.local/share/fonts'):
            if base.exists():
                paths.update(base.rglob('*.ttf'))
                paths.update(base.rglob('*.otf'))
    faces = []
    for path in sorted(paths, key=lambda p: str(p).casefold()):
        try:
            faces.append(read_font(path, installed=True))
        except Exception:
            # Malformed / unsupported system font files must not break the font chooser.
            continue
    return sorted(faces, key=lambda f: f.label.casefold())


def install_for_current_user(path: Path) -> FontFace:
    """Called only after the GUI explicitly asks the person to install this font."""
    if sys.platform != 'win32':
        raise ValueError('Install this font using your operating system, then rescan fonts.')
    import ctypes
    import winreg
    face = read_font(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    folder = Path(os.environ['LOCALAPPDATA']) / 'Microsoft' / 'Windows' / 'Fonts'
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / f'PageThaw-{digest}{path.suffix.lower()}'
    if not destination.exists():
        shutil.copy2(path, destination)
    if not ctypes.windll.gdi32.AddFontResourceExW(str(destination), 0, None):
        raise ValueError('Windows could not activate this font. Install it with Windows Font Viewer.')
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts') as key:
        winreg.SetValueEx(key, face.full_name+' (PageThaw '+digest+')', 0, winreg.REG_SZ, str(destination))
    result = ctypes.c_size_t()
    ctypes.windll.user32.SendMessageTimeoutW(0xFFFF, 0x001D, 0, 0, 2, 1000, ctypes.byref(result))
    return read_font(destination, installed=True)
