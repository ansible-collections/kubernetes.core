import os
import sys
from pathlib import PosixPath


def main():

    src = sys.argv[1]
    path = PosixPath(src) / PosixPath("tests/integration/targets/")

    def _is_disable(path):
        flags = ("unsupported", "disabled", "unstable", "hidden")
        aliases_path = path / PosixPath("aliases")
        return (aliases_path.exists() and any((d.startswith(flags) for d in aliases_path.read_text().split("\n"))))

    targets = [i.stem for i in path.glob("*") if i.is_dir() and not _is_disable(i)]
    with open(os.environ.get("GITHUB_OUTPUT"), "a", encoding="utf-8") as fw:
        fw.write(f"kubevirt_targets={targets}\n")


if __name__ == "__main__":
    main()
