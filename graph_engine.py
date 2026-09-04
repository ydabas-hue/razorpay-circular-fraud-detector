from collections import deque
from datetime import datetime, timedelta
import networkx as nx


class GraphEngine:
    def __init__(self, window_hours: int = 72, max_cycle_len: int = 3):
        self._window = timedelta(hours=window_hours)
        self._max_cycle_len = max_cycle_len
        self._edge_queue: deque = deque()
        self._graph = nx.MultiDiGraph()
        # (from_id, to_id, key) → {amount, tx_type, timestamp}
        self._edge_meta: dict = {}
        # frozenset of node sets for cycles already fired — dedup guard
        self._seen_cycles: set = set()

    def add_transaction(self, tx: dict) -> list:
        ts = datetime.fromisoformat(tx["timestamp"])
        from_id = tx["from_id"]
        to_id = tx["to_id"]
        amount = float(tx["amount"])
        tx_type = tx["tx_type"]

        # Evict edges outside the 72h window
        cutoff = ts - self._window
        while self._edge_queue and self._edge_queue[0][0] < cutoff:
            old_ts, old_from, old_to, _, _, old_key = self._edge_queue.popleft()
            if self._graph.has_edge(old_from, old_to, key=old_key):
                self._graph.remove_edge(old_from, old_to, key=old_key)
            self._edge_meta.pop((old_from, old_to, old_key), None)

        # Add new edge; MultiDiGraph.add_edge returns the new edge key
        key = self._graph.add_edge(from_id, to_id)
        self._edge_meta[(from_id, to_id, key)] = {
            "amount": amount,
            "tx_type": tx_type,
            "timestamp": ts.isoformat(),
        }
        self._edge_queue.append((ts, from_id, to_id, amount, tx_type, key))

        # Detect and deduplicate cycles
        hits = []
        for cycle_nodes in nx.simple_cycles(self._graph):
            if len(cycle_nodes) > self._max_cycle_len:
                continue
            cycle_key = frozenset(cycle_nodes)
            if cycle_key in self._seen_cycles:
                continue
            self._seen_cycles.add(cycle_key)
            hits.append(self._package_hit(cycle_nodes))

        return hits

    def _package_hit(self, cycle_nodes: list) -> dict:
        edges = []
        for i, node in enumerate(cycle_nodes):
            next_node = cycle_nodes[(i + 1) % len(cycle_nodes)]
            meta = self._best_edge_meta(node, next_node)
            edges.append({"from_id": node, "to_id": next_node, **meta})
        return {"nodes": cycle_nodes, "edges": edges}

    def _best_edge_meta(self, from_id: str, to_id: str) -> dict:
        best_ts = None
        best_meta = {"amount": 0.0, "tx_type": "unknown", "timestamp": ""}
        if self._graph.has_edge(from_id, to_id):
            for k in self._graph[from_id][to_id]:
                meta = self._edge_meta.get((from_id, to_id, k))
                if meta and (best_ts is None or meta["timestamp"] > best_ts):
                    best_ts = meta["timestamp"]
                    best_meta = meta
        return best_meta