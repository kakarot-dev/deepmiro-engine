---
name: predict
description: Run a DeepMiro swarm prediction — multi-agent social media simulation that predicts how communities react to events, policies, or announcements. Use when the user says "predict", "simulate", "how will people react", "what would happen if", or wants to model social dynamics.
argument-hint: [scenario] [optional-file-path]
disable-model-invocation: true
---

# DeepMiro Predict

## Step 0: Setup Check (MUST run first)

Check if the `create_simulation` MCP tool exists and is callable.

**If tools ARE available:** Skip to Step 1.

**If tools are NOT available (MCP disconnected):**

Ask the user:
> "DeepMiro isn't connected yet. Choose one:
> 1. **Hosted** — paste your API key from https://deepmiro.org
> 2. **Self-hosted** — I'll point to your local instance
> 3. **Manual** — I'll give you the commands to run yourself"

Then wait for their response.

### Auto-setup (if user provides API key or says self-hosted)

**If they provide an API key:**

Try to run:
```bash
claude mcp add deepmiro --transport http https://deepmiro.org/mcp -e DEEPMIRO_API_KEY=<their_key>
```

Also try to install the standalone `/predict` skill:
```bash
mkdir -p ~/.claude/skills/predict
```
Then copy this skill's workflow section to `~/.claude/skills/predict/SKILL.md`.

**If they say self-hosted:**

Ask for URL (default `http://localhost:3001/mcp`), then:
```bash
claude mcp add deepmiro --transport http <url>
```

### If user denies permissions or chooses manual:

Give them the commands to run themselves:
> "Run these in your terminal:
> ```
> claude mcp add deepmiro --transport http https://deepmiro.org/mcp -e DEEPMIRO_API_KEY=dm_your_key
> ```
> Then restart Claude Code. After that, `/deepmiro:predict` will work."
>
> For self-hosted:
> ```
> claude mcp add deepmiro --transport http http://localhost:3001/mcp
> ```

### After any setup path:

Tell user: "Restart Claude Code for the connection to activate. Then use `/predict` (or `/deepmiro:predict`) to run simulations."

**Stop here after setup. Do not proceed with the workflow until MCP is connected.**

---

## Step 1: Connectivity Test

Call `list_simulations` with `limit: 1` to verify the connection.

- **Success (returns list):** Proceed.
- **Auth/401 error:** Go back to Step 0 setup flow.
- **Connection error:** "Can't reach DeepMiro. Check your API key and network."

---

## Workflow

### Step 2: Upload document (if applicable)

If the user provided a file path in $ARGUMENTS or referenced a file earlier:
1. Call `upload_document` with the file path
2. Save `document_id`
3. "Uploaded your document — using it to build the knowledge graph."

No file? Skip to Step 3.

### Step 3: Choose preset

- **"quick"** — user said "quick", "fast", "rough idea"
- **"standard"** (default) — most predictions
- **"deep"** — user said "deep", "thorough", or provided a large document

### Step 4: Create simulation

Call `create_simulation` with prompt, document_id (optional), preset.

> "Simulation started. I'll narrate as the personas interact — you can keep working."

### Step 5: Monitor and narrate

Poll `simulation_status` every 30 seconds. Narrate naturally based on `phase`:

**building_graph:**
> "Building knowledge graph... {progress}%"

**generating_profiles:**
> "Creating personas: {profiles_generated}/{entities_count} — {recent_profiles}"

**simulating:**
Use entity names and action content:
> "Round 15/40 — 127 interactions. Prof. Zhang tweeted: 'Our research output shows remarkable growth...' Li Wei liked it."

**completed:** Move to Step 6.

If over 15 minutes: "Still running — I'll notify you when done."

### Step 6: Present report

Call `get_report`. Present the analysis. Then offer:
> "Want me to:
> - **Interview a persona** about their motivations
> - **Run a different scenario**
> - **Search past simulations**"

### Step 7: Interview (optional)

Call `interview_agent` with simulation_id, agent name, and user's question.

---

## Rules

- **Names not IDs** — "Prof. Zhang" not "Agent_34"
- **No base64** — always `upload_document` first, pass `document_id`
- **Error recovery** — if sim fails, retry with smaller preset
- **Quick predict** — for fast opinions use `quick_predict`, mention full sim is available
