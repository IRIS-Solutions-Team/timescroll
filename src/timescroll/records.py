r"""
"""


#[

from __future__ import annotations

# Standard library imports
from collections import Counter, namedtuple

# Typing imports
from typing import Any, Iterable

# Local imports
from .schemas import Schema
from .metadata import build_metadata_class, EmptyMetadata

#]


__all__ = (
    "Record",
)


class Record:

    data_fields = (
        "start_period",
        "observations",
    )

    __slots__ = (
        "metadata",
    ) + data_fields

    def __init__(
        self,
        metadata: namedtuple = EmptyMetadata(),
        start_period: str | None = None,
        observations: Iterable[Any] = (),
    ) -> None:
        r"""
        """
        self.metadata = metadata
        self.start_period = start_period
        self.observations = tuple(observations)

    @property
    def all_fields(self, ) -> tuple:
        r"""
        """
        return (
            *self.metadata._fields,
            *self.data_fields,
        )

    @property
    def __hash__(self, ) -> int:
        r"""
        """
        return hash(self.metadata, )

    def __eq__(self, other, ) -> bool:
        r"""
        """
        if not isinstance(other, type(self), ):
            return False
        return all(
            getattr(self, i) == getattr(other, i)
            for i in self.__slots__
        )

    def equal_metadata(self, other, ) -> bool:
        r"""
        """
        return self.metadata == other.metadata

    def to_tuple(self, ) -> tuple:
        r"""
        """
        return (
            *self.metadata,
            self.start_period,
            *self.observations,
        )

    def to_dict(self, ) -> dict:
        r"""
        """
        return {
            **self.metadata._asdict(),
            "start_period": self.start_period,
            "observations": self.observations,
        }

    def copy(self, ) -> Self:
        r"""
        """
        # All fields are immutable, so we can just return a new instance with
        # the same values
        return type(self)(
            metadata=self.metadata,
            start_period=self.start_period,
            observations=self.observations,
        )

    def apply_converter(
        self,
        converter: dict[str, Any] | None,
    ) -> None:
        r"""
        """
        if converter is None:
            return
        observations_converter = converter.get("observations", None)
        if observations_converter:
            self.observations = tuple(
                observations_converter(i)
                for i in self.observations
            )
        start_period_converter = converter.get("start_period", None)
        if start_period_converter:
            self.start_period = start_period_converter(self.start_period)

