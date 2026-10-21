# SPDX-License-Identifier: MPL-2.0
"""Synthetic control-flow cases; no host p-code fixtures."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools' / 'research'))
from check_pcode_stack import check, require_balanced


def method(code, exceptions='', limit=4):
    return f'body\nmaxstack {limit}\ncode\n{code}end ; code\n{exceptions}end ; body\n'


class StackHeightTests(unittest.TestCase):
    def test_handler_loses_finally_discriminator(self):
        # Normal flow retains a finally dispatcher value. An exception clears
        # it, so joining these paths is invalid even when the body parses.
        text = method('pushbyte -1\nstart:\npushnull\nthrow\nend_try:\n'
                      'jump join\nhandler:\npop\njump join\njoin:\n'
                      'lookupswitch done, [done]\ndone:\nreturnvoid\n',
                      'try from start to end_try target handler type null name null end\n')
        self.assertTrue(check(text)['issues'])
        with self.assertRaises(ValueError): require_balanced(text)

    def test_common_cleanup_with_catch_all_has_balanced_paths(self):
        text = method('start:\npushtrue\niffalse end_try\npushnull\nthrow\n'
                      'end_try:\njump cleanup\nhandler:\npop\n'
                      'cleanup:\npushfalse\nsetlocal1\nreturnvoid\n',
                      'try from start to end_try target handler type null name null end\n')
        self.assertEqual(require_balanced(text)['issues'], [])

    def test_branch_height_mismatch_is_rejected(self):
        text = method('pushtrue\niftrue join\npushnull\njoin:\nreturnvoid\n')
        self.assertTrue(any(x[0] == 'merge' for x in check(text)['issues']))

    def test_stack_limit_and_underflow_are_rejected(self):
        for text in (method('pushtrue\nreturnvalue\n', limit=0),
                     method('pop\nreturnvoid\n')):
            with self.assertRaises(ValueError): require_balanced(text)

    def test_unknown_opcode_is_rejected(self):
        with self.assertRaises(ValueError): require_balanced(method('unsupported_op\n'))

    def test_class_definition_consumes_base_and_returns_class(self):
        require_balanced(method('pushnull\nnewclass 0\npop\nreturnvoid\n', limit=1))
        with self.assertRaises(ValueError):
            require_balanced(method('newclass 0\nreturnvalue\n'))


if __name__ == '__main__':
    unittest.main()
