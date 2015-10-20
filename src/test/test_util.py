import unittest
from pyrules2.util import lazy_product
from itertools import product, count, repeat, islice


class Test(unittest.TestCase):
    def test_finite_product(self):
        self._test_product([])
        for num_iterables in [1, 2, 5]:
            iterables = [range(i*i) for i in range(1, num_iterables+1)]
            self._test_product(iterables)

    def _test_product(self, case):
        self.assertSetEqual(set(product(*case)), set(lazy_product(*case)))

    def test_infinite_product(self):
        g = lazy_product(count(0), [1])
        sliced = islice(g, 100)
        slice_as_set = set(sliced)
        self.assertSetEqual(set((i, 1) for i in range(100)), slice_as_set)

if __name__ == "__main__":
    unittest.main()
