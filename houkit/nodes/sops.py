from hou import OpNode, SopNode, Vector3


def add_merge(
    parent: OpNode,
    name: str,
    *inputs: OpNode,
) -> SopNode:
    merge = parent.createNode("merge", name)
    for index, node in enumerate(inputs):
        merge.setInput(index, node)
    return merge

def add_fuse(
    parent: OpNode,
    name: str,
    p_input: OpNode,
) -> SopNode:
    fuse = parent.createNode("fuse", name)
    fuse.setInput(0, p_input)
    return fuse

def add_mirror(
    parent: OpNode,
    name: str,
    p_input: OpNode,
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
    parent: OpNode,
    name: str,
    p_input: OpNode,
) -> SopNode:
    output = parent.createNode("null", name)
    output.setInput(0, p_input)
    output.setDisplayFlag(True)
    output.setRenderFlag(True)
    return output

def add_rig_pose(
    parent_node: OpNode,
    input_node: SopNode,
    *rotations: tuple[str, Vector3]
) -> SopNode:
    """

    :param parent_node:
    :param input_node:
    :param rotations: rotations in xyz in srt order
    """
    pose = parent_node.createNode("kinefx::rigpose", "rig_pose")
    pose.setInput(0, input_node)

    pose.parm("transformations").set(len(rotations))
    for index, (name, rotation) in enumerate(rotations):
        pose.parm(f"group{index}").set(f"@name={name}")
        pose.parm(f"xOrd{index}").set("srt")
        pose.parm(f"rOrd{index}").set("xyz")
        pose.parmTuple(f"r{index}").set(tuple(rotation))
    return pose