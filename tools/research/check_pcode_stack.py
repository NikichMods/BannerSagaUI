# SPDX-License-Identifier: MPL-2.0
"""Bounded symbolic p-code stack-height check, not an AVM2 verifier.

Supports the instructions used by the Ram probe. Rejects unknown opcodes;
does not verify types, names, access rights or exception coverage. Exception
handlers start with one operand and an empty dynamic scope stack.
"""
import re
import sys
from pathlib import Path

def check(text):
    header,rest=text.split('code\n',1)
    code,tail=rest.split('end ; code\n',1)
    labels={};ops=[]
    for line in code.splitlines():
        line=line.strip()
        if not line:continue
        if line.endswith(':'): labels[line[:-1]]=len(ops)
        else:ops.append(line)
    states={};todo=[(0,0,0,'entry')];issues=[];peak=0
    for match in re.finditer(r'try from (\w+) to (\w+) target (\w+)',tail):
        todo.append((labels[match[3]],1,0,'exception'))
    while todo:
        i,stack,scope,via=todo.pop()
        if i>=len(ops):issues.append(('falloff',i,stack));continue
        if i in states:
            if states[i]!=(stack,scope):issues.append(('merge',i,ops[i],states[i],(stack,scope),via))
            continue
        states[i]=(stack,scope);peak=max(peak,stack)
        line=ops[i];op=line.split()[0];a=line[len(op):].strip()
        runtime=2 if 'RTQNameL(' in a else (1 if 'MultinameL(' in a or 'RTQName(' in a else 0)
        pop=push=0;targets=[];stop=False;sd=0
        if op in ('pushnull','pushundefined','pushtrue','pushfalse','pushnan',
                  'pushbyte','pushshort','pushint','pushuint','pushdouble',
                  'pushstring','pushnamespace','getlocal','getlocal0',
                  'getlocal1','getlocal2','getlocal3'):push=1
        elif op in ('findpropstrict','findproperty'):pop=runtime;push=1
        elif op in ('getlex','getscopeobject','getglobalscope','getouterscope','newactivation','newcatch'):push=1
        elif op in ('setlocal','setlocal0','setlocal1','setlocal2','setlocal3'):pop=1
        elif op in ('getslot','getproperty'):pop=1+runtime;push=1
        elif op in ('setslot','setproperty','initproperty'):pop=2+runtime
        elif op=='deleteproperty':pop=1+runtime;push=1
        elif op in ('callproperty','callpropvoid','constructprop','callsuper','callsupervoid','callproplex'):
            pop=1+int(a.rsplit(',',1)[1])+runtime;push=0 if op.endswith('void') else 1
        elif op in ('construct','applytype'):pop=1+int(a);push=1
        elif op=='newclass':pop=push=1
        elif op=='constructsuper':pop=1+int(a)
        elif op=='call':pop=2+int(a);push=1
        elif op=='newobject':pop=2*int(a);push=1
        elif op=='newarray':pop=int(a);push=1
        elif op in ('pushscope','pushwith'):pop=1;sd=1
        elif op=='popscope':sd=-1
        elif op=='pop':pop=1
        elif op=='dup':pop=1;push=2
        elif op=='swap':pop=2;push=2
        elif op in ('add','subtract','multiply','divide','modulo','equals','strictequals','lessthan','lessequals','greaterthan','greaterequals','bitand','bitor','bitxor','lshift','rshift','urshift','astypelate','istypelate','nextname','nextvalue'):pop=2;push=1
        elif op in ('coerce','coerce_a','coerce_b','coerce_d','coerce_i','coerce_o',
                    'coerce_s','coerce_u','convert_s','convert_i','convert_u',
                    'convert_d','convert_b','convert_o','not','increment_i',
                    'decrement_i','increment','decrement','negate','negate_i',
                    'typeof','istype','astype'):pop=push=1
        elif op=='hasnext2':push=1
        elif op in ('returnvoid','returnvalue','throw'):pop=0 if op=='returnvoid' else 1;stop=True
        elif op=='jump':targets=[labels[a]];stop=True
        elif op in ('iftrue','iffalse','ifeq','ifne','iflt','ifle','ifgt','ifge',
                    'ifnlt','ifnle','ifngt','ifnge','ifstricteq','ifstrictne'):
            pop=1 if op in ('iftrue','iffalse') else 2;targets=[labels[a]]
        elif op=='lookupswitch':pop=1;targets=[labels[x] for x in re.findall(r'\b[A-Za-z_]\w*\b',a)];stop=True
        elif op in ('kill','nop','label','debug','debugline','debugfile','inclocal_i','declocal_i'):pass
        else:raise ValueError('Unsupported opcode '+line)
        if stack<pop or scope+sd<0:issues.append(('underflow',i,line,stack,scope,pop));continue
        stack=stack-pop+push;scope+=sd;peak=max(peak,stack)
        todo.extend((t,stack,scope,f'{i}:{line}') for t in targets)
        if not stop:todo.append((i+1,stack,scope,f'{i}:{line}'))
    limit=re.search(r'^maxstack (\d+)$',header,re.M)
    if limit and peak>int(limit[1]):issues.append(('maxstack',peak,int(limit[1])))
    return {'instructions':len(ops),'visited':len(states),'peak_stack':peak,'issues':issues}


def require_balanced(text):
    result=check(text)
    if result['issues']:
        raise ValueError('P-code stack-height check failed: '+repr(result['issues'][:8]))
    return result

if __name__=='__main__':
    for path in map(Path,sys.argv[1:]):print(path.name,require_balanced(path.read_text(encoding='utf-8-sig')))
