"""Deliver the finished front page to the output directory.

The artwork is drawn by render.py. This script only copies entry.png
next to this file into the output location and checks the copy is
complete. Output: $MAKEFUN_OUTPUT_DIR/entry.png, or /output/entry.png.

Usage: python3 main.py
Exit code 0 means the output file exists and matches the source byte
for byte.
"""

import hashlib
import os
import shutil
import sys

SOURCE_NAME = "entry.png"
DEFAULT_OUTPUT_DIR = "/output"


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, SOURCE_NAME)
    if not os.path.isfile(source):
        print("missing source: " + source, file=sys.stderr)
        return 1

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or DEFAULT_OUTPUT_DIR
    destination = os.path.join(out_dir, SOURCE_NAME)
    try:
        os.makedirs(out_dir, exist_ok=True)
    except OSError as exc:
        print("cannot create output dir: " + str(exc), file=sys.stderr)
        return 1
    try:
        shutil.copyfile(source, destination)
    except OSError as exc:
        print("copy failed: " + str(exc), file=sys.stderr)
        return 1

    if os.path.getsize(source) != os.path.getsize(destination):
        print("size mismatch after copy", file=sys.stderr)
        return 1
    if sha256_of(source) != sha256_of(destination):
        print("checksum mismatch after copy", file=sys.stderr)
        return 1

    print("delivered %s (%d bytes, sha256 %s)"
          % (destination, os.path.getsize(destination),
             sha256_of(destination)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
