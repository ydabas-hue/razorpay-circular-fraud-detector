import pandas as pd
from graph_engine import GraphEngine
from sar_agent import analyze_cycle
from mock_api import execute_action


def get_ground_truth(nodes: list, registry: pd.DataFrame) -> str:
    """
    Returns 'FRAUD' if any node in the cycle has is_fraud=True in registry.
    Defaults to 'LEGITIMATE' if no nodes found in registry.
    """
    rows = registry[registry["entity_id"].isin(nodes)]
    if rows.empty:
        return "LEGITIMATE"
    return "FRAUD" if rows["is_fraud"].any() else "LEGITIMATE"


def run_evaluation():
    test_df = pd.read_csv("data/test_transactions.csv").sort_values("timestamp")
    registry = pd.read_csv("data/entity_registry.csv")

    engine = GraphEngine()
    results = []  # list of (ground_truth: str, predicted: str)

    for _, row in test_df.iterrows():
        hits = engine.add_transaction(row.to_dict())
        for hit in hits:
            ground_truth = get_ground_truth(hit["nodes"], registry)
            sar = analyze_cycle(hit, registry)
            execute_action(hit["nodes"], sar)
            predicted = sar["verdict"]
            results.append((ground_truth, predicted))
            print(
                f"  Cycle {hit['nodes']}: "
                f"truth={ground_truth} | predicted={predicted} | conf={sar['confidence']:.2f}"
            )

    if not results:
        print("No cycles detected in test set. Run: python synthetic_data.py")
        return

    tp = sum(1 for t, p in results if t == "FRAUD"     and p == "FRAUD")
    fp = sum(1 for t, p in results if t == "LEGITIMATE" and p == "FRAUD")
    tn = sum(1 for t, p in results if t == "LEGITIMATE" and p == "LEGITIMATE")
    fn = sum(1 for t, p in results if t == "FRAUD"     and p == "LEGITIMATE")

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    print("\n=== CONFUSION MATRIX ===")
    print(f"  True Positives  (fraud caught):    {tp}")
    print(f"  False Positives (legit flagged):   {fp}")
    print(f"  True Negatives  (legit cleared):   {tn}")
    print(f"  False Negatives (fraud missed):    {fn}")
    print(f"\n  Precision: {precision:.2f}")
    print(f"  Recall:    {recall:.2f}")
    print(f"  F1 Score:  {f1:.2f}")


if __name__ == "__main__":
    run_evaluation()