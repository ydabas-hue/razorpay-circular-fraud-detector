import pandas as pd
from graph_engine import GraphEngine
from sar_agent import analyze_cycle
from mock_api import execute_action


def main():
    print("=== RazorpayX Circular Fraud Detector ===\n")
    df = pd.read_csv("data/train_transactions.csv").sort_values("timestamp")
    registry = pd.read_csv("data/entity_registry.csv")

    engine = GraphEngine()
    cycles_found = 0

    for _, row in df.iterrows():
        hits = engine.add_transaction(row.to_dict())
        for hit in hits:
            cycles_found += 1
            print(f"\n{'='*60}")
            print(f"[GRAPH ENGINE] Cycle #{cycles_found} — nodes: {hit['nodes']}")
            for edge in hit["edges"]:
                print(
                    f"  {edge['from_id']} → {edge['to_id']} | "
                    f"₹{edge['amount']:,.2f} | {edge['tx_type']} | {edge['timestamp']}"
                )
            sar = analyze_cycle(hit, registry)
            print(f"\n[LLM AGENT] Verdict:   {sar['verdict']} (confidence: {sar['confidence']:.2f})")
            print(f"[LLM AGENT] Reasoning: {sar['reasoning'][:150]}...")
            execute_action(hit["nodes"], sar)

    print(f"\n{'='*60}")
    print(f"Run complete. {cycles_found} cycles detected.")
    print("Full audit trail: audit_log.jsonl")


if __name__ == "__main__":
    main()