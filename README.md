# Incident Response Agent
> **Autonomous AI SRE Assistant with Organizational Memory, Dense Vector Retrieval, and Interactive Runbook Remediation**

---

## 1. Product Overview

Production outages are high-stakes, time-critical events where engineers struggle to diagnose complex distributed failures under severe pressure. While individual engineers come and go, organizations suffer repeat incidents with identical failure signatures because organizational knowledge is fragmented across Slack threads, Jira tickets, and disparate post-mortems.

The **Incident Response Agent** acts as an AI Site Reliability Engineering (SRE) copilot with persistent memory:
1. **Ingests Incident Telemetry**: Consumes raw logs, unhandled stack traces, and PagerDuty/Datadog alerts.
2. **Retrieves Historical Memory**: Executes high-dimensional vector similarity search against past resolved outages.
3. **Explains Precedents**: Demonstrates *why* recommendations are made with explicit links to past verified post-mortems and similarity confidence scores.
4. **Recommends Multi-Stage Remediation**: Synthesizes a 4-stage action plan (Immediate Workaround, Diagnostic Isolation, Permanent Fix, and Post-Recovery Verification).
5. **Interactive Runbook Simulator**: Provides executable CLI commands with a built-in terminal sandbox to safely simulate deployment rollbacks and pod restarts.
6. **Continuous Learning Loop**: When an engineer resolves the incident and submits a post-mortem, the system immediately generates a fresh 384-dimensional vector embedding and indexes it into organizational memory for future retrieval.

### The Central Product Loop
```
New Incident ──► Vector Retrieval ──► Grounded RAG ──► Remediation Plan ──► Runbook Simulation ──► Post-Mortem ──► Vector Indexing ──► Smarter Next Response
```

---

## 2. Tech Stack

- **Frontend**: React 19, TypeScript, Tailwind CSS, Lucide Icons, Canvas Confetti.
- **Backend & Middleware**: Node.js, Express, TSX, Vite (Middleware Mode in development).
- **AI & Reasoning**: Google GenAI SDK (`gemini-3.8-flash`) with structured output schemas + deterministic SRE fallback reasoning engine for 100% demo reliability.
- **Vector Retrieval**: 384-dimensional dense semantic embedding engine with cosine distance computation and hybrid BM25 lexical keyword boosting.
- **Persistence & Catalog**: In-memory persistent incident store, post-mortem knowledge base, and verified SRE runbook library.

---

## 3. Architecture & RAG Pipeline

```
              ┌───────────────────────────────────────┐
              │   Incident / Stack Traces / Alerts    │
              └───────────────────┬───────────────────┘
                                  │
                                  ▼
              ┌───────────────────────────────────────┐
              │ Incident Analyzer & Token Normalizer  │
              └───────────────────┬───────────────────┘
                                  │
                                  ▼
              ┌───────────────────────────────────────┐
              │ Vector Embedding Generation (384-dim) │
              └───────────────────┬───────────────────┘
                                  │
                                  ▼
              ┌───────────────────────────────────────┐
              │ Vector Database / Historical Memory   │
              │  (Top-K Cosine Similarity Retrieval)  │
              └───────────────────┬───────────────────┘
                                  │  Top-5 Historical
                                  │  Precedents & Resolutions
                                  ▼
              ┌───────────────────────────────────────┐
              │ LLM Orchestrator (Gemini 3.8 Flash)   │
              │  Strict Evidence Separation & RAG     │
              └───────────────────┬───────────────────┘
                                  │
                                  ▼
              ┌───────────────────────────────────────┐
              │ Actionable Remediation Plan & Runbook │
              │  (Interactive Checklists & Simulator) │
              └───────────────────┬───────────────────┘
                                  │
                                  ▼
              ┌───────────────────────────────────────┐
              │ Engineer Feedback & Post-Mortem       │
              └───────────────────┬───────────────────┘
                                  │
                                  ▼
              ┌───────────────────────────────────────┐
              │ Vector Embedding & Memory Indexation  │
              │ (Available for Future Retrievals)     │
              └───────────────────────────────────────┘
```

---

## 4. Key Features

- **SRE Dashboard**: High-level telemetry displaying active outages, 142 total incidents, 18m average resolution time (MTTR), 128 vector memories, and live service health monitoring.
- **1-Click Hackathon Demo Presets**:
  - *Demo 1 (Primary)*: Payment API Database Connection Pool Exhaustion (`QueuePool limit of size 100 overflow 0 reached`).
  - *Demo 2*: Kubernetes Payment Service Worker Pods in `CrashLoopBackOff` (`Exit Code 137 - OOMKilled`).
  - *Demo 3*: Redis Connection Timeout Spike in Auth Service (`GenericObjectPool.borrowObject timeout`).
- **Explainable AI Reasoning**: Dedicated "Why This Recommendation?" section detailing past precedents, confidence ratings, and verified resolution rates.
- **Evidence Separation**: Strict separation of *Observed Evidence* (facts in logs), *Historical Evidence* (patterns from memory), and *AI Hypothesis* (unverified diagnosis).
- **Interactive Staged Remediation**: 4 collapsible stages with checkboxes and copyable CLI commands.
- **Runbook Execution Simulator**: Animated SRE terminal window simulating `kubectl rollout undo` and verifying error rate recovery with live telemetry feedback.
- **Memory Explorer**: Full-text and filterable knowledge base of 15 realistic historical incidents with a glowing "Learned Live" badge for memories indexed during the demo.
- **Visual Architecture Page**: Interactive 8-stage architectural deep-dive with technical highlights and formula breakdowns.

---

## 5. Prerequisites

- **Node.js**: v18.0.0 or higher
- **npm**: v9.0.0 or higher

---

## 6. Installation & Quick Start

1. Clone or download the repository:
   ```bash
   git clone <repo-url>
   cd incident-response-agent
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure Environment Variables (Optional):
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Add your Gemini API Key if you wish to use live Google GenAI calls:
   ```bash
   GEMINI_API_KEY="your-gemini-api-key"
   ```
   *(Note: The app contains an intelligent deterministic SRE reasoning engine that automatically operates even if no API key is provided, guaranteeing 100% demo reliability!)*

4. Run the development server:
   ```bash
   npm run dev
   ```
   The application will start at **http://localhost:3000**.

5. Run Automated Tests:
   ```bash
   npm test
   ```

---

## 7. Hackathon Demo Walkthrough (3-5 Minutes)

1. **Open Dashboard**:
   - Observe the 142 total incidents, 128 memories, 42 runbooks, and active service health.
2. **Click "+ New Incident"**:
   - Click **Demo 1: Payment API Database Connection Pool Exhaustion**.
   - Notice the form pre-populates with the exact primary demo scenario:
     ```
     [ERROR] 2026-09-28 14:32:11
     service=payment-api
     status=500
     message="Database connection pool exhausted"
     active_connections=100
     max_connections=100

     ERROR sqlalchemy.exc.TimeoutError:
     QueuePool limit of size 100 overflow 0 reached, connection timed out.
     ```
3. **Click "Analyze Incident"**:
   - Watch the animated AI activity telemetry: Normalizing telemetry → Vector embedding → Searching historical memory → RAG context synthesis.
4. **Examine "Similar Incidents From Memory"**:
   - Notice top match `Payment API database connection pool exhaustion` with **94% similarity** (`94% ███████████████████░`).
5. **Inspect "Why This Recommendation?" & Root Cause**:
   - The AI explains that 3 prior payment-api incidents were resolved by deployment rollback in 7 minutes.
   - Evidence is cleanly categorized: Observed vs. Historical vs. Hypothesis.
6. **Interact with Remediation Plan**:
   - Check off individual steps across the 4 stages.
7. **Run Runbook Simulator**:
   - Click **Run in Simulation**.
   - Watch the interactive terminal execute `kubectl rollout undo` and verify that error rate drops from 48.2% to 0.02%.
8. **Resolve & Demonstrate Continuous Learning**:
   - Click **Mark as Resolved**.
   - Review or edit actual root cause & takeaway.
   - Click **Save to Memory** → Confetti explodes!
   - Navigate to **Incident Memory** tab: see your newly resolved incident at the very top tagged with a glowing **Learned from Live Incident** badge!
   - Now submit another similar payment incident: the system will immediately retrieve your newly learned incident!

---

## 8. REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/metrics` | Retrieve SRE dashboard statistics |
| `GET` | `/api/incidents` | List all active and historical live incidents |
| `POST` | `/api/incidents` | Ingest and create a new incident |
| `GET` | `/api/incidents/:id` | Get specific incident details |
| `POST` | `/api/incidents/:id/analyze` | Execute RAG pipeline and AI analysis |
| `GET` | `/api/incidents/:id/similar` | Retrieve top similar historical memories |
| `POST` | `/api/incidents/:id/step` | Toggle remediation step completion |
| `POST` | `/api/incidents/:id/simulate` | Execute runbook terminal simulation |
| `POST` | `/api/incidents/:id/resolve` | Mark resolved, create post-mortem & index memory |
| `GET` | `/api/memory` | Search and filter organizational vector memory |
| `GET` | `/api/memory/:id` | Get specific post-mortem record |
| `GET` | `/api/runbooks` | List standard SRE runbooks |
| `POST` | `/api/reset` | Reset demo memory and incidents to initial seed state |

---

## 9. Safety & Security Guardrails

- **Zero Arbitrary Execution**: Remediation commands are presented as suggestions and simulation sandboxes. The agent never executes live shell commands without engineer authorization.
- **Clear Hypotheses**: The AI never claims an unverified root cause as an absolute fact without observed evidence.
- **Server-Side API Security**: Gemini API keys are processed strictly on the Express backend and are never leaked to client bundles.
