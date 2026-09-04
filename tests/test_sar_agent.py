import json
from unittest.mock import MagicMock, patch
import pandas as pd
from sar_agent import analyze_cycle, DEFAULT_MODEL, FALLBACK_MODEL, _load_env


def _build_test_data():
    cycle_data = {
        "nodes": ["A", "B", "C"],
        "edges": [
            {"from_id": "A", "to_id": "B", "amount": 1000.0, "tx_type": "payout", "timestamp": "2026-01-01T00:00:00"},
            {"from_id": "B", "to_id": "C", "amount": 1000.0, "tx_type": "payout", "timestamp": "2026-01-01T01:00:00"},
            {"from_id": "C", "to_id": "A", "amount": 1000.0, "tx_type": "collection", "timestamp": "2026-01-01T02:00:00"},
        ],
    }
    registry = pd.DataFrame([
        {"entity_id": "A", "name": "Entity_A", "ip_subnet": "10.0.1.0/24", "mcc_code": "5045", "is_fraud": True},
        {"entity_id": "B", "name": "Entity_B", "ip_subnet": "10.0.1.0/24", "mcc_code": "1731", "is_fraud": True},
        {"entity_id": "C", "name": "Entity_C", "ip_subnet": "10.0.1.0/24", "mcc_code": "5251", "is_fraud": True},
    ])
    return cycle_data, registry


def test_analyze_cycle_uses_primary_model():
    fake_response = json.dumps({
        "verdict": "FRAUD",
        "confidence": 0.95,
        "reasoning": "Shared IP subnet and coordinated timing",
        "sar_summary": "Circular routing on RazorpayX",
        "recommended_action": "FREEZE_PAYOUTS",
    })

    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content=f"```json\n{fake_response}\n```"))]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_completion

    cycle_data, registry = _build_test_data()

    with patch("sar_agent._get_client", return_value=mock_client):
        result = analyze_cycle(cycle_data, registry)

    assert result["verdict"] == "FRAUD"
    assert result["confidence"] == 0.95
    assert result["recommended_action"] == "FREEZE_PAYOUTS"
    assert mock_client.chat.completions.create.call_count == 1
    call_kwargs = mock_client.chat.completions.create.call_args[1]
    assert call_kwargs["model"] == DEFAULT_MODEL


def test_analyze_cycle_falls_back_to_ultra_550b_on_primary_failure():
    fallback_response = json.dumps({
        "verdict": "LEGITIMATE",
        "confidence": 0.88,
        "reasoning": "Normal merchant cycle",
        "sar_summary": "No SAR required",
        "recommended_action": "CLEAR",
    })

    fallback_completion = MagicMock()
    fallback_completion.choices = [MagicMock(message=MagicMock(content=fallback_response))]

    mock_client = MagicMock()
    # First call (primary model) fails, second call (fallback model) succeeds
    mock_client.chat.completions.create.side_effect = [
        RuntimeError("Primary model 503 Overloaded"),
        fallback_completion,
    ]

    cycle_data, registry = _build_test_data()

    with patch("sar_agent._get_client", return_value=mock_client):
        result = analyze_cycle(cycle_data, registry)

    assert result["verdict"] == "LEGITIMATE"
    assert result["confidence"] == 0.88
    assert result["recommended_action"] == "CLEAR"
    assert mock_client.chat.completions.create.call_count == 2
    first_call_model = mock_client.chat.completions.create.call_args_list[0][1]["model"]
    second_call_model = mock_client.chat.completions.create.call_args_list[1][1]["model"]
    assert first_call_model == DEFAULT_MODEL
    assert second_call_model == FALLBACK_MODEL
