# SPDX-License-Identifier: MPL-2.0
"""Build an UNNUMBERED local diagnostic; never installs or launches the game.

Compile original diagnostic source in a disposable donor, then transplant only
its symbolic instructions into a guarded branch. Never ship the donor: FFDec's
whole-class replacement renumbers unrelated methods.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from build_ram_hover import command, extract_method, instructions, once, q, transform
from abc_index import abcs, swf_tags, frame_header, Reader

DATA = 'engine.battle.ability.model.StatChangeData'
ABILITY = 'engine.battle.ability.model.BattleAbility'
MANAGER = 'engine.battle.ability.model.BattleAbilityManager'
OVERLAY = 'engine.battle.board.view.overlay.AbilityDestinationOverlay'
IMPORTS = [
    'engine.battle.ability.def.BattleAbilityDef',
    'engine.battle.ability.def.IBattleAbilityDef',
    'engine.battle.ability.model.BattleAbility',
    'engine.battle.ability.model.BattleAbilityManager',
    'engine.battle.ability.model.BattleAbilityValidation',
    'engine.battle.ability.model.AbilityReason',
    'engine.battle.ability.effect.model.Effect',
    'engine.battle.ability.effect.model.EffectTag',
    'engine.battle.ability.effect.op.model.Op',
    'engine.battle.ability.effect.op.model.Op_ChangeStat',
    'engine.battle.ability.effect.op.model.Op_IntStatMod',
    'engine.battle.ability.effect.op.model.Op_KnockbackHelper',
    'engine.battle.board.model.IBattleBoard',
    'engine.battle.board.model.IBattleEntity',
    'engine.battle.board.model.IBattleMove',
    'engine.stat.def.StatType',
    'engine.tile.Tile', 'engine.tile.ITileResident',
    'engine.tile.def.TileRect', 'engine.tile.def.TileRectRange',
    'engine.tile.def.TileLocation', 'flash.utils.Dictionary',
]


def export(java, ffdec, source, out, classes, pcode=False):
    args = ['-format', 'script:pcode'] if pcode else []
    command(java, ffdec, *args, '-selectclass', ','.join(classes),
            '-export', 'script', out, source, cwd=out.parent)


def script(out, classname, suffix):
    return (out / 'scripts' / (classname.replace('.', '/') + suffix)).read_text(encoding='utf-8-sig')


def split_body(method):
    header, rest = method.split('code\n', 1)
    code, end = rest.split('end ; code\n', 1)
    return header, code, end


def splice_probe(original, donor):
    """Keep the normal code verbatim; give diagnostic activation slots new IDs."""
    oh, oc, ot = split_body(original)
    dh, dc, dt = split_body(donor)
    if 'newfunction ' in dc or 'getouterscope ' in dc:
        raise ValueError('Donor has nonportable function/scope references')
    slot_offset = max(map(int, re.findall(r'^slotid (\d+)$', oh, re.M)))
    donor_traits = dh[dh.index('trait slot '):]
    old_names = re.findall(r'^trait slot (.*)$', oh, re.M)
    new_names = re.findall(r'^trait slot (.*)$', donor_traits, re.M)
    if set(old_names) & set(new_names):
        raise ValueError('Activation names overlap')
    donor_traits = re.sub(r'^slotid (\d+)$', lambda m: 'slotid ' + str(int(m[1])+slot_offset), donor_traits, flags=re.M)
    dc = re.sub(r'\bofs[0-9a-f]+\b', lambda m: 'bsui_' + m[0], dc)
    dt = re.sub(r'\bofs[0-9a-f]+\b', lambda m: 'bsui_' + m[0], dt)
    exceptions = len(re.findall(r'^try from ', ot, re.M))
    lines = dc.splitlines()
    for i, line in enumerate(lines):
        match = re.fullmatch(r'(getslot|setslot) (\d+)', line)
        if match:
            # All getters are activation slots except the compiler's catch
            # scope. Its single exception slot must retain ID 1.
            catch = (match[1] == 'getslot' and lines[i-1] == 'getscopeobject 2') or (
                match[1] == 'setslot' and lines[i-1] == 'swap')
            if catch:
                if match[2] != '1':
                    raise ValueError('Unexpected catch slot')
            else:
                if match[1] == 'getslot' and lines[i-1] != 'getscopeobject 1':
                    raise ValueError('Unverified nonactivation slot access')
                lines[i] = match[1] + ' ' + str(int(match[2]) + slot_offset)
        if line.startswith('newcatch '):
            lines[i] = 'newcatch ' + str(int(line.split()[1]) + exceptions)
    dc = '\n'.join(lines) + '\n'
    init = int(re.search(r'initscopedepth (\d+)', oh)[1])
    donor_init = int(re.search(r'initscopedepth (\d+)', dh)[1])
    for field in ('maxstack', 'localcount', 'maxscopedepth'):
        old_value = int(re.search(field + r' (\d+)', oh)[1])
        new_value = int(re.search(field + r' (\d+)', dh)[1])
        if field == 'maxscopedepth':
            new_value += init - donor_init
        oh = re.sub(field + r' \d+', field + ' ' + str(max(old_value,new_value)), oh, count=1)
    guard = instructions('getlocal3', 'iftrue bsui_stock', 'getlocal 4',
        'iffalse bsui_entry', 'getlocal 4', f'getproperty {q("missChance")}',
        'pushshort -16384', 'ifne bsui_stock', 'bsui_entry:')
    return oh + donor_traits + 'code\n' + guard + dc + 'bsui_stock:\n' + oc + 'end ; code\n' + ot.replace('end ; body\n','') + dt


def verify_isolation(before, after, allowed):
    left, right = swf_tags(before), swf_tags(after)
    if len(left) != len(right) or frame_header(before) != frame_header(after):
        raise ValueError('SWF envelope changed')
    a, b = dict(abcs(before)), dict(abcs(after))
    changes = []
    for i, (x,y) in enumerate(zip(left,right)):
        if x == y: continue
        if x[0] != 82 or y[0] != 82: raise ValueError('Non-ABC tag changed')
        aa, bb = a[i], b[i]
        if aa.method_count != bb.method_count or len(aa.bodies) != len(bb.bodies) or aa.classes != bb.classes:
            raise ValueError('Method or class identity changed')
        if aa.methods != bb.methods: raise ValueError('Method signature changed')
        for section in ('metadata','class_script_traits'):
            if aa.sections[section] != bb.sections[section]:
                raise ValueError('Existing metadata/traits changed')
        for section in ('integer_pools','double_pool','names'):
            ar, br = Reader(aa.sections[section]), Reader(bb.sections[section])
            if section == 'integer_pools':
                for _ in range(2):
                    av = [ar.uint(32) for _ in range(max(0,ar.uint()-1))]
                    bv = [br.uint(32) for _ in range(max(0,br.uint()-1))]
                    if bv[:len(av)] != av: raise ValueError('Integer pool reindexed')
            elif section == 'double_pool':
                ac, bc = ar.uint(),br.uint()
                if bc < ac or ar.take(8*max(0,ac-1)) != br.take(8*max(0,ac-1)):
                    raise ValueError('Double pool reindexed')
            else:
                for r in (ar,br):
                    for _ in range(max(0,r.uint()-1)): r.byte();r.uint()
                av = [ar.many(ar.uint()) for _ in range(max(0,ar.uint()-1))]
                bv = [br.many(br.uint()) for _ in range(max(0,br.uint()-1))]
                if bv[:len(av)] != av: raise ValueError('Namespace set pool reindexed')
        if bb.strings[:len(aa.strings)] != aa.strings or bb.namespaces[:len(aa.namespaces)] != aa.namespaces or bb.names[:len(aa.names)] != aa.names:
            raise ValueError('Existing pool entries changed')
        for old,new in zip(aa.bodies,bb.bodies):
            if old['raw'] == new['raw']: continue
            key = (i,old['index'])
            if key not in allowed or old['method'] != new['method']:
                raise ValueError('Unrelated method body changed: ' + str(key))
            changes.append(key)
    if set(changes) != set(allowed): raise ValueError('Missing requested body change')
    return {'changed_bodies': changes, 'existing_method_signatures_and_class_traits_equal': True,
        'all_other_bodies_identical': True, 'old_named_pool_entries_preserved': True}


def canonical(code, exceptions):
    """Resolve symbolic labels to instruction positions, independent of offsets."""
    lines = [line.strip() for line in code.splitlines() if line.strip()]
    labels, ops = {}, []
    for line in lines:
        if re.fullmatch(r'\w+:',line): labels[line[:-1]] = len(ops)
        else: ops.append(line)
    def normalized(line):
        return re.sub(r'\b(?:ofs[0-9a-f]+|bsui_\w+)\b',lambda m: '@'+str(labels[m[0]]) if m[0] in labels else m[0],line)
    return [normalized(op) for op in ops], [normalized(x) for x in exceptions if x.startswith('try from ')]


def verify_stock_branch(original, result):
    oh, oc, ot = split_body(original)
    rh, rc, rt = split_body(result)
    # The very first guard transfers all normal calls directly to the original.
    entry = re.search(r'^getlocal3\niftrue (\w+)\n',rc)
    if not entry: raise ValueError('Normal-call guard is missing')
    stock = rc.split(entry[1]+':\n',1)[1]
    count = len(re.findall(r'^try from ',ot,re.M))
    if canonical(oc,ot.splitlines()) != canonical(stock,rt.splitlines()[:count]):
        raise ValueError('Normal getStatChange instructions/exception regions changed')
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, required=True)
    parser.add_argument('--java', type=Path, required=True)
    parser.add_argument('--ffdec', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--compile-only', action='store_true')
    parser.add_argument('--freeze', action='store_true',help='Numbered diagnostic from clean committed source')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    source = args.game_root.resolve() / 'win32/app.game-saga1.air.swf'
    out = args.out.resolve()
    if out.exists() or out == args.game_root.resolve() or args.game_root.resolve() in out.parents:
        raise ValueError('Need a new output directory outside the source tree')
    expected = json.loads((root / 'data/baseline.json').read_text())['swf_sha256']
    if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
        raise ValueError('Only the verified original SWF may be used')
    commit = subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    dirty = bool(subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip())
    version = (root/'VERSION').read_text().strip() if args.freeze else 'development-unversioned'
    if args.freeze and (dirty or args.compile_only or version in ('0.1.0-test.1','0.1.0-test.2')):
        raise ValueError('Freeze requires clean committed source and a new VERSION')
    out.mkdir(parents=True)
    args.java, args.ffdec = args.java.resolve(), args.ffdec.resolve()
    export(args.java, args.ffdec, source, out / 'host-as', [DATA])
    host = script(out / 'host-as', DATA, '.as')
    if host.count('public function toString()') != 1:
        raise ValueError('Unexpected donor host class')
    body = (Path(__file__).with_name('ram_probe_body.as.inc')).read_text(encoding='utf-8')
    # Host boilerplate is read locally, never embedded in the repository.
    imports = '\n'.join('   import ' + name + ';' for name in IMPORTS)
    donor = host.replace('{', '{\n' + imports, 1)
    insert = donor.rfind('   }')
    method = '''
      public static function bsuiProbe(param1:IBattleAbilityDef, param2:IBattleEntity,
          param3:StatType, param4:StatChangeData, param5:IBattleEntity,
          param6:IBattleMove) : Boolean
      {
BODY
      }
'''.replace('BODY', body)
    donor = donor[:insert] + method + donor[insert:]
    donor_path = out / 'donor.as'
    donor_path.write_text(donor, encoding='utf-8')
    donor_swf = out / 'DONOR-NOT-FOR-INSTALLATION.swf'
    command(args.java, args.ffdec, '-air', '-replace', source, donor_swf, DATA, donor_path, cwd=out)
    if not donor_swf.exists():
        raise ValueError('Compiler did not produce a donor')
    export(args.java, args.ffdec, donor_swf, out / 'donor-pcode', [DATA], True)
    probe = extract_method(script(out / 'donor-pcode', DATA, '.pcode'), 'public static function bsuiProbe(')
    (out / 'probe.pcode').write_text(probe, encoding='utf-8')
    print(json.dumps({'donor_compiled': True, 'pcode': str(out / 'probe.pcode'),
        'status': 'donor only; never install donor; not a numbered candidate'}))
    if args.compile_only:
        return
    export(args.java, args.ffdec, source, out / 'host-pcode', [ABILITY,MANAGER,OVERLAY], True)
    overlay_text = script(out / 'host-pcode', OVERLAY, '.pcode')
    markers = {'constructor':'public function AbilityDestinationOverlay(',
        'cleanup':'override public function cleanup()',
        'onRender':'override protected function onRender()',
        'checkCanRender':'override protected function checkCanRender()'}
    original = {name:extract_method(overlay_text,marker) for name,marker in markers.items()}
    hover = transform(original)
    call = instructions('getlocal 4', f'getlex {q("BattleAbilityTargetRule","engine.battle.ability.def")}',
        f'getproperty {q("SPECIAL_BATTERING_RAM")}', 'ifne bsui_after_probe',
        f'getlex {q("BattleAbility","engine.battle.ability.model")}',
        'getlocal2',f'getproperty {q("def")}','getlocal3','pushnull',
        f'getlex {q("StatChangeData","engine.battle.ability.model")}', 'construct 0','dup',
        'pushshort -16384', f'setproperty {q("missChance")}', 'getlocal 5','pushnull',
        f'callproperty {q("getStatChange")}, 6', 'pop','bsui_after_probe:')
    hover['onRender'] = once(hover['onRender'], 'ram_hover_ready:\n', 'ram_hover_ready:\n' + call)
    ability_text = script(out / 'host-pcode', ABILITY, '.pcode')
    old_calculation = extract_method(ability_text,'public static function getStatChange(')
    calculation = splice_probe(old_calculation,probe)
    manager_text = script(out / 'host-pcode', MANAGER, '.pcode')
    complete = extract_method(manager_text,'public function onAbilityFinalComplete(')
    ns = 'engine.battle.ability.model:IBattleAbility'
    idle = instructions('getlocal0',f'getproperty {q("_faking")}', 'iftrue bsui_idle_done',
        'getlocal0',f'getproperty {q("numIncompleteAbilities")}', 'iftrue bsui_idle_done',
        'getlocal1', f'getproperty {q("fake",ns,"Namespace")}', 'iftrue bsui_idle_done',
        f'getlex {q("BattleAbility","engine.battle.ability.model")}',
        'getlocal1',f'getproperty {q("def",ns,"Namespace")}',
        'getlocal1',f'getproperty {q("caster",ns,"Namespace")}',
        'pushnull','pushnull','pushnull','pushnull',f'callproperty {q("getStatChange")}, 6',
        'pop','bsui_idle_done:')
    # Capture before INCOMPLETES_EMPTY can advance turns or start an AI action.
    dispatch = instructions(f'findpropstrict {q("dispatchEvent")}',
        f'findpropstrict {q("BattleAbilityEvent","engine.battle.ability.model")}',
        f'getlex {q("BattleAbilityEvent","engine.battle.ability.model")}',
        f'getproperty {q("INCOMPLETES_EMPTY")}')
    complete = once(complete, dispatch,idle+dispatch)
    complete = once(complete, 'maxstack 5\n','maxstack 8\n')
    edits = [(OVERLAY,name,markers[name],text) for name,text in hover.items()]
    edits += [(ABILITY,'getStatChange','public static function getStatChange(',calculation),
        (MANAGER,'onAbilityFinalComplete','public function onAbilityFinalComplete(',complete)]
    index = abcs(source)
    replacements = []
    allowed = set()
    for classname,name,marker,text in edits:
        tag, abc = next((i,a) for i,a in index if classname in a.classes)
        cls = abc.classes[classname]
        method_id = cls['init'] if name == 'constructor' else next(
            t['method'] for t in cls['instance']+cls['static'] if t['name'].split('.')[-1] == name)
        body_id = next(body['index'] for body in abc.bodies if body['method'] == method_id)
        allowed.add((tag,body_id))
        path = out / (name + '.pcode')
        path.write_text(text,encoding='utf-8')
        replacements += [classname,path,body_id]
    payload = out / (f'BannerSagaUI-{version}-RamForecastProbe.swf' if args.freeze else 'RamForecastProbe-DEVELOPMENT-NOT-ACCEPTED.swf')
    command(args.java,args.ffdec,'-replace',source,payload,*replacements,cwd=out)
    report = verify_isolation(source,payload,allowed)
    export(args.java,args.ffdec,payload,out / 'result-pcode',[ABILITY,MANAGER,OVERLAY],True)
    verify_stock_branch(old_calculation,extract_method(script(out / 'result-pcode',ABILITY,'.pcode'),
        'public static function getStatChange('))
    report['normal_getStatChange_instructions_and_exception_regions_equal'] = True
    if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
        raise ValueError('Source changed during build')
    manifest = {'scope':'research-only native armor and Shield Wall projection, diagnostic log only',
        'version':version,'source_commit':commit,'source_dirty':dirty,
        'original_sha256':expected,'payload':payload.name,
        'sha256':hashlib.sha256(payload.read_bytes()).hexdigest(),'isolation':report,
        'status':'structural checks only; NOT installed; AIR/runtime unverified'}
    (out / 'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest))


if __name__ == '__main__':
    main()
