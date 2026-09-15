import hou
from hou import OpNode, ParmTemplateGroup, ParmTemplate, labelParmType

from ..formatter import snake_case, title_case


def add_folder(
    node: OpNode,
    name: str,
    label: str = "",
    folder_type: hou.folderType = hou.folderType.Tabs,
    **kwargs,
) -> None:
    if not label:
        label = title_case(name)
    ptg = node.parmTemplateGroup()
    folder = ptg.findFolder(label)
    if not folder:
        folder = hou.FolderParmTemplate(name, label, folder_type=folder_type, **kwargs)
        ptg.append(folder)
    node.setParmTemplateGroup(ptg)


def add_heading(
    node: OpNode,
    text: str,
    name: str = "",
    label: str = "",
    folder_label: str = "",
    **kwargs
) -> None:
    group = node.parmTemplateGroup()
    if not name:
        name = snake_case(text)
    heading = hou.LabelParmTemplate(
        name=name,
        label=label if label else text,
        **kwargs
    )
    heading.setLabelParmType(labelParmType.Heading)

    _add_to_group(group, heading, folder_label)
    node.setParmTemplateGroup(group)
    node.parm(name).set(text)


def add_float_parm(
    node: OpNode,
    name: str,
    size: int = 1,
    default: float | tuple[float, ...] = (0.0,),
    min_max: tuple[float | None, float | None] = (None, None),
    naming_scheme: hou.parmNamingScheme = hou.parmNamingScheme.XYZW,
    label: str = "",
    folder_label: str = "",
    **kwargs
) -> None:
    group = node.parmTemplateGroup()

    if isinstance(default, (int, float)):
        default = (float(default),)
    else:
        default = tuple(float(x) for x in default)
    param = hou.FloatParmTemplate(
        name,
        label if label else title_case(name),
        num_components=size,
        default_value=default,
        naming_scheme=naming_scheme,
        **kwargs,
    )
    p_min, p_max = min_max
    if p_min is not None:
        param.setMinValue(p_min)
        param.setMinIsStrict(True)
    if p_max is not None:
        param.setMaxValue(p_max)
        param.setMaxIsStrict(True)

    _add_to_group(group, param, folder_label)
    node.setParmTemplateGroup(group)


def _add_to_group(
    group: ParmTemplateGroup,
    parameter: ParmTemplate,
    folder: str
) -> None:
    if not folder:
        group.append(parameter)
    else:
        group.appendToFolder(folder, parameter)
