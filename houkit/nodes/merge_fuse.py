import hou
from hou import OpNode, SopNode

from .sops import add_merge, add_fuse, add_output


def add_merge_fuse(
    parent: OpNode,
    name: str,
    *p_inputs: OpNode,
) -> SopNode:
    type_name = _get_asset_type_name()
    node_type = hou.sopNodeTypeCategory().nodeTypes().get(type_name)

    if node_type is None:
        subnet = _create_merge_fuse_asset(parent, name, type_name)
    else:
        subnet = parent.createNode(type_name, name)

    for index, node in enumerate(p_inputs):
        subnet.setInput(index, node)

    return subnet


def _create_merge_fuse_asset(
    parent: OpNode,
    name: str,
    type_name: str,
    max_inputs: int = 64,
) -> SopNode:
    subnet = parent.createNode("subnet", name)
    hda = subnet.createDigitalAsset(
        name=type_name,
        save_as_embedded=True,
        min_num_inputs=0,
        max_num_inputs=max_inputs,
    )
    merge = add_merge(hda, "merge", *hda.indirectInputs())
    fuse = add_fuse(hda, "fuse", merge)
    add_output(hda, "OUT", fuse)
    hda.layoutChildren()

    definition = hda.type().definition()
    if definition is not None:
        definition.updateFromNode(hda)

    return hda


def _get_asset_type_name() -> str:
    pkg = (__package__ or __name__).split(".")[0].lstrip("_") or "houkit"
    return f"{pkg}_merge_fuse"