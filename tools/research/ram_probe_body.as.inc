// SPDX-License-Identifier: MPL-2.0
// Original research-only method body. Compiled in a disposable donor class;
// no host source or payload belongs in Git. Not a production forecast.
// Parameters match BattleAbility.getStatChange; only explicit null-stat calls
// from our two diagnostic hooks enter this branch.
if(!param2 || !param2.board) return false;
var probeBoard:IBattleBoard = param2.board;
// Research-only board-local circuit breaker. A unique, never-dispatched
// diagnostic event token avoids adding state to host classes or save data.
// trace accepts any arguments if the token is ever dispatched accidentally.
if(probeBoard.hasEventListener("BSUI_RAM_PROBE_DISABLED")) return false;
var probeManager:BattleAbilityManager = probeBoard.abilityManager as BattleAbilityManager;
var probeEntity:IBattleEntity;
var probeSource:IBattleEntity;
var probeOther:IBattleEntity;
var probeEffect:Effect;
var probeDef:BattleAbilityDef;
var probeInitial:BattleAbilityDef;
var probeFall:BattleAbilityDef;
var probeAura:BattleAbilityDef;
var probeSelf:BattleAbilityDef;
var probeAbility:BattleAbility;
var probeOp:Op;
var probeRect:TileRect;
var probeRect2:TileRect;
var probeTile:Tile;
var probeResident:ITileResident;
var probeSnapshots:Array = [];
var probeRequests:Array = [];
var probeOps:Array = [];
var probeSeen:Dictionary = new Dictionary();
var probeSnapshot:Object;
var probeRequest:Object;
var probeRow:Object;
var probeRows:Array = [];
var probeKey:String;
var probeAllowed:String = "|pas_shieldwall|abl_shieldwall_bonus|abl_shieldwall_bonus_self|pas_light_step|pas_puncture|pas_returnthefavor|";
var probeDamages:int = 0;
var probeI:int;
var probeX:int;
var probeY:int;
var probeDistance:int;
var probeDx:int;
var probeDy:int;
var probeRange:int;
var probeAuraCount:int;
var probeRngCount:int;
var probeFakeRngCount:int;
var probeId:int;
var probeExecutedId:int;
var probeTurn:Object = probeBoard.fsm ? probeBoard.fsm.turn : null;
var probeTurnAbility:Object = probeTurn ? probeTurn.ability : null;
var probeTargets:Object = probeTurnAbility ? probeTurnAbility.targetSet.targets.concat() : null;
var probeEntered:Boolean = false;
var probeStatus:String = "UNVERIFIED";
var probeError:String = "";
var probeFailureValue:*;
var probeCleanupFailureValue:*;
var probeFailed:Boolean = false;
var probeCleanupFailed:Boolean = false;
var probeStable:Boolean = true;
var probeEnd:Tile;
// Snapshot actual results only when the normal manager has become idle.
if(param4 == null)
{
    if(probeBoard.fake || probeManager.faking || probeManager.numIncompleteAbilities != 0)
        return false;
    try
    {
        for each(probeEntity in probeBoard.entities)
        {
            probeRows.push({id:probeEntity.id, x:probeEntity.x, y:probeEntity.y,
                armor:probeEntity.stats.getValue(StatType.ARMOR),
                armorBase:probeEntity.stats.getBase(StatType.ARMOR),
                strength:probeEntity.stats.getValue(StatType.STRENGTH),
                willpower:probeEntity.stats.getValue(StatType.WILLPOWER)});
        }
        probeBoard.logger.info("BSUI_RAM_IDLE " + JSON.stringify({trigger:param1.id, rows:probeRows}));
    }
    catch(probeReadFailure:Error)
    {
        probeBoard.addEventListener("BSUI_RAM_PROBE_DISABLED",trace);
        probeBoard.logger.error("BSUI_RAM_PROBE_DISABLED snapshot " + probeReadFailure);
    }
    return false;
}
try
{
    if(param1.id != "abl_batteringram" || !param5 || !param5.mobile || !param5.alive)
        throw new ArgumentError("unsupported:target");
    if(probeBoard.fake || probeManager.faking || probeManager.numIncompleteAbilities != 0)
        throw new ArgumentError("unsupported:busy");
    if(!probeTurn || probeTurn.committed || probeTurnAbility == null || probeTurnAbility.def != param1)
        throw new ArgumentError("unsupported:turn");
    if(probeTurn.move && !probeTurn.move.executed && probeTurn.move.numSteps > 1)
        throw new ArgumentError("unsupported:pending-move");
    if(BattleAbilityValidation.validate(param1,param2,null,param5,null,false,true,true) != BattleAbilityValidation.OK)
        throw new ArgumentError("unsupported:invalid-target");
    if(probeBoard.triggers && probeBoard.triggers.triggers.length != 0)
        throw new ArgumentError("unsupported:board-triggers");
    if(param5.effects.hasTag(EffectTag.NO_KNOCKBACK) || param5.effects.hasTag(EffectTag.GHOSTED))
        throw new ArgumentError("unsupported:movement-tag");
    probeEnd = Op_KnockbackHelper.getKnockbackStopTile(param1,param2,param2.rect,param5,true);
    if(!probeEnd) throw new ArgumentError("unsupported:no-destination");
    // The first probe deliberately rejects response-bearing targets, talents,
    // unknown active effects and hazards. These are research boundaries, not
    // an adopted reduction of the final product's scope.
    for each(probeEntity in probeBoard.entities)
    {
        if(!probeEntity.stats.hasStat(StatType.ARMOR)) throw new ArgumentError("unsupported:no-armor");
        if(probeEntity.stats.getValue(StatType.DIVERT_CHANCE) != 0)
            throw new ArgumentError("unsupported:divert");
        if(probeEntity.bonusedTalents)
        {
            if(probeEntity.bonusedTalents.talents && probeEntity.bonusedTalents.talents.totalRanks != 0)
                throw new ArgumentError("unsupported:talents");
            for(probeKey in probeEntity.bonusedTalents.talentBonuses)
                throw new ArgumentError("unsupported:talent-bonus");
        }
        for each(probeEffect in probeEntity.effects.effects)
        {
            if(probeAllowed.indexOf("|" + probeEffect.ability.def.id + "|") < 0)
                throw new ArgumentError("unsupported:effect:" + probeEffect.ability.def.id);
            if(probeEntity == param5 && probeEffect.ability.def.id == "pas_returnthefavor")
                throw new ArgumentError("unsupported:retaliating-target");
        }
        probeSnapshots.push({entity:probeEntity, real:probeEntity.stats,
            stats:probeEntity.stats.clone(probeEntity), x:probeEntity.x, y:probeEntity.y,
            effects:probeEntity.effects.effects.concat(), auraBefore:0, auraAfter:0});
    }
    probeInitial = probeManager.factory.fetchBattleAbilityDef("abl_batteringram_initial_arm_dam").getAbilityDefForLevel(param1.level) as BattleAbilityDef;
    probeFall = probeManager.factory.fetchBattleAbilityDef("abl_batteringram_fallthrough_arm_dam");
    probeAura = probeManager.factory.fetchBattleAbilityDef("abl_shieldwall_bonus");
    probeSelf = probeManager.factory.fetchBattleAbilityDef("abl_shieldwall_bonus_self");
    probeRequests.push({def:probeInitial, source:param2, target:param5, modifier:false});
    probeDx = probeEnd.x == param5.x ? 0 : (probeEnd.x > param5.x ? 1 : -1);
    probeDy = probeEnd.y == param5.y ? 0 : (probeEnd.y > param5.y ? 1 : -1);
    probeDistance = Math.max(Math.abs(probeEnd.x-param5.x),Math.abs(probeEnd.y-param5.y));
    probeRect = param5.rect.clone();
    for(probeI=1;probeI<=probeDistance;probeI++)
    {
        probeRect.setLocation(TileLocation.fetch(param5.x+probeDx*probeI,param5.y+probeDy*probeI));
        for(probeX=0;probeX<param5.boardWidth;probeX++)
        {
            for(probeY=0;probeY<param5.boardLength;probeY++)
            {
                probeTile = probeBoard.tiles.getTile(param5.x+probeDx*probeI+probeX,param5.y+probeDy*probeI+probeY);
                if(!probeTile) throw new ArgumentError("unsupported:path-outside-board");
                for each(probeResident in probeTile.residents)
                {
                    probeOther = probeResident as IBattleEntity;
                    if(probeOther && probeOther != param5 && probeOther.alive && !probeSeen[probeOther])
                    {
                        if(probeOther.effects.hasTag(EffectTag.GHOSTED)) continue;
                        probeSeen[probeOther] = true;
                        probeRequests.push({def:probeFall, source:probeOther, target:param5, modifier:false});
                    }
                }
            }
        }
    }
    probeDamages = probeRequests.length;
    // Project the known Shield Wall relation with cloned rectangles and the
    // host's own target predicate and rectangle distance. Never call Op_Aura.
    for each(probeSnapshot in probeSnapshots)
    {
        probeSource = probeSnapshot.entity;
        if(!probeSource.alive || !probeSource.enabled) continue;
        for each(probeEffect in probeSource.effects.effects)
        {
            if(probeEffect.ability.def.id != "pas_shieldwall") continue;
            probeRect = probeSource.rect.clone();
            if(probeSource == param5) probeRect.setLocation(probeEnd.location);
            for each(probeOther in probeBoard.entities)
            {
                if(!probeOther.alive || !probeOther.enabled) continue;
                if(!probeAura.targetRule.isValid(probeSource,probeRect,probeOther,null,false,probeAura,true)) continue;
                probeRect2 = probeOther.rect.clone();
                if(probeOther == param5) probeRect2.setLocation(probeEnd.location);
                probeRange = TileRectRange.computeRange(probeRect,probeRect2);
                if(probeRange < probeAura.rangeMin(probeSource) || probeRange > probeAura.rangeMax(probeSource)) continue;
                probeRequests.push({def:probeAura,source:probeSource,target:probeOther,modifier:true});
                probeRequests.push({def:probeSelf,source:probeSource,target:probeSource,modifier:true});
            }
        }
    }
    probeRngCount = probeManager.rng.sampleCount;
    probeId = probeManager.lastId;
    probeExecutedId = probeManager.lastExecutedId;
    probeEntered = true;
    probeBoard.fake = true;
    probeFakeRngCount = probeManager.rng.sampleCount;
    for(probeI=0;probeI<=probeRequests.length;probeI++)
    {
        if(probeI == probeDamages)
        {
            for each(probeSnapshot in probeSnapshots)
            {
                probeEntity = probeSnapshot.entity;
                for each(probeEffect in probeSnapshot.effects)
                {
                    if(probeEffect.ability.def.id == "abl_shieldwall_bonus" || probeEffect.ability.def.id == "abl_shieldwall_bonus_self")
                    {
                        probeEntity.stats.getStat(StatType.ARMOR).removeMods(probeEffect);
                        probeSnapshot.auraBefore++;
                    }
                }
            }
        }
        if(probeI == probeRequests.length) break;
        probeRequest = probeRequests[probeI];
        probeDef = probeRequest.def;
        if(probeDef.effects.length != 1 || probeDef.effects[0].ops.length != 1)
            throw new ArgumentError("unsupported:definition-shape");
        if(!probeRequest.modifier && BattleAbilityValidation.validate(probeDef,probeRequest.source,null,probeRequest.target,null,false,false,true) != BattleAbilityValidation.OK)
            throw new ArgumentError("unsupported:subability-condition");
        probeAbility = new BattleAbility(probeRequest.source,probeDef,probeBoard.abilityManager);
        probeAbility.targetSet.setTarget(probeRequest.target);
        if(!probeDef.effects[0].checkEffectConditionsAbility(probeAbility,probeRequest.target,true,new AbilityReason()))
            throw new ArgumentError("unsupported:effect-condition");
        probeEffect = new Effect(probeAbility,probeDef.effects[0],probeRequest.target,null);
        if(probeRequest.modifier)
        {
            if(probeDef.effects[0].ops[0].id.name != "INT_STAT_MOD" || probeDef.effects[0].ops[0].params.stat != "ARMOR")
                throw new ArgumentError("unsupported:modifier-op");
            probeOp = new Op_IntStatMod(probeDef.effects[0].ops[0],probeEffect);
        }
        else
        {
            if(probeDef.effects[0].persistent || probeDef.effects[0].ops[0].id.name != "CHANGE_STAT" || probeDef.effects[0].ops[0].params.stat != "ARMOR")
                throw new ArgumentError("unsupported:damage-op");
            probeOp = new Op_ChangeStat(probeDef.effects[0].ops[0],probeEffect);
        }
        probeOps.push(probeOp);
        probeOp.result = probeOp.execute();
        probeOp.apply();
        if(probeRequest.modifier)
        {
            for each(probeSnapshot in probeSnapshots)
                if(probeSnapshot.entity == probeRequest.target) probeSnapshot.auraAfter++;
        }
    }
    for each(probeSnapshot in probeSnapshots)
    {
        probeEntity = probeSnapshot.entity;
        probeRows.push({id:probeEntity.id,
            x:probeEntity == param5 ? probeEnd.x : probeEntity.x,
            y:probeEntity == param5 ? probeEnd.y : probeEntity.y,
            armorBefore:probeSnapshot.stats.getValue(StatType.ARMOR),
            armor:probeEntity.stats.getValue(StatType.ARMOR),
            armorBase:probeEntity.stats.getBase(StatType.ARMOR),
            strength:probeEntity.stats.getValue(StatType.STRENGTH),
            auraBefore:probeSnapshot.auraBefore,auraAfter:probeSnapshot.auraAfter});
    }
    if(probeManager.rng.sampleCount != probeFakeRngCount)
        throw new Error("Fake RNG consumed");
}
catch(probeFailure:*)
{
    // Defer formatting until after fake-mode restoration. Catch all thrown
    // values, including values that are not Error instances.
    probeFailed = true;
    probeFailureValue = probeFailure;
    probeStatus = probeFailure is ArgumentError ? "UNSUPPORTED" : "ERROR";
}
// There are no early exits in the calculation try/catch. Both paths reach
// cleanup; its catch only stores data before restoring the board. Do not nest
// handlers inside finally: FFDec 26.4.0 loses the outer stack discriminator.
{
    if(probeEntered)
    {
        try
        {
            for each(probeOp in probeOps) probeOp.remove();
        }
        catch(probeCleanupFailure:*)
        {
            probeStable = false;
            probeCleanupFailed = true;
            probeCleanupFailureValue = probeCleanupFailure;
        }
        probeBoard.fake = false;
        if(probeManager.rng.sampleCount != probeRngCount ||
            probeManager.lastId != probeId || probeManager.lastExecutedId != probeExecutedId ||
            probeManager.numIncompleteAbilities != 0) probeStable = false;
        for each(probeSnapshot in probeSnapshots)
        {
            probeEntity = probeSnapshot.entity;
            if(probeEntity.stats != probeSnapshot.real || probeEntity.stats.numStats != probeSnapshot.stats.numStats ||
                !probeEntity.stats.testEquals(probeSnapshot.stats,probeBoard.logger) ||
                probeEntity.x != probeSnapshot.x || probeEntity.y != probeSnapshot.y ||
                probeEntity.effects.effects.length != probeSnapshot.effects.length) probeStable = false;
            for(probeI=0;probeI<probeSnapshot.effects.length;probeI++)
                if(probeEntity.effects.effects[probeI] != probeSnapshot.effects[probeI]) probeStable = false;
        }
        if(probeBoard.fsm.turn != probeTurn || probeTurn.ability != probeTurnAbility || probeTurn.committed ||
            probeTurnAbility.targetSet.targets.length != probeTargets.length) probeStable = false;
        for(probeI=0;probeI<probeTargets.length;probeI++)
            if(probeTurnAbility.targetSet.targets[probeI] != probeTargets[probeI]) probeStable = false;
    }
}
if(probeFailed) probeError = String(probeFailureValue);
if(probeCleanupFailed) probeError += " cleanup=" + String(probeCleanupFailureValue);
probeBoard.logger.info("BSUI_RAM_PROBE " + JSON.stringify({status:probeStatus,error:probeError,
    restored:probeStable,entered:probeEntered,caster:param2.id,target:param5 ? param5.id : null,
    level:param1.level,damageApplications:probeDamages,rows:probeRows}));
if(!probeStable || probeStatus == "ERROR")
{
    probeBoard.addEventListener("BSUI_RAM_PROBE_DISABLED",trace);
    probeBoard.logger.error("BSUI_RAM_PROBE_DISABLED invariantOrCalculationError");
}
return false;
