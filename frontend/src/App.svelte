<script lang="ts">
  import InputPanel from "./components/InputPanel.svelte";
  import CandidateList from "./components/CandidateList.svelte";
  import ScoringRadar from "./components/ScoringRadar.svelte";
  import ResidueEditor from "./components/ResidueEditor.svelte";
  import ExportPanel from "./components/ExportPanel.svelte";
  import { generate, scoreSequence } from "./lib/api";
  import type { ScoredCandidate, GenerationParams, LockedResidue } from "./lib/api";

  let candidates: ScoredCandidate[] = [];
  let selectedIndex = 0;
  let loading = false;
  let sessionSummary = "";
  let lockedResidues: LockedResidue[] = [];
  let error = "";

  $: selectedCandidate = candidates[selectedIndex] ?? null;

  async function handleGenerate(e: CustomEvent<GenerationParams>) {
    loading = true;
    error = "";
    try {
      const params = { ...e.detail, locked_residues: lockedResidues };
      const result = await generate(params);
      candidates = result.candidates;
      sessionSummary = result.session_summary;
      selectedIndex = 0;
    } catch (err) {
      error = "Backend unreachable. Is the Python server running? (uvicorn python.main:app)";
    } finally {
      loading = false;
    }
  }

  async function handleLock(e: CustomEvent<LockedResidue>) {
    const { position, residue } = e.detail;
    const existing = lockedResidues.findIndex(r => r.position === position);
    if (existing >= 0) {
      lockedResidues = lockedResidues.map((r, i) => i === existing ? { position, residue } : r);
    } else {
      lockedResidues = [...lockedResidues, { position, residue }];
    }
  }

  async function handleRegenerate(e: CustomEvent<{ position: number }>) {
    if (!selectedCandidate) return;
    loading = true;
    error = "";
    try {
      // Re-score the current sequence with locked residues applied
      const seq = selectedCandidate.sequence.split("");
      for (const lr of lockedResidues) {
        if (lr.position < seq.length) seq[lr.position] = lr.residue;
      }
      const result = await scoreSequence(seq.join(""));
      candidates = candidates.map((c, i) => i === selectedIndex ? result : c);
    } catch (err) {
      error = "Failed to re-score sequence.";
    } finally {
      loading = false;
    }
  }
</script>

<div class="app">
  <header>
    <div class="logo">Seqra</div>
    <div class="subtitle">Antimicrobial Peptide Designer</div>
    {#if error}
      <div class="error-banner">{error}</div>
    {/if}
  </header>

  <main>
    <!-- Left panel: query + chat -->
    <aside class="left-panel">
      <InputPanel {loading} on:generate={handleGenerate} />
    </aside>

    <!-- Center panel: candidates -->
    <section class="center-panel">
      <CandidateList
        {candidates}
        {selectedIndex}
        on:select={(e) => { selectedIndex = e.detail; }}
      />

      {#if sessionSummary && candidates.length > 0}
        <div class="session-summary">
          <div class="summary-label">Session Analysis</div>
          <p>{sessionSummary}</p>
        </div>
      {/if}
    </section>

    <!-- Right panel: radar + residue editor + export -->
    <aside class="right-panel">
      <ScoringRadar candidate={selectedCandidate} />

      <div class="divider"></div>

      <ResidueEditor
        sequence={selectedCandidate?.sequence ?? ""}
        {lockedResidues}
        on:lock={handleLock}
        on:regenerate={handleRegenerate}
      />

      <div class="divider"></div>

      <ExportPanel candidate={selectedCandidate} candidateIndex={selectedIndex} />
    </aside>
  </main>
</div>

<style>
  :global(*, *::before, *::after) { box-sizing: border-box; }
  :global(body) {
    margin: 0;
    background: #1a1f1e;
    color: #c8d4d2;
    font-family: "Inter", system-ui, sans-serif;
    min-height: 100vh;
  }
  :global(body) {
    --font-mono: "JetBrains Mono", "Fira Mono", monospace;
  }

  .app {
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
  }

  header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0 24px;
    height: 48px;
    background: #212827;
    border-bottom: 1px solid #2e3d3a;
    flex-shrink: 0;
  }
  .logo {
    font-family: var(--font-mono);
    font-size: 16px;
    font-weight: 700;
    color: #1a9e75;
    letter-spacing: 0.05em;
  }
  .subtitle {
    font-size: 12px;
    color: #4a6460;
    letter-spacing: 0.05em;
  }
  .error-banner {
    margin-left: auto;
    background: #2e1a1a;
    border: 1px solid #e05252;
    color: #e05252;
    font-size: 12px;
    padding: 4px 12px;
    border-radius: 5px;
  }

  main {
    display: grid;
    grid-template-columns: 280px 1fr 280px;
    flex: 1;
    overflow: hidden;
  }

  .left-panel,
  .right-panel {
    background: #212827;
    border-right: 1px solid #2e3d3a;
    padding: 16px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 0;
  }
  .right-panel {
    border-right: none;
    border-left: 1px solid #2e3d3a;
  }

  .center-panel {
    padding: 16px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .session-summary {
    background: #212827;
    border: 1px solid #2e3d3a;
    border-radius: 8px;
    padding: 14px 16px;
  }
  .summary-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #6b8a85;
    margin-bottom: 8px;
  }
  .session-summary p {
    margin: 0;
    font-size: 13px;
    line-height: 1.6;
    color: #a0b8b4;
  }

  .divider {
    height: 1px;
    background: #2e3d3a;
    margin: 16px 0;
  }
</style>
