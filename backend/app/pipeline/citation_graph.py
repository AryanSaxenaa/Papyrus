from __future__ import annotations

from typing import Any


def find_internal_cycles(
    doi_to_index: dict[str, int],
    adjacency: dict[str, list[str]],
    max_depth: int = 2,
) -> list[dict[str, Any]]:
    """
    Find citation cycles where every DOI in the path exists in the audited bibliography.
    max_depth=2 corresponds to spec's two-level-deep check (A→B→A or A→B→C→A within depth budget).
    """
    internal = set(doi_to_index.keys())
    cycles: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()

    def dfs(start: str, path: list[str], depth: int) -> None:
        if depth > max_depth:
            return
        current = path[-1]
        for nxt in adjacency.get(current, []):
            if nxt not in internal:
                continue
            if nxt == start and len(path) >= 2:
                loop = tuple(path + [nxt])
                if loop not in seen:
                    seen.add(loop)
                    indices = [doi_to_index[doi] for doi in loop[:-1]]
                    cycles.append(
                        {
                            "dois": list(loop),
                            "citation_indices": indices,
                            "length": len(loop) - 1,
                        }
                    )
                continue
            if nxt in path:
                continue
            dfs(start, path + [nxt], depth + 1)

    for doi in doi_to_index:
        dfs(doi, [doi], 0)

    return cycles
