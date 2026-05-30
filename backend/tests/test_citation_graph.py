from app.pipeline.citation_graph import find_internal_cycles


def test_find_two_node_cycle() -> None:
    doi_to_index = {"10.a": 1, "10.b": 2}
    adjacency = {"10.a": ["10.b"], "10.b": ["10.a"]}
    cycles = find_internal_cycles(doi_to_index, adjacency, max_depth=2)
    assert len(cycles) >= 1
    assert set(cycles[0]["citation_indices"]) == {1, 2}
