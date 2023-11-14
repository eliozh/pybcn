import unittest

from pybcn.lexer import *


class TestLY(unittest.TestCase):
    def test_lexer(self):
        lexer.input("x3 & ( x1 | x2) ^ x4")
        tokens = lexer.get_all_tokens()
        self.assertEqual(len(tokens), 9)
        self.assertEqual(tokens[0].value, "x3")
        self.assertEqual(tokens[1].value, "&")
        self.assertEqual(tokens[2].value, "(")
        self.assertEqual(tokens[3].value, "x1")
        self.assertEqual(tokens[4].value, "|")
        self.assertEqual(tokens[5].value, "x2")
        self.assertEqual(tokens[6].value, ")")
        self.assertEqual(tokens[7].value, "^")
        self.assertEqual(tokens[8].value, "x4")
