# SPDX-License-Identifier: MPL-2.0
"""Read-only, bounded ABC 46.16 index; no instruction emulation or SWF writes.

Format reference: adobe/avmplus doc/abcFormat-46-16.txt.
Unknown structures fail rather than guessing. Keep host data outside Git.
"""
import hashlib
import json
import struct
import sys
import zlib
from pathlib import Path


class Reader:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def take(self, n):
        if n < 0 or self.pos + n > len(self.data):
            raise ValueError('Truncated structure')
        value = self.data[self.pos:self.pos + n]
        self.pos += n
        return value

    def byte(self):
        return self.take(1)[0]

    def uint(self, bits=30):
        value = 0
        for shift in range(0, 35, 7):
            b = self.byte()
            value |= (b & 127) << shift
            if not b & 128:
                if value >= 1 << bits:
                    raise ValueError('Integer outside supported width')
                return value
        raise ValueError('Unterminated variable integer')

    def many(self, n):
        return [self.uint() for _ in range(n)]


def swf_tags(path):
    raw = Path(path).read_bytes()
    if raw[:3] == b'CWS':
        body = zlib.decompress(raw[8:])
    elif raw[:3] == b'FWS':
        body = raw[8:]
    else:
        raise ValueError('Only FWS/CWS supported')
    if len(body) + 8 != struct.unpack('<I', raw[4:8])[0]:
        raise ValueError('SWF length mismatch')
    r = Reader(body)
    nbits = body[0] >> 3
    r.take((5 + 4 * nbits + 7) // 8 + 4)
    tags = []
    while r.pos < len(body):
        header = struct.unpack('<H', r.take(2))[0]
        code, size = header >> 6, header & 63
        if size == 63:
            size = struct.unpack('<I', r.take(4))[0]
        tags.append((code, r.take(size)))
        if code == 0:
            if r.pos != len(body):
                raise ValueError('Trailing bytes after End tag')
            break
    if not tags or tags[-1][0] != 0:
        raise ValueError('Missing End tag')
    return tags


def frame_header(path):
    raw = Path(path).read_bytes()
    body = zlib.decompress(raw[8:]) if raw[:3] == b'CWS' else raw[8:]
    length = (5 + 4 * (body[0] >> 3) + 7) // 8 + 4
    return raw[3:4] + body[:length]


class ABC:
    def __init__(self, data):
        self.data = data
        r = self.r = Reader(data)
        if r.take(4) != b'\x10\x00\x2e\x00':
            raise ValueError('Only ABC 46.16 supported')
        self.sections = {}
        start = r.pos
        for _ in range(2):
            for _ in range(max(0, r.uint() - 1)):
                r.uint(32)
        self.sections['integer_pools'] = data[start:r.pos]
        start = r.pos
        r.take(8 * max(0, r.uint() - 1))
        self.sections['double_pool'] = data[start:r.pos]
        start = r.pos
        self.strings = ['']
        for _ in range(max(0, r.uint() - 1)):
            self.strings.append(r.take(r.uint()).decode('utf-8'))
        self.sections['string_pool'] = data[start:r.pos]
        start = r.pos
        self.namespaces = [(0, 0)]
        for _ in range(max(0, r.uint() - 1)):
            self.namespaces.append((r.byte(), r.uint()))
        for _ in range(max(0, r.uint() - 1)):
            r.many(r.uint())
        self.names = [(0, [])]
        for _ in range(max(0, r.uint() - 1)):
            kind = r.byte()
            if kind in (7, 13, 9, 14):
                values = r.many(2)
            elif kind in (15, 16, 27, 28):
                values = r.many(1)
            elif kind in (17, 18):
                values = []
            elif kind == 29:
                values = [r.uint()]
                values += r.many(r.uint())
            else:
                raise ValueError(f'Unsupported multiname {kind}')
            self.names.append((kind, values))
        self.sections['names'] = data[start:r.pos]
        start = r.pos
        self.method_count = r.uint()
        self.methods = []
        for _ in range(self.method_count):
            method_start = r.pos
            params = r.uint()
            signature = r.many(params + 2)  # return type, parameter types, name
            flags = r.byte()
            if flags & 8:
                for _ in range(r.uint()):
                    r.uint()
                    r.byte()
            if flags & 128:
                r.many(params)
            self.methods.append({'params': params, 'signature': signature,
                'flags': flags, 'raw': data[method_start:r.pos]})
        self.sections['method_info'] = data[start:r.pos]
        start = r.pos
        for _ in range(r.uint()):
            r.uint()
            r.many(2 * r.uint())
        self.sections['metadata'] = data[start:r.pos]
        start = r.pos
        count = r.uint()
        self.classes = {}
        ordered = []
        for _ in range(count):
            name, _super = r.many(2)
            flags = r.byte()
            if flags & 8:
                r.uint()
            r.many(r.uint())
            initializer = r.uint()
            traits = self.traits()
            key = self.qname(name)
            self.classes[key] = {'init': initializer, 'instance': traits}
            ordered.append(key)
        for key in ordered:
            self.classes[key]['class_init'] = r.uint()
            self.classes[key]['static'] = self.traits()
        for _ in range(r.uint()):
            r.uint()
            self.traits()
        self.body_prefix = data[:r.pos]
        self.sections['class_script_traits'] = data[start:r.pos]
        self.bodies = []
        for body_index in range(r.uint()):
            start = r.pos
            method, stack, locals_, scope, maxscope = r.many(5)
            length = r.uint()
            code_start = r.pos
            r.take(length)
            tail_start = r.pos
            exceptions = r.uint()
            r.many(5 * exceptions)
            self.traits()
            self.bodies.append({'index': body_index, 'method': method,
                'stack': stack, 'locals': locals_, 'scope': scope,
                'maxscope': maxscope, 'exceptions': exceptions,
                'code': data[code_start:code_start + length],
                'tail': data[tail_start:r.pos],
                'raw': data[start:r.pos]})
        if r.pos != len(data):
            raise ValueError(f'Trailing ABC bytes: {len(data) - r.pos}')

    def qname(self, index):
        kind, values = self.names[index]
        if kind not in (7, 13):
            raise ValueError('Expected QName')
        ns, name = values
        package = self.strings[self.namespaces[ns][1]]
        return '.'.join(filter(None, [package, self.strings[name]]))

    def traits(self):
        r = self.r
        output = []
        for _ in range(r.uint()):
            name, kind = r.uint(), r.byte()
            low = kind & 15
            method = None
            if low in (0, 6):
                _slot, _type, val = r.many(3)
                if val:
                    r.byte()
            elif low in (1, 2, 3, 5):
                _slot, method = r.many(2)
            elif low == 4:
                r.many(2)
            else:
                raise ValueError(f'Unsupported trait {low}')
            if kind & 64:
                r.many(r.uint())
            output.append({'name': self.qname(name), 'kind': low, 'method': method})
        return output


def abcs(path):
    result = []
    for index, (code, payload) in enumerate(swf_tags(path)):
        if code == 82:
            name_end = payload.index(b'\x00', 4)
            result.append((index, ABC(payload[name_end + 1:])))
    return result


if __name__ == '__main__':
    classname = sys.argv[2]
    found = 0
    for tag_index, abc in abcs(sys.argv[1]):
        if classname not in abc.classes:
            continue
        found += 1
        cls = abc.classes[classname]
        methods = cls['instance'] + cls['static']
        for trait in methods:
            if trait['method'] is None:
                continue
            bodies = [b for b in abc.bodies if b['method'] == trait['method']]
            for body in bodies:
                print(json.dumps({'tag': tag_index, 'class': classname,
                    'name': trait['name'], 'method_info': trait['method'],
                    'body_index': body['index'], 'code_length': len(body['code']),
                    'code_sha256': hashlib.sha256(body['code']).hexdigest()}, ensure_ascii=False))
    if found != 1:
        raise ValueError(f'Expected exactly one class, got {found}')
