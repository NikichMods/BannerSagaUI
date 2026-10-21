# SPDX-License-Identifier: MPL-2.0
"""Generate a direct provider from the one original, verified research kernel.

Only the invocation/result boundary and additional scalar output are changed.
There is no embedded host source, new combat formula or real movement here.
"""
from pathlib import Path

from build_ram_probe import IMPORTS

ROW_EXTENSION = ('\n            strengthBefore:probeSnapshot.stats.getValue(StatType.STRENGTH),'
                 '\n            beforeX:probeSnapshot.x, beforeY:probeSnapshot.y,')
KERNEL_START = 'try\n{\n    if(param1.id'
KERNEL_END = 'if(probeCleanupFailed) probeError += " cleanup=" + String(probeCleanupFailureValue);'


def kernel(text):
    start = text.index(KERNEL_START)
    end = text.index(KERNEL_END, start) + len(KERNEL_END)
    return text[start:end]


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Unexpected provider boundary: ' + old[:60])
    return text.replace(old, new, 1)


def provider_source(root):
    body = (Path(root) / 'tools/research/ram_probe_body.as.inc').read_text(encoding='utf-8')
    original_kernel = kernel(body)
    body = once(body, 'if(!param2 || !param2.board) return false;',
        'var started:int = getTimer();\n'
        'if(!param1 || !param2 || !param2.board) return {status:"unsupported", '
        'restored:true, cacheRestored:false, rows:[]};')
    start = body.index('// Research-only board-local circuit breaker.')
    end = body.index('var probeManager:', start)
    body = body[:start] + body[end:]
    start = body.index('// Snapshot actual results only')
    end = body.index(KERNEL_START, start)
    body = body[:start] + body[end:]
    body = once(body, 'armorBefore:probeSnapshot.stats.getValue(StatType.ARMOR),',
        'armorBefore:probeSnapshot.stats.getValue(StatType.ARMOR),' + ROW_EXTENSION)
    if kernel(body).replace(ROW_EXTENSION, '', 1) != original_kernel:
        raise ValueError('Calculation/cleanup changed while adapting provider boundary')
    start = body.index('probeBoard.logger.info("BSUI_RAM_PROBE "')
    body = body[:start] + '''
var outputStatus:String = !probeStable || probeStatus == "ERROR" ? "error" :
    (probeStatus == "UNSUPPORTED" ? "unsupported" : "ready");
return {status:outputStatus, reason:probeError, restored:probeStable,
    cacheRestored:probeCacheRestored, elapsedMs:getTimer()-started,
    caster:param2.id, target:param5 ? param5.id : null, level:param1.level,
    damageApplications:probeDamages, rows:outputStatus == "ready" ? probeRows : []};
'''
    if 'BSUI_RAM_' in body or 'param4' in body or 'return false' in body:
        raise ValueError('Diagnostic protocol leaked into direct provider')
    imports = '\n'.join('import ' + name + ';' for name in IMPORTS)
    return '''// Generated from original project-owned research source; not host code.
package bannersagaui.preview {
IMPORTS
import flash.utils.getTimer;
public final class RamPreviewProvider {
    public static function calculate(param1:IBattleAbilityDef,
        param2:IBattleEntity, param5:IBattleEntity):Object {
BODY
    }
}
}
'''.replace('IMPORTS', imports).replace('BODY', body)


def needle_controller_source(source):
    """Optional research-only query. Keep default sources/Ram output unchanged.

    Selected targets only; no click/hover reconstruction, new graphic, or use
    of loss values as PreviewFrame final stats. Log output is evidence only.
    """
    source = once(source, 'import engine.battle.ability.model.BattleAbility;',
        'import engine.battle.ability.model.BattleAbility;\n'
        '    import engine.battle.ability.model.BattleAbilityEvent;\n'
        '    import engine.battle.ability.effect.model.Effect;\n'
        '    import engine.battle.ability.effect.model.EffectTag;\n'
        '    import engine.stat.def.StatType;')
    source = once(source, 'private var failed:Boolean = false;',
        'private var failed:Boolean = false;\n'
        '        private var needleAction:BattleAbility;\n'
        '        private var needleResult:Object;')
    source = once(source, 'var result:Object = RamPreviewProvider.calculate(ability.def, ability.caster, target);',
        '''if (ability.def.id == "abl_threadtheneedle") {
                var needle:Object = NeedlePreviewProbe.calculate(ability);
                board.logger.info("BSUI_NEEDLE_QUERY " + JSON.stringify(needle));
                clearNeedleObservation();
                if (needle.status == "ready") {
                    needleAction = ability; needleResult = needle;
                    needleAction.addEventListener(BattleAbilityEvent.ABILITY_AND_CHILDREN_COMPLETE, needleCompleted);
                }
                return {status:needle.status == "error" ? "error" : "unsupported",
                    reason:"needle-query-log-only", restored:needle.restored,
                    cacheRestored:needle.cacheRestored, rows:[]};
            }
            var result:Object = RamPreviewProvider.calculate(ability.def, ability.caster, target);''')
    source = once(source,
        'if (ability && ability.def.targetRule == BattleAbilityTargetRule.SPECIAL_BATTERING_RAM) {',
        '''if (ability && ability.def.id == "abl_threadtheneedle" && ability.targetSet.targets.length) {
                target = ability.targetSet.targets[ability.targetSet.targets.length-1];
            } else if (ability && ability.def.targetRule == BattleAbilityTargetRule.SPECIAL_BATTERING_RAM) {''')
    source = once(source, 'private function onDirty(event:Event):void {',
        '''private function onDirty(event:Event):void {
            // A selected-only Needle query is independent of pointer position.
            if (event.type == BattleBoardEvent.HOVER_TILE && ability &&
                ability.def.id == "abl_threadtheneedle" && ability.targetSet.targets.length) return;''')
    source = once(source, 'private function dispose():void {', '''
        private function clearNeedleObservation():void {
            if (needleAction) needleAction.removeEventListener(
                BattleAbilityEvent.ABILITY_AND_CHILDREN_COMPLETE, needleCompleted);
            needleAction = null; needleResult = null;
        }
        private function needleCompleted(event:BattleAbilityEvent):void {
            if (!needleAction || event.ability !== needleAction) return;
            var action:BattleAbility = needleAction;
            var prediction:Object = needleResult;
            clearNeedleObservation();
            if (board.fake || action.fake || !action.executed) return;
            try {
                var actual:Array = [];
                var matches:Boolean = action.def.level == prediction.level &&
                    action.targetSet.targets.length == prediction.rows.length;
                var resistanceMatches:Boolean = true;
                var index:int = 0;
                for each (var row:Object in prediction.rows) {
                    var entity:IBattleEntity = board.getEntity(row.id);
                    if (!entity || entity.stats == null) throw new Error("Missing actual target");
                    var armor:int = entity.stats.getValue(StatType.ARMOR);
                    var strength:int = entity.stats.getValue(StatType.STRENGTH);
                    if (armor != row.armorAfter || strength != row.strengthAfter ||
                        index >= action.targetSet.targets.length ||
                        action.targetSet.targets[index].id != row.id) matches = false;
                    var resistedArmor:Boolean = false;
                    var resistedStrength:Boolean = false;
                    for each (var nativeEffect:Effect in action.effects) {
                        if (nativeEffect.target && nativeEffect.target.id == row.id) {
                            resistedArmor = resistedArmor || nativeEffect.hasTag(EffectTag.RESISTING_ARMOR);
                            resistedStrength = resistedStrength || nativeEffect.hasTag(EffectTag.RESISTING_STRENGTH);
                        }
                    }
                    if (resistedArmor != row.resistedArmor || resistedStrength != row.resistedStrength)
                        resistanceMatches = false;
                    actual.push({id:row.id, armor:armor, strength:strength,
                        armorLoss:row.armorBefore-armor, strengthLoss:row.strengthBefore-strength,
                        resistedArmor:resistedArmor, resistedStrength:resistedStrength});
                    index++;
                }
                board.logger.info("BSUI_NEEDLE_ACTUAL " + JSON.stringify({
                    status:matches && resistanceMatches ? "MATCH" : "MISMATCH",
                    statsMatch:matches, resistanceMatch:resistanceMatches, caster:action.caster.id,
                    level:action.def.level, rows:actual, prediction:prediction.rows}));
            } catch (failure:*) {
                board.logger.error("BSUI_NEEDLE_ACTUAL_ERROR " + String(failure));
            }
        }
        private function dispose():void {
            clearNeedleObservation();''')
    return source
