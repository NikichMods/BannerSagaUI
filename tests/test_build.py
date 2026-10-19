# SPDX-License-Identifier: MPL-2.0
import hashlib
from pathlib import Path
import sys
import unittest
import zlib
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from amf3 import Reader, u29
from build import patch, NEW, KEY

def string(s):
    b=s.encode('utf-8'); return u29(len(b)*2+1)+b

def fixture():
    # Independent hand-built AMF3 dynamic object; uses a string reference
    # after the changed value to exercise preserved reference numbering.
    return b'\x0a\x0b\x01'+string('GUI')+b'\x0a\x01'+string(KEY)+b'\x06'+string('old')+string('unrelated')+b'\x06'+string('keep')+b'\x01'+string('other')+b'\x06\x08\x01'

class BuildTests(unittest.TestCase):
    def test_semantics_and_utf8_length(self):
        source=zlib.compress(fixture())
        result,_=patch(source,hashlib.sha256(source).hexdigest())
        self.assertEqual(Reader(zlib.decompress(result)).read_all(), {'GUI':{KEY:NEW,'unrelated':'keep'},'other':'keep'})
    def test_reject_unknown_baseline(self):
        with self.assertRaises(ValueError): patch(zlib.compress(fixture()),'0'*64)
    def test_reject_unknown_amf_type_and_trailing_bytes(self):
        for raw in (b'\x09',b'\x01\x00'):
            with self.assertRaises(ValueError): Reader(raw).read_all()
    def test_u29_boundaries(self):
        for n in (0,127,128,16383,16384,2097151,2097152,(1<<29)-1):
            self.assertEqual(Reader(u29(n)).u29(),n)
    def test_shared_string_changes_rejected(self):
        raw=fixture().replace(b'\x06\x08\x01',b'\x06\x04\x01')
        source=zlib.compress(raw)
        with self.assertRaises(ValueError): patch(source,hashlib.sha256(source).hexdigest())

if __name__=='__main__': unittest.main()
