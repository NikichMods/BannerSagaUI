# SPDX-License-Identifier: MPL-2.0
"""Strict AMF3 subset for observed string dictionaries; unsupported types fail closed."""
class Reader:
    def __init__(self, data):
        self.data=data; self.pos=0; self.strings=[]; self.objects=[]; self.traits=[]; self.spans={}
    def byte(self):
        b=self.data[self.pos]; self.pos+=1; return b
    def u29(self):
        n=0
        for i in range(4):
            b=self.byte()
            if i==3: return (n<<8)|b
            n=(n<<7)|(b&127)
            if b<128: return n
    def string(self):
        start=self.pos; n=self.u29()
        if not n&1: return self.strings[n>>1]
        length=n>>1; s=self.data[self.pos:self.pos+length].decode('utf-8'); self.pos+=length
        if s: self.strings.append(s); self.spans.setdefault(s,[]).append((start,self.pos))
        return s
    def value(self):
        t=self.byte()
        if t in (0,1): return None
        if t in (2,3): return t==3
        if t==4: return self.u29()
        if t==6: return self.string()
        if t!=10: raise ValueError(('unsupported',t,self.pos))
        n=self.u29()
        if not n&1: return self.objects[n>>1]
        if not n&2: traits=self.traits[n>>2]
        else:
            traits=(self.string(),bool(n&4),bool(n&8),[self.string() for _ in range(n>>4)]); self.traits.append(traits)
        name,external,dynamic,fields=traits
        if external: raise ValueError('externalizable')
        obj={}; self.objects.append(obj)
        for key in fields: obj[key]=self.value()
        if dynamic:
            while True:
                key=self.string()
                if not key: break
                obj[key]=self.value()
        return obj


    def read_all(self):
        result = self.value()
        if self.pos != len(self.data):
            raise ValueError("Trailing AMF3 bytes")
        return result

def u29(value):
    if not 0 <= value < (1 << 29):
        raise ValueError("Out of range U29")
    if value < 128: return bytes([value])
    if value < 16384: return bytes([(value >> 7) | 128, value & 127])
    if value < 2097152: return bytes([(value >> 14) | 128, ((value >> 7) & 127) | 128, value & 127])
    return bytes([((value >> 22) & 127) | 128, ((value >> 15) & 127) | 128, ((value >> 8) & 127) | 128, value & 255])
