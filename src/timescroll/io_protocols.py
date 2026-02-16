r"""
Protocols for file I/O operations.
"""

from __future__ import annotations

# Typing imports
from typing import Protocol, Iterable, Any

# Local imports
from .records import Record


__all__ = (
    "RecordReader",
    "RecordWriter",
)


class RecordReader(Protocol):
    """Protocol for reading records from files."""
    
    def read_records(
        self,
        file_name: str,
        converter: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Iterable[Record]:
        """
        Read records from a file.
        
        Args:
            file_name: Path to the file to read
            converter: Optional converter functions for data transformation
            **kwargs: Additional format-specific options
            
        Returns:
            Iterable of Record objects
        """
        ...


class RecordWriter(Protocol):
    """Protocol for writing records to files."""
    
    def write_records(
        self,
        records: Iterable[Record],
        file_name: str,
        **kwargs: Any,
    ) -> None:
        """
        Write records to a file.
        
        Args:
            records: Records to write
            file_name: Path to the output file
            **kwargs: Additional format-specific options
        """
        ...