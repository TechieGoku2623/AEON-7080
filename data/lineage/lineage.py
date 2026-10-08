"""Lineage graphs for a computational run."""

from __future__ import annotations

import networkx as nx


def experiment_lineage(dataset_name: str | None = None) -> dict:
    graph = nx.DiGraph()
    nodes = [
        ("input", "Input parameters or synthetic patient"),
        ("pk", "One-compartment oral PK"),
        ("pd", "Indirect glucose response"),
        ("uncertainty", "Monte Carlo or population spread"),
        ("analysis", "Endpoints and sensitivity"),
        ("report", "Report rendered from those numbers"),
    ]
    if dataset_name:
        nodes.insert(0, ("dataset", dataset_name))
    for node, label in nodes:
        graph.add_node(node, label=label)
    order = [node for node, _label in nodes]
    for left, right in zip(order, order[1:]):
        graph.add_edge(left, right)
    return {
        "nodes": [{"id": node, "label": graph.nodes[node]["label"]} for node in order],
        "edges": [{"source": u, "target": v} for u, v in graph.edges],
    }
