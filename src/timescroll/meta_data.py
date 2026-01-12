r"""
"""


#[

from __future__ import annotations

# Standard library imports
from collections import namedtuple

#]


__all__ = (
    "build_meta_data_class",
    "build_meta_data_pattern_class",
    "match_namedtuple_pattern",
)


META_DATA_TUPLE_NAME = "MetaData"


def build_meta_data_class(
    meta_fields: Iterable[str],
) -> namedtuple:
    r"""
    """
    return namedtuple(
        META_DATA_TUPLE_NAME,
        meta_fields,
    )


def build_meta_data_pattern_class(
    meta_fields: Iterable[str],
) -> namedtuple:
    r"""
    """
    return namedtuple(
        META_DATA_TUPLE_NAME,
        meta_fields,
        defaults=(None, ) * len(meta_fields),
    )


def match_namedtuple_pattern(
    data: namedtuple,
    pattern: namedtuple | None,
) -> bool:
    r"""
    """
    if pattern is None:
        return True
    for field in data._fields:
        pattern_value = getattr(pattern, field, None, )
        if pattern_value is not None:
            value = getattr(data, field, None, )
            if value != pattern_value:
                return False
    return True

