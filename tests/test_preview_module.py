# SPDX-License-Identifier: MPL-2.0
"""Boundary checks use only original project source and synthetic ABC fixtures."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/research'))
from preview_module_source import kernel, once, provider_source, ROW_EXTENSION
from compile_preview import test_swf as make_test_swf, validate_imports
from build_field_preview import add_abc, hooks
from abc_index import swf_tags
from test_swf_research import synthetic_abc
import tempfile


class PreviewModuleTests(unittest.TestCase):
    def test_direct_api_preserves_calculation_and_restoration(self):
        original = (ROOT / 'tools/research/ram_probe_body.as.inc').read_text(encoding='utf-8')
        direct = provider_source(ROOT)
        self.assertEqual(kernel(original), kernel(direct).replace(ROW_EXTENSION, '', 1))
        self.assertNotIn('BSUI_RAM_', direct)
        self.assertNotIn('param4', direct)
        self.assertIn('return {status:outputStatus', direct)

    def test_boundary_drift_rejected(self):
        for source in ['', 'x x']:
            with self.assertRaises(ValueError):
                once(source, 'x', 'y')

    def test_missing_native_import_rejected(self):
        with self.assertRaises(ValueError):
            validate_imports(['import engine.Wrong;'], {'engine.Right'}, set())
        self.assertEqual(validate_imports(['import engine.Right; import flash.display.Sprite;'],
                                         {'engine.Right'}, set()),
                         ['engine.Right', 'flash.display.Sprite'])

    def test_own_import_allowed(self):
        self.assertEqual(validate_imports(['import own.Frame;'], set(), {'own.Frame'}), ['own.Frame'])

    def test_harness_has_only_original_abc(self):
        abc = synthetic_abc()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'test.swf'
            path.write_bytes(make_test_swf(abc))
            tags = list(swf_tags(path))
        self.assertEqual([code for code, _ in tags], [69, 82, 76, 1, 0])
        self.assertEqual(tags[1][1], b'\x00' * 4 + b'bsui_tests\0' + abc)

    def test_module_insertion_preserves_every_existing_tag(self):
        module = synthetic_abc(b'\x02\x47')
        with tempfile.TemporaryDirectory() as folder:
            source, dest = Path(folder) / 'source.swf', Path(folder) / 'dest.swf'
            source.write_bytes(make_test_swf(synthetic_abc()))
            position = add_abc(source, dest, module)
            before, after = list(swf_tags(source)), list(swf_tags(dest))
        self.assertEqual(after.pop(position), (82, b'\x00' * 4 + b'BannerSagaUIFieldPreview\0' + module))
        self.assertEqual(before, after)

    def test_update_hook_preserves_native_early_exit(self):
        header = 'maxstack 1\nlocalcount 2\ninitscopedepth 0\nmaxscopedepth 1\ncode\n'
        original = header + ('getlocal0\npushscope\ngetlocal1\niftrue ready\nreturnvoid\n'
                             'ready:\nreturnvoid\nend ; code\n')
        patched = hooks({'update': original})['update']
        self.assertIn('iftrue ready\nreturnvoid\nready:\ngetlex ', patched)
        self.assertEqual(patched.count('callpropvoid '), 1)

    def test_unknown_cleanup_seam_rejected(self):
        with self.assertRaises(ValueError):
            hooks({'cleanup': 'maxstack 1\ncode\nreturnvoid\nend ; code\n'})
