from collections import defaultdict
from typing import Any, Sequence

from hou import Prim, Point, Geometry

from ..attributings.transferer import collect_prim_attribs, copy_point_attribs
from .basic import fill_faces
from .helper import get_edge_prim_count, Edge, get_prims_normal


def inset(
    prims: list[Prim],
    scalar: float,
    use_ratio: bool = False,
    follow_existing_edge: bool = True,
) -> dict[tuple[Prim, ...], list[Prim]]:
    if not prims or scalar == 0:
        return {tuple(prims): []}
    if scalar < 0:
        return outset(prims, -scalar, use_ratio, follow_existing_edge)

    geo = prims[0].geometry()
    components = partition_connected_prims(prims)

    result: dict[tuple[Prim, ...], list[Prim]] = {}
    for comp in components:
        inner_pts, inner_att, border_pts, border_att = _offset_connected(
            geo,
            comp,
            scalar,
            use_ratio,
            is_outset=False,
            follow_existing_edge=follow_existing_edge
        )
        inner_prims = fill_faces(inner_pts, inner_att)
        border_prims = fill_faces(border_pts, border_att)
        result[tuple(inner_prims)] = border_prims

    geo.deletePrims(prims, keep_points=True)
    return result


def outset(
    prims: list[Prim],
    scalar: float,
    use_ratio: bool = False,
    follow_existing_edge: bool = True,
) -> dict[tuple[Prim, ...], list[Prim]]:
    """Perform an outset operation on a collection of polygon primitives.
    - Groups primitives into connected components and outsets each component independently.
    - Offsets boundary vertices outward by distance or ratio and generates border quad faces around the exterior.
    - If scalar is negative, delegates to inset.
    - Preserves primitive attributes and primitive group memberships on newly created border primitives.
    - Preserves point attributes and group memberships on newly generated outset points.

    :param prims: List of polygon primitives to outset.
    :param scalar: Offset ratio or world distance. Negative values trigger inset.
    :param use_ratio: If True, scalar is interpreted as a ratio; otherwise as absolute distance.
    :param follow_existing_edge:
    :return: List of newly generated outer border quad primitives.
    """
    if not prims or scalar == 0:
        return {tuple(prims): []}
    if scalar < 0:
        return inset(prims, -scalar, use_ratio, follow_existing_edge)

    geo = prims[0].geometry()
    components = partition_connected_prims(prims)

    result: dict[tuple[Prim, ...], list[Prim]] = {}
    for comp in components:
        border_pts, border_att = _offset_connected(
            geo,
            comp,
            scalar,
            use_ratio,
            is_outset=True,
            follow_existing_edge=follow_existing_edge
        )
        border_prims = fill_faces(
            border_pts,
            border_att
        )
        result[comp] = border_prims

    return result


def _compute_connected_offset_delta(
        pt: Point,
        incoming_boundary_edge: dict[Point, tuple[Point, Prim, float]],
        outgoing_boundary_edge: dict[Point, tuple[Point, Prim, float]],
        interior_edges_by_point: defaultdict[Point, list[Point]],
        scalar: float,
        is_scalar_ratio: bool,
        is_outset: bool,
        follow_existing_edge: bool,
):
    u, p_in, l_in = incoming_boundary_edge[pt]
    w, p_out, l_out = outgoing_boundary_edge[pt]

    pos = pt.position()
    t_in = (pos - u.position()).normalized()
    t_out = (w.position() - pos).normalized()

    norm_in = get_prims_normal(p_in)
    norm_out = get_prims_normal(p_out)

    n1 = t_in.cross(norm_in).normalized()
    n2 = t_out.cross(norm_out).normalized()

    if is_scalar_ratio:
        d1 = l_in * scalar
        d2 = l_out * scalar
    else:
        d1 = scalar
        d2 = scalar

    delta_v = None

    if follow_existing_edge and pt in interior_edges_by_point:
        n_inward = (n1 + n2).normalized()

        best_nbr = max(
            interior_edges_by_point[pt],
            key=lambda nbr: (
                nbr.position() - pos
            ).normalized().dot(n_inward),
        )

        e_vec = best_nbr.position() - pos
        e_dir = e_vec.normalized()
        cos_phi = e_dir.dot(n_inward)

        if cos_phi > 1e-4:
            dist = ((d1 + d2) * 0.5) / cos_phi
            delta_v = e_dir * dist

    if delta_v is None:
        cos_theta = n1.dot(n2)
        denom = 1.0 - cos_theta * cos_theta

        if denom > 1e-6:
            alpha = (d1 - d2 * cos_theta) / denom
            beta = (d2 - d1 * cos_theta) / denom
            delta_v = n1 * alpha + n2 * beta
        else:
            delta_v = (
                (n1 + n2).normalized()
                * ((d1 + d2) * 0.5)
            )

    if is_outset:
        delta_v = -delta_v

    return delta_v


def _create_connected_offset_points(
        geo: Geometry,
        incoming_boundary_edge: dict[Point, tuple[Point, Prim, float]],
        outgoing_boundary_edge: dict[Point, tuple[Point, Prim, float]],
        interior_edges_by_point: defaultdict[Point, list[Point]],
        scalar: float,
        is_scalar_ratio: bool,
        is_outset: bool,
        follow_existing_edge: bool,
) -> dict[Point, Point]:
    offset_point_map: dict[Point, Point] = {}

    for pt in incoming_boundary_edge:
        delta_v = _compute_connected_offset_delta(
            pt=pt,
            incoming_boundary_edge=incoming_boundary_edge,
            outgoing_boundary_edge=outgoing_boundary_edge,
            interior_edges_by_point=interior_edges_by_point,
            scalar=scalar,
            is_scalar_ratio=is_scalar_ratio,
            is_outset=is_outset,
            follow_existing_edge=follow_existing_edge,
        )

        new_pt = geo.createPoint()
        new_pt.setPosition(pt.position() + delta_v)
        copy_point_attribs(pt, new_pt)

        offset_point_map[pt] = new_pt

    return offset_point_map


def _build_outset_faces(
        island: Sequence[Prim],
        boundary_edges_by_prim: defaultdict[Prim, list[tuple[Point, Point]]],
        offset_point_map: dict[Point, Point],
        prim_attr_map: dict[Prim, tuple[dict[str, Any], list[str]]],
) -> tuple[
    list[list[Point]],
    list[tuple[dict[str, Any], list[str]]],
]:
    border_face_points: list[list[Point]] = []
    border_attribs: list[tuple[dict[str, Any], list[str]]] = []

    for p in island:
        for u, v in boundary_edges_by_prim[p]:
            u_prime = offset_point_map[u]
            v_prime = offset_point_map[v]

            border_face_points.append([
                u,
                u_prime,
                v_prime,
                v,
            ])
            border_attribs.append(prim_attr_map[p])

    return border_face_points, border_attribs


def _build_inset_faces(
        island: Sequence[Prim],
        boundary_edges_by_prim: defaultdict[Prim, list[tuple[Point, Point]]],
        offset_point_map: dict[Point, Point],
        prim_attr_map: dict[Prim, tuple[dict[str, Any], list[str]]],
) -> tuple[
    list[list[Point]],
    list[tuple[dict[str, Any], list[str]]],
    list[list[Point]],
    list[tuple[dict[str, Any], list[str]]],
]:
    inner_face_points: list[list[Point]] = []
    inner_attribs: list[tuple[dict[str, Any], list[str]]] = []

    border_face_points: list[list[Point]] = []
    border_attribs: list[tuple[dict[str, Any], list[str]]] = []

    for p in island:
        pts = [v.point() for v in p.vertices()]
        inner_pts = [
            offset_point_map.get(pt, pt)
            for pt in pts
        ]

        inner_face_points.append(inner_pts)
        inner_attribs.append(prim_attr_map[p])

        for u, v in boundary_edges_by_prim[p]:
            u_prime = offset_point_map[u]
            v_prime = offset_point_map[v]

            border_face_points.append([
                u,
                v,
                v_prime,
                u_prime,
            ])
            border_attribs.append(prim_attr_map[p])

    return (
        inner_face_points,
        inner_attribs,
        border_face_points,
        border_attribs,
    )


def _offset_connected(
        geo: Geometry,
        island: Sequence[Prim],
        scalar: float,
        is_scalar_ratio: bool,
        is_outset: bool = False,
        follow_existing_edge: bool = True,
) -> tuple:
    (
        incoming_boundary_edge,
        outgoing_boundary_edge,
        boundary_edges_by_prim,
        interior_edges_by_point,
    ) = _collect_connected_edge_data(
        island,
        follow_existing_edge,
    )

    offset_point_map = _create_connected_offset_points(
        geo=geo,
        incoming_boundary_edge=incoming_boundary_edge,
        outgoing_boundary_edge=outgoing_boundary_edge,
        interior_edges_by_point=interior_edges_by_point,
        scalar=scalar,
        is_scalar_ratio=is_scalar_ratio,
        is_outset=is_outset,
        follow_existing_edge=follow_existing_edge,
    )

    attr_data = collect_prim_attribs(island)
    prim_attr_map = dict(zip(island, attr_data))
    if is_outset:
        return _build_outset_faces(
            island,
            boundary_edges_by_prim,
            offset_point_map,
            prim_attr_map,
        )
    return _build_inset_faces(
        island,
        boundary_edges_by_prim,
        offset_point_map,
        prim_attr_map,
    )


def partition_connected_prims(
    prims: list[Prim]
) -> list[tuple[Prim]]:
    """

    :param prims:
    :return: islands of argument `prims`
    """
    edge_prim_map: dict[tuple[int, int], list[Prim]] = {}
    for p in prims:
        pts = [v.point().number() for v in p.vertices()]
        n = len(pts)
        for i in range(n):
            edge = (pts[i], pts[(i + 1) % n]) if pts[i] < pts[(i + 1) % n] else (pts[(i + 1) % n], pts[i])
            edge_prim_map.setdefault(edge, []).append(p)

    adjacent_map: dict[Prim, set[Prim]] = {p: set() for p in prims}
    for shared_prims in edge_prim_map.values():
        for p1 in shared_prims:
            for p2 in shared_prims:
                if p1 != p2:
                    adjacent_map[p1].add(p2)

    components: list[tuple[Prim]] = []
    visited: set[Prim] = set()
    for p in prims:
        if p in visited:
            continue
        compo: list[Prim] = []
        queue = [p]
        visited.add(p)
        while queue:
            current = queue.pop()
            compo.append(current)
            for neighbor in adjacent_map[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        components.append(tuple(compo))

    return components


def _collect_connected_edge_data(
        island: Sequence[Prim],
        follow_existing_edge: bool,
) -> tuple[
    dict[Point, tuple[Point, Prim, float]],
    dict[Point, tuple[Point, Prim, float]],
    defaultdict[Prim, list[tuple[Point, Point]]],
    defaultdict[Point, list[Point]],
]:
    edge_counts = get_edge_prim_count(island)

    incoming_boundary_edge: dict[Point, tuple[Point, Prim, float]] = {}
    outgoing_boundary_edge: dict[Point, tuple[Point, Prim, float]] = {}
    boundary_edges_by_prim: defaultdict[Prim, list[tuple[Point, Point]]] = defaultdict(list)
    interior_edges_by_point: defaultdict[Point, list[Point]] = defaultdict(list)

    for p in island:
        pts = [v.point() for v in p.vertices()]
        n = len(pts)

        for i in range(n):
            u, v = pts[i], pts[(i + 1) % n]
            edge = Edge.from_points(u, v, reorder=True)

            if edge_counts[edge] == 1:
                boundary_edges_by_prim[p].append((u, v))
                edge_len = (v.position() - u.position()).length()
                outgoing_boundary_edge[u] = (v, p, edge_len)
                incoming_boundary_edge[v] = (u, p, edge_len)
            elif follow_existing_edge:
                if v not in interior_edges_by_point[u]:
                    interior_edges_by_point[u].append(v)
                if u not in interior_edges_by_point[v]:
                    interior_edges_by_point[v].append(u)

    return (
        incoming_boundary_edge,
        outgoing_boundary_edge,
        boundary_edges_by_prim,
        interior_edges_by_point,
    )
