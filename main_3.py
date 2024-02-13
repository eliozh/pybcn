from pybcn.large_bcn import SmallBCN


if __name__ == "__main__":
    d = {
        "x1": "x2 | x3",
        "x2": "x1 & u1",
        "x3": "(u1 | x2) & (!x1)"
    }
    bcn = SmallBCN(d)
    print(bcn.L)
