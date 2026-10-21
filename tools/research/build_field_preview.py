# SPDX-License-Identifier: MPL-2.0
"""Build an UNNUMBERED, uninstalled native field-preview research SWF.

Consumes compile_preview's isolated own ABC, preserves Ram hover, adds only
ScenePage update/cleanup calls. No game launch, installation or DEV adaptation.
"""
import argparse
import hashlib
import json
import re
import struct
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_ram_hover import command, extract_method, q
from abc_index import abcs, frame_header, swf_tags
from check_pcode_stack import require_balanced
from compare_swf import compare
from compile_preview import HOST_SHA256

CLASS = 'game.gui.page.ScenePage'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hooks(methods):
    result = {}
    for name, original in methods.items():
        header, rest = original.split('code\n', 1)
        code, tail = rest.split('end ; code\n', 1)
        callback = 'updatePage' if name == 'update' else 'cleanupPage'
        call = '\n'.join([f'getlex {q("FieldPreview", "bannersagaui.preview")}',
                          'getlocal0', f'callpropvoid {q(callback)}, 1']) + '\n'
        if name == 'update':
            # Preserve native early returns; only attach at the final seam.
            at = code.rfind('returnvoid\n')
            if at < 0 or code[at:].strip() != 'returnvoid':
                raise ValueError('Unexpected ScenePage.update final return')
        else:
            # After scope setup, before native cleanup releases its objects.
            seam = 'getlocal0\npushscope\n'
            if not code.startswith(seam):
                raise ValueError('Unexpected ScenePage.cleanup scope setup')
            at = len(seam)
        code = code[:at] + call + code[at:]
        header = re.sub(r'^maxstack (\d+)$', lambda m: 'maxstack ' + str(max(2, int(m[1]))),
                        header, flags=re.M)
        result[name] = header + 'code\n' + code + 'end ; code\n' + tail
        require_balanced(result[name])
    return result


def add_abc(source, destination, module):
    tags = swf_tags(source)
    # Put own definitions after native ABC but before any root construction.
    position = max(i for i, (code, _) in enumerate(tags) if code == 82) + 1
    tags.insert(position, (82, struct.pack('<I', 0) + b'BannerSagaUIFieldPreview\0' + module))
    body = frame_header(source)[1:]
    for code, payload in tags:
        body += (struct.pack('<H', (code << 6) | min(len(payload), 63)) +
                 (struct.pack('<I', len(payload)) if len(payload) >= 63 else b'') + payload)
    destination.write_bytes(b'FWS' + frame_header(source)[:1] + struct.pack('<I', len(body) + 8) + body)
    actual = swf_tags(destination)
    del actual[position]
    if actual != swf_tags(source) or frame_header(source) != frame_header(destination):
        raise ValueError('Module insertion changed native tags')
    return position


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, required=True)
    parser.add_argument('--java', type=Path, required=True)
    parser.add_argument('--ffdec', type=Path, required=True, help='ffdec-cli.jar')
    parser.add_argument('--module-dir', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True, help='Must not exist')
    args = parser.parse_args()
    game, java, ffdec, module_dir, out = [p.resolve() for p in
                                        (args.game_root, args.java, args.ffdec, args.module_dir, args.out)]
    source = game / 'win32/app.game-saga1.air.swf'
    if sha(source) != HOST_SHA256 or out.exists() or out == game or game in out.parents:
        raise ValueError('Expected original host and new output outside game')
    manifest = json.loads((module_dir / 'manifest.json').read_text(encoding='utf-8'))
    module = module_dir / 'preview.abc'
    if (manifest['mode'] != 'native-module' or manifest['host_sha256'] != HOST_SHA256 or
        manifest['outputs']['preview.abc'] != sha(module)):
        raise ValueError('Expected verified native-module ABC')
    root = Path(__file__).resolve().parents[2]
    for path, expected in {**manifest['sources'], **manifest['generator_inputs']}.items():
        if sha(root / path) != expected:
            raise ValueError('Source changed since module compilation: ' + path)
    out.mkdir(parents=True)
    subprocess.run([sys.executable, str(root / 'tools/build_ram_hover.py'), '--game-root', str(game),
                    '--java', str(java), '--ffdec', str(ffdec), '--out', str(out / 'hover'),
                    '--development'], check=True)
    hover = out / 'hover/BannerSagaUI-development-unversioned-RamHover.swf'
    assembled = out / 'module.swf'
    module_tag = add_abc(hover, assembled, module.read_bytes())
    command(java, ffdec, '-format', 'script:pcode', '-selectclass', CLASS,
            '-export', 'script', out / 'export', assembled, cwd=out)
    exported = (out / 'export/scripts/game/gui/page/ScenePage.pcode').read_text(encoding='utf-8-sig')
    methods = {name: extract_method(exported, 'override public function ' + name + '(')
               for name in ['update', 'cleanup']}
    _, before = next((i, a) for i, a in abcs(assembled) if CLASS in a.classes)
    ids = {name: next(t['method'] for t in before.classes[CLASS]['instance'] if t['name'] == name)
           for name in methods}
    indices = {name: next(b['index'] for b in before.bodies if b['method'] == mid)
               for name, mid in ids.items()}
    replacement = []
    for name, text in hooks(methods).items():
        path = out / (name + '.pcode')
        path.write_text(text, encoding='utf-8')
        replacement.extend([CLASS, path, indices[name]])
    output = out / 'BannerSagaUI-development-unversioned-FieldPreview.swf'
    command(java, ffdec, '-replace', assembled, output, *replacement, cwd=out)
    report = compare(assembled, output)
    if not report['frame_header_equal'] or len(report['changed_tags']) != 1:
        raise ValueError('Unexpected hook tag changes')
    change = report['changed_tags'][0]
    if (change['changed_method_info_count'] or change['changed_body_count'] != 2 or
        {b['index'] for b in change['changed_bodies']} != set(indices.values())):
        raise ValueError('Unexpected native method changes')
    _, after = next((i, a) for i, a in abcs(output) if CLASS in a.classes)
    for section in ['integer_pools', 'double_pool', 'method_info', 'metadata', 'class_script_traits']:
        if before.sections[section] != after.sections[section]:
            raise ValueError('Native ABC structure changed: ' + section)
    for pool in ['strings', 'namespaces', 'names']:
        old, new = getattr(before, pool), getattr(after, pool)
        if new[:len(old)] != old:
            raise ValueError('Existing native pool entries changed: ' + pool)
    for name, index in indices.items():
        old, new = before.bodies[index], after.bodies[index]
        for field in ['method', 'locals', 'scope', 'maxscope', 'exceptions', 'tail']:
            if old[field] != new[field]:
                raise ValueError('Native hook metadata changed: ' + name + ':' + field)
    # FFDec must preserve isolated own ABC exactly, too.
    if swf_tags(output)[module_tag] != swf_tags(assembled)[module_tag]:
        raise ValueError('Own module changed during native hook import')
    command(java, ffdec, '-format', 'script:pcode', '-selectclass', ','.join([CLASS] + manifest['classes']),
            '-export', 'script', out / 'final-export', output, cwd=out)
    final_export = (out / 'final-export/scripts/game/gui/page/ScenePage.pcode').read_text(encoding='utf-8-sig')
    checks = {name: require_balanced(extract_method(final_export,
              'override public function ' + name + '(')) for name in methods}
    module_checks = []
    for classname in manifest['classes']:
        path = out / 'final-export/scripts' / (classname.replace('.', '/') + '.pcode')
        text = path.read_text(encoding='utf-8-sig')
        for ordinal, body in enumerate(re.findall(r'(?ms)^\s*method\s*\n(.*?)^\s*end ; method\s*$', text)):
            body = '\n'.join(line.strip() for line in body.splitlines()) + '\n'
            if 'code\n' in body:
                module_checks.append({'class': classname, 'ordinal': ordinal, **require_balanced(body)})
    if not module_checks:
        raise ValueError('Missing own method exports')
    if sha(source) != HOST_SHA256:
        raise ValueError('Original input changed')
    record = {'status': 'research; unnumbered; NOT installed or game-runtime accepted',
              'payload': output.name, 'sha256': sha(output), 'original_sha256': HOST_SHA256,
              'module_sha256': sha(module), 'module_tag': module_tag, 'hook_body_indices': indices,
              'hook_comparison': report, 'hook_stack_checks': checks,
              'module_stack_checks': module_checks,
              'builder_inputs': {str(p.relative_to(root)): sha(p) for p in
                                 [Path(__file__).resolve(), root / 'tools/build_ram_hover.py',
                                  root / 'tools/research/check_pcode_stack.py',
                                  root / 'tools/research/compare_swf.py']},
              'hover_manifest': json.loads((out / 'hover/manifest.json').read_text()),
              'module_manifest': manifest}
    (out / 'manifest.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps({'payload': str(output), 'sha256': sha(output)}))


if __name__ == '__main__':
    main()
