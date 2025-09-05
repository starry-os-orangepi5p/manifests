#!/usr/bin/env python3
"""
Generate a pinned repo manifest (locked.xml) from an input manifest
by replacing each project's revision with the current local HEAD SHA.

Usage examples:
  # From manifests/ directory
  python3 scripts/gen_locked.py -i default.xml -o locked.xml
  python3 scripts/gen_locked.py -i local.xml   -o locked.xml

Options:
  -i/--input     Input manifest XML (default: default.xml)
  -o/--output    Output manifest XML (default: locked.xml)
  -w/--workspace Workspace root that contains projects (default: parent of manifests/)
  --allow-missing  Skip projects that are missing or not git repos (default: strict)
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import xml.etree.ElementTree as ET


def find_workspace_default() -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    # scripts/ -> manifests/ -> workspace root
    return os.path.abspath(os.path.join(here, os.pardir, os.pardir))


def run_git_rev_parse(repo_path: str) -> str:
    try:
        sha = (
            subprocess.check_output(
                ["git", "-C", repo_path, "rev-parse", "HEAD"], stderr=subprocess.STDOUT
            )
            .decode()
            .strip()
        )
        # basic sanity
        if len(sha) != 40:
            raise ValueError(f"unexpected SHA length for {repo_path}: {sha}")
        return sha
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"Failed to resolve HEAD for {repo_path}: {e.output.decode().strip()}"
        ) from e


def pretty_indent(elem: ET.Element, level: int = 0) -> None:
    # Minimal pretty printer for ElementTree
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        for child in elem:
            pretty_indent(child, level + 1)
        if not child.tail or not child.tail.strip():  # type: ignore[name-defined]
            child.tail = i  # type: ignore[name-defined]
    if level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i


def build_locked(input_xml: str, output_xml: str, workspace: str, allow_missing: bool) -> None:
    tree = ET.parse(input_xml)
    root_in = tree.getroot()

    # Output root
    root_out = ET.Element("manifest")

    # Preserve remotes and default if present
    for tag in ("remote", "default"):
        for node in root_in.findall(tag):
            root_out.append(node)

    # Iterate projects and pin SHAs
    errors: list[str] = []
    for proj in root_in.findall("project"):
        attrs = proj.attrib.copy()
        name = attrs.get("name") or attrs.get("path")
        path = attrs.get("path", name)
        if not path:
            errors.append("project without name/path attribute")
            continue

        repo_path = os.path.join(workspace, path)
        try:
            sha = run_git_rev_parse(repo_path)
        except Exception as e:  # noqa: BLE001 - want to report and possibly continue
            if allow_missing:
                print(f"warn: skipping {path}: {e}", file=sys.stderr)
                continue
            errors.append(f"{path}: {e}")
            continue

        # Construct pinned project element, preserving groups and other attrs except revision
        pinned_attrs = {k: v for k, v in attrs.items() if k != "revision"}
        pinned_attrs["revision"] = sha
        root_out.append(ET.Element("project", pinned_attrs))

    if errors and not allow_missing:
        raise SystemExit("Error(s) while pinning:\n- " + "\n- ".join(errors))

    pretty_indent(root_out)
    tree_out = ET.ElementTree(root_out)
    # Write with XML declaration
    ET.register_namespace("", "")  # keep tags clean
    with open(output_xml, "wb") as f:
        f.write(b"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        tree_out.write(f, encoding="utf-8")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-i", "--input", default="default.xml", help="input manifest XML")
    parser.add_argument("-o", "--output", default="locked.xml", help="output manifest XML")
    parser.add_argument(
        "-w",
        "--workspace",
        default=find_workspace_default(),
        help="workspace root containing the project directories",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="skip projects that are missing or not git repos",
    )
    args = parser.parse_args(argv)

    # Normalize paths relative to this script directory (manifests/)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    input_xml = args.input if os.path.isabs(args.input) else os.path.join(base_dir, args.input)
    output_xml = args.output if os.path.isabs(args.output) else os.path.join(base_dir, args.output)
    workspace = args.workspace

    build_locked(input_xml, output_xml, workspace, args.allow_missing)
    print(f"Wrote pinned manifest: {output_xml}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

