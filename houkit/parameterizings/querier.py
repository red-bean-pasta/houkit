from typing import TypeVar, get_origin, get_args, Any

import hou
from hou import OpNode, Vector3, ParmTuple

T = TypeVar("T")


class Parameters(dict[str, Any]):
    """A dictionary subclass supporting attribute-style parameter access (e.g., `param.width`)."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"Parameter '{name}' not found") from None

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value

    def __delattr__(self, name: str) -> None:
        try:
            del self[name]
        except KeyError:
            raise AttributeError(f"Parameter '{name}' not found") from None


def get_parms(
    node: OpNode,
    exclude_internal: bool = True,
    use_tuple: bool = True,
) -> Parameters:
    params = Parameters()

    for pt in node.parmTuples():
        if _should_skip_parm_tuple(pt, exclude_internal):
            continue
        params[pt.name()] = _evaluate_parm_tuple(pt, use_tuple)

    return params


def get_parm(node: OpNode, name: str, cls: type[T]) -> T:
    runtime_type = get_origin(cls) or cls

    if runtime_type is tuple:
        value = node.evalParmTuple(name)
    else:
        value = node.evalParm(name)

    assert value is not None, f"Expected parameter {name!r} on {node.path()}"
    assert validate_type(value, cls), f"Expected parameter {name!r} on {node.path()}  to be {cls!r}, got {value!r}"
    return value


def validate_type(value, cls: type[T]) -> bool:
    origin = get_origin(cls)

    if origin is not tuple:
        return isinstance(value, cls)

    if not isinstance(value, tuple):
        return False

    args = get_args(cls)
    if not args:
        return True
    if len(args) == 2 and args[1] is Ellipsis:
        return all(isinstance(v, args[0]) for v in value)
    return (
        len(value) == len(args)
        and all(isinstance(v, t) for v, t in zip(value, args))
    )


def _should_skip_parm_tuple(
    pt: ParmTuple,
    exclude_internal: bool,
) -> bool:
    if exclude_internal and not pt.isSpare():
        return True

    tpl = pt.parmTemplate()
    if isinstance(
        tpl,
        (
            hou.ButtonParmTemplate,
            hou.LabelParmTemplate,
            hou.SeparatorParmTemplate,
        ),
    ):
        return True

    parent = pt[0].parentMultiParm() if hasattr(pt[0], "parentMultiParm") else None
    if parent is not None and isinstance(parent.parmTemplate(), hou.RampParmTemplate):
        return True

    return False

def _evaluate_parm_tuple(
    pt: hou.ParmTuple,
    use_tuple: bool,
):
    tpl = pt.parmTemplate()

    if isinstance(tpl, hou.ToggleParmTemplate):
        return bool(pt[0].evalAsInt())
    if isinstance(tpl, hou.RampParmTemplate):
        return pt[0].evalAsRamp()
    if len(pt) == 1:
        return pt[0].eval()

    evaluated = pt.eval()
    if use_tuple or not isinstance(tpl, hou.FloatParmTemplate):
        return evaluated
    return _convert_float_tuple(tpl, pt, evaluated)

def _convert_float_tuple(
    tpl: hou.FloatParmTemplate,
    pt: hou.ParmTuple,
    evaluated,
):
    if not _is_vector_template(tpl):
        return evaluated
    match len(pt):
        case 2:
            return hou.Vector2(evaluated)
        case 3:
            return Vector3(evaluated)
        case 4:
            return hou.Vector4(evaluated)
        case _:
            return evaluated

def _is_vector_template(tpl: hou.FloatParmTemplate) -> bool:
    return (
        tpl.namingScheme()
        in (
            hou.parmNamingScheme.XYZW,
            hou.parmNamingScheme.UVW,
            hou.parmNamingScheme.XYWH,
        )
        or tpl.look() == hou.parmLook.Vector
    )
