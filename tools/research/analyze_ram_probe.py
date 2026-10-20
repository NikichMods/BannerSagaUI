# SPDX-License-Identifier: MPL-2.0
"""Compare diagnostic predictions to independently observed native Ram results.

Reads a local game log only. Does not run a simulator, edit saves or accept UX.
"""
import argparse
import json
import re
from pathlib import Path


def analyze(lines):
    pending = armed = None
    samples, skipped = [], []
    for number, line in enumerate(lines, 1):
        if 'BSUI_RAM_PROBE ' in line:
            record = json.loads(line.split('BSUI_RAM_PROBE ',1)[1])
            valid = (record.get('status') == 'UNVERIFIED' and record.get('entered') is True
                     and record.get('restored') is True and record.get('cacheRestored', True) is True)
            pending = (number, record) if valid else None
            if not valid: skipped.append({'line':number,'status':record.get('status'),'error':record.get('error')})
        elif 'Execute [' in line:
            execution = re.search(r'Execute\s+\[\S+\s+(.+?)->\{([^}]*)\}\s+abl_batteringram/(\d+)\]',line)
            if execution:
                if pending and (pending[1].get('caster') != execution[1] or pending[1].get('target') != execution[2] or pending[1].get('level') != int(execution[3])):
                    skipped.append({'line':number,'status':'IDENTITY_MISMATCH','error':'native caster/target differ from last prediction'})
                    pending = None
                armed, pending = pending, None
            elif armed is None:
                # A cancelled Ram followed by a different action is no sample.
                pending = None
        elif 'BSUI_RAM_PROBE_DISABLED' in line:
            pending = armed = None
            skipped.append({'line':number,'status':'DISABLED','error':line.strip()})
        elif 'BSUI_RAM_IDLE ' in line and armed is not None:
            actual = json.loads(line.split('BSUI_RAM_IDLE ',1)[1])
            prediction_line, predicted = armed
            before = {row['id']:row for row in predicted['rows']}
            after = {row['id']:row for row in actual['rows']}
            if len(before) != len(predicted['rows']) or len(after) != len(actual['rows']):
                raise ValueError('Duplicate entity IDs in diagnostic rows')
            differences = []
            for identity in sorted(before.keys() | after.keys()):
                if identity not in before or identity not in after:
                    differences.append({'id':identity,'field':'presence'})
                    continue
                for field in ('x','y','armor','armorBase','strength'):
                    if before[identity][field] != after[identity][field]:
                        differences.append({'id':identity,'field':field,
                            'predicted':before[identity][field],'actual':after[identity][field]})
            samples.append({'prediction_line':prediction_line,'actual_line':number,
                'status':'MISMATCH' if differences else 'MATCH',
                'damage_applications':predicted['damageApplications'],
                'aura_changes':[row['id'] for row in predicted['rows'] if row['auraBefore'] != row['auraAfter']],
                'differences':differences})
            armed = None
    return {'scope':'numeric comparison only; no UX or stable acceptance',
        'samples':samples,'skipped':skipped,'awaiting_native_completion':armed is not None,
        'comparable_sample_count':len(samples)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log',type=Path)
    args = parser.parse_args()
    print(json.dumps(analyze(args.log.read_text(encoding='utf-8-sig').splitlines()),indent=2,ensure_ascii=False))
