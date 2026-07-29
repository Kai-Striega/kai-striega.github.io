# reasonable-benchmarking

The code behind the [Reasonable Benchmarking](https://kaistriega.com/blog/reasonable-benchmarking/) series: a
three-part argument that a single timing is untrustworthy, that one benchmark is a distribution rather than a
number, and that a comparison is a statistical claim. Every figure and number in the posts comes from here.

All of it was measured on an Apple Silicon laptop (macOS, Rust 1.95). Your numbers will be different; that is
the entire point of the series.

## The workload

Nothing here is meant to be fast or interesting. The workloads in [`src/lib.rs`](src/lib.rs) are deliberately
dull and, above all, *deterministic*: given the same input they return the same answer on every run. That is the
trick the whole series rests on. If the answer never changes but the runtime does, every bit of variation is a
property of the measurement, not the computation.

- `sum_of_squares`: a pure reduction over a slice. The subject of parts one and two, and the perfect victim for
  dead-code elimination.
- `chase` / `build_cycle`: pointer-chasing around a random cycle far larger than cache, so the loop is bound by
  memory latency. This is the memory-bound example whose distribution is so clearly non-normal.
- `generate_pattern`: the four input shapes (random, sorted, reversed, few-unique) for the sort comparison in
  part three.

## Part 1: a single measurement (binaries)

These are plain binaries, not benches, because the point is what happens when you time things *by hand*.

```shell
cargo run --release --bin three_runs   # E1: same workload, three runs, three answers
cargo run --release --bin dce          # E2: the benchmark the compiler deleted
cargo run --release --bin min_timer    # E3: does an incidental change move the number?
```

`min_timer` is the one to poke at. Run it under different conditions and compare the minimum it reports:

```shell
cargo run --release --bin min_timer
RUSTFLAGS="-C target-cpu=native" cargo run --release --bin min_timer
env PADDING=$(printf 'x%.0s' {1..8000}) cargo run --release --bin min_timer
```

On this machine the floor is identical to four significant figures across all of them, because the inner loop
compiles to the same vectorised code every time. What *does* move it is the machine's own frequency and
core-scheduling state, which is the honest lesson.

## Part 2: one benchmark's distribution (benches)

```shell
cargo bench --bench distribution         # criterion: persists raw samples under target/criterion
cargo bench --bench distribution_divan   # divan: the same workloads, median-centric
```

Criterion keeps every sample under `target/criterion/<group>/<bench>/new/sample.json`. The Python in
[`analysis/`](analysis/) reads those back to draw the histogram + QQ-plot and to run the normality test.

## Part 3: comparing a suite (bench)

```shell
cargo bench --bench sorts   # stable vs unstable across the suite, plus a null (A/A) group
```

The `sort` group is the real comparison; the `null` group benchmarks the *same* algorithm as "left" and "right"
so that any measured difference is noise, which is what the multiple-comparison section needs.

## The analysis

```shell
uv venv --python 3.13 analysis/.venv
uv pip install --python analysis/.venv numpy scipy matplotlib
analysis/.venv/bin/python analysis/analyze.py
```

`analyze.py` prints every table in parts two and three as Markdown, writes the distribution figure into the
site's `static/images/`, and runs the Mann-Whitney U tests, the Benjamini-Hochberg correction, the geometric
mean, and the null experiments. The captured results are in [`analysis/RESULTS.md`](analysis/RESULTS.md).
