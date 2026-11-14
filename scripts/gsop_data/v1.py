"""Read-only access to the v1 results zip. Members are verified against the zip's own FILES.sha256."""
import io
import json
import zipfile

import pyarrow.parquet as pq
import yaml

from .fmt import sha256_bytes

ROOT = "gsop_v1/"


class V1:
    def __init__(self, zip_path):
        self.zip_path = zip_path
        self.z = zipfile.ZipFile(zip_path)
        listed = self.z.read(ROOT + "FILES.sha256").decode("utf-8").splitlines()
        self.sha = {}
        for line in listed:
            h, p = line.split("  ", 1)
            self.sha[p.strip()] = h
        self._cache = {}

    def verify_all(self):
        """Hash every member and compare with FILES.sha256. Returns (n_checked, problems)."""
        problems = []
        names = sorted(n[len(ROOT):] for n in self.z.namelist() if not n.endswith("/") and n != ROOT + "FILES.sha256")
        for p in names:
            if p not in self.sha:
                problems.append(f"unlisted: {p}")
                continue
            if sha256_bytes(self.z.read(ROOT + p)) != self.sha[p]:
                problems.append(f"mismatch: {p}")
        for p in sorted(self.sha):
            if p not in names:
                problems.append(f"missing: {p}")
        return len(names), problems

    def bytes(self, path):
        if path not in self.sha:
            raise KeyError(f"not in FILES.sha256: {path}")
        return self.z.read(ROOT + path)

    def json(self, path):
        return json.loads(self.bytes(path).decode("utf-8"))

    def yaml(self, path):
        return yaml.safe_load(self.bytes(path))

    def text(self, path):
        return self.bytes(path).decode("utf-8")

    def table(self, path, columns=None):
        key = (path, tuple(columns) if columns else None)
        if key not in self._cache:
            self._cache[key] = pq.read_table(io.BytesIO(self.bytes(path)), columns=columns)
        return self._cache[key]

    def src(self, path):
        """Source reference for meta.sources and claims."""
        return {"source_file": ROOT + path, "sha256": self.sha[path]}
