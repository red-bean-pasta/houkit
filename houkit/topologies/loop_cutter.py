from dataclasses import dataclass, field

from hou import Prim, Point, Vector3, Geometry

from .basic import fill_faces
from .helper import interpolate_point
from ..attributings.transferer import collect_prim_attribs


@dataclass
class _LoopCutState:
    geo: Geometry
    root_prim: Prim
    start_point: Point
    end_point: Point
    m_start: Point
    scalar: float
    use_ratio: bool
    scope: list[Prim] | None

    visited_prims: list[Prim] = field(default_factory=list)
    cut_edges: list[tuple[Point, Point]] = field(default_factory=list)
    end_side_faces: list[list[Point]] = field(default_factory=list)
    start_side_faces: list[list[Point]] = field(default_factory=list)


def loop_cut(
    prim: Prim,
    start_point: Point,
    end_point: Point,
    scalar: float,
    use_ratio: bool = True,
    scope: list[Prim] | None = None,
) -> dict[tuple[Point, Point], tuple[Prim, Prim]]:
    _validate_loop_cut_input(prim, scope)

    geo = prim.geometry()
    m_start = _create_cut_point(geo, start_point, end_point, scalar, use_ratio)

    state = _LoopCutState(
        geo=geo,
        root_prim=prim,
        start_point=start_point,
        end_point=end_point,
        m_start=m_start,
        scalar=scalar,
        use_ratio=use_ratio,
        scope=scope,
    )

    dir1_points, is_closed = _traverse_loop(state, prim, start_point, end_point, m_start)
    dir2_points: list[Point] = []

    if not is_closed:
        opposite_prim = _find_opposite_start_prim(state)

        if opposite_prim is not None:
            dir2_points, _ = _traverse_loop(state, opposite_prim, start_point, end_point, m_start)

    added_points = list(reversed(dir2_points)) + [m_start] + dir1_points
    face_map = _rebuild_loop_faces(state)

    cut_edges = list(zip(added_points, added_points[1:]))

    if is_closed and len(added_points) > 1:
        cut_edges.append((added_points[-1], added_points[0]))

    return {edge: face_map[frozenset(edge)] for edge in cut_edges}


def _validate_loop_cut_input(prim: Prim, scope: list[Prim] | None) -> None:
    assert isinstance(prim, Prim), f"Expected a primitive, got {type(prim)}"
    assert len(prim.vertices()) == 4, f"Expected quad prim with 4 vertices, got {len(prim.vertices())}"
    assert scope is None or prim in scope, "prim must be in scope"


def _create_cut_point(
    geo: Geometry,
    start_point: Point,
    end_point: Point,
    scalar: float,
    use_ratio: bool,
) -> Point:
    point = geo.createPoint()
    point.setPosition(_calc_loop_cut_position(start_point, end_point, scalar, use_ratio))
    return point


def _traverse_loop(
    state: _LoopCutState,
    first_prim: Prim,
    s_initial: Point,
    e_initial: Point,
    m_initial: Point,
) -> tuple[list[Point], bool]:
    curr_prim: Prim | None = first_prim
    s_cur = s_initial
    e_cur = e_initial
    m_cur = m_initial
    added_points: list[Point] = []

    while curr_prim is not None:
        state.visited_prims.append(curr_prim)

        s_nxt, e_nxt, forward = _get_opposite_edge_points(curr_prim, s_cur, e_cur)
        m_nxt, next_prim, closed = _get_next_loop_step(state, curr_prim, s_nxt, e_nxt)

        _record_split_faces(state, s_cur, e_cur, m_cur, s_nxt, e_nxt, m_nxt, forward)

        if closed:
            return added_points, True

        if next_prim is None:
            added_points.append(m_nxt)
            return added_points, False

        added_points.append(m_nxt)

        curr_prim = next_prim
        s_cur = s_nxt
        e_cur = e_nxt
        m_cur = m_nxt

    return added_points, False


def _get_opposite_edge_points(
    prim: Prim,
    s_cur: Point,
    e_cur: Point,
) -> tuple[Point, Point, bool]:
    points = list(prim.points())

    i_s = points.index(s_cur)
    i_e = points.index(e_cur)
    forward = (i_e - i_s) % 4 == 1

    if forward:
        e_nxt = points[(i_s + 2) % 4]
        s_nxt = points[(i_s + 3) % 4]
    else:
        s_nxt = points[(i_e + 2) % 4]
        e_nxt = points[(i_e + 3) % 4]

    return s_nxt, e_nxt, forward


def _get_next_loop_step(
    state: _LoopCutState,
    curr_prim: Prim,
    s_nxt: Point,
    e_nxt: Point,
) -> tuple[Point, Prim | None, bool]:
    if _is_start_edge(state, s_nxt, e_nxt):
        return state.m_start, None, True

    adjacent_prims = _get_adjacent_prims(state.geo, curr_prim, s_nxt, e_nxt)

    if state.root_prim in adjacent_prims:
        return state.m_start, None, True

    candidates = [prim for prim in adjacent_prims if _is_valid_next_prim(state, prim)]

    m_nxt = _create_cut_point(state.geo, s_nxt, e_nxt, state.scalar, state.use_ratio)
    next_prim = candidates[0] if len(candidates) == 1 else None

    return m_nxt, next_prim, False


def _is_start_edge(state: _LoopCutState, point_a: Point, point_b: Point) -> bool:
    return {point_a, point_b} == {state.start_point, state.end_point}


def _get_adjacent_prims(
    geo: Geometry,
    curr_prim: Prim,
    point_a: Point,
    point_b: Point,
) -> list[Prim]:
    edge = geo.findEdge(point_a, point_b)
    if edge is None:
        return []
    return [prim for prim in edge.prims() if prim != curr_prim]


def _is_valid_next_prim(state: _LoopCutState, prim: Prim) -> bool:
    if prim in state.visited_prims:
        return False
    if len(prim.vertices()) != 4:
        return False
    if state.scope is not None and prim not in state.scope:
        return False
    return True


def _record_split_faces(
    state: _LoopCutState,
    s_cur: Point,
    e_cur: Point,
    m_cur: Point,
    s_nxt: Point,
    e_nxt: Point,
    m_nxt: Point,
    forward: bool,
) -> None:
    state.cut_edges.append((m_cur, m_nxt))
    if forward:
        state.end_side_faces.append([m_cur, e_cur, e_nxt, m_nxt])
        state.start_side_faces.append([s_cur, m_cur, m_nxt, s_nxt])
    else:
        state.end_side_faces.append([e_cur, m_cur, m_nxt, e_nxt])
        state.start_side_faces.append([m_cur, s_cur, s_nxt, m_nxt])


def _find_opposite_start_prim(state: _LoopCutState) -> Prim | None:
    edge = state.geo.findEdge(state.start_point, state.end_point)
    if edge is None:
        return None
    candidates = [prim for prim in edge.prims() if _is_valid_next_prim(state, prim)]
    return candidates[0] if len(candidates) == 1 else None


def _rebuild_loop_faces(
    state: _LoopCutState,
) -> dict[frozenset[Point], tuple[Prim, Prim]]:
    attr_data = collect_prim_attribs(state.visited_prims)

    state.geo.deletePrims(state.visited_prims, keep_points=True)

    end_side_prims = fill_faces(state.end_side_faces, attr_data)
    start_side_prims = fill_faces(state.start_side_faces, attr_data)

    return {
        frozenset(edge): (start_prim, end_prim)
        for edge, start_prim, end_prim in zip(state.cut_edges, start_side_prims, end_side_prims)
    }


def _calc_loop_cut_position(
    p_start: Point,
    p_end: Point,
    scalar: float,
    use_ratio: bool
) -> Vector3:
    if use_ratio:
        return interpolate_point(p_start, p_end, scalar)

    pos_s = p_start.position()
    pos_e = p_end.position()
    v = pos_e - pos_s
    length = v.length()
    assert length > 1e-6
    return pos_s + (v / length) * scalar
