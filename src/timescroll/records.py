r"""
"""


#[

from __future__ import annotations

# Standard library imports
from collections import Counter, namedtuple

# Typing imports
from typing import Any, Iterable

# Local imports
from .meta_data import build_meta_data_class

#]


__all__ = (
    "build_record_class",
)


class RecordTemplate:

    __slots__ = (
        "meta_data",
        "start_period",
        "observations",
    )

    all_fields = None
    meta_fields = None
    meta_data_tuple_factory = None

    def __init__(
        self,
        meta_data: namedtuple | None = None,
        start_period: str | None = None,
        observations: Iterable[Any] = (),
    ) -> None:
        r"""
        """
        self.meta_data = meta_data
        self.start_period = start_period
        self.observations = tuple(observations)

    def copy(self, ) -> Self:
        r"""
        """
        return type(self)(
            meta_data=self.meta_data_tuple_factory(*self.meta_data, ),
            start_period=self.start_period,
            observations=tuple(self.observations),
        )

    @property
    def id(self) -> int:
        r"""
        """
        return hash(self.meta_data) if self.meta_data is not None else 0

    def __eq__(self, other, ) -> bool:
        r"""
        """
        if not isinstance(other, type(self), ):
            return False
        return all(
            getattr(self, i) == getattr(other, i)
            for i in self.__slots__
        )

    def equal_meta_data(self, other, ) -> bool:
        r"""
        """
        return self.meta_data == other.meta_data

    @classmethod
    def from_fields(
        klass,
        start_period: str | None = None,
        observations: Iterable[Any] = (),
        **meta_data_kwargs,
    ) -> Self:
        r"""
        """
        meta_data = klass.meta_data_tuple_factory(**meta_data_kwargs, )
        return klass(
            meta_data=meta_data,
            start_period=start_period,
            observations=observations,
        )

    @classmethod
    def from_tuple(
        klass,
        tuple_: Iterable,
    ) -> Self:
        r"""
        """
        meta_fields = klass.meta_data_tuple_factory._fields
        num_meta_fields = len(meta_fields)
        meta_data = klass.meta_data_tuple_factory(*tuple_[:num_meta_fields], )
        start_period = tuple_[num_meta_fields]
        observations = tuple(tuple_[num_meta_fields+1:])
        return klass(
            meta_data=meta_data,
            start_period=start_period,
            observations=observations,
        )

    @classmethod
    def from_dict(
        klass,
        data_dict: dict,
    ) -> Self:
        r"""
        """
        meta_fields = klass.meta_data_tuple_factory._fields
        meta_data = klass.meta_data_tuple_factory(*(
            data_dict[i] for i in meta_fields
        ))
        start_period = data_dict["start_period"]
        observations = tuple(data_dict["observations"])
        return klass(
            meta_data=meta_data,
            start_period=start_period,
            observations=observations,
        )

    @classmethod
    def by_converting_fields(
        klass,
        other: Self,
        converters: dict[str, Callable],
    ) -> Self:
        r"""
        """
        meta_data, start_period, observations, = other._convert(converters, )
        return klass(
            meta_data=meta_data,
            start_period=start_period,
            observations=observations,
        )

    def _convert(
        self,
        converters: dict[str, Callable] | None,
    ) -> tuple[namedtuple, Any, Iterable[Any]]:
        r"""
        """
        if not converters:
            return self.meta_data, self.start_period, self.observations,
        #
        def _convert_value(field, value, ):
            func = converters.get(field, None, )
            return func(value, ) if func else value
        #
        meta_data = self.meta_data_tuple_factory(*(
            _convert_value(field, value, )
            for field, value, in zip(self.meta_fields, self.meta_data, )
        ))
        start_period = _convert_value("start_period", self.start_period, )
        observations_converter = converters.get("observations", None, )
        if observations_converter:
            observations = tuple(observations_converter(i) for i in self.observations)
        else:
            observations = tuple(self.observations)
        return meta_data, start_period, observations,


    def to_tuple(self, ) -> tuple:
        r"""
        """
        return (
            *self.meta_data,
            self.start_period,
            *self.observations,
        )

    def to_dict(self, ) -> dict:
        r"""
        """
        return {
            **self.meta_data._asdict(),
            "start_period": self.start_period,
            "observations": self.observations,
        }

    def convert_fields(
        self,
        converters: dict[str, Callable] | None,
    ) -> None:
        r"""
        """
        meta_data, start_period, observations, = self._convert(converters, )
        self.meta_data = meta_data
        self.start_period = start_period
        self.observations = observations

    def copy(self, ) -> Self:
        r"""
        """
        return type(self)(
            meta_data=self.meta_data,
            start_period=self.start_period,
            observations=self.observations,
        )


# Implement the record factory:

def build_record_class(
    meta_fields: Iterable[str] = (),
    class_name: str = "Record",
) -> Callable:
    r"""
    """
    all_fields = _assemble_all_fields(meta_fields, )
    meta_data_tuple_factory = build_meta_data_class(meta_fields, )
    namespace = {
        "meta_data_tuple_factory": meta_data_tuple_factory,
        "meta_fields": meta_fields,
        "all_fields": all_fields,
    }
    return type(
        class_name,
        (RecordTemplate, ),
        namespace,
    )


def _assemble_all_fields(meta_fields: Iterable[str], ) -> tuple[str]:
    r"""
    """
    return _validate_unique_fields((
        *meta_fields,
        "start_period",
        "observations",
    ))


def _is_all_fields(all_fields: Iterable[str], ) -> bool:
    r"""
    """
    all_fields = tuple(all_fields)
    return (
        len(all_fields) >= 2
        and all_fields[-2] == "start_period"
        and all_fields[-1] == "observations"
    )


def meta_fields_from_all_fields(all_fields: Iterable[str], ) -> tuple[str]:
    r"""
    """
    all_fields = tuple(all_fields)
    if not _is_all_fields(all_fields, ):
        raise ValueError(
            "The last two fields in all_fields must be 'start_period' and 'observations'.",
        )
    return all_fields[:-2]


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

