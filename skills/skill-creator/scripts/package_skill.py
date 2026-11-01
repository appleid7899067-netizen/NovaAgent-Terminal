#!/usr/bin/env python3
"""Package one validated skill directory into a standalone .skill ZIP archive.

Usage:
    package_skill.py <source-directory> <output-file.skill>

The archive root contains SKILL.md and the skill's resource directories directly.
The script does not overwrite an existing output file.
"""

import argparse
import os
from pathlib import Path
import stat
import sys
import zipfile

from quick_validate import validate_skill


FILTERED_DIRECTORY_NAMES = {
    ".git",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "venv",
}
FILTERED_FILE_NAMES = {".DS_Store", ".coverage"}
FILTERED_FILE_SUFFIXES = {".pyc", ".pyo", ".swp", ".tmp"}


class PackageError(Exception):
    """Report an unsafe or invalid packaging request."""


def _is_filtered(relative_path, is_directory):
    """Return whether a known cache or temporary entry must stay out of the archive."""
    if is_directory:
        return relative_path.name in FILTERED_DIRECTORY_NAMES

    name = relative_path.name
    return (
        name in FILTERED_FILE_NAMES
        or name.endswith("~")
        or Path(name).suffix in FILTERED_FILE_SUFFIXES
    )


def _walk_error(error):
    raise PackageError(f"Cannot read source directory: {error}") from error


def _require_regular_source_tree(source_dir):
    """Reject links and special files before any source path is read or archived."""
    try:
        root_mode = source_dir.lstat().st_mode
    except OSError as error:
        raise PackageError(f"Cannot inspect source directory: {error}") from error

    if stat.S_ISLNK(root_mode):
        raise PackageError("Source directory cannot be a symbolic link")
    if not stat.S_ISDIR(root_mode):
        raise PackageError("Source path must be a directory")

    for directory, _directories, filenames in os.walk(source_dir, followlinks=False, onerror=_walk_error):
        directory_path = Path(directory)
        _directories[:] = [name for name in _directories if name not in FILTERED_DIRECTORY_NAMES]
        for name in filenames:
            if _is_filtered(Path(name), is_directory=False):
                continue
            entry = directory_path / name
            try:
                mode = entry.lstat().st_mode
            except OSError as error:
                raise PackageError(f"Cannot inspect source entry {entry}: {error}") from error
            if stat.S_ISLNK(mode):
                raise PackageError(f"Symbolic links are not allowed: {entry}")
            if not stat.S_ISREG(mode):
                raise PackageError(f"Only regular files are allowed: {entry}")

        for name in list(_directories):
            entry = directory_path / name
            try:
                mode = entry.lstat().st_mode
            except OSError as error:
                raise PackageError(f"Cannot inspect source entry {entry}: {error}") from error
            if stat.S_ISLNK(mode):
                raise PackageError(f"Symbolic links are not allowed: {entry}")
            if not stat.S_ISDIR(mode):
                raise PackageError(f"Only directories are allowed: {entry}")


def _collect_entries(source_dir):
    """Collect filtered archive entries in stable order without adding a root wrapper."""
    entries = []
    for directory, directories, filenames in os.walk(
        source_dir, topdown=True, followlinks=False, onerror=_walk_error
    ):
        directory_path = Path(directory)
        relative_directory = directory_path.relative_to(source_dir)

        directories[:] = sorted(
            name
            for name in directories
            if not _is_filtered(relative_directory / name, is_directory=True)
        )
        for name in directories:
            directory_entry = directory_path / name
            entries.append((directory_entry, directory_entry.relative_to(source_dir), True))

        for name in sorted(filenames):
            file_entry = directory_path / name
            relative_file = file_entry.relative_to(source_dir)
            if not _is_filtered(relative_file, is_directory=False):
                entries.append((file_entry, relative_file, False))

    return entries


def _validate_output_path(source_dir, output_file):
    """Return a safe, absent output path that cannot be archived into itself."""
    requested_output = output_file.expanduser()
    if os.path.lexists(requested_output):
        raise PackageError(f"Output file already exists: {requested_output}")

    output_file = requested_output.resolve(strict=False)
    if not (str(output_file).endswith(".skill") or str(output_file).endswith(".skill.zip")):
        raise PackageError("Output file must end in .skill or .skill.zip")

    parent = output_file.parent
    if not parent.is_dir():
        raise PackageError(f"Output directory does not exist: {parent}")
    if os.path.lexists(output_file):
        raise PackageError(f"Output file already exists: {output_file}")

    try:
        output_file.relative_to(source_dir)
    except ValueError:
        return output_file
    raise PackageError("Output file cannot be inside the source directory")


def _archive_mode(source_path, is_directory):
    """Keep executable bits and normalize other permissions so any user can read the skill."""
    if is_directory:
        return stat.S_IFDIR | 0o755
    executable = source_path.stat().st_mode & 0o111
    return stat.S_IFREG | (0o755 if executable else 0o644)


def _write_archive(entries, output_file):
    """Create output_file exclusively and remove it if packaging fails."""
    # Exclusive creation never replaces a file and, unlike hard links, works on FAT/exFAT and network volumes.
    try:
        archive = zipfile.ZipFile(output_file, mode="x", compression=zipfile.ZIP_DEFLATED)
    except FileExistsError as error:
        raise PackageError(f"Output file already exists: {output_file}") from error

    try:
        with archive:
            for source_path, relative_path, is_directory in entries:
                archive_name = relative_path.as_posix()
                if '\\' in archive_name or ':' in archive_name:
                    raise PackageError(f"Unsafe cross-platform archive name: {archive_name}")
                info = zipfile.ZipInfo.from_file(source_path, arcname=archive_name, strict_timestamps=False)
                info.external_attr = _archive_mode(source_path, is_directory) << 16 | (info.external_attr & 0xFFFF)
                if is_directory:
                    archive.writestr(info, b"")
                else:
                    info.compress_type = zipfile.ZIP_DEFLATED
                    archive.writestr(info, source_path.read_bytes())
    except BaseException:
        output_file.unlink(missing_ok=True)
        raise


def package_skill(source_directory, output_file):
    """Validate and package source_directory, returning the absolute output file path."""
    requested_source = Path(source_directory).expanduser()
    if requested_source.is_symlink():
        raise PackageError("Source directory cannot be a symbolic link")

    try:
        source_dir = requested_source.resolve(strict=True)
    except OSError as error:
        raise PackageError(f"Source directory does not exist: {requested_source}") from error

    _require_regular_source_tree(source_dir)
    output_file = _validate_output_path(source_dir, Path(output_file))

    valid, message = validate_skill(str(source_dir))
    if not valid:
        raise PackageError(f"Skill validation failed: {message}")

    entries = _collect_entries(source_dir)
    _write_archive(entries, output_file)
    return output_file


def main():
    parser = argparse.ArgumentParser(
        description="Validate and package a skill as a root-level .skill ZIP archive."
    )
    parser.add_argument("source_directory", type=Path, help="Skill directory to package")
    parser.add_argument("output_file", type=Path, help="New .skill or .skill.zip output file")
    args = parser.parse_args()

    try:
        output_file = package_skill(args.source_directory, args.output_file)
    except PackageError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"Error: Cannot create skill archive: {error}", file=sys.stderr)
        return 1

    print(f"Packaged skill: {output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
