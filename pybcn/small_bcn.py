from itertools import product
from typing import List, Mapping, Optional, Union

from pybcn.lexer import lexer
from pybcn.logical_vector import LogicalVector


class SmallBCN:
    """
    Small-scale Boolean Control Network
    """

    def __init__(self, d: Mapping[str, str], init_states: Optional[List[int]] = None):
        """
        Generate a SmallBCN instance.

        :param d: a dict with structure '<variable, expression>'
        :param init_states: initial states, set to all 0 if it is None
        :return: a SmallBCN instance
        """
        self.variables = []
        self.list_of_tokens = {}
        self.input_variables = []
        self.states = {}
        self.n = None  # number of state variables
        self.m = None  # number of input variables
        self.N = None  # equals to 2 ** n
        self.M = None  # equals to 2 ** m

        self._generate(d, init_states)

    def _generate(self, d: Mapping[str, str], init_states: Optional[List[int]] = None):
        """
        :param d: a dict with structure '<variable, expression>'
        :param init_states: initial states, set to all 0 if it is None
        :return: a SmallBCN instance
        """
        self.variables = list(d.keys())
        self.n = len(self.variables)
        self.N = 2 ** self.n
        for var, expr in d.items():
            lexer.input(expr)
            tokens = lexer.get_all_tokens()
            self.list_of_tokens[var] = tokens
            self.input_variables.extend(map(
                lambda t: t.value,
                filter(
                    lambda t: t.value not in self.variables
                    and t.value not in self.input_variables
                    and t.type == "VARIABLE",
                    tokens
                )
            ))
        self.m = len(self.input_variables)
        self.M = 2 ** self.m

        self._generate_assr()

        if init_states is None:
            self.states = dict(zip(self.variables, [0] * len(self.variables)))
            return
        assert len(self.variables) == len(
            init_states), f"the number of states and variables must be the same, but we got {len(self.states)} and {len(init_states)}"
        for var, state in zip(self.variables, init_states):
            assert state == 0 or state == 1, f"state should be 0 or 1, got {state}"
            self.states[var] = state

    def _generate_assr(self):
        """
        Generate Algebraic State Space Representation (ASSR) of the BCN.
        """
        L = [0] * (self.M * self.N)
        for state_l in product(*([[0, 1]] * self.n)):
            for input_l in product(*([[0, 1]] * self.m)):
                state_v = LogicalVector.from_states(list(state_l))
                input_v = LogicalVector.from_states(list(input_l))

                self.set_states(dict(zip(self.variables, state_l)))
                inputs = dict(zip(self.input_variables, input_l))
                self.update_network(inputs)

                next_state_l = self.get_states("list")
                next_state_v = LogicalVector.from_states(next_state_l)

                i = state_v.pos - 1
                j = input_v.pos - 1
                L[i + j * self.N] = next_state_v.pos

        self.L = L

    def update_variable(self, variable: str, inputs: Mapping[str, int]) -> int:
        """
        Update the state of a variable with given inputs.
        :param variable: name of the variable
        :param inputs: a dict with structure '<input_variable, value>'
        :return: the updated value
        """
        tokens = self.list_of_tokens[variable]
        expression = []
        for t in tokens:
            if t.type == "VARIABLE":
                if t.value in self.variables:
                    expression.append(str(self.states[t.value]))
                elif t.value in self.input_variables:
                    expression.append(str(inputs[t.value]))
            elif t.type == "AND":
                expression.append("&")
            elif t.type == "OR":
                expression.append("|")
            elif t.type == "XOR":
                expression.append("^")
            elif t.type == "NOT":
                expression.append("not")
            else:
                expression.append(t.value)
        return int(eval(" ".join(expression)))

    def update_network(self, inputs: Mapping[str, int]):
        """
        Update the state of the network with given inputs.
        :param inputs: a dict with structure '<input_variable, value>'
        """
        new_states = {}
        for variable in self.variables:
            state = self.update_variable(variable, inputs)
            new_states[variable] = state
        self.set_states(new_states)

    def set_states(self, states: Mapping[str, int]):
        """
        Set the states of the variables.
        Make sure the order of states remains.
        :param state: <variable, value>
        """
        states_formatted = {}
        try:
            for var in self.variables:
                states_formatted[var] = states[var]
        except KeyError as e:
            raise AssertionError(f"state missed key(s), {e}")
        self.states = states_formatted

    def get_states(self, format: Union["list", "dict"]) -> Union[List, Mapping]:
        if format == "list":
            return list(self.states.values())
        elif format == "dict":
            return self.states
        else:
            raise AssertionError(f"format should be 'list' or 'dict'")

    def __str__(self):
        return f"{{variables: {self.variables}, inputs: {self.input_variables}, states: {list(self.states.values())}}}"
