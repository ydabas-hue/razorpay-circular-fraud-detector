import os
import random
import pandas as pd
from datetime import datetime, timedelta

random.seed(42)
BASE_TIME = datetime(2026, 1, 1, 0, 0, 0)


def _make_entity(entity_id, ip_subnet, mcc_code, incorp_offset_days, account_age, is_fraud):
    return {
        "entity_id": entity_id,
        "name": f"Entity_{entity_id}",
        "incorporation_date": (BASE_TIME - timedelta(days=incorp_offset_days)).strftime("%Y-%m-%d"),
        "ip_subnet": ip_subnet,
        "mcc_code": mcc_code,
        "account_age_days": account_age,
        "is_fraud": is_fraud,
    }


def _make_fraud_cluster(cluster_id, prefix, t_offset_hours):
    """3-node fraud cycle: shared /24, MCC mismatch, incorporated within 5 days, round amounts."""
    a = f"{prefix}_A{cluster_id}"
    b = f"{prefix}_B{cluster_id}"
    c = f"{prefix}_C{cluster_id}"
    entities = [
        _make_entity(a, "10.0.1.0/24", "5045", random.randint(10, 14), random.randint(30, 60), True),
        _make_entity(b, "10.0.1.0/24", "1731", random.randint(11, 15), random.randint(30, 60), True),
        _make_entity(c, "10.0.1.0/24", "5251", random.randint(12, 14), random.randint(30, 60), True),
    ]
    t0 = BASE_TIME + timedelta(hours=t_offset_hours)
    amount = random.choice([50000, 75000, 100000, 150000, 200000])
    txs = [
        {
            "tx_id": f"tx_{prefix}_{cluster_id}_1",
            "timestamp": t0.isoformat(),
            "from_id": a, "to_id": b,
            "amount": float(amount),
            "tx_type": "payout",
        },
        {
            "tx_id": f"tx_{prefix}_{cluster_id}_2",
            "timestamp": (t0 + timedelta(hours=random.randint(1, 20))).isoformat(),
            "from_id": b, "to_id": c,
            "amount": float(amount),
            "tx_type": "payout",
        },
        {
            "tx_id": f"tx_{prefix}_{cluster_id}_3",
            "timestamp": (t0 + timedelta(hours=random.randint(21, 70))).isoformat(),
            "from_id": c, "to_id": a,
            "amount": float(amount),
            "tx_type": "collection",
        },
    ]
    return entities, txs


def _make_legit_cluster(cluster_id, prefix, t_offset_hours):
    """3-node legit cycle: cafe→bakery→dairy→cafe, distinct /24s, varied amounts."""
    a = f"{prefix}_cafe{cluster_id}"
    b = f"{prefix}_bakery{cluster_id}"
    c = f"{prefix}_dairy{cluster_id}"
    entities = [
        _make_entity(a, f"192.168.{cluster_id % 255}.0/24", "5812",
                     random.randint(100, 500), random.randint(200, 800), False),
        _make_entity(b, f"172.16.{cluster_id % 255}.0/24", "5461",
                     random.randint(200, 600), random.randint(300, 900), False),
        _make_entity(c, f"10.10.{cluster_id % 255}.0/24", "5451",
                     random.randint(300, 700), random.randint(400, 1000), False),
    ]
    t0 = BASE_TIME + timedelta(hours=t_offset_hours)
    txs = [
        {
            "tx_id": f"tx_{prefix}_{cluster_id}_1",
            "timestamp": t0.isoformat(),
            "from_id": a, "to_id": b,
            "amount": round(random.uniform(1000, 8000), 2),
            "tx_type": "payout",
        },
        {
            "tx_id": f"tx_{prefix}_{cluster_id}_2",
            "timestamp": (t0 + timedelta(hours=random.randint(5, 30))).isoformat(),
            "from_id": b, "to_id": c,
            "amount": round(random.uniform(500, 4000), 2),
            "tx_type": "payout",
        },
        {
            "tx_id": f"tx_{prefix}_{cluster_id}_3",
            "timestamp": (t0 + timedelta(hours=random.randint(31, 70))).isoformat(),
            "from_id": c, "to_id": a,
            "amount": round(random.uniform(200, 2000), 2),
            "tx_type": "collection",
        },
    ]
    return entities, txs


def _make_noise_entities(max_src=50, max_dst=100):
    """
    Generate registry entries for noise_src_1..50 and noise_dst_51..100.
    All is_fraud=False, distinct 172.31.x.x subnets.
    """
    entities = []
    for i in range(1, max_src + 1):
        entities.append(_make_entity(
            f"noise_src_{i}",
            f"172.31.{i % 256}.0/24",
            str(random.choice([5411, 5912, 5999, 7011, 8049])),
            random.randint(200, 1000),
            random.randint(180, 1200),
            False,
        ))
    for i in range(max_src + 1, max_dst + 1):
        entities.append(_make_entity(
            f"noise_dst_{i}",
            f"172.31.{i % 256}.0/24",
            str(random.choice([5411, 5912, 5999, 7011, 8049])),
            random.randint(200, 1000),
            random.randint(180, 1200),
            False,
        ))
    return entities


def _make_noise_txs(n, prefix, t_max_hours=200):
    txs = []
    for i in range(n):
        src = random.randint(1, 50)
        dst = random.randint(51, 100)
        txs.append({
            "tx_id": f"tx_noise_{prefix}_{i}",
            "timestamp": (BASE_TIME + timedelta(hours=random.randint(0, t_max_hours))).isoformat(),
            "from_id": f"noise_src_{src}",
            "to_id": f"noise_dst_{dst}",
            "amount": round(random.uniform(100, 50000), 2),
            "tx_type": random.choice(["payout", "collection"]),
        })
    return txs


def generate_all_data():
    os.makedirs("data", exist_ok=True)

    all_entities = []
    train_txs = []
    test_txs = []

    for i in range(15):
        ents, txs = _make_fraud_cluster(i, "train_fraud", t_offset_hours=i * 10)
        all_entities.extend(ents)
        train_txs.extend(txs)

    for i in range(20):
        ents, txs = _make_legit_cluster(i, "train_legit", t_offset_hours=i * 8 + 200)
        all_entities.extend(ents)
        train_txs.extend(txs)

    all_entities.extend(_make_noise_entities(max_src=50, max_dst=100))
    train_txs.extend(_make_noise_txs(100, "train", t_max_hours=200))

    for i in range(5):
        ents, txs = _make_fraud_cluster(i, "test_fraud", t_offset_hours=i * 10 + 500)
        all_entities.extend(ents)
        test_txs.extend(txs)

    for i in range(7):
        ents, txs = _make_legit_cluster(i, "test_legit", t_offset_hours=i * 8 + 600)
        all_entities.extend(ents)
        test_txs.extend(txs)

    test_txs.extend(_make_noise_txs(30, "test", t_max_hours=50))

    pd.DataFrame(all_entities).drop_duplicates("entity_id").to_csv(
        "data/entity_registry.csv", index=False
    )
    pd.DataFrame(train_txs).sort_values("timestamp").to_csv(
        "data/train_transactions.csv", index=False
    )
    pd.DataFrame(test_txs).sort_values("timestamp").to_csv(
        "data/test_transactions.csv", index=False
    )


if __name__ == "__main__":
    generate_all_data()
    print("Done: data/train_transactions.csv, data/test_transactions.csv, data/entity_registry.csv")