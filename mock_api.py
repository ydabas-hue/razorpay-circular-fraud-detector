import json
from datetime import datetime, timezone

CONFIDENCE_THRESHOLD = 0.75


def execute_action(cycle_nodes: list, sar: dict) -> None:
    action = sar["recommended_action"]
    confidence = sar["confidence"]

    if action == "FREEZE_PAYOUTS" and confidence < CONFIDENCE_THRESHOLD:
        action = "MONITOR"

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cycle_nodes": cycle_nodes,
        "llm_verdict": sar["verdict"],
        "llm_confidence": confidence,
        "sar_summary": sar["sar_summary"],
        "action_taken": action,
    }

    if action == "FREEZE_PAYOUTS":
        calls = [f"POST /v1/payouts/{eid}/suspend" for eid in cycle_nodes]
        entry["mock_api_calls"] = calls
        for call in calls:
            print(f"[MOCK API EXECUTED]: {call}")

    with open("audit_log.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")

    print(f"[AUDIT] {action} | nodes={cycle_nodes} | conf={confidence:.2f} | {sar['sar_summary']}")