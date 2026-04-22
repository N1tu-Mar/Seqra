import random

STUB_SEQUENCES = [
    "KLFKKLKKIGAVLKVLTTGLPALIS",
    "GIGKFLHSAKKFGKAFVGEIMNS",
    "ILPWKWPWWPWRR",
    "KWKLFKKIGAVLKVLTTGLPALIS",
    "RRIKIWFQNRRMKWKK",
    "GLLSKLKTFLSKVQYVLSKTYL",
    "FLPLIGRVLSGIL",
    "KKVVFKVKFKK",
    "ACYKLPPKRRRPK",
    "RRWWRRWRR",
    "KLKLLLLLKLK",
    "RWRWRWRWRW",
]

AA_LIST = list("ACDEFGHIKLMNPQRSTVWY")


def _mutate(seq: str, n_mutations: int = 2) -> str:
    seq = list(seq)
    for _ in range(n_mutations):
        pos = random.randint(0, len(seq) - 1)
        seq[pos] = random.choice(AA_LIST)
    return "".join(seq)


def generate_sequences(params: dict, n: int = 8) -> list[str]:
    pool = STUB_SEQUENCES.copy()
    # Apply locked residues if any
    locked = params.get("locked_residues", [])

    def apply_locked(seq):
        seq = list(seq)
        for lr in locked:
            pos = lr.get("position", 0)
            res = lr.get("residue", "")
            if 0 <= pos < len(seq) and res:
                seq[pos] = res.upper()
        return "".join(seq)

    # Generate variants by mutating stubs
    variants = []
    for base in pool:
        variants.append(apply_locked(base))
        variants.append(apply_locked(_mutate(base, 1)))
        variants.append(apply_locked(_mutate(base, 2)))

    random.shuffle(variants)
    return variants[:n]
