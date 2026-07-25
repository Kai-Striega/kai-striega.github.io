# branch-prediction

The benchmark behind the blog post [Branch
Prediction](https://kaistriega.com/blog/mechanical-sympathy/branch-prediction/), part 2 of the Mechanical
Sympathy series.

Two halves, because there are two different predictors involved.

**Part A, conditional branches.** Count the values in an array above a threshold. The generator takes the
proportion of values that should pass, so how often the branch is taken, and therefore how predictable it is,
becomes a dial we can turn.

**Part B, indirect branches.** A small bytecode interpreter whose dispatch compiles to a jump table. Every
opcode is total and accumulator neutral, so any sequence is a valid program, and every generated program
executes exactly the same mix of opcodes. The only variable is the order, and therefore how learnable the
instruction stream is.

## A warning about the compiler

The obvious way to write the counting loop does not compile to a branch at all:

```shell
$ RUSTFLAGS="-C target-cpu=native" cargo rustc --release --lib -- --emit asm
$ grep -A4 'count_above_naive' target/release/deps/branch_prediction-*.s
```

LLVM vectorises it into ``vpcmpgtd`` and ``vpaddq``: a SIMD compare and add, with no data dependent branch
anywhere. Benchmarking that would have measured nothing.

``count_above_branchy`` therefore puts an optimisation barrier inside the taken arm so a real ``jle``
survives, and ``count_above_branchless_barrier`` carries the same barrier so the two are compared on equal
terms. **Check the assembly before trusting any number this crate produces.** The branchy variant must
contain a data dependent ``jcc``; the branchless one must use ``setg`` instead.

## Reproducing the numbers

Measured on a 12th Gen Intel Core i9-12900K running Linux. That CPU is a hybrid design with fast P-cores and
slow E-cores, so **every measurement must be pinned to a P-core** or the numbers are meaningless:

```shell
$ cat /sys/devices/cpu_core/cpus
```

The working set is 256K elements, which is 1 MB and fits in this core's 1.25 MB L2. That is deliberate. A
working set that spilled to main memory would just re-measure part 1 of the series.

### Timings

```shell
$ RUSTFLAGS="-C target-cpu=native" taskset -c 2 cargo bench
```

### Hardware counters

``perf`` needs ``kernel.perf_event_paranoid`` at 2 or lower to read counters as an unprivileged user. This
CPU exposes conditional and indirect mispredictions separately, which is what lets the two halves of the post
be told apart rather than merely asserted:

```shell
$ sudo sysctl -w kernel.perf_event_paranoid=1
$ RUSTFLAGS="-C target-cpu=native" cargo build --release

$ taskset -c 2 perf stat \
    -e cycles,instructions,branches,branch-misses,br_misp_retired.cond,br_misp_retired.indirect \
    ./target/release/counters cond branchy 50

$ taskset -c 2 perf stat \
    -e cycles,instructions,branches,branch-misses,br_misp_retired.cond,br_misp_retired.indirect \
    ./target/release/counters interp match random
```

Put it back when you're done:

```shell
$ sudo sysctl -w kernel.perf_event_paranoid=4
```

## Tests

```shell
$ cargo test --release
```

The tests assert that every counting variant returns the same answer, that the generator hits the requested
proportion exactly, that sorting preserves the multiset, that every generated program contains exactly the
same number of each opcode regardless of period, and that both dispatch strategies agree. If any of those
fail the benchmark is measuring the workload rather than the predictor.
