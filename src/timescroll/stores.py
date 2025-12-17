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
from . import records as _records

#]


__all__ = (
    "Store",
)


_read_file = ft.partial(
    open,
    mode="rt",
    encoding="utf-8",
    newline="",
)


_write_file = ft.partial(
    open,
    mode="wt",
    encoding="utf-8",
    newline="",
)


class Store:

    def __init__(
        self,
        meta_fields: Iterable[str],
        record_class_name: str = "Record",
        converter_after_reading: dict | None = None,
        converter_before_writing: dict | None = None,
    ) -> None:
        r"""
        """
        self.record_class = _records.build_record_class(
            meta_fields=meta_fields,
            class_name=record_class_name,
        )
        self.records = []
        self.converter_after_reading = converter_after_reading
        self.converter_before_writing = converter_before_writing

    def clear_records(self, ) -> None:
        r"""
        """
        self.records = []

    @classmethod
    def from_csv_file(
        klass,
        file_name: str,
        read_records: bool = True,
        **kwargs,
    ) -> Self:
        r"""
        """
        meta_fields = _read_meta_fields_from_csv_file(file_name, )
        self = klass(
            meta_fields=meta_fields,
            **kwargs,
        )
        if read_records:
            self.read_records_from_csv_file(file_name, )
        return self

    def read_records_from_csv_file(
        self,
        file_name: str,
    ) -> Self:
        r"""
        """
        converter = self.converter_after_reading
        with _read_file(file_name, ) as f:
            reader = csv.reader(f, )
            header = next(reader, )
            self._check_header_compliance(header, )
            for i in reader:
                record = self.record_class.from_tuple(i, )
                record.convert_fields(converter, )
                self.records.append(record, )

    def to_csv_file(
        self,
        file_name: str,
    ) -> None:
        r"""
        """
        converter = self.converter_before_writing
        with _write_file(file_name, ) as f:
            writer = csv.writer(f, )
            writer.writerow(self.all_fields, )
            for record in self.records:
                record_to_write = self.record_class.by_converting_fields(record, converter, )
                writer.writerow(record_to_write.to_tuple(), )

    @property
    def meta_fields(self) -> Iterable[str]:
        r"""
        """
        return self.record_class.meta_fields

    @property
    def all_fields(self) -> Iterable[str]:
        r"""
        """
        return self.record_class.all_fields

    @property
    def num_records(self, ) -> int:
        r"""
        """
        return len(self.records)

    def create_meta_data(
        self,
        **kwargs,
    ) -> namedtuple:
        r"""
        """
        return self.record_class._meta_data_tuple_factory(**kwargs, )

    def create_record(
        self,
        **kwargs,
    ) -> _records.RecordTemplate:
        r"""
        """
        return self.record_class.from_fields(**kwargs, )

    def find_indexes_by_matching(
        self,
        targets: Iterable[namedtuple],
    ) -> tuple[list[namedtuple], list[namedtuple], ]:
        r"""
        Find indexes of records whose metadata matches any of the target metadata.
        """
        if not targets:
            return [], [],
        target_set = set(targets)
        matching_indexes = []
        for index, record in enumerate(self.records, ):
            if record.meta_data and record.meta_data in target_set:
                matching_indexes.append(index, )
                target_set.remove(record.meta_data)
                if not target_set:
                    break
        return matching_indexes, list(target_set),

    def replace_record(
        self,
        index: int,
        new_record: _records.RecordTemplate,
        check_meta_data_compliance: bool = True,
        check_meta_data_uniqueness: bool = True,
    ) -> None:
        r"""
        Replace the record at the specified index with a new record.
        """
        if check_meta_data_compliance:
            self.check_meta_data_compliance(new_record, )
        if check_meta_data_uniqueness:
            self.check_meta_data_uniqueness(new_record, )
        self.records[index] = new_record

    def append_record(
        self,
        new_record: _records.RecordTemplate,
        check_meta_data_compliance: bool = True,
        check_meta_data_uniqueness: bool = True,
    ) -> None:
        r"""
        Append a new record to the store.
        """
        if check_meta_data_compliance:
            self.check_meta_data_compliance(new_record, )
        if check_meta_data_uniqueness:
            self.check_meta_data_uniqueness(new_record, )
        self.records.append(new_record, )

    def check_meta_data_compliance(
        self,
        record: _records.RecordTemplate,
    ) -> None:
        r"""
        """
        if record.meta_data._fields != self.record_class._meta_data_tuple_factory._fields:
            raise TypeError(
                "The record's meta_data does not match the store's meta_data structure."
            )

    def check_meta_data_uniqueness(
        self,
        new_record: _records.RecordTemplate,
    ) -> None:
        r"""
        """
        matching_record = next((
            i for i in self.records
            if i.meta_data == new_record.meta_data
        ), None)
        if matching_record is not None:
            raise ValueError(
                "The record's meta_data already exists in the store."
            )

    def _check_header_compliance(
        self,
        header: Iterable[str],
    ) -> None:
        r"""
        """
        if tuple(header) != self.all_fields:
            raise ValueError(
                "The CSV file header does not match the expected fields."
            )


def _read_meta_fields_from_csv_file(
    file_name: str,
) -> tuple[str, ...]:
    r"""
    """
    #[
    with _read_file(file_name, ) as f:
        reader = csv.reader(f, )
        header = next(reader, )
        meta_fields = _records.meta_fields_from_all_fields(header, )
    return meta_fields
    #]

