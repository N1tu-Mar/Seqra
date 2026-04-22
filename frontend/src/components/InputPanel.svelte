<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import { parseQuery } from "../lib/api";
  import type { GenerationParams } from "../lib/api";

  const dispatch = createEventDispatcher();

  export let loading = false;

  let chatInput = "";
  let chatHistory: Array<{ role: "user" | "assistant"; text: string }> = [
    {
      role: "assistant",
      text: 'Welcome to Seqra. Describe what you need — e.g. "generate MRSA candidates, low toxicity, topical delivery".',
    },
  ];

  let constraints = {
    low_hemolysis: true,
    serum_stable: false,
    topical_delivery: true,
  };

  async function sendMessage() {
    const msg = chatInput.trim();
    if (!msg || loading) return;
    chatHistory = [...chatHistory, { role: "user", text: msg }];
    chatInput = "";
    chatHistory = [
      ...chatHistory,
      { role: "assistant", text: "Parsing query..." },
    ];

    try {
      const params: GenerationParams = await parseQuery(msg);
      if (constraints.low_hemolysis) params.max_hemolysis = "low";
      if (constraints.topical_delivery) params.delivery_mode = "topical";

      chatHistory = chatHistory.slice(0, -1);
      chatHistory = [
        ...chatHistory,
        {
          role: "assistant",
          text: `Generating candidates for: ${params.target_pathogen || "unknown pathogen"} | gram-${params.gram_type} | ${params.delivery_mode} delivery | toxicity ≤ ${params.max_toxicity}`,
        },
      ];
      dispatch("generate", params);
    } catch (e) {
      chatHistory = chatHistory.slice(0, -1);
      chatHistory = [
        ...chatHistory,
        { role: "assistant", text: "Failed to parse query. Try again." },
      ];
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }
</script>

<div class="panel">
  <div class="panel-title">Query</div>

  <div class="constraints">
    <label class="checkbox-row">
      <input type="checkbox" bind:checked={constraints.low_hemolysis} />
      <span>Low hemolysis</span>
    </label>
    <label class="checkbox-row">
      <input type="checkbox" bind:checked={constraints.serum_stable} />
      <span>Serum stable</span>
    </label>
    <label class="checkbox-row">
      <input type="checkbox" bind:checked={constraints.topical_delivery} />
      <span>Topical delivery</span>
    </label>
  </div>

  <div class="chat-log" id="chat-log">
    {#each chatHistory as msg}
      <div class="msg {msg.role}">
        <span class="role-label">{msg.role === "user" ? "You" : "Seqra"}</span>
        <p>{msg.text}</p>
      </div>
    {/each}
  </div>

  <div class="chat-input-row">
    <textarea
      bind:value={chatInput}
      on:keydown={handleKeydown}
      placeholder="ask or refine..."
      rows="3"
      disabled={loading}
    ></textarea>
    <button on:click={sendMessage} disabled={loading || !chatInput.trim()}>
      {#if loading}
        <span class="spinner"></span>
      {:else}
        Send
      {/if}
    </button>
  </div>
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
    margin-bottom: 4px;
  }
  .constraints {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .checkbox-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    cursor: pointer;
    color: #c8d4d2;
  }
  .checkbox-row input[type="checkbox"] {
    accent-color: #1a9e75;
    width: 14px;
    height: 14px;
  }
  .chat-log {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding-right: 4px;
  }
  .msg {
    display: flex;
    flex-direction: column;
    gap: 3px;
  }
  .role-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #6b8a85;
  }
  .msg.user .role-label {
    color: #1a9e75;
  }
  .msg p {
    margin: 0;
    font-size: 13px;
    line-height: 1.5;
    color: #c8d4d2;
    background: #1a1f1e;
    padding: 8px 10px;
    border-radius: 6px;
  }
  .msg.user p {
    background: #1e2e2a;
  }
  .chat-input-row {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  textarea {
    width: 100%;
    background: #1a1f1e;
    border: 1px solid #2e3d3a;
    border-radius: 6px;
    color: #c8d4d2;
    font-family: "Inter", sans-serif;
    font-size: 13px;
    padding: 8px 10px;
    resize: none;
    box-sizing: border-box;
    outline: none;
  }
  textarea:focus {
    border-color: #1a9e75;
  }
  button {
    background: #1a9e75;
    color: #fff;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    cursor: pointer;
    align-self: flex-end;
    min-width: 64px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  button:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }
  .spinner {
    width: 14px;
    height: 14px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: #fff;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    display: inline-block;
  }
  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }
</style>
