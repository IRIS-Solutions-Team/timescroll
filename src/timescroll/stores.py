r"""
Clean Store implementation with separated I/O concerns.
"""

from __future__ import annotations

# Typing imports
from typing import Iterable, Self, Any
from collections import namedtuple

# Local imports
from .records import Record
from .schemas import Schema
from .io_protocols import RecordReader, RecordWriter
from .io_csv import CsvReader, CsvWriter
from .io_parquet import ParquetReader, ParquetWriter
from . import records as _records


__all__ = (
    "Store",
)


class Store:
    """
    Time series record store with pluggable I/O backends.
    
    This class manages collections of time series records in memory,
    with the ability to read from and write to various file formats
    through pluggable reader/writer implementations.
    """

    def __init__(
        self,
        schema: Schema,
        converters_after_reading: dict | None = None,
        converters_before_writing: dict | None = None,
    ) -> None:
        """
        Initialize store with schema and optional converters.
        
        Args:
            schema: Schema defining metadata structure
            converters_after_reading: Optional converters applied after reading
            converters_before_writing: Optional converters applied before writing
        """
        self.schema = schema
        self.converters_after_reading = converters_after_reading
        self.converters_before_writing = converters_before_writing
        self.records = []
        self.metadata_factory = _records.build_metadata_class(schema)
        self.data_fields = Record.data_fields
        self.metadata_fields = schema.fields
        self.all_fields = self.metadata_fields + self.data_fields

    def clear_records(self) -> None:
        """Clear all records from the store."""
        self.records = []

    def read_from_file(
        self,
        file_name: str,
        reader: RecordReader,
        **kwargs: Any,
    ) -> Self:
        """
        Read records from file using specified reader.
        
        Args:
            file_name: Path to file to read
            reader: Reader implementation to use
            **kwargs: Additional arguments passed to reader
        """
        for record in reader.read_records(file_name, **kwargs):
            self.records.append(record)
        return self

    def write_to_file(
        self,
        file_name: str,
        writer: RecordWriter,
        **kwargs: Any,
    ) -> None:
        """
        Write records to file using specified writer.
        
        Args:
            file_name: Path to output file
            writer: Writer implementation to use
            **kwargs: Additional arguments passed to writer
        """
        writer.write_records(self.records, file_name, **kwargs)

    def read_records_from_csv_file(self, file_name: str, **kwargs: Any) -> Self:
        """Read records from CSV file."""
        reader = CsvReader(self.schema)
        return self.read_from_file(file_name, reader, **kwargs)

    def write_records_to_csv_file(self, file_name: str, **kwargs: Any) -> None:
        """Write records to CSV file."""
        writer = CsvWriter(self.schema)
        self.write_to_file(file_name, writer, **kwargs)

    def read_records_from_parquet_file(self, file_name: str, **kwargs: Any) -> Self:
        """Read records from Parquet file."""
        reader = ParquetReader(self.schema)
        return self.read_from_file(file_name, reader, **kwargs)

    def write_records_to_parquet_file(self, file_name: str, **kwargs: Any) -> None:
        """Write records to Parquet file."""
        writer = ParquetWriter(self.schema)
        self.write_to_file(file_name, writer, **kwargs)

    @property
    def num_records(self) -> int:
        """Get number of records in store."""
        return len(self.records)

    def build_record(self, **kwargs) -> Record:
        """
        Build a record from keyword arguments.
        
        Args:
            **kwargs: Metadata and data field values
            
        Returns:
            New Record instance
        """
        data_kwargs = {
            i: kwargs.pop(i)
            for i in self.data_fields
        }
        metadata_kwargs = {
            i: kwargs.pop(i)
            for i in self.metadata_fields
        }
        metadata = self.metadata_factory(**metadata_kwargs)
        return Record(
            metadata=metadata,
            **data_kwargs,
        )

    def build_record_from_compliant_tuple(
        self,
        input_tuple: Iterable[Any],
    ) -> Record:
        """
        Build record from tuple matching field order.
        
        Args:
            input_tuple: Tuple of values in metadata + data field order
            
        Returns:
            New Record instance
        """
        input_tuple = tuple(input_tuple)
        num_metadata_fields = len(self.metadata_fields)
        metadata_tuple = input_tuple[:num_metadata_fields]
        data_tuple = input_tuple[num_metadata_fields:]
        metadata = self.metadata_factory(*metadata_tuple)
        return Record(
            metadata=metadata,
            start_period=data_tuple[0],
            observations=data_tuple[1:],
        )

    def submit_records(self, records: Iterable[Record]) -> None:
        """
        Submit records to store, replacing existing ones with same metadata.
        
        Args:
            records: Records to submit
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
        """
        Request records by metadata.
        
        Args:
            metadata_targets: Target metadata to find, or None for all records
            return_missing: If True, also return missing metadata
            
        Returns:
            Found records, optionally with missing metadata
        """
        if metadata_targets is None:
            records = tuple(self.records)
            missing = ()
        else:
            metadata_targets = set(metadata_targets)
            index_map = self.indexes_by_metadata(metadata_targets)
            records = tuple(
                self.records[index]
                for index in index_map.values()
                if index is not None
            )
            missing = tuple(
                metadata
                for metadata, index in index_map.items()
                if index is None
            )
        if return_missing:
            return records, missing
        return records

    def indexes_by_metadata(
        self,
        metadata_targets: Iterable[namedtuple],
    ) -> dict[namedtuple, int | None]:
        """
        Find indexes of records matching target metadata.
        
        Args:
            metadata_targets: Target metadata to find
            
        Returns:
            Mapping from metadata to index (None if not found)
        """
        index_map = {
            metadata: None
            for metadata in metadata_targets
        }
        hash_set = set(hash(i) for i in metadata_targets)
        for index, record in enumerate(self.records):
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
        """Replace record at specified index."""
        if check_metadata_compliance:
            self.check_metadata_compliance(new_record)
        self.records[index] = new_record

    def _append_record(
        self,
        new_record: Record,
        check_metadata_compliance: bool = True,
        check_metadata_uniqueness: bool = True,
    ) -> None:
        """Append new record to store."""
        if check_metadata_compliance:
            self.check_metadata_compliance(new_record)
        if check_metadata_uniqueness:
            self.check_metadata_uniqueness(new_record)
        self.records.append(new_record)

    def check_metadata_compliance(self, record: Record) -> None:
        """Check if record metadata matches store schema."""
        if not self.schema.validate(record.metadata):
            raise TypeError(
                "The record's metadata does not match the store's schema."
            )

    def check_metadata_uniqueness(self, new_record: Record) -> None:
        """Check if record metadata is unique in store."""
        matching_record = next((
            i for i in self.records
            if i.metadata == new_record.metadata
        ), None)
        if matching_record is not None:
            raise ValueError(
                "The record's metadata already exists in the store."
            )