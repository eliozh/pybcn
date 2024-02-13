from pybcn.small_bcn import SmallBCN
from itertools import product
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
    bcn = SmallBCN(d)
    # ends = []
    # for i in range(1, 2 ** 10 + 1):
    #     res = bcn.optimal_time_control(1, i)
    #     if res[1] != []:
    #         ends.append(i)

    # print(ends)
    T, res = bcn.optimal_time_control_2(1, 1)
    for i in product(res):
        state_seq = i[0][0]
        for j in product(*i[0][1]):
            print(state_seq, j)
            for t in range(T):
                print(f"T={t}")
                print(dict(zip(bcn.variables, LogicalVector(state_seq[t], bcn.N).to_list())))
                print(bcn.get_inputs(j[t]))
            print("----------------")
