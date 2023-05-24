#!/usr/bin/env python3

import os
from argparse import ArgumentParser
from pathlib import PosixPath
import logging
import re
from packaging import version


FORMAT = "[%(asctime)s] - %(message)s"
logging.basicConfig(format=FORMAT)
logger = logging.getLogger("compute_release_version")
logger.setLevel(logging.DEBUG)


def update_version(path, myfunc):
    out = []
    updated = False
    for d in path.read_text().split("\n"):
        upd = myfunc(d)
        if upd != d:
            updated = True
        out.append(upd)
    if updated:
        with open(path, "w") as fw:
            fw.write("\n".join(out))
    return updated


def main() -> None:
    """Update collection files with the new version number."""
    parser = ArgumentParser(
        description="Update the version in the following places\n\tThe version in galaxy.yml"
        "\n\tThe README's requirements.yml example"
        "\n\tThe VERSION in Makefile"
    )
    parser.add_argument(
        "--path",
        help="Path to the directory, default to the current directory",
        type=PosixPath,
        default=PosixPath("."),
    )

    args = parser.parse_args()
    release_version = os.environ.get("RELEASE_VERSION")
    logger.info(
        "Collection path: '%s' - Release version '%s'", args.path, release_version
    )

    # Update Makefile
    makefile_path = PosixPath(args.path / "Makefile")
    makefile_path.write_text(
        re.sub(
            r"VERSION = ([0-9]+\.[0-9]+\.[0-9]+)",
            r"VERSION = {0}".format(release_version),
            makefile_path.read_text(),
        )
    )

    # Update README.md
    readme_path = PosixPath(args.path / "README.md")
    readme_path.write_text(
        re.sub(
            r"( +)version\: ([0-9]+\.[0-9]+\.[0-9]+)",
            r"\1version: {0}".format(release_version),
            readme_path.read_text(),
        )
    )

    # update 'version_added' from modules/*.py files
    # why this ? sometimes we push a changes expecting it to be part of a major/minor/patch release
    # and we release instead major/minor/pach release different than the expecting one
    # e.g: 'version_added: 4.3.0' should be replaced by 'version_added: 4.2.9'
    version_obj = version.parse(release_version)
    for module in PosixPath(args.path / "plugins" / "modules").glob("*.py"):
        content = module.read_text()
        updated_content = []
        for line in content.split("\n"):
            m = re.match(
                r'(.*)version_added: (\'|"?)([0-9]+\.[0-9]+\.[0-9]+)(\'|"?)', line
            )
            if m and version_obj < version.parse(m.group(3)):
                updated_content.append(
                    re.sub(
                        r'(.*)version_added\: (\'|"?)([0-9]+\.[0-9]+\.[0-9]+)(\'|"?)',
                        r'\1version_added: "{0}"'.format(release_version),
                        line,
                    )
                )
            else:
                updated_content.append(line)
        if content != "\n".join(updated_content):
            logger.info("The following file will be updated => %s", module)
            module.write_text("\n".join(updated_content))


if __name__ == "__main__":
    main()
