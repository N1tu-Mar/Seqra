import math

KD_SCALE = {
    'A': 1.8, 'R': -4.5, 'N': -3.5, 'D': -3.5, 'C': 2.5,
    'Q': -3.5, 'E': -3.5, 'G': -0.4, 'H': -3.2, 'I': 4.5,
    'L': 3.8, 'K': -3.9, 'M': 1.9, 'F': 2.8, 'P': -1.6,
    'S': -0.8, 'T': -0.7, 'W': -0.9, 'Y': -1.3, 'V': 4.2
}

EISENBERG_SCALE = {
    'A': 0.62, 'R': -2.53, 'N': -0.78, 'D': -0.90, 'C': 0.29,
    'Q': -0.85, 'E': -0.74, 'G': 0.48, 'H': -0.40, 'I': 1.38,
    'L': 1.06, 'K': -1.50, 'M': 0.64, 'F': 1.19, 'P': 0.12,
    'S': -0.18, 'T': -0.05, 'W': 0.81, 'Y': 0.26, 'V': 1.08
}

PKA = {
    'D': (3.9, -1), 'E': (4.1, -1), 'H': (6.0, +1),
    'C': (8.3, -1), 'Y': (10.1, -1), 'K': (10.5, +1),
    'R': (12.5, +1)
}
N_TERM_PKA = 8.0
C_TERM_PKA = 3.1


def compute_charge(sequence: str, ph: float = 7.4) -> float:
    charge = 0.0
    # N-terminus
    charge += 1.0 / (1.0 + 10 ** (ph - N_TERM_PKA))
    # C-terminus
    charge -= 1.0 / (1.0 + 10 ** (C_TERM_PKA - ph))
    for aa in sequence.upper():
        if aa in PKA:
            pka, sign = PKA[aa]
            if sign > 0:
                charge += 1.0 / (1.0 + 10 ** (ph - pka))
            else:
                charge -= 1.0 / (1.0 + 10 ** (pka - ph))
    return round(charge, 2)


def compute_hydrophobicity(sequence: str) -> float:
    seq = sequence.upper()
    values = [KD_SCALE.get(aa, 0.0) for aa in seq]
    return round(sum(values) / len(values), 3) if values else 0.0


def compute_amphipathicity(sequence: str) -> float:
    seq = sequence.upper()
    angle_per_residue = 100.0  # degrees, alpha-helix
    sum_sin = 0.0
    sum_cos = 0.0
    for i, aa in enumerate(seq):
        h = EISENBERG_SCALE.get(aa, 0.0)
        angle = math.radians(i * angle_per_residue)
        sum_sin += h * math.sin(angle)
        sum_cos += h * math.cos(angle)
    moment = math.sqrt(sum_sin ** 2 + sum_cos ** 2) / len(seq)
    # Normalize to 0-1 (max raw ~0.7)
    normalized = min(moment / 0.7, 1.0)
    return round(normalized, 3)


def predict_hemolysis(sequence: str, charge: float, hydrophobicity: float) -> str:
    if hydrophobicity > 0.5 and charge < 2:
        return "high"
    if hydrophobicity > 0.3 or (charge > 6 and len(sequence) > 30):
        return "medium"
    return "low"


def predict_toxicity(sequence: str, charge: float) -> str:
    seq = sequence.upper()
    hydrophobic = set("FILMVW")
    if charge > 9:
        return "high"
    if len(seq) < 15:
        # Check 3+ consecutive hydrophobic residues
        count = 0
        for aa in seq:
            if aa in hydrophobic:
                count += 1
                if count >= 3:
                    return "high"
            else:
                count = 0
    if charge > 6:
        return "medium"
    return "low"


def estimate_mic(sequence: str, charge: float, amphipathicity: float) -> float:
    mic = 64.0
    extra_charge = max(charge - 2, 0)
    mic *= (0.85 ** extra_charge)
    extra_amph = max(amphipathicity - 0.3, 0)
    steps = extra_amph / 0.1
    mic *= (0.9 ** steps)
    mic = max(0.5, min(128.0, mic))
    return round(mic, 2)


def compute_composite_score(charge: float, hydrophobicity: float,
                             amphipathicity: float, hemolysis: str,
                             toxicity: str, mic: float) -> float:
    # MIC score (log scale 0.5-128)
    mic_norm = 1.0 - (math.log(mic) - math.log(0.5)) / (math.log(128) - math.log(0.5))
    mic_score = max(0.0, min(1.0, mic_norm)) * 0.35

    hemolysis_map = {"low": 1.0, "medium": 0.5, "high": 0.0}
    toxicity_map = {"low": 1.0, "medium": 0.5, "high": 0.0}

    hemolysis_score = hemolysis_map.get(hemolysis, 0.0) * 0.25
    toxicity_score = toxicity_map.get(toxicity, 0.0) * 0.20
    amph_score = amphipathicity * 0.10
    charge_norm = max(0.0, min(1.0, (charge - 2) / 7)) * 0.10

    total = mic_score + hemolysis_score + toxicity_score + amph_score + charge_norm
    return round(total, 3)


def score_sequence(sequence: str) -> dict:
    seq = sequence.upper().strip()
    length = len(seq)
    charge = compute_charge(seq)
    hydrophobicity = compute_hydrophobicity(seq)
    amphipathicity = compute_amphipathicity(seq)
    hemolysis = predict_hemolysis(seq, charge, hydrophobicity)
    toxicity = predict_toxicity(seq, charge)
    mic = estimate_mic(seq, charge, amphipathicity)
    composite = compute_composite_score(charge, hydrophobicity, amphipathicity,
                                        hemolysis, toxicity, mic)
    return {
        "sequence": seq,
        "length": length,
        "charge": charge,
        "hydrophobicity": hydrophobicity,
        "amphipathicity": amphipathicity,
        "hemolysis": hemolysis,
        "toxicity": toxicity,
        "mic_estimate": mic,
        "length_valid": 15 <= length <= 35,
        "composite_score": composite,
    }
