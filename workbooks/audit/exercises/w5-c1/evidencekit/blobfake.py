"""A local stand-in for azure.storage.blob.ContainerClient (no Azure account, no network). Complete.

Only the calls ControlPilot uses are implemented, with the same names and shapes:
  container.list_blobs(name_starts_with=None) -> iterator of BlobProperties (.name, .size, .etag)
  container.download_blob(name).readall()     -> bytes
Missing blobs raise ResourceNotFoundError, like azure.core.exceptions.ResourceNotFoundError.
Blobs are files under a root folder; the blob name is the relative path with forward slashes.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


class ResourceNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class BlobProperties:
    name: str
    size: int
    etag: str


class StorageStreamDownloader:
    def __init__(self, data: bytes):
        self._data = data

    def readall(self) -> bytes:
        return self._data


class FakeContainerClient:
    def __init__(self, root: str | Path, container_name: str = "evidence"):
        self.root = Path(root)
        self.container_name = container_name
        self.downloads: list[str] = []

    def list_blobs(self, name_starts_with: str | None = None) -> Iterator[BlobProperties]:
        for p in sorted(self.root.rglob("*")):
            if not p.is_file():
                continue
            name = p.relative_to(self.root).as_posix()
            if name_starts_with and not name.startswith(name_starts_with):
                continue
            data = p.read_bytes()
            yield BlobProperties(name=name, size=len(data), etag='"0x' + hashlib.sha1(data).hexdigest()[:16].upper() + '"')

    def download_blob(self, blob: str) -> StorageStreamDownloader:
        p = self.root / blob
        if not p.is_file():
            raise ResourceNotFoundError(f"The specified blob does not exist. Blob: {blob}")
        self.downloads.append(blob)
        return StorageStreamDownloader(p.read_bytes())
