import rustworkx as rx
from pybcn.large_bcn import LargeBCN
from pybcn.logical_vector import LogicalVector


if __name__ == "__main__":
    d = {
        "x1": "!x2 & u1",
        "x2": "x1 ^ u2 & x3",
        "x3": "(u1 & x2) | x1",
        "x4": "x5 | x2",
        "x5": "!x4",
        "x6": "x7 ^ u3",
        "x7": "x6",
        "x8": "x3 | (!x10)",
        "x9": "!x7 & x8",
        "x10": "x5 & x9"
    }
    bcn = LargeBCN(d)
    bcn.partition()
    # for i in bcn.blocks:
    #     print(i)
    T, res = bcn.optimal_time_control(1, 1)
    for t in range(T):
        states = {}
        inputs = {}
        print(f"T={t}")
        for key, val in res.items():
            states.update(
                dict(zip(bcn.blocks[key].variables, LogicalVector(val[0][t], bcn.blocks[key].N).to_list()))
            )
            inputs.update(bcn.blocks[key].get_inputs(val[1][t]))
        print(states)
        print(inputs)
