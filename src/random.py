class Random:
    """ Realy poor random number generator. But 0will help keep the
    code deterministic
    """
    def __init__(self, seed):
        self.seed = seed

    def integer(self, low, high):
        """ Return a pseudorandom number from interval [low, high]
        """
        self.seed *= 65537
        self.seed %= 3571
        return self.seed % (high - low + 1) + low
