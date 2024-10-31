#!/usr/bin/env python3
import argparse
import subprocess
import sys


def run_command(command):
    process = subprocess.run(command, shell=True, check=True)
    return process.returncode


def main():
    parser = argparse.ArgumentParser(description="Publish package to PyPI or TestPyPI")
    parser.add_argument("version", help="Version to publish (e.g., 0.2.0)")
    parser.add_argument(
        "--production",
        "-p",
        action="store_true",
        help="Publish to PyPI instead of TestPyPI",
    )
    args = parser.parse_args()

    version = args.version
    if not version.startswith("v"):
        version = f"v{version}"

    # Default repository is TestPyPI
    twine_command = "twine upload --repository testpypi dist/*"
    if args.production:
        twine_command = "twine upload dist/*"

    commands = [
        f"git tag {version}",
        f"git push origin {version}",
        "rm -rf dist/ build/ *.egg-info",
        "python -m build",
        twine_command,
    ]

    for command in commands:
        print(f"Executing: {command}")
        try:
            run_command(command)
        except subprocess.CalledProcessError as e:
            print(f"Error executing command: {command}")
            print(f"Error: {e}")
            sys.exit(1)

    repo = "PyPI" if args.production else "TestPyPI"
    print(f"Successfully published version {version} to {repo}")


if __name__ == "__main__":
    main()
