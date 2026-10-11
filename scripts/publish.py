#!/usr/bin/env python3
"""Cross-platform build and publish helper for JiuZhang (九章).

Usage:
    python publish.py              # Build only
    python publish.py test         # Build + upload to TestPyPI
    python publish.py release      # Build + upload to PyPI
"""

import os
import re
import subprocess
import sys
from pathlib import Path


INIT_FILE = Path("jiuzhang/__init__.py")


def get_version():
    content = INIT_FILE.read_text()
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
    if not match:
        print("Error: Could not find __version__ in jiuzhang/__init__.py")
        sys.exit(1)
    return match.group(1)


def bump_version():
    current = get_version()
    parts = current.split(".")
    new_version = f"{parts[0]}.{parts[1]}.{int(parts[2]) + 1}"

    content = INIT_FILE.read_text()
    content = content.replace(
        f'__version__ = "{current}"',
        f'__version__ = "{new_version}"',
    )
    INIT_FILE.write_text(content)
    print(f"Version bumped: {current} -> {new_version}")
    return new_version


def clean():
    print("Cleaning old builds...")
    for path in ["dist", "build"]:
        if os.path.exists(path):
            subprocess.run(["rm", "-rf", path], check=True)
    for egg_info in Path(".").glob("*.egg-info"):
        subprocess.run(["rm", "-rf", str(egg_info)], check=True)


def install_tools():
    print("Installing build tools...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "build", "twine"],
        check=True,
    )


def build():
    print("Building package...")
    subprocess.run([sys.executable, "-m", "build"], check=True)
    print("Running twine check...")
    subprocess.run(["twine", "check", "dist/*"], check=True)


def upload(test=False):
    if test:
        print("Uploading to TestPyPI...")
        subprocess.run(
            ["twine", "upload", "--repository", "testpypi", "dist/*"],
            check=True,
        )
    else:
        print("Uploading to PyPI...")
        subprocess.run(["twine", "upload", "dist/*"], check=True)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "build"

    if mode not in ("build", "test", "release"):
        print(f"Unknown mode: {mode}")
        print("Usage: python publish.py [build|test|release]")
        sys.exit(1)

    print("=" * 50)
    print("  JiuZhang (九章) Build & Publish")
    print("=" * 50)

    bump_version()
    clean()
    install_tools()
    build()

    if mode == "test":
        upload(test=True)
    elif mode == "release":
        upload()

    version = get_version()
    print()
    print("=" * 50)
    print(f"  Done! Version: {version}")
    if mode == "build":
        print("  Run 'twine upload dist/*' to publish to PyPI")
    elif mode == "test":
        print("  Uploaded to TestPyPI")
    else:
        print("  Uploaded to PyPI")
        print(f"  pip install jiuzhang=={version}")
    print("=" * 50)


if __name__ == "__main__":
    main()
