"""Unpack the bundled snapshot into disposable /tmp storage, once per instance."""

import fcntl
import gzip
import hashlib
from pathlib import Path
import shutil
import tempfile


def materialize(source, cache_dir=None):
    source = Path(source).resolve()
    if source.suffix != ".gz":
        return source
    cache = Path(cache_dir or tempfile.gettempdir())
    signature = hashlib.sha256(
        f"{source}:{source.stat().st_mtime_ns}:{source.stat().st_size}".encode()
    ).hexdigest()[:20]
    output = cache / f"asi-search-{signature}.sqlite"
    # Threads and worker processes share /tmp; avoid duplicate 419 MiB unpacking.
    with (cache / "asi-snapshot.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not output.exists():
            temporary = output.with_suffix(".tmp")
            try:
                with gzip.open(source, "rb") as src, temporary.open("wb") as dst:
                    shutil.copyfileobj(src, dst, length=1024 * 1024)
                temporary.replace(output)
            finally:
                temporary.unlink(missing_ok=True)
        return output
