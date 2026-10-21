// SPDX-License-Identifier: MPL-2.0
package bannersagaui.preview {
    import com.stoicstudio.platform.PlatformInput;
    import engine.battle.ability.def.BattleAbilityTargetRule;
    import engine.battle.ability.model.BattleAbility;
    import engine.battle.board.BattleBoardEvent;
    import engine.battle.board.model.BattleBoard;
    import engine.battle.board.model.IBattleEntity;
    import engine.battle.board.view.BattleBoardView;
    import engine.battle.entity.model.BattleEntityEvent;
    import engine.battle.ability.effect.model.PersistedEffectsEvent;
    import engine.battle.fsm.BattleFsmEvent;
    import engine.battle.fsm.BattleFsmConfig;
    import engine.scene.SceneControllerConfig;
    import engine.stat.model.StatEvent;
    import flash.events.Event;
    import flash.events.IEventDispatcher;
    import flash.geom.Point;
    import flash.utils.Dictionary;
    import game.gui.page.ScenePage;

    /** Research integration only. The plain text is an engineering instrument. */
    public final class FieldPreview {
        private static var pages:Dictionary = new Dictionary(true);
        private var page:ScenePage;
        private var board:BattleBoard;
        private var view:BattleBoardView;
        private var session:PreviewSession = new PreviewSession();
        private var layer:PreviewLayer = new PreviewLayer();
        private var subscriptions:Array = [];
        private var rebind:Boolean = true;
        private var last:PreviewFrame;
        private var context:Object = {};
        private var ability:BattleAbility;
        private var target:IBattleEntity;
        private var failed:Boolean = false;

        public function FieldPreview(owner:ScenePage, model:BattleBoard, visual:BattleBoardView) {
            page = owner; board = model; view = visual;
            page.addChild(layer);
        }

        public static function updatePage(page:ScenePage):void {
            var existing:FieldPreview = pages[page];
            var model:BattleBoard = page.scene ? page.scene.focusedBoard : null;
            var visual:BattleBoardView = page.view && page.view.boards ? page.view.boards.focusedBoardView : null;
            if (!model || !visual || !model.enabled) {
                cleanupPage(page);
                return;
            }
            if (existing && existing.board !== model) {
                cleanupPage(page); existing = null;
            }
            if (!existing) {
                existing = new FieldPreview(page, model, visual);
                pages[page] = existing;
            }
            try { existing.update(); }
            catch (failure:*) {
                existing.failed = true;
                existing.layer.clear();
                existing.board.logger.error("BSUI_FIELD_DISABLED " + String(failure));
            }
        }

        public static function cleanupPage(page:ScenePage):void {
            var existing:FieldPreview = pages[page];
            if (existing) existing.dispose();
            delete pages[page];
        }

        private function watch(owner:IEventDispatcher, type:String, topology:Boolean = false):void {
            owner.addEventListener(type, topology ? onTopology : onDirty);
            subscriptions.push({owner:owner, type:type, topology:topology});
        }
        private function unwatch():void {
            for each (var sub:Object in subscriptions)
                sub.owner.removeEventListener(sub.type, sub.topology ? onTopology : onDirty);
            subscriptions = [];
        }
        private function onDirty(event:Event):void {
            session.invalidate(); layer.clear(); last = null;
        }
        private function onTopology(event:Event):void {
            rebind = true; onDirty(event);
        }
        private function bind():void {
            unwatch(); rebind = false;
            watch(board, BattleBoardEvent.HOVER_TILE);
            watch(board, BattleBoardEvent.BOARD_TILE_CONFIGURATION);
            watch(board, BattleEntityEvent.ADDED, true);
            watch(board, BattleEntityEvent.REMOVED, true);
            for each (var type:String in [BattleFsmEvent.TURN, BattleFsmEvent.TURN_ABILITY,
                BattleFsmEvent.TURN_ABILITY_TARGETS, BattleFsmEvent.TURN_COMMITTED,
                BattleFsmEvent.TURN_COMPLETE, BattleFsmEvent.DEPLOY, BattleFsmEvent.INTERACT])
                watch(board.fsm, type);
            watch(BattleFsmConfig.dispatcher, BattleFsmConfig.EVENT_GUI_VISIBLE);
            watch(BattleFsmConfig.dispatcher, BattleFsmConfig.EVENT_GUI_HUD_ENABLE);
            for each (var entity:IBattleEntity in board.entities) {
                watch(entity, BattleEntityEvent.MOVED);
                watch(entity, BattleEntityEvent.VISIBLE);
                watch(entity, BattleEntityEvent.ENABLED);
                watch(entity, BattleEntityEvent.ACTIVE);
                watch(entity, BattleEntityEvent.ALIVE);
                watch(entity.effects, PersistedEffectsEvent.CHANGED, true);
                for (var i:int = 0; i < entity.stats.numStats; i++)
                    watch(entity.stats.getStatByIndex(i), StatEvent.CHANGE);
            }
        }

        private function calculate():Object {
            var result:Object = RamPreviewProvider.calculate(ability.def, ability.caster, target);
            // Research evidence only; not the data transport to the renderer.
            board.logger.info("BSUI_FIELD_RESULT " + JSON.stringify(result));
            return result;
        }
        private function locate(id:String):Point {
            var entity:IBattleEntity = board.getEntity(id);
            if (!entity || !entity.enabled || !entity.active || !entity.visibleToPlayer) return null;
            var entityView:Object = view.getEntityView(entity);
            if (!entityView) return null;
            var point:Point = new Point();
            entityView.getBattleInfoFlagPosition(point);
            point.y -= 26; // Neutral test offset; not an adopted layout.
            return point;
        }
        private function update():void {
            if (failed) return;
            if (rebind) bind();
            var turn:Object = board.fsm.turn;
            ability = turn ? turn.ability as BattleAbility : null;
            target = null;
            if (ability && ability.def.targetRule == BattleAbilityTargetRule.SPECIAL_BATTERING_RAM) {
                if (ability.targetSet.targets.length) target = ability.targetSet.targets[0];
                else if (!PlatformInput.lastInputGp && !SceneControllerConfig.instance.restrictInput)
                    target = board.hoverEntity;
            }
            context.valid = Boolean(view.layerSprite && BattleFsmConfig.guiHudShouldRender &&
                turn && !turn.committed && ability && ability.caster.playerControlled && target != null);
            context.board = board; context.turn = turn; context.ability = ability;
            context.casterId = ability ? ability.caster.id : null;
            context.targetId = target ? target.id : null;
            context.level = ability ? ability.def.level : 0;
            var frame:PreviewFrame = session.refresh(context, calculate);
            if (view.layerSprite) {
                var scale:Number = board.scene.camera.scale;
                layer.x = page.width / 2 + (view.layerSprite.x + board.def.pos.x) * scale;
                layer.y = page.height / 2 + (view.layerSprite.y + board.def.pos.y) * scale;
            }
            if (frame !== last) {
                layer.show(frame, locate); last = frame;
            } else if (frame) layer.updatePositions(locate);
        }
        private function dispose():void {
            unwatch(); session.dispose(); layer.clear();
            if (layer.parent) layer.parent.removeChild(layer);
            last = null; target = null; ability = null;
            page = null; view = null; board = null;
        }
    }
}
