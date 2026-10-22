"""Build a Windows one-folder app and package only an explicit public allowlist."""
from pathlib import Path
import hashlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def build():
    if sys.platform != 'win32':
        raise SystemExit('Build the Windows release on Windows.')
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir', '--windowed',
        '--name', 'PageThaw', '--paths', str(ROOT/'src'),
        '--add-data', str(ROOT/'src'/'pagethaw'/'word_worker.ps1')+';pagethaw',
        '--add-data', str(ROOT/'src'/'pagethaw'/'stop_owned_word.ps1')+';pagethaw',
        '--collect-data', 'docx', '--collect-data', 'pymupdf',
        '--exclude-module', 'pytest', '--exclude-module', 'IPython',
        '--distpath', str(ROOT/'dist'), '--workpath', str(ROOT/'build'),
        '--specpath', str(ROOT/'build'), str(ROOT/'scripts'/'launch.py')], check=True, cwd=ROOT)
    package = ROOT/'dist'/'PageThaw'
    for name in ('README.md', 'LICENSE', 'THIRD_PARTY.md'):
        shutil.copy2(ROOT/name, package/name)
    licenses = package/'licenses'
    licenses.mkdir(exist_ok=True)
    sources = []
    for dist in sorted(metadata.distributions(), key=lambda d: d.metadata['Name'].casefold()):
        name, version = dist.metadata['Name'], dist.version
        if name.casefold() == 'pagethaw':
            continue
        entries = []
        try:
            with urllib.request.urlopen(f'https://pypi.org/pypi/{name}/{version}/json', timeout=20) as response:
                info = json.load(response)
            entries = [{'url': f['url'], 'sha256': f['digests']['sha256']} for f in info['urls'] if f['packagetype'] == 'sdist']
        except Exception as exc:
            raise RuntimeError('Cannot resolve corresponding source for '+name) from exc
        sources.append({'name': name, 'version': version, 'source_archives': entries,
                        'project_urls': dist.metadata.get_all('Project-URL') or []})
        for entry in dist.files or []:
            lower = str(entry).lower()
            if any(part in lower for part in ('license', 'copying', 'copyright', 'notice')) and entry.suffix.lower() in ('.txt', '.md', '.rst', ''):
                source = Path(dist.locate_file(entry))
                if source.is_file():
                    destination = licenses/name/Path(*entry.parts[-3:])
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, destination)
    python_license = Path(sys.base_prefix)/'LICENSE.txt'
    if python_license.exists():
        shutil.copy2(python_license, licenses/'PYTHON-LICENSE.txt')
    sources.append({'name': 'CPython', 'version': sys.version.split()[0],
                    'source_url': 'https://www.python.org/ftp/python/'+sys.version.split()[0]+'/Python-'+sys.version.split()[0]+'.tgz'})
    (package/'DEPENDENCY_SOURCES.json').write_text(json.dumps(sources, indent=2), encoding='utf-8')
    import docx
    default_template = package/'_internal'/'docx'/'templates'/'default.docx'
    upstream_template = Path(docx.__file__).parent/'templates'/'default.docx'
    if hashlib.sha256(default_template.read_bytes()).digest() != hashlib.sha256(upstream_template.read_bytes()).digest():
        raise RuntimeError('Bundled DOCX template does not match python-docx.')
    forbidden = [p for p in package.rglob('*') if p.is_file() and p != default_template and
                 (p.suffix.lower() in {'.pdf', '.docx', '.ttf', '.otf', '.ttc'} or 'sirius' in p.name.lower())]
    if forbidden:
        raise RuntimeError('Unexpected document/font in portable package: '+str(forbidden))
    archive = ROOT/'dist'/'PageThaw-0.1.0-windows-x64.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zipped:
        for path in sorted(package.rglob('*')):
            if path.is_file():
                zipped.write(path, path.relative_to(package.parent))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (ROOT/'dist'/'SHA256SUMS.txt').write_text(f'{digest}  {archive.name}\n', encoding='ascii')
    print('Built', archive, archive.stat().st_size, 'bytes')


if __name__ == '__main__':
    build()
