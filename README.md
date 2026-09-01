# RazorpayX Circular Fraud Detector

An autonomous financial surveillance pipeline combining a NetworkX graph engine with NVIDIA NIM agentic workflows to detect, analyze, and mitigate 3-hop money-flow anomalies on RazorpayX infrastructure.

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

```mermaid
graph TD
    A[Transaction Ledger & KYC Data] -->|Raw Events| B[Graph Engine: NetworkX MultiDiGraph]
    B -->|Discovers Closed 3-Hop Loops| C[NVIDIA NIM Agent: Llama 3.2 11B]
    C -->|Evaluates IP Subnets & MCC Codes| D{Verdict Analysis}
    D -->|Fraud Detected| E[Trigger Mock Payout Freezes & Log JSONL Audit]
    D -->|Legitimate Loop| F[Clear Entity / Normal Monitoring]
Graph topology analysis (graph_engine.py): Leverages NetworkX (MultiDiGraph) to discover closed 3-hop money loops across transaction ledgers, separating organic merchant activity from synthetic circular loops.Agentic SAR classifier (sar_agent.py): Interfaces with NVIDIA NIM APIs (Llama 3.2 11B) using constrained JSON prompts to evaluate metadata signals, IP subnet overlap, and merchant category code (MCC) alignment.Automated mitigation (mock_api.py): Executes bounded remediation workflows, automatically triggering payout suspension hooks (POST /v1/payouts/{id}/suspend) for confirmed frauds.Evaluation harness (evaluate.py): Benchmarks detector recall and precision against held-out synthetic validation splits, generating an immutable audit trail (audit_log.jsonl).StackLayerChoiceWhyGraph EngineNetworkX (MultiDiGraph)Native directed multigraph support to isolate closed circular transaction loops efficiently.LLM AgentNVIDIA NIM (meta/llama-3.2-11b-vision-instruct)High-speed inference for processing KYC payloads and generating strict JSON verdicts.Data ProcessingPandas + NumPyFast manipulation of transaction ledgers and entity metadata registries.Auditing & LogsJSONL (audit_log.jsonl)Immutable, line-delimited audit trails structured for filing Suspicial Activity Reports (SAR).Getting Started LocallyClone the repository:Bashgit clone [https://github.com/ydabas-hue/razorpay-circular-fraud-detector.git](https://github.com/ydabas-hue/razorpay-circular-fraud-detector.git)
cd razorpay-circular-fraud-detector
Create and activate a virtual environment:Bashpython3 -m venv venv
source venv/bin/activate
Install dependencies:Bashpip install openai networkx pandas
Configure your NVIDIA NIM API key:Bashexport NVIDIA_API_KEY="nvapi-your-key-here"
Run the fraud detection pipeline:Bashpython3 main.py
Run the evaluation suite:Bashpython3 evaluate.py
