#!/usr/bin/env python3
"""Download checksum-pinned tools; mathematical reference data is optional."""

import argparse
import hashlib
from pathlib import Path
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
DEPS = ROOT / "deps"


def download(url, path, digest, algorithm="sha256"):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        temporary = path.with_suffix(path.suffix + ".part")
        urllib.request.urlretrieve(url, temporary)
        if hashlib.new(algorithm, temporary.read_bytes()).hexdigest() != digest:
            temporary.unlink()
            raise RuntimeError(f"Checksum mismatch: {path.name}")
        temporary.replace(path)
    if hashlib.new(algorithm, path.read_bytes()).hexdigest() != digest:
        raise RuntimeError(f"Checksum mismatch: {path.name}")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--audit",
        action="store_true",
        help="also download nauty source for independent audits",
    )
    parser.add_argument(
        "--catalogue",
        action="store_true",
        help="also download the optional Zenodo reference catalogue",
    )
    args = parser.parse_args()
    archive = download(
        "https://github.com/meelgroup/ganak/releases/download/release/v2.6.4/ganak-v2.6.4-linux-amd64.tar.gz",
        DEPS / "ganak.tar.gz",
        "2d5f731e7529e55c021b4966068bd3f0c22ed337949a2c7b496c45ec44ae6137",
    )
    with tarfile.open(archive) as bundle:
        members = [
            m
            for m in bundle.getmembers()
            if m.isfile() and Path(m.name).name == "ganak"
        ]
        if len(members) != 1:
            raise RuntimeError("Unexpected Ganak archive layout")
        executable = bundle.extractfile(members[0]).read()
    if (
        hashlib.sha256(executable).hexdigest()
        != "c43a7d7c6d1e2ba438ee72541ceb15bc81b414bff5aa22038a9f6baa9f82bb61"
    ):
        raise RuntimeError("Ganak executable checksum mismatch")
    (DEPS / "ganak").write_bytes(executable)
    (DEPS / "ganak").chmod(0o755)
    print("Ganak v2.6.4 ready (Linux x86-64).")

    if args.audit:
        archive = download(
            "https://users.cecs.anu.edu.au/~bdm/nauty/nauty2_9_3.tar.gz",
            DEPS / "nauty2_9_3.tar.gz",
            "9fc4edae04f88a0f5883985be3b39cf7f898fd6cc96e96b9ee25452743cc1b5b",
        )
        if not (DEPS / "nauty2_9_3/configure").exists():
            with tarfile.open(archive) as bundle:
                for member in bundle.getmembers():
                    if (
                        not (DEPS / member.name)
                        .resolve()
                        .is_relative_to(DEPS.resolve())
                        or member.issym()
                        or member.islnk()
                    ):
                        raise RuntimeError("Unexpected nauty archive member")
                bundle.extractall(DEPS)
        print("Nauty 2.9.3 source ready; run make audit.")

    if args.catalogue:
        download(
            "https://zenodo.org/records/6825419/files/matroids09_rankLine?download=1",
            ROOT / "data/matroids09_rankLine",
            "66777481824f5426a1469bafde130c82",
            "md5",
        )
        print(
            "Reference catalogue downloaded and checksum verified; not used by the counter."
        )


if __name__ == "__main__":
    main()
