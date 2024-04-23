import rustworkx as rx
import time
from tqdm import tqdm
from pybcn.large_bcn import LargeBCN
from pybcn.small_bcn import SmallBCN
from rustworkx.visualization import graphviz_draw
from pybcn.logical_vector import LogicalVector


if __name__ == "__main__":
    d = {
        "x1": "u1 & (x3 | x6)",
        "x2": "x1 | (x3 & x6)",
        "x3": "(u1 & u2) & (!x5)",
        "x4": "(!x7) & x3 & x2",
        "x5": "x1 | (!x6)",
        "x6": "u3 & (!x7)",
        "x7": "x4",
        "x8": "x3",
        "x9": "x4",
        "x10": "x9",
        "x11": "x10",
        "x12": "x11 & x4",
        "x13": "x9",
        "x14": "x9",
        "x15": "(x8 | x12) & (x4 & x11 & x14)",
        "x16": "x15",
        "x17": "x16",
        "x18": "x17",
        "x19": "x18",
        "x20": "x15",
        "x21": "x23",
        "x22": "x21",
        "x23": "x20",
        "x24": "x22",
        "x25": "x23",
        "x26": "!x25",
        "x27": "!x26",
        "x28": "x29",
        "x29": "x30",
        "x30": "x34",
        "x31": "x13 | x35",
        "x32": "x31",
        "x33": "x32",
        "x34": "x33",
        "x35": "x20 & x23",
        "x36": "x34",
        "x37": "x36 & x24"
    }
    bcn = LargeBCN(d)
    init = LogicalVector.from_states(
        [0, 0, 0, 0, 1, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    ).pos
    dest = LogicalVector.from_states(
        [1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1]
    ).pos
    start = time.time()
    bcn.partition()
    T, res = bcn.optimal_time_control(init, dest)
    end = time.time()
    print(f"T* = {T}")
    print(f"time: {end - start}")
    control_seqs = {}
    for i in range(T):
        control_inputs = {}
        for blk_id, seq in res.items():
            blk = bcn.blocks[blk_id]
            v = LogicalVector(seq[1][i], blk.M)
            control_inputs.update(dict(zip(blk.input_variables, v.to_list())))
        control_inputs = dict(filter(lambda x: x[0] in bcn.input_variables, control_inputs.items()))
        control_seqs[i] = control_inputs
    print(control_seqs)
