from typing import List, Union


class LogicalVector:
    """
    Logical vector, a vector of a single 1 and all other 0
    When Logical vector is used to represent the state of BCNs, only those vectors whose dims are a power of 2 are legal.
    """

    def __init__(self, pos: int, dim: int):
        """
        :param pos: can be integer in `[1, dim]`, indicates the position of 1 in the logical vector
        :param dim: the dimensionality of the logical vector, must be a power of 2
        :return:  a `LogicalVector` instance
        """
        assert (dim & (dim - 1) ==
                0) and dim != 0, f"Ilegal value for dim: {dim}, must be power of 2"
        self.pos = pos
        self.dim = dim

    def to_list(self) -> list:
        """
        Convert to vector form.
        :return: the corresponding state list
        """
        result = []
        pos = self.pos
        dim = self.dim
        while dim != 1:
            if pos <= dim // 2:
                result.append(1)
            else:
                result.append(0)
            dim = dim // 2
            pos = (pos - 1) % dim + 1
        return result

    @classmethod
    def from_list(cls, l: List[int]):
        """
        Return a `LogicalVector` instance with give list consisting of 0s and 1
        :param l: a list consisting of 0s and 1
        """
        assert sum(l) == 1, f"should only contain one 1"
        pos = None
        for index, num in enumerate(l):
            assert num == 0 or num == 1, f"should only contain 0 or 1"
            if num == 1:
                pos = index + 1
        return cls(pos, len(l))

    @classmethod
    def from_integer(cls, val: int):
        """
        :param val: can be only 0 or 1
        """
        assert val == 0 or val == 1, f"got {val}, should be 0 or 1"
        return cls(2 - val, 2)

    @classmethod
    def from_states(cls, l: List[int]):
        """
        :param l: a list of states consisting of 1 or 0
        """
        assert len(l) != 0, f"l cannot be empty"
        l = list(map(lambda i: cls.from_integer(i), l))
        return l[0] * l[1:]

    def __eq__(self, o):
        if isinstance(o, LogicalVector) and self.dim == o.dim and self.pos == o.pos:
            return True
        return False

    def __str__(self):
        return f"LogicalVector({self.pos}, {self.dim})"

    def __repr__(self):
        return str(self)

    def __mul__(self, o):
        if isinstance(o, LogicalVector):
            pos = (self.pos - 1) * o.dim + o.pos
            dim = self.dim * o.dim
            return LogicalVector(pos, dim)
        elif isinstance(o, List):
            if len(o) == 0:
                return self
            return (self * o[0]) * o[1:]
