// SPDX-License-Identifier: MPL-2.0
package bannersagaui.preview {
    /** Detached, validated presentation data. No host Stats/Effect references. */
    public final class PreviewFrame {
        private var values:Array;
        private var target:String;

        public function PreviewFrame(primary:String, rows:Array) {
            target = primary;
            values = [];
            for each (var row:Object in rows) values.push(copy(row));
        }

        public function get targetId():String { return target; }

        public static function changeText(before:int, after:int):String {
            var change:int = after - before;
            return change > 0 ? "+" + change : String(change);
        }

        public static function fromResult(result:Object, target:String):PreviewFrame {
            if (!result || result.status != "ready" || result.restored !== true ||
                result.cacheRestored !== true || !target || !(result.rows is Array)) return null;
            var seen:Object = {};
            var rows:Array = [];
            var found:Boolean = false;
            for each (var row:Object in result.rows) {
                if (!row || !(row.id is String) || row.id.length == 0 ||
                    seen["id:" + row.id]) return null;
                seen["id:" + row.id] = true;
                for each (var field:String in ["armorBefore", "strengthBefore", "armor", "strength",
                    "beforeX", "beforeY", "x", "y", "auraBefore", "auraAfter"]) {
                    if (typeof row[field] != "number" || !isFinite(row[field]) ||
                        row[field] != int(row[field])) return null;
                }
                if (row.auraBefore < 0 || row.auraAfter < 0) return null;
                if (row.id == target) found = true;
                // Always include the primary target, including zero-damage or
                // damage compensated by a new aura. Neighbours need a change.
                if (result.allTargets === true || row.id == target || row.armorBefore != row.armor ||
                    row.strengthBefore != row.strength || row.auraBefore != row.auraAfter) {
                    rows.push(copy(row));
                }
            }
            if (!found) return null;
            return new PreviewFrame(target, rows);
        }

        private static function copy(row:Object):Object {
            return {id:row.id, armorBefore:row.armorBefore, strengthBefore:row.strengthBefore,
                armor:row.armor, strength:row.strength, beforeX:row.beforeX, beforeY:row.beforeY,
                x:row.x, y:row.y, auraBefore:row.auraBefore, auraAfter:row.auraAfter};
        }

        public function get rows():Array {
            var detached:Array = [];
            for each (var row:Object in values) detached.push(copy(row));
            return detached;
        }
    }
}
