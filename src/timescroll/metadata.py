r"""
"""


#[

from __future__ import annotations

# Standard library imports
from collections import namedtuple

# Local imports
from .schemas import Schema, EmptySchema

#]


__all__ = (
    "build_metadata_class",
)


_METADATA_CLASS_NAME = "Metadata"


def build_metadata_class(
    schema: Schema,
) -> type:
    """Create a metadata class with specified fields"""
    return namedtuple(
        _METADATA_CLASS_NAME,
        schema.fields,
    )


EmptyMetadata = build_metadata_class(schema=EmptySchema, )

