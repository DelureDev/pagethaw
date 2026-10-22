"""Build lean one-file and one-folder Windows releases from the same analysis."""
from pathlib import Path
import hashlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
import tomllib
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = tomllib.loads((ROOT/'pyproject.toml').read_text(encoding='utf-8'))['project']['version']
# Optional AI analysis is not used by PageThaw's coordinate-based converter.
EXCLUDES = ('pymupdf.layout', 'onnxruntime', 'numpy', 'pytest', 'IPython')
PUBLIC_FILES = ('README.md', 'README.ru.md', 'LICENSE', 'THIRD_PARTY.md', 'CONTRIBUTING.md')
NOTICE_PACKAGES = ('PyMuPDF', 'python-docx', 'fonttools', 'Pillow', 'lxml',
                   'typing_extensions', 'pyinstaller', 'pyinstaller-hooks-contrib')


def collect_notices(destination):
    destination.mkdir(parents=True, exist_ok=True)
    for name in PUBLIC_FILES:
        shutil.copy2(ROOT/name, destination/name)
    shutil.copytree(ROOT/'docs', destination/'docs', dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__'))
    licenses = destination/'licenses'
    licenses.mkdir(exist_ok=True)
    sources = []
    for package in NOTICE_PACKAGES:
        dist = metadata.distribution(package)
        name, version = dist.metadata['Name'], dist.version
        with urllib.request.urlopen(f'https://pypi.org/pypi/{name}/{version}/json', timeout=20) as response:
            info = json.load(response)
        entries = [{'url': f['url'], 'sha256': f['digests']['sha256']}
                   for f in info['urls'] if f['packagetype'] == 'sdist']
        if not entries:
            raise RuntimeError('Cannot resolve corresponding source for '+name)
        sources.append({'name': name, 'version': version, 'source_archives': entries,
                        'project_urls': dist.metadata.get_all('Project-URL') or []})
        for entry in dist.files or []:
            lower = str(entry).lower()
            if any(part in lower for part in ('license', 'copying', 'copyright', 'notice')) and entry.suffix.lower() in ('.txt', '.md', '.rst', ''):
                source = Path(dist.locate_file(entry))
                if source.is_file():
                    target = licenses/name/Path(*entry.parts[-3:])
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
    python_license = Path(sys.base_prefix)/'LICENSE.txt'
    if not python_license.exists():
        raise RuntimeError('Python license is missing from the build environment.')
    shutil.copy2(python_license, licenses/'PYTHON-LICENSE.txt')
    sources.append({'name': 'CPython', 'version': sys.version.split()[0],
                    'source_url': 'https://www.python.org/ftp/python/'+sys.version.split()[0]+'/Python-'+sys.version.split()[0]+'.tgz'})
    (destination/'DEPENDENCY_SOURCES.json').write_text(json.dumps(sources, indent=2), encoding='utf-8')


def audit_package(package, executable):
    """Fail a release if optional AI payloads or private documents creep back in."""
    import docx
    from PyInstaller.archive.readers import CArchiveReader
    blank_name = 'docx/templates/default.docx'
    upstream = Path(docx.__file__).parent/'templates'/'default.docx'
    blank = package/'_internal'/blank_name
    if blank.read_bytes() != upstream.read_bytes():
        raise RuntimeError('Bundled DOCX template does not match python-docx.')

    def check_name(name):
        name = name.replace('\\', '/').lower()
        parts = name.split('/')
        if (name.endswith('.onnx') or ('layout' in parts and 'pymupdf' in parts)
                or any(p.startswith(('onnxruntime', 'numpy')) for p in parts)):
            raise RuntimeError('Unused AI dependency in package: '+name)
        if ('sirius' in name or (Path(name).suffix in {'.pdf', '.docx', '.ttf', '.otf', '.ttc'}
                                and not name.endswith(blank_name))):
            raise RuntimeError('Unexpected document/font in package: '+name)

    for path in package.rglob('*'):
        if path.is_file():
            check_name(path.relative_to(package).as_posix())
    archive = CArchiveReader(str(executable))
    names = {name.replace('\\', '/'): name for name in archive.toc}
    for name in names:
        check_name(name)
    if archive.extract(names[blank_name]) != upstream.read_bytes():
        raise RuntimeError('Single-file DOCX template differs from upstream.')
    modules = archive.open_embedded_archive('PYZ.pyz').toc
    for module in modules:
        if any(module == banned or module.startswith(banned+'.') for banned in EXCLUDES):
            raise RuntimeError('Excluded Python module found: '+module)
    for required in ('pagethaw/word_worker.ps1', 'pagethaw/stop_owned_word.ps1',
                     'pagethaw_notices/LICENSE', 'pagethaw_notices/DEPENDENCY_SOURCES.json'):
        if required not in names:
            raise RuntimeError('Single-file resource missing: '+required)


def build():
    if sys.platform != 'win32':
        raise SystemExit('Build the Windows release on Windows.')
    work = ROOT/'build'/VERSION
    release = ROOT/'dist'/VERSION
    notices = work/'notices'
    collect_notices(notices)
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
                    '--distpath', str(release), '--workpath', str(work/'pyinstaller'),
                    str(ROOT/'scripts'/'PageThaw.spec')], check=True, cwd=ROOT)
    package = release/'PageThaw'
    executable = release/f'PageThaw-{VERSION}-windows-x64.exe'
    # Both formats embed notices; the folder edition also exposes them beside
    # the launcher so README links work without a special extraction command.
    shutil.copytree(notices, package, dirs_exist_ok=True)
    audit_package(package, executable)
    archive = release/f'PageThaw-{VERSION}-windows-x64.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zipped:
        for path in sorted(package.rglob('*')):
            if path.is_file():
                zipped.write(path, path.relative_to(package.parent))
    checksums = []
    for path in (executable, archive):
        checksums.append(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n')
        print('Built', path.name, path.stat().st_size, 'bytes')
    (release/'SHA256SUMS.txt').write_text(''.join(checksums), encoding='ascii')


if __name__ == '__main__':
    build()
