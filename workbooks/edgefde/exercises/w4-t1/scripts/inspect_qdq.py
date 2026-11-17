"""Print every QuantizeLinear in an ONNX model with its scale and zero point (do not edit).

    python scripts/inspect_qdq.py build/pump-anomaly-int8.onnx
"""

import sys

import onnx
from onnx import numpy_helper

m = onnx.load(sys.argv[1])
inits = {i.name: numpy_helper.to_array(i) for i in m.graph.initializer}
for n in m.graph.node:
    if n.op_type == "QuantizeLinear":
        scale, zp = inits.get(n.input[1]), inits.get(n.input[2])
        lo = (-128 - int(zp)) * float(scale) if scale is not None else None
        hi = (127 - int(zp)) * float(scale) if scale is not None else None
        print(f"{n.input[0]:40} scale={float(scale):.6g} zero_point={int(zp)} representable=[{lo:.4g}, {hi:.4g}]")
