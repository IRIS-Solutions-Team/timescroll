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
from .records import RecordTemplate
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


class Store:

    def __init__(
        self,
        meta_fields: Iterable[str],
        record_class_name: str = "Record",
        converters_after_reading: dict | None = None,
        converters_before_writing: dict | None = None,
    ) -> None:
        r"""
        """
        self.record_class = _records.build_record_class(
            meta_fields=meta_fields,
            class_name=record_class_name,
        )
        self.records = []
        self.converters_after_reading = converters_after_reading
        self.converters_before_writing = converters_before_writing

    def clear_records(self, ) -> None:
        r"""
        """
        self.records = []

    @classmethod
    def from_csv_file(
        klass,
        file_name: str,
        read_records: bool = True,
        skip_when: Callable | None = None,
        **kwargs,
    ) -> Self:
        r"""
        """
        header_fields = _read_header_fields_from_csv_file(file_name, )
        meta_fields = _records.meta_fields_from_all_fields(header_fields, )
        self = klass(
            meta_fields=meta_fields,
            **kwargs,
        )
        if read_records:
            self.read_records_from_csv_file(
                file_name,
                skip_when=skip_when,
                check_header_compliance=False,
            )
        return self

    def read_records_from_csv_file(
        self,
        file_name: str,
        skip_when: Callable = lambda x: x[0].strip() == "",
        check_header_compliance: bool = True,
    ) -> Self:
        r"""
        """
        converters = self.converters_after_reading
        header_fields = _read_header_fields_from_csv_file(file_name, )
        self._check_header_compliance(header_fields, )
        meta_fields = _records.meta_fields_from_all_fields(header_fields, )
        with _read_file(file_name, ) as f:
            reader = csv.reader(f, )
            next(reader, )
            for i in reader:
                if skip_when and skip_when(i, ):
                    continue
                record = self.record_class.from_tuple(i, )
                record.convert_fields(converters, )
                self.records.append(record, )

    def to_csv_file(
        self,
        file_name: str,
    ) -> None:
        r"""
        """
        converters = self.converters_before_writing
        with _write_file(file_name, ) as f:
            writer = csv.writer(f, )
            writer.writerow(self.all_fields, )
            for record in self.records:
                record_to_write = self.record_class.by_converting_fields(record, converters, )
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

    def build_meta_data_tuple(
        self,
        **kwargs,
    ) -> namedtuple:
        r"""
        """
        return self.record_class.meta_data_tuple_factory(**kwargs, )

    def build_record(
        self,
        **kwargs,
    ) -> _records.RecordTemplate:
        r"""
        """
        return self.record_class.from_fields(**kwargs, )

    def submit_records(
        self,
        records: Iterable[_records.RecordTemplate],
    ) -> None:
        r"""
        """
        index_map = self.indexes_by_meta_data([
            i.meta_data for i in records
        ])
        for r in records:
            index = index_map[r.meta_data]
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
        meta_data_targets: Iterable[namedtuple] | None,
        return_missing: bool = False,
    ) -> tuple[namedtuple] | tuple[tuple[namedtuple], tuple[namedtuple]]:
        r"""
        """
        if meta_data_targets is None:
            records = tuple(self.records)
            missing = ()
        else:
            meta_data_targets = set(meta_data_targets)
            index_map = self.indexes_by_meta_data(meta_data_targets, )
            records = tuple(
                self.records[index]
                for index in index_map.values()
                if index is not None
            )
            missing = tuple(
                meta_data
                for meta_data, index, in index_map.items()
                if index is None
            )
        if return_missing:
            return records, missing,
        return records

    def indexes_by_meta_data(
        self,
        meta_data_targets: Iterable[namedtuple],
    ) -> dict[namedtuple, int | None]:
        r"""
        Find indexes of records whose metadata matches any of the target metadata.
        """
        index_map = {
            meta_data: None
            for meta_data in meta_data_targets
        }
        hash_set = set(hash(i) for i in meta_data_targets)
        for index, record, in enumerate(self.records, ):
            record_meta_data_hash = hash(record.meta_data)
            if record_meta_data_hash in hash_set:
                index_map[record.meta_data] = index
                hash_set.remove(record_meta_data_hash)
            if not hash_set:
                break
        return index_map

    def _replace_record(
        self,
        index: int,
        new_record: _records.RecordTemplate,
        check_meta_data_compliance: bool = True,
    ) -> None:
        r"""
        Replace the record at the specified index with a new record.
        """
        if check_meta_data_compliance:
            self.check_meta_data_compliance(new_record, )
        self.records[index] = new_record

    def _append_record(
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
        if record.meta_data._fields != self.record_class.meta_data_tuple_factory._fields:
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

