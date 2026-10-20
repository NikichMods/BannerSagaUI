# SPDX-License-Identifier: MPL-2.0
"""Synthetic format fixtures only; no game payload or extracted code."""
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from abc_index import ABC, Reader, swf_tags
from compare_swf import compare


def synthetic_abc(code=b'\x47', params=0, exception_target=None):
    # Tiny class with constructor, class initializer, and one method.
    data = b'\x10\x00\x2e\x00' + b'\x01' * 3
    data += b'\x03\x07Example\x06method'  # strings
    data += b'\x02\x16\x00\x01'  # namespace and empty namespace-set pool
    data += b'\x03\x07\x01\x01\x07\x01\x02'  # two QNames
    data += b'\x03' + b'\x00\x00\x00\x00' * 2
    data += bytes([params, 0]) + b'\x00' * params + b'\x00\x00'
    data += b'\x00\x01'  # metadata_count, class_count
    data += b'\x01\x00\x00\x00\x00\x01\x02\x01\x00\x02'
    data += b'\x01\x00\x00\x03'  # class init, traits, script count, body count
    for method in range(3):
        body = code if method == 2 else b'\x47'
        data += bytes([method, 1, params + 1 if method == 2 else 1, 0, 1, len(body)])
        data += body
        if method == 2 and exception_target is not None:
            data += bytes([1, 0, len(body), exception_target, 0, 0, 0])
        else:
            data += b'\x00\x00'
    return data


def synthetic_swf(abc, compressed=False, end=True):
    payload = b'\x00' * 5 + abc
    tag = struct.pack('<HI', (82 << 6) | 63, len(payload)) + payload
    body = b'\x08\x00\x00\x18\x01\x00' + tag + (b'\x00\x00' if end else b'')
    header = (b'CWS' if compressed else b'FWS') + b'\x10' + struct.pack('<I', len(body) + 8)
    return header + (zlib.compress(body) if compressed else body)


class SwfResearchTests(unittest.TestCase):
    def test_index_synthetic_class(self):
        abc = ABC(synthetic_abc())
        trait = abc.classes['Example']['instance'][0]
        self.assertEqual((trait['name'], trait['method']), ('method', 2))
        self.assertEqual(abc.bodies[2]['code'], b'\x47')

    def test_unknown_version_and_trailing_bytes_rejected(self):
        for data in (b'\x11' + synthetic_abc()[1:], synthetic_abc() + b'\0'):
            with self.assertRaises(ValueError):
                ABC(data)

    def test_truncation_and_u30_overflow_rejected(self):
        for data in (b'\x80', b'\xff\xff\xff\xff\x07'):
            with self.assertRaises(ValueError):
                Reader(data).uint()

    def compare_files(self, left, right):
        with tempfile.TemporaryDirectory() as root:
            a, b = Path(root) / 'a.swf', Path(root) / 'b.swf'
            a.write_bytes(left)
            b.write_bytes(right)
            before = (a.read_bytes(), b.read_bytes())
            report = compare(a, b)
            self.assertEqual(before, (a.read_bytes(), b.read_bytes()))
            return report

    def test_compression_difference_does_not_mean_content_difference(self):
        abc = synthetic_abc()
        result = self.compare_files(synthetic_swf(abc), synthetic_swf(abc, True))
        self.assertTrue(result['frame_header_equal'])
        self.assertEqual(result['changed_tags'], [])

    def test_one_body_change_is_identified(self):
        result = self.compare_files(synthetic_swf(synthetic_abc()),
            synthetic_swf(synthetic_abc(b'\x02\x47')))
        tag = result['changed_tags'][0]
        self.assertTrue(tag['prefix_equal'])
        self.assertEqual(tag['changed_method_info_count'], 0)
        self.assertEqual(tag['changed_body_count'], 1)
        self.assertEqual(tag['changed_bodies'][0]['index'], 2)

    def test_parameter_loss_is_visible_despite_same_instructions(self):
        result = self.compare_files(synthetic_swf(synthetic_abc(params=1)),
            synthetic_swf(synthetic_abc(params=0)))
        tag = result['changed_tags'][0]
        self.assertFalse(tag['prefix_equal'])
        self.assertEqual(tag['changed_method_info_count'], 1)

    def test_exception_changes_are_not_labelled_equal_metadata(self):
        result = self.compare_files(
            synthetic_swf(synthetic_abc(b'\x02\x47', exception_target=0)),
            synthetic_swf(synthetic_abc(b'\x02\x47', exception_target=1)))
        body = result['changed_tags'][0]['changed_bodies'][0]
        self.assertEqual(body['code_sha_before'], body['code_sha_after'])
        self.assertFalse(body['metadata_equal'])

    def test_missing_end_tag_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'invalid.swf'
            path.write_bytes(synthetic_swf(synthetic_abc(), end=False))
            with self.assertRaisesRegex(ValueError, 'Missing End'):
                swf_tags(path)
