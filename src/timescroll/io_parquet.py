r"""
Parquet file I/O implementations.
"""

from __future__ import annotations

# Third-party imports
import pyarrow as pa
import pyarrow.parquet as pq

# Typing imports
from typing import Iterable, Any

# Local imports
from .records import Record
from .schemas import Schema
from . import records as _records


__all__ = (
    "ParquetReader",
    "ParquetWriter",
)


class ParquetReader:
    """Parquet file reader for timescroll records."""

    def __init__(self, schema: Schema) -> None:
        """
        Initialize Parquet reader.

        Args:
            schema: Schema defining the metadata structure
        """
        self.schema = schema
        self.metadata_factory = _records.build_metadata_class(schema)
        self.data_fields = Record.data_fields
        self.metadata_fields = schema.fields

    def read_records(
        self,
        file_name: str,
        converter: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Iterable[Record]:
        """Read records from Parquet file."""
        # Read the parquet file
        table = pq.read_table(file_name)

        # Convert to Python dictionaries for processing
        data = table.to_pylist()

        # Process each row
        for row_dict in data:
            # Extract metadata fields
            metadata_values = [row_dict[field] for field in self.metadata_fields]

            # Extract data fields
            start_period = row_dict["start_period"]
            observations = row_dict["observations"]

            # Create record
            record = self._build_record_from_compliant_tuple(
                (*metadata_values, start_period, *observations)
            )

            # Apply converter if provided
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


class ParquetWriter:
    """Parquet file writer for timescroll records."""

    def __init__(self, schema: Schema) -> None:
        """
        Initialize Parquet writer.

        Args:
            schema: Schema defining the metadata structure
        """
        self.schema = schema
        self.metadata_fields = schema.fields

    def write_records(
        self,
        records: Iterable[Record],
        file_name: str,
        compression: str = "snappy",
        **kwargs: Any,
    ) -> None:
        """Write records to Parquet file."""
        records_list = list(records)  # Convert to list to avoid exhausting iterator

        if not records_list:
            raise ValueError("No records to write")

        # Prepare data for PyArrow table
        data_dict = {}

        # Add metadata fields
        for field in self.metadata_fields:
            data_dict[field] = [getattr(record.metadata, field) for record in records_list]

        # Add data fields
        data_dict["start_period"] = [record.start_period for record in records_list]
        data_dict["observations"] = [list(record.observations) for record in records_list]

        # Create PyArrow table with explicit schema
        schema_fields = []

        # Add metadata field schemas (infer types from first record)
        first_record = records_list[0]
        for field in self.metadata_fields:
            value = getattr(first_record.metadata, field)
            if isinstance(value, str):
                schema_fields.append(pa.field(field, pa.string()))
            elif isinstance(value, bool):
                schema_fields.append(pa.field(field, pa.bool_()))
            elif isinstance(value, int):
                schema_fields.append(pa.field(field, pa.int64()))
            elif isinstance(value, float):
                schema_fields.append(pa.field(field, pa.float64()))
            else:
                schema_fields.append(pa.field(field, pa.string()))  # Default to string

        # Add data field schemas
        schema_fields.append(pa.field("start_period", pa.string()))
        schema_fields.append(pa.field("observations", pa.list_(pa.float64())))

        schema = pa.schema(schema_fields)
        table = pa.Table.from_pydict(data_dict, schema=schema)

        # Write to parquet file
        pq.write_table(table, file_name, compression=compression)

