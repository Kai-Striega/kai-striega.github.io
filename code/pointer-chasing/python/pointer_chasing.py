"""The Python half of the pointer chasing post.

Everything here is a control. Each pair of measurements holds the objects, the object count, the bytecode and
the arithmetic fixed, and varies exactly one thing, so that whatever moves can only be the memory.

Run it on as many interpreters as you have:

    uv run --no-project --python 3.12  --with numpy python pointer_chasing.py
    uv run --no-project --python 3.14  --with numpy python pointer_chasing.py
    uv run --no-project --python 3.14t --with numpy python pointer_chasing.py
"""

import array
import random
import sys
import time
from collections import Counter

try:
    import numpy as np
except ImportError:
    np = None

N = int(sys.argv[1]) if len(sys.argv) > 1 else 2_000_000

# Comfortably above the small integer cache, so every element is its own heap object.
BASE = 1 << 40


def best(fn, repeats=3):
    """Fastest of several runs, in milliseconds. The fastest run is the one with the least interference."""
    return min(_timed(fn) for _ in range(repeats)) * 1e3


def _timed(fn):
    start = time.perf_counter()
    fn()
    return time.perf_counter() - start


def count_loop(xs):
    """A loop that never looks at the values.

    It still touches every object, because the interpreter has to adjust each one's reference count on the
    way past. That write is the whole cost being measured.
    """
    total = 0
    for _ in xs:
        total += 1
    return total


def report_layout(values):
    """Where the integer objects actually live."""
    ids = sorted(id(v) for v in values)
    strides = Counter(b - a for a, b in zip(ids, ids[1:]))
    stride, _ = strides.most_common(1)[0]
    span = (ids[-1] - ids[0]) / 1e6
    print(f"  int object          {sys.getsizeof(values[0])} bytes")
    print(f"  most common stride  {stride} bytes")
    print(f"  address span        {span:.0f} MB for {len(values):,} objects")
    print(f"  pointer array       {sys.getsizeof(values) / 1e6:.0f} MB")


def main():
    print(f"{sys.version.split()[0]}  free-threaded={not getattr(sys, '_is_gil_enabled', lambda: True)()}")
    print(f"n = {N:,}\n")

    ordered = [BASE + i for i in range(N)]
    shuffled = list(ordered)
    random.shuffle(shuffled)

    print("Where the objects live")
    report_layout(ordered)

    # The control. Same objects, same list length, same bytecode. Only the order of the pointers differs.
    print("\nThe same objects, in a different order")
    loop_ordered = best(lambda: count_loop(ordered))
    loop_shuffled = best(lambda: count_loop(shuffled))
    sum_ordered = best(lambda: sum(ordered))
    sum_shuffled = best(lambda: sum(shuffled))
    print(f"  for loop, ordered   {loop_ordered:8.1f} ms")
    print(f"  for loop, shuffled  {loop_shuffled:8.1f} ms   {loop_shuffled / loop_ordered:.1f}x")
    print(f"  sum(), ordered      {sum_ordered:8.1f} ms")
    print(f"  sum(), shuffled     {sum_shuffled:8.1f} ms   {sum_shuffled / sum_ordered:.1f}x")

    # The ratio grows as the interpreter does less per element, which is how you know the interpreter is not
    # what is being measured.

    # And the trap. Below 257 every slot points at the same preallocated singleton, so there is nothing
    # scattered to find and shuffling changes nothing at all.
    print("\nThe same experiment with small integers")
    small = [i % 200 for i in range(N)]
    small_shuffled = list(small)
    random.shuffle(small_shuffled)
    a = best(lambda: count_loop(small))
    b = best(lambda: count_loop(small_shuffled))
    print(f"  for loop, ordered   {a:8.1f} ms")
    print(f"  for loop, shuffled  {b:8.1f} ms   {b / a:.1f}x")
    print(f"  distinct objects    {len({id(v) for v in small}):,} for {N:,} slots")

    # The ladder. Compact storage does not pay for itself unless whatever consumes it can do so without
    # building an object per element on the way out.
    print("\nThe ladder")
    print(f"  sum() list ordered  {sum_ordered:8.2f} ms")
    print(f"  sum() list shuffled {sum_shuffled:8.2f} ms")
    aq = array.array("q", [BASE + i for i in range(N)])
    print(f"  sum() array('q')    {best(lambda: sum(aq)):8.2f} ms")
    if np is None:
        print("  numpy not installed, skipping the last two rows")
        return
    npa = np.arange(BASE, BASE + N, dtype=np.int64)
    # sum() over an ndarray boxes a np.int64 per element and is punishingly slow, so it is measured over a
    # slice and scaled rather than run to completion.
    slice_n = min(N, 200_000)
    scaled = best(lambda: sum(npa[:slice_n]), repeats=1) * N / slice_n
    print(f"  sum() ndarray       {scaled:8.2f} ms   (measured over {slice_n:,} and scaled)")
    print(f"  npa.sum()           {best(lambda: npa.sum(), repeats=5):8.2f} ms")


if __name__ == "__main__":
    main()
