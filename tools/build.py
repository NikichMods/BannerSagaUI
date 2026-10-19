# SPDX-License-Identifier: MPL-2.0
"""Build one guarded local locale candidate; never writes into the game."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import zlib
from amf3 import Reader, u29

RELATIVE = Path('assets/common/locale/ru/strings.json.z')
KEY = 'pg_q_stat_strength'
NEW = "<font color='#FF6048'>Сила</font> — здоровье и основа урона воина. Потеря силы ослабляет обычную атаку. При 0 воин теряет сознание."

def digest(data):
    return hashlib.sha256(data).hexdigest()

def patch(source, expected_hash):
    if digest(source) != expected_hash:
        raise ValueError('Unsupported locale baseline; do not overwrite other mods')
    raw = zlib.decompress(source)
    reader = Reader(raw)
    original = reader.read_all()
    old = original['GUI'][KEY]
    spans = reader.spans.get(old, [])
    if len(spans) != 1:
        raise ValueError('Expected exactly one inline string record')
    start, end = spans[0]
    encoded = NEW.encode('utf-8')
    changed = raw[:start] + u29(len(encoded) * 2 + 1) + encoded + raw[end:]
    expected = json.loads(json.dumps(original))
    expected['GUI'][KEY] = NEW
    if Reader(changed).read_all() != expected:
        raise ValueError('Unexpected semantic changes or shared string reference')
    return zlib.compress(changed, 9), {'category': 'GUI', 'key': KEY,
        'original_sha256': digest(source), 'patched_sha256': digest(zlib.compress(changed, 9)),
        'original_amf_sha256': digest(raw), 'patched_amf_sha256': digest(changed),
        'original_bytes': len(source), 'patched_bytes': len(zlib.compress(changed, 9))}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    source_commit = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    if subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain'], text=True).strip():
        raise ValueError('Commit or preserve pending work before freezing a candidate')
    baseline = json.loads((root/'data/baseline.json').read_text(encoding='utf-8'))
    source = (args.game_root/RELATIVE).read_bytes()
    payload, manifest = patch(source, baseline['locale_sha256'])
    manifest['version'] = (root/'VERSION').read_text().strip()
    manifest['source_commit'] = source_commit
    manifest['resource'] = RELATIVE.as_posix()
    manifest['build_status'] = 'static-verified; runtime-unaccepted'
    manifest['toolchain'] = 'Python 3.13 stdlib; zlib runtime recorded by version'
    manifest['zlib_runtime'] = zlib.ZLIB_RUNTIME_VERSION
    args.out.mkdir(parents=True, exist_ok=False)
    dest = args.out/RELATIVE
    dest.parent.mkdir(parents=True)
    dest.write_bytes(payload)
    (args.out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(manifest, ensure_ascii=False))

if __name__ == '__main__':
    main()
