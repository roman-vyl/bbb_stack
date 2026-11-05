#!/usr/bin/env python3
"""Authorize the existing Compose ABI; never deploy or start another ABI."""
import argparse
import os
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["authorize", "retry", "status"])
    parser.add_argument("encrypted", nargs="?")
    parser.add_argument("--abi-repo", default=os.environ.get("ABI_REPO_PATH", "../abi_executor_bot"))
    args = parser.parse_args()
    if (args.operation == "authorize") != (args.encrypted is not None):
        parser.error("authorize requires an age file; retry/status do not accept one")
    root = Path(__file__).resolve().parents[1]
    client = (Path(args.abi_repo) if Path(args.abi_repo).is_absolute() else root / args.abi_repo) / "scripts/abi-authorize.py"
    if not client.is_file():
        parser.error("ABI checkout with the reviewed authorization client is required")
    try:
        result = subprocess.run(["docker", "compose", "-f", "docker-compose.yml", "-f", "docker-compose.demo.yml",
                                 "-f", "docker-compose.deploy.yml", "--env-file", "deploy/images.env", "ps", "-q", "abi"],
                                cwd=root, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True, timeout=15)
        containers = result.stdout.decode("ascii").split()
        if len(containers) != 1 or not all(ch in "0123456789abcdef" for ch in containers[0]):
            raise ValueError()
        cmd = [sys.executable, str(client), containers[0], args.operation]
        if args.encrypted is not None:
            cmd.append(str(Path(args.encrypted).resolve()))
        return subprocess.call(cmd)
    except (Exception, KeyboardInterrupt):
        print("ABI authorization unavailable; no deploy or restart was performed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
