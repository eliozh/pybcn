import unittest

from pybcn.small_bcn import *


class TestSmallBCN(unittest.TestCase):
    def test_init(self):
        d = {"x1": "x2 & x3 ^ u1", "x2": "x1 | x3", "x3": "x1 & u2"}
        self.assertRaises(AssertionError, SmallBCN, d, [1])
        self.assertRaises(AssertionError, SmallBCN, d, [1, 0, 2])
        bcn = SmallBCN(d, [1, 0, 1])
        self.assertEqual(bcn.variables, ["x1", "x2", "x3"])
        self.assertEqual(bcn.input_variables, ["u1", "u2"])
        self.assertEqual(bcn.states, {"x1": 1, "x2": 0, "x3": 1})

    def test_update_variable(self):
        d = {"x1": "x2 & x3 ^ u1", "x2": "x1 | x3", "x3": "x1 & u2"}
        bcn = SmallBCN(d, [1, 0, 1])
        self.assertEqual(bcn.update_variable("x1", {"u1": 1, "u2": 0}), 1)

    def test_set_states(self):
        d = {"x1": "x2 & x3 ^ u1", "x2": "x1 | x3", "x3": "x1 & u2"}
        bcn = SmallBCN(d, [1, 0, 1])
        bcn.set_states({"x2": 1, "x3": 1, "x1": 0, "x4": 0})
        self.assertEqual(bcn.states, {"x1": 0, "x2": 1, "x3": 1})
        self.assertRaises(AssertionError, bcn.set_states, {"x1": 1, "x2": 1})

    def test_get_states(self):
        d = {"x1": "x2 & x3 ^ u1", "x2": "x1 | x3", "x3": "x1 & u2"}
        bcn = SmallBCN(d, [1, 0, 1])
        self.assertEqual(bcn.get_states("list"), [1, 0, 1])
        self.assertEqual(bcn.get_states("dict"), {"x1": 1, "x2": 0, "x3": 1})
        self.assertRaises(AssertionError, bcn.get_states, "foo")

    def test_update_network(self):
        d = {"x1": "x2 & x3 ^ u1", "x2": "x1 | x3", "x3": "x1 & u2"}
        bcn = SmallBCN(d, [1, 0, 1])
        bcn.update_network({"u1": 1, "u2": 0})
        self.assertEqual(bcn.get_states("list"), [1, 1, 0])

    def test_generate_assr(self):
        d = {"x1": "x2 | x3", "x2": "x1 & u1", "x3": "(u1 | x2) & (!x1)"}
        bcn = SmallBCN(d)
        self.assertEqual(
            bcn.L,
            [2, 2, 2, 6, 3, 3, 3, 7, 4, 4, 4, 8, 3, 3, 4, 8]
        )

    def test_one_step_states(self):
        d = {"x1": "x2 | x3", "x2": "x1 & u1", "x3": "(u1 | x2) & (!x1)"}
        bcn = SmallBCN(d)
        states = list(bcn.one_step_states(8))
        self.assertEqual(
            states,
            [(7, 1), (8, 2)]
        )
