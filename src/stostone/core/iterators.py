import itertools

class stcombos:
    """Class to implement an iterator of (s,t)-combinations which are
    binary strings containing s copies of 0 and t copies of 1.  These strings
    are in one-to-one correspondence with subsets of size t of {0,1,...,s+t-1}
    which are generated using itertools.combinations."""

    def __init__(self, s = 0, t = 0):
        self.s = s
        self.t = t
        self.n = s+t

    def __iter__(self):
        self.combinations = itertools.combinations(list(range(self.n)), self.t)
        return self

    def __next__(self):
        # Get the next combination from itertools.combinations.
        combo = next(self.combinations)

        # Convert the combination to an incidence vector.
        return [int(i in combo) for i in range(self.n)]

    # This is for compatibility with Python 2.
    next = __next__
