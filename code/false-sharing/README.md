# false-sharing

The benchmark behind the blog post [False
Sharing](https://kaistriega.com/blog/mechanical-sympathy/false-sharing/), part 3 of the Mechanical Sympathy
series.

Every variant computes the same total over the same readings with the same number of threads. The only thing
that differs is *where in memory* each thread keeps its running total, and therefore whether two threads end up
fighting over one 64 byte cache line.

## Why the counters are atomics

The obvious way to write this hands each thread a ``&mut u64`` out of a shared slice. Don't: LLVM keeps the
accumulator in a register and writes it back once at the end, which quietly turns every variant into the fast
one and leaves you measuring nothing. A ``Vec<AtomicU64>`` cannot be register-promoted, and happens to be what
people actually write for per-thread statistics.

## Pinning is mandatory

Measured on an i9-12900K. Its P-cores are logical CPUs 0-15 arranged as **SMT pairs**, so ``(0,1)`` are two
hyperthreads of one physical core sharing an L1 and an L2. Running eight threads on CPUs 0-7 gives you four
physical cores' worth of throughput and moves the numbers by 2-3x.

``physical_cores(n)`` returns 0, 2, 4, … Check your own layout with:

```shell
$ cat /sys/devices/cpu_core/cpus
$ lscpu -e
```

## Reproducing

```shell
$ cargo test --release
$ RUSTFLAGS="-C target-cpu=native" cargo build --release
$ for v in single shared padded local readonly true-shared; do
    ./target/release/counters $v 8 200
  done
```

### Coherence counters

Needs ``kernel.perf_event_paranoid`` at 2 or lower:

```shell
$ sudo sysctl -w kernel.perf_event_paranoid=1
$ perf stat -e cpu_core/cycles/,cpu_core/mem_load_l3_hit_retired.xsnp_hitm/ \
    ./target/release/counters shared 8 200
```

``mem_load_l3_hit_retired.xsnp_hitm`` counts loads served by a *modified* line in another core's cache, which
is the direct signature of false sharing. Note that ``xsnp_fwd`` returns byte-identical values on this CPU, so
the two are aliased; don't present them as independent measurements.

### Finding the guilty cache line

```shell
$ perf c2c record -- ./target/release/counters shared 8 60
$ perf c2c report --stdio
```

This names the contended lines and the offsets within them. On a hybrid CPU it may select the ``cpu_atom``
PMU, so treat its absolute rates with care; the line addresses and offsets are sound.

Put the sysctl back when you're done:

```shell
$ sudo sysctl -w kernel.perf_event_paranoid=4
```

## The Python half

```shell
$ cd python
$ uv run --python 3.14  python false_sharing.py   # with the GIL
$ uv run --python 3.14t python false_sharing.py   # free-threaded
```

Under the GIL, padding the counters apart is worth nothing at all, because two threads never write the line
concurrently. Free-threaded, the identical change is worth about 6x.

## Tests

```shell
$ cargo test --release
```

The tests assert that every variant returns the same total, that ``Padded`` really occupies 64 bytes and gets a
line each, that unpadded counters cannot get a line each, and that ``sched_setaffinity`` actually moved the
thread to the CPU we asked for. If any of those fail the benchmark is measuring something other than false
sharing.
