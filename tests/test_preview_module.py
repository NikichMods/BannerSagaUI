# SPDX-License-Identifier: MPL-2.0
"""Boundary checks use only original project source and synthetic ABC fixtures."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/research'))
from preview_module_source import kernel, once, provider_source, needle_controller_source, needle_ui_controller_source, banner_ui_controller_source, ROW_EXTENSION
from compile_preview import test_swf as make_test_swf, validate_imports
from build_field_preview import add_abc, hooks, flag_hook
from abc_index import swf_tags
from test_swf_research import synthetic_abc
import tempfile


class PreviewModuleTests(unittest.TestCase):
    def test_ram_ui_extension_preserves_existing_calculation_boundary(self):
        original = (ROOT / 'src/bannersagaui/preview/FieldPreview.as').read_text(encoding='utf-8')
        previous = needle_ui_controller_source(original)
        shared = banner_ui_controller_source(original)
        start, end = 'private function calculate()', 'private function locate('
        self.assertEqual(previous[previous.index(start):previous.index(end)],
                         shared[shared.index(start):shared.index(end)])
        self.assertIn('ability.def.targetRule == BattleAbilityTargetRule.SPECIAL_BATTERING_RAM))', shared)

    def test_flag_hook_projects_only_request_operand(self):
        operand = 'getlocal1\ngetproperty QName(Namespace("engine.battle.board.model:IBattleEntity"),"battleInfoFlagVisible")\n'
        original = 'maxstack 2\ncode\ngetlocal0\npushscope\n' + operand + 'pop\nreturnvoid\nend ; code\n'
        patched = flag_hook(original)
        self.assertIn(operand, patched)
        self.assertIn('"requested"', patched)
        with self.assertRaises(ValueError):
            flag_hook(original.replace('battleInfoFlagVisible', 'changedOwner'))

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

    def test_optional_needle_probe_is_log_only_and_manager_observer_filters_identity(self):
        original = (ROOT / 'src/bannersagaui/preview/FieldPreview.as').read_text(encoding='utf-8')
        modified = needle_controller_source(original)
        self.assertNotIn('NeedlePreviewProbe', original)
        self.assertIn('BSUI_NEEDLE_QUERY', modified)
        self.assertIn('reason:"needle-query-log-only"', modified)
        self.assertIn('needleDispatcher.addEventListener(BattleAbilityEvent.ABILITY_AND_CHILDREN_COMPLETE', modified)
        self.assertIn('needleDispatcher.removeEventListener(', modified)
        self.assertIn('event.ability !== needleAction', modified)
        self.assertIn('BSUI_NEEDLE_OBSERVER_ARM', modified)
        self.assertIn('BSUI_NEEDLE_OBSERVER_EVENT', modified)
        self.assertIn('BSUI_NEEDLE_OBSERVER_PENDING', modified)
        self.assertIn('readNeedleActual(action, prediction);', modified)
        self.assertIn('BattleAbilityEvent.EXECUTING, needleExecuting', modified)
        self.assertIn('NeedleObservationMatch.reason(needleRequest, describeNeedleAction(actual))', modified)
        self.assertIn('BSUI_NEEDLE_OBSERVER_BIND', modified)
        self.assertIn('clearNeedleObservation();', modified.split('private function dispose():void {')[1])
        self.assertEqual(original[original.index('private function locate('):original.index('private function update(')],
                         modified[modified.index('private function locate('):modified.index('private function update(')])

    def test_needle_controller_refuses_changed_source_seam(self):
        original = (ROOT / 'src/bannersagaui/preview/FieldPreview.as').read_text(encoding='utf-8')
        with self.assertRaises(ValueError):
            needle_controller_source(original.replace('private var failed:Boolean = false;', ''))

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
