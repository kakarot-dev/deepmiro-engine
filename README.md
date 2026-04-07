<div align="center">

<img src="./static/image/deepmiro-lockup.png" alt="DeepMiro Engine" width="420"/>

<br/>

**A swarm intelligence engine that rehearses the future.**

Feed it a document. Describe a scenario. Watch thousands of AI agents with distinct personalities, memories, and social instincts interact — and return with a prediction.

[![License](https://img.shields.io/badge/License-AGPL--3.0-blue?style=flat-square)](./LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat-square&logo=docker&logoColor=white)](#-docker-deployment)
[![Website](https://img.shields.io/badge/deepmiro.org-live-22d3ee?style=flat-square)](https://deepmiro.org)

</div>

---

## 🧠 What It Does

DeepMiro extracts entities and relationships from any document — a policy draft, a market report, a chapter of a novel — and constructs a parallel digital world. Inside it, hundreds of autonomous agents form opinions, argue on simulated social platforms, shift allegiances, and produce emergent behavior that no single prompt could predict.

You get back a structured prediction report and a living world you can interrogate, agent by agent.

> **Input:** A PDF and a question in plain language.
> **Output:** A detailed prediction report + an interactive simulation you can explore.

## ⚙️ How It Works

```
Document ──► Entity Extraction ──► Agent Generation ──► Dual-Platform Simulation ──► Prediction Report
              (NER + GraphRAG)    (personas, memory,     (Twitter-like + Reddit-like     (ReportAgent with
                                   social networks)       parallel interaction)            deep analysis tools)
```

Five phases, fully automated:

| Phase | What happens |
|-------|-------------|
| 🔗 **Graph Build** | Extracts entities, relationships, and context from your documents. Builds a knowledge graph via GraphRAG. |
| 🧬 **Environment Setup** | Generates agent personas with distinct personalities, beliefs, and social connections. Configures behavioral parameters. |
| 🌐 **Simulation** | Agents interact across dual platforms (Twitter-like and Reddit-like) in parallel. Dynamic memory updates each round. |
| 📊 **Report Generation** | A ReportAgent analyzes the post-simulation environment — sentiment shifts, faction formation, viral dynamics, outcome trajectories. |
| 💬 **Deep Interaction** | Chat with any agent to understand their reasoning. Query the ReportAgent for follow-up analysis. |

## 🔑 Key Capabilities

- 📄 **Document-seeded worlds** — upload PDFs, reports, articles. The engine extracts reality seeds and builds a simulation around them.
- 🤖 **Autonomous agents** — each agent has a unique persona, long-term memory, and behavioral logic. They aren't scripted — they emerge.
- 🔀 **Dual-platform dynamics** — agents interact on both a Twitter-like and Reddit-like platform simultaneously, producing richer social dynamics.
- 👁️ **God's-eye control** — inject variables mid-simulation, adjust scenarios, test counterfactuals.
- 📈 **Structured reports** — the ReportAgent produces analysis with sentiment breakdowns, key faction identification, and outcome probabilities.
- 🎙️ **Agent interrogation** — after simulation, interview any agent to understand their beliefs and decision process.

## ⚡ Performance

Benchmarked on a 15-agent quick simulation with enriched prompts:

| Stage | Time |
|-------|------|
| Graph build | ~10s |
| Agent generation | ~3 min |
| Simulation (110 Twitter + 26 Reddit actions) | ~4 min |
| **Total pipeline** | **~7 min (quick) / ~12 min (standard, 80 agents)** |

Key optimizations over the base engine:
- 🧲 **Cached TWHIN-BERT** recommendation system — 15ms/round (down from 200s)
- ⚡ **Parallel NER** with 5 concurrent workers — graph build 5min → 56s
- 🗄️ **WAL mode** on SQLite for concurrent read performance

## 🚀 Quick Start

### Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| 🐍 **Python** | 3.11 – 3.12 | `python --version` |
| 📦 **Node.js** | 18+ | `node -v` |
| ⚙️ **uv** | Latest | `uv --version` |

### 1. Configure

```bash
cp .env.example .env
```

Required environment variables:

```env
# LLM — any OpenAI-compatible API
LLM_API_KEY=your_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o

# Database
SURREALDB_URL=ws://localhost:8000/rpc
SURREALDB_USER=root
SURREALDB_PASS=root
```

### 2. Install

```bash
npm run setup:all
```

Or step by step:

```bash
npm run setup           # Node dependencies (root + frontend)
npm run setup:backend   # Python dependencies (auto-creates venv)
```

### 3. Run

```bash
npm run dev
```

| Service | URL |
|---------|-----|
| 🖥️ Frontend | `http://localhost:3000` |
| 🔌 Backend API | `http://localhost:5001` |

### 🐳 Docker Deployment

```bash
cp .env.example .env    # configure your keys
docker compose up -d
```

## 🏗️ Architecture

```
deepmiro-engine/
├── backend/                 # Python Flask API
│   ├── app/
│   │   ├── api/            # REST endpoints (simulation, graph, documents, report)
│   │   ├── services/       # Core logic (graph builder, simulation runner, report agent)
│   │   ├── storage/        # SurrealDB adapter, embedding service, NER
│   │   └── utils/          # LLM client, retry logic, logging
│   └── pyproject.toml
├── frontend/                # Vue 3 + Vite
│   ├── src/
│   │   ├── components/     # 5-step workflow UI
│   │   ├── views/          # Home, Simulation, Report, Interaction
│   │   └── api/            # API client
│   └── vite.config.js
├── locales/                 # i18n (en, zh)
├── docker-compose.yml
└── Dockerfile
```

## 💡 Use Cases

| Domain | Example |
|--------|---------|
| 📉 **Market analysis** | Upload an earnings report. Ask: *"How will retail investors react to this guidance revision?"* |
| 🏛️ **Policy testing** | Upload a draft regulation. Ask: *"What public backlash should we expect, and from which demographics?"* |
| 📣 **PR & comms** | Upload a press release. Ask: *"How will this announcement play on social media over 48 hours?"* |
| 🏁 **Competitive analysis** | Upload competitor product specs. Ask: *"How will our user base respond to this feature gap?"* |
| 📖 **Creative exploration** | Upload a novel's first 80 chapters. Ask: *"What ending would emerge from these character dynamics?"* |
| 🚨 **Crisis simulation** | Upload an incident report. Ask: *"How does public opinion evolve if we respond with X vs Y?"* |

## 🙏 Acknowledgments

DeepMiro Engine is a fork of [MiroFish](https://github.com/666ghj/MiroFish), originally created by Guo Hangjiang and supported by Shanda Group. The simulation layer is powered by [OASIS](https://github.com/camel-ai/oasis) from the CAMEL-AI team.

## 📄 License

[AGPL-3.0](./LICENSE)

---

<div align="center">

**[deepmiro.org](https://deepmiro.org)** · Built by [Joel Libni](https://github.com/kakarot-dev)

</div>
