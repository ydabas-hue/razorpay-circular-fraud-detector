from synthetic_data import _make_fraud_cluster, _make_legit_cluster


def test_make_fraud_cluster():
    entities, txs = _make_fraud_cluster(0, "test_fraud", t_offset_hours=0)
    assert len(entities) == 3
    assert len(txs) == 3

    # All fraud nodes should have is_fraud=True and identical IP subnet
    assert all(e["is_fraud"] is True for e in entities)
    subnets = {e["ip_subnet"] for e in entities}
    assert len(subnets) == 1
    assert "10.0.1.0/24" in subnets

    # All transactions in cycle have identical amounts
    amounts = {tx["amount"] for tx in txs}
    assert len(amounts) == 1


def test_make_legit_cluster():
    entities, txs = _make_legit_cluster(0, "test_legit", t_offset_hours=0)
    assert len(entities) == 3
    assert len(txs) == 3

    # All legit nodes should have is_fraud=False and distinct IP subnets
    assert all(e["is_fraud"] is False for e in entities)
    subnets = {e["ip_subnet"] for e in entities}
    assert len(subnets) == 3
