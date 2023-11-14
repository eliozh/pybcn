import unittest

from ply.lex import LexToken

from pybcn.logical_vector import *


class TestLogicalVector(unittest.TestCase):
    def test_init(self):
        self.assertRaises(AssertionError, LogicalVector, 1, 3)

    def test_to_list(self):
        self.assertEqual(LogicalVector(1, 4).to_list(), [1, 1])
        self.assertEqual(LogicalVector(2, 4).to_list(), [1, 0])
        self.assertEqual(LogicalVector(3, 4).to_list(), [0, 1])
        self.assertEqual(LogicalVector(4, 4).to_list(), [0, 0])
        self.assertEqual(LogicalVector(3, 8).to_list(), [1, 0, 1])

    def test_from_list(self):
        self.assertEqual(LogicalVector.from_list(
            [0, 0, 0, 1]), LogicalVector(4, 4))
        self.assertRaises(
            AssertionError, LogicalVector.from_list, [1, 1, 0, 0])
        self.assertRaises(
            AssertionError, LogicalVector.from_list, [1, 1, 0, -1])

    def test_from_integer(self):
        self.assertEqual(LogicalVector.from_integer(1), LogicalVector(1, 2))
        self.assertEqual(LogicalVector.from_integer(0), LogicalVector(2, 2))

    def test_mul(self):
        self.assertEqual(LogicalVector(2, 4) *
                         LogicalVector(2, 2), LogicalVector(4, 8))
        l = [LogicalVector(1, 2)] * 3
        self.assertEqual(LogicalVector(2, 2) * l, LogicalVector(9, 16))

    def test_from_states(self):
        self.assertEqual(LogicalVector.from_states(
            [0, 0, 0]), LogicalVector(8, 8))

    def test_eq(self):
        self.assertTrue(LogicalVector(5, 16) == LogicalVector(5, 16))
        self.assertFalse(LogicalVector(5, 16) == 1)
