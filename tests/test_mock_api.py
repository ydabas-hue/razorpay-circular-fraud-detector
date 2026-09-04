import json
import os
from mock_api import execute_action


def test_execute_action_freeze(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    sar = {
        "verdict": "FRAUD",
        "confidence": 0.95,
        "reasoning": "Suspicious shell cluster",
        "sar_summary": "Circular routing detected",
        "recommended_action": "FREEZE_PAYOUTS",
    }
    nodes = ["node1", "node2", "node3"]

    execute_action(nodes, sar)

    assert os.path.exists("audit_log.jsonl")
    with open("audit_log.jsonl") as f:
        data = json.loads(f.readline())

    assert data["action_taken"] == "FREEZE_PAYOUTS"
    assert len(data["mock_api_calls"]) == 3
    assert "POST /v1/payouts/node1/suspend" in data["mock_api_calls"]


def test_execute_action_low_confidence_downgrades_to_monitor(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    sar = {
        "verdict": "FRAUD",
        "confidence": 0.60,
        "reasoning": "Low confidence pattern",
        "sar_summary": "Unclear activity",
        "recommended_action": "FREEZE_PAYOUTS",
    }
    nodes = ["node1", "node2"]

    execute_action(nodes, sar)

    with open("audit_log.jsonl") as f:
        data = json.loads(f.readline())

    assert data["action_taken"] == "MONITOR"
    assert "mock_api_calls" not in data
