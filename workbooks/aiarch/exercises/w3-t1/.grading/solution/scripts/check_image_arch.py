"""CI gate: fail unless the pushed image can run on AgentCore Runtime (linux/arm64).

Usage: python scripts/check_image_arch.py <manifest.json> [<config.json>]
Exit 0 when linux/arm64 is present, 1 when it is not, 2 on unreadable input.
"""
import json
import sys

INDEX_TYPES = {"application/vnd.oci.image.index.v1+json", "application/vnd.docker.distribution.manifest.list.v2+json"}


def _load(path):
    with open(path, encoding="utf8") as f:
        return json.load(f)


def platforms(manifest: dict, config: dict | None) -> list[str]:
    if manifest.get("mediaType") in INDEX_TYPES or "manifests" in manifest:
        out = []
        for m in manifest.get("manifests", []):
            p = m.get("platform") or {}
            if (m.get("annotations") or {}).get("vnd.docker.reference.type") == "attestation-manifest":
                continue
            if p.get("os") == "unknown":
                continue
            out.append(f"{p.get('os')}/{p.get('architecture')}" + (f"/{p['variant']}" if p.get("variant") else ""))
        return out
    if config is None:
        raise ValueError("single-platform manifest: pass the image config as the second argument")
    cfg = config.get("config", config) if "architecture" not in config else config
    return [f"{config.get('os') or cfg.get('os')}/{config.get('architecture') or cfg.get('architecture')}"]


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: check_image_arch.py <manifest.json> [<config.json>]")
        return 2
    try:
        manifest = _load(argv[0])
        config = _load(argv[1]) if len(argv) > 1 else None
        found = platforms(manifest, config)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(f"cannot read image metadata: {e}")
        return 2
    if any(p == "linux/arm64" or p.startswith("linux/arm64/") for p in found):
        print(f"ok: linux/arm64 present ({', '.join(found)})")
        return 0
    print(f"FAIL: AgentCore Runtime needs linux/arm64; image has {', '.join(found) or 'no platforms'}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
