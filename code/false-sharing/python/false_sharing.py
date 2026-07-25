"""False sharing from Python, under the GIL and without it.

Run the same experiment on a GIL build and on a free-threaded build:

    uv run --python 3.14  python false_sharing.py
    uv run --python 3.14t python false_sharing.py

Under the GIL only one thread executes bytecode at a time, so the threads never write the shared cache line
concurrently and false sharing cannot happen. On a free-threaded build they do run at once, and it can.

The accumulators live in an ``array('q')`` so the slots are genuinely adjacent 8 byte integers in one
allocation. A Python ``list`` would hold pointers to boxed ints scattered across the heap, which would measure
something else entirely.
"""

import os
import sys
import sysconfig
import threading
import time
from array import array

ITERS = 2_000_000
THREADS = 8
STRIDE_PACKED = 1  # 8 bytes apart: eight counters share one 64 byte cache line
STRIDE_PADDED = 8  # 64 bytes apart: one counter per cache line

# One logical CPU per physical P-core on a 12900K. CPUs 0 and 1 are two hyperthreads of one core.
PHYSICAL_CORES = [i * 2 for i in range(THREADS)]


def worker(acc, slot, iters, cpu):
    os.sched_setaffinity(0, {cpu})
    for _ in range(iters):
        acc[slot] += 1


def worker_local(acc, slot, iters, cpu):
    os.sched_setaffinity(0, {cpu})
    local = 0
    for _ in range(iters):
        local += 1
    acc[slot] = local


def run(kind, threads):
    if kind == "local":
        acc = array("q", [0] * (threads * STRIDE_PADDED))
        stride, target = STRIDE_PADDED, worker_local
    elif kind == "padded":
        acc = array("q", [0] * (threads * STRIDE_PADDED))
        stride, target = STRIDE_PADDED, worker
    elif kind == "shared":
        acc = array("q", [0] * threads)
        stride, target = STRIDE_PACKED, worker
    else:
        raise SystemExit(f"unknown kind {kind!r}")

    ts = [
        threading.Thread(target=target, args=(acc, i * stride, ITERS, PHYSICAL_CORES[i]))
        for i in range(threads)
    ]
    start = time.perf_counter()
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    elapsed = time.perf_counter() - start

    total = sum(acc)
    assert total == ITERS * threads, f"{kind}: got {total}, want {ITERS * threads}"
    return elapsed


def main():
    free_threaded = bool(sysconfig.get_config_var("Py_GIL_DISABLED"))
    gil_on = getattr(sys, "_is_gil_enabled", lambda: True)()
    print(f"python {sys.version.split()[0]}  free-threaded build={free_threaded}  gil_enabled={gil_on}")
    print(f"{THREADS} threads, {ITERS:,} increments each, pinned to CPUs {PHYSICAL_CORES}")
    print()
    print(f"{'variant':<10}{'wall (s)':>10}{'ns per increment':>20}")

    results = {}
    for kind in ("shared", "padded", "local"):
        # Best of three: we want the floor, not the average, to keep scheduler noise out.
        best = min(run(kind, THREADS) for _ in range(3))
        results[kind] = best
        per = best * 1e9 / (ITERS * THREADS)
        print(f"{kind:<10}{best:>10.3f}{per:>20.2f}")

    print()
    print(f"shared / padded = {results['shared'] / results['padded']:.2f}x")
    print(f"shared / local  = {results['shared'] / results['local']:.2f}x")


if __name__ == "__main__":
    main()
