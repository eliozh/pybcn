import sys
import copy
import rustworkx as rx
from collections import deque
from itertools import product
from typing import List, Mapping, Optional, Union
from rustworkx.visualization import graphviz_draw

from pybcn.lexer import lexer
from pybcn.logical_vector import LogicalVector
from pybcn.small_bcn import SmallBCN


class LargeBCN:
    """
    Large-scale Boolean Control Network
    """

    def __init__(self, d: Mapping[str, str], init_states: Optional[List[int]] = None):
        """
        Generate a LargeBCN instance.

        :param d: a dict with structure '<variable, expression>'
        :param init_states: initial states, set to all 0 if it is None
        :return: a LargeBCN instance
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

        if init_states is None:
            self.states = dict(zip(self.variables, [0] * len(self.variables)))
            return
        assert len(self.variables) == len(
            init_states), f"the number of states and variables must be the same, but we got {len(self.states)} and {len(init_states)}"
        for var, state in zip(self.variables, init_states):
            assert state == 0 or state == 1, f"state should be 0 or 1, got {state}"
            self.states[var] = state

    def partition(self):
        dag = rx.PyDiGraph()
        indices = dag.add_nodes_from(self.variables)
        variable_indices = dict(zip(self.variables, indices))
        
        for var, tokens in self.list_of_tokens.items():
            for tok in tokens:
                if tok.value in self.variables:
                    dag.add_edge(variable_indices[tok.value], variable_indices[var], None)

        sccs = rx.strongly_connected_components(dag)

        condensation_graph = rx.PyDiGraph()
        indices = condensation_graph.add_nodes_from(list(range(len(sccs))))
        node_index_to_block_index = {}
        for block_index, scc in enumerate(sccs):
            for i in scc:
                node_index_to_block_index[i] = block_index
        for edge in dag.edge_list():
            start_block_idx = node_index_to_block_index[edge[0]]
            end_block_idx = node_index_to_block_index[edge[1]]
            if (not condensation_graph.has_edge(start_block_idx, end_block_idx)
                and start_block_idx != end_block_idx):
                condensation_graph.add_edge(start_block_idx, end_block_idx, None)

        self.condensation_graph = condensation_graph

        topo_seq = rx.topological_sort(condensation_graph)
        self.A = []
        self.B = []
        self.pred_list = {}
        for block_idx in topo_seq:
            if len(condensation_graph.predecessors(block_idx)) == 0:
                self.A.append(block_idx)
            else:
                self.B.append(block_idx)
                self.pred_list[block_idx] = condensation_graph.predecessors(block_idx)

        self.blocks = []
        for scc in sccs:
            d = {dag.nodes()[node_idx]: self.d[dag.nodes()[node_idx]] for node_idx in scc}
            small_bcn = SmallBCN(d)
            self.blocks.append(small_bcn)

        for block in self.blocks:
            interior_inputs = []
            exterior_inputs = []
            for input_node in block.input_variables:
                if input_node not in self.input_variables:
                    interior_inputs.append(input_node)
                else:
                    exterior_inputs.append(input_node)
            block.interior_inputs = interior_inputs
            block.exterior_inputs = exterior_inputs

    def optimal_time_control(self, init, dest):
        # 1. state projection
        init_v = LogicalVector(init, 2 ** self.n)
        dest_v = LogicalVector(dest, 2 ** self.n)
        init_dict = dict(zip(self.variables, init_v.to_list()))
        dest_dict = dict(zip(self.variables, dest_v.to_list()))

        self.inits = []
        self.dests = []
        for block in self.blocks:
            block_init_l = [init_dict[key] for key in block.variables]
            block_dest_l = [dest_dict[key] for key in block.variables]
            block_init_v = LogicalVector.from_states(block_init_l)
            block_dest_v = LogicalVector.from_states(block_dest_l)
            self.inits.append(block_init_v.pos)
            self.dests.append(block_dest_v.pos)

        # 2. initialize
        queues = {k: deque([(self.inits[k], [self.inits[k]], [])]) for k in self.A}
        T = 0
        flag = True
        find_flag = False
        res = {k: [] for k in self.A}

        while flag:
            flag = False
            T += 1
            res = {k: [] for k in self.A}
            for k in self.A:
                find_flag = False
                bcn = self.blocks[k]
                dest = self.dests[k]
                while len(queues[k][0][1]) == T:
                    state, seq, c_seq = queues[k].popleft()
                    for next_state, inputs in bcn.one_step_states(state).items():
                        new_seq = seq + [next_state]
                        new_c_seq = c_seq + [inputs]
                        queues[k].append((next_state, new_seq, new_c_seq))
                for i in queues[k]:
                    if i[0] == dest:
                        res[k].append((i[1], i[2]))
                        find_flag = True
                if not find_flag:
                    flag = True

            if flag:
                continue

            block_find_flag = False
            cur_seq_comb = None
            for seq_comb in self.iterate(res):
                block_find_flag = False
                cur_seq_comb = seq_comb
                for k in self.B:
                    block = self.blocks[k]
                    cur_state = self.inits[k]
                    cur_seq = [[cur_state], []]
                    ex_inputs_num = 2 ** len(block.exterior_inputs)

                    if ex_inputs_num != 1:
                        for self_control_seq in product(*([range(1, ex_inputs_num + 1)] * T)):
                            cur_state = self.inits[k]
                            cur_seq = [[cur_state], []]
                            for t in range(T):
                                projection = {}
                                for pred in self.pred_list[k]:
                                    self.blocks[pred].set_states_i(cur_seq_comb[pred][0][t])
                                    projection.update(self.blocks[pred].get_states("dict"))
                                    projection.update(self.blocks[pred].get_inputs(cur_seq_comb[pred][1][t]))
                                projection.update(dict(zip(block.exterior_inputs, LogicalVector(self_control_seq[t], ex_inputs_num).to_list())))
                                inputs = block.get_inputs(projection)
                                next_state = block.next_state(cur_state, inputs)
                                cur_seq[0].append(next_state)
                                cur_seq[1].append(inputs)
                                cur_state = next_state
                            if cur_state == self.dests[k]:
                                block_find_flag = True
                                cur_seq_comb[k] = cur_seq
                                break
                            else:
                                block_find_flag = False
                    else:
                        for t in range(T):
                            projection = {}
                            for pred in self.pred_list[k]:
                                self.blocks[pred].set_states_i(cur_seq_comb[pred][0][t])
                                projection.update(self.blocks[pred].get_states("dict"))
                                projection.update(self.blocks[pred].get_inputs(cur_seq_comb[pred][1][t]))
                            inputs = block.get_inputs(projection)
                            next_state = block.next_state(cur_state, inputs)
                            cur_seq[0].append(next_state)
                            cur_seq[1].append(inputs)
                            cur_state = next_state
                        if cur_state == self.dests[k]:
                            block_find_flag = True
                            cur_seq_comb[k] = cur_seq
                        else:
                            block_find_flag = False

                    if block_find_flag == False:
                        flag = True
                        break
                    else:
                        flag = False

                if flag == False:
                    break

        return T, cur_seq_comb

    def iterate(self, res: dict):
        ret = {}
        for i in product(*res.values()):
            ret = dict(zip(res.keys(), [[ii[0], None] for ii in i]))
            for j in product(*[product(*k[1]) for k in i]):
                for idx, key in enumerate(ret.keys()):
                    ret[key][1] = j[idx]
                yield copy.deepcopy(ret)

    def iterate_2(self, res: dict, self_control: int, T):
        ret = res
        for i in product(*([range(1, self_control + 1)] * T)):
            ret["self"] = i
            yield ret.copy()

    def __str__(self):
        return f"{{variables: {self.variables}, inputs: {self.input_variables}, states: {list(self.states.values())}}}"
