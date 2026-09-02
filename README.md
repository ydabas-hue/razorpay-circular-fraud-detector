# RazorpayX Circular Fraud Detector

Graph-based agentic security pipeline for identifying multi-entity shell company fraud on RazorpayX infrastructure.

## Why this exists

Traditional fraud detection relies on rigid static threshold rules or isolated transaction blacklists. That approach completely fails against coordinated multi-entity loops (circular round-tripping) where shell entities pass funds in tight 3-hop cycles to launder money or manufacture fake volume.

| Failure Mode | What It Costs You |
| :--- | :--- |
| **Static Thresholds** | Sophisticated rings fragment transactions just below alert limits, remaining invisible to rule-based engines. |
| **Isolated Blacklists** | Newly generated shell accounts bypass static blacklists entirely because they have no historical record. |
| **Lack of Context** | Systems flag raw movement without analyzing whether connected merchants share IP subnets or mismatched MCC codes. |

The RazorpayX Circular Fraud Detector's premise: transaction topology is a graph problem, and malicious intent requires agentic reasoning. By mapping flows into directed multigraphs and passing flagged neighborhoods to an LLM reasoning engine with real KYC metadata, discovery becomes an automated, auditable defense system.

## How it works

Four core components drive the detection pipeline:

1. **Graph topology analysis (`graph_engine.py`):** Leverages NetworkX (`MultiDiGraph`) to discover closed 3-hop money loops across transaction ledgers, separating organic merchant activity from synthetic circular loops.
2. **Agentic SAR classifier (`sar_agent.py`):** Interfaces with NVIDIA NIM APIs (`meta/llama-3.2-11b-vision-instruct`) using constrained JSON prompts to evaluate metadata signals, IP subnet overlap, and merchant category code (MCC) alignment.
3. **Automated mitigation (`mock_api.py`):** Executes bounded remediation workflows, automatically triggering payout suspension hooks (`POST /v1/payouts/{id}/suspend`) for confirmed frauds.
4. **Evaluation harness (`evaluate.py`):** Benchmarks detector recall and precision against held-out synthetic validation splits, generating an immutable audit trail (`audit_log.jsonl`).

## Stack

| Layer | Choice | Why |
| :--- | :--- | :--- |
| **Graph Engine** | NetworkX (`MultiDiGraph`) | Native directed multigraph support to isolate closed circular transaction loops efficiently. |
| **LLM Agent** | NVIDIA NIM (`meta/llama-3.2-11b-vision-instruct`) | High-speed inference model for deep analysis of complex KYC payloads and strict JSON verdicts. |
| **Data Processing** | Pandas + NumPy | Fast manipulation of transaction ledgers and entity metadata registries. |
| **Auditing & Logs** | JSONL (`audit_log.jsonl`) | Immutable, line-delimited audit trails structured for filing Suspicious Activity Reports (SAR). |

## Getting Started Locally

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/ydabas-hue/razorpay-circular-fraud-detector.git](https://github.com/ydabas-hue/razorpay-circular-fraud-detector.git)
   cd razorpay-circular-fraud-detector
Create and activate a virtual environment:

Bash
python3 -m venv venv
source venv/bin/activate
Install dependencies:

Bash
pip install openai networkx pandas pytest
Configure your NVIDIA NIM API key:

Bash
export NVIDIA_API_KEY="nvapi-your-key-here"
Run the test suite:

Bash
pytest tests/ -v   # Verifies core graph and mock execution components
Run the fraud detection pipeline:

Bash
python3 main.py
Run the evaluation suite:

Bash
python3 evaluate.py
Results
Run the evaluation harness to generate live results against the held-out test set:

Bash
export NVIDIA_API_KEY="nvapi-your-key-here"
python3 evaluate.py
The harness prints a live confusion matrix and F1 score to stdout and appends every decision to audit_log.jsonl for inspection.
