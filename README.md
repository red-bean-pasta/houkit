# Houkit

A utility for procedural modeling with the Houdini Object Model (HOM). Houkit is built for Python SOP workflows: use **Python for the modeling** logic, and use the **SOP network** to inspect every stage of the result.

It suits **programming-oriented, precision, math-driven, and procedural modeling**. A SOP stage can be displayed or bypassed while you inspect points, topology, attributes, warnings, and intermediate geometry in Houdini.

## Features

- **Turn module-level Python functions into Python SOPs.** Build a network in code without losing Houdini’s normal debugging workflow.

  ```python
  extruded = sopify(subnet, head.indirectInputs()[0], _extrude_lips)
  add_output(head, "OUT_HEAD", extruded)
  ```

- **Use attributes as stable point references.** Complex models outgrow point-number references. Name a point `leg_2_joint`, retrieve it later, and retain that relationship while topology changes.

  ```python
  p0, p1, p2 = points_from_geo(geo, "id", "a", "b", "c")
  ```

- **Reload changed Python modules from Houdini.** This shortens the edit-and-test loop without restarting Houdini or regenerating the HIP file. Regenerate when the SOP network or its parameter interface changes.

  ```python
  head = add_reloadable_subnet(parent, "head")
  ```

Topology helpers include inset, outset, extrusion, quad-based pentagon fills, loop cuts, point merging, point splitting, and normal recalculation. Attribute and group data is preserved where operations rebuild geometry.

```python
inset_result = inset(prims, scalar=1, use_ratio=False, follow_existing_edge=True)
```

For SOP interfaces, Houkit adds reloadable subnets, common built-in SOPs such as Mirror, Fuse, and Output, parameter folders and headings, and promoted controls.

```python
leg = add_reloadable_subnet(parent, "leg")
add_float_parm(leg, "length")
length = get_parms(leg).length
```

For the complete API and type signatures, inspect the façade source files.


## Setup

Set Houdini’s `hython` executable as the project interpreter. Houkit is tested with Houdini 22.0.368 and its Python 3.11 build; no additional packages are required because Houdini includes NumPy.

Add Houkit as a top-level submodule:
```sh
git submodule add https://github.com/red-bean-pasta/houkit houkit
```

Make the submodule root importable in the Houdini project, then use the public façade modules—for example, `houkit.topology.inset` rather than `houkit.topologies.face_offseter.inset`. The façades are the stable interface; internal modules may be refactored.


## Main modules

- `topology` — topology creation, editing, adjacency, and spatial helpers.
- `attributer` — create, query, positionally name, deduplicate, and transfer attributes. 
- `noder` — build SOP networks, generate Python SOPs, create reload controls, and add common nodes such as merge, fuse, mirror, and output.
- `parameterizer` — add parameters, read parameter values, and promote child-network controls.
- `geomath` — vector and line operations, rotations, and conic or elliptical interpolation for geometry algorithms.
- `grouper`, `formatter`, and `developing` — small helpers for geometry groups, naming, saving, and module reloads.

## Example

This Python SOP creates a named quad, extrudes it, then retrieves and moves one point by its semantic identifier. In a larger network, keep stages this small so every SOP remains easy to inspect.

```python
import hou
from hou import Vector3

from houkit.topology import add_point, fill_face, extrude, offset_point
from houkit.attributer import add_point_attrib, points_from_geo


geo = hou.pwd().geometry()

add_point_attrib(geo, "id", "")

points = [
    add_point(geo, Vector3(0, 0, 0), ("id", "corner_1")),
    add_point(geo, Vector3(1, 0, 0), ("id", "corner_2")),
    add_point(geo, Vector3(1, 1, 0), ("id", "corner_3")),
    add_point(geo, Vector3(0, 1, 0), ("id", "corner_4")),
]
face = fill_face(points)
extrude(face, 0.25)

corner_1, = points_from_geo(geo, "id", "corner_1")
offset_point(corner_1, Vector3(-1, 0, 0))
```

## More examples

[Houdini Spider Generator](https://github.com/red-bean-pasta/houdini-spider-generator) is a complete procedural-modeling project built with Houkit.


## Acknowledgements

This project is manually directed, reviewed, structured, and tested at the method level. AI assists with implementation within that process.

