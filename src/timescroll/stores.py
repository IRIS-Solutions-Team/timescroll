r"""
"""


#[

from __future__ import annotations

# Standard library imports
import csv
import functools as ft

# Typing imports
from typing import Iterable, Self
from collections import namedtuple

# Local imports
from .records import Record
from .schemas import Schema
from . import records as _records

#]


__all__ = (
    "Store",
)


_read_file = ft.partial(
    open,
    mode="rt",
    encoding="utf-8-sig",
    newline="",
)


_write_file = ft.partial(
    open,
    mode="wt",
    encoding="utf-8-sig",
    newline="",
)


_DEFAULT_CONVERTER_FROM_CSV = {
    "observations": lambda x: float(x) if x != "" else None,
    "start_period": None,
}


class Store:

    def __init__(
        self,
        schema: Schema,
        converters_after_reading: dict | None = None,
        converters_before_writing: dict | None = None,
    ) -> None:
        r"""
        """
        self.schema = schema
        self.converters_after_reading = converters_after_reading
        self.converters_before_writing = converters_before_writing
        self.records = []
        self.metadata_factory = _records.build_metadata_class(schema, )
        self.data_fields = Record.data_fields
        self.metadata_fields = schema.fields
        self.all_fields = self.metadata_fields + self.data_fields

    def clear_records(self, ) -> None:
        r"""
        """
        self.records = []

    def read_records_from_csv_file(
        self,
        file_name: str,
        skip_when: Callable = lambda x: x[0].strip() == "",
        check_header_compliance: bool = True,
        converter: dict[str, Any] | None = _DEFAULT_CONVERTER_FROM_CSV,
    ) -> Self:
        r"""
        """
        header_fields = _read_header_fields_from_csv_file(file_name, )
        self._check_header_compliance(header_fields, )
        with _read_file(file_name, ) as f:
            reader = csv.reader(f, )
            next(reader, )
            for i in reader:
                if skip_when and skip_when(i, ):
                    continue
                record = self.build_record_from_compliant_tuple(i, )
                record.apply_converter(converter, )
                self.records.append(record, )

    def write_records_to_csv_file(
        self,
        file_name: str,
    ) -> None:
        r"""
        """
        with _write_file(file_name, ) as f:
            writer = csv.writer(f, )
            writer.writerow(self.all_fields, )
            for record in self.records:
                writer.writerow(record.to_tuple(), )

    @property
    def num_records(self, ) -> int:
        r"""
        """
        return len(self.records)

    def build_record(
        self,
        **kwargs,
    ) -> Record:
        r"""
        """
        data_kwargs = {
            i: kwargs.pop(i)
            for i in self.data_fields
        }
        metadata_kwargs = {
            i: kwargs.pop(i)
            for i in self.metadata_fields
        }
        metadata = self.metadata_factory(**metadata_kwargs, )
        return Record(
            metadata=metadata,
            **data_kwargs,
        )

    def build_record_from_compliant_tuple(
        self,
        input_tuple: Iterable[Any],
    ) -> Record:
        r"""
        """
        input_tuple = tuple(input_tuple)
        num_metadata_fields = len(self.metadata_fields)
        metadata_tuple = input_tuple[:num_metadata_fields]
        data_tuple = input_tuple[num_metadata_fields:]
        metadata = self.metadata_factory(*metadata_tuple, )
        return Record(
            metadata=metadata,
            start_period=data_tuple[0],
            observations=data_tuple[1:],
        )

    def submit_records(
        self,
        records: Iterable[Record],
    ) -> None:
        r"""
        """
        index_map = self.indexes_by_metadata([
            i.metadata for i in records
        ])
        for r in records:
            index = index_map[r.metadata]
            if index is not None:
                self._replace_record(
                    index=index,
                    new_record=r,
                )
            else:
                self._append_record(
                    new_record=r,
                )

    def request_records(
        self,
        metadata_targets: Iterable[namedtuple] | None,
        return_missing: bool = False,
    ) -> tuple[namedtuple, ...] | tuple[tuple[namedtuple, ...], tuple[namedtuple, ...]]:
        r"""
        """
        if metadata_targets is None:
            records = tuple(self.records)
            missing = ()
        else:
            metadata_targets = set(metadata_targets)
            index_map = self.indexes_by_metadata(metadata_targets, )
            records = tuple(
                self.records[index]
                for index in index_map.values()
                if index is not None
            )
            missing = tuple(
                metadata
                for metadata, index, in index_map.items()
                if index is None
            )
        if return_missing:
            return records, missing,
        return records

    def indexes_by_metadata(
        self,
        metadata_targets: Iterable[namedtuple],
    ) -> dict[namedtuple, int | None]:
        r"""
        Find indexes of records whose metadata matches any of the target metadata.
        """
        index_map = {
            metadata: None
            for metadata in metadata_targets
        }
        hash_set = set(hash(i) for i in metadata_targets)
        for index, record, in enumerate(self.records, ):
            record_metadata_hash = hash(record.metadata)
            if record_metadata_hash in hash_set:
                index_map[record.metadata] = index
                hash_set.remove(record_metadata_hash)
            if not hash_set:
                break
        return index_map

    def _replace_record(
        self,
        index: int,
        new_record: Record,
        check_metadata_compliance: bool = True,
    ) -> None:
        r"""
        Replace the record at the specified index with a new record.
        """
        if check_metadata_compliance:
            self.check_metadata_compliance(new_record, )
        self.records[index] = new_record

    def _append_record(
        self,
        new_record: Record,
        check_metadata_compliance: bool = True,
        check_metadata_uniqueness: bool = True,
    ) -> None:
        r"""
        Append a new record to the store.
        """
        if check_metadata_compliance:
            self.check_metadata_compliance(new_record, )
        if check_metadata_uniqueness:
            self.check_metadata_uniqueness(new_record, )
        self.records.append(new_record, )

    def check_metadata_compliance(
        self,
        record: Record,
    ) -> None:
        r"""
        """
        if not self.schema.validate(record.metadata, ):
            raise TypeError(
                "The record's metadata does not match the store's schema."
            )

    def check_metadata_uniqueness(
        self,
        new_record: Record,
    ) -> None:
        r"""
        """
        matching_record = next((
            i for i in self.records
            if i.metadata == new_record.metadata
        ), None)
        if matching_record is not None:
            raise ValueError(
                "The record's metadata already exists in the store."
            )

    def _check_header_compliance(
        self,
        header_fields: Iterable[str],
    ) -> None:
        r"""
        """
        if tuple(header_fields) != self.all_fields:
            raise ValueError(
                "The CSV file header does not match the Store fields."
            )


def _read_header_fields_from_csv_file(
    file_name: str,
) -> tuple[str, ...]:
    r"""
    """
    #[
    with _read_file(file_name, ) as f:
        reader = csv.reader(f, )
        header_fields = next(reader, )
        if "" in header_fields:
            first_empty = header_fields.index("", )
            header_fields = header_fields[:first_empty]
    return header_fields
    #]

