# SPDX-License-Identifier: MPL-2.0
"""Compare tag payloads and complete ABC bodies independently of FFDec text."""
import hashlib
import json
import sys
from pathlib import Path
from abc_index import ABC, swf_tags, frame_header


def compare(before, after):
    a, b = swf_tags(before), swf_tags(after)
    if len(a) != len(b):
        raise ValueError('Tag count changed')
    output = {'frame_header_equal': frame_header(before) == frame_header(after),
        'tag_count': len(a), 'changed_tags': []}
    for i, (left, right) in enumerate(zip(a, b)):
        if left == right:
            continue
        if left[0] != right[0]:
            raise ValueError('Tag type changed')
        info = {'index': i, 'type': left[0], 'size_before': len(left[1]),
                'size_after': len(right[1])}
        if left[0] == 82:
            def split(payload):
                end = payload.index(b'\0', 4) + 1
                return payload[:end], ABC(payload[end:])
            ah, aa = split(left[1])
            bh, ba = split(right[1])
            info['abc_header_equal'] = ah == bh
            info['prefix_equal'] = aa.body_prefix == ba.body_prefix
            info['changed_sections'] = [{'name': key, 'before': len(val),
                'after': len(ba.sections[key])} for key, val in aa.sections.items()
                if val != ba.sections[key]]
            info['changed_method_info'] = [{'index': idx,
                'before': {k:v for k,v in am.items() if k != 'raw'},
                'after': {k:v for k,v in bm.items() if k != 'raw'}}
                for idx, (am,bm) in enumerate(zip(aa.methods,ba.methods))
                if am != bm]
            info['changed_method_info_count'] = len(info['changed_method_info'])
            info['changed_method_info'] = info['changed_method_info'][:12]
            info['body_count_before'] = len(aa.bodies)
            info['body_count_after'] = len(ba.bodies)
            if len(aa.bodies) != len(ba.bodies):
                raise ValueError('ABC body count changed')
            changes = []
            for ab, bb in zip(aa.bodies, ba.bodies):
                if ab['raw'] != bb['raw']:
                    changes.append({'index': ab['index'], 'method_before': ab['method'],
                        'method_after': bb['method'], 'bytes_before': len(ab['code']),
                        'bytes_after': len(bb['code']),
                        'code_sha_before': hashlib.sha256(ab['code']).hexdigest(),
                        'code_sha_after': hashlib.sha256(bb['code']).hexdigest(),
                        'metadata_equal': all(ab[k] == bb[k] for k in
                            ('stack', 'locals', 'scope', 'maxscope', 'exceptions', 'tail'))})
            info['changed_body_count'] = len(changes)
            info['changed_bodies'] = changes[:12]
        output['changed_tags'].append(info)
    output['before_sha256'] = hashlib.sha256(Path(before).read_bytes()).hexdigest()
    output['after_sha256'] = hashlib.sha256(Path(after).read_bytes()).hexdigest()
    return output


if __name__ == '__main__':
    print(json.dumps(compare(*sys.argv[1:]), ensure_ascii=False, indent=2))
