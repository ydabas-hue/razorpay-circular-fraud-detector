from datetime import datetime, timedelta
from graph_engine import GraphEngine


def test_detects_3_hop_cycle():
    engine = GraphEngine(window_hours=72, max_cycle_len=3)
    t0 = datetime(2026, 1, 1, 12, 0, 0)

    # A -> B
    assert engine.add_transaction({
        "timestamp": t0.isoformat(),
        "from_id": "A",
        "to_id": "B",
        "amount": 1000.0,
        "tx_type": "payout",
    }) == []

    # B -> C
    assert engine.add_transaction({
        "timestamp": (t0 + timedelta(hours=1)).isoformat(),
        "from_id": "B",
        "to_id": "C",
        "amount": 1000.0,
        "tx_type": "payout",
    }) == []

    # C -> A completes cycle
    hits = engine.add_transaction({
        "timestamp": (t0 + timedelta(hours=2)).isoformat(),
        "from_id": "C",
        "to_id": "A",
        "amount": 1000.0,
        "tx_type": "collection",
    })

    assert len(hits) == 1
    assert set(hits[0]["nodes"]) == {"A", "B", "C"}
    assert len(hits[0]["edges"]) == 3


def test_window_eviction():
    engine = GraphEngine(window_hours=72, max_cycle_len=3)
    t0 = datetime(2026, 1, 1, 0, 0, 0)

    engine.add_transaction({
        "timestamp": t0.isoformat(),
        "from_id": "A",
        "to_id": "B",
        "amount": 500.0,
        "tx_type": "payout",
    })

    # Transaction 80 hours later should evict A -> B
    hits = engine.add_transaction({
        "timestamp": (t0 + timedelta(hours=80)).isoformat(),
        "from_id": "B",
        "to_id": "A",
        "amount": 500.0,
        "tx_type": "payout",
    })

    assert hits == []
    assert not engine._graph.has_edge("A", "B")
