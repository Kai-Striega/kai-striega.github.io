# pointer-chasing

The benchmark behind the blog post [Pointer
Chasing](https://kaistriega.com/blog/mechanical-sympathy/pointer-chasing/), part 4 of the Mechanical Sympathy
series.

Every variant sums the same values and asserts the same total. What differs is how the address of the next
value becomes known.

## The two things being separated

Scattered data is slow for two reasons that are usually mixed together:

1. **Locality.** Objects spread across the heap mean a cache miss per element instead of one per sixteen.
2. **Dependency.** If the next address comes *out of* the current load, the core cannot overlap the misses.
   Golden Cove tracks sixteen outstanding L1 misses; a pointer chain lets it use one.

`boxed-shuffled` and `list-chase` walk the identical heap objects in the identical order, so the only thing
between them is the second point. `gather-independent` and `gather-dependent` do the same again over one flat
allocation, which removes the allocator entirely and guarantees an identical set of cache lines.

| variant | structure |
|---|---|
| `contiguous` | `Vec<u64>`, front to back |
| `boxed-ordered` | one heap node per element, walked in allocation order |
| `boxed-shuffled` | the same nodes, walked through a shuffled array of pointers |
| `list-chase` | the same nodes, in the same order, followed through `next` |
| `gather-independent` | flat array, indices streamed from a second array |
| `gather-dependent` | flat array, each index read from the previous slot |

## Running it

```shell
$ cargo test --release          # every variant agrees, and the chase is one full cycle
$ ./collect.sh                  # the table published in the post
$ ./sweep.sh                    # the working set sweep behind the chart
$ cd python && uv run --no-project --python 3.12 --with numpy python pointer_chasing.py
```

`collect.sh` needs counters:

```shell
$ sudo sysctl -w kernel.perf_event_paranoid=1
```

## Subtracting the setup

`perf stat` counts the whole process, and allocating four million nodes costs far more than walking them
once. So every variant is measured twice, once with its real pass count and once with `passes = 0`, and the
difference is the traversal. Without that subtraction the fast variants are almost entirely allocator, and
the counters describe `malloc` rather than the benchmark.

Events are collected in two small groups so that nothing is multiplexed. A scaled counter is not worth
publishing.

## Traps

- **`black_box` the total.** Otherwise LLVM notices the sum is unused and deletes the loop.
- **A permutation read as a mapping is not one cycle.** It breaks into several short ones, and a chase built
  from it silently traverses a fraction of the data. Reading the permutation as a *visit order* — link each
  element to the one after it, wrap the last to the first — always gives a single cycle of length `n`. There
  is a test asserting exactly that.
- **Allocate the nodes in order, then shuffle the pointers.** Shuffling first would change the object set and
  destroy the control between `boxed-ordered` and `boxed-shuffled`.
- **Pin the process.** `taskset -c 2`, as the scripts do. The i9-12900K is a hybrid part, and being migrated
  onto an E-core mid-run moves the numbers a long way.

## Notes on the hardware

Measured on an i9-12900K (Alder Lake, 12th generation), 30 MiB L3. Alder Lake has **no data-dependent
prefetcher**, so a pointer chase here is the clean, fully serialised case. Apple silicon and Intel's 13th
generation do have one, and will speculatively follow pointers they find in a cache line — expect a smaller
ratio there.

Perf events on this chip need the hybrid prefix: `cpu_core/l1d_pend_miss.pending/`, not
`l1d_pend_miss.pending`.
