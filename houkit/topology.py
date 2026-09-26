from typing import Iterator

from hou import Point, Prim

from .topologies import helper
# noinspection PyUnusedImports
from .topologies.basic import (
    points_to_positions,
    add_point,
    offset_point,
    fill_face,
    fill_faces,
    fill_face_by_attrib,
)
# noinspection PyUnusedImports
from .topologies.face_offseter import (
    inset,
    outset,
    partition_connected_prims,
)
# noinspection PyUnusedImports
from .topologies.helper import (
    Edge,
    is_neighbor,
    check_neighbors,
    get_first_neighbor,
    get_prims_normal,
    get_prim_normal,
    unique_prim_points,
    get_edge_prim_count,
    get_prim_centroid,
    interpolate_point,
    point_distance_to_line,
    order_prim_points,
    is_same_geo,
    line_intersect_line,
    get_alignment_rotation,
    traverse_faces_between_edges,
)
# noinspection PyUnusedImports
from .topologies.sorter import (
    Axis,
    sort_points_by_position,
)
# noinspection PyUnusedImports
from .topologies.extruder import (
    extrude,
)
# noinspection PyUnusedImports
from .topologies.loop_cutter import (
    loop_cut,
)
# noinspection PyUnusedImports
from .topologies.pentagon_handler import (
    fill_pentagon,
    fill_pentagon_with_buffer,
)
# noinspection PyUnusedImports
from .topologies.merger import (
    merge_points,
)
# noinspection PyUnusedImports
from .topologies.splitter import (
    split_point,
)


def find_prim(
    *points: Point
) -> Prim:
    """Return the first primitive containing ``reference_point`` and all required points."""
    reference, *rest = points
    return next(find_prims(reference, *rest))

def find_prims(
    *points: Point
) -> Iterator[Prim]:
    """Return the primitives containing ``reference_point`` and all required points."""
    reference, *rest = points
    return helper.find_prims(reference, *rest)
