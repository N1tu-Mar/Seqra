import json
import math
import requests

OLLAMA_BASE = "http://localhost:11434"
DEFAULT_MODEL = "llama3"

PARSE_SYSTEM = (
    "You are a parameter extraction assistant for an antimicrobial peptide design tool. "
    "Extract structured parameters from researcher queries. "
    "Respond ONLY with a valid JSON object. No explanation, no markdown, no preamble. "
    "If a field cannot be determined, use the default. "
    'Defaults: min_length=15, max_length=35, max_toxicity="low", max_hemolysis="low", '
    'delivery_mode="topical", gram_type="positive", charge_preference="high", locked_residues=[]'
)

DEFAULTS = {
    "target_pathogen": "unknown",
    "gram_type": "positive",
    "min_length": 15,
    "max_length": 35,
    "max_toxicity": "low",
    "max_hemolysis": "low",
    "delivery_mode": "topical",
    "charge_preference": "high",
    "locked_residues": [],
}


def _call_ollama(prompt: str, system: str = "", model: str = DEFAULT_MODEL) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": 0.2, "num_predict": 500},
    }
    response = requests.post(
        f"{OLLAMA_BASE}/api/generate", json=payload, timeout=60
    )
    response.raise_for_status()
    return response.json()["response"]


def _ollama_available() -> bool:
    try:
        r = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def parse_query(user_query: str) -> dict:
    if not _ollama_available():
        return _fallback_parse(user_query)
    try:
        raw = _call_ollama(user_query, system=PARSE_SYSTEM)
        parsed = json.loads(raw)
        result = {**DEFAULTS, **parsed}
        return result
    except Exception:
        return _fallback_parse(user_query)


def _fallback_parse(query: str) -> dict:
    result = dict(DEFAULTS)
    q = query.lower()
    if "mrsa" in q or "staph" in q:
        result["target_pathogen"] = "MRSA"
        result["gram_type"] = "positive"
    elif "e. coli" in q or "ecoli" in q or "gram neg" in q:
        result["target_pathogen"] = "E. coli"
        result["gram_type"] = "negative"
    elif "pseudomonas" in q:
        result["target_pathogen"] = "Pseudomonas"
        result["gram_type"] = "negative"
    elif "candida" in q or "fungal" in q:
        result["target_pathogen"] = "Candida"
    if "systemic" in q:
        result["delivery_mode"] = "systemic"
    if "topical" in q:
        result["delivery_mode"] = "topical"
    if "medium toxicity" in q or "medium tox" in q:
        result["max_toxicity"] = "medium"
    if "low toxicity" in q or "low tox" in q:
        result["max_toxicity"] = "low"
    return result


def _rule_summary(candidate: dict) -> str:
    seq = candidate.get("sequence", "")
    charge = candidate.get("charge", 0)
    mic = candidate.get("mic_estimate", 64)
    hemolysis = candidate.get("hemolysis", "unknown")
    toxicity = candidate.get("toxicity", "unknown")
    amphipathicity = candidate.get("amphipathicity", 0)
    score = candidate.get("composite_score", 0)

    activity = "strong" if score > 0.7 else "moderate" if score > 0.4 else "weak"
    amph_desc = "high" if amphipathicity > 0.6 else "moderate" if amphipathicity > 0.3 else "low"

    return (
        f"Candidate shows {activity} predicted antimicrobial activity with a {hemolysis} "
        f"hemolytic profile and estimated MIC of {mic} ug/mL. "
        f"Charge of {charge:+.1f} and {amph_desc} amphipathicity suggest "
        f"{'good' if amphipathicity > 0.4 else 'limited'} membrane interaction. "
        f"Toxicity predicted {toxicity}."
    )


def generate_candidate_summary(candidate: dict) -> str:
    if not _ollama_available():
        return _rule_summary(candidate)
    try:
        prompt = (
            f"Summarize this antimicrobial peptide candidate in 2-3 sentences, max 60 words. "
            f"No hedging language. Data: {json.dumps(candidate)}"
        )
        system = (
            "You are a concise scientific summarizer. "
            "Write 2-3 sentences max 60 words. No hedging. Be direct."
        )
        return _call_ollama(prompt, system=system)
    except Exception:
        return _rule_summary(candidate)


def generate_session_summary(candidates: list) -> str:
    if not candidates:
        return "No candidates to summarize."
    if not _ollama_available():
        top = candidates[0]
        return (
            f"Top candidate: {top['sequence']} with composite score {top['composite_score']:.2f}, "
            f"MIC {top['mic_estimate']} ug/mL, {top['hemolysis']} hemolysis. "
            f"Recommend pursuing candidate #1 first based on overall profile."
        )
    try:
        prompt = (
            f"Compare these top 5 antimicrobial peptide candidates in 3-4 sentences. "
            f"Recommend which to pursue first. Data: {json.dumps(candidates[:5])}"
        )
        return _call_ollama(prompt, system="You are a concise scientific advisor. Be direct.")
    except Exception:
        top = candidates[0]
        return (
            f"Top candidate: {top['sequence']} with composite score {top['composite_score']:.2f}. "
            f"Recommend pursuing candidate #1 first."
        )
