from dataclasses import dataclass

import hou
from hou import OpNode, SopNode

from ..attributings.operator import add_attrib, remove_attribs
from .sops import add_output
from .sopifier import sopify


def add_outside_recalculation(
    parent: OpNode,
    name: str,
    p_input: OpNode,
    reverse: bool = False,
) -> SopNode:
    subnet = _create_subnet(parent, name, p_input)
    clean_orient = _add_orient_polygons(subnet)
    calc = sopify(subnet, clean_orient, _check_majority_insides)
    clean_reverse = _add_reverse_winding(subnet, calc, reverse)
    cleanup = sopify(subnet, clean_reverse, _cleanup_recalculate_outside)
    add_output(subnet, "OUT", cleanup)
    subnet.layoutChildren()
    return subnet


def _create_subnet(parent: OpNode, name: str, p_input: OpNode) -> SopNode:
    subnet = parent.createNode("subnet", name)
    subnet.setInput(0, p_input)
    return subnet


def _add_orient_polygons(subnet: OpNode) -> SopNode:
    clean = subnet.createNode("clean", "orient_polygons")
    clean.setInput(0, subnet.indirectInputs()[0])
    _configure_clean(clean, orient_polygons=True)
    return clean


def _add_reverse_winding(
    subnet: OpNode,
    input_node: OpNode,
    reverse: bool,
) -> SopNode:
    clean = subnet.createNode("clean", "reverse_winding")
    clean.setInput(0, input_node)
    _configure_clean(clean, orient_polygons=False)
    expression = (
        "1 - detail(0, \"tmp_reverse_winding\", 0)"
        if reverse
        else "detail(0, \"tmp_reverse_winding\", 0)"
    )
    clean.parm("reversewinding").setExpression(expression)
    return clean


def _configure_clean(clean: OpNode, orient_polygons: bool) -> None:
    clean.parm("orientpoly").set(int(orient_polygons))
    for parameter in (
        "reversewinding",
        "deldegengeo",
        "delunusedpts",
        "removeunusedgrp",
        "deleteoverlap",
        "delnans",
        "delete_small",
        "fixoverlap",
        "fusepts",
    ):
        clean.parm(parameter).set(0)


def _check_majority_insides(node: SopNode) -> None:
    geo = node.geometry()
    report = _inspect_topology(geo)
    is_inside = False
    if report.is_closed:
        vol = sum(prim.intrinsicValue("measuredvolume") for prim in geo.prims())
        is_inside = vol < 0
    message = "Geometry is closed." if report.is_closed else "Geometry is open."
    node.addMessage(message)
    parent = node.parent()
    if parent is not None:
        parent.setComment(message)
    add_attrib(geo, hou.attribType.Global, "tmp_reverse_winding", 0)
    geo.setGlobalAttribValue("tmp_reverse_winding", 1 if is_inside else 0)


@dataclass(frozen=True)
class _TopologyReport:
    face_count: int
    edge_count: int
    boundary_edges: int
    non_manifold_edges: int
    invalid_primitives: int

    @property
    def is_closed(self) -> bool:
        return (
            self.face_count > 0
            and self.boundary_edges == 0
            and self.non_manifold_edges == 0
            and self.invalid_primitives == 0
        )


def _inspect_topology(geo: hou.Geometry) -> _TopologyReport:
    edge_counts: dict[tuple[int, int], int] = {}
    face_count = 0
    invalid_primitives = 0
    for prim in geo.prims():
        if not isinstance(prim, hou.Face):
            invalid_primitives += 1
            continue
        verts = prim.vertices()
        point_numbers = [vert.point().number() for vert in verts]
        if len(point_numbers) < 3 or len(set(point_numbers)) < 3:
            invalid_primitives += 1
            continue
        face_count += 1
        for i in range(len(point_numbers)):
            p1 = point_numbers[i]
            p2 = point_numbers[(i + 1) % len(point_numbers)]
            edge = (p1, p2) if p1 < p2 else (p2, p1)
            edge_counts[edge] = edge_counts.get(edge, 0) + 1
    return _TopologyReport(
        face_count=face_count,
        edge_count=len(edge_counts),
        boundary_edges=sum(count == 1 for count in edge_counts.values()),
        non_manifold_edges=sum(count > 2 for count in edge_counts.values()),
        invalid_primitives=invalid_primitives,
    )


def _cleanup_recalculate_outside(node: SopNode) -> None:
    geo = node.geometry()
    remove_attribs(geo, global_attributes="tmp_reverse_winding")
