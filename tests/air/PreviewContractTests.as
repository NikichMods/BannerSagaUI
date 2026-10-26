// SPDX-License-Identifier: MPL-2.0
package bannersagaui.tests {
    import bannersagaui.preview.PreviewFrame;
    import bannersagaui.preview.PreviewSession;
    import bannersagaui.preview.PreviewLayer;
    import bannersagaui.preview.NeedleObservationMatch;
    import flash.desktop.NativeApplication;
    import flash.display.Sprite;
    import flash.geom.Point;
    import flash.filesystem.File;
    import flash.filesystem.FileMode;
    import flash.filesystem.FileStream;
    import flash.text.TextField;

    /** Standalone AIR checks; no game startup, combat simulation or user input. */
    public final class PreviewContractTests extends Sprite {
        private var passed:Array = [];
        public function PreviewContractTests() {
            var report:Object = {status:"failed", passed:passed};
            try {
                run();
                report.status = "passed";
            } catch (failure:*) {
                report.error = String(failure);
                report.stack = failure is Error ? Error(failure).getStackTrace() : "";
            }
            var stream:FileStream = new FileStream();
            stream.open(File.applicationStorageDirectory.resolvePath("results.json"), FileMode.WRITE);
            stream.writeUTFBytes(JSON.stringify(report));
            stream.close();
            NativeApplication.nativeApplication.exit(report.status == "passed" ? 0 : 1);
        }

        private function check(value:Boolean, name:String):void {
            if (!value) throw new Error(name);
            passed.push(name);
        }
        private function row(id:String = "target"):Object {
            return {id:id, armorBefore:9, strengthBefore:8, armor:7, strength:8,
                beforeX:4, beforeY:12, x:0, y:12, auraBefore:0, auraAfter:0};
        }
        private function result(rows:Array = null):Object {
            return {status:"ready", restored:true, cacheRestored:true,
                caster:"caster", target:"target", level:1, rows:rows || [row()]};
        }
        private function context():Object {
            return {valid:true, board:{}, turn:{}, ability:{}, casterId:"caster", targetId:"target", level:1};
        }

        private function observationCandidate(request:Object):Object {
            return {instance:{}, board:request.board, turn:request.turn, caster:"archer",
                ability:"needle", level:1, fake:false, casterState:"caster-original-state",
                rows:[{id:"A", state:"A-original-state"}, {id:"B", state:"B-original-state"}]};
        }
        private function observationChecks():void {
            var request:Object = {instance:{}, board:{}, turn:{}, caster:"archer", ability:"needle",
                level:1, casterState:"caster-original-state",
                rows:[{id:"A", state:"A-original-state"}, {id:"B", state:"B-original-state"}]};
            var candidate:Object = observationCandidate(request);
            check(candidate.instance !== request.instance && NeedleObservationMatch.reason(request,candidate) == "",
                "different execution object can match same request");
            candidate.fake = true;
            check(NeedleObservationMatch.reason(request,candidate) == "fake", "popup fake cannot bind");
            candidate = observationCandidate(request); candidate.board = {};
            check(NeedleObservationMatch.reason(request,candidate) == "context", "foreign board cannot bind");
            candidate = observationCandidate(request); candidate.turn = {};
            check(NeedleObservationMatch.reason(request,candidate) == "context", "later turn cannot bind");
            candidate = observationCandidate(request); candidate.caster = "other";
            check(NeedleObservationMatch.reason(request,candidate) == "caster", "other caster cannot bind");
            candidate = observationCandidate(request); candidate.ability = "other";
            check(NeedleObservationMatch.reason(request,candidate) == "ability", "other ability cannot bind");
            candidate = observationCandidate(request); candidate.level = 2;
            check(NeedleObservationMatch.reason(request,candidate) == "rank", "changed rank cannot bind");
            candidate = observationCandidate(request); candidate.casterState = "changed";
            check(NeedleObservationMatch.reason(request,candidate) == "caster-state", "changed caster cannot bind");
            candidate = observationCandidate(request); candidate.rows.pop();
            check(NeedleObservationMatch.reason(request,candidate) == "target-count", "partial line cannot bind");
            candidate = observationCandidate(request); candidate.rows.reverse();
            check(NeedleObservationMatch.reason(request,candidate) == "target-order", "reordered line cannot bind");
            candidate = observationCandidate(request); candidate.rows[1].state = "changed";
            check(NeedleObservationMatch.reason(request,candidate) == "target-state", "changed target cannot bind");
        }
        private function run():void {
            var protectedRow:Object = row("protected"); protectedRow.armor = protectedRow.armorBefore;
            var line:Object = result([protectedRow, row()]); line.allTargets = true;
            check(PreviewFrame.fromResult(line, "target").rows.length == 2,
                "explicit affected set keeps a protected intermediate target");
            delete line.allTargets;
            check(PreviewFrame.fromResult(line, "target").rows.length == 1,
                "ordinary neighbour filtering remains unchanged");
            observationChecks();
            var unchanged:Object = row("unchanged"); unchanged.armorBefore = unchanged.armor;
            var aura:Object = row("aura"); aura.armorBefore = aura.armor; aura.auraAfter = 1;
            var input:Object = result([row(), unchanged, aura]);
            var frame:PreviewFrame = PreviewFrame.fromResult(input, "target");
            check(frame != null && frame.rows.length == 2, "target and changed aura neighbour only");
            input.rows[0].armor = 999;
            var exposed:Array = frame.rows; exposed[0].armor = 888;
            check(frame.rows[0].armor == 7, "provider and consumer mutation cannot alter snapshot");
            var owned:Object = row(); var constructed:PreviewFrame = new PreviewFrame("target", [owned]);
            owned.armor = 999;
            check(constructed.rows[0].armor == 7, "public AS3 constructor also detaches rows");
            var zero:Object = row(); zero.armorBefore = zero.armor = 0;
            check(PreviewFrame.fromResult(result([zero]), "target").rows.length == 1, "zero damage target remains visible");
            var negative:Object = row(); negative.strengthBefore = negative.strength = -2;
            check(PreviewFrame.fromResult(result([negative]), "target").rows[0].strength == -2, "native negative strength is not silently clamped");
            check(PreviewFrame.fromResult(result([row(), row()]), "target") == null, "duplicate ids rejected atomically");
            check(PreviewFrame.fromResult(result([row("other")]), "target") == null, "missing primary target rejected");
            var invalid:Object = row(); invalid.armor = NaN;
            check(PreviewFrame.fromResult(result([row(), invalid]), "target") == null, "nonfinite row rejects entire result");
            invalid = row(); invalid.x = 1.5;
            check(PreviewFrame.fromResult(result([invalid]), "target") == null, "fractional integer field rejected");
            var failed:Object = result(); failed.restored = false;
            check(PreviewFrame.fromResult(failed, "target") == null, "failed real restoration never renders");
            failed = result(); failed.cacheRestored = false;
            check(PreviewFrame.fromResult(failed, "target") == null, "failed cache restoration never renders");

            var session:PreviewSession = new PreviewSession();
            var ctx:Object = context(); var calls:int = 0;
            var calculate:Function = function():Object { calls++; return result(); };
            frame = session.refresh(ctx, calculate);
            check(session.refresh(ctx, calculate) === frame && calls == 1, "unchanged context does not recalculate");
            session.invalidate();
            check(session.frame == null, "invalidation clears stale frame immediately");
            session.refresh(ctx, calculate);
            check(calls == 2, "one calculation after explicit invalidation");
            session.invalidate();
            check(session.refresh(ctx, function():Object { session.invalidate(); return result(); }) == null,
                "invalidation during calculation prevents publication");
            session.refresh(ctx, calculate);
            ctx.ability = {};
            check(session.refresh(ctx, function():Object { return {status:"unsupported", restored:true, cacheRestored:false, rows:[]}; }) == null && !session.failed,
                "unsupported clears numbers without tripping breaker");
            ctx.ability = {};
            check(session.refresh(ctx, function():Object { return {status:"error", restored:true}; }) == null && session.failed,
                "provider error disables current board");
            session.clear();
            ctx.ability = {};
            check(session.refresh(ctx, calculate) == null && session.failed, "cancel does not reset board breaker");
            ctx = context();
            check(session.refresh(ctx, calculate) != null && !session.failed, "different board starts fresh session");
            ctx.valid = false;
            check(session.refresh(ctx, calculate) == null && session.frame == null, "invalid command clears immediately");
            ctx.valid = true;
            session.refresh(ctx, calculate); session.invalidate();
            check(session.refresh(ctx, function():Object { throw new Error("synthetic provider failure"); }) == null && session.failed,
                "thrown provider failure contained");
            session.dispose();
            check(session.frame == null, "dispose releases current frame");
            session = new PreviewSession(); ctx = context();
            check(session.refresh(ctx, function():Object {
                var wrong:Object = result(); wrong.caster = "other"; return wrong;
            }) == null && session.failed, "result identity cannot cross requests");

            var layer:PreviewLayer = new PreviewLayer();
            var offset:Number = 0;
            var locate:Function = function(id:String):Point { return new Point(10 + offset, 20); };
            layer.show(PreviewFrame.fromResult(result(), "target"), locate);
            check(layer.numChildren == 1 && layer.visible && !layer.mouseEnabled && !layer.mouseChildren,
                "passive layer creates exactly one primary label");
            var label:TextField = layer.getChildAt(0) as TextField;
            check(label && label.text == "ARM 7  STR 8" && label.x == 10 && label.y == 20 && !label.selectable,
                "technical text uses final numbers at supplied anchor");
            offset = 50; var oldCalls:int = calls; layer.updatePositions(locate);
            check(label.x == 60 && calls == oldCalls, "camera anchor movement does not invoke calculator");
            layer.updatePositions(function(id:String):Point { return null; });
            check(!label.visible && !layer.visible, "missing visible anchor hides its label");
            layer.show(null, locate);
            check(layer.numChildren == 0 && !layer.visible, "null result removes previous display");
        }
    }
}
