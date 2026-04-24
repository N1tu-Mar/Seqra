import json
import os
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = "claude-haiku-4-5-20251001"

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

PARSE_SYSTEM = (
    "You are a parameter extraction assistant for an antimicrobial peptide design tool. "
    "Extract structured parameters from researcher queries. "
    "Respond ONLY with a valid JSON object. No explanation, no markdown, no preamble. "
    "If a field cannot be determined, use the default. "
    'Defaults: min_length=15, max_length=35, max_toxicity="low", max_hemolysis="low", '
    'delivery_mode="topical", gram_type="positive", charge_preference="high", locked_residues=[]'
)


def _call_claude(prompt: str, system: str = "", max_tokens: int = 500) -> str:
    msg = client.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def parse_query(user_query: str) -> dict:
    try:
        raw = _call_claude(user_query, system=PARSE_SYSTEM)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw)
        return {**DEFAULTS, **parsed}
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
    try:
        prompt = (
            f"Summarize this antimicrobial peptide candidate in 2-3 sentences, max 60 words. "
            f"No hedging language. Data: {json.dumps(candidate)}"
        )
        system = "You are a concise scientific summarizer. Write 2-3 sentences max 60 words. No hedging. Be direct."
        return _call_claude(prompt, system=system)
    except Exception:
        return _rule_summary(candidate)


def generate_session_summary(candidates: list) -> str:
    if not candidates:
        return "No candidates to summarize."
    try:
        prompt = (
            f"Compare these top 5 antimicrobial peptide candidates in 3-4 sentences. "
            f"Recommend which to pursue first. Data: {json.dumps(candidates[:5])}"
        )
        return _call_claude(prompt, system="You are a concise scientific advisor. Be direct.")
    except Exception:
        top = candidates[0]
        return (
            f"Top candidate: {top['sequence']} with composite score {top['composite_score']:.2f}. "
            f"Recommend pursuing candidate #1 first."
        )
