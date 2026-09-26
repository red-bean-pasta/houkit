from hou import attribType, Geometry, attribData, Vector3

from houkit.attributings.querier import unique_points_by_attrib
from houkit.topology import get_alignment_rotation


def write_skinning_capture_attribs(
    geo: Geometry,
    bones: list[str],
    weights: dict[int, list[tuple[str, float]]],
) -> None:
    """

    :param geo:
    :param bones: bone names
    :param weights: dict[point, list[tuple[bone_index, weight]]]
    """
    path_attr = geo.addArrayAttrib(attribType.Global, "boneCapture_pCaptPath", attribData.String)
    geo.setGlobalAttribValue(path_attr, bones)

    idx_attr = geo.addArrayAttrib(attribType.Point, "boneCapture_index", attribData.Int)
    data_attr = geo.addArrayAttrib(attribType.Point, "boneCapture_data", attribData.Float)

    for p in geo.points():
        w = weights[p.number()]
        p.setAttribValue(idx_attr, tuple(item[0] for item in w))
        p.setAttribValue(data_attr, tuple(item[1] for item in w))


def get_named_point_alignment_rotation(
    geo: Geometry,
    start_joint: str,
    middle_joint: str,
    end_joint: str,
) -> Vector3:
    points = unique_points_by_attrib(geo, "name")
    return get_alignment_rotation(
        points[start_joint],
        points[middle_joint],
        points[end_joint],
    )