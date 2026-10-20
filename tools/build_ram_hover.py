# SPDX-License-Identifier: MPL-2.0
"""Build a research-only Ram hover candidate from the user's exact TBS1 SWF.

Original transformations only. Exported host p-code and generated SWF stay in
the local output directory. This tool never installs or runs the game.
"""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'research'))
from abc_index import abcs
from compare_swf import compare

CLASS = 'engine.battle.board.view.overlay.AbilityDestinationOverlay'
RESOURCE = Path('win32/app.game-saga1.air.swf')
PREFIX = 'engine.battle.board.view:DirtyRenderSprite'
RULE = 'engine.battle.ability.def'
VALIDATION = 'engine.battle.ability.model'


def q(name, namespace='', kind='PackageNamespace'):
    return f'QName({kind}({json.dumps(namespace)}),{json.dumps(name)})'


def instructions(*lines):
    return '\n'.join(lines) + '\n'


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Expected exactly one verified p-code seam: ' + old[:90])
    return text.replace(old, new, 1)


def extract_method(text, marker):
    if text.count(marker) != 1:
        raise ValueError('Method marker is not unique: ' + marker)
    lines = [line.strip() for line in text.split(marker, 1)[1].splitlines()]
    start = lines.index('method') + 1
    end = lines.index('end ; method', start)
    return '\n'.join(lines[start:end]) + '\n'


def hover_listener(action):
    return instructions(
        f'getlex {q("board")}',
        f'getlex {q("BattleBoardEvent", "engine.battle.board")}',
        f'getproperty {q("HOVER_TILE")}',
        'getlocal0',
        f'getproperty {q("bitmapPoolChangeHandler", PREFIX, "ProtectedNamespace")}',
        f'callpropvoid {q(action)}, 2')


def transform(methods):
    output = dict(methods)
    output['constructor'] = once(output['constructor'], 'returnvoid\n',
        hover_listener('addEventListener') + 'returnvoid\n')
    cleanup_seam = f'getlocal0\ncallsupervoid {q("cleanup")}, 0\n'
    output['cleanup'] = once(output['cleanup'], cleanup_seam,
        hover_listener('removeEventListener') + cleanup_seam)

    # Keep the renderer available for targetless Ram. Rendering is deferred;
    # HOVER_TILE fires before hoverEntity is assigned by the board controller.
    rule = f'getlex {q("BattleAbilityTargetRule", RULE)}\ngetproperty {q("SPECIAL_BATTERING_RAM")}\n'
    target_count = instructions('getlocal2', f'getproperty {q("targetSet")}',
        f'getproperty {q("targets")}', f'getproperty {q("length")}')
    allow = instructions('getlocal3') + rule + instructions(
        'ifne ram_hover_existing_gate', f'findproperty {q("canRender")}',
        'pushtrue', f'initproperty {q("canRender")}', 'returnvoid',
        'ram_hover_existing_gate:')
    output['checkCanRender'] = once(output['checkCanRender'], target_count,
        allow + target_count)

    render = output['onRender']
    render = once(render, 'maxstack 6\n', 'maxstack 9\n')
    start, end = render.index('ofs006a:\n'), render.index('ofs007f:\n')
    render = render[:start] + 'ofs006a:\n' + render[end:]
    # Preserve the native selected-target lookup verbatim, including namespace set.
    target_start = render.index('getlocal2\ngetproperty ' + q('targetSet'), render.index('setlocal 4\n'))
    target_end = render.index('pushdouble 0.5\n', target_start)
    selected = render[target_start:target_end]
    if not selected.endswith('setlocal 5\n'):
        raise ValueError('Unexpected selected target writer')
    candidate = target_count + instructions('pushbyte 0', 'ifgt ram_hover_selected', 'getlocal 4')
    candidate += rule + instructions('ifne ram_hover_return',
        f'getlex {q("PlatformInput", "com.stoicstudio.platform")}',
        f'getproperty {q("lastInputGp")}', 'iftrue ram_hover_return',
        f'getlex {q("SceneControllerConfig", "engine.scene")}',
        f'getproperty {q("instance")}', f'getproperty {q("restrictInput")}',
        'iftrue ram_hover_return', 'getlocal3',
        f'getproperty {q("playerControlled", "engine.entity.model:IEntity", "Namespace")}',
        'iffalse ram_hover_return', 'getlocal1', f'getproperty {q("move")}',
        'iffalse ram_hover_no_pending_move', 'getlocal1', f'getproperty {q("move")}',
        f'getproperty {q("executed", "engine.battle.board.model:IBattleMove", "Namespace")}',
        'iftrue ram_hover_no_pending_move', 'getlocal1', f'getproperty {q("move")}',
        f'getproperty {q("numSteps", "engine.battle.board.model:IBattleMove", "Namespace")}',
        'pushbyte 1', 'ifgt ram_hover_return', 'ram_hover_no_pending_move:',
        f'getlex {q("board")}', f'getproperty {q("hoverEntity")}',
        f'coerce {q("IBattleEntity", "engine.battle.board.model")}', 'setlocal 5',
        'getlocal 5', 'iffalse ram_hover_return',
        f'getlex {q("BattleAbilityValidation", VALIDATION)}', 'getlocal2',
        f'getproperty {q("def")}', 'getlocal3', 'pushnull', 'getlocal 5',
        'pushnull', 'pushfalse', 'pushtrue', 'pushtrue',
        f'callproperty {q("validate")}, 8',
        f'getlex {q("BattleAbilityValidation", VALIDATION)}',
        f'getproperty {q("OK")}', 'ifne ram_hover_return',
        'jump ram_hover_ready', 'ram_hover_return:', 'returnvoid',
        'ram_hover_selected:') + selected + 'ram_hover_ready:\n'
    render = render[:target_start] + candidate + render[target_end:]
    output['onRender'] = render
    return output


def command(java, ffdec, *args, cwd=None):
    subprocess.run([str(java), '-jar', str(ffdec), *map(str, args)], check=True, cwd=cwd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, required=True)
    parser.add_argument('--java', type=Path, required=True)
    parser.add_argument('--ffdec', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--development', action='store_true', help='Unnumbered, non-handoff tool validation')
    args = parser.parse_args()
    args.java, args.ffdec = args.java.resolve(), args.ffdec.resolve()
    root = Path(__file__).resolve().parents[1]
    game = args.game_root.resolve()
    out = args.out.resolve()
    if out == game or game in out.parents:
        raise ValueError('Output must be outside the game directory')
    if out.exists():
        raise ValueError('Output directory must not exist')
    source = game / RESOURCE
    expected = json.loads((root / 'data/baseline.json').read_text())['swf_sha256']
    if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
        raise ValueError('Unsupported SWF baseline; refusing to modify another mod')
    commit = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    if not args.development and subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain'], text=True).strip():
        raise ValueError('Commit source before freezing a numbered candidate')
    version = 'development-unversioned' if args.development else (root / 'VERSION').read_text().strip()
    out.mkdir(parents=True)
    command(args.java, args.ffdec, '-format', 'script:pcode', '-selectclass', CLASS,
        '-export', 'script', out / 'host-export', source, cwd=out)
    export = (out / 'host-export/scripts' / (CLASS.replace('.', '/') + '.pcode')).read_text(encoding='utf-8-sig')
    markers = {'constructor': 'public function AbilityDestinationOverlay(',
        'cleanup': 'override public function cleanup()',
        'onRender': 'override protected function onRender()',
        'checkCanRender': 'override protected function checkCanRender()'}
    original = {key: extract_method(export, marker) for key, marker in markers.items()}
    changed = transform(original)
    tag_index, abc = next((index, abc) for index, abc in abcs(source) if CLASS in abc.classes)
    cls = abc.classes[CLASS]
    ids = {'constructor': cls['init']}
    for key in markers:
        if key != 'constructor':
            ids[key] = next(t['method'] for t in cls['instance'] if t['name'].split('.')[-1] == key)
    indices = {key: next(b['index'] for b in abc.bodies if b['method'] == method) for key, method in ids.items()}
    patch_args = []
    for key, text in changed.items():
        path = out / (key + '.pcode')
        path.write_text(text, encoding='utf-8')
        patch_args.extend([CLASS, path, indices[key]])
    dest = out / f'BannerSagaUI-{version}-RamHover.swf'
    command(args.java, args.ffdec, '-replace', source, dest, *patch_args, cwd=out)
    report = compare(source, dest)
    if not report['frame_header_equal'] or len(report['changed_tags']) != 1:
        raise ValueError('Unexpected changes outside the ABC tag')
    tag = report['changed_tags'][0]
    if not tag['abc_header_equal'] or not tag['prefix_equal'] or tag['changed_method_info_count']:
        raise ValueError('Unexpected signature, constant, or trait change')
    if tag['changed_body_count'] != 4 or {x['index'] for x in tag['changed_bodies']} != set(indices.values()):
        raise ValueError('Unexpected method changes')
    result_abc = dict(abcs(dest))[tag_index]
    for key, index in indices.items():
        old, new = abc.bodies[index], result_abc.bodies[index]
        if any(old[field] != new[field] for field in
                ('method', 'locals', 'scope', 'maxscope', 'exceptions', 'tail')):
            raise ValueError('Unexpected local/scope/exception metadata change: ' + key)
        if new['stack'] != (9 if key == 'onRender' else old['stack']):
            raise ValueError('Unexpected stack requirement: ' + key)
    if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
        raise ValueError('Installed source changed during build')
    manifest = {'version': version, 'source_commit': commit, 'resource': RESOURCE.as_posix(),
        'scope': 'research: targetless mouse Ram arrows; no damage forecast',
        'status': 'static-verified; AIR/runtime/UX-unaccepted; not installed',
        'payload': dest.name, 'payload_sha256': report['after_sha256'],
        'original_sha256': expected, 'method_body_indices': indices,
        'structural_comparison': report,
        'python': sys.version.split()[0],
        'java_sha256': hashlib.sha256(args.java.read_bytes()).hexdigest(),
        'ffdec_sha256': hashlib.sha256(args.ffdec.read_bytes()).hexdigest()}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'payload': str(dest), 'version': version, 'sha256': manifest['payload_sha256']}))


if __name__ == '__main__':
    main()
