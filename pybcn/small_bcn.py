import sys
from collections import deque
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
        self.d = d
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

    def set_states_i(self, states: int):
        states_v = LogicalVector(states, self.N).to_list()
        states_formatted = dict(zip(self.variables, states_v))
        self.states = states_formatted

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

    def get_inputs(self, inputs):
        if isinstance(inputs, int):
            input_l = LogicalVector(inputs, self.M).to_list()
            return dict(zip(self.input_variables, input_l))
        elif isinstance(inputs, dict):
            inputs_formatted = {}
            for input_var in self.input_variables:
                inputs_formatted[input_var] = inputs[input_var]
            return LogicalVector.from_states(list(inputs_formatted.values())).pos

    def next_state(self, state, inputs):
        return self.L[(inputs - 1) * self.N + state - 1]

    def one_step_states(self, state: int):
        """
        return the states that can be reached from current state in one step.
        :param state: current state
        :return: the states and the corresponding inputs
        """
        res = {}
        for k in range(self.M):
            r = self.L[k * self.N + state - 1]
            if r not in res:
                res[r] = []
            res[r].append(k + 1)

        return res

    def optimal_time_control(self, init: int, dest: int):
        """
        Optimal Time Control with BFS.
        :param init: pos of corresponding vector of initial state
        :param dest: pos of corresponding vector of destination state
        """
        s = set((init,))
        q = deque([(init, [init], [])])
        T = sys.maxsize
        res = []

        while len(q) != 0:
            state, seq, c_seq = q.popleft()
            if len(seq) >= T:
                continue
            for next_state, inputs in self.one_step_states(state).items():
                new_seq = seq + [next_state]
                new_c_seq = c_seq + [inputs]
                if next_state == dest:
                    T = len(seq)
                    res.append((new_seq, new_c_seq))
                if next_state not in s:
                    s.add(next_state)
                    q.append((next_state, new_seq, new_c_seq))
        return T, res

    def optimal_time_control_2(self, init: int, dest: int):
        T = 0
        q = deque([(init, [init], [])])
        res = []
        flag = True

        while flag:
            T += 1
            while len(q[0][1]) == T:
                state, seq, c_seq = q.popleft()
                for next_state, inputs in self.one_step_states(state).items():
                    new_seq = seq + [next_state]
                    new_c_seq = c_seq + [inputs]
                    q.append((next_state, new_seq, new_c_seq))

            for i in q:
                if i[0] == dest:
                    res.append((i[1], i[2]))
                    flag = False

        return T, res

    def __str__(self):
        return f"{{variables: {self.variables}, inputs: {self.input_variables}, states: {list(self.states.values())}}}"
