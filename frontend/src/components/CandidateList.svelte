<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import type { ScoredCandidate } from "../lib/api";

  export let candidates: ScoredCandidate[] = [];
  export let selectedIndex: number = 0;

  const dispatch = createEventDispatcher();

  function stars(score: number): string {
    if (score > 0.7) return "★★★";
    if (score >= 0.4) return "★★☆";
    return "★☆☆";
  }

  function riskColor(val: "low" | "medium" | "high"): string {
    return val === "low" ? "#1a9e75" : val === "medium" ? "#e6a817" : "#e05252";
  }

  function micBarWidth(mic: number): number {
    // 0.5 -> 100%, 128 -> 0%
    const norm = 1 - (Math.log(mic) - Math.log(0.5)) / (Math.log(128) - Math.log(0.5));
    return Math.round(Math.max(0, Math.min(1, norm)) * 100);
  }

  function chargeBarWidth(charge: number): number {
    return Math.round(Math.max(0, Math.min(1, (charge - 2) / 7)) * 100);
  }
</script>

<div class="panel">
  <div class="panel-title">Candidates</div>

  {#if candidates.length === 0}
    <div class="empty">Run a query to generate candidates.</div>
  {:else}
    <div class="tabs">
      {#each candidates as c, i}
        <button
          class="tab {selectedIndex === i ? 'active' : ''}"
          on:click={() => { selectedIndex = i; dispatch("select", i); }}
        >
          #{i + 1} <span class="stars">{stars(c.composite_score)}</span>
        </button>
      {/each}
    </div>

    {#if candidates[selectedIndex]}
      {@const c = candidates[selectedIndex]}
      <div class="candidate-body">
        <div class="sequence">{c.sequence}</div>
        <div class="meta">
          {c.length} aa · {c.length_valid ? "valid length" : "⚠ length out of range"}
        </div>

        <div class="bars">
          <div class="bar-row">
            <span class="bar-label">Charge</span>
            <div class="bar-track">
              <div class="bar-fill" style="width:{chargeBarWidth(c.charge)}%; background:#1a9e75"></div>
            </div>
            <span class="bar-val">{c.charge > 0 ? "+" : ""}{c.charge.toFixed(1)}</span>
          </div>

          <div class="bar-row">
            <span class="bar-label">MIC</span>
            <div class="bar-track">
              <div class="bar-fill" style="width:{micBarWidth(c.mic_estimate)}%; background:#1a9e75"></div>
            </div>
            <span class="bar-val">{c.mic_estimate} µg/mL</span>
          </div>

          <div class="bar-row">
            <span class="bar-label">Hemolysis</span>
            <div class="bar-track">
              <div class="bar-fill risk" style="width:{c.hemolysis==='low'?30:c.hemolysis==='medium'?65:100}%; background:{riskColor(c.hemolysis)}"></div>
            </div>
            <span class="bar-val" style="color:{riskColor(c.hemolysis)}">{c.hemolysis}</span>
          </div>

          <div class="bar-row">
            <span class="bar-label">Toxicity</span>
            <div class="bar-track">
              <div class="bar-fill risk" style="width:{c.toxicity==='low'?30:c.toxicity==='medium'?65:100}%; background:{riskColor(c.toxicity)}"></div>
            </div>
            <span class="bar-val" style="color:{riskColor(c.toxicity)}">{c.toxicity}</span>
          </div>
        </div>

        <div class="score-line">
          Composite score: <strong>{(c.composite_score * 100).toFixed(0)}/100</strong>
        </div>

        {#if c.summary}
          <div class="summary">{c.summary}</div>
        {/if}
      </div>
    {/if}
  {/if}
</div>

<style>
  .panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    gap: 12px;
  }
  .panel-title {
    font-size: 11px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #6b8a85;
  }
  .empty {
    color: #4a6460;
    font-size: 13px;
    margin-top: 20px;
    text-align: center;
  }
  .tabs {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
  }
  .tab {
    background: #1a1f1e;
    border: 1px solid #2e3d3a;
    border-radius: 5px;
    color: #6b8a85;
    font-size: 12px;
    padding: 5px 10px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 5px;
    transition: border-color 0.15s;
  }
  .tab.active {
    border-color: #1a9e75;
    color: #c8d4d2;
  }
  .stars {
    font-size: 11px;
    letter-spacing: 1px;
    color: #e6a817;
  }
  .candidate-body {
    display: flex;
    flex-direction: column;
    gap: 10px;
    overflow-y: auto;
    flex: 1;
  }
  .sequence {
    font-family: "JetBrains Mono", monospace;
    font-size: 14px;
    color: #1a9e75;
    word-break: break-all;
    letter-spacing: 0.05em;
    background: #1a1f1e;
    padding: 10px 12px;
    border-radius: 6px;
    border: 1px solid #2e3d3a;
  }
  .meta {
    font-size: 12px;
    color: #6b8a85;
  }
  .bars {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .bar-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .bar-label {
    font-size: 12px;
    color: #6b8a85;
    width: 72px;
    flex-shrink: 0;
  }
  .bar-track {
    flex: 1;
    height: 6px;
    background: #2e3d3a;
    border-radius: 3px;
    overflow: hidden;
  }
  .bar-fill {
    height: 100%;
    border-radius: 3px;
    transition: width 0.4s ease;
  }
  .bar-val {
    font-size: 12px;
    color: #c8d4d2;
    width: 80px;
    text-align: right;
    flex-shrink: 0;
  }
  .score-line {
    font-size: 13px;
    color: #6b8a85;
  }
  .score-line strong {
    color: #1a9e75;
  }
  .summary {
    font-size: 13px;
    color: #a0b8b4;
    line-height: 1.6;
    background: #1a1f1e;
    border-left: 2px solid #1a9e75;
    padding: 10px 12px;
    border-radius: 0 6px 6px 0;
  }
</style>
