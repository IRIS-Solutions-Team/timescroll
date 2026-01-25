r"""
"""


#[

from __future__ import annotations

# Standard library imports
from collections import Counter, namedtuple

# Typing imports
from typing import Any, Iterable

# Local imports
from .metadata import build_metadata_class, EmptyMetadata

#]


__all__ = (
    "Record",
)


class Record:

    __slots__ = (
        "metadata",
        "start_period",
        "observations",
    )

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
    def __hash__(self, ) -> int:
        r"""
        """
        return hash(self.metadata) if self.metadata is not None else 0

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
        return type(self)(
            metadata=self.metadata,
            start_period=self.start_period,
            observations=self.observations,
        )


def _validate_unique_fields(fields: tuple[str], ) -> tuple[str]:
    r"""
    """
    #[
    counter = Counter(fields)
    nonunique_fields = [field for field, count in counter.items() if count > 1]
    if nonunique_fields:
        raise ValueError(f"Non-unique field names: {nonunique_fields}", )
    return fields
    #]

