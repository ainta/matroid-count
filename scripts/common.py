"""Shared CPU discovery and permutation centralizers."""

import collections
import math
import os
from pathlib import Path


def physical_cpus():
    """One allowed logical CPU per physical core, interleaved over sockets."""
    cores = {}
    for cpu in sorted(os.sched_getaffinity(0)):
        top = Path(f"/sys/devices/system/cpu/cpu{cpu}/topology")
        key = (
            int((top / "physical_package_id").read_text()),
            int((top / "core_id").read_text()),
        )
        cores.setdefault(key, cpu)
    return [
        cpu
        for key, cpu in sorted(cores.items(), key=lambda item: (item[0][1], item[0][0]))
    ]


def centralizer(partition):
    """z_lambda = product j**a_j * a_j! for an S_n cycle type."""
    return math.prod(
        size**count * math.factorial(count)
        for size, count in collections.Counter(partition).items()
    )
