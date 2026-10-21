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
