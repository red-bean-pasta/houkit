import re
from collections import defaultdict
from typing import Sequence, Iterator

from hou import Geometry, Point, Prim


def points_by_attrib(
    source: Geometry | Prim | Sequence[Prim],
    attribute: str,
    skip_blank: bool = False,
) -> dict[str, set[Point]]:
    result: defaultdict[str, set[Point]] = defaultdict(set)
    if not isinstance(source, Sequence):
        source = (source,)
    for s in source:
        for point in s.points():
            value = point.stringAttribValue(attribute)
            if value or not skip_blank:
                result[value].add(point)
    return dict(result)


def points_start_with(
    geo: Geometry,
    attribute: str,
    prefixes: str | tuple[str, ...],
) -> list[Point]:
    return [
        point
        for point, value in zip(
            geo.points(),
            geo.pointStringAttribValues(attribute),
        )
        if value.startswith(prefixes)
    ]


def unique_points_start_with(
    geo: Geometry,
    attribute: str,
    prefixes: str | tuple[str, ...],
) -> dict[str, dict[str, Point]]:
    """

    :param geo:
    :param attribute:
    :param prefixes:
    :return: dict[prefix, dict[attribute_value, point]]
    """
    result = defaultdict(dict)
    for point, value in zip(
        geo.points(),
        geo.pointStringAttribValues(attribute),
    ):
        if not value:
            continue
        matched = next(
            (p for p in prefixes if value.startswith(p)),
            None
        )
        if not matched:
            continue
        assert value not in result[matched], f"Duplicate point {attribute}: {value}"
        result[matched][value] = point
    return result


def unique_points_by_attrib(
    source: Geometry | Prim | Sequence[Prim],
    attribute: str,
) -> dict[str, Point]:
    result = {}
    if not isinstance(source, Sequence):
        source = (source,)
    for g in source:
        for point in g.points():
            value = point.stringAttribValue(attribute)
            if not value:
                continue
            assert value not in result, f"Duplicate point {attribute}: {value}"
            result[value] = point
    return result


def latest_points_by_attrib(
    geo: Geometry,
    attribute: str,
    *values: str,
    assert_existing: bool = True,
) -> Iterator[Point]:
    """

    :param geo:
    :param attribute:
    :param values:
    :param assert_existing: If False, missing point will return None
    :return:
    """
    pts = points_by_attrib(geo, attribute, skip_blank=True)
    for v in values:
        if v not in pts:
            if not assert_existing:
                yield None
                continue
            raise AssertionError(f"Missing value '{v}' for attribute '{attribute}'")
        candidates = pts[v]
        yield max(candidates, key=lambda point: point.number())


def scan_indexed_attrib_range(
    geo: Geometry,
    attribute: str,
    prefix: str,
) -> tuple[int, int] | None:
    values = geo.pointStringAttribValues(attribute)
    numbers: list[int] = []
    for value in values:
        if prefix:
            if not value.startswith(prefix):
                continue
            remainder = value[len(prefix):]
            match = re.search(r"-?\d+", remainder)
        else:
            match = re.search(r"-?\d+", value)
        if match is not None:
            numbers.append(int(match.group()))

    if not numbers:
        return None
    return min(numbers), max(numbers)
