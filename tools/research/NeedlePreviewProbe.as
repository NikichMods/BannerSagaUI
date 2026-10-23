// SPDX-License-Identifier: MPL-2.0
package bannersagaui.preview {
    import engine.battle.ability.def.BattleAbilityDef;
    import engine.battle.ability.effect.def.AbilityReason;
    import engine.battle.ability.effect.def.IEffectDef;
    import engine.battle.ability.effect.model.Effect;
    import engine.battle.ability.effect.model.EffectResult;
    import engine.battle.ability.effect.model.EffectTag;
    import engine.battle.ability.effect.op.model.Op;
    import engine.battle.ability.effect.op.model.Op_DamageStr;
    import engine.battle.ability.effect.op.model.Op_ChangeStat;
    import engine.battle.ability.model.BattleAbility;
    import engine.battle.ability.model.BattleAbilityManager;
    import engine.battle.ability.model.BattleAbilityValidation;
    import engine.battle.board.model.IBattleBoard;
    import engine.battle.board.model.IBattleEntity;
    import engine.stat.def.StatType;
    import engine.stat.model.Stats;
    import flash.utils.Dictionary;
    import flash.utils.getTimer;

    /** Research only: selected native targetSet, no input, movement or live execution.
     * No renderer contract and no promise of release coverage. The caller must
     * stop querying this battle on error/restored=false, as PreviewSession does.
     */
    public final class NeedlePreviewProbe {
        private static const ALLOWED:String = "|pas_puncture|pas_light_step|pas_shieldwall|" +
            "abl_shieldwall_bonus|abl_shieldwall_bonus_self|abl_stonewall|pas_returnthefavor|pas_heavyimpact|";

        private static function sameStats(a:Stats, b:Stats, board:IBattleBoard):Boolean {
            if (!a.testEquals(b, board.logger) || a.numStats != b.numStats) return false;
            for (var i:int = 0; i < a.numStats; i++)
                if (a.getStatByIndex(i).getDebugStringMods("") !=
                    b.getStatByIndex(i).getDebugStringMods("")) return false;
            return true;
        }

        private static function resetFake(snapshot:Object, board:IBattleBoard):void {
            var entity:IBattleEntity = snapshot.entity;
            if (!entity.fake || entity.stats === snapshot.real)
                throw new Error("Expected detached fake stats");
            // Same fresh-container route verified for the Ram research kernel.
            entity.stats.synchronizeFrom(new Stats(entity, false));
            entity.stats.synchronizeFrom(snapshot.stats);
            if (!sameStats(entity.stats, snapshot.stats, board))
                throw new Error("Fake modifier copy differs");
        }

        private static function rejectStats(entity:IBattleEntity):void {
            // These native paths are omitted/different in fake. Research guard,
            // not an adopted restriction of the eventual product.
            for each (var type:StatType in [StatType.KILL_STOP, StatType.IMMORTAL,
                StatType.TWICEBORN, StatType.CRIT_CHANCE, StatType.DIVERT_CHANCE,
                StatType.ARMOR_ABSORPTION, StatType.WILLPOWER_ABSORPTION,
                StatType.DAMAGE_ABSORPTION_SHIELD, StatType.TRANSFER_DAMAGE_COUNT,
                StatType.KNOCKBACK_STR, StatType.ALWAYS_MISS,
                StatType.STRENGTH_ATTACK, StatType.MIN_STRENGTH_ATTACK,
                StatType.ARMOR_NEGATION]) {
                if (entity.stats.getValue(type, 0) != 0)
                    throw new ArgumentError("unsupported:stat:" + type.name);
            }
            if (entity.bonusedTalents) {
                if (entity.bonusedTalents.talents && entity.bonusedTalents.talents.totalRanks != 0)
                    throw new ArgumentError("unsupported:talents");
                for (var key:String in entity.bonusedTalents.talentBonuses)
                    throw new ArgumentError("unsupported:talent-bonus");
            }
        }

        public static function calculate(selected:BattleAbility):Object {
            var started:int = getTimer();
            if (!selected || !selected.caster || !selected.caster.board)
                return {status:"unsupported", reason:"no-request", restored:true, rows:[]};
            var caster:IBattleEntity = selected.caster;
            var board:IBattleBoard = caster.board;
            var manager:BattleAbilityManager = board.abilityManager as BattleAbilityManager;
            var def:BattleAbilityDef = selected.def as BattleAbilityDef;
            var turn:Object = board.fsm ? board.fsm.turn : null;
            var targets:Array = [];
            var snapshots:Array = [];
            var byId:Object = {};
            var rows:Array = [];
            var seen:Dictionary = new Dictionary();
            var entity:IBattleEntity;
            var effect:Effect;
            var existingOp:Op;
            var snapshot:Object;
            var i:int;
            var entered:Boolean = false;
            var restored:Boolean = true;
            var cacheRestored:Boolean = false;
            var status:String = "unsupported";
            var failure:* = null;
            var cleanupFailure:* = null;
            var stage:String = "request";
            var liveRng:int;
            var fakeRng:int;
            var liveId:int;
            var liveExecuted:int;
            var incomplete:int;
            try {
                if (!manager || board.fake || manager.faking || manager.numIncompleteAbilities != 0)
                    throw new ArgumentError("unsupported:busy");
                if (!turn || turn.ability !== selected || turn.committed || turn.entity !== caster ||
                    !caster.playerControlled || !caster.alive || selected.executed || selected.executing)
                    throw new ArgumentError("unsupported:turn");
                if (turn.move && !turn.move.executed && turn.move.numSteps > 1)
                    throw new ArgumentError("unsupported:pending-move");
                stage = "definition";
                if (!def || def.id != "abl_threadtheneedle" || def.level < 1 || def.level > 3 ||
                    def.effects.length != 2 || def.effects[0].ops.length != 0 ||
                    def.effects[0].persistent || def.effects[1].persistent ||
                    def.effects[1].ops.length != 2)
                    throw new ArgumentError("unsupported:definition");
                var damageDef:IEffectDef = def.effects[1];
                // Native tags is a Dictionary, not the serialized data's array.
                for each (var definitionTag:EffectTag in damageDef.tags)
                    throw new ArgumentError("unsupported:definition-tags");
                var strParams:Object = damageDef.ops[0].params;
                var armParams:Object = damageDef.ops[1].params;
                if (damageDef.ops[0].id.name != "DAMAGE_STR" ||
                    damageDef.ops[1].id.name != "CHANGE_STAT" || armParams.stat != "ARMOR" ||
                    armParams.amount != -def.level || strParams.perCasterStrength != 1 ||
                    strParams.perTargetArmor != -1 || strParams.damage != 0 ||
                    strParams.maxMissChance != 0 || strParams.missChancePer != 0 ||
                    strParams.distributeToArmor || strParams.distributeToWillpower ||
                    strParams.attack_expression)
                    throw new ArgumentError("unsupported:ops");
                if (selected.targetSet.tiles.length || selected.targetSet.targets.length == 0)
                    throw new ArgumentError("unsupported:select-line-first");
                stage = "targets";
                for each (entity in selected.targetSet.targets) {
                    if (!entity || seen[entity] || entity.board !== board || !entity.alive ||
                        !entity.attackable || !entity.stats.hasStat(StatType.ARMOR))
                        throw new ArgumentError("unsupported:target");
                    seen[entity] = true;
                    if (BattleAbilityValidation.validate(def, caster, null, entity, null,
                        false, false, true) != BattleAbilityValidation.OK)
                        throw new ArgumentError("unsupported:validation");
                    targets.push(entity);
                }
                for each (entity in board.entities) {
                    stage = "entity-guards:" + entity.id;
                    rejectStats(entity);
                    if (entity.effects.hasTag(EffectTag.HAS_DAMAGE_RECOURSE_TARGET))
                        throw new ArgumentError("unsupported:damage-recourse");
                    // Exact-build diagnostic format is used only as a fail-closed
                    // research guard; no public modifier iterator exists here.
                    for (i = 0; i < entity.stats.numStats; i++) {
                        var mods:String = entity.stats.getStatByIndex(i).getDebugStringMods("");
                        if (mods && mods.indexOf(" charges=") >= 0)
                            throw new ArgumentError("unsupported:charged-stat");
                    }
                    for each (effect in entity.effects.effects) {
                        if (ALLOWED.indexOf("|" + effect.ability.def.id + "|") < 0)
                            throw new ArgumentError("unsupported:effect:" + effect.ability.def.id);
                        if (seen[entity] && effect.ability.def.id == "pas_returnthefavor")
                            throw new ArgumentError("unsupported:reaction-annotation");
                        // Heavy Impact watches its owner's outgoing STR attack,
                        // not another archer's hit on that owner (casterRule SELF).
                        if (effect.ability.def.id == "pas_heavyimpact" && effect.ability.caster === caster)
                            throw new ArgumentError("unsupported:heavy-impact-caster");
                        for each (existingOp in effect.ops)
                            if (existingOp.def.id.name == "INT_STAT_MOD" && existingOp.def.params.charges != 0)
                                throw new ArgumentError("unsupported:charged-modifier");
                    }
                    stage = "snapshot:" + entity.id;
                    snapshot = {entity:entity, real:entity.stats, stats:entity.stats.clone(entity),
                        x:entity.x, y:entity.y, effects:entity.effects.effects.concat(), alive:entity.alive};
                    if (!sameStats(entity.stats, snapshot.stats, board))
                        throw new ArgumentError("unsupported:modifier-clone");
                    snapshots.push(snapshot); byId["id:" + entity.id] = snapshot;
                }
                liveRng = manager.rng.sampleCount;
                liveId = manager.lastId; liveExecuted = manager.lastExecutedId;
                incomplete = manager.numIncompleteAbilities;
                stage = "fake";
                entered = true; board.fake = true;
                for each (snapshot in snapshots) resetFake(snapshot, board);
                fakeRng = manager.rng.sampleCount;
                var temporary:BattleAbility = new BattleAbility(caster, def, manager);
                for each (entity in targets) temporary.targetSet.addTarget(entity);
                for each (entity in targets) {
                    if (!damageDef.checkEffectConditionsAbility(temporary, entity, false, new AbilityReason()))
                        throw new ArgumentError("unsupported:effect-condition");
                    effect = new Effect(temporary, damageDef, entity, null);
                    var strengthOp:Op_DamageStr = new Op_DamageStr(damageDef.ops[0], effect);
                    var armorOp:Op_ChangeStat = new Op_ChangeStat(damageDef.ops[1], effect);
                    // Native Effect computes all ops before applying any of them.
                    // Call ops directly so an exception cannot be swallowed by Effect.
                    strengthOp.result = strengthOp.execute();
                    armorOp.result = armorOp.execute();
                    if (strengthOp.result == null || armorOp.result == null)
                        throw new Error("Missing native result");
                    if (strengthOp.result != EffectResult.OK ||
                        (armorOp.result != EffectResult.OK && armorOp.result != EffectResult.FAIL))
                        throw new ArgumentError("unsupported:native-result");
                    strengthOp.apply(); armorOp.apply();
                    snapshot = byId["id:" + entity.id];
                    var beforeArmor:int = snapshot.stats.getValue(StatType.ARMOR);
                    var beforeStrength:int = snapshot.stats.getValue(StatType.STRENGTH);
                    var afterArmor:int = entity.stats.getValue(StatType.ARMOR);
                    var afterStrength:int = entity.stats.getValue(StatType.STRENGTH);
                    // Lethal lifecycle/aura removal needs its own native evidence.
                    if (afterStrength <= 0) throw new ArgumentError("unsupported:lethal");
                    if (afterArmor > beforeArmor || afterStrength > beforeStrength)
                        throw new Error("Unexpected gain in damage-only probe");
                    rows.push({id:entity.id, armorBefore:beforeArmor, strengthBefore:beforeStrength,
                        armorAfter:afterArmor, strengthAfter:afterStrength,
                        armorLoss:beforeArmor-afterArmor, strengthLoss:beforeStrength-afterStrength,
                        resistedArmor:effect.hasTag(EffectTag.RESISTING_ARMOR),
                        resistedStrength:effect.hasTag(EffectTag.RESISTING_STRENGTH)});
                }
                if (manager.rng.sampleCount != fakeRng) throw new Error("Fake RNG consumed");
                status = "ready";
            } catch (problem:*) {
                failure = problem;
                status = "error"; // Classify explicit rejections only after restoration.
            }
            // No return or nested finally: both paths reach cleanup. Same boundary
            // discipline as the existing verified Ram research implementation.
            if (entered) {
                try {
                    for each (snapshot in snapshots) resetFake(snapshot, board);
                    cacheRestored = true;
                } catch (cacheProblem:*) { cleanupFailure = cacheProblem; restored = false; }
                try { board.fake = false; }
                catch (exitProblem:*) { cleanupFailure = exitProblem; restored = false; }
                try {
                    if (board.fake || manager.faking || manager.rng.sampleCount != liveRng ||
                        manager.lastId != liveId || manager.lastExecutedId != liveExecuted ||
                        manager.numIncompleteAbilities != incomplete || board.fsm.turn !== turn ||
                        turn.ability !== selected || turn.committed ||
                        selected.targetSet.targets.length != targets.length) restored = false;
                    for (i = 0; i < targets.length; i++)
                        if (selected.targetSet.targets[i] !== targets[i]) restored = false;
                    for each (snapshot in snapshots) {
                        entity = snapshot.entity;
                        if (entity.stats !== snapshot.real || entity.fake ||
                            !sameStats(entity.stats, snapshot.stats, board) || entity.x != snapshot.x ||
                            entity.y != snapshot.y || entity.alive != snapshot.alive ||
                            entity.effects.effects.length != snapshot.effects.length) restored = false;
                        for (i = 0; i < snapshot.effects.length; i++)
                            if (entity.effects.effects[i] !== snapshot.effects[i]) restored = false;
                    }
                } catch (verifyProblem:*) { cleanupFailure = verifyProblem; restored = false; }
            }
            var reason:String = failure == null ? "" : String(failure);
            if (failure != null && restored && failure is ArgumentError && reason.indexOf("unsupported:") >= 0)
                status = "unsupported";
            if (!restored) status = "error";
            return {status:status, reason:reason, stage:stage,
                failureStack:failure is Error ? Error(failure).getStackTrace() : null,
                cleanup:cleanupFailure == null ? "" : String(cleanupFailure),
                entered:entered, restored:restored, cacheRestored:cacheRestored,
                caster:caster.id, target:targets.length ? targets[targets.length-1].id : null,
                level:def ? def.level : 0, elapsedMs:getTimer()-started,
                rows:status == "ready" ? rows : []};
        }
    }
}
