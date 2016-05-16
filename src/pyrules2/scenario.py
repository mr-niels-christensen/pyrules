__author__ = 'nhc'


class Scenario(frozenset):
    """
    A Scenario is essentially a frozendict, see http://stackoverflow.com/a/9997296/1095455
    It is an immutable and hashable dict.
    TODO: Make into a collections.Mapping, see
    http://stackoverflow.com/questions/3387691/python-how-to-perfectly-override-a-dict
    http://stackoverflow.com/questions/3385269/how-to-wrap-a-python-dict
    """
    def __new__(cls, d):
        """
        Creates a frozenset of d.items()
        :param cls: This class
        :param d: A dict with immutable, hashable values. Example: {'a': 'b'}
        :return: The created frozenset
        """
        assert isinstance(d, dict)
        return super(Scenario, cls).__new__(cls, list(d.items()))

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
    def unite(scenarios):
        """
        Computes the union of Scenarios.
        Note: Should not be named union() because this would shadow frozenset.union
        :param scenarios A tuple or list of Scenarios
        :return The union of the Scenarios
        :raises AssertionError if two Scenarios defined different values for
        the same key.
        """
        assert len(scenarios) > 0
        assert all([isinstance(s, Scenario) for s in scenarios])
        if len(scenarios) == 1:
            return scenarios[0]
        result_as_set = scenarios[0].union(*scenarios[1:])
        keys = set((key for key, value in result_as_set))
        assert len(keys) == len(result_as_set)
        return Scenario(dict(result_as_set))
