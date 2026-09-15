from hou import SopNode, Vector3


def add_merge(
    parent: SopNode,
    name: str,
    *inputs: SopNode,
) -> SopNode:
    merge = parent.createNode("merge", name)
    for index, node in enumerate(inputs):
        merge.setInput(index, node)
    return merge

def add_fuse(
    parent: SopNode,
    name: str,
    p_input: SopNode,
) -> SopNode:
    fuse = parent.createNode("fuse", name)
    fuse.setInput(0, p_input)
    return fuse

def add_mirror(
    parent: SopNode,
    name: str,
    p_input: SopNode,
    axis: Vector3 | tuple[float, float, float],
    keep_original: bool,
    consolidate_unshared: bool,
    *args,
) -> SopNode:
    mirror = parent.createNode("mirror", name, *args)
    mirror.setInput(0, p_input)
    mirror.parm("keepOriginal").set(keep_original)
    mirror.parm("dirx").set(axis[0])
    mirror.parm("diry").set(axis[1])
    mirror.parm("dirz").set(axis[2])
    mirror.parm("consolidateunshared").set(consolidate_unshared)
    return mirror

def add_output(
    parent: SopNode,
    name: str,
    p_input: SopNode,
) -> SopNode:
    output = parent.createNode("null", name)
    output.setInput(0, p_input)
    output.setDisplayFlag(True)
    output.setRenderFlag(True)
    return output