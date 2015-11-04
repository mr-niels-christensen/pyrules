from collections import defaultdict

__author__ = 'nhc'


class Scenario(frozenset):
    """
    A Scenario is essentially a frozendict, see http://stackoverflow.com/a/9997296/1095455
    It is an immutable and hashable dict.
    """
    def __new__(cls, d):
        """
        Creates a frozenset of d.items()
        :param cls: This class
        :param d: A dict with immutable, hashable values. Example: {'a': 'b'}
        :return: The created frozenset
        """
        assert isinstance(d, dict)
        return super(Scenario, cls).__new__(cls, d.items())

    def get_only_item(self):
        """
        Verifies that this is a singleton Scenario and returns its only item.
        :return: The only item in this Scenario, e.g. ('a', 'b')
        :raises AssertionError if len(self) != 1
        """
        assert len(self) == 1
        for item in self:
            return item

    def as_dict(self):
        """
        Converts Scenario to dict
        :return: A dict equal to the one used to create this Scenario,
        e.g. {'a': 'b'}
        """
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
