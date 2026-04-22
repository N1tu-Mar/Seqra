<script lang="ts">
  import type { ScoredCandidate } from "../lib/api";

  export let candidate: ScoredCandidate | null = null;

  const SIZE = 220;
  const CX = SIZE / 2;
  const CY = SIZE / 2;
  const R = 80;
  const AXES = 5;

  const LABELS = [
    "Amphipathicity",
    "Stability",
    "MIC",
    "Charge",
    "Hydrophob.",
  ];

  function axisPoint(i: number, r: number): [number, number] {
    const angle = (Math.PI * 2 * i) / AXES - Math.PI / 2;
    return [CX + r * Math.cos(angle), CY + r * Math.sin(angle)];
  }

  function labelPoint(i: number): [number, number] {
    const angle = (Math.PI * 2 * i) / AXES - Math.PI / 2;
    const lr = R + 24;
    return [CX + lr * Math.cos(angle), CY + lr * Math.sin(angle)];
  }

  function gridPolygon(r: number): string {
    return Array.from({ length: AXES }, (_, i) => axisPoint(i, r).join(",")).join(" ");
  }

  function getValues(c: ScoredCandidate): number[] {
    const amph = c.amphipathicity; // 0-1
    const stability = c.toxicity === "low" ? 1.0 : c.toxicity === "medium" ? 0.5 : 0.0;
    const micNorm = Math.max(0, Math.min(1, 1 - (Math.log(c.mic_estimate) - Math.log(0.5)) / (Math.log(128) - Math.log(0.5))));
    const chargeNorm = Math.max(0, Math.min(1, (c.charge - 2) / 7));
    // hydrophobicity: normalize from -4.5 to 4.5
    const hydNorm = Math.max(0, Math.min(1, (c.hydrophobicity + 4.5) / 9));
    return [amph, stability, micNorm, chargeNorm, hydNorm];
  }

  function dataPolygon(c: ScoredCandidate): string {
    const vals = getValues(c);
    return vals.map((v, i) => axisPoint(i, v * R).join(",")).join(" ");
  }
</script>

<div class="radar-wrap">
  <div class="panel-title">Scoring Radar</div>

  {#if !candidate}
    <div class="empty">Select a candidate.</div>
  {:else}
    <svg width={SIZE} height={SIZE} viewBox="0 0 {SIZE} {SIZE}">
      <!-- Grid rings -->
      {#each [0.25, 0.5, 0.75, 1.0] as frac}
        <polygon
          points={gridPolygon(R * frac)}
          fill="none"
          stroke="#2e3d3a"
          stroke-width="1"
        />
      {/each}

      <!-- Axis lines -->
      {#each Array.from({ length: AXES }, (_, i) => i) as i}
        {@const [ax, ay] = axisPoint(i, R)}
        <line x1={CX} y1={CY} x2={ax} y2={ay} stroke="#2e3d3a" stroke-width="1" />
      {/each}

      <!-- Data polygon -->
      <polygon
        points={dataPolygon(candidate)}
        fill="#1a9e75"
        fill-opacity="0.35"
        stroke="#1a9e75"
        stroke-width="1.5"
      />

      <!-- Axis labels -->
      {#each LABELS as label, i}
        {@const [lx, ly] = labelPoint(i)}
        <text
          x={lx}
          y={ly}
          text-anchor="middle"
          dominant-baseline="middle"
          font-size="9"
          fill="#6b8a85"
          font-family="Inter, sans-serif"
        >{label}</text>
      {/each}
    </svg>

    <div class="legend">
      <div class="legend-row">
        <span class="dot"></span>
        <span>Score: {(candidate.composite_score * 100).toFixed(0)}/100</span>
      </div>
    </div>
  {/if}
</div>

<style>
  .radar-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    width: 100%;
  }
  .panel-title {
    font-size: 11px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #6b8a85;
    align-self: flex-start;
  }
  .empty {
    color: #4a6460;
    font-size: 13px;
    margin-top: 20px;
  }
  svg {
    overflow: visible;
  }
  .legend {
    display: flex;
    flex-direction: column;
    gap: 4px;
    font-size: 12px;
    color: #6b8a85;
  }
  .legend-row {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .dot {
    width: 10px;
    height: 10px;
    background: #1a9e75;
    border-radius: 2px;
    opacity: 0.7;
  }
</style>
