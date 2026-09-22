from hou import attribType, Geometry, attribData


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