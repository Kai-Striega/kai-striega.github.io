# aos-vs-soa

The benchmark behind the blog post [Array of Structs vs Struct of
Arrays](https://kaistriega.com/blog/mechanical-sympathy/array-of-structs-vs-struct-of-arrays/).

Both layouts hold identical weather station readings. Every kernel answers the same question: what is the
total of the ``temperature`` field? The only thing that differs is how the readings are arranged in memory.

## Reproducing the numbers

The results in the post were measured on a 12th Gen Intel Core i9-12900K (64 byte cache lines, 48 KiB L1d per
P-core, 1.25 MiB L2 per P-core, 30 MiB shared L3) running Linux.

That CPU is a hybrid design with fast P-cores and slower E-cores, so **every measurement must be pinned to a
P-core** or the numbers are meaningless. On this machine CPUs 0-15 are P-cores; check yours with:

```shell
$ cat /sys/devices/cpu_core/cpus
```

### Timings

```shell
$ RUSTFLAGS="-C target-cpu=native" taskset -c 2 cargo bench
```

### Assembly

```shell
$ RUSTFLAGS="-C target-cpu=native" cargo rustc --release --lib -- --emit asm
$ grep -n total_temperature target/release/deps/aos_vs_soa-*.s
```

### Hardware counters

``perf`` needs ``kernel.perf_event_paranoid`` to be 2 or lower to read counters as an unprivileged user:

```shell
$ sudo sysctl -w kernel.perf_event_paranoid=1
$ RUSTFLAGS="-C target-cpu=native" cargo build --release
$ taskset -c 2 perf stat -e cycles,instructions,L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-load-misses \
      ./target/release/counters aos
$ taskset -c 2 perf stat -e cycles,instructions,L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-load-misses \
      ./target/release/counters soa
```

On a hybrid CPU ``perf`` may need the core type spelled out, e.g. ``cpu_core/L1-dcache-load-misses/``.

Put ``perf_event_paranoid`` back when you're done:

```shell
$ sudo sysctl -w kernel.perf_event_paranoid=4
```

## Tests

```shell
$ cargo test --release
```

The tests assert that ``Reading`` really is 32 bytes, that both layouts hold the same data, and that both
produce the same total. If the layouts ever disagree the benchmark is measuring nothing.
