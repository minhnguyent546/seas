#!/usr/bin/env python3

import argparse
import importlib.util
import pathlib
import sys


def check_imports(args: argparse.Namespace) -> None:
    src_paths = [pathlib.Path(p) for p in args.src_path]
    py_files_globs = [src_path.rglob("*.py") for src_path in src_paths]
    for src_path, py_files_glob in zip(src_paths, py_files_globs):
        num_files = 0
        ignored_files = 0
        for py_file in py_files_glob:
            basename = py_file.name
            if basename == "models.py":
                # ignore models.py containing sqlalchemy models definitions
                ignored_files += 1
                continue
            print("Trying to import", py_file)
            module_name = py_file.with_suffix("").as_posix().replace("/", ".")
            spec = importlib.util.spec_from_file_location(
                name=module_name,
                location=py_file,
            )
            if spec is None:
                print(f"Failed to load {py_file}", file=sys.stderr)
                raise SystemExit(1)

            assert spec.loader is not None
            module = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(module)
                num_files += 1
            except Exception as e:
                print(f"Error importing {module_name}: {e}", file=sys.stderr)
                raise SystemExit(1)

        print(
            f"{src_path}: {num_files} imports checked successfully, ignored {ignored_files} files."
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check imports in Python files",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--src_path",
        type=str,
        nargs="+",
        help="Path to the source directory",
        default="src",
    )
    args = parser.parse_args()
    check_imports(args)


if __name__ == "__main__":
    main()
