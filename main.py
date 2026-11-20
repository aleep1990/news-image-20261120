#!/usr/bin/env python3
"""Entrypoint for the news-image-20261120 entry.

Reads the bundled ``entry.png`` sitting next to this file, checks that it is
a real PNG of exactly 1024x1024 pixels and at most 1 MiB, and copies it to
``/output/entry.png``. Pure standard library, no network, no clock, no
randomness: two runs produce byte-identical output.
"""

import hashlib
import shutil
import struct
import sys
from pathlib import Path

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024
MAX_BYTES = 1_048_576
OUTPUT_PATH = Path("/output/entry.png")


def read_png_size(data: bytes) -> tuple[int, int]:
    """Return (width, height) from a PNG's IHDR chunk."""
    if len(data) < 33 or data[:8] != PNG_MAGIC:
        raise ValueError("not a PNG file (bad magic bytes)")
    chunk_length, chunk_type = struct.unpack(">I4s", data[8:16])
    if chunk_type != b"IHDR" or chunk_length != 13:
        raise ValueError("not a PNG file (first chunk is not IHDR)")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def main() -> int:
    source = Path(__file__).resolve().parent / "entry.png"
    if not source.is_file():
        print(f"error: bundled image not found: {source}", file=sys.stderr)
        return 1

    data = source.read_bytes()
    if len(data) > MAX_BYTES:
        print(
            f"error: entry.png is {len(data)} bytes, over the 1 MiB limit",
            file=sys.stderr,
        )
        return 1

    width, height = read_png_size(data)
    if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        print(
            f"error: entry.png is {width}x{height}, expected "
            f"{EXPECTED_WIDTH}x{EXPECTED_HEIGHT}",
            file=sys.stderr,
        )
        return 1

    digest = hashlib.sha256(data).hexdigest()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, OUTPUT_PATH)
    # Post-copy integrity check: the written file must be byte-identical to
    # the validated source; a partial or corrupted copy is a hard error.
    written = OUTPUT_PATH.read_bytes()
    if hashlib.sha256(written).hexdigest() != digest:
        print(
            f"error: {OUTPUT_PATH} failed its integrity check "
            f"(sha256 mismatch after copy)",
            file=sys.stderr,
        )
        return 1
    print(f"wrote {OUTPUT_PATH} ({len(data)} bytes, sha256 {digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
