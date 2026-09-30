"""Build a byte-preserving offline kit; refuse to overwrite an existing ZIP."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
KIT_NAME = 'stage3-environment-check-v0.1'
KIT = ROOT / 'local-tools' / KIT_NAME


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(root, item):
    path = (root / item['path']).resolve()
    if not path.is_relative_to(root):
        raise ValueError('path_outside_source_root')
    raw = path.read_bytes()
    if sha(raw) != item['sha256']:
        raise ValueError('source_hash_mismatch:' + item['path'])
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'distributions' / (KIT_NAME + '.zip'))
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or output.with_suffix('.zip.sha256').exists():
        parser.error('choose a new ZIP path; existing artifacts are never overwritten')
    files = {}
    tool_manifest = (KIT / 'tool-manifest.json').read_bytes()
    for row in json.loads(tool_manifest)['files']:
        files[row['path']] = checked(KIT, row)
    files['tool-manifest.json'] = tool_manifest
    for row in json.loads(files['target-manifest.json'])['files']:
        files['targets/repo/' + row['path']] = checked(ROOT, row)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(files.items()):
            info = zipfile.ZipInfo(KIT_NAME + '/' + name, date_time=(2026, 9, 30, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)
    digest = sha(output.read_bytes())
    with output.with_suffix('.zip.sha256').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(digest + '  ' + output.name + '\n')
    print(json.dumps({'zip': str(output), 'sha256': digest, 'file_count': len(files),
                      'model_api_calls': 0, 'windows_check_started': False}))


if __name__ == '__main__':
    main()
