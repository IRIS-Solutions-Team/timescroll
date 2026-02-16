r"""
CSV file I/O implementations.
"""

from __future__ import annotations

# Standard library imports
import csv
import functools as ft

# Typing imports
from typing import Iterable, Any, Callable

# Local imports
from .records import Record
from .schemas import Schema
from . import records as _records


__all__ = (
    "CsvReader",
    "CsvWriter",
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


class CsvReader:
    """CSV file reader for timescroll records."""
    
    def __init__(self, schema: Schema) -> None:
        """
        Initialize CSV reader.
        
        Args:
            schema: Schema defining the metadata structure
        """
        self.schema = schema
        self.metadata_factory = _records.build_metadata_class(schema)
        self.data_fields = Record.data_fields
        self.metadata_fields = schema.fields
        self.all_fields = self.metadata_fields + self.data_fields
    
    def read_records(
        self,
        file_name: str,
        converter: dict[str, Any] | None = _DEFAULT_CONVERTER_FROM_CSV,
        skip_when: Callable = lambda x: x[0].strip() == "",
        check_header_compliance: bool = True,
        **kwargs: Any,
    ) -> Iterable[Record]:
        """Read records from CSV file."""
        header_fields = self._read_header_fields_from_csv_file(file_name)
        if check_header_compliance:
            self._check_header_compliance(header_fields)
            
        with _read_file(file_name) as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if skip_when and skip_when(row):
                    continue
                record = self._build_record_from_compliant_tuple(row)
                if converter:
                    record.apply_converter(converter)
                yield record
    
    def _build_record_from_compliant_tuple(
        self,
        input_tuple: Iterable[Any],
    ) -> Record:
        """Build record from tuple matching the expected field order."""
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
    
    def _read_header_fields_from_csv_file(self, file_name: str) -> tuple[str, ...]:
        """Read header fields from CSV file."""
        with _read_file(file_name) as f:
            reader = csv.reader(f)
            header_fields = next(reader)
            if "" in header_fields:
                first_empty = header_fields.index("")
                header_fields = header_fields[:first_empty]
        return tuple(header_fields)
    
    def _check_header_compliance(self, header_fields: Iterable[str]) -> None:
        """Check if header fields match expected schema."""
        if tuple(header_fields) != self.all_fields:
            raise ValueError(
                "The CSV file header does not match the Store fields."
            )


class CsvWriter:
    """CSV file writer for timescroll records."""
    
    def __init__(self, schema: Schema) -> None:
        """
        Initialize CSV writer.
        
        Args:
            schema: Schema defining the metadata structure
        """
        self.schema = schema
        self.data_fields = Record.data_fields
        self.metadata_fields = schema.fields
        self.all_fields = self.metadata_fields + self.data_fields
    
    def write_records(
        self,
        records: Iterable[Record],
        file_name: str,
        **kwargs: Any,
    ) -> None:
        """Write records to CSV file."""
        records_list = list(records)  # Convert to list to avoid exhausting iterator
        
        with _write_file(file_name) as f:
            writer = csv.writer(f)
            writer.writerow(self.all_fields)
            for record in records_list:
                writer.writerow(record.to_tuple())