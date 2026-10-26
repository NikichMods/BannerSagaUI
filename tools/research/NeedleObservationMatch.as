// SPDX-License-Identifier: MPL-2.0
package bannersagaui.preview {
    /** Research-only request/execution correlation; no battle calculation. */
    public final class NeedleObservationMatch {
        public static function reason(request:Object, candidate:Object):String {
            if (!request || !candidate || !request.rows || !candidate.rows) return "missing";
            if (candidate.fake !== false) return "fake";
            if (!request.board || !request.turn || candidate.board !== request.board ||
                candidate.turn !== request.turn) return "context";
            if (!request.caster || candidate.caster != request.caster) return "caster";
            if (!request.ability || candidate.ability != request.ability) return "ability";
            if (request.level < 1 || candidate.level != request.level) return "rank";
            if (!request.casterState || candidate.casterState != request.casterState) return "caster-state";
            if (request.rows.length == 0 || candidate.rows.length != request.rows.length) return "target-count";
            for (var i:int = 0; i < request.rows.length; i++) {
                if (candidate.rows[i].id != request.rows[i].id) return "target-order";
                if (!request.rows[i].state || candidate.rows[i].state != request.rows[i].state)
                    return "target-state";
            }
            return "";
        }
    }
}
