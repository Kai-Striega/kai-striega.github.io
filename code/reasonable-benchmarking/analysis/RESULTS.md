# Captured results (Apple Silicon, macOS, Rust 1.95)

All numbers measured on this machine. Reproduce with the commands shown.
The workload answer is identical every run: `sum_of_squares` over 10k u64 = `11251846665439727927`.

## E1: three runs, three numbers (`cargo run --release --bin three_runs`)

| round | per-iteration |
|-------|---------------|
| 1     | 6024.21 ns    |
| 2     | 5472.83 ns    |
| 3     | 5448.21 ns    |

Same code, same input, same answer. ~10% spread; round 1 slowest (cold start / frequency ramp).

## E2: the benchmark the compiler deleted (`cargo run --release --bin dce`)

| variant       | per-iteration | apparent throughput |
|---------------|---------------|---------------------|
| no `black_box`| 0.000 ns      | ~9.6e8 GB/s (fiction)|
| `black_box`   | 5457.80 ns    | 14.7 GB/s (real)    |

The barrier-free loop measured 83 ns *total* for 1,000,000 iterations: the loop was
deleted. Reported as "65,756,663x faster. It is not faster. It does not exist."
Note the real per-iter (5458 ns) matches E1's ~5450 ns, internal consistency.

## E3: incidentals (`cargo run --release --bin min_timer`, min of 300 rounds)

Minimum estimator is extremely stable at the floor: **5420.0 ns/iter** (runs agree to <0.01%).

Compilation incidentals, *no effect on this workload* (LLVM emits the same optimal
vectorized inner loop in every case):

| condition                    | min ns/iter |
|------------------------------|-------------|
| baseline release             | 5420.0      |
| + 8 KB environment padding   | 5420.1      |
| `-C target-cpu=native`       | 5420.0      |
| codegen-units = 1            | 5420.1      |

Machine-state incidental *does* move the number: on a minority of runs the minimum
drops to **~4460 to 4670 ns** (13 to 18% faster), the frequency / P-vs-E-core state. An
incidental you do not control, moving the floor more than any compiler flag did.

Honest framing for the post: our loop is too optimizer-stable to show *layout* effects;
that story is carried by the literature (Mytkowicz 2009 [1], Stabilizer 2013 [2], where
-O2 vs -O3 is indistinguishable from layout noise on SPEC CPU2006).

## E4 / E5: one benchmark's distribution (`cargo bench --bench distribution`; `analyze.py`)

Per-iteration estimators (criterion, 500 samples each):

| workload | min | mean | median | slope (OLS) | std/mean | Shapiro-Wilk p |
|----------|-----|------|--------|-------------|----------|----------------|
| compute_bound (in cache) | 5.19 µs | 5.52 µs | 5.49 µs | 5.53 µs | 9.1% | 1.40e-43 |
| memory_bound (chase)     | 339 µs  | 348 µs  | 348 µs  | n/a (Flat)  | 1.3% | 2.69e-15 |

- compute_bound: skew +15.50, excess kurtosis +240.79 (a few catastrophic outliers, i.e. perturbing events).
- memory_bound: skew +1.40, excess kurtosis +4.93 (smooth right-skew, Lemire's shape). Figure uses this one.

divan on the same workloads (median-centric):

```
                    fastest   │ slowest   │ median    │ mean
compute_bound       5.374 µs  │ 6.708 µs  │ 5.416 µs  │ 5.426 µs
memory_bound        323 µs    │ 5.171 ms  │ 324.9 µs  │ 337.6 µs   ← slowest is 15x the median
```

Figure written to `static/images/benchmark-distribution.svg`.

## E7: comparing a suite (`cargo bench --bench sorts`; `analyze.py`)

Overlap figure (`static/images/two-distributions-overlap.svg`): on random 100k, the stable and unstable
sample **ranges overlap by 68%** of the pooled span despite a **27% gap in medians**: you could not tell
them apart from single runs, yet Mann-Whitney U on 200 samples returns p=7e-61. Illustrates "don't race the
point estimates" in Part 3.


unstable (pdqsort) vs stable (merge) sort, per-case ratio unstable/stable:

| input | unstable is | | input | unstable is |
|-------|-------------|-|-------|-------------|
| random 100k | 27% faster | | sorted 100k | 2.6% faster |
| random 1k | 16% faster | | reversed 100k | 2.4% faster |
| few-unique 100k | 27% faster | | (all 8 cases: unstable faster) | |

- **Geometric mean of ratios:** 0.871 → unstable **14.8% faster overall**. (Arithmetic mean 0.875 is
  inconsistent: 0.875 × its inverse-mean 1.153 = 1.009 ≠ 1; geomean 0.871 × 1.148 = 1.000. Fleming-Wallace.)
- **All 8 cases significant** (Mann-Whitney U) both raw and after Benjamini-Hochberg; effects are large.

### Null / multiple-comparison experiment

- **Same sort benchmarked twice** (left vs right, identical code, 8 cases): **3 of 8** "significant" at raw
  p<0.05, inflated above α because the two sides ran sequentially and the machine drifted between them.
- **1000 random 50/50 splits of one real sample:** **5.3%** significant at raw p<0.05 ≈ the chosen α=0.05.
  → 20 honest comparisons ⇒ expect ~1 false winner. This is the inflation a correction removes.

