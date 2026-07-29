//! Experiments E4 and E5: one benchmark is a distribution, not a number.
//!
//!     cargo bench --bench distribution
//!
//! Criterion does the right thing by default: it takes a whole sample of measurements, fits a line
//! through them and puts a bootstrap confidence interval on the estimate, no normality assumed. It also
//! *persists the raw sample* under `target/criterion/<group>/<bench>/new/`, which is what we want: the
//! Python analysis in `analysis/` reads those samples back to draw the histogram and QQ-plot (E4) and to
//! compute the minimum, mean and median side by side (E5).
//!
//! Two workloads, because the shape of the distribution depends on what you are measuring:
//!
//!   * `compute_bound`: sum of squares over a small array that lives in cache. Fast and tight, but the
//!     one-sided nature of noise still skews it: nothing ever makes a run faster than the ideal, plenty
//!     of things make it slower.
//!   * `memory_bound`: pointer chasing over an array far larger than the last-level cache. This is
//!     Lemire's example, and it is where non-normality becomes obvious.

use criterion::{criterion_group, criterion_main, Criterion, Throughput};

use reasonable_benchmarking::{build_cycle, chase, generate_values, sum_of_squares};
use std::hint::black_box;

/// 10k u64 = 80 KB. Comfortably inside L2 on an Apple Silicon P-core, so this measures compute, not
/// memory traffic.
const COMPUTE_N: usize = 10_000;

/// 8M u64 = 64 MB. Far larger than any core-private cache, so every chase step is a cache miss and the
/// loop is latency-bound.
const MEMORY_N: usize = 8 << 20;
const CHASE_STEPS: usize = 20_000;

fn compute_bound(c: &mut Criterion) {
    let values = generate_values(COMPUTE_N, 0xC0FFEE);
    let mut group = c.benchmark_group("compute_bound");
    group.throughput(Throughput::Elements(COMPUTE_N as u64));
    group.bench_function("sum_of_squares", |b| {
        b.iter(|| black_box(sum_of_squares(black_box(&values))))
    });
    group.finish();
}

fn memory_bound(c: &mut Criterion) {
    let next = build_cycle(MEMORY_N, 0x5EED);
    let mut group = c.benchmark_group("memory_bound");
    group.throughput(Throughput::Elements(CHASE_STEPS as u64));
    group.bench_function("pointer_chase", |b| {
        b.iter(|| black_box(chase(black_box(&next), 0, CHASE_STEPS)))
    });
    group.finish();
}

criterion_group! {
    name = benches;
    // A large sample so the distribution is worth looking at, and a longer measurement time so the
    // memory-bound case gets enough iterations to be stable.
    config = Criterion::default().sample_size(500).measurement_time(std::time::Duration::from_secs(10));
    targets = compute_bound, memory_bound
}
criterion_main!(benches);
