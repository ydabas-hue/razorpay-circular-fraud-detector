# RazorpayX Circular Fraud Detector

An autonomous financial surveillance pipeline combining a NetworkX graph engine with LLM-powered agentic workflows to detect, analyze, and mitigate 3-hop money-flow anomalies on RazorpayX infrastructure.

## Why This Exists

Traditional fraud detection relies on rigid threshold rules or isolated transaction blacklists. That approach fails against coordinated multi-entity loops (circular round-tripping) where shell entities pass funds in tight 3-hop cycles to launder money or manufacture fake volume. 

The RazorpayX Circular Fraud Detector's premise: transaction topology is a graph problem, and malicious intent requires agentic reasoning. By mapping flows into directed multigraphs and passing flagged neighborhoods to an LLM reasoning engine with real KYC metadata, discovery becomes an automated, auditable defense system.

## How It Works

Four core components drive the detection pipeline:

1. **Graph Topology Analysis (`graph_engine.py`):** Leverages NetworkX (`MultiDiGraph`) to discover closed 3-hop money loops across transaction ledgers, separating organic merchant activity from synthetic circular loops.
2. **Agentic SAR Classifier (`sar_agent.py`):** Interfaces with NVIDIA NIM APIs (Llama 3.2 11B) using constrained JSON prompts to evaluate metadata signals, IP subnet overlap, and merchant category code (MCC) alignment.
3. **Automated Mitigation (`mock_api.py`):** Executes bounded remediation workflows, automatically triggering payout suspension hooks (`POST /v1/payouts/{id}/suspend`) for confirmed frauds.
4. **Evaluation Harness (`evaluate.py`):** Benchmarks detector recall and precision against held-out synthetic validation splits, generating an immutable audit trail (`audit_log.jsonl`).

## System Architecture

1. **Transaction Ingestion & KYC Data:** Raw ledger events and entity metadata are loaded into memory.
2. **Graph Engine:** NetworkX parses the data to isolate closed 3-hop money-flow loops.
3. **NVIDIA NIM LLM Agent:** Flagged nodes and transactions are evaluated for subnet overlaps and MCC anomalies.
4. **Automated Enforcement:** Confirmed fraud routes trigger mock payout freezes and generate structured audit logs.

## Getting Started Locally

### 1. Clone the repository and set up a virtual environment
```bash
git clone [https://github.com/ydabas-hue/razorpay-circular-fraud-detector.git](https://github.com/ydabas-hue/razorpay-circular-fraud-detector.git)
cd razorpay-circular-fraud-detector
python3 -m venv venv
source venv/bin/activate
2. Install dependencies
Bash
pip install openai networkx pandas
3. Configure your NVIDIA NIM API key
Bash
export NVIDIA_API_KEY="nvapi-your-key-here"
4. Run the fraud detection pipeline
Bash
python3 main.py
5. Run the evaluation suite
Bash
python3 evaluate.py
Audit & Compliance Logs
Every detected loop execution writes an immutable JSONL audit event containing confidence scores, entity payloads, and regulatory summaries formatted for filing Suspicious Activity Reports (SAR).
