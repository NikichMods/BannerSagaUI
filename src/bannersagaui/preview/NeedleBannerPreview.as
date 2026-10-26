// SPDX-License-Identifier: MPL-2.0
package bannersagaui.preview {
    import engine.battle.board.model.BattleBoard;
    import engine.battle.board.model.IBattleEntity;
    import engine.battle.entity.model.BattleEntityEvent;
    import engine.gui.IGuiBattleInfoFlag;
    import flash.display.MovieClip;
    import flash.display.Sprite;
    import flash.filters.GlowFilter;
    import flash.geom.Rectangle;
    import flash.text.TextField;
    import flash.text.TextFormat;
    import flash.utils.Dictionary;
    import game.gui.page.ScenePage;

    /** Research UI: native flags retain their own stats, layout and transforms. */
    public final class NeedleBannerPreview {
        private static var policies:Dictionary = new Dictionary(true);
        private var page:ScenePage;
        private var board:BattleBoard;
        private var frame:PreviewFrame;
        private var labels:Array = [];

        public function NeedleBannerPreview(owner:ScenePage, model:BattleBoard) {
            page = owner; board = model;
        }

        /** Called only at the native visibility-request operand. */
        public static function requested(entity:IBattleEntity, nativeRequest:Boolean):Boolean {
            var selected:Object = policies[entity.board];
            return selected ? selected["id:" + entity.id] === true : nativeRequest;
        }

        public static function result(prediction:Object, model:BattleBoard):Object {
            var rows:Array = [];
            if (prediction.status == "ready") {
                for each (var row:Object in prediction.rows) {
                    var entity:IBattleEntity = model.getEntity(row.id);
                    rows.push({id:row.id, armorBefore:row.armorBefore,
                        strengthBefore:row.strengthBefore, armor:row.armorAfter,
                        strength:row.strengthAfter, beforeX:entity.x, beforeY:entity.y, x:entity.x, y:entity.y,
                        auraBefore:0, auraAfter:0});
                }
            }
            return {status:prediction.status, restored:prediction.restored,
                cacheRestored:prediction.cacheRestored, caster:prediction.caster,
                target:prediction.target, level:prediction.level, allTargets:true, rows:rows};
        }

        private function refreshFlags():void {
            for each (var entity:IBattleEntity in board.entities)
                board.dispatchEvent(new BattleEntityEvent(BattleEntityEvent.BATTLE_INFO_FLAG_VISIBLE, entity));
        }

        private function removeLabels():void {
            for each (var label:Object in labels)
                if (label.sprite.parent) label.sprite.parent.removeChild(label.sprite);
            labels = [];
        }

        public function show(value:PreviewFrame):void {
            if (frame !== value) {
                removeLabels(); frame = value;
                if (frame) {
                    var selected:Object = {};
                    for each (var row:Object in frame.rows) selected["id:" + row.id] = true;
                    policies[board] = selected;
                } else delete policies[board];
                refreshFlags();
                board.logger.info("BSUI_NEEDLE_BANNERS " + (frame ? "show count=" + frame.rows.length : "clear"));
            }
            if (!frame || !page.battleInfoFlags) return;
            // Native flags may be replaced (e.g. a changed flag class). Bind the
            // current instance; no independent entity-to-screen projection.
            for each (var flag:IGuiBattleInfoFlag in page.battleInfoFlags.flags) {
                var match:Object = null;
                for each (row in frame.rows) if (row.id == flag.entityId) { match = row; break; }
                if (!match) continue;
                var clip:MovieClip = flag.movieClip;
                var known:Boolean = false;
                for each (var prior:Object in labels) if (prior.clip === clip) { known = true; break; }
                if (known) continue;
                var armor:MovieClip = clip.getChildByName("arm_text") as MovieClip;
                var strength:MovieClip = clip.getChildByName("str_text") as MovieClip;
                if (!armor || !strength || !(armor["textField"] is TextField) ||
                    !(strength["textField"] is TextField))
                    throw new Error("Native stat text fields unavailable");
                var sprite:Sprite = new Sprite();
                sprite.mouseEnabled = sprite.mouseChildren = false;
                sprite.name = "bsui_needle_delta";
                addDelta(sprite, clip, armor["textField"] as TextField,
                    match.armorBefore - match.armor, 0x8FD2FF);
                addDelta(sprite, clip, strength["textField"] as TextField,
                    match.strengthBefore - match.strength, 0xFFA591);
                clip.addChild(sprite);
                labels.push({clip:clip, sprite:sprite});
                board.logger.info("BSUI_NEEDLE_LABEL " + JSON.stringify({id:match.id,
                    parent:clip.name, armorLoss:match.armorBefore-match.armor,
                    strengthLoss:match.strengthBefore-match.strength,
                    armorX:sprite.getChildAt(0).x, strengthX:sprite.getChildAt(1).x,
                    y:sprite.getChildAt(0).y}));
            }
        }

        private function addDelta(parent:Sprite, clip:MovieClip, current:TextField,
            loss:int, color:uint):void {
            var bounds:Rectangle = current.getBounds(clip);
            var format:TextFormat = current.getTextFormat();
            format.size = Number(format.size) + 2;
            format.color = color; format.align = "center";
            var text:TextField = new TextField();
            text.mouseEnabled = false; text.selectable = false;
            text.embedFonts = current.embedFonts;
            text.antiAliasType = current.antiAliasType;
            text.defaultTextFormat = format;
            // Keep the half-banner's actual centre, including unequal field widths.
            text.width = bounds.width + 10; text.height = Number(format.size) + 8;
            text.x = bounds.x + (bounds.width - text.width) / 2;
            text.y = bounds.bottom - 2;
            text.filters = [new GlowFilter(0x000000, 1, 2, 2, 4)];
            text.text = loss == 0 ? "0" : "-" + loss;
            parent.addChild(text);
        }

        public function dispose():void {
            removeLabels();
            if (policies[board]) { delete policies[board]; refreshFlags(); }
            frame = null; page = null; board = null;
        }
    }
}
