// SPDX-License-Identifier: MPL-2.0
package bannersagaui.preview {
    /** One synchronous preview owner. The host adapter supplies invalidations. */
    public final class PreviewSession {
        private var board:Object;
        private var turn:Object;
        private var ability:Object;
        private var target:String;
        private var actor:String;
        private var level:int;
        private var revision:uint;
        private var dirty:Boolean = true;
        private var calculating:Boolean = false;
        private var disabled:Boolean = false;
        private var current:PreviewFrame;

        public function invalidate():void {
            revision++;
            dirty = true;
            current = null;
        }

        public function clear():void {
            invalidate();
            // Keep board identity so cancel/reselect cannot reset its breaker.
            turn = ability = null;
            actor = target = null;
        }

        public function dispose():void {
            clear();
            board = null;
            disabled = false;
        }

        public function refresh(context:Object, calculate:Function):PreviewFrame {
            if (!context || context.valid !== true || !context.board || !context.turn ||
                !context.ability || !context.targetId || !context.casterId || context.level < 1) {
                clear();
                return null;
            }
            if (board !== context.board) {
                clear();
                board = context.board;
                disabled = false;
            }
            if (turn !== context.turn || ability !== context.ability ||
                target != context.targetId || actor != context.casterId || level != context.level) {
                invalidate();
                turn = context.turn;
                ability = context.ability;
                target = context.targetId;
                actor = context.casterId;
                level = context.level;
            }
            if (disabled || calculating || !dirty) return current;
            dirty = false;
            calculating = true;
            var requested:uint = revision;
            try {
                var result:Object = calculate();
                if (result && (result.status == "error" || result.restored !== true ||
                    (result.status == "ready" && result.cacheRestored !== true))) {
                    disabled = true;
                }
                if (result && result.status == "ready" &&
                    (result.caster != actor || result.target != target || result.level != level)) {
                    disabled = true;
                }
                // A synchronous provider can dispatch events. Never publish a
                // result invalidated during that call, or after a failed restore.
                if (!disabled && revision == requested) {
                    current = PreviewFrame.fromResult(result, target);
                    if (result && result.status == "ready" && !current) disabled = true;
                }
            } catch (failure:*) {
                disabled = true;
                current = null;
            }
            calculating = false;
            if (disabled) current = null;
            return current;
        }

        public function get frame():PreviewFrame { return current; }
        public function get failed():Boolean { return disabled; }
    }
}
