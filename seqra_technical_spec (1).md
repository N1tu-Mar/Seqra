# Seqra — Technical Specification
## Stack: Python backend, Svelte + Tauri frontend, Rust glue layer

---

## Project Structure

```
seqra/
├── src-tauri/
│   ├── src/
│   │   └── main.rs
│   └── tauri.conf.json
├── src/
│   ├── App.svelte
│   ├── components/
│   │   ├── InputPanel.svelte
│   │   ├── CandidateList.svelte
│   │   ├── ScoringRadar.svelte
│   │   ├── ResidueEditor.svelte
│   │   └── ExportPanel.svelte
│   └── lib/
│       └── api.ts
├── python/
│   ├── main.py
│   ├── scoring.py
│   ├── llm.py
│   └── generator.py
├── tests/
│   └── test_scoring.py
└── requirements.txt
```

---

## Scoring Layer

**File:** `python/scoring.py`

Takes a sequence string, returns a dict.

```python
def score_sequence(sequence: str) -> dict:
    """
    Main entry point. Calls all sub-scorers and returns combined result.

    Input:
        sequence: str — amino acid sequence in single-letter code e.g. "KLFKKLKKIGAVLKVLTTGLPALIS"

    Output:
        {
            "sequence": str,
            "length": int,
            "charge": float,          # net charge at pH 7.4
            "hydrophobicity": float,  # GRAVY score, Kyte-Doolittle
            "amphipathicity": float,  # normalized helical wheel moment, 0-1
            "hemolysis": str,         # "low" | "medium" | "high"
            "toxicity": str,          # "low" | "medium" | "high"
            "mic_estimate": float,    # estimated MIC in ug/mL, rule-based
            "length_valid": bool,     # True if 15-35 aa
            "composite_score": float  # weighted 0-1, higher is better
        }
    """

def compute_charge(sequence: str, ph: float = 7.4) -> float:
    """
    Net charge using Henderson-Hasselbalch.
    pKa values: Asp=3.9, Glu=4.1, His=6.0, Cys=8.3, Tyr=10.1, Lys=10.5, Arg=12.5, N-term=8.0, C-term=3.1
    Positive residues: Lys(K), Arg(R), His(H)
    Negative residues: Asp(D), Glu(E), Cys(C), Tyr(Y)
    """

def compute_hydrophobicity(sequence: str) -> float:
    """
    Grand Average of Hydropathicity (GRAVY). Kyte-Doolittle scale.
    A=1.8, R=-4.5, N=-3.5, D=-3.5, C=2.5, Q=-3.5, E=-3.5, G=-0.4,
    H=-3.2, I=4.5, L=3.8, K=-3.9, M=1.9, F=2.8, P=-1.6, S=-0.8,
    T=-0.7, W=-0.9, Y=-1.3, V=4.2
    """

def compute_amphipathicity(sequence: str) -> float:
    """
    Helical wheel moment. Alpha-helical geometry (100 degrees per residue).
    Eisenberg hydrophobicity scale. Normalize to 0-1 (range 0 to 0.7).
    A=0.62, R=-2.53, N=-0.78, D=-0.90, C=0.29, Q=-0.85, E=-0.74, G=0.48,
    H=-0.40, I=1.38, L=1.06, K=-1.50, M=0.64, F=1.19, P=0.12, S=-0.18,
    T=-0.05, W=0.81, Y=0.26, V=1.08
    """

def predict_hemolysis(sequence: str, charge: float, hydrophobicity: float) -> str:
    """
    Rule-based. Returns "low" | "medium" | "high"
    High: hydrophobicity > 0.5 AND charge < +2
    Medium: hydrophobicity > 0.3 OR (charge > +6 AND length > 30)
    Low: everything else
    """

def predict_toxicity(sequence: str, charge: float) -> str:
    """
    Rule-based. Returns "low" | "medium" | "high"
    High: charge > +9 OR 3+ consecutive hydrophobic residues (FILMVW) AND length < 15
    Medium: charge > +6
    Low: everything else
    """

def estimate_mic(sequence: str, charge: float, amphipathicity: float) -> float:
    """
    Rule-based MIC in ug/mL.
    Base: 64 ug/mL
    Each +1 charge above +2: multiply by 0.85
    Each 0.1 amphipathicity above 0.3: multiply by 0.9
    Floor: 0.5, ceiling: 128
    """

def compute_composite_score(charge: float, hydrophobicity: float,
                             amphipathicity: float, hemolysis: str,
                             toxicity: str, mic: float) -> float:
    """
    Weighted 0-1. Higher = better.
    mic_score: 0.35       (lower MIC = higher score, log scale 0.5-128)
    hemolysis_score: 0.25 (low=1.0, medium=0.5, high=0.0)
    toxicity_score: 0.20  (low=1.0, medium=0.5, high=0.0)
    amphipathicity: 0.10  (already 0-1)
    charge_score: 0.10    (normalize +2 to +9 to 0-1)
    """
```

### Tests (`tests/test_scoring.py`)

```python
def test_known_amp():
    result = score_sequence("GIGKFLHSAKKFGKAFVGEIMNS")
    assert result["length"] == 23
    assert result["length_valid"] == True
    assert 3.0 <= result["charge"] <= 6.0
    assert result["hemolysis"] in ["low", "medium"]

def test_length_flag():
    result = score_sequence("KLFK")
    assert result["length_valid"] == False

def test_high_charge():
    result = score_sequence("KKKKKKKKKRRRR")
    assert result["charge"] > 8
```

---

## LLM Integration

**File:** `python/llm.py`

Local LLM via Ollama REST API at `http://localhost:11434`. Ollama runs separately (`ollama serve`). Default model: `llama3`.

```python
OLLAMA_BASE = "http://localhost:11434"
DEFAULT_MODEL = "llama3"

def parse_query(user_query: str) -> dict:
    """
    Plain English -> structured params.
    Input:  "generate MRSA candidates, low toxicity, topical delivery"
    Output:
        {
            "target_pathogen": str,
            "gram_type": str,         # "positive" | "negative" | "both" | "unknown"
            "min_length": int,        # default 15
            "max_length": int,        # default 35
            "max_toxicity": str,      # "low" | "medium" | "any"
            "max_hemolysis": str,     # "low" | "medium" | "any"
            "delivery_mode": str,     # "topical" | "systemic" | "any"
            "charge_preference": str, # "high" | "moderate" | "any"
            "locked_residues": list   # [{"position": 3, "residue": "K"}]
        }
    LLM must return ONLY valid JSON. Parse with json.loads(). On failure return defaults.
    """

def generate_candidate_summary(candidate: dict) -> str:
    """
    Scored candidate dict -> 2-3 sentence plain English summary.
    Max 60 words. No hedging language.
    Example: "Candidate shows strong predicted activity against MRSA with a low hemolytic
    profile and estimated MIC of 4 ug/mL. Charge of +6 and moderate amphipathicity
    suggest good membrane interaction. Suitable for topical application."
    """

def generate_session_summary(candidates: list[dict]) -> str:
    """
    Top 5 candidates -> 3-4 sentence comparison, recommend which to pursue first.
    """

def _call_ollama(prompt: str, system: str = "", model: str = DEFAULT_MODEL) -> str:
    """
    POST to /api/generate, stream=False. Raise RuntimeError if unreachable.
    """
```

### Ollama call structure

```python
payload = {
    "model": model,
    "prompt": prompt,
    "system": system,
    "stream": False,
    "options": { "temperature": 0.2, "num_predict": 500 }
}
response = requests.post(f"{OLLAMA_BASE}/api/generate", json=payload, timeout=60)
return response.json()["response"]
```

### System prompt for `parse_query`

```
You are a parameter extraction assistant for an antimicrobial peptide design tool.
Extract structured parameters from researcher queries.
Respond ONLY with a valid JSON object. No explanation, no markdown, no preamble.
If a field cannot be determined, use the default.
Defaults: min_length=15, max_length=35, max_toxicity="low", max_hemolysis="low",
delivery_mode="topical", gram_type="positive", charge_preference="high", locked_residues=[]
```

---

## Generator Stub

**File:** `python/generator.py`

```python
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
]

def generate_sequences(params: dict, n: int = 8) -> list[str]:
    pool = STUB_SEQUENCES.copy()
    random.shuffle(pool)
    return pool[:n]
```

---

## Python Sidecar

**File:** `python/main.py`

Tauri talks to Python via persistent subprocess, stdin/stdout JSON, one message per line.

```python
# Input from Tauri:
{ "command": "generate", "payload": { ...GenerationParams } }
{ "command": "parse_query", "payload": { "query": "..." } }
{ "command": "summarize", "payload": { "candidate": { ... } } }

# Output to Tauri:
{ "status": "ok", "data": { ... } }
{ "status": "error", "message": "..." }
```

```python
import sys, json
from scoring import score_sequence
from llm import parse_query, generate_candidate_summary
from generator import generate_sequences

def handle(command: str, payload: dict) -> dict:
    if command == "parse_query":
        return parse_query(payload["query"])
    if command == "summarize":
        return {"summary": generate_candidate_summary(payload["candidate"])}
    if command == "generate":
        sequences = generate_sequences(payload)
        scored = [score_sequence(s) for s in sequences]
        for c in scored:
            c["summary"] = generate_candidate_summary(c)
        scored.sort(key=lambda x: x["composite_score"], reverse=True)
        return {"candidates": scored[:5]}
    raise ValueError(f"Unknown command: {command}")

if __name__ == "__main__":
    for line in sys.stdin:
        msg = json.loads(line.strip())
        try:
            result = handle(msg["command"], msg.get("payload", {}))
            print(json.dumps({"status": "ok", "data": result}), flush=True)
        except Exception as e:
            print(json.dumps({"status": "error", "message": str(e)}), flush=True)
```

### Tauri command (`src-tauri/src/main.rs`)

```rust
use std::process::{Command, Stdio};
use std::io::{BufRead, BufReader, Write};

#[tauri::command]
fn call_python(payload: String) -> String {
    // Spawn python sidecar as persistent subprocess
    // Send payload as stdin line, read response line
    // Keep process alive between calls — do not respawn per command
}
```

---

## UI

**Stack:** Svelte inside Tauri. Three-panel layout.

```
┌──────────────┬─────────────────┬──────────────┐
│  left 280px  │   center flex   │  right 280px │
└──────────────┴─────────────────┴──────────────┘
```

Colors: bg `#1a1f1e`, panel `#212827`, text `#c8d4d2`, accent `#1a9e75`
Fonts: `JetBrains Mono` for sequences, `Inter` for UI

### TypeScript types (`src/lib/types.ts`)

```typescript
interface ScoredCandidate {
  sequence: string
  length: number
  charge: number
  hydrophobicity: number
  amphipathicity: number
  hemolysis: "low" | "medium" | "high"
  toxicity: "low" | "medium" | "high"
  mic_estimate: number
  length_valid: boolean
  composite_score: number
  summary: string
}

interface LockedResidue {
  position: number
  residue: string
}

interface GenerationParams {
  target_pathogen: string
  gram_type: string
  min_length: number
  max_length: number
  max_toxicity: string
  max_hemolysis: string
  delivery_mode: string
  locked_residues: LockedResidue[]
}
```

### `InputPanel.svelte`

Emits: `generate` event with `{ query, constraints }`

Elements:
- Text input: `target_pathogen`, placeholder "target pathogen..."
- Text input: `length_range`, pre-filled "15-35 aa", read-only
- Number input: `toxicity_threshold`, placeholder "toxicity threshold..."
- Checkboxes: `low_hemolysis`, `serum_stable`, `topical_delivery`
- Button: "generate" — disabled + spinner while loading
- Scrollable chat log: alternating user/assistant messages
- Text input at bottom: "ask or refine..." with send button

```typescript
let query = ""
let constraints = { low_hemolysis: false, serum_stable: false, topical_delivery: false }
let chatHistory: Array<{ role: "user" | "assistant", text: string }> = []
let loading = false
```

### `CandidateList.svelte`

Props: `candidates: ScoredCandidate[]`, `selectedIndex: number`
Emits: `select` with candidate index

Elements:
- Tab bar #1 through #5 with star rating:
  - composite > 0.7: 3 stars
  - composite 0.4-0.7: 2 stars
  - composite < 0.4: 1 star
- Per candidate: sequence in monospace, score bars for charge/hemolysis/MIC/toxicity, plain English summary
- Bar colors: green = low risk, amber = medium, red = high

### `ScoringRadar.svelte`

Props: `candidate: ScoredCandidate | null`

SVG pentagon radar chart, no chart library. Five axes: amphipathicity, stability (inverse toxicity), MIC (inverse normalized), charge (normalized +2 to +9), hydrophobicity (normalized). Fill polygon teal at 40% opacity.

### `ResidueEditor.svelte`

Props: `sequence: string`, `lockedResidues: LockedResidue[]`
Emits: `lock` with `{ position, residue }`, `regenerate`

Elements:
- Display selected residue: "selected: R3 (Lys)"
- Dropdown: replacement residue (all 20 amino acids)
- Lock checkbox
- Button: "regenerate around R{n}"

### `ExportPanel.svelte`

Props: `candidate: ScoredCandidate | null`

Elements:
- Button: "download FASTA" — generates and downloads client-side
- Button: "copy sequence to clipboard"

FASTA format:
```
>Seqra_Candidate_1 | charge=+6 | MIC=4ug/mL | hemolysis=low
KLFKKLKKIGAVLKVLTTGLPALIS
```

---

## Dependencies

```
# requirements.txt
requests
numpy
```

Ollama: https://ollama.ai — run `ollama pull llama3` before starting.
