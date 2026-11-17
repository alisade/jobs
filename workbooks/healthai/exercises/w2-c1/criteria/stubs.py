"""Generate (once) and import the protobuf/gRPC stubs from protos/criteria.proto into gen/."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "gen"


def ensure() -> None:
    if not (GEN / "criteria_pb2_grpc.py").exists():
        from grpc_tools import protoc

        GEN.mkdir(exist_ok=True)
        rc = protoc.main(["protoc", f"-I{ROOT / 'protos'}", f"--python_out={GEN}", f"--grpc_python_out={GEN}",
                          str(ROOT / "protos" / "criteria.proto")])
        if rc != 0:
            raise RuntimeError("protoc failed")
    if str(GEN) not in sys.path:
        sys.path.insert(0, str(GEN))


ensure()
import criteria_pb2 as pb2  # noqa: E402
import criteria_pb2_grpc as pb2_grpc  # noqa: E402

__all__ = ["pb2", "pb2_grpc"]
