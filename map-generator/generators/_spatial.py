"""Spatial layout helpers: Poisson disk sampling and graph connectivity."""
from __future__ import annotations
import math
import random
from collections import deque


_MARGIN = 0.10  # keep nodes away from the canvas edge


def poisson_disk_sample(
    count: int,
    rng: random.Random,
    min_sep: float | None = None,
    max_attempts: int = 50,
) -> list[tuple[float, float]]:
    """Return up to `count` points in [margin, 1-margin]² with minimum separation."""
    if min_sep is None:
        min_sep = 2.5 / math.sqrt(count)

    lo, hi = _MARGIN, 1.0 - _MARGIN
    points: list[tuple[float, float]] = []
    for _ in range(count):
        for _ in range(max_attempts):
            x = lo + rng.random() * (hi - lo)
            y = lo + rng.random() * (hi - lo)
            if all(math.hypot(x - px, y - py) >= min_sep for px, py in points):
                points.append((x, y))
                break
        else:
            x = lo + rng.random() * (hi - lo)
            y = lo + rng.random() * (hi - lo)
            points.append((x, y))
    return points


def hub_spoke_positions(
    count: int,
    rng: random.Random,
) -> list[tuple[float, float]]:
    """Hub at center; satellites on jittered rings."""
    positions: list[tuple[float, float]] = [(0.5, 0.5)]
    ring_radius = 0.28
    lo, hi = _MARGIN, 1.0 - _MARGIN
    for i in range(count - 1):
        angle = (2 * math.pi * i / (count - 1)) + rng.uniform(-0.2, 0.2)
        r = ring_radius + rng.uniform(-0.05, 0.05)
        x = max(lo, min(hi, 0.5 + r * math.cos(angle)))
        y = max(lo, min(hi, 0.5 + r * math.sin(angle)))
        positions.append((x, y))
    return positions


def spine_branch_positions(
    count: int,
    rng: random.Random,
) -> list[tuple[float, float]]:
    """Spine nodes left-to-right, branch nodes above/below."""
    spine_count = max(2, int(count * 0.4))
    branch_count = count - spine_count
    lo, hi = _MARGIN, 1.0 - _MARGIN

    positions: list[tuple[float, float]] = []
    for i in range(spine_count):
        x = lo + (hi - lo) * (i / max(1, spine_count - 1))
        y = 0.5 + rng.uniform(-0.07, 0.07)
        positions.append((x, y))

    min_sep = 2.0 / math.sqrt(count)
    for _ in range(branch_count):
        placed = False
        for _ in range(60):
            spine_x, spine_y = rng.choice(positions[:spine_count])
            offset_y = rng.choice([-1, 1]) * rng.uniform(0.18, 0.30)
            x = max(lo, min(hi, spine_x + rng.uniform(-0.10, 0.10)))
            y = max(lo, min(hi, spine_y + offset_y))
            if all(math.hypot(x - px, y - py) >= min_sep for px, py in positions):
                positions.append((x, y))
                placed = True
                break
        if not placed:
            positions.append((lo + rng.random() * (hi - lo), lo + rng.random() * (hi - lo)))
    return positions


def build_organic_edges(
    points: list[tuple[float, float]],
    max_neighbors: int = 3,
) -> list[tuple[int, int]]:
    """Gabriel-graph approximation via Delaunay + nearest-neighbor pruning."""
    try:
        from scipy.spatial import Delaunay  # type: ignore
        import numpy as np

        arr = np.array(points)
        tri = Delaunay(arr)
        candidate_edges: set[tuple[int, int]] = set()
        for simplex in tri.simplices:
            for i in range(3):
                a, b = simplex[i], simplex[(i + 1) % 3]
                candidate_edges.add((min(a, b), max(a, b)))

        # Keep only edges where both endpoints appear in each other's k-NN
        from scipy.spatial import cKDTree
        tree = cKDTree(arr)
        _, nn_idx = tree.query(arr, k=max_neighbors + 1)
        nn_sets = [set(row[1:]) for row in nn_idx]

        return [
            (a, b)
            for a, b in candidate_edges
            if b in nn_sets[a] or a in nn_sets[b]
        ]
    except ImportError:
        return _fallback_knn_edges(points, k=3)


def _fallback_knn_edges(
    points: list[tuple[float, float]],
    k: int,
) -> list[tuple[int, int]]:
    """k-nearest-neighbor edges without scipy."""
    edges: set[tuple[int, int]] = set()
    for i, (xi, yi) in enumerate(points):
        dists = sorted(
            ((math.hypot(xi - xj, yi - yj), j) for j, (xj, yj) in enumerate(points) if j != i)
        )
        for _, j in dists[:k]:
            edges.add((min(i, j), max(i, j)))
    return list(edges)


def ensure_connected(
    n: int,
    edges: list[tuple[int, int]],
    points: list[tuple[float, float]],
) -> list[tuple[int, int]]:
    """Bridge disconnected components with shortest available cross-edges."""
    extra = list(edges)

    def components() -> list[set[int]]:
        adj: dict[int, set[int]] = {i: set() for i in range(n)}
        for a, b in extra:
            adj[a].add(b)
            adj[b].add(a)
        visited: set[int] = set()
        comps: list[set[int]] = []
        for start in range(n):
            if start not in visited:
                comp: set[int] = set()
                q = deque([start])
                while q:
                    node = q.popleft()
                    if node in visited:
                        continue
                    visited.add(node)
                    comp.add(node)
                    q.extend(adj[node] - visited)
                comps.append(comp)
        return comps

    while True:
        comps = components()
        if len(comps) == 1:
            break
        best_dist = float("inf")
        best_edge: tuple[int, int] | None = None
        for i, ci in enumerate(comps):
            for cj in comps[i + 1 :]:
                for a in ci:
                    for b in cj:
                        d = math.hypot(
                            points[a][0] - points[b][0],
                            points[a][1] - points[b][1],
                        )
                        if d < best_dist:
                            best_dist = d
                            best_edge = (min(a, b), max(a, b))
        if best_edge:
            extra.append(best_edge)
    return extra


def build_mst_edges(points: list[tuple[float, float]]) -> list[tuple[int, int]]:
    """Prim's MST — produces the minimal spanning tree (dungeon corridor backbone)."""
    if len(points) < 2:
        return []

    import heapq
    in_tree = {0}
    heap: list[tuple[float, int, int]] = []
    for j in range(1, len(points)):
        d = math.hypot(points[0][0] - points[j][0], points[0][1] - points[j][1])
        heapq.heappush(heap, (d, 0, j))

    edges: list[tuple[int, int]] = []
    while heap and len(in_tree) < len(points):
        dist, u, v = heapq.heappop(heap)
        if v in in_tree:
            continue
        in_tree.add(v)
        edges.append((min(u, v), max(u, v)))
        for w in range(len(points)):
            if w not in in_tree:
                d = math.hypot(points[v][0] - points[w][0], points[v][1] - points[w][1])
                heapq.heappush(heap, (d, v, w))
    return edges


def build_dungeon_edges(
    points: list[tuple[float, float]],
    rng: random.Random,
    extra_ratio: float = 0.25,
) -> list[tuple[int, int]]:
    """MST backbone + a fraction of short extra edges to create loops.

    Does NOT force full connectivity — isolated pocket clusters are acceptable
    and give the dungeon a sense of hidden or unreachable areas.
    """
    mst = build_mst_edges(points)
    mst_set = set(mst)

    # Candidate extras: short kNN edges not already in the MST
    knn = _fallback_knn_edges(points, k=3)
    candidates = [e for e in knn if e not in mst_set]

    extra_count = max(0, int(len(mst) * extra_ratio))
    extras = rng.sample(candidates, min(extra_count, len(candidates)))
    return mst + extras
