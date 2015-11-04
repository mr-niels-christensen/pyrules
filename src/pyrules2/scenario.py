from collections import defaultdict

__author__ = 'nhc'


class Scenario(frozenset):
    def __new__(cls, d):
        assert isinstance(d, dict)
        return super(Scenario, cls).__new__(cls, d.items())

    def get_only_item(self):
        assert len(self) == 1
        for item in self:
            return item

    def as_dict(self):
        return dict(self)

    @staticmethod
    def union(scenarios):
        """
        :param scenarios A tuple or list of Scenarios
        :return The union of the Scenarios
        :raises AssertionError if two Scenarios defined different values for
        the same key.
        """
        assert len(scenarios) > 0
        assert all([isinstance(s, Scenario) for s in scenarios])
        accumulator = defaultdict(set)
        for scenario in scenarios:
            for item in scenario:
                key, value = item
                accumulator[key].add(value)
        result_as_dict = dict()
        for key, value_set in accumulator.iteritems():
            assert len(value_set) == 1
            result_as_dict[key] = value_set.pop()
        return Scenario(result_as_dict)
