# SPDX-License-Identifier: MPL-2.0
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'/'research'))
from analyze_ram_probe import analyze
from build_ram_probe import canonical, verify_stock_branch, verify_host_imports


class ProbeComparisonTests(unittest.TestCase):
    def record(self,marker,payload):
        return '[INFO] 123 '+marker+' '+json.dumps(payload)

    def scenario(self):
        row = {'id':'synthetic','x':4,'y':1,'armorBefore':7,'armor':5,
            'armorBase':5,'strength':8,'auraBefore':1,'auraAfter':0}
        prediction = {'status':'UNVERIFIED','entered':True,'restored':True,
            'caster':'source','target':'synthetic','level':1,'damageApplications':1,'rows':[row]}
        actual = {'trigger':'synthetic','rows':[dict(row)]}
        return prediction,actual

    def test_compares_only_after_native_ram_execution(self):
        prediction,actual = self.scenario()
        lines = [self.record('BSUI_RAM_PROBE',prediction),
            self.record('BSUI_RAM_IDLE',actual),
            '[INFO] Execute [1 source->{synthetic} abl_batteringram/1]',
            self.record('BSUI_RAM_IDLE',actual)]
        result = analyze(lines)
        self.assertEqual(result['comparable_sample_count'],1)
        self.assertEqual(result['samples'][0]['actual_line'],4)
        self.assertEqual(result['samples'][0]['status'],'MATCH')

    def test_detects_wrong_aura_result(self):
        prediction,actual = self.scenario()
        actual['rows'][0]['armor'] = 6
        result = analyze([self.record('BSUI_RAM_PROBE',prediction),
            'Execute [1 source->{synthetic} abl_batteringram/1]',self.record('BSUI_RAM_IDLE',actual)])
        self.assertEqual(result['samples'][0]['status'],'MISMATCH')
        self.assertEqual(result['samples'][0]['differences'][0]['field'],'armor')

    def test_unsupported_and_failed_restoration_never_pass(self):
        for status,restored in [('UNSUPPORTED',True),('UNVERIFIED',False),('ERROR',True)]:
            prediction,actual = self.scenario()
            prediction.update(status=status,restored=restored)
            result = analyze([self.record('BSUI_RAM_PROBE',prediction),
                'Execute [1 source->{synthetic} abl_batteringram/1]',self.record('BSUI_RAM_IDLE',actual)])
            self.assertEqual(result['comparable_sample_count'],0)
            self.assertEqual(len(result['skipped']),1)

    def test_cancelled_prediction_does_not_match_a_later_action(self):
        prediction,actual = self.scenario()
        result = analyze([self.record('BSUI_RAM_PROBE',prediction),
            'Execute [1 source->{synthetic} abl_attack/1]',
            'Execute [2 source->{synthetic} abl_batteringram/1]',self.record('BSUI_RAM_IDLE',actual)])
        self.assertEqual(result['comparable_sample_count'],0)

    def test_execution_without_idle_is_incomplete(self):
        prediction,_ = self.scenario()
        result = analyze([self.record('BSUI_RAM_PROBE',prediction),
            'Execute [1 source->{synthetic} abl_batteringram/1]'])
        self.assertTrue(result['awaiting_native_completion'])
        self.assertEqual(result['comparable_sample_count'],0)

    def test_prediction_for_another_target_never_passes(self):
        prediction,actual = self.scenario()
        result = analyze([self.record('BSUI_RAM_PROBE',prediction),
            'Execute [1 source->{another} abl_batteringram/1]',self.record('BSUI_RAM_IDLE',actual)])
        self.assertEqual(result['comparable_sample_count'],0)
        self.assertEqual(result['skipped'][0]['status'],'IDENTITY_MISMATCH')


class PcodePreservationTests(unittest.TestCase):
    def test_wrong_import_package_is_rejected(self):
        with self.assertRaises(ValueError):
            verify_host_imports(['synthetic.wrong.Reason'], {'synthetic.correct.Reason'})

    def test_runtime_import_and_exact_host_class_are_allowed(self):
        verify_host_imports(['synthetic.correct.Reason', 'flash.utils.Dictionary'],
                            {'synthetic.correct.Reason'})

    def test_unknown_runtime_import_is_not_silently_allowed(self):
        with self.assertRaises(ValueError):
            verify_host_imports(['flash.unknown.NotVerified'], set())

    def test_labels_resolve_independently_of_offsets(self):
        left = canonical('getlocal0\niftrue ofs0010\npushfalse\nreturnvalue\nofs0010:\npushtrue\nreturnvalue\n',[])
        right = canonical('getlocal0\niftrue ofs0020\npushfalse\nreturnvalue\nofs0020:\npushtrue\nreturnvalue\n',[])
        self.assertEqual(left,right)

    def test_modified_native_branch_is_rejected(self):
        original = 'body\ncode\ngetlocal0\npushtrue\nreturnvalue\nend ; code\nend ; body\n'
        result = 'body\ncode\ngetlocal3\niftrue ofs0010\npushfalse\nreturnvalue\nofs0010:\ngetlocal0\npushfalse\nreturnvalue\nend ; code\nend ; body\n'
        with self.assertRaises(ValueError): verify_stock_branch(original,result)


if __name__ == '__main__':
    unittest.main()
