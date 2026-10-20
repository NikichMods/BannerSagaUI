# SPDX-License-Identifier: MPL-2.0
"""Build a temporary hero-portrait animation probe; never installs or launches.

Layer over the immutable test.6 candidate, with its unmodified portrait method
checked against the original game. Preserve instruction offsets with NOPs.
Host bytecode and generated payloads must remain outside Git.
"""
import argparse
import hashlib
import json
import struct
import subprocess
import zlib
from pathlib import Path

from abc_index import abcs, Reader
from compare_swf import compare

CLASS = 'game.gui.pages.GuiPgDetails'
INPUT_SHA = '4f94d821b008655a3b969b3e4a0c1996d26919e0cbe86ef78d8ca63714fd954c'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def u30(value):
    result = bytearray()
    while value >= 128:
        result.append((value & 127) | 128)
        value >>= 7
    result.append(value)
    return bytes(result)


def target(path):
    tag, abc = next((i, a) for i, a in abcs(path) if CLASS in a.classes)
    method = next(t['method'] for t in abc.classes[CLASS]['instance']
                  if t['name'] == 'update')
    body = next(b for b in abc.bodies if b['method'] == method)
    return tag, abc, body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    if args.out.exists():
        raise ValueError('Output must not exist; frozen artifacts are immutable')
    if sha(args.input) != INPUT_SHA:
        raise ValueError('Expected immutable test.6 candidate, not installed DEV')
    baseline_sha = json.loads((root / 'data/baseline.json').read_text())['swf_sha256']
    if sha(args.baseline) != baseline_sha:
        raise ValueError('Original baseline hash mismatch')
    if subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain'], text=True).strip():
        raise ValueError('Commit source before freezing this candidate')
    tag, abc, body = target(args.input)
    if body['raw'] != target(args.baseline)[2]['raw']:
        raise ValueError('Portrait update no longer matches original game')
    def name_index(name):
        matches = [i for i, (kind, _) in enumerate(abc.names)
                   if kind in (7, 13) and abc.qname(i) == name]
        if len(matches) != 1:
            raise ValueError('Ambiguous public name: ' + name)
        return matches[0]
    # this.portrait.update(delta): remove both argument evaluation and the call.
    seam = b'\xd0\x66' + u30(name_index('portrait')) + b'\xd1\x4f' + u30(name_index('update')) + b'\x01'
    if body['code'].count(seam) != 1:
        raise ValueError('Expected exactly one portrait update call')
    start = body['code'].index(seam)
    # Verified TBS1 method has no branch target inside this expression (p-code).
    changed_code = body['code'][:start] + b'\x02' * len(seam) + body['code'][start + len(seam):]
    reader = Reader(body['raw'])
    reader.many(5)
    if reader.uint() != len(body['code']):
        raise ValueError('Method code length mismatch')
    changed_body = body['raw'][:reader.pos] + changed_code + body['raw'][reader.pos + len(body['code']):]
    raw = args.input.read_bytes()
    unpacked = zlib.decompress(raw[8:]) if raw[:3] == b'CWS' else raw[8:]
    if raw[:3] not in (b'CWS', b'FWS') or unpacked.count(body['raw']) != 1:
        raise ValueError('Unsupported or ambiguous SWF body')
    patched = unpacked.replace(body['raw'], changed_body, 1)
    args.out.mkdir(parents=True)
    version = (root / 'VERSION').read_text().strip()
    payload = args.out / f'BannerSagaUI-{version}-PortraitFreeze.swf'
    encoded = zlib.compress(patched) if raw[:3] == b'CWS' else patched
    payload.write_bytes(raw[:4] + struct.pack('<I', len(patched) + 8) + encoded)
    report = compare(args.input, payload)
    expected_changes = report['changed_tags']
    assert report['frame_header_equal'] and len(expected_changes) == 1
    change = expected_changes[0]
    assert change['index'] == tag and change['prefix_equal'] and change['abc_header_equal']
    assert change['changed_method_info_count'] == 0 and change['changed_body_count'] == 1
    assert change['changed_bodies'][0]['index'] == body['index']
    assert change['changed_bodies'][0]['metadata_equal']
    assert target(payload)[2]['raw'] == changed_body
    assert sha(args.input) == INPUT_SHA
    manifest = dict(version=version, source_commit=subprocess.check_output(
        ['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
        source_dirty=False, payload=payload.name, sha256=sha(payload),
        base_candidate_sha256=INPUT_SHA, original_sha256=baseline_sha,
        scope='Research only: suppress hero-detail portrait animation update; retain test.6 diagnostics',
        changed_class=CLASS, method='update', body_index=body['index'],
        code_offset=start, nop_bytes=len(seam), structural_comparison=report,
        runtime_verified=False, python=__import__('sys').version.split()[0])
    (args.out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest))


if __name__ == '__main__':
    main()
