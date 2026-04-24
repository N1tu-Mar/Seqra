const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface LockedResidue {
  position: number;
  residue: string;
}

export interface GenerationParams {
  target_pathogen: string;
  gram_type: string;
  min_length: number;
  max_length: number;
  max_toxicity: string;
  max_hemolysis: string;
  delivery_mode: string;
  charge_preference: string;
  locked_residues: LockedResidue[];
}

export interface ScoredCandidate {
  sequence: string;
  length: number;
  charge: number;
  hydrophobicity: number;
  amphipathicity: number;
  hemolysis: "low" | "medium" | "high";
  toxicity: "low" | "medium" | "high";
  mic_estimate: number;
  length_valid: boolean;
  composite_score: number;
  summary: string;
}

export async function parseQuery(query: string): Promise<GenerationParams> {
  const res = await fetch(`${BASE}/parse_query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error("parse_query failed");
  return res.json();
}

export async function generate(
  params: GenerationParams
): Promise<{ candidates: ScoredCandidate[]; session_summary: string }> {
  const res = await fetch(`${BASE}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error("generate failed");
  return res.json();
}

export async function scoreSequence(
  sequence: string
): Promise<ScoredCandidate> {
  const res = await fetch(`${BASE}/score`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sequence }),
  });
  if (!res.ok) throw new Error("score failed");
  return res.json();
}
