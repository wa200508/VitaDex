"""Bounded, atomic local document transfer; no storage or network permissions."""

import os
from pathlib import Path
import tempfile

from backup import MAX_BYTES


def copy_document(source, destination):
    """Copy a binary stream without exposing partial imports or replacing on failure."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("wb", dir=destination.parent, delete=False) as output:
            temporary = Path(output.name)
            count = 0
            while True:
                chunk = source.read(min(65536, MAX_BYTES + 1 - count))
                if not chunk:
                    break
                count += len(chunk)
                if count > MAX_BYTES:
                    raise ValueError("Backup exceeds the 32 MiB limit.")
                output.write(chunk)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, destination)
        return destination
    finally:
        if temporary and temporary.exists():
            temporary.unlink()
