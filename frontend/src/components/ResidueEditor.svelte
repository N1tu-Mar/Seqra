<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import type { LockedResidue } from "../lib/api";

  export let sequence: string = "";
  export let lockedResidues: LockedResidue[] = [];

  const dispatch = createEventDispatcher();

  const AA_LIST = [
    "A","C","D","E","F","G","H","I","K","L",
    "M","N","P","Q","R","S","T","V","W","Y"
  ];
  const AA_NAMES: Record<string, string> = {
    A:"Ala",C:"Cys",D:"Asp",E:"Glu",F:"Phe",G:"Gly",H:"His",
    I:"Ile",K:"Lys",L:"Leu",M:"Met",N:"Asn",P:"Pro",Q:"Gln",
    R:"Arg",S:"Ser",T:"Thr",V:"Val",W:"Trp",Y:"Tyr"
  };

  let selectedPos: number | null = null;
  let replacementResidue: string = "K";
  let lockThis: boolean = false;

  $: selectedAA = selectedPos !== null ? (sequence[selectedPos] || "") : "";
  $: isLocked = selectedPos !== null && lockedResidues.some(r => r.position === selectedPos);

  function selectResidue(i: number) {
    selectedPos = i;
    replacementResidue = sequence[i] || "K";
    lockThis = lockedResidues.some(r => r.position === i);
  }

  function applyLock() {
    if (selectedPos === null) return;
    dispatch("lock", { position: selectedPos, residue: replacementResidue });
  }

  function handleRegenerate() {
    if (selectedPos === null) return;
    dispatch("regenerate", { position: selectedPos });
  }
</script>

<div class="panel">
  <div class="panel-title">Residue Editor</div>

  {#if !sequence}
    <div class="empty">Select a candidate to edit residues.</div>
  {:else}
    <div class="seq-display">
      {#each sequence.split("") as aa, i}
        {@const locked = lockedResidues.some(r => r.position === i)}
        <button
          class="aa {selectedPos === i ? 'selected' : ''} {locked ? 'locked' : ''}"
          on:click={() => selectResidue(i)}
          title="{aa}{i+1} ({AA_NAMES[aa] || aa}){locked ? ' — locked' : ''}"
        >
          {aa}
          {#if locked}<span class="lock-dot">•</span>{/if}
        </button>
      {/each}
    </div>

    {#if selectedPos !== null}
      <div class="editor-row">
        <div class="selected-info">
          Selected: <strong>{selectedAA}{selectedPos + 1}</strong>
          ({AA_NAMES[selectedAA] || selectedAA})
          {#if isLocked}<span class="locked-badge">locked</span>{/if}
        </div>

        <div class="controls">
          <label class="control-label" for="residue-select">Replace with</label>
          <select id="residue-select" bind:value={replacementResidue}>
            {#each AA_LIST as aa}
              <option value={aa}>{aa} — {AA_NAMES[aa]}</option>
            {/each}
          </select>

          <label class="checkbox-row">
            <input type="checkbox" bind:checked={lockThis} on:change={applyLock} />
            <span>Lock this position</span>
          </label>

          <button class="regen-btn" on:click={handleRegenerate}>
            Regenerate around {selectedAA}{selectedPos + 1}
          </button>
        </div>
      </div>
    {/if}

    {#if lockedResidues.length > 0}
      <div class="locked-list">
        <span class="panel-title">Locked</span>
        <div class="lock-chips">
          {#each lockedResidues as lr}
            <span class="chip">{lr.residue}{lr.position + 1}</span>
          {/each}
        </div>
      </div>
    {/if}
  {/if}
</div>

<style>
  .panel { display:flex; flex-direction:column; gap:12px; }
  .panel-title { font-size:11px; letter-spacing:0.1em; text-transform:uppercase; color:#6b8a85; }
  .empty { color:#4a6460; font-size:13px; margin-top:12px; }

  .seq-display {
    display:flex; flex-wrap:wrap; gap:3px;
    background:#1a1f1e; padding:10px; border-radius:6px;
    border:1px solid #2e3d3a;
  }
  .aa {
    font-family:"JetBrains Mono",monospace;
    font-size:13px; width:22px; height:22px;
    display:flex; align-items:center; justify-content:center;
    position:relative;
    background:#212827; border:1px solid #2e3d3a;
    border-radius:3px; color:#c8d4d2; cursor:pointer;
    padding:0; transition:border-color 0.1s;
  }
  .aa:hover { border-color:#1a9e75; }
  .aa.selected { border-color:#1a9e75; background:#1e2e2a; color:#1a9e75; }
  .aa.locked { border-color:#e6a817; color:#e6a817; }
  .lock-dot { position:absolute; bottom:1px; right:2px; font-size:7px; color:#e6a817; line-height:1; }

  .editor-row { display:flex; flex-direction:column; gap:10px; }
  .selected-info { font-size:13px; color:#c8d4d2; }
  .selected-info strong { color:#1a9e75; }
  .locked-badge {
    display:inline-block; margin-left:6px;
    background:#2e2200; border:1px solid #e6a817; color:#e6a817;
    font-size:10px; padding:1px 5px; border-radius:3px;
  }

  .controls { display:flex; flex-direction:column; gap:8px; }
  .control-label { font-size:11px; color:#6b8a85; }
  select {
    background:#1a1f1e; border:1px solid #2e3d3a; border-radius:5px;
    color:#c8d4d2; font-size:13px; padding:6px 8px; outline:none;
  }
  select:focus { border-color:#1a9e75; }

  .checkbox-row { display:flex; align-items:center; gap:8px; font-size:13px; color:#c8d4d2; cursor:pointer; }
  .checkbox-row input { accent-color:#e6a817; }

  .regen-btn {
    background:#1e2e2a; border:1px solid #1a9e75; color:#1a9e75;
    border-radius:5px; padding:7px 12px; font-size:12px; cursor:pointer;
    transition:background 0.15s;
  }
  .regen-btn:hover { background:#1a2e26; }

  .locked-list { display:flex; flex-direction:column; gap:6px; }
  .lock-chips { display:flex; flex-wrap:wrap; gap:5px; }
  .chip {
    font-family:"JetBrains Mono",monospace; font-size:11px;
    background:#2e2200; border:1px solid #e6a817; color:#e6a817;
    padding:2px 7px; border-radius:3px;
  }
</style>
