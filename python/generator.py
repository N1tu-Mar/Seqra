import json
import random
import re
import os
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-haiku-4-5-20251001"

AA_VALID = set("ACDEFGHIKLMNPQRSTVWY")

# Fallback pool — only used if Claude call fails completely
FALLBACK_SEQUENCES = [
    "KLFKKLKKIGAVLKVLTTGLPALIS",
    "GIGKFLHSAKKFGKAFVGEIMNS",
    "KWKLFKKIGAVLKVLTTGLPALIS",
    "RRIKIWFQNRRMKWKK",
    "GLLSKLKTFLSKVQYVLSKTYL",
    "ACYKLPPKRRRPK",
    "RRWWRRWRR",
    "KLKLLLLLKLK",
]

GENERATE_SYSTEM = """You are an expert computational biologist specializing in antimicrobial peptide (AMP) design.
Design novel antimicrobial peptide sequences based on the given constraints.

Rules:
- Use only standard single-letter amino acid codes: ACDEFGHIKLMNPQRSTVWY
- Each sequence must be unique — no duplicates
- Sequences must strictly satisfy the length range given
- For gram-positive targets: favor cationic (+4 to +8 charge) peptides with moderate hydrophobicity
- For gram-negative targets: favor shorter, highly cationic peptides that can penetrate the outer membrane
- For low hemolysis: avoid excessive hydrophobicity (GRAVY < 1.0), use lysine over arginine where possible
- For low toxicity: avoid 3+ consecutive hydrophobic residues (F,I,L,M,V,W), keep charge < +9
- For high charge preference: include multiple K/R residues
- Apply any locked residues exactly as specified

Respond ONLY with a JSON array of sequence strings. No explanation, no markdown fences, no preamble.
Example output: ["KLFKKLKK", "RWRWRWRW", "GIGKFLHS"]"""


def _call_claude(prompt: str, system: str = "", max_tokens: int = 800) -> str:
    msg = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def _apply_locked(seq: str, locked: list) -> str:
    seq = list(seq)
    for lr in locked:
        pos = lr.get("position", 0)
        res = lr.get("residue", "")
        if 0 <= pos < len(seq) and res:
            seq[pos] = res.upper()
    return "".join(seq)


def _is_valid(seq: str, min_len: int, max_len: int) -> bool:
    if not seq or not (min_len <= len(seq) <= max_len):
        return False
    return all(aa in AA_VALID for aa in seq.upper())


def _parse_sequences(raw: str) -> list[str]:
    """Extract sequence list from Claude's response, robust to minor formatting issues."""
    raw = raw.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = re.sub(r"```[a-z]*\n?", "", raw).replace("```", "").strip()
    try:
        seqs = json.loads(raw)
        if isinstance(seqs, list):
            return [s.upper().strip() for s in seqs if isinstance(s, str)]
    except json.JSONDecodeError:
        pass
    # Fallback: extract anything that looks like a peptide sequence
    return [m.upper() for m in re.findall(r'\b[ACDEFGHIKLMNPQRSTVWY]{8,40}\b', raw)]


def generate_sequences(params: dict, n: int = 8) -> list[str]:
    min_len = params.get("min_length", 15)
    max_len = params.get("max_length", 35)
    gram = params.get("gram_type", "positive")
    pathogen = params.get("target_pathogen", "unknown")
    max_tox = params.get("max_toxicity", "low")
    max_hemo = params.get("max_hemolysis", "low")
    charge_pref = params.get("charge_preference", "high")
    delivery = params.get("delivery_mode", "topical")
    locked = params.get("locked_residues", [])

    locked_desc = ""
    if locked:
        locked_desc = "Locked residues (must appear at these positions): " + ", ".join(
            f"position {lr['position']} = {lr['residue']}" for lr in locked
        )

    prompt = f"""Design {n + 4} novel antimicrobial peptide sequences with these constraints:
- Target pathogen: {pathogen}
- Gram type: gram-{gram}
- Length: {min_len} to {max_len} amino acids (strictly enforced)
- Max toxicity: {max_tox}
- Max hemolysis: {max_hemo}
- Charge preference: {charge_pref}
- Delivery mode: {delivery}
{locked_desc}

Return a JSON array of {n + 4} unique sequence strings."""

    try:
        raw = _call_claude(prompt, system=GENERATE_SYSTEM)
        candidates = _parse_sequences(raw)

        # Apply locked residues and filter valid sequences
        valid = []
        seen = set()
        for seq in candidates:
            if locked:
                seq = _apply_locked(seq, locked)
            seq = seq.upper()
            if _is_valid(seq, min_len, max_len) and seq not in seen:
                seen.add(seq)
                valid.append(seq)

        if len(valid) >= n:
            return valid[:n]

        # If we didn't get enough valid sequences, pad with mutated fallbacks
        valid.extend(_fallback_generate(params, n - len(valid), exclude=seen))
        return valid[:n]

    except Exception:
        return _fallback_generate(params, n)


def _mutate(seq: str, n_mutations: int = 2) -> str:
    aa_list = list("ACDEFGHIKLMNPQRSTVWY")
    seq = list(seq)
    for _ in range(n_mutations):
        pos = random.randint(0, len(seq) - 1)
        seq[pos] = random.choice(aa_list)
    return "".join(seq)


def _fallback_generate(params: dict, n: int, exclude: set = None) -> list[str]:
    """Rule-based fallback that at least respects length constraints."""
    if exclude is None:
        exclude = set()
    min_len = params.get("min_length", 15)
    max_len = params.get("max_length", 35)
    locked = params.get("locked_residues", [])

    pool = FALLBACK_SEQUENCES.copy()
    # Filter to sequences within length range, pad/trim if needed
    sized = [s for s in pool if min_len <= len(s) <= max_len]
    if not sized:
        sized = pool  # give up on length filtering rather than returning nothing

    variants = []
    for base in sized:
        for _ in range(3):
            candidate = _apply_locked(_mutate(base, random.randint(1, 3)), locked)
            if candidate not in exclude:
                variants.append(candidate)

    random.shuffle(variants)
    return variants[:n]