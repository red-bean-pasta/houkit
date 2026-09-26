from typing import Sequence, Any, Iterator

from hou import Vector3, Prim, Point, Face, Matrix3, Matrix4, Quaternion

from .. import geomath


class Edge:
    def __init__(self, point1: int, point2: int, reorder: bool = False) -> None:
        if reorder:
            self.start = min(point1, point2)
            self.end = max(point1, point2)
        else:
            self.start = point1
            self.end = point2

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Edge):
            return self.start == other.start and self.end == other.end
        return False

    def __hash__(self) -> int:
        return hash((self.start, self.end))

    def __iter__(self):
        yield self.start
        yield self.end

    @staticmethod
    def from_points(point1: Point, point2: Point, reorder: bool = False) -> "Edge":
        return Edge(point1.number(), point2.number(), reorder)


def is_neighbor(p1: Point, p2: Point) -> bool:
    assert is_same_geo((p1, p2))
    geo = p1.geometry()
    return geo.findEdge(p1, p2) is not None

def check_neighbors(target: Point, samples: Sequence[Point]) -> list[Point]:
    if not samples:
        return []
    return [p for p in samples if is_neighbor(target, p)]

def get_first_neighbor(target: Point, samples: Sequence[Point]) -> Point | None:
    if not samples:
        return None
    return next((p for p in samples if is_neighbor(target, p)), None)


def find_prims(
    reference_point: Point,
    *required_points: Point
) -> Iterator[Prim]:
    return (
        prim
        for prim in reference_point.prims()
        if all(point in prim.points() for point in required_points)
    )


def interpolate_point(
    p0: Point,
    p1: Point,
    ratio: float,
) -> Vector3:
    """

    :param p0:
    :param p1:
    :param ratio: How closer to p0
    :return:
    """
    return p0.position() * (1 - ratio) + p1.position() * ratio


def point_distance_to_line(
    point: Point,
    line: Edge | tuple[Point, Point]
) -> float:
    if isinstance(line, Edge):
        points_by_number = {
            candidate.number(): candidate
            for candidate in point.geometry().points()
        }
        p0 = points_by_number[line.start]
        p1 = points_by_number[line.end]
    else:
        p0, p1 = line
    return geomath.point_distance_to_line(
        point.position(),
        (p0.position(), p1.position())
    )


def line_intersect_line(
    first_line: tuple[Point, Point],
    second_line: tuple[Point, Point],
) -> Vector3:
    """Return the projected intersection of two 3D lines on first line."""
    return geomath.line_intersect_line(
        tuple(p.position() for p in first_line),
        tuple(p.position() for p in second_line),
    )


def get_prims_normal(prims: Prim | Face | Sequence[Prim]) -> Vector3:
    if not isinstance(prims, Sequence):
        return get_prim_normal(prims)

    normal = sum((get_prim_normal(prim) for prim in prims), Vector3())
    assert normal.length() > 1e-6, "Expected a nonzero averaged primitive normal"
    return normal.normalized()

def get_prim_normal(prim: Prim | Face) -> Vector3:
    if isinstance(prim, Face):
        return prim.normal()

    pts = [v.point().position() for v in prim.vertices()]
    n = Vector3()
    for i, p in enumerate(pts):
        q = pts[(i + 1) % len(pts)]
        n += Vector3(
            (p[1] - q[1]) * (p[2] + q[2]),
            (p[2] - q[2]) * (p[0] + q[0]),
            (p[0] - q[0]) * (p[1] + q[1])
        )
    return -n.normalized()


def unique_prim_points(prims: Sequence[Prim]) -> list[Point]:
    points = []
    seen = set()
    for prim in prims:
        for point in prim.points():
            if point in seen:
                continue
            seen.add(point)
            points.append(point)
    return points


def get_edge_prim_count(
        prims: Sequence[Prim]
) -> dict[Edge, int]:
    counts: dict[Edge, int] = {}
    for p in prims:
        pts = [v.point().number() for v in p.vertices()]
        n = len(pts)
        for i in range(n):
            edge = Edge(pts[i], pts[(i + 1) % n], reorder=True)
            counts[edge] = counts.get(edge, 0) + 1
    return counts


def get_prim_centroid(prims: Prim | Sequence[Prim]) -> Vector3:
    if isinstance(prims, Prim):
        prims = (prims,)
    assert len(prims) > 0, "Expected at least one primitive to compute centroid"
    center = Vector3()
    for prim in prims:
        center += prim.boundingBox().center()
    return center / len(prims)


def order_prim_points(
    points: Sequence[Point],
    edge: tuple[Point, Point],
    assert_count: int | None = None,
) -> list[Point]:
    """

    :param points:
    :param edge:
    :param assert_count:
    :return: the first and second points are the edge
    """
    l = len(points)
    if assert_count is not None:
        assert l == assert_count

    p_a, p_b = edge
    assert p_a in points and p_b in points and p_a != p_b, f"edge {edge} must be in points"

    idx_a = points.index(p_a)
    idx_b = points.index(p_b)
    diff = (idx_b - idx_a) % l
    assert diff in (1, l-1), f"edge points must be adjacent in points sequence, got diff {diff}"

    if diff == 1:
        return [points[(idx_a + k) % l] for k in range(l)]
    else:
        # return [points[(idx_a - k) % l] for k in range(l)] # To avoid face flipping
        return [points[(idx_b + k) % l] for k in range(l)]


def get_alignment_rotation(
    start: Point,
    middle: Point,
    end: Point,
    middle_transform: Matrix3 | None = None,
) -> Vector3:
    """Get the rotation needed for ``middle_joint-end_joint`` to be on the same line with ``start_joint-middle_joint``

    :param start:
    :param middle:
    :param end:
    :param middle_transform: If None, will try read from attribute "transform"
    """
    if middle_transform is None:
        middle_transform = Matrix4(
            Matrix3(middle.attribValue("transform"))
        )
    middle_transform_inverse = middle_transform.inverted()

    current_direction = (end.position() - middle.position()).normalized()
    target_direction = (middle.position() - start.position()).normalized()
    current_local = current_direction.multiplyAsDir(middle_transform_inverse)
    target_local = target_direction.multiplyAsDir(middle_transform_inverse)

    rotation = Quaternion()
    rotation.setToVectors(current_local, target_local)
    rotation_matrix = Matrix4(rotation.extractRotationMatrix3())
    return rotation_matrix.extractRotates("srt", "xyz")


def traverse_faces_between_edges(
    edge_start: tuple[Point, Point],
    edge_end: tuple[Point, Point],
    side_point: Point | None = None,
    limit: int = 100,
) -> list[Prim]:
    """

    :param edge_start:
    :param edge_end:
    :param side_point: Optional point to disambiguate the traverse direction. This point must be share a quad with edge_start.
    :param limit: Maximum count of returned faces
    :return:
    """
    p1, p2 = edge_start
    target_pts = set(edge_end)

    candidates = [
        prim for prim in p1.prims()
        if p2 in prim.points() and len(prim.points()) == 4
    ]
    assert candidates, f"No quad found sharing starting edge ({p1.number()}, {p2.number()})"

    start_prim = candidates[0]
    if len(candidates) > 1:
        assert side_point, f"Ambiguous quad found sharing starting edge ({p1.number()}, {p2.number()})"
        matching = [c for c in candidates if side_point in c.points()]
        assert len(matching) == 1, (
            f"Expected exactly one starting quad containing side point {side_point.number()} "
            f"across edge ({p1.number()}, {p2.number()}), "
            f"found {len(matching)}"
        )
        start_prim = matching[0]

    faces = [start_prim]
    curr_prim = start_prim
    curr_in_edge = set(edge_start)
    while True:
        opp = [pt for pt in curr_prim.points() if pt not in curr_in_edge]
        assert len(opp) == 2, f"Expected quad opposite edge, got {len(opp)} points"
        if set(opp) == target_pts:
            return faces
        next_candidates = [
            pr for pr in opp[0].prims()
            if opp[1] in pr.points() and pr != curr_prim and len(pr.points()) == 4
        ]
        assert len(next_candidates) == 1, (
            f"Expected single next quad across edge ({opp[0].number()}, {opp[1].number()}), "
            f"found {len(next_candidates)}"
        )
        curr_prim = next_candidates[0]
        curr_in_edge = set(opp)
        faces.append(curr_prim)
        assert len(faces) <= limit, "Quad traversal exceeded limit without reaching target edge"


def is_same_geo(sequence: Sequence[Any]) -> bool:
    if len(sequence) <= 1:
        return True
    first_repr = repr(sequence[0].geometry())
    return all(
        repr(item.geometry()) == first_repr
        for item in sequence[1:]
    )
