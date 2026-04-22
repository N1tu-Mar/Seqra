<script lang="ts">
  import type { ScoredCandidate } from "../lib/api";

  export let candidate: ScoredCandidate | null = null;
  export let candidateIndex: number = 0;

  let copied = false;

  function fastaString(): string {
    if (!candidate) return "";
    const charge = candidate.charge >= 0
      ? `+${candidate.charge.toFixed(1)}`
      : candidate.charge.toFixed(1);
    return `>Seqra_Candidate_${candidateIndex + 1} | charge=${charge} | MIC=${candidate.mic_estimate}ug/mL | hemolysis=${candidate.hemolysis}\n${candidate.sequence}`;
  }

  function downloadFasta() {
    if (!candidate) return;
    const blob = new Blob([fastaString()], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `seqra_candidate_${candidateIndex + 1}.fasta`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function copySequence() {
    if (!candidate) return;
    await navigator.clipboard.writeText(candidate.sequence);
    copied = true;
    setTimeout(() => (copied = false), 1800);
  }
</script>

<div class="export-panel">
  <div class="panel-title">Export</div>

  {#if !candidate}
    <div class="empty">Select a candidate to export.</div>
  {:else}
    <div class="fasta-preview">
      <pre>{fastaString()}</pre>
    </div>

    <div class="btn-row">
      <button class="btn-primary" on:click={downloadFasta}>
        ↓ Download FASTA
      </button>
      <button class="btn-secondary" on:click={copySequence}>
        {copied ? "✓ Copied!" : "Copy sequence"}
      </button>
    </div>
  {/if}
</div>

<style>
  .export-panel { display:flex; flex-direction:column; gap:12px; }
  .panel-title { font-size:11px; letter-spacing:0.1em; text-transform:uppercase; color:#6b8a85; }
  .empty { color:#4a6460; font-size:13px; }

  .fasta-preview {
    background:#1a1f1e; border:1px solid #2e3d3a; border-radius:6px;
    padding:10px 12px; overflow-x:auto;
  }
  pre {
    font-family:"JetBrains Mono",monospace; font-size:11px;
    color:#a0b8b4; margin:0; white-space:pre-wrap; word-break:break-all;
  }

  .btn-row { display:flex; flex-direction:column; gap:8px; }
  .btn-primary {
    background:#1a9e75; color:#fff; border:none;
    border-radius:6px; padding:9px 14px; font-size:13px; cursor:pointer;
  }
  .btn-primary:hover { background:#16896a; }
  .btn-secondary {
    background:#1a1f1e; color:#1a9e75; border:1px solid #1a9e75;
    border-radius:6px; padding:9px 14px; font-size:13px; cursor:pointer;
  }
  .btn-secondary:hover { background:#1e2e2a; }
</style>
