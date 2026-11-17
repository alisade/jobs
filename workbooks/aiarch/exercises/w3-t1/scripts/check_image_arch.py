"""CI gate: fail unless the pushed image can run on AgentCore Runtime (linux/arm64).

Usage: python scripts/check_image_arch.py <manifest.json> [<config.json>]
manifest.json is `docker buildx imagetools inspect --raw <image>` output: either an OCI image
index / Docker manifest list (with "manifests"), or a single image manifest. For a single
manifest the platform is in the image config blob, passed as the optional second file
(`docker buildx imagetools inspect --format '{{json .Image}}'` or the config blob itself).

Exit 0 when linux/arm64 is present, 1 when it is not (print why), 2 on unreadable input.
TODO: implement main().
"""
import sys


def main(argv: list[str]) -> int:
    raise NotImplementedError("TODO")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
