import unittest
from hurry.workflow.workflow import Transition


class TransitionOrderingTest(unittest.TestCase):

    def test_sorting(self):
        a = Transition('a', 'A', None, None, order=0)
        b = Transition('b', 'B', None, None, order=1)
        c = Transition('c', 'C', None, None, order=2)
        self.assertTrue(a < b)
        self.assertTrue(b < c)
        self.assertTrue(c > a)

    def test_sorting_with_equal_order(self):
        a = Transition('a', 'A', None, None, order=0)
        b = Transition('b', 'B', None, None, order=0)
        self.assertFalse(a < b)
        self.assertTrue(a <= b)
        self.assertTrue(b >= a)
        self.assertTrue(b <= a)

    def test_equality(self):
        # sorting equality does not imply identity
        a = Transition('a', 'A', None, None, order=0)
        b = Transition('b', 'B', None, None, order=0)
        self.assertTrue(a == b)
