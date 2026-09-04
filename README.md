# RazorpayX Circular Fraud Detector

> A prototype fraud detection pipeline combining sliding-window graph cycle detection with LLM-assisted Suspicious Activity Report (SAR) generation and automated payout mitigation on synthetic transaction ledgers.

---

## Overview

Circular fraud (round-tripping) occurs when coordinated entities route funds through multi-hop cycles (e.g., $A \to B \to C \to A$) to manufacture artificial transaction volume, exploit payout terms, or launder illicit capital. Traditional rule engines and static blacklists often miss these topologies because transactions are split below alert thresholds across newly minted shell entities.

This repository implements a proof-of-concept architecture exploring:
1. **Topology Detection:** Ingesting transactions into a directed multigraph and isolating closed $\le 3$-hop money loops within a 72-hour sliding window.
2. **Contextual Enrichment:** Extracting KYC metadata (IP subnets, MCC business categories, account age, incorporation delta) for flagged entities.
3. **LLM Investigation:** Querying an LLM analyst powered by **NVIDIA Nemotron Super 120B** (with automated fallback to **Nemotron Ultra 550B**) to evaluate circular flows against entity metadata and generate structured SAR recommendations.
4. **Mitigation & Auditing:** Triggering mock payout suspension hooks (`POST /v1/payouts/{id}/suspend`) and logging decisions to `audit_log.jsonl`.

---

## Architecture & Data Flow

```
Transaction Stream (CSV)
         │
         ▼
┌─────────────────────────────────┐
│ GraphEngine (graph_engine.py)   │
│ - 72h sliding window eviction   │
│ - Directed multigraph (NetworkX)│
│ - 3-hop cycle identification    │
└────────────────┬────────────────┘
                 │ Flagged Cycle
                 ▼
┌─────────────────────────────────┐
│ SAR Agent (sar_agent.py)        │
│ - Entity KYC metadata lookup    │
│ - Primary: Nemotron Super 120B  │
│ - Fallback: Nemotron Ultra 550B │
│ - Structured JSON SAR output    │
└────────────────┬────────────────┘
                 │ Verdict & Action
                 ▼
┌─────────────────────────────────┐
│ Mock API & Audit (mock_api.py)  │
│ - Confidence threshold gating   │
│ - Mock POST /v1/payouts/suspend │
│ - Append to audit_log.jsonl     │
└─────────────────────────────────┘
```

### Component Summary

| Component | File | Role |
| :--- | :--- | :--- |
| **Synthetic Generator** | `synthetic_data.py` | Synthesizes train/test transaction ledgers with embedded 3-node fraud rings, legitimate commerce cycles (cafe/bakery/dairy), and background noise. |
| **Graph Engine** | `graph_engine.py` | Maintains a 72-hour sliding window in NetworkX `MultiDiGraph`, detecting closed loops $\le 3$ hops. |
| **SAR Classifier** | `sar_agent.py` | Formats cycle graph data and entity KYC records into a prompt for NVIDIA NIM (`nvidia/nemotron-3-super-120b-a12b`, falling back to `nvidia/nemotron-3-ultra-550b-a55b`). |
| **Remediation API** | `mock_api.py` | Executes mock payout suspension hooks when confidence $\ge 0.75$, falling back to `MONITOR`. |
| **Evaluation Harness** | `evaluate.py` | Runs detector across `test_transactions.csv`, calculates Precision/Recall/F1 against ground truth, and writes audit records. |

---

## Evaluation Results

Running the evaluation suite (`evaluate.py`) on the held-out test set (12 detected cycles: 5 coordinated fraud rings, 7 legitimate merchant loops) with the **Nemotron Super 120B** agent (and **Nemotron Ultra 550B** fallback) achieves **perfect separation**:

| Metric | Score | Analysis |
| :--- | :--- | :--- |
| **Recall** | **1.00** (5 / 5) | All 5 synthetic circular fraud rings are caught and mitigated. |
| **Precision** | **1.00** (5 / 5) | Zero false positives: 0 legitimate merchant cycles incorrectly flagged. |
| **Specificity** | **1.00** (7 / 7) | All 7 legitimate supply-chain loops (cafe/bakery/dairy) correctly cleared. |
| **F1 Score** | **1.00** | Harmonic mean of precision and recall. |

### Confusion Matrix
```
  True Positives  (fraud caught):    5
  False Positives (legit flagged):   0
  True Negatives  (legit cleared):   7
  False Negatives (fraud missed):    0
```

### Solving Prompt Confirmation Bias
Earlier naive zero-shot prompts suffered from severe confirmation bias (flagging 100% of legitimate supply-chain loops as fraud). By adopting a dedicated agent persona ([agents/sar_analyst.md](agents/sar_analyst.md)) with explicit forensic rubrics distinguishing organic supply-chain commerce (staggered incorporation, distinct IP subnets, realistic commercial margins) from coordinated shell rings (shared subnet, identical amounts, clustered registration), the agent achieved flawless discrimination.

---

## Known Bottlenecks & Architectural Trade-offs

1. **Cycle Detection Scalability:**
   - `graph_engine.py` invokes `nx.simple_cycles(self._graph)` on the full graph. Johnson's algorithm is $O((V + E)(C + 1))$. For streaming scale, this must be replaced with a localized bounded DFS/BFS from target to source ($O(d^k)$) restricted to the newly added edge.
2. **Synchronous LLM Calls:**
   - Ingestion synchronously blocks on external LLM inference (with 30s timeouts). High-throughput ledgers require decoupling cycle detection into a message broker (Kafka/RabbitMQ) with asynchronous worker pools handling SAR generation.
3. **Memory & Dedup Growth:**
   - `_seen_cycles` uses an in-memory set of node `frozenset`s that grows indefinitely without TTL eviction. A production deployment requires time-decaying cache keys (e.g., Redis with TTL).

---

## Getting Started

### Prerequisites
- Python 3.10+
- NVIDIA NIM API key ([build.nvidia.com](https://build.nvidia.com)) for live LLM inference

### Installation

```bash
# 1. Clone repository
git clone https://github.com/ydabas-hue/razorpay-circular-fraud-detector.git
cd razorpay-circular-fraud-detector

# 2. Set up virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install openai networkx pandas pytest
```

### Environment Configuration

Configure your credentials by copying `.env.example` to `.env`:

```bash
cp .env.example .env
```

Open `.env` and insert your NVIDIA NIM API key:
```bash
NVIDIA_API_KEY=nvapi-your-key-here
NVIDIA_MODEL=nvidia/nemotron-3-super-120b-a12b
NVIDIA_FALLBACK_MODEL=nvidia/nemotron-3-ultra-550b-a55b
```
The codebase automatically loads settings from `.env`.

### Running Tests

Unit tests verify cycle detection, 72-hour window eviction, mock API thresholds, synthetic data generation, and response parsing / model fallback without requiring an external API key:

```bash
pytest tests/ -v
```

### Generating Synthetic Data

```bash
python3 synthetic_data.py
# Generates data/train_transactions.csv, data/test_transactions.csv, and data/entity_registry.csv
```

### Running Detection Pipeline

```bash
python3 main.py
```

### Running Evaluation Harness

```bash
python3 evaluate.py
```
Outputs live confusion matrix and writes each case to `audit_log.jsonl`.

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.  
Copyright (c) 2026 Yashasvi Dabas.
