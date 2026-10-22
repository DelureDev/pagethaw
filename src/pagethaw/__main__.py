from pathlib import Path
import argparse
import json
import sys

from . import __version__


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if len(sys.argv) == 1:
        from .gui import launch
        launch()
        return 0
    parser = argparse.ArgumentParser(description='PageThaw — offline PDF forms to editable Word. Run without arguments for the GUI.')
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('--inspect', nargs='+', type=Path, metavar='PDF')
    parser.add_argument('--convert', nargs='+', type=Path, metavar='PDF')
    parser.add_argument('--font-map', type=Path, help='JSON object: PDF font name → installed .ttf/.otf file path. Explicit mappings approve substitution.')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--rules', action='store_true', help='Convert standalone runs of 3+ underscores into vector lines')
    parser.add_argument('--dpi', type=int, choices=[96, 144, 192], default=144)
    parser.add_argument('--self-test', type=Path, metavar='NEW_FOLDER', help='Run a synthetic portable-runtime smoke test and write its report')
    args = parser.parse_args()
    if args.self_test:
        from .smoke import run
        run(args.self_test)
        return 0
    from .engine import inspect_pdf, convert_batch
    from .fonts import installed_fonts, read_font
    paths = args.inspect or args.convert
    if not paths:
        parser.error('Choose --inspect, --convert, or run without arguments for the GUI.')
    infos = [inspect_pdf(p) for p in paths]
    if args.inspect:
        value = [{'file': str(i.path), 'pages': i.pages, 'fonts': sorted(i.fonts), 'error': i.error} for i in infos]
        print(json.dumps(value, ensure_ascii=False, indent=2))
        return int(any(i.error for i in infos))
    if not args.output:
        parser.error('--convert requires --output')
    faces = installed_fonts()
    mapping = {}
    for info in infos:
        for name in info.fonts:
            matches = [face for face in faces if face.matches(name)]
            if len(matches) == 1:
                mapping[name] = matches[0]
    if args.font_map:
        raw = json.loads(args.font_map.read_text(encoding='utf-8-sig'))
        for name, path in raw.items():
            candidate = read_font(Path(path))
            matches = [face for face in faces if Path(face.path).resolve() == Path(candidate.path).resolve()]
            if not matches:
                raise ValueError('Mapped font is not registered with Windows: '+candidate.full_name)
            mapping[name] = matches[0]
    records = convert_batch(infos, args.output, mapping, rules=args.rules, dpi=args.dpi)
    print(json.dumps(records, ensure_ascii=False, indent=2))
    return int(any(r.get('content_check') != 'passed' for r in records))


if __name__ == '__main__':
    raise SystemExit(main())
